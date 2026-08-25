"""Tests des structures et validations des documents externes."""

import pytest

from ADM.schemas import AppConfig, DisplayThresholds, Thresholds, parse_questions


def test_configuration_uses_explicit_typed_defaults() -> None:
    assert AppConfig.from_object({}) == AppConfig()


def test_configuration_rejects_an_empty_backend() -> None:
    with pytest.raises(ValueError, match="db_backend"):
        AppConfig.from_object({"db_backend": " "})


def test_configuration_parses_display_thresholds() -> None:
    config = AppConfig.from_object(
        {
            "display_thresholds": {
                "score": {"warning": 25, "critical": 55},
                "risk": {"warning": 80.5, "critical": 250},
            }
        }
    )

    assert config.display_thresholds == DisplayThresholds(
        score=Thresholds(warning=25, critical=55),
        risk=Thresholds(warning=80.5, critical=250),
    )

def test_configuration_parses_auth_backend_default() -> None:
    assert AppConfig.from_object({}).auth_backend == "local"


def test_configuration_normalizes_auth_backend_case() -> None:
    config = AppConfig.from_object({"auth_backend": " LDAP "})
    assert config.auth_backend == "ldap"
    

@pytest.mark.parametrize(
    "thresholds",
    [
        {"score": {"warning": -1, "critical": 60}},
        {"score": {"warning": 60, "critical": 60}},
        {"risk": {"warning": True, "critical": 350}},
        {"risk": "incorrect"},
    ],
)
def test_configuration_rejects_invalid_display_thresholds(
    thresholds: object,
) -> None:
    with pytest.raises(ValueError, match="seuil"):
        AppConfig.from_object({"display_thresholds": thresholds})


def test_questions_reject_a_non_positive_weight() -> None:
    questions = {
        "Architecture": {
            "api": {
                "label": "Question fictive ?",
                "type": "select",
                "weight": 0,
                "options": [{"value": "Oui", "score": 0}],
            }
        }
    }

    with pytest.raises(ValueError, match="poids.*entier positif"):
        parse_questions(questions)


def test_questions_are_normalized_into_the_typed_shape() -> None:
    questions = {
        "Architecture": {
            "api": {
                "label": "Question fictive ?",
                "type": "select",
                "options": [{"value": "Non applicable", "score": None}],
            }
        }
    }

    parsed = parse_questions(questions)

    assert parsed["Architecture"]["api"]["weight"] == 1
    assert parsed["Architecture"]["api"]["options"][0]["score"] is None
