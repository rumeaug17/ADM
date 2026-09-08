"""Tests du rôle readonly (US6.4) : consultation seule, sans modification possible
(ni application, ni notation, ni configuration)."""

import json
from pathlib import Path

from flask import Flask

from ADM.accounts_json import AccountJsonSession, init_account_db
from ADM.accounts_service import ROLES, create_account
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


def _seed_application(tmp_path: Path, *, name: str = "Application de test") -> Path:
    catalogue_path = tmp_path / "catalogue.json"
    catalogue_session = JsonSession(init_db(str(catalogue_path)))
    catalogue_session.add(
        Application(
            name=name,
            rda="Responsable fictif",
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
    return catalogue_path


def _create_test_app(tmp_path: Path, *, accounts_path: Path, catalogue_path: Path) -> Flask:
    from ADM.app import create_app

    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
            "DB_CONNECTION": str(catalogue_path),
            "ACCOUNTS_CONNECTION": str(accounts_path),
            "CONFIG": str(_config_path(tmp_path)),
        }
    )


def _readonly_session(client: object, *, username: str = "carole") -> None:
    with client.session_transaction() as sess:  # type: ignore[attr-defined]
        sess["logged_in"] = True
        sess["username"] = username
        sess["role"] = "readonly"
        sess["auth_generation"] = 0
        sess["csrf_token"] = "jeton-de-test"


# --- Rôle disponible ---


def test_readonly_is_a_known_role() -> None:
    assert "readonly" in ROLES


def test_create_account_accepts_readonly_role(tmp_path: Path) -> None:
    accounts_path = tmp_path / "accounts.json"
    engine = init_account_db(str(accounts_path))
    accounts_session = AccountJsonSession(engine)

    account = create_account(
        accounts_session, username="carole", password="secret-de-test", role="readonly"
    )
    accounts_session.commit()

    assert account.role == "readonly"


# --- Actions de modification refusées (403) ---


def test_readonly_forbidden_on_add_application_get(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="carole", role="readonly")
    catalogue_path = _seed_application(tmp_path)
    application = _create_test_app(
        tmp_path, accounts_path=accounts_path, catalogue_path=catalogue_path
    )
    client = application.test_client()
    _readonly_session(client)

    response = client.get("/add")

    assert response.status_code == 403


def test_readonly_forbidden_on_add_application_post(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="carole", role="readonly")
    catalogue_path = _seed_application(tmp_path)
    application = _create_test_app(
        tmp_path, accounts_path=accounts_path, catalogue_path=catalogue_path
    )
    client = application.test_client()
    _readonly_session(client)

    response = client.post(
        "/add",
        data={
            "csrf_token": "jeton-de-test",
            "name": "Nouvelle application",
            "rda": "Un responsable",
            "possession": "2024-01-01",
            "type_app": "Interne",
            "hosting": "On prem",
            "criticite": "4",
            "disponibilite": "D1",
            "integrite": "I1",
            "confidentialite": "C1",
            "perennite": "P1",
        },
    )

    assert response.status_code == 403


def test_readonly_forbidden_on_edit_application_get(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="carole", role="readonly")
    catalogue_path = _seed_application(tmp_path)
    application = _create_test_app(
        tmp_path, accounts_path=accounts_path, catalogue_path=catalogue_path
    )
    client = application.test_client()
    _readonly_session(client)

    response = client.get("/edit/Application%20de%20test")

    assert response.status_code == 403


def test_readonly_forbidden_on_edit_application_post(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="carole", role="readonly")
    catalogue_path = _seed_application(tmp_path)
    application = _create_test_app(
        tmp_path, accounts_path=accounts_path, catalogue_path=catalogue_path
    )
    client = application.test_client()
    _readonly_session(client)

    response = client.post(
        "/edit/Application%20de%20test",
        data={
            "csrf_token": "jeton-de-test",
            "rda": "Autre responsable",
            "possession": "2024-01-01",
            "type_app": "Interne",
            "hosting": "On prem",
            "criticite": "4",
            "disponibilite": "D1",
            "integrite": "I1",
            "confidentialite": "C1",
            "perennite": "P1",
        },
    )

    assert response.status_code == 403


def test_readonly_forbidden_on_delete_application(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="carole", role="readonly")
    catalogue_path = _seed_application(tmp_path)
    application = _create_test_app(
        tmp_path, accounts_path=accounts_path, catalogue_path=catalogue_path
    )
    client = application.test_client()
    _readonly_session(client)

    response = client.post("/delete/Application%20de%20test", data={"csrf_token": "jeton-de-test"})

    assert response.status_code == 403


