"""Tests de la gestion des transactions et des échanges de catalogue."""

import io
import json

import pytest

from ADM.catalogue_io import replace_catalogue, serialize_catalogue
from ADM.database import Application
from ADM.database_json import JsonSession, init_db
from ADM.persistence import transactional_session
from ADM.validation import validate_import


class RecordingSession:
    """Double de test enregistrant le cycle de vie d'une transaction."""

    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0
        self.closes = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def close(self) -> None:
        self.closes += 1


def application_record(name: str) -> dict[str, object]:
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


def test_transactional_session_commits_and_closes() -> None:
    session = RecordingSession()

    with transactional_session(lambda: session):
        pass

    assert (session.commits, session.rollbacks, session.closes) == (1, 0, 1)


def test_transactional_session_rolls_back_and_preserves_error() -> None:
    session = RecordingSession()

    with pytest.raises(ValueError, match="échec attendu"):
        with transactional_session(lambda: session):
            raise ValueError("échec attendu")

    assert (session.commits, session.rollbacks, session.closes) == (0, 1, 1)


def test_import_replaces_catalogue_in_one_transaction(tmp_path) -> None:
    database_path = tmp_path / "catalogue.json"
    engine = init_db(str(database_path))
    initial = Application.from_dict(application_record("Ancienne application"))
    with transactional_session(lambda: JsonSession(engine)) as session:
        session.add(initial)

    imported = validate_import(
        io.BytesIO(json.dumps([application_record("Nouvelle application")]).encode())
    )

    def factory() -> JsonSession:
        return JsonSession(engine)

    with transactional_session(factory) as session:
        replace_catalogue(session, imported)

    stored = JsonSession(engine).query(Application).all()
    assert [application.name for application in stored] == ["Nouvelle application"]


def test_export_can_be_validated_and_imported_again() -> None:
    application = Application.from_dict(application_record("Application exportée"))

    exported = serialize_catalogue([application])
    restored = validate_import(io.BytesIO(exported.encode()))

    assert len(restored) == 1
    assert restored[0].to_dict() == application.to_dict()
