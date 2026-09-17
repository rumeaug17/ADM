"""Tests de la page de configuration des seuils d'affichage (US4.2)."""

import json
from pathlib import Path

import pytest

from ADM.accounts_json import AccountJsonSession, init_account_db
from ADM.accounts_service import create_account
from ADM.config_io import save_display_thresholds
from ADM.schemas import DisplayThresholds, Thresholds
from ADM.validation import InputValidationError, validate_display_thresholds_form

# --- Tests unitaires purs (sans Flask) ---


def test_validate_display_thresholds_form_valid() -> None:
    form = {
        "score_warning": "25",
        "score_critical": "55",
        "risk_warning": "80",
        "risk_critical": "300",
    }
    result = validate_display_thresholds_form(form)
    assert result.score.warning == 25
    assert result.risk.critical == 300


def test_validate_display_thresholds_form_rejects_warning_ge_critical() -> None:
    form = {
        "score_warning": "80",
        "score_critical": "60",
        "risk_warning": "80",
        "risk_critical": "300",
    }
    with pytest.raises(InputValidationError, match="seuil"):
        validate_display_thresholds_form(form)


def test_validate_display_thresholds_form_rejects_negative() -> None:
    form = {
        "score_warning": "-5",
        "score_critical": "60",
        "risk_warning": "80",
        "risk_critical": "300",
    }
    with pytest.raises(InputValidationError):
        validate_display_thresholds_form(form)


def test_validate_display_thresholds_form_rejects_non_numeric() -> None:
    form = {
        "score_warning": "abc",
        "score_critical": "60",
        "risk_warning": "80",
        "risk_critical": "300",
    }
    with pytest.raises(InputValidationError, match="nombre"):
        validate_display_thresholds_form(form)


def test_validate_display_thresholds_form_rejects_missing_field() -> None:
    with pytest.raises(InputValidationError, match="obligatoire"):
        validate_display_thresholds_form({"score_warning": "25"})


def test_save_display_thresholds_preserves_other_keys(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "db_backend": "mysql",
                "json_connection_url": "applications.json",
                "display_thresholds": {
                    "score": {"warning": 30, "critical": 60},
                    "risk": {"warning": 100, "critical": 350},
                },
            }
        ),
        encoding="utf-8",
    )

    save_display_thresholds(
        config_path,
        DisplayThresholds(score=Thresholds(20, 50), risk=Thresholds(90, 300)),
    )

    saved = json.loads(config_path.read_text(encoding="utf-8"))
    assert saved["db_backend"] == "mysql"
    assert saved["display_thresholds"]["score"]["warning"] == 20


def test_save_display_thresholds_rejects_invalid_json(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON valide"):
        save_display_thresholds(config_path, DisplayThresholds())


def test_save_display_thresholds_atomic_on_write_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "config.json"
    original = json.dumps(
        {
            "db_backend": "json",
            "json_connection_url": "applications.json",
            "display_thresholds": {
                "score": {"warning": 30, "critical": 60},
                "risk": {"warning": 100, "critical": 350},
            },
        }
    )
    config_path.write_text(original, encoding="utf-8")

    def _boom(self: Path, *args: object, **kwargs: object) -> int:
        raise OSError("disque plein simulé")

    monkeypatch.setattr(Path, "write_text", _boom)
    with pytest.raises(ValueError, match="enregistrer"):
        save_display_thresholds(config_path, DisplayThresholds())
    assert config_path.read_text(encoding="utf-8") == original


# --- Tests d'intégration HTTP, alignés sur le style de test_app_factory.py ---


def _config_path(tmp_path: Path) -> Path:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "db_backend": "json",
                "json_connection_url": "applications.json",
                "display_thresholds": {
                    "score": {"warning": 30, "critical": 60},
                    "risk": {"warning": 100, "critical": 350},
                },
            }
        ),
        encoding="utf-8",
    )
    return config_path


def _seed_admin_account(tmp_path: Path, *, username: str = "alice") -> Path:
    """Crée un compte administrateur actif isolé dans ``tmp_path``, pour que la
    revalidation du compte à chaque requête protégée trouve un compte réel correspondant
    à la session simulée (au lieu du fichier accounts.json par défaut du dépôt)."""
    accounts_path = tmp_path / "accounts.json"
    engine = init_account_db(str(accounts_path))
    accounts_session = AccountJsonSession(engine)
    create_account(accounts_session, username=username, password="secret-de-test", role="admin")
    accounts_session.commit()
    accounts_session.close()
    return accounts_path


def test_show_settings_requires_login(tmp_path: Path) -> None:
    from ADM.app import create_app

    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
            "DB_CONNECTION": str(tmp_path / "catalogue.json"),
            "CONFIG": str(_config_path(tmp_path)),
        }
    )

    response = application.test_client().get("/settings")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_update_settings_requires_csrf_token(tmp_path: Path) -> None:
    from ADM.app import create_app

    accounts_path = _seed_admin_account(tmp_path)
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
            "DB_CONNECTION": str(tmp_path / "catalogue.json"),
            "CONFIG": str(_config_path(tmp_path)),
            "ACCOUNTS_CONNECTION": str(accounts_path),
        }
    )
    client = application.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "alice"
        sess["role"] = "admin"
        sess["auth_generation"] = 0

    response = client.post(
        "/settings",
        data={
            "score_warning": "25",
            "score_critical": "55",
            "risk_warning": "80",
            "risk_critical": "300",
        },
    )

    assert response.status_code == 400


