"""Phase 5 de US4.1 (US4.1, voir docs/UI_MODERNIZATION_PROPOSAL.md section 18) :
mode sombre, accessibilité et finitions.

Ces tests couvrent l'audit de contraste et les corrections d'accessibilité
apportées lors de cette phase :

- Les badges DICP/criticité et les badges de score/risque affichés sur fond
  jaune (``--adm-warning``) ou orange (``--adm-orange``) n'offraient qu'un
  très faible contraste avec le texte blanc appliqué par défaut par
  Bootstrap (``.badge``) : environ 1,6:1 et 2,6:1, très en-dessous du minimum
  WCAG AA de 4,5:1 pour du texte normal. Les badges de score/risque calculés
  côté serveur (``_application_row.html``, ``_synthese_results.html``,
  ``resume.html``, ``synthese.html``) sont passés des utilitaires Bootstrap
  ``bg-*`` (qui ne fixent pas de couleur de texte) aux utilitaires
  ``text-bg-*`` (qui pairent automatiquement une couleur de texte lisible,
  noire pour ``text-bg-warning``) ; les badges DICP/criticité personnalisés
  (``.badge-d2``, ``.badge-criticite3``, etc., définis dans ``app.css``) ont
  reçu un texte sombre explicite (``--adm-badge-text-dark``).
- Les deux liens d'action de ``resume.html`` (modifier/évaluer) n'étaient
  identifiés que par un ``title`` (infobulle Bootstrap), sans ``aria-label`` :
  un lecteur d'écran ne les annonce pas de façon fiable. Un ``aria-label``
  reprenant le même texte que le ``title`` (et que les libellés déjà utilisés
  ailleurs pour la même action, voir ``_application_row.html``) a été ajouté.
- Le modal de réinitialisation de mot de passe d'``accounts.html`` (un par
  compte, ``id="resetPasswordModal-{{ loop.index }}"``) n'avait pas
  d'``aria-labelledby`` ni d'``id`` sur son titre, contrairement à tous les
  autres modaux de l'application (``createAccountModal``, les modaux de
  confirmation d'``index.html``, etc.) : un lecteur d'écran n'annonce donc
  pas de nom accessible à l'ouverture. Corrigé à l'identique du patron déjà
  utilisé partout ailleurs."""

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
        username="admin-test",
        password="secret-de-test",
        role="admin",
    )
    create_account(
        accounts_session,
        username="second-compte",
        password="autre-secret",
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


def _logged_in_admin_client(application: Flask) -> FlaskClient:
    client = application.test_client()
    with client.session_transaction() as user_session:
        user_session["logged_in"] = True
        user_session["username"] = "admin-test"
        user_session["role"] = "admin"
        user_session["auth_generation"] = 0
    return client


# ---------------------------------------------------------------------------
# Contraste WCAG des badges sur fond jaune/orange
# ---------------------------------------------------------------------------


def _srgb_to_linear(channel_0_1: float) -> float:
    if channel_0_1 <= 0.03928:
        return channel_0_1 / 12.92
    return ((channel_0_1 + 0.055) / 1.055) ** 2.4


def _relative_luminance(hex_color: str) -> float:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))
    r_lin, g_lin, b_lin = (_srgb_to_linear(c) for c in (r, g, b))
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def _contrast_ratio(hex_a: str, hex_b: str) -> float:
    """Ratio de contraste WCAG entre deux couleurs (formule officielle)."""
    l_a = _relative_luminance(hex_a) + 0.05
    l_b = _relative_luminance(hex_b) + 0.05
    return max(l_a, l_b) / min(l_a, l_b)


def _extract_css_variable(css: str, name: str) -> str:
    match = re.search(rf"{re.escape(name)}:\s*(#[0-9a-fA-F]{{3,8}})", css)
    assert match, f"Variable CSS {name} introuvable dans app.css"
    return match.group(1)


def test_warning_and_orange_badge_text_meets_wcag_aa_contrast() -> None:
    """Le texte posé sur les fonds ``--adm-warning``/``--adm-orange`` (badges
    DICP/criticité concernés, voir app.css) doit respecter le minimum WCAG AA
    de 4,5:1 pour du texte normal — ce qui n'était pas le cas avec le blanc
    par défaut de Bootstrap (~1,6:1 et ~2,6:1)."""
    app_css = (STATIC / "css" / "app.css").read_text(encoding="utf-8")
    warning_bg = _extract_css_variable(app_css, "--adm-warning")
    orange_bg = _extract_css_variable(app_css, "--adm-orange")
    badge_text = _extract_css_variable(app_css, "--adm-badge-text-dark")

    # Le blanc par défaut de Bootstrap échoue largement, ce qui motive le
    # correctif : sert de garde-fou si jamais la palette change et que
    # quelqu'un revient au blanc par erreur.
    assert _contrast_ratio("#ffffff", warning_bg) < 4.5
    assert _contrast_ratio("#ffffff", orange_bg) < 4.5

    assert _contrast_ratio(badge_text, warning_bg) >= 4.5
    assert _contrast_ratio(badge_text, orange_bg) >= 4.5


