"""Tests de la page de gestion des questions (US4.3)."""

import json
from pathlib import Path

import pytest
from flask import Flask
from flask.testing import FlaskClient

from ADM.accounts_json import AccountJsonSession, init_account_db
from ADM.accounts_service import create_account

SAMPLE_QUESTIONS = {
    "Architecture": {
        "api": {
            "label": "Utilise-t-on des API standardisées ?",
            "type": "select",
            "weight": 2,
            "options": [
                {"value": "Oui", "score": 0},
                {"value": "Non", "score": 3},
                {"value": "Non applicable", "score": None},
            ],
            "app_types": ["Interne", "Editeur", "Open source"],
            "hosting_types": ["On prem", "Hybride", "Cloud", "SaaS"],
        }
    },
    "Sécurité": {
        "sauvegarde": {
            "label": "Y a-t-il une sauvegarde ?",
            "type": "select",
            "weight": 1,
            "options": [{"value": "Oui", "score": 0}, {"value": "Non", "score": 3}],
            "app_types": ["Interne", "Editeur", "Open source"],
            "hosting_types": ["On prem", "Hybride", "Cloud", "SaaS"],
        }
    },
}

SAMPLE_INFO_TEXTS = {"api": "Aide existante pour api."}


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


def _seed_admin_account(tmp_path: Path, *, username: str = "alice", role: str = "admin") -> Path:
    accounts_path = tmp_path / "accounts.json"
    engine = init_account_db(str(accounts_path))
    accounts_session = AccountJsonSession(engine)
    create_account(accounts_session, username=username, password="secret-de-test", role=role)
    accounts_session.commit()
    accounts_session.close()
    return accounts_path


def _create_test_app(tmp_path: Path, *, role: str = "admin") -> Flask:
    from ADM.app import create_app

    questions_path = tmp_path / "questions.json"
    questions_path.write_text(json.dumps(SAMPLE_QUESTIONS), encoding="utf-8")
    info_texts_path = tmp_path / "info_texts.json"
    info_texts_path.write_text(json.dumps(SAMPLE_INFO_TEXTS), encoding="utf-8")
    accounts_path = _seed_admin_account(tmp_path, role=role)

    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
            "DB_CONNECTION": str(tmp_path / "catalogue.json"),
            "CONFIG": str(_config_path(tmp_path)),
            "ACCOUNTS_CONNECTION": str(accounts_path),
            "QUESTIONS_PATH": str(questions_path),
            "INFO_TEXTS_PATH": str(info_texts_path),
        }
    )


def _logged_in_client(application: Flask, *, role: str = "admin") -> FlaskClient:
    client = application.test_client()
    with client.session_transaction() as user_session:
        user_session["logged_in"] = True
        user_session["username"] = "alice"
        user_session["role"] = role
        user_session["auth_generation"] = 0
        user_session["csrf_token"] = "jeton-de-test"
    return client


def test_list_questions_requires_login(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)

    response = application.test_client().get("/settings/questions")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_list_questions_rejects_non_admin_role(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path, role="user")
    client = _logged_in_client(application, role="user")

    response = client.get("/settings/questions")

    assert response.status_code == 403