def test_readonly_forbidden_on_score_application_get(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="carole", role="readonly")
    catalogue_path = _seed_application(tmp_path)
    application = _create_test_app(
        tmp_path, accounts_path=accounts_path, catalogue_path=catalogue_path
    )
    client = application.test_client()
    _readonly_session(client)

    response = client.get("/score/Application%20de%20test")

    assert response.status_code == 403


def test_readonly_forbidden_on_score_application_post(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="carole", role="readonly")
    catalogue_path = _seed_application(tmp_path)
    application = _create_test_app(
        tmp_path, accounts_path=accounts_path, catalogue_path=catalogue_path
    )
    client = application.test_client()
    _readonly_session(client)

    response = client.post(
        "/score/Application%20de%20test",
        data={"csrf_token": "jeton-de-test", "save_draft": "true"},
    )

    assert response.status_code == 403


def test_readonly_forbidden_on_reset_evaluation(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="carole", role="readonly")
    catalogue_path = _seed_application(tmp_path)
    application = _create_test_app(
        tmp_path, accounts_path=accounts_path, catalogue_path=catalogue_path
    )
    client = application.test_client()
    _readonly_session(client)

    response = client.post("/reset/Application%20de%20test", data={"csrf_token": "jeton-de-test"})

    assert response.status_code == 403


def test_readonly_forbidden_on_reevaluate_all(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="carole", role="readonly")
    catalogue_path = _seed_application(tmp_path)
    application = _create_test_app(
        tmp_path, accounts_path=accounts_path, catalogue_path=catalogue_path
    )
    client = application.test_client()
    _readonly_session(client)

    response = client.post("/reevaluate_all", data={"csrf_token": "jeton-de-test"})

    assert response.status_code == 403


# --- Accès en lecture autorisés ---


def test_readonly_can_view_index(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="carole", role="readonly")
    catalogue_path = _seed_application(tmp_path)
    application = _create_test_app(
        tmp_path, accounts_path=accounts_path, catalogue_path=catalogue_path
    )
    client = application.test_client()
    _readonly_session(client)

    response = client.get("/")

    assert response.status_code == 200


def test_readonly_can_view_resume(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="carole", role="readonly")
    catalogue_path = _seed_application(tmp_path)
    application = _create_test_app(
        tmp_path, accounts_path=accounts_path, catalogue_path=catalogue_path
    )
    client = application.test_client()
    _readonly_session(client)

    response = client.get("/resume/Application%20de%20test")

    assert response.status_code == 200


def test_readonly_can_view_synthese(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="carole", role="readonly")
    catalogue_path = _seed_application(tmp_path)
    application = _create_test_app(
        tmp_path, accounts_path=accounts_path, catalogue_path=catalogue_path
    )
    client = application.test_client()
    _readonly_session(client)

    response = client.get("/synthese")

    assert response.status_code == 200


def test_readonly_can_export_csv(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="carole", role="readonly")
    catalogue_path = _seed_application(tmp_path)
    application = _create_test_app(
        tmp_path, accounts_path=accounts_path, catalogue_path=catalogue_path
    )
    client = application.test_client()
    _readonly_session(client)

    response = client.get("/export_csv")

    assert response.status_code == 200


def test_readonly_can_export_all(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="carole", role="readonly")
    catalogue_path = _seed_application(tmp_path)
    application = _create_test_app(
        tmp_path, accounts_path=accounts_path, catalogue_path=catalogue_path
    )
    client = application.test_client()
    _readonly_session(client)

    response = client.get("/export_all")

    assert response.status_code == 200


# --- Routes réservées à l'admin : toujours refusées pour readonly ---


def test_readonly_forbidden_on_settings(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="carole", role="readonly")
    catalogue_path = _seed_application(tmp_path)
    application = _create_test_app(
        tmp_path, accounts_path=accounts_path, catalogue_path=catalogue_path
    )
    client = application.test_client()
    _readonly_session(client)

    response = client.get("/settings")

    assert response.status_code == 403


def test_readonly_forbidden_on_accounts_list(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="carole", role="readonly")
    catalogue_path = _seed_application(tmp_path)
    application = _create_test_app(
        tmp_path, accounts_path=accounts_path, catalogue_path=catalogue_path
    )
    client = application.test_client()
    _readonly_session(client)

    response = client.get("/accounts")

    assert response.status_code == 403


def test_readonly_forbidden_on_import_data(tmp_path: Path) -> None:
    accounts_path = _seed_account(tmp_path, username="carole", role="readonly")
    catalogue_path = _seed_application(tmp_path)
    application = _create_test_app(
        tmp_path, accounts_path=accounts_path, catalogue_path=catalogue_path
    )
    client = application.test_client()
    _readonly_session(client)

    response = client.get("/import_data")

    assert response.status_code == 403
