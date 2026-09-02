"""Tests du point de contrôle de supervision."""

from pathlib import Path

from flask import Flask

from ADM.app import create_app


def _create_test_app(tmp_path: Path) -> Flask:
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
            "DB_CONNECTION": str(tmp_path / "catalogue.json"),
            "ACCOUNTS_CONNECTION": str(tmp_path / "accounts.json"),
        }
    )


def test_healthz_reports_application_and_persistence_available(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)

    response = application.test_client().get("/healthz")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
    assert response.headers["Cache-Control"] == "no-store"


def test_healthz_reports_unavailable_when_persistence_cannot_be_read(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    (tmp_path / "catalogue.json").write_text("document invalide", encoding="utf-8")

    response = application.test_client().get("/healthz")

    assert response.status_code == 503
    assert response.get_json() == {"status": "unavailable"}


def test_healthz_rejects_post_requests(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)

    response = application.test_client().post("/healthz")

    assert response.status_code == 400
