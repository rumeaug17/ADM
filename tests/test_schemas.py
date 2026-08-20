"""Tests des structures et validations des documents externes."""

import pytest

from ADM.schemas import AppConfig, parse_questions


def test_configuration_uses_explicit_typed_defaults() -> None:
    assert AppConfig.from_object({}) == AppConfig()


def test_configuration_rejects_an_empty_backend() -> None:
    with pytest.raises(ValueError, match="db_backend"):
        AppConfig.from_object({"db_backend": " "})


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
