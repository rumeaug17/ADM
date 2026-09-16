"""Tâche 4.6 du backlog : tableau du catalogue non responsive.

Avant cette correction, le tableau de ``/`` (11 colonnes, ``table-bordered``)
n'était pas enveloppé dans ``table-responsive`` : sur mobile/tablette, il
devenait illisible faute de défilement horizontal contrôlé. Les boutons
d'action (évaluer/réinitialiser/modifier/supprimer) n'étaient par ailleurs
représentés que par un émoji, avec pour seule explication une infobulle au
survol — absente au toucher sur mobile et non fiable pour les lecteurs
d'écran.

Ces tests vérifient que le tableau est enveloppé dans un conteneur
``table-responsive`` (défilement horizontal contrôlé) et que chacun des
boutons d'action porte un ``aria-label`` explicite, en plus du ``title``
existant."""

import json
from pathlib import Path

from flask import Flask
from flask.testing import FlaskClient

from ADM.accounts_json import AccountJsonSession, init_account_db
from ADM.accounts_service import create_account
from ADM.database import Application
from ADM.database_json import JsonSession, init_db

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = PROJECT_ROOT / "src" / "ADM" / "resources" / "templates"


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


def test_catalogue_table_is_wrapped_in_table_responsive() -> None:
    """Le tableau de ``index.html`` doit être enveloppé dans un conteneur
    ``table-responsive`` pour offrir un défilement horizontal contrôlé sur
    petit écran, plutôt que des colonnes tassées."""
    index_html = (TEMPLATES / "index.html").read_text(encoding="utf-8")
    assert '<div class="table-responsive">' in index_html
    assert index_html.index('<div class="table-responsive">') < index_html.index(
        '<table class="table table-bordered text-center">'
    )


def test_catalogue_table_renders_inside_table_responsive_wrapper(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    index_html = client.get("/").get_data(as_text=True)

    assert '<div class="table-responsive">' in index_html
    assert index_html.index('<div class="table-responsive">') < index_html.index("<table")


def test_catalogue_action_buttons_have_accessible_labels() -> None:
    """Les 4 boutons d'action (évaluer/réinitialiser/modifier/supprimer) ne
    sont représentés que par un émoji : chacun doit porter un ``aria-label``
    explicite en complément du ``title`` (infobulle absente au toucher sur
    mobile).

    Phase 4 (US4.1) : ce balisage a été factorisé de ``index.html`` vers
    ``_application_row.html`` (partiel réutilisé par le tableau complet et par
    la réponse htmx de ``/reset/<name>``), d'où la lecture de ce nouveau
    fichier plutôt que d'``index.html`` — même précédent que l'adaptation de
    ``test_help_widget.py``/``test_score_progress_indicator.py`` en Phase 1."""
    row_html = (TEMPLATES / "_application_row.html").read_text(encoding="utf-8")
    for label in (
        "Évaluer l'application",
        "Réinitialiser l'évaluation",
        "Modifier l'application",
        "Supprimer l'application",
    ):
        assert f'aria-label="{label}"' in row_html, label


def test_catalogue_action_buttons_render_with_accessible_labels(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    index_html = client.get("/").get_data(as_text=True)

    for label in (
        "Évaluer l'application",
        "Réinitialiser l'évaluation",
        "Modifier l'application",
        "Supprimer l'application",
    ):
        assert f'aria-label="{label}"' in index_html, label
