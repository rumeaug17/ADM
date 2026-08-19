"""Opérations métier d'import et d'export du catalogue."""

import json
from typing import Protocol

from ADM.database import Application


class ApplicationQuery(Protocol):
    """Requête minimale nécessaire au remplacement d'un catalogue."""

    def all(self) -> list[Application]: ...


class CatalogueSession(Protocol):
    """Session minimale partagée par les backends SQL et JSON."""

    def query(self, model: type[Application]) -> ApplicationQuery: ...

    def add(self, item: Application) -> None: ...

    def delete(self, item: Application) -> None: ...


def replace_catalogue(session: CatalogueSession, applications: list[Application]) -> None:
    """Remplace le catalogue dans l'unité de travail courante, sans la valider."""
    for existing_application in session.query(Application).all():
        session.delete(existing_application)
    for application in applications:
        session.add(application)


def serialize_catalogue(applications: list[Application]) -> str:
    """Sérialise un catalogue et son historique dans le format d'échange JSON."""
    return json.dumps(
        [application.to_dict() for application in applications],
        indent=4,
        ensure_ascii=False,
    )
