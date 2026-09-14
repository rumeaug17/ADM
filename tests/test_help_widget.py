"""Tâche 4.5 du backlog : unification du composant d'aide contextuelle.

Avant cette correction, l'application mélangeait deux implémentations
différentes : les boutons d'action de ``index.html``/``resume.html``
utilisaient les tooltips Bootstrap natifs (``data-bs-toggle="tooltip"``),
tandis que les icônes d'aide (``?``) de ``score.html``, ``add.html`` et
``edit.html`` réimplémentaient une infobulle maison positionnée en absolu,
avec une largeur fixe différente selon la page (450px sur ``score.html`` et
``edit.html``, 1050px sur ``add.html``), susceptible de déborder sur petit
écran.

Ces tests vérifient qu'un seul composant natif Bootstrap (le popover, déjà
fourni par ``bootstrap.bundle.min.js``) est désormais utilisé partout pour
l'aide contextuelle, sans largeur fixée en dur par page, et que
l'initialisation des tooltips Bootstrap des boutons d'action est centralisée
dans ``base.html`` (elle était absente de ``resume.html`` et cassée sur
``index.html``, dont le script s'exécutait avant le chargement de
bootstrap.bundle.min.js)."""

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


def test_action_button_tooltips_are_initialised_once_in_base_html() -> None:
    """base.html doit être l'unique gabarit qui instancie
    ``new bootstrap.Tooltip(...)`` ; les pages qui l'étendent ne doivent
    plus le faire elles-mêmes."""
    base_html = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    index_html = (TEMPLATES / "index.html").read_text(encoding="utf-8")
    resume_html = (TEMPLATES / "resume.html").read_text(encoding="utf-8")

    assert "new bootstrap.Tooltip" in base_html
    assert "new bootstrap.Tooltip" not in index_html
    assert "new bootstrap.Tooltip" not in resume_html


def test_action_button_tooltips_render_and_are_initialised(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    index_html = client.get("/").get_data(as_text=True)
    resume_html = client.get("/resume/Application%20de%20test").get_data(as_text=True)

    for page in (index_html, resume_html):
        assert 'data-bs-toggle="tooltip"' in page
        assert "new bootstrap.Tooltip" in page  # hérité de base.html


def test_help_icons_no_longer_use_the_hand_rolled_widget() -> None:
    """Les 3 pages qui affichent des icônes d'aide ne doivent plus contenir
    l'ancienne classe ``.info-tooltip`` ni les largeurs fixes qui causaient
    le débordement sur petit écran."""
    for name in ("score.html", "add.html", "edit.html"):
        html = (TEMPLATES / name).read_text(encoding="utf-8")
        assert "info-tooltip" not in html, name
        assert "450px" not in html, name
        assert "1050px" not in html, name
        assert '<span class="info-icon"' not in html, name


def test_help_icons_render_as_accessible_popover_buttons(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    add_html = client.get("/add").get_data(as_text=True)
    score_html = client.get("/score/Application%20de%20test").get_data(as_text=True)
    edit_html = client.get("/edit/Application%20de%20test").get_data(as_text=True)

    for page in (add_html, score_html, edit_html):
        # Un vrai <button>, focusable au clavier par défaut, plutôt qu'un
        # <span> nécessitant un tabindex et une gestion clavier manuelle.
        assert '<button type="button" class="info-icon"' in page
        assert 'aria-label="Aide' in page
        assert "ADM.initInfoTooltips" in page


def test_popover_width_is_responsive_not_fixed_per_page() -> None:
    """Une seule règle CSS ``.popover`` (dans base.html), avec une largeur
    plafonnée relativement à la fenêtre (``vw``), remplace les largeurs
    fixes dupliquées et divergentes de score.html (450px) et add.html
    (1050px)."""
    base_html = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    assert ".popover" in base_html
    assert "vw" in base_html


def test_info_tooltip_script_uses_bootstrap_popover_not_a_hand_rolled_widget() -> None:
    source = (STATIC / "info_tooltip.js").read_text(encoding="utf-8")
    assert "bootstrap.Popover" in source
    assert "getBoundingClientRect" not in source
    # "focus" seul : accessible au clavier, et ouvre/ferme en un clic. Un
    # déclencheur combiné focus+click faisait interférer les deux
    # gestionnaires et obligeait à cliquer deux fois pour fermer le popover.
    assert 'trigger: "focus"' in source
    assert 'trigger: "focus click"' not in source
