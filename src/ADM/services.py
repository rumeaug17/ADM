"""Services métier indépendants de Flask pour les indicateurs du catalogue."""

import base64
import io
import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, TypeAlias

import matplotlib.pyplot as plt
import numpy as np

JsonData: TypeAlias = dict[str, object]
Questions: TypeAlias = dict[str, dict[str, dict[str, object]]]
ScoreMap: TypeAlias = dict[str, int | None]


@dataclass(frozen=True)
class EvaluationSubmission:
    """Données calculées à partir d'un formulaire d'évaluation validé."""

    responses: dict[str, str]
    comments: dict[str, str]
    score: int
    answered_questions: int


@dataclass(frozen=True)
class CatalogueSummary:
    """Indicateurs nécessaires à la page de synthèse."""

    total_applications: int
    average_score: float
    applications_above_30: int
    applications_above_60: int
    global_risk: float | None


class EvaluationLike(Protocol):
    score: int
    answered_questions: int
    last_evaluation: datetime
    evaluator_name: str
    responses: dict[str, object]
    comments: dict[str, object]
    created_at: datetime


class ApplicationLike(Protocol):
    name: str
    rda: str
    possession: object
    type_app: str
    hosting: str
    criticite: int
    disponibilite: str
    integrite: str
    confidentialite: str
    perennite: str
    score: int | None
    answered_questions: int | None
    last_evaluation: datetime | None
    responses: dict[str, object]
    comments: dict[str, object]
    evaluator_name: str | None
    evaluations: list[EvaluationLike]


def application_to_dict(application: ApplicationLike) -> JsonData:
    """Convertit une application persistée en données de présentation."""

    def to_iso(value: object) -> str | None:
        return value.isoformat() if hasattr(value, "isoformat") else None

    return {
        "name": application.name,
        "rda": application.rda,
        "possession": to_iso(application.possession),
        "type_app": application.type_app,
        "hosting": application.hosting,
        "criticite": str(application.criticite),
        "disponibilite": application.disponibilite,
        "integrite": application.integrite,
        "confidentialite": application.confidentialite,
        "perennite": application.perennite,
        "score": application.score,
        "answered_questions": application.answered_questions,
        "last_evaluation": to_iso(application.last_evaluation),
        "responses": application.responses,
        "comments": application.comments,
        "evaluator_name": application.evaluator_name,
        "evaluations": [
            {
                "score": item.score,
                "answered_questions": item.answered_questions,
                "last_evaluation": to_iso(item.last_evaluation),
                "evaluator_name": item.evaluator_name,
                "responses": item.responses,
                "comments": item.comments,
                "created_at": to_iso(item.created_at),
            }
            for item in application.evaluations
        ],
    }


def calculate_risk(application: JsonData) -> float | None:
    """Calcule le risque à partir du score, des indicateurs DICP et de la criticité."""
    try:
        score = float(application["score"])
        factors = [
            int("".join(filter(str.isdigit, str(application.get(key, "0")))))
            for key in ("disponibilite", "integrite", "confidentialite", "perennite")
        ]
        criticity = int(str(application.get("criticite", "0")))
    except (KeyError, TypeError, ValueError):
        return None
    if criticity == 0:
        return None
    return score * ((float(np.prod(factors)) / 4 / criticity) / 2)


def update_app_metrics(application: JsonData) -> None:
    """Ajoute les métriques dérivées à une application."""
    score = application.get("score")
    answered = application.get("answered_questions", 0)
    if isinstance(score, (int, float)) and isinstance(answered, int) and answered > 0:
        maximum = answered * 3
        application.update(max_score=maximum, percentage=round(score / maximum * 100, 2))
        application["risque"] = calculate_risk(application)
    else:
        application.update(max_score=None, percentage=None, risque=None)


def question_definition(key: str, questions: Questions) -> dict[str, object]:
    return next((group[key] for group in questions.values() if key in group), {})


def build_evaluation_submission(
    form: Mapping[str, str], questions: Questions, scoring: ScoreMap
) -> EvaluationSubmission:
    """Transforme un formulaire déjà validé en résultat métier pondéré."""
    responses: dict[str, str] = {}
    comments: dict[str, str] = {}
    score = 0
    answered_questions = 0
    for key, value in form.items():
        if key.endswith("_comment"):
            comments[key] = value
            continue
        option_score = scoring.get(value)
        if value not in scoring:
            continue
        responses[key] = value
        if option_score is not None:
            weight = int(question_definition(key, questions).get("weight", 1))
            score += option_score * weight
            answered_questions += weight
    return EvaluationSubmission(responses, comments, score, answered_questions)


def summarize_catalogue(applications: list[JsonData]) -> CatalogueSummary:
    """Calcule les indicateurs globaux sans dépendre de Flask."""
    scores = [
        value
        for app in applications
        if isinstance(value := app.get("score"), int) and not isinstance(value, bool)
    ]
    percentages = [
        value for app in applications if isinstance(value := app.get("percentage"), (int, float))
    ]
    risks = [value for app in applications if isinstance(value := app.get("risque"), (int, float))]
    return CatalogueSummary(
        total_applications=len(applications),
        average_score=round(sum(scores) / len(scores), 2) if scores else 0,
        applications_above_30=sum(value > 30 for value in percentages),
        applications_above_60=sum(value > 60 for value in percentages),
        global_risk=round(sum(risks) / len(risks), 2) if risks else None,
    )


def category_sums(
    application: JsonData,
    questions: Questions,
    categories: dict[str, list[str]],
    scoring: dict[str, int | None],
) -> dict[str, int]:
    responses = application.get("responses", {})
    if not isinstance(responses, dict):
        return {category: 0 for category in categories}
    return {
        category: sum(
            (scoring.get(str(responses.get(key, "Non applicable"))) or 0)
            * int(question_definition(key, questions).get("weight", 1))
            for key in keys
        )
        for category, keys in categories.items()
    }


def axis_scores(
    data: list[JsonData],
    questions: Questions,
    categories: dict[str, list[str]],
    scoring: dict[str, int | None],
) -> dict[str, float]:
    values: dict[str, list[float]] = {key: [] for key in categories}
    for application in data:
        responses = application.get("responses", {})
        if not isinstance(responses, dict):
            continue
        for category, keys in categories.items():
            scores = [
                (scoring.get(str(responses[key])) or 0)
                * int(question_definition(key, questions).get("weight", 1))
                for key in keys
                if key in responses and scoring.get(str(responses[key])) is not None
            ]
            if scores:
                values[category].append(sum(scores) / len(scores))
    return {key: round(sum(items) / len(items), 2) if items else 0 for key, items in values.items()}


def generate_radar_chart(scores_by_axis: dict[str, float]) -> str:
    """Produit un graphique radar PNG encodé en base64."""
    categories, scores = list(scores_by_axis), list(scores_by_axis.values())
    maximum = max(1, math.ceil(max(scores))) if scores else 3
    scores += scores[:1]
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]
    figure, axis = plt.subplots(figsize=(6, 6), subplot_kw={"projection": "polar"})
    axis.set_theta_offset(np.pi / 2)
    axis.set_theta_direction(-1)
    axis.set_xticks(angles[:-1])
    axis.set_xticklabels(categories)
    axis.set_ylim(-1, maximum)
    axis.plot(angles, scores, color="blue", linewidth=2)
    axis.fill(angles, scores, color="blue", alpha=0.25)
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(figure)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def update_all_metrics(applications: list[JsonData]) -> None:
    """Met à jour les métriques de toutes les applications."""
    for application in applications:
        update_app_metrics(application)
