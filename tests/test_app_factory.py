"""Tests de la fabrique Flask et de son initialisation explicite."""

import importlib
import sys
from pathlib import Path

import pytest


def test_import_has_no_configuration_or_persistence_side_effect(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "catalogue.json"
    monkeypatch.delenv("ADM_SECRET_KEY", raising=False)
    monkeypatch.setenv("ADM_DB_BACKEND", "json")
    monkeypatch.setenv("ADM_DATABASE_URL", str(database_path))
    sys.modules.pop("ADM.app", None)

    module = importlib.import_module("ADM.app")

    assert hasattr(module, "create_app")
    assert not database_path.exists()


def test_create_app_registers_blueprints_and_injects_session_factory(tmp_path: Path) -> None:
    from ADM.app import create_app

    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
            "DB_CONNECTION": str(tmp_path / "catalogue.json"),
        }
    )

    assert set(application.blueprints) == {"auth", "applications", "evaluations", "exports"}
    assert callable(application.extensions["adm_session_factory"])
    assert application.test_client().get("/login").status_code == 200
    assert application.extensions["adm_display_thresholds"].score.warning == 30


def test_create_app_uses_json_database_from_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from ADM.app import create_app

    database_path = tmp_path / "standalone-demo.json"
    monkeypatch.setenv("ADM_DATABASE_URL", str(database_path))

    create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
        }
    )

    assert database_path.exists()
