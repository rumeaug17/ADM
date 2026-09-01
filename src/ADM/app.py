"""Fabrique de l'application Flask ADM, sans effet de bord à l'import."""

import json
import os
import secrets
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import cast

from flask import Flask, abort, render_template, request, session
from werkzeug.exceptions import HTTPException

from ADM.accounts_service import AccountSession
from ADM.auth_providers import get_auth_provider
from ADM.routes import accounts, applications, auth, evaluations, exports, settings
from ADM.schemas import AppConfig, parse_questions
from ADM.scoring import compute_categories, compute_scoring_map

PACKAGE_RESOURCES = Path(__file__).resolve().parent / "resources"


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
    d'affichage y sont réécrits à chaud depuis ``/settings`` (US4.2). Le laisser
    par défaut sous ``PACKAGE_RESOURCES`` fonctionne, mais ce chemin se trouve
    à l'intérieur du paquet installé (site-packages ou virtualenv) : une mise à
    jour du wheel (voir INSTALL.md, section 12) le remplace intégralement et
    efface silencieusement toute personnalisation. ``ADM_CONFIG_PATH`` permet
    de pointer vers un emplacement persistant, à l'image d'``ADM_DATABASE_URL``
    ou ``ADM_ACCOUNTS_URL``. S'il désigne un fichier qui n'existe pas encore,
    il est initialisé à partir du gabarit empaqueté.
    """
    path = Path(configured)
    if not path.exists():
        default_content = (PACKAGE_RESOURCES / "config.json").read_text(encoding="utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(default_content, encoding="utf-8")
    return path


def create_app(test_config: Mapping[str, object] | None = None) -> Flask:
    """Construit et configure une instance isolée de l'application."""
    app = Flask(
        __name__,
        static_folder=str(PACKAGE_RESOURCES / "static"),
        template_folder=str(PACKAGE_RESOURCES / "templates"),
    )
    app.config.from_mapping(
        CONFIG=os.environ.get("ADM_CONFIG_PATH") or str(PACKAGE_RESOURCES / "config.json"),
        QUESTIONS_FILE="questions.json",
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    config_path = _resolve_config_path(str(app.config["CONFIG"]))
    app.config["CONFIG"] = str(config_path)
    config = AppConfig.from_object(_load_json(config_path))
    questions = parse_questions(
        _load_json(Path(app.static_folder or "") / str(app.config["QUESTIONS_FILE"]))
    )
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
    for blueprint in (auth, applications, evaluations, exports, settings, accounts):
        app.register_blueprint(blueprint)

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
