"""Tests unitaires des calculs de synthèse et de la génération graphique."""

import base64

import matplotlib.pyplot as plt

from ADM.services import axis_scores, category_sums, generate_radar_chart


def questions() -> dict[str, dict[str, dict[str, object]]]:
    """Retourne un questionnaire minimal avec une question pondérée."""
    return {
        "Architecture": {
            "urbanisation": {"weight": 2},
            "documentation": {"weight": 1},
        },
        "Exploitation": {"supervision": {"weight": 3}},
    }


def test_category_sums_applies_weights_and_ignores_missing_answers() -> None:
    application: dict[str, object] = {
        "responses": {"urbanisation": "Partiel", "supervision": "Non applicable"}
    }
    categories = {
        "Architecture": ["urbanisation", "documentation"],
        "Exploitation": ["supervision"],
    }
    scoring = {"Partiel": 2, "Non applicable": None}

    assert category_sums(application, questions(), categories, scoring) == {
        "Architecture": 4,
        "Exploitation": 0,
    }


def test_axis_scores_averages_each_axis_across_answered_applications() -> None:
    applications: list[dict[str, object]] = [
        {
            "responses": {
                "urbanisation": "Oui",
                "documentation": "Non",
                "supervision": "Partiel",
            }
        },
        {"responses": {"urbanisation": "Non", "supervision": "Non applicable"}},
        {"responses": "format invalide"},
    ]
    categories = {
        "Architecture": ["urbanisation", "documentation"],
        "Exploitation": ["supervision"],
    }
    scoring = {"Oui": 0, "Partiel": 2, "Non": 3, "Non applicable": None}

    assert axis_scores(applications, questions(), categories, scoring) == {
        "Architecture": 3.75,
        "Exploitation": 6.0,
    }


def test_generate_radar_chart_returns_a_png_and_closes_its_figure() -> None:
    open_figures_before = set(plt.get_fignums())

    encoded_chart = generate_radar_chart({"Architecture": 2.5, "Exploitation": 1.0})

    chart = base64.b64decode(encoded_chart, validate=True)
    assert chart.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(chart) > 1_000
    assert set(plt.get_fignums()) == open_figures_before
