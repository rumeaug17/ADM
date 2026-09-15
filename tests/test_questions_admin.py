"""Tests des opérations pures d'ajout/modification/suppression d'une question (US4.3)."""

import pytest

from ADM.questions_admin import add_question, delete_question, update_question


def sample_questions() -> dict[str, dict[str, dict[str, object]]]:
    return {
        "Architecture": {
            "api": {
                "label": "Utilise-t-on des API standardisées ?",
                "type": "select",
                "weight": 2,
                "options": [
                    {"value": "Oui", "score": 0},
                    {"value": "Non", "score": 3},
                    {"value": "Non applicable", "score": None},
                ],
                "app_types": ["Interne"],
                "hosting_types": ["Cloud"],
            }
        },
        "Sécurité": {},
    }


def valid_definition() -> dict[str, object]:
    return {
        "label": "Nouvelle question ?",
        "type": "select",
        "weight": 1,
        "options": [{"value": "Oui", "score": 0}, {"value": "Non", "score": 3}],
        "app_types": ["Interne"],
        "hosting_types": ["Cloud"],
    }


def test_add_question_inserts_into_existing_category() -> None:
    updated = add_question(sample_questions(), "Sécurité", "nouvelle", valid_definition())

    assert set(updated["Sécurité"]) == {"nouvelle"}
    assert updated["Architecture"]["api"]["label"] == "Utilise-t-on des API standardisées ?"


def test_add_question_rejects_unknown_category() -> None:
    with pytest.raises(ValueError, match="inconnue"):
        add_question(sample_questions(), "Inexistante", "nouvelle", valid_definition())


def test_add_question_rejects_duplicate_key() -> None:
    with pytest.raises(ValueError, match="existe déjà"):
        add_question(sample_questions(), "Architecture", "api", valid_definition())


def test_add_question_rejects_conflicting_option_score() -> None:
    """Une même valeur de réponse doit conserver le même score dans tout le
    questionnaire (docs/BUSINESS_RULES.md), y compris après l'ajout d'une question."""
    definition = valid_definition()
    definition["options"] = [{"value": "Oui", "score": 1}]  # "Oui" vaut 0 pour "api"

    with pytest.raises(ValueError, match="contradictoires"):
        add_question(sample_questions(), "Sécurité", "nouvelle", definition)


def test_update_question_replaces_definition_in_place() -> None:
    definition = valid_definition()
    definition["label"] = "Libellé mis à jour"

    updated = update_question(sample_questions(), "Architecture", "api", "Architecture", definition)

    assert updated["Architecture"]["api"]["label"] == "Libellé mis à jour"
    assert updated["Architecture"]["api"]["weight"] == 1


def test_update_question_moves_to_another_existing_category() -> None:
    updated = update_question(
        sample_questions(), "Architecture", "api", "Sécurité", valid_definition()
    )

    assert "api" not in updated["Architecture"]
    assert "api" in updated["Sécurité"]


def test_update_question_rejects_unknown_source() -> None:
    with pytest.raises(ValueError, match="introuvable"):
        update_question(
            sample_questions(), "Architecture", "inconnue", "Architecture", valid_definition()
        )


def test_update_question_rejects_unknown_target_category() -> None:
    with pytest.raises(ValueError, match="inconnue"):
        update_question(
            sample_questions(), "Architecture", "api", "Inexistante", valid_definition()
        )


def test_update_question_rejects_key_collision_in_target_category() -> None:
    questions = sample_questions()
    questions["Sécurité"]["api"] = dict(questions["Architecture"]["api"])

    with pytest.raises(ValueError, match="existe déjà"):
        update_question(questions, "Architecture", "api", "Sécurité", valid_definition())


def test_delete_question_removes_it() -> None:
    updated = delete_question(sample_questions(), "Architecture", "api")

    assert updated["Architecture"] == {}


def test_delete_question_rejects_unknown_question() -> None:
    with pytest.raises(ValueError, match="introuvable"):
        delete_question(sample_questions(), "Architecture", "inconnue")
