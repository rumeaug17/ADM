"""Distinction entre le profil de sensibilité ADM et l'analyse de risques DICP.

Les niveaux D/I/C/P saisis dans ADM ne sont qu'une estimation servant à
pondérer la dette technique. Leur présentation ne doit pas laisser croire
qu'il s'agit de la classification DICP issue de l'analyse de risques (RSSI),
dont le 4e critère est la Preuve et non la Pérennité (voir
``docs/BUSINESS_RULES.md``, « Profil de sensibilité et analyse de risques »).

Seuls les libellés et l'affichage changent : les clés techniques, les codes
stockés (``P3``) et la formule du risque restent identiques.
"""

import csv
import io
import json
from pathlib import Path

import pytest
from flask import Flask
from flask.testing import FlaskClient

from ADM.accounts_json import AccountJsonSession, init_account_db
from ADM.accounts_service import create_account
from ADM.database import Application
from ADM.database_json import JsonSession, init_db
from ADM.services import sensitivity_display_code

TEMPLATES = Path(__file__).resolve().parents[1] / "src" / "ADM" / "resources" / "templates"
APP_NAME = "Application de test"
DISCLAIMER = "ne remplace pas la classification DICP issue de l'analyse de risques"


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
            name=APP_NAME,
            rda="Responsable fictif",
            possession=None,
            type_app="cloud",
            hosting="cloud",
            criticite=2,
            disponibilite="D2",
            integrite="I3",
            confidentialite="C1",
            perennite="P3",
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
        user_session["username"] = "admin-test"
        user_session["role"] = "admin"
        user_session["auth_generation"] = 0
    return client


@pytest.mark.parametrize(
    ("stored", "displayed"),
    [("D2", "D2"), ("I3", "I3"), ("C4", "C4"), ("P1", "Pé1"), ("P4", "Pé4")],
)
def test_sensitivity_display_code_only_renames_perennite(stored: str, displayed: str) -> None:
    assert sensitivity_display_code(stored) == displayed


@pytest.mark.parametrize("value", ["1", "P5", "X2", "P12", ""])
def test_sensitivity_display_code_keeps_invalid_values_unchanged(value: str) -> None:
    """Une valeur non reconnue est restituée telle quelle, sans interprétation."""
    assert sensitivity_display_code(value) == value


def test_sensitivity_display_code_handles_none() -> None:
    assert sensitivity_display_code(None) == ""


def test_catalogue_groups_the_four_criteria_under_dicpe_and_renames_risk(
    tmp_path: Path,
) -> None:
    """Les quatre pastilles restent côte à côte dans une seule colonne,
    renommée « Sensibilité DICPé » pour lever l'ambiguïté avec le DICP de
    l'analyse de risques (P = Preuve)."""
    client = _logged_in_client(_create_test_app(tmp_path))

    html = client.get("/").get_data(as_text=True)

    assert "Classification (DICP)" not in html
    assert "Sensibilité DICPé</th>" in html
    assert "Pérennité attendue</th>" not in html
    assert ">Pé3</span>" in html
    assert ">P3</span>" not in html
    # Les quatre pastilles sont dans le même groupe, dans l'ordre D, I, C, Pé.
    group = html.split('<div class="d-flex flex-nowrap gap-2">', 1)[1].split("</div>", 1)[0]
    positions = [group.index(f">{code}</span>") for code in ("D2", "I3", "C1", "Pé3")]
    assert positions == sorted(positions)
    assert "Exposition dette" in html
    assert ">Risque <i" not in html


def test_catalogue_sort_columns_match_the_single_sensitivity_column() -> None:
    """Une seule colonne de sensibilité : les index ``data-sort-col`` restent
    uniques et l'exposition dette est la 8e colonne (index 7)."""
    index_html = (TEMPLATES / "index.html").read_text(encoding="utf-8")
    for index in range(10):
        assert index_html.count(f'data-sort-col="{index}"') <= 1
    assert 'data-sort-col="7" data-sort-type="number">Exposition dette' in index_html
    assert 'colspan="11"' in index_html


@pytest.mark.parametrize("path", ["/add", f"/edit/{APP_NAME}"])
def test_application_forms_present_an_estimated_sensitivity_profile(
    tmp_path: Path, path: str
) -> None:
    client = _logged_in_client(_create_test_app(tmp_path))

    html = client.get(path).get_data(as_text=True)

    assert "Classification de sécurité" not in html
    assert "Criticité et sensibilité DICPé (estimation ADM)" in html
    assert DISCLAIMER in html
    assert "DICPé : Disponibilité, Intégrité, Confidentialité, Pérennité attendue" in html
    assert "Pérennité attendue (Pé) :" in html
    # Les valeurs soumises restent les codes stockés historiques.
    assert 'value="P3"' in html


def test_resume_groups_the_four_criteria_and_shows_the_disclaimer(tmp_path: Path) -> None:
    client = _logged_in_client(_create_test_app(tmp_path))

    html = client.get(f"/resume/{APP_NAME}").get_data(as_text=True)

    assert "Classification (DICP)" not in html
    line = html.split("<strong>Sensibilité DICPé (estimation ADM) :</strong>", 1)[1]
    line = line.split("</p>", 1)[0]
    for code in ("D2", "I3", "C1", "Pé3"):
        assert f">{code}</span>" in line, code
    assert "remplace pas la classification DICP" in html
    assert "Exposition dette :" in html
    assert "<strong>Risque :</strong>" not in html


def test_settings_labels_risk_thresholds_as_debt_exposure(tmp_path: Path) -> None:
    client = _logged_in_client(_create_test_app(tmp_path))

    html = client.get("/settings").get_data(as_text=True)

    assert '<legend class="fs-6 fw-bold">Exposition dette</legend>' in html
    assert '<legend class="fs-6 fw-bold">Risque</legend>' not in html
    # Les noms de champs, eux, ne changent pas (config.json inchangé).
    assert 'name="risk_warning"' in html
    assert 'name="risk_critical"' in html


def test_csv_export_headers_mark_the_values_as_estimates(tmp_path: Path) -> None:
    client = _logged_in_client(_create_test_app(tmp_path))

    body = client.get("/export_csv").data.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(body), delimiter=";"))

    assert rows[0] == [
        "Nom",
        "Type",
        "RDA",
        "Criticité",
        "DICPé - Disponibilité",
        "DICPé - Intégrité",
        "DICPé - Confidentialité",
        "DICPé - Pérennité attendue",
        "Score",
        "Max Score",
        "Pourcentage",
        "Dernière évaluation",
        "Évaluateur",
        "Exposition dette",
    ]
    # Les valeurs exportées restent les codes stockés, inchangés.
    assert rows[1][4:8] == ["D2", "I3", "C1", "P3"]


def test_help_texts_warn_about_the_dicp_confusion() -> None:
    info_texts_path = TEMPLATES.parent / "static" / "info_texts.json"
    info_texts = json.loads(info_texts_path.read_text(encoding="utf-8"))

    for key in ("app-disponibilite", "app-integrite", "app-confidentialite"):
        assert "analyse de risques" in "".join(info_texts[key]), key
    assert "Preuve" in "".join(info_texts["app-perennite"])
    assert "échelle de criticité est inverse" in "".join(info_texts["app-criticite"])
