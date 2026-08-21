"""Validation des données reçues par l'interface ADM."""

import json
from collections.abc import Mapping
from datetime import date
from typing import Final

from ADM.database import Application
from ADM.schemas import DisplayThresholds, parse_display_thresholds

APPLICATION_CHOICES: Final[tuple[tuple[str, frozenset[str]], ...]] = (
    ("type_app", frozenset({"Interne", "Editeur", "Open source"})),
    ("hosting", frozenset({"On prem", "Hybride", "Cloud", "SaaS"})),
    ("criticite", frozenset({"1", "2", "3", "4"})),
    ("disponibilite", frozenset({"D1", "D2", "D3", "D4"})),
    ("integrite", frozenset({"I1", "I2", "I3", "I4"})),
    ("confidentialite", frozenset({"C1", "C2", "C3", "C4"})),
    ("perennite", frozenset({"P1", "P2", "P3", "P4"})),
)


class InputValidationError(ValueError):
    """Signale une entrée utilisateur invalide et affichable sans donnée sensible."""


def validate_application_form(form: Mapping[str, str], *, require_name: bool) -> dict[str, object]:
    """Valide et normalise les champs d'un formulaire application."""
    validated: dict[str, object] = {}
    if require_name:
        validated["name"] = _required_text(form, "name", "Le nom de l'application")
    validated["rda"] = _required_text(form, "rda", "Le responsable")
    possession = _required_text(form, "possession", "La date de mise en possession")
    try:
        validated["possession"] = date.fromisoformat(possession)
    except ValueError as error:
        raise InputValidationError(
            "La date de mise en possession doit être une date valide."
        ) from error
    for field, choices in APPLICATION_CHOICES:
        value = form.get(field, "")
        if value not in choices:
            raise InputValidationError(f"Le champ {field!r} contient une valeur invalide.")
        validated[field] = int(value) if field == "criticite" else value
    return validated


def validate_import(stream: object) -> list[Application]:
    """Décode et valide entièrement un export JSON avant toute écriture."""
    try:
        content = json.load(stream)  # type: ignore[arg-type]  # json.load accepte tout objet avec read().
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InputValidationError(
            "Le fichier fourni n'est pas un document JSON valide."
        ) from error
    if not isinstance(content, list):
        raise InputValidationError("La racine du fichier importé doit être une liste.")
    applications: list[Application] = []
    for index, record in enumerate(content, start=1):
        if not isinstance(record, dict):
            raise InputValidationError(f"L'application n°{index} doit être un objet JSON.")
        try:
            applications.append(Application.from_dict(record))
        except ValueError as error:
            raise InputValidationError(f"Application n°{index} invalide : {error}") from error
    return applications


def validate_login_form(form: Mapping[str, str]) -> tuple[str, str]:
    """Valide la présence des identifiants sans les journaliser ni les normaliser."""
    username = _required_text(form, "username", "Le nom d'utilisateur")
    password = form.get("password", "")
    if not password:
        raise InputValidationError("Le mot de passe est obligatoire.")
    if len(password) > 255:
        raise InputValidationError("Le mot de passe ne doit pas dépasser 255 caractères.")
    return username, password


def validate_evaluation_form(
    form: Mapping[str, str], question_keys: frozenset[str], scoring_values: frozenset[str]
) -> None:
    """Refuse les questions, réponses et textes inattendus d'une évaluation."""
    evaluator_name = form.get("evaluator_name", "").strip()
    if len(evaluator_name) > 255:
        raise InputValidationError("Le nom de l'évaluateur ne doit pas dépasser 255 caractères.")
    ignored_fields = {"csrf_token", "evaluator_name", "save_draft"}
    for field, value in form.items():
        question_key = field.removesuffix("_comment")
        if field in ignored_fields:
            continue
        if question_key not in question_keys:
            raise InputValidationError(f"Le champ d'évaluation {field!r} est inconnu.")
        if field.endswith("_comment"):
            if len(value) > 2_000:
                raise InputValidationError(f"Le commentaire {field!r} est trop long.")
        elif value not in scoring_values:
            raise InputValidationError(f"La réponse à la question {field!r} est invalide.")


def _required_text(form: Mapping[str, str], field: str, label: str) -> str:
    value = form.get(field, "").strip()
    if not value:
        raise InputValidationError(f"{label} est obligatoire.")
    if len(value) > 255:
        raise InputValidationError(f"{label} ne doit pas dépasser 255 caractères.")
    return value

def _required_number(form: Mapping[str, str], field: str, label: str) -> float:
    raw_value = form.get(field, "").strip()
    if not raw_value:
        raise InputValidationError(f"{label} est obligatoire.")
    try:
        return float(raw_value)
    except ValueError as error:
        raise InputValidationError(f"{label} doit être un nombre.") from error


def validate_display_thresholds_form(form: Mapping[str, str]) -> DisplayThresholds:
    """Valide le formulaire de configuration des seuils d'affichage (US4.2)."""
    raw: dict[str, dict[str, float]] = {
        "score": {
            "warning": _required_number(form, "score_warning", "Le seuil d'alerte du score"),
            "critical": _required_number(form, "score_critical", "Le seuil critique du score"),
        },
        "risk": {
            "warning": _required_number(form, "risk_warning", "Le seuil d'alerte du risque"),
            "critical": _required_number(form, "risk_critical", "Le seuil critique du risque"),
        },
    }
    try:
        return parse_display_thresholds(raw)
    except ValueError as error:
        raise InputValidationError(str(error)) from error
    