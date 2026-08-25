"""Structures typées et validation des documents externes d'ADM."""

from dataclasses import dataclass
from typing import NotRequired, Required, TypedDict


class QuestionOption(TypedDict):
    """Option proposée pour une question et valeur utilisée par le score."""

    value: str
    score: int | None


class QuestionDefinition(TypedDict):
    """Définition validée d'une question du questionnaire."""

    label: NotRequired[str]
    type: NotRequired[str]
    weight: NotRequired[int]
    options: list[QuestionOption]
    app_types: NotRequired[list[str]]
    hosting_types: NotRequired[list[str]]


Questions = dict[str, dict[str, QuestionDefinition]]


class EvaluationImport(TypedDict, total=False):
    """Forme JSON acceptée pour une évaluation importée."""

    id: int | None
    application_id: int | None
    score: Required[int]
    answered_questions: Required[int]
    last_evaluation: Required[str]
    evaluator_name: Required[str]
    responses: dict[str, object]
    comments: dict[str, object]
    created_at: str | None


class ApplicationImport(TypedDict, total=False):
    """Forme JSON acceptée pour une application importée."""

    id: int | None
    name: Required[str]
    rda: Required[str]
    possession: str | None
    type_app: Required[str]
    hosting: Required[str]
    criticite: Required[int]
    disponibilite: Required[str]
    integrite: Required[str]
    confidentialite: Required[str]
    perennite: Required[str]
    score: int | None
    answered_questions: int | None
    last_evaluation: str | None
    responses: dict[str, object]
    comments: dict[str, object]
    evaluator_name: str | None
    evaluations: list[EvaluationImport]


@dataclass(frozen=True, slots=True)
class Thresholds:
    """Seuils croissants utilisés pour qualifier un indicateur."""

    warning: float
    critical: float


@dataclass(frozen=True, slots=True)
class DisplayThresholds:
    """Seuils de présentation des scores et des risques."""

    score: Thresholds = Thresholds(warning=30, critical=60)
    risk: Thresholds = Thresholds(warning=100, critical=350)


@dataclass(frozen=True, slots=True)
@dataclass(frozen=True, slots=True)
class AppConfig:
    """Configuration non sensible chargée depuis ``config.json``."""

    db_backend: str = "json"
    json_connection_url: str = "applications.json"
    auth_backend: str = "local"
    accounts_connection_url: str = "accounts.json"
    display_thresholds: DisplayThresholds = DisplayThresholds()

    @classmethod
    def from_object(cls, value: object) -> "AppConfig":
        if not isinstance(value, dict):
            raise ValueError("La configuration doit être un objet JSON.")
        backend = _optional_non_empty_string(value, "db_backend", "json").casefold()
        json_url = _optional_non_empty_string(value, "json_connection_url", "applications.json")
        auth_backend = _optional_non_empty_string(value, "auth_backend", "local").casefold()
        accounts_url = _optional_non_empty_string(
            value, "accounts_connection_url", "accounts.json"
        )
        display_thresholds = parse_display_thresholds(value.get("display_thresholds", {}))
        return cls(
            db_backend=backend,
            json_connection_url=json_url,
            auth_backend=auth_backend,
            accounts_connection_url=accounts_url,
            display_thresholds=display_thresholds,
        )


def parse_display_thresholds(value: object) -> DisplayThresholds:
    if not isinstance(value, dict):
        raise ValueError("Le champ de configuration 'display_thresholds' doit être un objet.")
    return DisplayThresholds(
        score=_parse_thresholds(value.get("score", {}), "score", 30, 60),
        risk=_parse_thresholds(value.get("risk", {}), "risk", 100, 350),
    )


def display_thresholds_to_dict(thresholds: DisplayThresholds) -> dict[str, dict[str, float]]:
    """Sérialise les seuils au format attendu par config.json."""
    return {
        "score": {"warning": thresholds.score.warning, "critical": thresholds.score.critical},
        "risk": {"warning": thresholds.risk.warning, "critical": thresholds.risk.critical},
    }


