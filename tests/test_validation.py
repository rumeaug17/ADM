"""Tests des validations de la phase de sécurisation."""

import io
import json

import pytest
from werkzeug.datastructures import MultiDict

from ADM.validation import (
    InputValidationError,
    validate_application_form,
    validate_evaluation_form,
    validate_import,
    validate_password_change_form,
    validate_password_reset_form,
    validate_question_create_form,
    validate_question_edit_form,
)


def valid_form() -> dict[str, str]:
    return {
        "name": "Application fictive",
        "rda": "Responsable fictif",
        "possession": "2025-01-15",
        "type_app": "Interne",
        "hosting": "Cloud",
        "criticite": "2",
        "disponibilite": "D2",
        "integrite": "I2",
        "confidentialite": "C2",
        "perennite": "P2",
    }


def test_application_form_reports_the_invalid_field() -> None:
    form = valid_form()
    form["disponibilite"] = "niveau inconnu"

    with pytest.raises(InputValidationError, match="disponibilite"):
        validate_application_form(form, require_name=True)


def test_application_form_rejects_invalid_date() -> None:
    form = valid_form()
    form["possession"] = "2025-02-30"

    with pytest.raises(InputValidationError, match="date de mise en possession"):
        validate_application_form(form, require_name=True)


def test_import_rejects_non_list_root() -> None:
    stream = io.BytesIO(json.dumps({"name": "Objet isolé"}).encode())

    with pytest.raises(InputValidationError, match="racine.*liste"):
        validate_import(stream)


def test_import_identifies_invalid_record() -> None:
    stream = io.BytesIO(json.dumps([{"name": "Enregistrement incomplet"}]).encode())

    with pytest.raises(InputValidationError, match="Application n°1.*rda"):
        validate_import(stream)


def test_evaluation_rejects_unknown_question() -> None:
    with pytest.raises(InputValidationError, match="champ d'évaluation.*inconnu"):
        validate_evaluation_form(
            {"question_inconnue": "Oui"}, frozenset({"question_connue"}), frozenset({"Oui"})
        )


def test_password_reset_form_rejects_mismatched_confirmation() -> None:
    with pytest.raises(InputValidationError, match="ne correspondent pas"):
        validate_password_reset_form({"password": "secret-un", "password_confirm": "secret-deux"})


def test_password_reset_form_returns_password_on_match() -> None:
    password = validate_password_reset_form(
        {"password": "nouveau-secret", "password_confirm": "nouveau-secret"}
    )

    assert password == "nouveau-secret"


def test_password_change_form_requires_current_password() -> None:
    with pytest.raises(InputValidationError, match="mot de passe actuel"):
        validate_password_change_form(
            {"new_password": "nouveau-secret", "new_password_confirm": "nouveau-secret"}
        )


def test_password_change_form_rejects_identical_new_password() -> None:
    with pytest.raises(InputValidationError, match="différent de l'actuel"):
        validate_password_change_form(
            {
                "current_password": "meme-secret",
                "new_password": "meme-secret",
                "new_password_confirm": "meme-secret",
            }
        )


def test_password_change_form_returns_both_passwords_on_success() -> None:
    current, new = validate_password_change_form(
        {
            "current_password": "ancien-secret",
            "new_password": "nouveau-secret",
            "new_password_confirm": "nouveau-secret",
        }
    )

    assert (current, new) == ("ancien-secret", "nouveau-secret")


def valid_question_form() -> MultiDict[str, str]:
    return MultiDict(
        [
            ("category", "Architecture"),
            ("key", "api"),
            ("label", "Utilise-t-on des API standardisées ?"),
            ("weight", "2"),
            ("option_value", "Oui"),
            ("option_score", "0"),
            ("option_value", "Non applicable"),
            ("option_score", ""),
            ("app_types", "Interne"),
            ("hosting_types", "Cloud"),
            ("help_text", "Un peu d'aide."),
        ]
    )


