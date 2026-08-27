"""Contrat de persistance commun aux backends JSON et SQL.

Ce module exécute la même suite de tests sur les deux implémentations de
``ADM.persistence.TransactionSession`` / ``ADM.catalogue_io.CatalogueSession``
afin d'éviter que leurs comportements divergent silencieusement (Phase 6 du
backlog). Chaque test paramétré instancie sa session avec les mêmes fonctions
``init_db`` / ``get_session_factory`` que ``ADM.app.create_app``, pour exercer
exactement le code de production plutôt qu'une reconstruction ad hoc.

Le backend SQL de production est MySQL, mais les tests utilisent SQLite : cela
respecte la règle du projet selon laquelle un test ne doit dépendre ni du réseau
ni d'un service partagé (voir ``CONTRIBUTING.md``), tout en exerçant exactement
le même code (``ADM.database``, ses modèles et ``get_engine``/``init_db``) que
MySQL en production — seul le dialecte SQL change. La compatibilité du dialecte
MySQL lui-même n'est donc pas couverte ici et resterait à vérifier séparément
(par exemple via un service dédié en CI) si elle devient un point de rupture.
"""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import pytest

from ADM import database, database_json
from ADM.database import Application, Evaluation

SessionFactory = Callable[[], object]


def _sql_session_factory(tmp_path: Path) -> SessionFactory:
    # `as_posix()` garantit des séparateurs `/` valides dans l'URL SQLAlchemy,
    # y compris lorsque les tests s'exécutent sous Windows.
    connection_url = f"sqlite:///{(tmp_path / 'catalogue.db').as_posix()}"
    engine = database.init_db(connection_url)
    return database.get_session_factory(engine)


def _json_session_factory(tmp_path: Path) -> SessionFactory:
    connection_url = str(tmp_path / "catalogue.json")
    engine = database_json.init_db(connection_url)
    return database_json.get_session_factory(engine)


BACKENDS: dict[str, Callable[[Path], SessionFactory]] = {
    "json": _json_session_factory,
    "sql": _sql_session_factory,
}


@pytest.fixture(params=sorted(BACKENDS))
def session_factory(request: pytest.FixtureRequest, tmp_path: Path) -> SessionFactory:
    """Fournit une fabrique de sessions fraîche pour chaque backend testé."""
    return BACKENDS[request.param](tmp_path)


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


def test_add_commit_and_query_round_trips_the_application(session_factory: SessionFactory) -> None:
    session = session_factory()
    session.add(Application.from_dict(application_record()))
    session.commit()
    session.close()

    stored = session_factory().query(Application).all()

    assert [application.name for application in stored] == ["Catalogue de test"]


def test_rollback_discards_uncommitted_changes(session_factory: SessionFactory) -> None:
    session = session_factory()
    application = Application.from_dict(application_record())
    session.add(application)
    session.commit()

    application.name = "Modification non validée"
    session.rollback()
    session.close()

    restored = session_factory().query(Application).first()

    assert restored is not None
    assert restored.name == "Catalogue de test"


def test_delete_removes_the_application(session_factory: SessionFactory) -> None:
    session = session_factory()
    application = Application.from_dict(application_record())
    session.add(application)
    session.commit()

    session.delete(application)
    session.commit()
    session.close()

    assert session_factory().query(Application).all() == []


def test_filter_by_name_finds_only_the_matching_application(
    session_factory: SessionFactory,
) -> None:
    session = session_factory()
    session.add(Application.from_dict(application_record("Cible")))
    session.add(Application.from_dict(application_record("Autre application")))
    session.commit()
    session.close()

    found = session_factory().query(Application).filter_by(name="Cible").first()

    assert found is not None
    assert found.name == "Cible"


def test_evaluation_history_is_preserved_with_the_application(
    session_factory: SessionFactory,
) -> None:
    session = session_factory()
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
    session.add(application)
    session.commit()
    session.close()

    restored = session_factory().query(Application).first()

    assert restored is not None
    assert len(restored.evaluations) == 1
    assert restored.evaluations[0].score == 4


def test_querying_an_empty_catalogue_returns_no_application(
    session_factory: SessionFactory,
) -> None:
    assert session_factory().query(Application).all() == []
