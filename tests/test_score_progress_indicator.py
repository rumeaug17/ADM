"""Tâche 4.8 du backlog : formulaire d'évaluation long sans repère de progression.

``score.html`` empilait toutes les catégories de questions verticalement,
sans sommaire ni indicateur de progression (« X/Y questions répondues »), ni
bouton « enregistrer » persistant en bas d'écran pour un formulaire
potentiellement très long.

Ces tests vérifient qu'un sommaire d'ancres par catégorie, un indicateur de
progression, et un conteneur d'actions persistant (``position: sticky``)
sont bien présents dans le gabarit et dans la page rendue."""

import json
from pathlib import Path

from flask import Flask
from flask.testing import FlaskClient

from ADM.accounts_json import AccountJsonSession, init_account_db
from ADM.accounts_service import create_account
from ADM.database import Application
from ADM.database_json import JsonSession, init_db
from ADM.scoring import filter_questions_by_type

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = PROJECT_ROOT / "src" / "ADM" / "resources" / "templates"
STATIC = PROJECT_ROOT / "src" / "ADM" / "resources" / "static"


def _create_test_app(tmp_path: Path) -> Flask:
    from ADM.app import create_app

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
    catalogue_path = tmp_path / "catalogue.json"
    catalogue_session = JsonSession(init_db(str(catalogue_path)))
    catalogue_session.add(
        Application(
            name="Application de test",
            rda="Responsable fictif",
            possession=None,
            type_app="Interne",
            hosting="On prem",
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

    accounts_path = tmp_path / "accounts.json"
    accounts_session = AccountJsonSession(init_account_db(str(accounts_path)))
    create_account(
        accounts_session,
        username="utilisateur-test",
        password="secret-de-test",
        role="user",
    )
    accounts_session.commit()
    accounts_session.close()

    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cle-factice-reservee-aux-tests",
            "DB_BACKEND": "json",
            "DB_CONNECTION": str(catalogue_path),
            "ACCOUNTS_CONNECTION": str(accounts_path),
            "CONFIG": str(config_path),
        }
    )


def _logged_in_client(application: Flask) -> FlaskClient:
    client = application.test_client()
    with client.session_transaction() as user_session:
        user_session["logged_in"] = True
        user_session["username"] = "utilisateur-test"
        user_session["role"] = "user"
        user_session["auth_generation"] = 0
    return client


def test_score_template_has_progress_indicator_and_category_summary() -> None:
    score_html = (TEMPLATES / "score.html").read_text(encoding="utf-8")
    # Indicateur de progression (barre + libellé "X/Y questions répondues").
    assert 'id="evaluationProgressBar"' in score_html
    assert 'role="progressbar"' in score_html
    assert "questions répondues" in score_html
    # Sommaire d'ancres par catégorie.
    assert 'href="#category-' in score_html
    assert 'id="category-{{ loop.index }}"' in score_html
    # Bouton d'actions persistant en bas d'écran. Le style ".eval-actions"
    # (position: sticky) a été déplacé depuis ce gabarit vers la feuille de
    # style partagée static/css/app.css lors de la Phase 1 de US4.1 (voir
    # docs/UI_MODERNIZATION_PROPOSAL.md) : seule la classe reste dans le
    # gabarit, la règle CSS elle-même se vérifie désormais dans app.css.
    assert "eval-actions" in score_html
    app_css = (STATIC / "css" / "app.css").read_text(encoding="utf-8")
    assert ".eval-actions" in app_css
    assert "position: sticky" in app_css


def test_score_page_renders_progress_bar_and_category_anchors(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)
    # Le formulaire n'affiche que les questions applicables au type/hébergement
    # de l'application (`filter_questions_by_type`, appelé par la route GET).
    questions = filter_questions_by_type(
        application.extensions["adm_questions"], "Interne", "On prem"
    )

    score_html = client.get("/score/Application%20de%20test").get_data(as_text=True)

    assert 'id="evaluationProgressBar"' in score_html
    # Libellé par défaut avant toute exécution du script de progression côté
    # client (aucune réponse enregistrée pour cette application de test).
    assert "0/0 questions répondues" in score_html
    # Une ancre de sommaire par catégorie du questionnaire filtré.
    for index in range(1, len(questions) + 1):
        assert f'id="category-{index}"' in score_html
        assert f'href="#category-{index}"' in score_html


def test_score_page_question_selects_expose_progress_data_attributes(tmp_path: Path) -> None:
    """Chaque question porte un attribut ``data-question``/``data-answered``
    exploité par le script de progression côté client."""
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)
    questions = filter_questions_by_type(
        application.extensions["adm_questions"], "Interne", "On prem"
    )
    total_questions = sum(len(category_questions) for category_questions in questions.values())

    score_html = client.get("/score/Application%20de%20test").get_data(as_text=True)

    assert score_html.count("data-question=") == total_questions
    # Aucune réponse enregistrée pour cette application de test : toutes les
    # questions démarrent comme non répondues.
    assert score_html.count('data-answered="0"') == total_questions
    assert 'data-answered="1"' not in score_html


def test_score_page_marks_already_saved_response_as_answered(tmp_path: Path) -> None:
    """Une réponse déjà enregistrée (brouillon ou évaluation précédente) doit
    être comptée dans l'indicateur de progression dès le chargement de la
    page, sans attendre une interaction de l'utilisateur."""
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    session_factory = application.extensions["adm_session_factory"]
    session_db = session_factory()
    try:
        app_item = session_db.query(Application).filter_by(name="Application de test").first()
        assert app_item is not None
        app_item.responses = {"api": "Oui uniquement"}
        session_db.commit()
    finally:
        session_db.close()

    score_html = client.get("/score/Application%20de%20test").get_data(as_text=True)

    assert 'data-question="api" data-answered="1"' in score_html
