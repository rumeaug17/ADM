"""Homogénéisation des messages informatifs (US4.1, post-Phase 5).

Avant ce correctif, l'application affichait ses messages informatifs de deux
façons différentes selon leur origine : les messages flash Flask (connexion,
erreurs de formulaire, actions terminées par un rechargement complet de
page) apparaissaient en haut de la page, dans une alerte Bootstrap
(``alert alert-{{ category }}``) — un bloc identique dupliqué dans 11
gabarits (``index.html``, ``add.html``, ``edit.html``, ``score.html``,
``login.html``, ``change_password.html``, ``accounts.html``,
``questions_settings.html``, ``settings.html``, ``import_data.html``,
``question_form.html``) — tandis que les actions déclenchées en htmx
(suppression/réinitialisation d'une application, voir la Phase 4)
affichaient un toast Bootstrap en bas à droite de l'écran. Deux emplacements,
deux formats, pour la même notion de message informatif après une action.

Corrigé en centralisant le rendu des messages flash dans ``base.html`` : ils
sont désormais rendus directement comme des toasts Bootstrap, dans le même
conteneur (``#admToastContainer``, en bas à droite) et avec exactement le
même balisage que les toasts créés dynamiquement après une action htmx
(``toast align-items-center text-bg-<catégorie> border-0``, avec un bouton
de fermeture dont la couleur s'adapte à la catégorie). Les 11 gabarits qui
dupliquaient le rendu en haut de page ont perdu leur bloc ``{% with messages
= get_flashed_messages(...) %}`` : ``base.html`` est désormais le seul
endroit qui appelle ``get_flashed_messages``."""

import json
import re
from pathlib import Path

from flask import Flask

from ADM.accounts_json import AccountJsonSession, init_account_db
from ADM.accounts_service import create_account
from ADM.database import Application
from ADM.database_json import JsonSession, init_db

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = PROJECT_ROOT / "src" / "ADM" / "resources" / "templates"

# Les 11 gabarits qui dupliquaient le rendu des messages flash avant ce
# correctif (voir grep historique sur `get_flashed_messages`).
FORMERLY_DUPLICATED_TEMPLATES = (
    "index.html",
    "add.html",
    "edit.html",
    "score.html",
    "login.html",
    "change_password.html",
    "accounts.html",
    "questions_settings.html",
    "settings.html",
    "import_data.html",
    "question_form.html",
)


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


