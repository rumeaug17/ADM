"""Gestion transactionnelle commune aux backends de persistance."""

from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Protocol, TypeVar

from ADM.database import Application


class ApplicationQuery(Protocol):
    """Résultat minimal d'une requête portant sur les applications."""

    def all(self) -> list[Application]: ...

    def filter_by(self, **criteria: object) -> "ApplicationQuery": ...

    def first(self) -> Application | None: ...


class TransactionSession(Protocol):
    """Opérations nécessaires à la gestion d'une unité de travail."""

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def close(self) -> None: ...

    def query(self, model: type[Application]) -> ApplicationQuery: ...

    def add(self, item: Application) -> None: ...

    def delete(self, item: Application) -> None: ...


SessionType = TypeVar("SessionType", bound=TransactionSession)


@contextmanager
def transactional_session(factory: Callable[[], SessionType]) -> Generator[SessionType, None, None]:
    """Valide une unité de travail, ou l'annule intégralement en cas d'erreur.

    La fermeture est garantie, y compris si le commit échoue. L'exception d'origine
    est conservée afin que la couche d'orchestration puisse choisir le message adapté.
    """
    session = factory()
    try:
        yield session
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()