def _parse_thresholds(
    value: object, indicator: str, default_warning: float, default_critical: float
) -> Thresholds:
    if not isinstance(value, dict):
        raise ValueError(f"Les seuils de {indicator!r} doivent être un objet.")
    warning = value.get("warning", default_warning)
    critical = value.get("critical", default_critical)
    for name, threshold in (("warning", warning), ("critical", critical)):
        if not isinstance(threshold, (int, float)) or isinstance(threshold, bool) or threshold < 0:
            raise ValueError(
                f"Le seuil {name!r} de {indicator!r} doit être un nombre positif ou nul."
            )
    if warning >= critical:
        raise ValueError(
            f"Le seuil 'warning' de {indicator!r} doit être inférieur au seuil 'critical'."
        )
    return Thresholds(warning=float(warning), critical=float(critical))


def parse_questions(value: object) -> Questions:
    """Valide le questionnaire complet et retourne sa structure typée."""
    if not isinstance(value, dict) or not value:
        raise ValueError("Les questions doivent être un objet JSON non vide.")
    questions: Questions = {}
    for category, definitions in value.items():
        if (
            not isinstance(category, str)
            or not category.strip()
            or not isinstance(definitions, dict)
        ):
            raise ValueError("Chaque catégorie doit être un objet JSON nommé.")
        questions[category] = {
            key: _parse_question(key, definition) for key, definition in definitions.items()
        }
    return questions


def _parse_question(key: object, value: object) -> QuestionDefinition:
    if not isinstance(key, str) or not key.strip() or not isinstance(value, dict):
        raise ValueError("Chaque question doit être un objet JSON nommé.")
    if key.startswith("_"):
        return {"options": []}
    label = _required_non_empty_string(value, "label", key)
    question_type = _required_non_empty_string(value, "type", key)
    weight = value.get("weight", 1)
    if not isinstance(weight, int) or isinstance(weight, bool) or weight <= 0:
        raise ValueError(f"Le poids de la question {key!r} doit être un entier positif.")
    options_value = value.get("options")
    if not isinstance(options_value, list) or not options_value:
        raise ValueError(f"Les options de la question {key!r} doivent former une liste non vide.")
    options = [_parse_option(option, key) for option in options_value]
    definition: QuestionDefinition = {
        "label": label,
        "type": question_type,
        "weight": weight,
        "options": options,
    }
    if "app_types" in value:
        definition["app_types"] = _string_list(value["app_types"], "app_types", key)
    if "hosting_types" in value:
        definition["hosting_types"] = _string_list(value["hosting_types"], "hosting_types", key)
    return definition


def _parse_option(value: object, question_key: str) -> QuestionOption:
    if not isinstance(value, dict):
        raise ValueError(f"Chaque option de la question {question_key!r} doit être un objet.")
    option_value = _required_non_empty_string(value, "value", question_key)
    score = value.get("score")
    if score is not None and (not isinstance(score, int) or isinstance(score, bool)):
        raise ValueError(f"Le score de l'option {option_value!r} doit être un entier ou null.")
    return {"value": option_value, "score": score}


def _string_list(value: object, field: str, question_key: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, str) and item.strip() for item in value)
    ):
        raise ValueError(
            f"Le champ {field!r} de la question {question_key!r} doit être une liste de chaînes."
        )
    return list(value)


def _required_non_empty_string(value: dict[object, object], field: str, context: str) -> str:
    result = value.get(field)
    if not isinstance(result, str) or not result.strip():
        raise ValueError(f"Le champ {field!r} de {context!r} doit être une chaîne non vide.")
    return result


def _optional_non_empty_string(value: dict[object, object], field: str, default: str) -> str:
    result = value.get(field, default)
    if not isinstance(result, str) or not result.strip():
        raise ValueError(f"Le champ de configuration {field!r} doit être une chaîne non vide.")
    return result
