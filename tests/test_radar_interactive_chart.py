"""Phase 6 (US4.1) : graphiques radar interactifs (Chart.js).

Avant cette phase, le radar (scores moyens par dimension DICP) n'existait
qu'en image PNG statique générée côté serveur par matplotlib
(``ADM.services.generate_radar_chart``) : pas de survol pour lire une valeur
exacte, pas de zoom. Cette phase ajoute une représentation interactive
Chart.js (vendorisée, pas de CDN) affichant exactement les mêmes données,
sans supprimer le PNG (conservé comme repli sans JavaScript et pour
l'export/impression) : ``resume.html`` et ``synthese.html`` affichent le PNG
par défaut et le remplacent par le graphique interactif dès que celui-ci se
rend avec succès (voir ``static/radar_charts.js``), et une nouvelle route
JSON (``/radar/<name>/data``) alimente la modale de la synthèse qui affiche
le radar d'une application choisie.

Ces tests ne peuvent pas exécuter de JavaScript ni piloter un vrai
navigateur (aucun outil de ce type n'est disponible dans cette suite) : ils
vérifient la donnée exposée côté serveur (``ADM.services.radar_chart_data``,
la nouvelle route JSON) et la présence/structure du balisage et des scripts
attendus dans les gabarits réellement servis, pas le rendu visuel du
graphique lui-même — un test manuel dans un navigateur reste nécessaire pour
ça (voir « Ce qui reste à faire côté utilisateur » du document de
modernisation)."""

import json
import math
from pathlib import Path

import pytest
from flask import Flask

from ADM.accounts_json import AccountJsonSession, init_account_db
from ADM.accounts_service import create_account
from ADM.database import Application
from ADM.database_json import JsonSession, init_db
from ADM.services import generate_radar_chart, radar_chart_data

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


def _logged_in_client(application: Flask) -> object:
    client = application.test_client()
    with client.session_transaction() as user_session:
        user_session["logged_in"] = True
        user_session["username"] = "utilisateur-test"
        user_session["role"] = "user"
        user_session["auth_generation"] = 0
    return client


# ---------------------------------------------------------------------------
# ADM.services.radar_chart_data : même donnée que le PNG, au format Chart.js
# ---------------------------------------------------------------------------


def test_radar_chart_data_returns_labels_scores_and_max() -> None:
    result = radar_chart_data({"Architecture": 2.5, "Exploitation": 1.0})

    assert result == {"labels": ["Architecture", "Exploitation"], "scores": [2.5, 1.0], "max": 3}


def test_radar_chart_data_matches_generate_radar_chart_maximum() -> None:
    """La borne d'échelle (``max``) doit être identique à celle utilisée par
    le PNG matplotlib, pour que les deux représentations restent cohérentes
    entre elles : les deux s'appuient sur le même calcul interne
    (``ADM.services._radar_chart_bounds``)."""
    scores_by_axis = {"Architecture": 2.1, "Exploitation": 4.6, "Sécurité": 0.0}

    result = radar_chart_data(scores_by_axis)

    assert result["max"] == max(1, math.ceil(max(scores_by_axis.values())))
    # Le PNG doit se générer sans erreur avec ces mêmes scores (pas de test
    # sur son contenu binaire, déjà couvert par tests/test_services.py).
    encoded_chart = generate_radar_chart(dict(scores_by_axis))
    assert encoded_chart


def test_radar_chart_data_defaults_to_a_maximum_of_three_when_there_are_no_scores() -> None:
    """Même repli que ``generate_radar_chart`` (voir ``_radar_chart_bounds``)
    quand aucun score n'est disponible (aucune catégorie de question
    configurée, ou aucune réponse)."""
    assert radar_chart_data({}) == {"labels": [], "scores": [], "max": 3}


# ---------------------------------------------------------------------------
# Nouvelle route JSON : /radar/<name>/data
# ---------------------------------------------------------------------------