def _get_csrf_token(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match, "Jeton CSRF introuvable dans la page"
    return match.group(1)


# ---------------------------------------------------------------------------
# Un seul point de rendu des messages flash, dans base.html
# ---------------------------------------------------------------------------


def test_only_base_html_calls_get_flashed_messages() -> None:
    """``base.html`` doit être l'unique gabarit qui appelle
    ``get_flashed_messages`` : les 11 gabarits qui dupliquaient ce rendu en
    haut de page ne doivent plus le faire."""
    base_html = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    assert "get_flashed_messages" in base_html

    for name in FORMERLY_DUPLICATED_TEMPLATES:
        html = (TEMPLATES / name).read_text(encoding="utf-8")
        assert "get_flashed_messages" not in html, name


def test_no_template_renders_the_old_top_of_page_alert_block() -> None:
    """Garde-fou : aucun gabarit ne doit plus contenir le patron d'alerte
    Bootstrap ``alert alert-{{ category }}`` utilisé avant ce correctif pour
    les messages flash (haut de page)."""
    for path in TEMPLATES.glob("*.html"):
        html = path.read_text(encoding="utf-8")
        assert "alert-{{ category }}" not in html, path.name


# ---------------------------------------------------------------------------
# Les messages flash sont rendus comme des toasts, dans #admToastContainer
# ---------------------------------------------------------------------------


def test_base_html_renders_flash_messages_as_toasts_in_the_shared_container() -> None:
    """Le bloc qui boucle sur les messages flash doit être à l'intérieur de
    ``#admToastContainer`` (le même conteneur, en bas à droite, que celui
    utilisé par les toasts déclenchés en htmx) et produire un ``.toast``
    Bootstrap, pas une ``.alert``."""
    base_html = (TEMPLATES / "base.html").read_text(encoding="utf-8")

    container_match = re.search(
        r'<div class="toast-container[^>]*id="admToastContainer"[^>]*>(.*?)</div>\s*(?:<footer|<!-- Homogé)',
        base_html,
        re.DOTALL,
    )
    assert container_match, "#admToastContainer introuvable ou de forme inattendue"
    container_body = container_match.group(1)

    assert "get_flashed_messages" in container_body
    assert (
        'class="toast align-items-center text-bg-{{ toast_category }} border-0"' in container_body
    )
    assert '<div class="toast-body">{{ message }}</div>' in container_body
    assert "alert-{{" not in container_body


def test_login_page_renders_flash_message_as_a_toast(tmp_path: Path) -> None:
    """Une erreur de connexion (message flash de catégorie ``danger``) doit
    apparaître comme un toast dans ``#admToastContainer``, pas comme une
    alerte en haut de page."""
    application = _create_test_app(tmp_path)
    client = application.test_client()

    login_page = client.get("/login").get_data(as_text=True)
    token = _get_csrf_token(login_page)

    response = client.post(
        "/login",
        data={
            "csrf_token": token,
            "username": "utilisateur-test",
            "password": "mot-de-passe-errone",
        },
        follow_redirects=True,
    )
    html = response.get_data(as_text=True)

    assert "Identifiants incorrects." in html
    assert '<div class="toast-body">Identifiants incorrects.</div>' in html
    assert "text-bg-danger" in html
    # La forme historique (alerte en haut de page) ne doit plus apparaître.
    assert "alert-danger" not in html


def test_logout_flash_message_uses_a_close_button_matching_its_category(
    tmp_path: Path,
) -> None:
    """La catégorie ``info`` (ex. déconnexion) pose un texte sombre
    (``text-bg-info`` de Bootstrap) : son bouton de fermeture doit rester
    ``.btn-close`` par défaut, pas ``.btn-close-white`` (illisible sur fond
    clair)."""
    application = _create_test_app(tmp_path)
    client = application.test_client()
    with client.session_transaction() as user_session:
        user_session["logged_in"] = True
        user_session["username"] = "utilisateur-test"
        user_session["role"] = "user"
        user_session["auth_generation"] = 0

    response = client.get("/logout", follow_redirects=True)
    html = response.get_data(as_text=True)

    assert "Vous êtes déconnecté." in html
    toast_match = re.search(
        r'<div class="toast align-items-center text-bg-info border-0"[^>]*>.*?</div>\s*</div>',
        html,
        re.DOTALL,
    )
    assert toast_match, "Toast de déconnexion (text-bg-info) introuvable"
    assert "btn-close-white" not in toast_match.group(0)
    normalized = re.sub(r"\s+", " ", toast_match.group(0))
    assert 'class="btn-close me-2 m-auto"' in normalized


def test_successful_login_flash_message_uses_the_white_close_button(tmp_path: Path) -> None:
    """La catégorie ``success`` pose un texte blanc (``text-bg-success``) :
    son bouton de fermeture doit rester ``btn-close-white``, comme pour les
    toasts htmx (catégorie ``success`` également, voir
    ``tests/test_htmx_modal_dismissal.py``)."""
    application = _create_test_app(tmp_path)
    client = application.test_client()

    login_page = client.get("/login").get_data(as_text=True)
    token = _get_csrf_token(login_page)

    response = client.post(
        "/login",
        data={"csrf_token": token, "username": "utilisateur-test", "password": "secret-de-test"},
        follow_redirects=True,
    )
    html = response.get_data(as_text=True)

    assert "Connexion réussie." in html
    toast_match = re.search(
        r'<div class="toast align-items-center text-bg-success border-0"[^>]*>.*?</div>\s*</div>',
        html,
        re.DOTALL,
    )
    assert toast_match, "Toast de connexion réussie (text-bg-success) introuvable"
    assert "btn-close-white" in toast_match.group(0)


# ---------------------------------------------------------------------------
# Les helpers JS partagés couvrent aussi bien le rendu serveur que htmx
# ---------------------------------------------------------------------------


def test_shared_js_helpers_activate_both_flash_and_htmx_toasts() -> None:
    """Les fonctions JS ``admActivateToast``/``admToastCloseButtonClass``
    doivent être définies une seule fois et réutilisées par : (1) la boucle
    qui active les toasts flash pré-rendus au chargement de la page, et (2)
    le gestionnaire ``htmx:afterRequest`` qui construit un toast après une
    action htmx — pour garantir un comportement identique (délai, retrait du
    DOM à la fermeture) quelle que soit l'origine du message."""
    base_html = (TEMPLATES / "base.html").read_text(encoding="utf-8")

    assert base_html.count("function admActivateToast(") == 1
    assert base_html.count("function admToastCloseButtonClass(") == 1

    # Activation des toasts flash pré-rendus au chargement de page.
    assert (
        "document.querySelectorAll('#admToastContainer .toast').forEach(admActivateToast)"
        in base_html
    )

    # Le gestionnaire htmx doit appeler les deux mêmes fonctions plutôt que
    # de reconstruire sa propre logique (delay, retrait au hidden.bs.toast,
    # classe du bouton de fermeture selon la catégorie).
    htmx_handler_match = re.search(
        r"addEventListener\('htmx:afterRequest',\s*function\s*\(event\)\s*\{(.*)\}\);\s*</script>",
        base_html,
        re.DOTALL,
    )
    assert htmx_handler_match, "Gestionnaire 'htmx:afterRequest' introuvable"
    handler_body = htmx_handler_match.group(1)
    assert "admToastCloseButtonClass(category)" in handler_body
    assert "admActivateToast(toastEl)" in handler_body