def test_dicp_and_criticite_badge_classes_use_dark_text_on_warning_and_orange() -> None:
    """Les classes de badges DICP/criticité affichées sur fond jaune ou
    orange déclarent explicitement ``--adm-badge-text-dark`` comme couleur de
    texte (Bootstrap ne le fait pas pour une classe personnalisée)."""
    app_css = (STATIC / "css" / "app.css").read_text(encoding="utf-8")
    for selector_block in (
        r"\.badge-d2,\s*\.badge-i2,\s*\.badge-c2,\s*\.badge-p2,\s*\.badge-criticite3\s*\{[^}]*\}",
        r"\.badge-d3,\s*\.badge-i3,\s*\.badge-c3,\s*\.badge-p3,\s*\.badge-criticite2\s*\{[^}]*\}",
    ):
        match = re.search(selector_block, app_css)
        assert match, f"Règle CSS introuvable ou de forme inattendue : {selector_block}"
        assert "var(--adm-badge-text-dark)" in match.group(0)


def test_score_and_risk_badges_use_text_bg_utilities_not_bare_bg() -> None:
    """Les badges de score/risque (couleur calculée à l'exécution selon les
    seuils) doivent utiliser les utilitaires Bootstrap ``text-bg-*``, qui
    pairent une couleur de texte lisible, plutôt que ``bg-*`` seul (qui laisse
    le texte blanc par défaut de ``.badge`` même sur un fond jaune)."""
    for template_name in (
        "_application_row.html",
        "_synthese_results.html",
        "resume.html",
        "synthese.html",
    ):
        html = (TEMPLATES / template_name).read_text(encoding="utf-8")
        assert "text-bg-warning" in html, template_name
        assert "text-bg-danger" in html, template_name
        assert "text-bg-success" in html, template_name
        # Garde-fou : aucune régression vers le patron `badge ... bg-warning`
        # (ou danger/success) qui ne fixe pas de couleur de texte. Exclut
        # `text-bg-warning` lui-même via une lookbehind négative sur "text-".
        assert not re.search(r'class="badge[^"]*(?<!text-)\bbg-warning\b', html), template_name
        assert not re.search(r'class="badge[^"]*(?<!text-)\bbg-danger\b', html), template_name
        assert not re.search(r'class="badge[^"]*(?<!text-)\bbg-success\b', html), template_name


# ---------------------------------------------------------------------------
# Libellés accessibles des actions de resume.html
# ---------------------------------------------------------------------------


def test_resume_icon_only_actions_have_aria_label() -> None:
    """Les deux boutons d'action de ``resume.html`` (modifier/évaluer) ne
    contiennent qu'une icône : ils doivent porter un ``aria-label`` en plus du
    ``title`` (infobulle absente au clavier/lecteur d'écran selon le
    navigateur)."""
    resume_html = (TEMPLATES / "resume.html").read_text(encoding="utf-8")
    for label in ("Modifier l'application", "Évaluer l'application"):
        assert f'title="{label}" aria-label="{label}"' in resume_html, label


def test_resume_page_renders_icon_only_actions_with_aria_label(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_admin_client(application)

    resume_html = client.get("/resume/Application%20de%20test").get_data(as_text=True)

    for label in ("Modifier l'application", "Évaluer l'application"):
        assert f'aria-label="{label}"' in resume_html, label


# ---------------------------------------------------------------------------
# Nom accessible du modal de réinitialisation de mot de passe (accounts.html)
# ---------------------------------------------------------------------------


def test_reset_password_modal_has_accessible_name() -> None:
    """Le modal de réinitialisation de mot de passe (un par compte) doit,
    comme tous les autres modaux de l'application, référencer via
    ``aria-labelledby`` l'``id`` posé sur son titre (``.modal-title``)."""
    accounts_html = (TEMPLATES / "accounts.html").read_text(encoding="utf-8")
    assert 'id="resetPasswordModal-{{ loop.index }}"' in accounts_html
    assert 'aria-labelledby="resetPasswordModalLabel-{{ loop.index }}"' in accounts_html
    assert 'id="resetPasswordModalLabel-{{ loop.index }}"' in accounts_html


def test_reset_password_modal_renders_matching_ids_per_account(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_admin_client(application)

    accounts_html = client.get("/accounts").get_data(as_text=True)

    # Deux comptes créés par _create_test_app -> deux modaux, chacun avec un
    # id de modal et un id de titre qui se correspondent (loop.index 1 et 2).
    for index in (1, 2):
        modal_id = f"resetPasswordModal-{index}"
        label_id = f"resetPasswordModalLabel-{index}"
        assert f'id="{modal_id}"' in accounts_html
        assert f'aria-labelledby="{label_id}"' in accounts_html
        assert f'id="{label_id}"' in accounts_html