def test_question_create_form_accepts_a_valid_submission() -> None:
    category, key, definition, help_text = validate_question_create_form(
        valid_question_form(), categories=["Architecture", "Sécurité"]
    )

    assert (category, key) == ("Architecture", "api")
    assert definition["label"] == "Utilise-t-on des API standardisées ?"
    assert definition["weight"] == 2
    assert definition["options"] == [
        {"value": "Oui", "score": 0},
        {"value": "Non applicable", "score": None},
    ]
    assert definition["app_types"] == ["Interne"]
    assert definition["hosting_types"] == ["Cloud"]
    assert help_text == "Un peu d'aide."


def test_question_create_form_rejects_unknown_category() -> None:
    form = valid_question_form()
    form["category"] = "Inexistante"

    with pytest.raises(InputValidationError, match="catégorie"):
        validate_question_create_form(form, categories=["Architecture"])


def test_question_create_form_requires_a_key() -> None:
    form = valid_question_form()
    del form["key"]

    with pytest.raises(InputValidationError, match="clé technique"):
        validate_question_create_form(form, categories=["Architecture"])


def test_question_create_form_rejects_a_key_starting_with_underscore() -> None:
    form = valid_question_form()
    form["key"] = "_commentaire"

    with pytest.raises(InputValidationError, match="'_'"):
        validate_question_create_form(form, categories=["Architecture"])


def test_question_create_form_rejects_zero_weight() -> None:
    form = valid_question_form()
    form["weight"] = "0"

    with pytest.raises(InputValidationError, match="strictement positif"):
        validate_question_create_form(form, categories=["Architecture"])


def test_question_create_form_rejects_non_numeric_weight() -> None:
    form = valid_question_form()
    form["weight"] = "abc"

    with pytest.raises(InputValidationError, match="entier"):
        validate_question_create_form(form, categories=["Architecture"])


def test_question_create_form_rejects_empty_option_list() -> None:
    form = MultiDict(
        [
            ("category", "Architecture"),
            ("key", "api"),
            ("label", "Question ?"),
            ("weight", "1"),
            ("option_value", ""),
            ("option_score", ""),
            ("app_types", "Interne"),
            ("hosting_types", "Cloud"),
        ]
    )

    with pytest.raises(InputValidationError, match="au moins une option"):
        validate_question_create_form(form, categories=["Architecture"])


def test_question_create_form_rejects_duplicate_option_values() -> None:
    form = valid_question_form()
    form.setlist("option_value", ["Oui", "Oui"])
    form.setlist("option_score", ["0", "1"])

    with pytest.raises(InputValidationError, match="dupliquée"):
        validate_question_create_form(form, categories=["Architecture"])


def test_question_create_form_rejects_non_numeric_option_score() -> None:
    form = valid_question_form()
    form.setlist("option_score", ["abc", ""])

    with pytest.raises(InputValidationError, match="score de l'option"):
        validate_question_create_form(form, categories=["Architecture"])


def test_question_create_form_rejects_no_app_type_selected() -> None:
    form = valid_question_form()
    del form["app_types"]

    with pytest.raises(InputValidationError, match="app_types"):
        validate_question_create_form(form, categories=["Architecture"])


def test_question_create_form_rejects_help_text_too_long() -> None:
    form = valid_question_form()
    form["help_text"] = "x" * 10_001

    with pytest.raises(InputValidationError, match="aide en ligne"):
        validate_question_create_form(form, categories=["Architecture"])


def test_question_edit_form_does_not_require_a_key() -> None:
    form = valid_question_form()
    del form["key"]

    category, definition, help_text = validate_question_edit_form(
        form, categories=["Architecture", "Sécurité"]
    )

    assert category == "Architecture"
    assert definition["label"] == "Utilise-t-on des API standardisées ?"
    assert help_text == "Un peu d'aide."


def test_all_post_routes_require_csrf_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADM_SECRET_KEY", "cle-factice-reservee-aux-tests")
    from ADM.app import create_app

    app = create_app({"TESTING": True})
    response = app.test_client().post("/login", data={})

    assert response.status_code == 400
    assert "requête envoyée est invalide" in response.get_data(as_text=True)
