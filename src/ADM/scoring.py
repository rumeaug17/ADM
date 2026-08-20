"""Calculs métier relatifs au questionnaire de dette applicative."""

from collections.abc import Mapping, Sequence

from ADM.schemas import QuestionDefinition, Questions


def compute_categories(questions: Questions) -> dict[str, list[str]]:
    """Retourne les clés de questions visibles, regroupées par catégorie."""
    return {
        category: [key for key in definitions if not key.startswith("_")]
        for category, definitions in questions.items()
    }


def compute_scoring_map(questions: Questions) -> dict[str, int | None]:
    """Associe chaque valeur de réponse à son score et valide les définitions."""
    scoring_map: dict[str, int | None] = {}
    for definitions in questions.values():
        for definition in definitions.values():
            options = definition.get("options", ())
            if not isinstance(options, Sequence) or isinstance(options, (str, bytes)):
                raise ValueError("Le champ 'options' doit être une liste.")
            for option in options:
                value, score = _validated_option(option)
                previous_score = scoring_map.get(value)
                if value in scoring_map and previous_score != score:
                    raise ValueError(f"Scores contradictoires pour l'option {value!r}.")
                scoring_map[value] = score
    return scoring_map


def filter_questions_by_type(
    questions: Questions,
    type_app: str,
    hosting: str,
) -> dict[str, dict[str, QuestionDefinition]]:
    """Filtre les questions applicables au type et à l'hébergement indiqués."""
    normalized_type = _normalized_required_value(type_app, "type_app")
    normalized_hosting = _normalized_required_value(hosting, "hosting")
    return {
        category: {
            key: definition
            for key, definition in definitions.items()
            if _matches_filter(definition, "app_types", normalized_type)
            and _matches_filter(definition, "hosting_types", normalized_hosting)
        }
        for category, definitions in questions.items()
    }


def _validated_option(option: object) -> tuple[str, int | None]:
    if not isinstance(option, Mapping):
        raise ValueError("Chaque option doit être un objet JSON.")
    value = option.get("value")
    score = option.get("score")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Chaque option doit avoir une valeur textuelle non vide.")
    if score is not None and (not isinstance(score, int) or isinstance(score, bool)):
        raise ValueError(f"Le score de l'option {value!r} doit être un entier ou null.")
    return value, score


def _normalized_required_value(value: str, field_name: str) -> str:
    normalized = value.strip().casefold()
    if not normalized:
        raise ValueError(f"Le champ {field_name!r} ne peut pas être vide.")
    return normalized


def _matches_filter(
    definition: QuestionDefinition,
    field_name: str,
    actual_value: str,
) -> bool:
    allowed_values = definition.get(field_name)
    if allowed_values is None:
        return True
    if not isinstance(allowed_values, Sequence) or isinstance(allowed_values, (str, bytes)):
        raise ValueError(f"Le champ {field_name!r} doit être une liste de chaînes.")
    if not all(isinstance(value, str) for value in allowed_values):
        raise ValueError(f"Le champ {field_name!r} doit contenir uniquement des chaînes.")
    return actual_value in {value.strip().casefold() for value in allowed_values}
