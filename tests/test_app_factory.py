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
    from ADM.services import RadarChartCache

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
        "supervision",
    }

    assert callable(application.extensions["adm_session_factory"])
    assert application.test_client().get("/login").status_code == 200
    assert application.extensions["adm_display_thresholds"].score.warning == 30
    assert isinstance(application.extensions["adm_radar_chart_cache"], RadarChartCache)


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


def test_create_app_uses_sqlite_for_catalogue_and_accounts(tmp_path: Path) -> None:
    from ADM.app import create_app
    from ADM.database import Account, Application

    database_path = tmp_path / "adm.db"
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "sqlite",
            "DB_CONNECTION": f"sqlite:///{database_path.as_posix()}",
        }
    )

    catalogue_session = application.extensions["adm_session_factory"]()
    account_session = application.extensions["adm_account_session_factory"]()
    try:
        assert catalogue_session.query(Application).all() == []
        assert account_session.query(Account).all() == []
    finally:
        catalogue_session.close()
        account_session.close()

    assert database_path.exists()


def test_create_app_requires_database_url_for_sqlite(monkeypatch: pytest.MonkeyPatch) -> None:
    from ADM.app import create_app

    monkeypatch.delenv("ADM_DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="SQLite"):
        create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "cle-factice-reservee-aux-tests",
                "DB_BACKEND": "sqlite",
            }
        )


def test_create_app_uses_packaged_resources(tmp_path: Path) -> None:
    import ADM.app as app_module

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


def test_packaged_config_uses_safe_defaults_when_file_is_missing(tmp_path: Path) -> None:
    from ADM.app import _load_app_config

    missing_config = tmp_path / "missing-config.json"
    config = _load_app_config(missing_config, use_defaults_when_missing=True)

    assert config.db_backend == "json"
    assert config.display_thresholds.score.warning == 30
    assert not missing_config.exists()


def test_explicit_missing_config_is_rejected(tmp_path: Path) -> None:
    from ADM.app import _load_app_config

    with pytest.raises(FileNotFoundError):
        _load_app_config(
            tmp_path / "missing-config.json",
            use_defaults_when_missing=False,
        )


def test_template_values_reads_version_file_when_present(tmp_path: Path) -> None:
    """Cas nominal de `template_values` (context processor de
    `_register_web_components`) : le contenu de `version.txt` est affiché tel
    quel dans le pied de page (voir Tâche 0.3 du backlog, `INSTALL.md`,
    section 4)."""
    from ADM.app import create_app

    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
            "DB_CONNECTION": str(tmp_path / "catalogue.json"),
        }
    )
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "version.txt").write_text("v9.9.9-test\n", encoding="utf-8")
    application.static_folder = str(static_dir)

    response = application.test_client().get("/login")

    assert response.status_code == 200
    assert b"v9.9.9-test" in response.data


def test_template_values_falls_back_to_placeholder_version_when_missing(
    tmp_path: Path,
) -> None:
    """`template_values` doit retomber sur un identifiant de version par défaut
    lorsque `version.txt` est absent du dossier statique -- cas normal sur un
    poste de développement où ce fichier n'est généré que par le job `build`
    de la CI (voir `.gitlab-ci.yml` et `.github/workflows/release.yml`).

    Le dossier statique est ici un `tmp_path` vide plutôt que le dossier
    empaqueté du dépôt : la couverture de cette branche ne doit pas dépendre
    de la présence accidentelle d'un `version.txt` généré par un build local
    antérieur (voir Tâche 3.10 du backlog).
    """
    from ADM.app import create_app

    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
            "DB_CONNECTION": str(tmp_path / "catalogue.json"),
        }
    )
    application.static_folder = str(tmp_path)

    response = application.test_client().get("/login")

    assert response.status_code == 200
    assert b"v0.0.0" in response.data


def test_create_app_seeds_config_from_env_when_absent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ADM_CONFIG_PATH doit permettre de stocker config.json hors du paquet installé,
    afin qu'une réinstallation du wheel (mise à jour) n'efface pas les seuils
    personnalisés depuis /settings (voir INSTALL.md, section 12)."""
    from ADM.app import create_app

    config_path = tmp_path / "persistent" / "config.json"
    monkeypatch.setenv("ADM_CONFIG_PATH", str(config_path))

    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
            "DB_CONNECTION": str(tmp_path / "catalogue.json"),
            "ACCOUNTS_CONNECTION": str(tmp_path / "accounts.json"),
        }
    )

    assert config_path.exists()
    assert Path(application.config["CONFIG"]) == config_path
    assert application.extensions["adm_display_thresholds"].score.warning == 30


def test_create_app_seeds_questions_and_info_texts_from_env_when_absent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ADM_QUESTIONS_PATH/ADM_INFO_TEXTS_PATH doivent permettre de stocker le
    questionnaire et son aide en ligne hors du paquet installé, afin qu'une
    réinstallation du wheel n'efface pas les questions ajoutées ou modifiées
    depuis /settings/questions (US4.3, même raisonnement que ADM_CONFIG_PATH,
    voir INSTALL.md section 12)."""
    from ADM.app import create_app

    questions_path = tmp_path / "persistent" / "questions.json"
    info_texts_path = tmp_path / "persistent" / "info_texts.json"
    monkeypatch.setenv("ADM_QUESTIONS_PATH", str(questions_path))
    monkeypatch.setenv("ADM_INFO_TEXTS_PATH", str(info_texts_path))

    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
            "DB_CONNECTION": str(tmp_path / "catalogue.json"),
            "ACCOUNTS_CONNECTION": str(tmp_path / "accounts.json"),
        }
    )

    assert questions_path.exists()
    assert info_texts_path.exists()
    assert Path(application.config["QUESTIONS_PATH"]) == questions_path
    assert Path(application.config["INFO_TEXTS_PATH"]) == info_texts_path
    assert application.extensions["adm_questions"]
