"""Tests des backends de persistance du catalogue."""

import json
from datetime import date, datetime

import pytest

from ADM.database import Application, Evaluation
from ADM.database_json import JsonSession, init_db


def application_record(name: str = "Catalogue de test") -> dict[str, object]:
    """Retourne un enregistrement valide sans donnée réelle."""
    return {
        "name": name,
        "rda": "Responsable fictif",
        "possession": "2025-01-15",
        "type_app": "Interne",
        "hosting": "Cloud",
        "criticite": 2,
        "disponibilite": "D2",
        "integrite": "I2",
        "confidentialite": "C2",
        "perennite": "P2",
        "responses": {},
        "comments": {},
        "evaluations": [],
    }


def test_application_round_trip_validates_and_serializes_dates() -> None:
    application = Application.from_dict(application_record())

    assert application.possession == date(2025, 1, 15)
    assert application.to_dict()["possession"] == "2025-01-15"


def test_evaluation_rejects_an_invalid_datetime() -> None:
    record: dict[str, object] = {
        "score": 3,
        "answered_questions": 1,
        "last_evaluation": "date incorrecte",
        "evaluator_name": "Évaluateur fictif",
    }

    with pytest.raises(ValueError, match="last_evaluation"):
        Evaluation.from_dict(record)


def test_json_session_persists_and_rolls_back(tmp_path) -> None:
    database_path = tmp_path / "catalogue.json"
    engine = init_db(str(database_path))
    session = JsonSession(engine)
    application = Application.from_dict(application_record())
    session.add(application)
    session.commit()

    application.name = "Modification non validée"
    session.rollback()
    restored = session.query(Application).first()

    assert restored is not None
    assert restored.name == "Catalogue de test"
    assert JsonSession(engine).query(Application).first().name == "Catalogue de test"


def test_json_session_preserves_evaluation_history(tmp_path) -> None:
    database_path = tmp_path / "catalogue.json"
    application = Application.from_dict(application_record())
    application.evaluations.append(
        Evaluation(
            score=4,
            answered_questions=2,
            last_evaluation=datetime(2025, 2, 1, 10, 30),
            evaluator_name="Évaluateur fictif",
            responses={"question": "réponse"},
            comments={},
        )
    )
    session = JsonSession(init_db(str(database_path)))
    session.add(application)
    session.commit()

    restored = JsonSession(database_path).query(Application).first()

    assert restored is not None
    assert restored.evaluations[0].score == 4


def test_json_backend_rejects_a_catalogue_that_is_not_a_list(tmp_path) -> None:
    database_path = tmp_path / "catalogue.json"
    database_path.write_text(json.dumps({"application": application_record()}), encoding="utf-8")

    with pytest.raises(ValueError, match="liste d'objets"):
        init_db(str(database_path))


def test_json_session_saves_deletions_and_unicode(tmp_path) -> None:
    database_path = tmp_path / "catalogue.json"
    engine = init_db(str(database_path))
    first_application = Application.from_dict(application_record("Application supprimée"))
    kept_application = Application.from_dict(application_record("Étude conservée"))
    session = JsonSession(engine)
    session.add(first_application)
    session.add(kept_application)
    session.commit()

    session.delete(first_application)
    session.commit()

    persisted_content = database_path.read_text(encoding="utf-8")
    restored = JsonSession(engine).query(Application).all()
    assert "Étude conservée" in persisted_content
    assert [application.name for application in restored] == ["Étude conservée"]
