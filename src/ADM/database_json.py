"""Persistance locale du catalogue dans un fichier JSON."""

import json
from collections.abc import Callable, Iterable
from copy import deepcopy
from pathlib import Path
from typing import Generic, TypeVar

from .database import Application, Evaluation, JsonObject

Model = TypeVar("Model", Application, Evaluation)
JsonSessionFactory = Callable[[], "JsonSession"]


class JsonQuery(Generic[Model]):
    """Sous-ensemble volontairement réduit de l'API de requête SQLAlchemy."""

    def __init__(self, objects: Iterable[Model]) -> None:
        self._objects: list[Model] = list(objects)

    def all(self) -> list[Model]:
        return list(self._objects)

    def filter_by(self, **criteria: object) -> "JsonQuery[Model]":
        return JsonQuery(
            item
            for item in self._objects
            if all(getattr(item, name, None) == value for name, value in criteria.items())
        )

    def first(self) -> Model | None:
        return self._objects[0] if self._objects else None


class JsonSession:
    """Unité de travail enregistrant atomiquement les applications en JSON."""

    def __init__(self, filename: str | Path) -> None:
        self._path = Path(filename)
        records = _load_records(self._path)
        applications = [Application.from_dict(record) for record in records]
        self._applications = _index_applications(applications)
        self._snapshot = deepcopy(self._applications)
        self._next_id = max(self._applications, default=0) + 1

    def query(self, model: type[Model]) -> JsonQuery[Model]:
        if model is Application:
            return JsonQuery(self._applications.values())
        return JsonQuery([])

    def add(self, item: Application) -> None:
        if not isinstance(item, Application):
            raise ValueError("Seules les applications peuvent être ajoutées à la session JSON.")
        if item.id is None:
            item.id = self._next_id
            self._next_id += 1
        self._applications[item.id] = item

    def add_all(self, items: Iterable[Application]) -> None:
        for item in items:
            self.add(item)

    def delete(self, item: Application) -> None:
        if not isinstance(item, Application):
            raise ValueError("Seules les applications peuvent être supprimées de la session JSON.")
        if item.id is not None:
            self._applications.pop(item.id, None)

    def commit(self) -> None:
        records = [item.to_dict() for item in self._applications.values()]
        _save_records(self._path, records)
        self._snapshot = deepcopy(self._applications)

    def rollback(self) -> None:
        self._applications = deepcopy(self._snapshot)

    def close(self) -> None:
        """Ferme la session (aucune ressource persistante n'est détenue)."""


def get_engine(connection_url: str) -> Path:
    """Valide et retourne le chemin utilisé comme moteur JSON."""
    if not connection_url.strip():
        raise ValueError("Le chemin du fichier JSON ne peut pas être vide.")
    return Path(connection_url)


def get_session_factory(engine: Path) -> JsonSessionFactory:
    """Retourne une fabrique de sessions utilisant le chemin fourni."""
    return lambda: JsonSession(engine)


def init_db(connection_url: str) -> Path:
    """Initialise un fichier vide s'il n'existe pas, sans écraser les données."""
    path = get_engine(connection_url)
    if not path.exists():
        _save_records(path, [])
    else:
        _load_records(path)
    return path


def _load_records(path: Path) -> list[JsonObject]:
    if not path.exists():
        return []
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Impossible de lire la base JSON {path}.") from error
    if not isinstance(content, list) or not all(isinstance(item, dict) for item in content):
        raise ValueError("La base JSON doit contenir une liste d'objets.")
    return content


def _save_records(path: Path, records: list[JsonObject]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    try:
        temporary_path.write_text(
            json.dumps(records, indent=4, ensure_ascii=False), encoding="utf-8"
        )
        temporary_path.replace(path)
    except OSError as error:
        temporary_path.unlink(missing_ok=True)
        raise ValueError(f"Impossible d'enregistrer la base JSON {path}.") from error


def _index_applications(applications: list[Application]) -> dict[int, Application]:
    identifiers = [application.id for application in applications if application.id is not None]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("La base JSON contient des identifiants d'application dupliqués.")

    next_identifier = max(identifiers, default=0) + 1
    indexed_applications: dict[int, Application] = {}
    for application in applications:
        if application.id is None:
            application.id = next_identifier
            next_identifier += 1
        indexed_applications[application.id] = application
    return indexed_applications