def test_update_settings_valid_persists_and_reloads(tmp_path: Path) -> None:
    from ADM.app import create_app

    config_path = _config_path(tmp_path)
    accounts_path = _seed_admin_account(tmp_path)
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
            "DB_CONNECTION": str(tmp_path / "catalogue.json"),
            "CONFIG": str(config_path),
            "ACCOUNTS_CONNECTION": str(accounts_path),
        }
    )
    client = application.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "alice"
        sess["role"] = "admin"
        sess["auth_generation"] = 0
        sess["csrf_token"] = "jeton-de-test"

    response = client.post(
        "/settings",
        data={
            "csrf_token": "jeton-de-test",
            "score_warning": "25",
            "score_critical": "55",
            "risk_warning": "80",
            "risk_critical": "300",
        },
    )

    assert response.status_code == 302
    saved = json.loads(config_path.read_text(encoding="utf-8"))
    assert saved["display_thresholds"]["score"]["warning"] == 25
    assert saved["db_backend"] == "json"
    # rechargé à chaud, sans redémarrage
    assert application.extensions["adm_display_thresholds"].score.warning == 25


def test_update_settings_rejects_invalid_thresholds_without_persisting(tmp_path: Path) -> None:
    from ADM.app import create_app

    config_path = _config_path(tmp_path)
    accounts_path = _seed_admin_account(tmp_path)
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
            "DB_CONNECTION": str(tmp_path / "catalogue.json"),
            "CONFIG": str(config_path),
            "ACCOUNTS_CONNECTION": str(accounts_path),
        }
    )
    client = application.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "alice"
        sess["role"] = "admin"
        sess["auth_generation"] = 0
        sess["csrf_token"] = "jeton-de-test"

    response = client.post(
        "/settings",
        data={
            "csrf_token": "jeton-de-test",
            "score_warning": "80",
            "score_critical": "60",
            "risk_warning": "80",
            "risk_critical": "300",
        },
    )

    assert response.status_code == 400
    saved = json.loads(config_path.read_text(encoding="utf-8"))
    assert saved["display_thresholds"]["score"]["warning"] == 30  # inchangé


# --- Tests : chemins/valeurs réellement chargés, bloc "Paramètres de déploiement" ---


def test_show_settings_displays_real_deployment_values_over_stale_config_file(
    tmp_path: Path,
) -> None:
    """La page doit refléter ce que l'application a réellement chargé au
    démarrage, pas uniquement la valeur écrite dans config.json : ADM_DB_BACKEND/
    ADM_DATABASE_URL (ici simulés via DB_BACKEND/DB_CONNECTION, le mécanisme de
    test habituel de create_app) peuvent la supplanter, exactement comme en
    production. Vérifie aussi que les chemins réels de questions.json et
    info_texts.json (US4.3), absents jusqu'ici du bloc, sont désormais affichés."""
    from ADM.app import create_app

    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "db_backend": "mysql",
                "json_connection_url": "applications.json",
                "display_thresholds": {
                    "score": {"warning": 30, "critical": 60},
                    "risk": {"warning": 100, "critical": 350},
                },
            }
        ),
        encoding="utf-8",
    )
    catalogue_path = tmp_path / "catalogue.json"
    questions_target = tmp_path / "questions.json"
    info_texts_target = tmp_path / "info_texts.json"
    accounts_path = _seed_admin_account(tmp_path)
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
            "DB_CONNECTION": str(catalogue_path),
            "CONFIG": str(config_path),
            "ACCOUNTS_CONNECTION": str(accounts_path),
            "QUESTIONS_PATH": str(questions_target),
            "INFO_TEXTS_PATH": str(info_texts_target),
        }
    )
    client = application.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "alice"
        sess["role"] = "admin"
        sess["auth_generation"] = 0

    response = client.get("/settings")
    body = response.data.decode("utf-8")

    assert response.status_code == 200
    # Le backend réellement démarré (JSON, via DB_BACKEND) doit être affiché,
    # jamais celui, obsolète, de config.json ("mysql").
    assert "mysql" not in body
    assert str(catalogue_path) in body
    assert str(config_path.resolve()) in body
    assert str(questions_target.resolve()) in body
    assert str(info_texts_target.resolve()) in body


def test_show_settings_redacts_credentials_from_connection_string(tmp_path: Path) -> None:
    """Un identifiant/mot de passe éventuellement présent dans la chaîne de
    connexion réelle (``ADM_DATABASE_URL`` pour un backend MySQL) ne doit jamais
    apparaître en clair sur la page, même réservée au rôle admin."""
    from ADM.app import create_app

    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
            "DB_CONNECTION": str(tmp_path / "catalogue.json"),
            "CONFIG": str(_config_path(tmp_path)),
            "ACCOUNTS_CONNECTION": str(_seed_admin_account(tmp_path)),
        }
    )
    # Simule après coup un backend MySQL avec identifiants en clair, comme le
    # ferait ADM_DATABASE_URL en production (pas besoin d'un vrai serveur MySQL
    # pour vérifier l'affichage : adm_db_backend/adm_db_connection sont lus à la
    # requête, voir ADM.routes.db_backend_in_use/db_connection_in_use).
    application.extensions["adm_db_backend"] = "mysql"
    application.extensions["adm_db_connection"] = (
        "mysql+pymysql://adm_user:s3cr3t-mdp@db.internal:3306/adm"
    )
    client = application.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "alice"
        sess["role"] = "admin"
        sess["auth_generation"] = 0

    response = client.get("/settings")

    assert response.status_code == 200
    assert b"s3cr3t-mdp" not in response.data
    assert b"adm_user:***@db.internal:3306" in response.data
