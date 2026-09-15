"""Validation des données reçues par l'interface ADM."""

import json
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Final

from werkzeug.datastructures import MultiDict

from ADM.accounts_service import ROLES
from ADM.database import Application
from ADM.schemas import DisplayThresholds, parse_display_thresholds

# Valeurs de type d'application et d'hébergement, utilisées à la fois pour
# valider une application (APPLICATION_CHOICES ci-dessous) et pour restreindre
# les filtres app_types/hosting_types d'une question (US4.3) au même
# vocabulaire, dans un ordre d'affichage stable pour les cases à cocher.
QUESTION_APP_TYPES: Final[tuple[str, ...]] = ("Interne", "Editeur", "Open source")
QUESTION_HOSTING_TYPES: Final[tuple[str, ...]] = ("On prem", "Hybride", "Cloud", "SaaS")

QUESTION_KEY_MAX_LENGTH: Final = 100
QUESTION_LABEL_MAX_LENGTH: Final = 500
QUESTION_HELP_TEXT_MAX_LENGTH: Final = 10_000

APPLICATION_CHOICES: Final[tuple[tuple[str, frozenset[str]], ...]] = (
    ("type_app", frozenset(QUESTION_APP_TYPES)),
    ("hosting", frozenset(QUESTION_HOSTING_TYPES)),
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


def validate_account_creation_form(form: Mapping[str, str]) -> dict[str, object]:
    """Valide le formulaire de création d'un compte (US6.1)."""
    username = _required_text(form, "username", "Le nom d'utilisateur")
    password = form.get("password", "")
    confirmation = form.get("password_confirm", "")
    if not password:
        raise InputValidationError("Le mot de passe est obligatoire.")
    if len(password) > 255:
        raise InputValidationError("Le mot de passe ne doit pas dépasser 255 caractères.")
    if password != confirmation:
        raise InputValidationError("Les mots de passe ne correspondent pas.")
    role = form.get("role", "")
    if role not in ROLES:
        raise InputValidationError(f"Le rôle doit être l'un de {sorted(ROLES)}.")
    return {"username": username, "password": password, "role": role}


def validate_password_reset_form(form: Mapping[str, str]) -> str:
    """Valide le nouveau mot de passe imposé à un compte par un administrateur (US6.2)."""
    password = form.get("password", "")
    confirmation = form.get("password_confirm", "")
    if not password:
        raise InputValidationError("Le mot de passe est obligatoire.")
    if len(password) > 255:
        raise InputValidationError("Le mot de passe ne doit pas dépasser 255 caractères.")
    if password != confirmation:
        raise InputValidationError("Les mots de passe ne correspondent pas.")
    return password


def validate_password_change_form(form: Mapping[str, str]) -> tuple[str, str]:
    """Valide le formulaire d'auto-changement de mot de passe (US6.2).

    Contrairement à ``validate_password_reset_form`` (réinitialisation par un
    administrateur), ce formulaire exige le mot de passe actuel : sa validité est
    vérifiée par l'appelant, cette fonction se limitant à la forme des champs.
    """
    current_password = form.get("current_password", "")
    if not current_password:
        raise InputValidationError("Le mot de passe actuel est obligatoire.")
    new_password = form.get("new_password", "")
    confirmation = form.get("new_password_confirm", "")
    if not new_password:
        raise InputValidationError("Le nouveau mot de passe est obligatoire.")
    if len(new_password) > 255:
        raise InputValidationError("Le mot de passe ne doit pas dépasser 255 caractères.")
    if new_password != confirmation:
        raise InputValidationError("Les mots de passe ne correspondent pas.")
    if new_password == current_password:
        raise InputValidationError("Le nouveau mot de passe doit être différent de l'actuel.")
    return current_password, new_password


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


def _required_category(form: Mapping[str, str], categories: Sequence[str]) -> str:
    category = form.get("category", "")
    if category not in categories:
        raise InputValidationError("La catégorie sélectionnée est invalide.")
    return category


def _parse_question_key(form: Mapping[str, str]) -> str:
    key = form.get("key", "").strip()
    if not key:
        raise InputValidationError("La clé technique de la question est obligatoire.")
    if len(key) > QUESTION_KEY_MAX_LENGTH:
        raise InputValidationError("La clé technique de la question est trop longue.")
    if key.startswith("_"):
        raise InputValidationError("La clé technique de la question ne peut pas commencer par '_'.")
    return key


def _question_options_from_form(form: MultiDict[str, str]) -> list[dict[str, object]]:
    """Reconstitue la liste ordonnée d'options depuis les champs répétés du formulaire.

    ``option_value`` et ``option_score`` sont soumis en parallèle (mêmes index),
    une ligne dont la valeur est vide étant ignorée (suppression d'une option
    côté client, voir question_form.html). Un score vide signifie « Non
    applicable » (``null``, voir docs/BUSINESS_RULES.md).
    """
    values = form.getlist("option_value")
    scores = form.getlist("option_score")
    if len(values) != len(scores):
        raise InputValidationError("Les options de la question sont incohérentes.")
    options: list[dict[str, object]] = []
    seen: set[str] = set()
    for raw_value, raw_score in zip(values, scores, strict=True):
        value = raw_value.strip()
        if not value:
            continue
        if value in seen:
            raise InputValidationError(f"L'option {value!r} est dupliquée.")
        seen.add(value)
        stripped_score = raw_score.strip()
        score: int | None
        if not stripped_score:
            score = None
        else:
            try:
                score = int(stripped_score)
            except ValueError as error:
                raise InputValidationError(
                    f"Le score de l'option {value!r} doit être un entier ou vide."
                ) from error
        options.append({"value": value, "score": score})
    if not options:
        raise InputValidationError("La question doit avoir au moins une option.")
    return options


def _question_filter_from_form(
    form: MultiDict[str, str], field: str, allowed_values: Sequence[str]
) -> list[str]:
    """Valide un filtre à cases à cocher (``app_types``/``hosting_types``).

    Au moins une valeur doit être cochée (voir docs/BUSINESS_RULES.md : « lorsqu'ils
    existent, [ces filtres] sont des listes non vides ») ; l'ordre de référence
    (``allowed_values``) est conservé plutôt que l'ordre de soumission du formulaire.
    """
    selected = {value for value in form.getlist(field) if value in allowed_values}
    if not selected:
        raise InputValidationError(f"Sélectionnez au moins une valeur pour le filtre {field!r}.")
    return [value for value in allowed_values if value in selected]


def _question_definition_from_form(form: MultiDict[str, str]) -> dict[str, object]:
    label = form.get("label", "").strip()
    if not label:
        raise InputValidationError("Le libellé de la question est obligatoire.")
    if len(label) > QUESTION_LABEL_MAX_LENGTH:
        raise InputValidationError("Le libellé de la question est trop long.")
    weight_raw = form.get("weight", "").strip()
    if not weight_raw:
        raise InputValidationError("Le poids de la question est obligatoire.")
    try:
        weight = int(weight_raw)
    except ValueError as error:
        raise InputValidationError("Le poids de la question doit être un entier.") from error
    if weight <= 0:
        raise InputValidationError(
            "Le poids de la question doit être un entier strictement positif."
        )
    return {
        "label": label,
        "type": "select",
        "weight": weight,
        "options": _question_options_from_form(form),
        "app_types": _question_filter_from_form(form, "app_types", QUESTION_APP_TYPES),
        "hosting_types": _question_filter_from_form(form, "hosting_types", QUESTION_HOSTING_TYPES),
    }


def _question_help_text_from_form(form: Mapping[str, str]) -> str:
    help_text = form.get("help_text", "").strip()
    if len(help_text) > QUESTION_HELP_TEXT_MAX_LENGTH:
        raise InputValidationError("L'aide en ligne de la question est trop longue.")
    return help_text


def validate_question_create_form(
    form: MultiDict[str, str], *, categories: Sequence[str]
) -> tuple[str, str, dict[str, object], str]:
    """Valide le formulaire d'ajout d'une question (US4.3).

    Retourne ``(catégorie, clé, définition brute, aide en ligne)``. ``categories``
    restreint le choix à celles déjà existantes dans le questionnaire : ce
    formulaire ne permet ni de créer, ni de renommer, ni de supprimer une
    catégorie (portée volontairement réduite de l'US4.3, voir backlog.md).
    """
    category = _required_category(form, categories)
    key = _parse_question_key(form)
    definition = _question_definition_from_form(form)
    help_text = _question_help_text_from_form(form)
    return category, key, definition, help_text


def validate_question_edit_form(
    form: MultiDict[str, str], *, categories: Sequence[str]
) -> tuple[str, dict[str, object], str]:
    """Valide le formulaire de modification d'une question (US4.3).

    La clé technique n'est volontairement pas reprise ici : elle est immuable
    après création (voir docs/BUSINESS_RULES.md) et provient de l'URL, pas du
    formulaire. Retourne ``(nouvelle catégorie, définition brute, aide en ligne)``.
    """
    category = _required_category(form, categories)
    definition = _question_definition_from_form(form)
    help_text = _question_help_text_from_form(form)
    return category, definition, help_text
