"""Tests des validations de la phase de sécurisation."""

import io
import json

import pytest

from ADM.validation import (
    InputValidationError,
    validate_application_form,
    validate_evaluation_form,
    validate_import,
    validate_password_change_form,
    validate_password_reset_form,
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


def test_all_post_routes_require_csrf_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADM_SECRET_KEY", "cle-factice-reservee-aux-tests")
    from ADM.app import create_app

    app = create_app({"TESTING": True})
    response = app.test_client().post("/login", data={})

    assert response.status_code == 400
    assert "requête envoyée est invalide" in response.get_data(as_text=True)
