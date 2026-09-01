"""Tests de la fabrique Flask et de son initialisation explicite."""

import importlib
import sys
from pathlib import Path

import pytest


def test_import_has_no_configuration_or_persistence_side_effect(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """L'import du module ne doit ni ouvrir de fichier, ni préparer de connexion.

    ``ADM.database_json`` et ``ADM.accounts_json`` ne sont importés que dans le
    corps de ``create_app`` (voir ``ADM.app``), jamais au niveau module : les
    retirer de ``sys.modules`` puis vérifier leur absence après le seul import de
    ``ADM.app`` prouve qu'aucune initialisation de backend (fichier ou connexion)
    n'a pu se produire, indépendamment de l'ordre d'exécution des autres tests.
    """
    database_path = tmp_path / "catalogue.json"
    monkeypatch.delenv("ADM_SECRET_KEY", raising=False)
    monkeypatch.setenv("ADM_DB_BACKEND", "json")
    monkeypatch.setenv("ADM_DATABASE_URL", str(database_path))
    sys.modules.pop("ADM.app", None)
    sys.modules.pop("ADM.database_json", None)
    sys.modules.pop("ADM.accounts_json", None)

    module = importlib.import_module("ADM.app")

    assert hasattr(module, "create_app")
    assert list(tmp_path.iterdir()) == []
    assert "ADM.database_json" not in sys.modules
    assert "ADM.accounts_json" not in sys.modules


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

    assert set(application.blueprints) == {
        "auth",
        "applications",
        "evaluations",
        "exports",
        "settings",
        "accounts",
    }

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


def test_create_app_wires_local_auth_provider_by_default(tmp_path: Path) -> None:
    from ADM.app import create_app
    from ADM.auth_providers import LocalAuthProvider

    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
            "DB_CONNECTION": str(tmp_path / "catalogue.json"),
            "ACCOUNTS_CONNECTION": str(tmp_path / "accounts.json"),
        }
    )

    assert isinstance(application.extensions["adm_auth_provider"], LocalAuthProvider)
    assert callable(application.extensions["adm_account_session_factory"])


def test_create_app_uses_packaged_resources_outside_source_checkout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import ADM.app as app_module

    monkeypatch.setattr(app_module, "PROJECT_ROOT", tmp_path / "installation")
    application = app_module.create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
            "DB_CONNECTION": str(tmp_path / "catalogue.json"),
            "ACCOUNTS_CONNECTION": str(tmp_path / "accounts.json"),
        }
    )

    assert Path(application.config["CONFIG"]) == app_module.PACKAGE_RESOURCES / "config.json"
    assert Path(application.static_folder or "") == app_module.PACKAGE_RESOURCES / "static"
    assert application.test_client().get("/login").status_code == 200
