"""Tâche 4.9 du backlog : image du radar chart non responsive dans ``resume.html``.

L'image du graphique radar (encodée en base64) est affichée avec la classe
Bootstrap ``img-fluid`` dans ``index.html`` (modale radar) et ``synthese.html``,
mais pas dans ``resume.html`` : sans cette classe, l'image conserve sa taille
naturelle et peut déborder de sa carte sur petit écran.

Ces tests vérifient que l'image du radar de ``resume.html`` porte elle aussi
la classe ``img-fluid``."""

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


def test_resume_radar_image_has_img_fluid_class() -> None:
    """Le gabarit ``resume.html`` doit donner la classe ``img-fluid`` à
    l'image du radar, comme le fait déjà ``index.html`` pour la modale radar
    et ``synthese.html`` pour le graphique comparatif.

    Phase 5 (US4.1) : l'image gagne aussi ``chart-surface`` (voir app.css),
    qui l'encadre d'une plaque blanche en thème sombre — sans cette classe,
    le graphique matplotlib (toujours rendu sur fond blanc) flottait en
    rectangle brut sur la carte sombre qui le contient."""
    resume_html = (TEMPLATES / "resume.html").read_text(encoding="utf-8")
    assert 'src="data:image/png;base64,{{ radar_chart }}"' in resume_html
    assert (
        '<img src="data:image/png;base64,{{ radar_chart }}" alt="Radar Chart" class="img-fluid chart-surface">'
        in resume_html
    )


def test_resume_page_renders_radar_image_with_img_fluid_class(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    resume_html = client.get("/resume/Application%20de%20test").get_data(as_text=True)

    assert 'alt="Radar Chart" class="img-fluid chart-surface"' in resume_html