def test_list_questions_renders_existing_questions(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    response = client.get("/settings/questions")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Utilise-t-on des API standardisées ?" in html
    assert "Architecture" in html
    assert "Sécurité" in html


def test_add_question_form_renders_for_admin(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    response = client.get("/settings/questions/add")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'name="category"' in html
    assert 'name="key"' in html


def test_edit_question_form_renders_prefilled_for_admin(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    response = client.get("/settings/questions/edit/Architecture/api")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Utilise-t-on des API standardisées ?" in html
    assert "Aide existante pour api." in html


def test_edit_question_rejects_invalid_category(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    response = client.post(
        "/settings/questions/edit/Architecture/api",
        data={
            "csrf_token": "jeton-de-test",
            "category": "Inexistante",
            "label": "Libellé ?",
            "weight": "1",
            "option_value": "Oui",
            "option_score": "0",
            "app_types": "Interne",
            "hosting_types": "Cloud",
        },
    )

    assert response.status_code == 400
    assert application.extensions["adm_questions"]["Architecture"]["api"]["label"] != "Libellé ?"


def test_edit_question_rejects_key_collision_when_moving_category(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)
    # On renomme d'abord "sauvegarde" en "api" côté Sécurité pour provoquer la collision.
    questions_path = Path(application.config["QUESTIONS_PATH"])
    saved = json.loads(questions_path.read_text(encoding="utf-8"))
    saved["Sécurité"]["api"] = saved["Sécurité"].pop("sauvegarde")
    questions_path.write_text(json.dumps(saved), encoding="utf-8")
    from ADM.schemas import parse_questions

    application.extensions["adm_questions"] = parse_questions(saved)

    response = client.post(
        "/settings/questions/edit/Architecture/api",
        data={
            "csrf_token": "jeton-de-test",
            "category": "Sécurité",
            "label": "Libellé ?",
            "weight": "1",
            "option_value": "Oui",
            "option_score": "0",
            "app_types": "Interne",
            "hosting_types": "Cloud",
        },
    )

    assert response.status_code == 400


def test_add_question_reports_persistence_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    def _boom(*args: object, **kwargs: object) -> None:
        raise ValueError("disque plein simulé")

    monkeypatch.setattr("ADM.routes.save_questions", _boom)

    response = client.post(
        "/settings/questions/add",
        data={
            "csrf_token": "jeton-de-test",
            "category": "Architecture",
            "key": "nouvelle",
            "label": "Nouvelle question ?",
            "weight": "1",
            "option_value": "Oui",
            "option_score": "0",
            "app_types": "Interne",
            "hosting_types": "Cloud",
        },
    )

    assert response.status_code == 409
    assert "nouvelle" not in application.extensions["adm_questions"]["Architecture"]


def test_edit_question_reports_persistence_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    def _boom(*args: object, **kwargs: object) -> None:
        raise ValueError("disque plein simulé")

    monkeypatch.setattr("ADM.routes.save_questions", _boom)

    response = client.post(
        "/settings/questions/edit/Architecture/api",
        data={
            "csrf_token": "jeton-de-test",
            "category": "Architecture",
            "label": "Libellé ?",
            "weight": "1",
            "option_value": "Oui",
            "option_score": "0",
            "app_types": "Interne",
            "hosting_types": "Cloud",
        },
    )

    assert response.status_code == 409
    assert application.extensions["adm_questions"]["Architecture"]["api"]["label"] != "Libellé ?"


def test_delete_question_reports_persistence_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    def _boom(*args: object, **kwargs: object) -> None:
        raise ValueError("disque plein simulé")

    monkeypatch.setattr("ADM.routes.save_questions", _boom)

    response = client.post(
        "/settings/questions/delete/Architecture/api",
        data={"csrf_token": "jeton-de-test"},
    )

    assert response.status_code == 302
    assert "api" in application.extensions["adm_questions"]["Architecture"]


def test_add_question_requires_csrf_token(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    response = client.post(
        "/settings/questions/add",
        data={
            "category": "Architecture",
            "key": "nouvelle",
            "label": "Nouvelle question ?",
            "weight": "1",
            "option_value": "Oui",
            "option_score": "0",
            "app_types": "Interne",
            "hosting_types": "Cloud",
        },
    )

    assert response.status_code == 400


def test_add_question_persists_reloads_and_saves_help_text(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)
    questions_path = Path(application.config["QUESTIONS_PATH"])
    info_texts_path = Path(application.config["INFO_TEXTS_PATH"])

    response = client.post(
        "/settings/questions/add",
        data={
            "csrf_token": "jeton-de-test",
            "category": "Architecture",
            "key": "nouvelle",
            "label": "Nouvelle question ?",
            "weight": "3",
            "option_value": ["Oui", "Non"],
            "option_score": ["0", "3"],
            "app_types": "Interne",
            "hosting_types": "Cloud",
            "help_text": "Aide de la nouvelle question.",
        },
    )

    assert response.status_code == 302
    saved = json.loads(questions_path.read_text(encoding="utf-8"))
    assert saved["Architecture"]["nouvelle"]["weight"] == 3
    saved_help = json.loads(info_texts_path.read_text(encoding="utf-8"))
    assert saved_help["nouvelle"] == "Aide de la nouvelle question."
    # rechargé à chaud, sans redémarrage (comme les seuils de /settings, US4.2)
    assert "nouvelle" in application.extensions["adm_questions"]["Architecture"]
    assert "nouvelle" in application.extensions["adm_categories"]["Architecture"]


def test_add_question_rejects_unknown_category(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    response = client.post(
        "/settings/questions/add",
        data={
            "csrf_token": "jeton-de-test",
            "category": "Inexistante",
            "key": "nouvelle",
            "label": "Nouvelle question ?",
            "weight": "1",
            "option_value": "Oui",
            "option_score": "0",
            "app_types": "Interne",
            "hosting_types": "Cloud",
        },
    )

    assert response.status_code == 400
    assert "nouvelle" not in application.extensions["adm_questions"].get("Architecture", {})


def test_add_question_rejects_duplicate_key(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    response = client.post(
        "/settings/questions/add",
        data={
            "csrf_token": "jeton-de-test",
            "category": "Architecture",
            "key": "api",
            "label": "Doublon ?",
            "weight": "1",
            "option_value": "Oui",
            "option_score": "0",
            "app_types": "Interne",
            "hosting_types": "Cloud",
        },
    )

    assert response.status_code == 400


def test_edit_question_updates_fields_and_help_text(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)
    questions_path = Path(application.config["QUESTIONS_PATH"])
    info_texts_path = Path(application.config["INFO_TEXTS_PATH"])

    response = client.post(
        "/settings/questions/edit/Architecture/api",
        data={
            "csrf_token": "jeton-de-test",
            "category": "Architecture",
            "label": "Libellé modifié ?",
            "weight": "5",
            "option_value": ["Oui", "Non"],
            "option_score": ["0", "3"],
            "app_types": "Interne",
            "hosting_types": "Cloud",
            "help_text": "Aide modifiée.",
        },
    )

    assert response.status_code == 302
    saved = json.loads(questions_path.read_text(encoding="utf-8"))
    assert saved["Architecture"]["api"]["weight"] == 5
    assert saved["Architecture"]["api"]["label"] == "Libellé modifié ?"
    saved_help = json.loads(info_texts_path.read_text(encoding="utf-8"))
    assert saved_help["api"] == "Aide modifiée."
    assert application.extensions["adm_questions"]["Architecture"]["api"]["weight"] == 5


def test_edit_question_can_move_to_another_existing_category(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    response = client.post(
        "/settings/questions/edit/Architecture/api",
        data={
            "csrf_token": "jeton-de-test",
            "category": "Sécurité",
            "label": "Libellé conservé ?",
            "weight": "1",
            "option_value": "Oui",
            "option_score": "0",
            "app_types": "Interne",
            "hosting_types": "Cloud",
        },
    )

    assert response.status_code == 302
    assert "api" not in application.extensions["adm_questions"]["Architecture"]
    assert "api" in application.extensions["adm_questions"]["Sécurité"]


def test_edit_question_returns_404_for_unknown_question(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    response = client.get("/settings/questions/edit/Architecture/inconnue")

    assert response.status_code == 404


def test_delete_question_removes_it_and_hides_it_from_scoring(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)
    questions_path = Path(application.config["QUESTIONS_PATH"])
    info_texts_path = Path(application.config["INFO_TEXTS_PATH"])

    response = client.post(
        "/settings/questions/delete/Architecture/api",
        data={"csrf_token": "jeton-de-test"},
    )

    assert response.status_code == 302
    saved = json.loads(questions_path.read_text(encoding="utf-8"))
    assert "api" not in saved["Architecture"]
    saved_help = json.loads(info_texts_path.read_text(encoding="utf-8"))
    assert "api" not in saved_help
    assert "api" not in application.extensions["adm_questions"]["Architecture"]


def test_delete_question_rejects_unknown_question(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    response = client.post(
        "/settings/questions/delete/Architecture/inconnue",
        data={"csrf_token": "jeton-de-test"},
    )

    assert response.status_code == 302  # redirige avec un message d'erreur, catalogue inchangé
    assert "api" in application.extensions["adm_questions"]["Architecture"]


def test_info_texts_route_serves_persisted_content(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application, role="user")

    response = client.get("/info_texts.json")

    assert response.status_code == 200
    assert response.get_json() == SAMPLE_INFO_TEXTS


def test_info_texts_route_reflects_updates_without_restart(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    admin_client = _logged_in_client(application)

    admin_client.post(
        "/settings/questions/edit/Architecture/api",
        data={
            "csrf_token": "jeton-de-test",
            "category": "Architecture",
            "label": "Utilise-t-on des API standardisées ?",
            "weight": "2",
            "option_value": "Oui",
            "option_score": "0",
            "app_types": "Interne",
            "hosting_types": "Cloud",
            "help_text": "Nouvelle aide en ligne.",
        },
    )

    response = admin_client.get("/info_texts.json")

    assert response.get_json()["api"] == "Nouvelle aide en ligne."


@pytest.mark.parametrize(
    "path",
    [
        "/settings/questions/add",
        "/settings/questions/edit/Architecture/api",
    ],
)
def test_question_forms_reject_non_admin_role(tmp_path: Path, path: str) -> None:
    application = _create_test_app(tmp_path, role="user")
    client = _logged_in_client(application, role="user")

    response = client.get(path)

    assert response.status_code == 403
