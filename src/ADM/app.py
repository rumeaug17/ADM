"""Fabrique de l'application Flask ADM, sans effet de bord à l'import."""

import json
import os
import secrets
from collections.abc import Callable, Mapping
from datetime import timedelta
from pathlib import Path
from typing import cast

from flask import Flask, abort, render_template, request, session
from werkzeug.exceptions import HTTPException

from ADM.accounts_service import AccountSession
from ADM.auth_providers import get_auth_provider
from ADM.persistent_paths import resolve_persistent_path
from ADM.routes import accounts, applications, auth, evaluations, exports, settings, supervision
from ADM.schemas import AppConfig, parse_questions
from ADM.scoring import compute_categories, compute_scoring_map
from ADM.services import RadarChartCache, dicp_level_label

PACKAGE_RESOURCES = Path(__file__).resolve().parent / "resources"

_TRUE_ENV_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_ENV_VALUES = frozenset({"0", "false", "no", "off"})


def _load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def _default_config() -> dict[str, object]:
    """Retourne la configuration non sensible utilisée sans fichier dédié."""
    return {
        "db_backend": "json",
        "json_connection_url": "applications.json",
        "display_thresholds": {
            "score": {"warning": 30, "critical": 60},
            "risk": {"warning": 100, "critical": 350},
        },
    }


def _load_app_config(path: Path, *, use_defaults_when_missing: bool) -> AppConfig:
    """Charge la configuration, avec des valeurs sûres si le fichier est absent."""
    try:
        raw_config = _load_json(path)
    except FileNotFoundError:
        if not use_defaults_when_missing:
            raise
        raw_config = _default_config()
    return AppConfig.from_object(raw_config)


def _resolve_config_path(configured: str) -> Path:
    """Retourne le chemin de ``config.json`` à utiliser pour cette instance.

    ``config.json`` n'est pas une simple ressource statique : les seuils
    d'affichage y sont réécrits à chaud depuis ``/settings`` (US4.2).
    ``ADM_CONFIG_PATH`` permet de pointer vers un emplacement persistant, à
    l'image d'``ADM_DATABASE_URL`` ou ``ADM_ACCOUNTS_URL`` (voir
    ``ADM.persistent_paths`` pour la justification complète).
    """
    return resolve_persistent_path(configured, PACKAGE_RESOURCES / "config.json")


def _resolve_questions_path(configured: str) -> Path:
    """Retourne le chemin de ``questions.json`` à utiliser pour cette instance.

    Même raisonnement que ``_resolve_config_path`` : depuis la page de gestion
    des questions (US4.3), le questionnaire est réécrit à chaud et doit donc
    pouvoir être stocké hors du paquet installé via ``ADM_QUESTIONS_PATH``.
    """
    return resolve_persistent_path(configured, PACKAGE_RESOURCES / "static" / "questions.json")


def _resolve_info_texts_path(configured: str) -> Path:
    """Retourne le chemin d'``info_texts.json`` à utiliser pour cette instance.

    Même raisonnement que ``_resolve_config_path`` : l'aide en ligne de chaque
    question (US4.3) est réécrite à chaud et doit donc pouvoir être stockée
    hors du paquet installé via ``ADM_INFO_TEXTS_PATH``.
    """
    return resolve_persistent_path(configured, PACKAGE_RESOURCES / "static" / "info_texts.json")


def _env_flag(name: str, *, default: bool) -> bool:
    """Interprète une variable d'environnement booléenne (US6.3).

    Accepte ``1``/``true``/``yes``/``on`` et ``0``/``false``/``no``/``off``
    (insensible à la casse et aux espaces périphériques) ; absente, elle vaut
    ``default``.
    """
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    normalized = raw_value.strip().casefold()
    if normalized in _TRUE_ENV_VALUES:
        return True
    if normalized in _FALSE_ENV_VALUES:
        return False
    raise ValueError(
        f"La variable d'environnement {name!r} doit être un booléen ({raw_value!r} invalide)."
    )


