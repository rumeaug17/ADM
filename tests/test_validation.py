"""Tests des validations de la phase de sécurisation."""

import io
import json

import pytest

from ADM.validation import (
    InputValidationError,
    validate_application_form,
    validate_evaluation_form,
    validate_import,
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


def test_all_post_routes_require_csrf_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADM_SECRET_KEY", "cle-factice-reservee-aux-tests")
    from ADM.app import create_app

    app = create_app({"TESTING": True})
    response = app.test_client().post("/login", data={})

    assert response.status_code == 400
    assert "requête envoyée est invalide" in response.get_data(as_text=True)
