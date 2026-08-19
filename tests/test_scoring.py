import pytest

from ADM.scoring import (
    compute_categories,
    compute_scoring_map,
    filter_questions_by_type,
)


def sample_questions() -> dict[str, dict[str, dict[str, object]]]:
    return {
        "Architecture": {
            "_description": {},
            "api": {
                "app_types": ["Interne"],
                "options": [
                    {"value": "Oui", "score": 0},
                    {"value": "Non applicable", "score": None},
                ],
            },
            "cloud": {
                "hosting_types": ["Cloud"],
                "options": [{"value": "Non", "score": 3}],
            },
        }
    }


def test_compute_categories_ignores_metadata() -> None:
    assert compute_categories(sample_questions()) == {"Architecture": ["api", "cloud"]}


def test_compute_scoring_map_collects_scores() -> None:
    assert compute_scoring_map(sample_questions()) == {
        "Oui": 0,
        "Non applicable": None,
        "Non": 3,
    }


def test_compute_scoring_map_rejects_conflicting_scores() -> None:
    questions = sample_questions()
    questions["Architecture"]["cloud"]["options"] = [{"value": "Oui", "score": 2}]

    with pytest.raises(ValueError, match="contradictoires"):
        compute_scoring_map(questions)


def test_filter_questions_normalizes_values_and_combines_filters() -> None:
    filtered = filter_questions_by_type(sample_questions(), " interne ", " cloud ")

    assert set(filtered["Architecture"]) == {"_description", "api", "cloud"}


def test_filter_questions_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="type_app"):
        filter_questions_by_type(sample_questions(), " ", "Cloud")
