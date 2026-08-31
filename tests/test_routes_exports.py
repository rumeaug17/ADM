"""Tests de la restriction par rôle de la réimportation totale du catalogue (US6.1)."""

import io
import json
from pathlib import Path

from flask import Flask

from ADM.accounts_json import AccountJsonSession, init_account_db
from ADM.accounts_service import create_account


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