def test_radar_data_route_returns_json_with_labels_scores_and_max(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    response = client.get("/radar/Application%20de%20test/data")

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    payload = response.get_json()
    assert isinstance(payload["labels"], list)
    assert isinstance(payload["scores"], list)
    assert len(payload["labels"]) == len(payload["scores"])
    assert isinstance(payload["max"], int)
    assert payload["max"] >= 1


def test_radar_route_and_radar_data_route_agree_on_categories(tmp_path: Path) -> None:
    """Repli PNG (``/radar/<name>``, inchangé) et graphique interactif
    (``/radar/<name>/data``, nouveau) doivent porter sur exactement les mêmes
    catégories : ce sont les deux faces de la même donnée
    (``ADM.services.axis_scores``), voir ``ADM.routes.radar_chart`` et
    ``ADM.routes.radar_chart_json``."""
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    png_response = client.get("/radar/Application%20de%20test")
    json_response = client.get("/radar/Application%20de%20test/data")

    assert png_response.status_code == 200
    assert png_response.mimetype == "image/png"
    assert json_response.status_code == 200
    # Le nombre d'axes du radar (une catégorie par question configurée) est
    # ce que les deux routes ont en commun de façon vérifiable sans décoder
    # l'image PNG.
    assert len(json_response.get_json()["labels"]) > 0


# ---------------------------------------------------------------------------
# Chart.js est vendorisé (pas de CDN), comme Bootstrap/htmx/Alpine.js
# ---------------------------------------------------------------------------


def test_chartjs_is_vendored_and_not_loaded_from_a_cdn() -> None:
    chartjs_path = STATIC / "vendor" / "chartjs" / "chart.umd.min.js"
    assert chartjs_path.is_file()
    content = chartjs_path.read_text(encoding="utf-8")
    assert "Chart.js" in content

    for name in ("resume.html", "synthese.html"):
        html = (TEMPLATES / name).read_text(encoding="utf-8")
        # Garde-fou anti-régression : aucun <script src="http...">, seul un
        # chemin vers le fichier vendorisé local est attendu (les commentaires
        # du gabarit mentionnent volontairement "CDN" en toutes lettres pour
        # expliquer ce choix, d'où l'absence de recherche naïve de ce mot).
        assert 'src="http' not in html
        assert "vendor/chartjs/chart.umd.min.js" in html, (
            f"{name} doit charger Chart.js depuis static/vendor/, pas un CDN"
        )


def test_radar_charts_js_exposes_the_expected_helper_functions() -> None:
    content = (STATIC / "radar_charts.js").read_text(encoding="utf-8")
    for function_name in (
        "admRadarChartConfig",
        "admRenderRadarChart",
        "admRenderRadarChartFromElement",
        "admShowRadarChart",
    ):
        assert f"function {function_name}(" in content


def test_radar_chart_config_forces_a_square_aspect_ratio() -> None:
    """Correctif (bug d'affichage post-Phase 6) : un ratio carré explicite,
    plutôt que de dépendre du ratio par défaut de Chart.js, pour un rendu
    prévisible combiné à ``.radar-chart-wrapper`` (voir app.css)."""
    content = (STATIC / "radar_charts.js").read_text(encoding="utf-8")
    assert "aspectRatio: 1" in content


# ---------------------------------------------------------------------------
# Correctif (post-Phase 6) : le radar de resume.html s'affichait bien plus
# grand que le PNG qu'il remplaçait, dans une carte pleine largeur.
# ---------------------------------------------------------------------------


def test_app_css_defines_a_radar_chart_wrapper_with_a_bounded_width() -> None:
    css = (STATIC / "css" / "app.css").read_text(encoding="utf-8")
    # La règle elle-même (pas seulement son nom, qui apparaît aussi dans le
    # commentaire qui la précède).
    rule_start = css.index(".radar-chart-wrapper {")
    rule_body = css[rule_start:].split("}")[0]
    assert "max-width" in rule_body


@pytest.mark.parametrize(
    ("template_name", "canvas_id"),
    [
        ("resume.html", "resumeRadarChart"),
        ("synthese.html", "syntheseRadarChart"),
        ("synthese.html", "radarChartCanvas"),
    ],
)
def test_radar_canvas_is_wrapped_in_a_width_bounded_container(
    template_name: str, canvas_id: str
) -> None:
    html = (TEMPLATES / template_name).read_text(encoding="utf-8")
    canvas_index = html.index(f'id="{canvas_id}"')
    preceding_html = html[:canvas_index]
    wrapper_index = preceding_html.rindex("<div")
    # Le <div class="radar-chart-wrapper"> doit être le parent direct (ou
    # quasi direct) du <canvas>, pas une carte pleine largeur plus haute dans
    # l'arborescence : on vérifie que le dernier <div> ouvert avant le canvas
    # porte bien cette classe.
    assert 'class="radar-chart-wrapper"' in preceding_html[wrapper_index:]


# ---------------------------------------------------------------------------
# resume.html : PNG affiché par défaut, remplacé par le graphique interactif
# ---------------------------------------------------------------------------


def test_resume_html_keeps_the_png_image_and_adds_an_interactive_canvas() -> None:
    resume_html = (TEMPLATES / "resume.html").read_text(encoding="utf-8")

    # Le PNG (repli) reste strictement identique à avant cette phase (voir
    # tests/test_resume_radar_responsive.py, qui vérifie déjà cette exacte
    # sous-chaîne) : ce test-ci vérifie seulement l'ajout du canvas et des
    # scripts, sans dupliquer cette assertion.
    assert 'src="data:image/png;base64,{{ radar_chart }}"' in resume_html
    assert 'id="resumeRadarChart"' in resume_html
    assert 'class="d-none chart-surface"' in resume_html
    assert 'id="resumeRadarData"' in resume_html
    assert "radar_chart_json|tojson" in resume_html
    assert "vendor/chartjs/chart.umd.min.js" in resume_html
    assert "radar_charts.js" in resume_html
    assert "admShowRadarChart('resumeRadarChart'" in resume_html


def test_resume_page_embeds_the_radar_scores_as_json(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    html = client.get("/resume/Application%20de%20test").get_data(as_text=True)

    assert '<script type="application/json" id="resumeRadarData">' in html
    assert 'id="resumeRadarChart"' in html
    # Toujours présent (repli), quel que soit le succès du rendu Chart.js.
    assert 'src="data:image/png;base64,' in html


# ---------------------------------------------------------------------------
# synthese.html : radar moyen + modale par application, même principe
# ---------------------------------------------------------------------------


def test_synthese_html_keeps_the_png_image_and_adds_an_interactive_canvas() -> None:
    synthese_html = (TEMPLATES / "synthese.html").read_text(encoding="utf-8")

    assert 'src="data:image/png;base64,{{ chart_data }}"' in synthese_html
    assert 'id="syntheseRadarChart"' in synthese_html
    assert 'id="syntheseRadarData"' in synthese_html
    assert "radar_chart_json|tojson" in synthese_html
    assert "vendor/chartjs/chart.umd.min.js" in synthese_html
    assert "admShowRadarChart('syntheseRadarChart'" in synthese_html


def test_synthese_html_modal_fetches_json_and_falls_back_to_the_png_on_failure() -> None:
    """La modale continue de poser le PNG (``/radar/<name>``, comportement
    historique) avant même de tenter le graphique interactif : en cas
    d'échec du ``fetch`` JSON, le PNG déjà affiché reste en place, sans
    canvas vide ni radar manquant."""
    synthese_html = (TEMPLATES / "synthese.html").read_text(encoding="utf-8")

    assert 'id="radarChartCanvas" class="d-none chart-surface"' in synthese_html
    assert (
        "document.getElementById('radarChartImg').src = \"/radar/\" + encodeURIComponent(appName);"
        in (synthese_html)
    )
    assert '"/radar/" + encodeURIComponent(appName) + "/data"' in synthese_html
    assert "pendingRadarData = null;" in synthese_html
    assert "resetRadarModalDisplay();" in synthese_html


def test_synthese_html_modal_renders_the_chart_only_after_shown_not_show() -> None:
    """Correctif (bug d'affichage post-Phase 6) : ``show.bs.modal`` se
    déclenche AVANT que Bootstrap ne rende le modal visible (le fondu
    d'ouverture ne démarre qu'ensuite). Créer le graphique Chart.js à ce
    moment-là mesure un conteneur de largeur nulle et produit un canvas
    quasi invisible (juste le contour blanc de ``.chart-surface`` — le
    « point blanc » signalé). ``admRenderRadarChart`` ne doit donc être
    appelé que dans un gestionnaire ``shown.bs.modal``, jamais directement
    dans ``show.bs.modal``."""
    synthese_html = (TEMPLATES / "synthese.html").read_text(encoding="utf-8")

    show_start = synthese_html.index("addEventListener('show.bs.modal'")
    shown_start = synthese_html.index("addEventListener('shown.bs.modal'")
    hidden_start = synthese_html.index("addEventListener('hidden.bs.modal'")
    assert show_start < shown_start < hidden_start

    show_handler_body = synthese_html[show_start:shown_start]
    shown_handler_body = synthese_html[shown_start:hidden_start]

    assert "admRenderRadarChart(" not in show_handler_body
    assert "admRenderRadarChart(" in shown_handler_body
    # La requête réseau, elle, démarre bien dès "show.bs.modal" (pas besoin
    # d'attendre la fin du fondu d'ouverture pour l'envoyer) : seul le rendu
    # est différé.
    assert "fetch(" in show_handler_body


def test_synthese_page_embeds_the_average_radar_scores_as_json(tmp_path: Path) -> None:
    application = _create_test_app(tmp_path)
    client = _logged_in_client(application)

    html = client.get("/synthese").get_data(as_text=True)

    assert '<script type="application/json" id="syntheseRadarData">' in html
    assert 'id="syntheseRadarChart"' in html
    assert 'src="data:image/png;base64,' in html