def _env_positive_int(name: str, *, default: int) -> int:
    """Interprète une variable d'environnement entière strictement positive (US6.3)."""
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError as error:
        raise ValueError(
            f"La variable d'environnement {name!r} doit être un entier ({raw_value!r} invalide)."
        ) from error
    if value <= 0:
        raise ValueError(f"La variable d'environnement {name!r} doit être strictement positive.")
    return value


def create_app(test_config: Mapping[str, object] | None = None) -> Flask:
    """Construit et configure une instance isolée de l'application."""
    app = Flask(
        __name__,
        static_folder=str(PACKAGE_RESOURCES / "static"),
        template_folder=str(PACKAGE_RESOURCES / "templates"),
    )
    app.config.from_mapping(
        CONFIG=os.environ.get("ADM_CONFIG_PATH") or str(PACKAGE_RESOURCES / "config.json"),
        QUESTIONS_PATH=os.environ.get("ADM_QUESTIONS_PATH")
        or str(PACKAGE_RESOURCES / "static" / "questions.json"),
        INFO_TEXTS_PATH=os.environ.get("ADM_INFO_TEXTS_PATH")
        or str(PACKAGE_RESOURCES / "static" / "info_texts.json"),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
        # --- US6.3 : attributs de cookie de session explicites, plutôt que de
        # s'appuyer sur les valeurs par défaut de Flask. ADM_SESSION_COOKIE_SECURE
        # permet de désactiver l'attribut Secure pour un développement local en
        # HTTP simple (voir scripts/setup_demo.sh) ; il doit rester activé (valeur
        # par défaut) dès que le service est exposé, comme l'exige INSTALL.md.
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=_env_flag("ADM_SESSION_COOKIE_SECURE", default=True),
        PERMANENT_SESSION_LIFETIME=timedelta(
            minutes=_env_positive_int("ADM_SESSION_LIFETIME_MINUTES", default=480)
        ),
    )
    if test_config:
        app.config.update(test_config)
    config_path = _resolve_config_path(str(app.config["CONFIG"]))
    app.config["CONFIG"] = str(config_path)
    config = AppConfig.from_object(_load_json(config_path))
    questions_path = _resolve_questions_path(str(app.config["QUESTIONS_PATH"]))
    app.config["QUESTIONS_PATH"] = str(questions_path)
    questions = parse_questions(_load_json(questions_path))
    info_texts_path = _resolve_info_texts_path(str(app.config["INFO_TEXTS_PATH"]))
    app.config["INFO_TEXTS_PATH"] = str(info_texts_path)
    secret_key = app.config.get("SECRET_KEY") or os.environ.get("ADM_SECRET_KEY")
    if not secret_key:
        raise RuntimeError("La variable d'environnement ADM_SECRET_KEY est obligatoire.")
    app.secret_key = str(secret_key)
    backend = str(
        app.config.get("DB_BACKEND") or os.environ.get("ADM_DB_BACKEND") or config.db_backend
    ).lower()
    if backend in {"mysql", "sqlite"}:
        from ADM.database import get_session_factory, init_db

        connection = app.config.get("DB_CONNECTION") or os.environ.get("ADM_DATABASE_URL")
        if not connection:
            backend_name = "SQLite" if backend == "sqlite" else "MySQL"
            raise RuntimeError(f"ADM_DATABASE_URL est obligatoire avec le backend {backend_name}.")
    elif backend == "json":
        from ADM.database_json import get_session_factory, init_db

        connection = (
            app.config.get("DB_CONNECTION")
            or os.environ.get("ADM_DATABASE_URL")
            or config.json_connection_url
        )
    else:
        raise ValueError("Configuration du backend incorrecte.")
    engine = init_db(str(connection))
    app.extensions["adm_session_factory"] = get_session_factory(engine)
    app.extensions["adm_questions"] = questions
    app.extensions["adm_scoring_map"] = compute_scoring_map(questions)
    app.extensions["adm_categories"] = compute_categories(questions)
    app.extensions["adm_display_thresholds"] = config.display_thresholds
    app.extensions["adm_app_config"] = config  # ajout US4.2
    # Tâche 3.7 : cache borné des radar charts, propre à cette instance d'application
    # (voir ADM.services.RadarChartCache pour la justification de l'absence
    # d'invalidation explicite).
    app.extensions["adm_radar_chart_cache"] = RadarChartCache()

    # --- US6.1 : fabrique de session pour les comptes + fournisseur d'authentification ---
    account_session_factory: Callable[[], AccountSession]
    if backend in {"mysql", "sqlite"}:
        # Account partage la même Base SQLAlchemy qu'Application/Evaluation : la table
        # a déjà été créée par init_db ci-dessus, et la même fabrique de session sait
        # l'interroger. Pas de connexion séparée nécessaire.
        account_session_factory = cast(
            Callable[[], AccountSession], app.extensions["adm_session_factory"]
        )
    else:
        from ADM.accounts_json import get_account_session_factory, init_account_db

        accounts_connection = (
            app.config.get("ACCOUNTS_CONNECTION")
            or os.environ.get("ADM_ACCOUNTS_URL")
            or config.accounts_connection_url
        )
        accounts_engine = init_account_db(str(accounts_connection))
        account_session_factory = get_account_session_factory(accounts_engine)

    app.extensions["adm_account_session_factory"] = account_session_factory
    app.extensions["adm_auth_provider"] = get_auth_provider(
        config.auth_backend, account_session_factory
    )

    _register_web_components(app)
    return app


