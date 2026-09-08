"""Tests des exports du catalogue : restriction par rôle du réimport (US6.1) et
encodage du CSV (Tâche 0.2)."""

import io
import json
from pathlib import Path

from flask import Flask

from ADM.accounts_json import AccountJsonSession, init_account_db
from ADM.accounts_service import create_account
from ADM.database import Application
from ADM.database_json import JsonSession, init_db


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


def _seed_account(
    tmp_path: Path, *, username: str, password: str = "secret-de-test", role: str
) -> Path:
    """Crée un compte actif isolé dans ``tmp_path``, pour que la revalidation du compte
    à chaque requête protégée trouve un compte réel correspondant à la session simulée."""
    accounts_path = tmp_path / "accounts.json"
    engine = init_account_db(str(accounts_path))
    accounts_session = AccountJsonSession(engine)
    create_account(accounts_session, username=username, password=password, role=role)
    accounts_session.commit()
    accounts_session.close()
    return accounts_path


def _create_test_app(tmp_path: Path, accounts_path: Path | None = None) -> Flask:
    from ADM.app import create_app

    config: dict[str, object] = {
        "TESTING": True,
        "SECRET_KEY": "cle-factice-reservee-aux-tests",
        "DB_BACKEND": "json",
        "DB_CONNECTION": str(tmp_path / "catalogue.json"),
        "CONFIG": str(_config_path(tmp_path)),
    }
    if accounts_path is not None:
        config["ACCOUNTS_CONNECTION"] = str(accounts_path)
    return create_app(config)


def test_import_data_requires_login(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = application.test_client()

    response = client.get("/import_data")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_import_data_forbidden_for_non_admin(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="bob", role="user")
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "bob"
        sess["role"] = "user"
        sess["auth_generation"] = 0

    response = client.get("/import_data")

    assert response.status_code == 403


def test_import_data_post_forbidden_for_non_admin(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="bob", role="user")
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "bob"
        sess["role"] = "user"
        sess["auth_generation"] = 0
        sess["csrf_token"] = "jeton-de-test"

    response = client.post(
        "/import_data",
        data={
            "csrf_token": "jeton-de-test",
            "file": (io.BytesIO(b"[]"), "export_all.json"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 403


def test_import_data_allowed_for_admin(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="alice", role="admin")
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "alice"
        sess["role"] = "admin"
        sess["auth_generation"] = 0
        sess["csrf_token"] = "jeton-de-test"

    response = client.post(
        "/import_data",
        data={
            "csrf_token": "jeton-de-test",
            "file": (io.BytesIO(b"[]"), "export_all.json"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 302
    assert "/import_data" not in response.headers["Location"]


def test_export_csv_is_written_with_utf8_bom(tmp_path: Path) -> None:
    """Tâche 0.2 : le CSV exporté commence par le BOM utf-8-sig et restitue
    correctement les caractères accentués, pour une ouverture directe dans Excel
    sous Windows sans étape d'import manuel."""
    catalogue_path = tmp_path / "catalogue.json"
    catalogue_session = JsonSession(init_db(str(catalogue_path)))
    catalogue_session.add(
        Application(
            name="Application accentuée éàç",
            rda="Responsable",
            possession=None,
            type_app="cloud",
            hosting="cloud",
            criticite=1,
            disponibilite="1",
            integrite="1",
            confidentialite="1",
            perennite="1",
            score=None,
            answered_questions=0,
            last_evaluation=None,
            responses={},
            comments={},
            evaluator_name=None,
        )
    )
    catalogue_session.commit()
    catalogue_session.close()

    accounts_path = _seed_account(tmp_path, username="bob", role="user")
    application = _create_test_app(tmp_path, accounts_path)
    client = application.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "bob"
        sess["role"] = "user"
        sess["auth_generation"] = 0

    response = client.get("/export_csv")

    assert response.status_code == 200
    body = response.data
    assert body.startswith(b"\xef\xbb\xbf")
    decoded = body.decode("utf-8-sig")
    assert "Application accentuée éàç" in decoded
