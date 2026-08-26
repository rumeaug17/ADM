"""Tests de la restriction par rôle de la réimportation totale du catalogue (US6.1)."""

import io
import json
from pathlib import Path

from flask import Flask


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


def _create_test_app(tmp_path: Path) -> Flask:
    from ADM.app import create_app

    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
            "DB_CONNECTION": str(tmp_path / "catalogue.json"),
            "CONFIG": str(_config_path(tmp_path)),
        }
    )


def test_import_data_requires_login(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = application.test_client()

    response = client.get("/import_data")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_import_data_forbidden_for_non_admin(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = application.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["username"] = "bob"
        sess["role"] = "user"

    response = client.get("/import_data")

    assert response.status_code == 403


def test_import_data_post_forbidden_for_non_admin(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
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
    application = _create_test_app(tmp_path)
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