def _register_web_components(app: Flask) -> None:
    for blueprint in (supervision, auth, applications, evaluations, exports, settings, accounts):
        app.register_blueprint(blueprint)

    # Tâche 4.4 du backlog : un seul filtre Jinja traduit un indicateur DICP
    # (ex. "D1") en libellé humain, réutilisé en infobulle par les templates
    # qui affichent encore le code brut (`index.html`, `resume.html`).
    app.jinja_env.filters["dicp_label"] = dicp_level_label

    def protect_posts() -> None:
        if request.method == "POST":
            expected = session.get("csrf_token", "")
            submitted = request.form.get("csrf_token", "")
            if not expected or not secrets.compare_digest(expected, submitted):
                abort(400)

    def template_values() -> dict[str, object]:
        token = session.get("csrf_token")
        if not isinstance(token, str):
            token = secrets.token_urlsafe(32)
            session["csrf_token"] = token
        version_path = Path(app.static_folder or "") / "version.txt"
        try:
            version = version_path.read_text(encoding="utf-8").strip()
        except OSError:
            version = "v0.0.0"
        return {
            "csrf_token": token,
            "app_version": version,
            "display_thresholds": app.extensions["adm_display_thresholds"],
            "local_auth": app.extensions["adm_app_config"].auth_backend == "local",
        }

    def http_error(error: HTTPException) -> tuple[str, int]:
        messages = {
            400: "La requête envoyée est invalide.",
            403: "Vous n'êtes pas autorisé à effectuer cette action.",
            404: "La ressource demandée est introuvable.",
            413: "Le fichier envoyé est trop volumineux.",
            503: "Le service est temporairement indisponible.",
        }
        return render_template(
            "error.html", error_message=messages.get(error.code, "Une erreur est survenue.")
        ), error.code or 500

    def unexpected_error(error: Exception) -> tuple[str, int]:
        app.logger.error("Erreur serveur non gérée (%s).", type(error).__name__)
        return render_template("error.html", error_message="Une erreur interne est survenue."), 500

    app.before_request(protect_posts)
    app.context_processor(template_values)
    app.register_error_handler(HTTPException, http_error)
    app.register_error_handler(Exception, unexpected_error)
