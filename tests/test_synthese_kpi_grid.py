"""Tâche 4.10 du backlog : grille des indicateurs de ``/synthese`` mal alignée.

Les cinq cartes de KPI utilisaient chacune `col-md-3` dans une grille
Bootstrap à 12 colonnes (5 × 3 = 15 > 12 colonnes), ce qui provoquait un
retour à la ligne asymétrique de la dernière carte. Des balises
`<p></p>`/`<p/>` isolées servaient par ailleurs d'espacement à la place des
classes utilitaires Bootstrap.

Ces tests vérifient que la grille des KPI utilise des colonnes de largeur
égale (`row-cols-*`) plutôt que des `col-md-3` fixes, que les espaceurs
`<p></p>`/`<p/>` ont disparu au profit de classes utilitaires (`g-3`,
`my-4`, `mb-3`), et que la page continue de se rendre correctement."""

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
            score=42,
            answered_questions=3,
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


def test_synthese_template_kpi_grid_uses_row_cols_not_col_md_3() -> None:
    synthese_html = (TEMPLATES / "synthese.html").read_text(encoding="utf-8")
    # Les 5 cartes de KPI ne doivent plus se répartir dans une grille de 12
    # colonnes fixes (5 × col-md-3 = 15 > 12), mais dans des colonnes de
    # largeur égale calculées par row-cols-*.
    assert "row-cols-" in synthese_html
    assert synthese_html.count('<div class="col">') == 5
    # Les espaceurs `<p></p>`/`<p/>` ont été remplacés par des classes
    # utilitaires (g-3, my-4, mb-3).
    assert "<p></p>" not in synthese_html
    assert "<p/>" not in synthese_html


def test_synthese_page_renders_kpi_grid_without_legacy_spacers(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    response = client.get("/synthese")
    synthese_html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "row-cols-" in synthese_html
    assert synthese_html.count('<div class="col">') == 5
    assert "<p></p>" not in synthese_html
    assert "<p/>" not in synthese_html
    # Les 5 indicateurs sont toujours bien présents et rendus.
    assert "Nombre total d'applications" in synthese_html
    assert "Score moyen" in synthese_html
    assert "Risque global" in synthese_html
