"""Correctif post-Phase 4 (US4.1) : le modal de confirmation reste ouvert
après une suppression/réinitialisation d'application.

Avant htmx (Phase 3 et antérieures), soumettre le formulaire de confirmation
d'``index.html`` rechargeait toute la page : le modal, qui n'existait plus
dans le nouveau DOM, disparaissait de facto. Depuis la Phase 4, ce même
formulaire est intercepté par htmx (``hx-post``/``hx-target``/``hx-swap``
posés dynamiquement sur ``show.bs.modal``, voir ``index.html``) : la page ne
se recharge plus, la ligne du tableau est bien mise à jour et un toast
confirme l'action, mais rien ne dit à Bootstrap de fermer le modal — il
restait donc ouvert, superposé à la page, jusqu'à ce que l'utilisateur le
ferme lui-même.

Corrigé dans ``base.html`` : l'écouteur ``htmx:afterRequest`` (déjà présent
pour afficher le toast à partir de l'en-tête ``HX-Trigger``) recherche
désormais, pour toute requête htmx réussie, un modal Bootstrap ancêtre de
l'élément qui a déclenché la requête (``event.detail.elt.closest('.modal')``)
et le referme via l'instance ``bootstrap.Modal`` existante. Cette correction
est générique : elle s'applique à n'importe quel formulaire htmx placé dans
un modal, pas seulement aux deux cas actuels (suppression, réinitialisation),
sans qu'il soit nécessaire de coder en dur les ids de modal.

Ces tests ne peuvent pas exécuter de JavaScript (pas de navigateur dans la
suite pytest) : ils vérifient la présence et la forme de ce correctif dans
le gabarit servi, comme garde-fou contre une régression future (suppression
accidentelle du bloc, ou déplacement dans un script qui ne serait plus
chargé sur toutes les pages)."""

import json
import re
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


def test_htmx_after_request_closes_the_ancestor_modal_on_success() -> None:
    """``base.html`` doit fermer, via l'API ``bootstrap.Modal``, le modal
    ancêtre de l'élément qui a déclenché une requête htmx réussie."""
    base_html = (TEMPLATES / "base.html").read_text(encoding="utf-8")

    # Le bloc doit être dans le même écouteur 'htmx:afterRequest' que celui
    # qui affiche le toast (un seul écouteur, pas un second enregistré
    # ailleurs qui pourrait être oublié/supprimé indépendamment).
    match = re.search(
        r"addEventListener\('htmx:afterRequest',\s*function\s*\(event\)\s*\{(.*)\}\);\s*</script>",
        base_html,
        re.DOTALL,
    )
    assert match, "Écouteur 'htmx:afterRequest' introuvable dans base.html"
    listener_body = match.group(1)

    assert "event.detail.successful" in listener_body
    assert ".closest('.modal')" in listener_body
    assert "bootstrap.Modal.getInstance(modalEl)" in listener_body
    assert "modalInstance.hide()" in listener_body

    # Garde-fou : le correctif doit s'appliquer avant tout "return" anticipé
    # du traitement du toast (sinon une réponse sans en-tête HX-Trigger, comme
    # la suppression qui renvoie un corps vide, sortirait de la fonction avant
    # d'avoir fermé le modal).
    close_modal_pos = listener_body.index("modalInstance.hide()")
    first_early_return_pos = listener_body.index("return;")
    assert close_modal_pos < first_early_return_pos


def test_reset_and_delete_forms_live_inside_a_bootstrap_modal() -> None:
    """Les deux formulaires concernés (réinitialisation, suppression) doivent
    bien être des descendants d'un élément ``.modal``, condition nécessaire
    pour que ``closest('.modal')`` les retrouve à l'exécution."""
    index_html = (TEMPLATES / "index.html").read_text(encoding="utf-8")

    for modal_id, form_id in (
        ("confirmDeleteModal", "confirmDeleteForm"),
        ("confirmResetModal", "confirmResetForm"),
    ):
        modal_match = re.search(
            rf'<div class="modal fade" id="{modal_id}".*?(?=<div class="modal fade"|\Z)',
            index_html,
            re.DOTALL,
        )
        assert modal_match, f"Modal {modal_id} introuvable"
        assert f'id="{form_id}"' in modal_match.group(0), form_id


def test_reset_evaluation_htmx_response_keeps_the_form_inside_the_modal_reachable(
    tmp_path: Path,
) -> None:
    """Vérifie, via une vraie requête applicative, que la page initiale
    contient bien tout ce dont le correctif a besoin à l'exécution : le
    conteneur de toasts, le script htmx et le formulaire dans son modal."""
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    index_html = client.get("/").get_data(as_text=True)

    assert 'id="admToastContainer"' in index_html
    assert "vendor/htmx/htmx.min.js" in index_html
    assert 'id="confirmResetModal"' in index_html
    assert 'id="confirmResetForm"' in index_html
