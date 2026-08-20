"""Tests unitaires des calculs de synthèse et de la génération graphique."""

import base64
from unittest.mock import patch

from matplotlib.backends.backend_agg import FigureCanvasAgg

from ADM.schemas import Thresholds
from ADM.services import (
    axis_scores,
    build_evaluation_submission,
    category_sums,
    generate_radar_chart,
    summarize_catalogue,
)


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


def test_generate_radar_chart_returns_a_png_without_pyplot() -> None:
    with patch("ADM.services.FigureCanvasAgg", wraps=FigureCanvasAgg) as canvas_factory:
        encoded_chart = generate_radar_chart({"Architecture": 2.5, "Exploitation": 1.0})

    canvas_factory.assert_called_once()
    chart = base64.b64decode(encoded_chart, validate=True)
    assert chart.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(chart) > 1_000


def test_build_evaluation_submission_applies_weights() -> None:
    submission = build_evaluation_submission(
        {
            "urbanisation": "Partiel",
            "urbanisation_comment": "Justification factice",
            "csrf_token": "jeton-factice",
        },
        questions(),
        {"Partiel": 2, "Non applicable": None},
    )

    assert submission.responses == {"urbanisation": "Partiel"}
    assert submission.comments == {"urbanisation_comment": "Justification factice"}
    assert submission.score == 4
    assert submission.answered_questions == 2


def test_summarize_catalogue_ignores_unevaluated_metrics() -> None:
    summary = summarize_catalogue(
        [
            {"score": 6, "percentage": 40.0, "risque": 2.0},
            {"score": 9, "percentage": 70.0, "risque": 4.0},
            {"score": None, "percentage": None, "risque": None},
            {"score": True, "percentage": None, "risque": None},
        ]
    )

    assert summary.total_applications == 4
    assert summary.average_score == 7.5
    assert summary.applications_above_warning == 2
    assert summary.applications_above_critical == 1
    assert summary.global_risk == 3.0


def test_summarize_catalogue_returns_zero_without_evaluation() -> None:
    summary = summarize_catalogue([{"score": None}, {"name": "Application fictive"}])

    assert summary.total_applications == 2
    assert summary.average_score == 0


def test_summarize_catalogue_uses_configured_score_thresholds() -> None:
    summary = summarize_catalogue(
        [{"percentage": 25}, {"percentage": 55}, {"percentage": 75}],
        Thresholds(warning=20, critical=70),
    )

    assert summary.applications_above_warning == 3
    assert summary.applications_above_critical == 1
