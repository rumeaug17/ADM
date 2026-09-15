"""Ajout, modification et suppression d'une question du questionnaire (US4.3).

Les catégories elles-mêmes ne sont pas gérées par ce module : une question ne
peut être ajoutée ou déplacée que vers une catégorie déjà existante dans le
questionnaire (aucune création, renommage ni suppression de catégorie --
portée volontairement réduite dans un premier temps, voir backlog.md).

Toute modification revalide l'intégralité du questionnaire résultant, pas
seulement la question modifiée : ``ADM.schemas.parse_questions`` garantit que
chaque question reste bien formée, et ``ADM.scoring.compute_scoring_map``
détecte en plus un score d'option devenu contradictoire avec une autre
question (une même valeur de réponse doit conserver le même score dans tout
le questionnaire, voir docs/BUSINESS_RULES.md).
"""

from ADM.schemas import Questions, parse_question_definition, parse_questions
from ADM.scoring import compute_scoring_map


def add_question(
    questions: Questions, category: str, key: str, raw_definition: object
) -> Questions:
    """Retourne un nouveau questionnaire avec la question ajoutée à ``category``."""
    if category not in questions:
        raise ValueError(f"La catégorie {category!r} est inconnue.")
    if key in questions[category]:
        raise ValueError(f"La question {key!r} existe déjà dans la catégorie {category!r}.")
    definition = parse_question_definition(key, raw_definition)
    updated = _copy_questions(questions)
    updated[category][key] = definition
    return _revalidated(updated)


def update_question(
    questions: Questions,
    category: str,
    key: str,
    new_category: str,
    raw_definition: object,
) -> Questions:
    """Retourne un nouveau questionnaire avec la question ``key`` mise à jour.

    ``new_category`` permet de déplacer la question vers une autre catégorie
    déjà existante. La clé technique, elle, reste immuable après création :
    elle identifie les réponses déjà enregistrées dans l'historique des
    évaluations (voir docs/BUSINESS_RULES.md) et n'est donc pas modifiable ici.
    """
    if category not in questions or key not in questions[category]:
        raise ValueError(f"La question {key!r} est introuvable dans la catégorie {category!r}.")
    if new_category not in questions:
        raise ValueError(f"La catégorie {new_category!r} est inconnue.")
    if new_category != category and key in questions[new_category]:
        raise ValueError(f"La question {key!r} existe déjà dans la catégorie {new_category!r}.")
    definition = parse_question_definition(key, raw_definition)
    updated = _copy_questions(questions)
    del updated[category][key]
    updated[new_category][key] = definition
    return _revalidated(updated)


def delete_question(questions: Questions, category: str, key: str) -> Questions:
    """Retourne un nouveau questionnaire sans la question ``key``.

    Les réponses déjà enregistrées pour cette question dans l'historique des
    évaluations existantes ne sont pas supprimées : elles cessent seulement
    d'être affichées et scorées (voir docs/BUSINESS_RULES.md).
    """
    if category not in questions or key not in questions[category]:
        raise ValueError(f"La question {key!r} est introuvable dans la catégorie {category!r}.")
    updated = _copy_questions(questions)
    del updated[category][key]
    return _revalidated(updated)


def _copy_questions(questions: Questions) -> Questions:
    """Copie superficielle à deux niveaux, suffisante puisque les définitions
    de question elles-mêmes ne sont jamais mutées en place, seulement
    remplacées."""
    return {category: dict(definitions) for category, definitions in questions.items()}


def _revalidated(questions: Questions) -> Questions:
    revalidated = parse_questions(questions)
    compute_scoring_map(revalidated)
    return revalidated
