"""Persistance locale des comptes dans un fichier JSON dédié (US6.1).

Volontairement isolé de ADM.database_json : les comptes ne doivent jamais
transiter par le circuit d'import/export du catalogue (ADM.catalogue_io).
"""

import json
from collections.abc import Callable, Iterable
from copy import deepcopy
from pathlib import Path

from ADM.database import Account, JsonObject

AccountSessionFactory = Callable[[], "AccountJsonSession"]


class AccountQuery:
    """Sous-ensemble réduit de l'API de requête SQLAlchemy, dédié aux comptes."""

    def __init__(self, objects: Iterable[Account]) -> None:
        self._objects: list[Account] = list(objects)

    def all(self) -> list[Account]:
        return list(self._objects)

    def filter_by(self, **criteria: object) -> "AccountQuery":
        return AccountQuery(
            item
            for item in self._objects
            if all(getattr(item, name, None) == value for name, value in criteria.items())
        )

    def first(self) -> Account | None:
        return self._objects[0] if self._objects else None


class AccountJsonSession:
    """Unité de travail enregistrant atomiquement les comptes en JSON."""

    def __init__(self, filename: str | Path) -> None:
        self._path = Path(filename)
        records = _load_records(self._path)
        accounts = [Account.from_dict(record) for record in records]
        self._accounts = _index_accounts(accounts)
        self._snapshot = deepcopy(self._accounts)
        self._next_id = max(self._accounts, default=0) + 1

    def query(self, model: type[Account]) -> AccountQuery:
        if model is Account:
            return AccountQuery(self._accounts.values())
        return AccountQuery([])

    def add(self, item: Account) -> None:
        if not isinstance(item, Account):
            raise ValueError("Seuls les comptes peuvent être ajoutés à cette session.")
        if item.id is None:
            item.id = self._next_id
            self._next_id += 1
        self._accounts[item.id] = item

    def delete(self, item: Account) -> None:
        if not isinstance(item, Account):
            raise ValueError("Seuls les comptes peuvent être supprimés de cette session.")
        if item.id is not None:
            self._accounts.pop(item.id, None)

    def commit(self) -> None:
        records = [item.to_dict() for item in self._accounts.values()]
        _save_records(self._path, records)
        self._snapshot = deepcopy(self._accounts)

    def rollback(self) -> None:
        self._accounts = deepcopy(self._snapshot)

    def close(self) -> None:
        """Ferme la session (aucune ressource persistante n'est détenue)."""


def get_account_engine(connection_url: str) -> Path:
    """Valide et retourne le chemin utilisé comme moteur de comptes JSON."""
    if not connection_url.strip():
        raise ValueError("Le chemin du fichier de comptes ne peut pas être vide.")
    return Path(connection_url)


def get_account_session_factory(engine: Path) -> AccountSessionFactory:
    """Retourne une fabrique de sessions utilisant le chemin fourni."""
    return lambda: AccountJsonSession(engine)


def init_account_db(connection_url: str) -> Path:
    """Initialise un fichier de comptes vide s'il n'existe pas."""
    path = get_account_engine(connection_url)
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
        raise ValueError(f"Impossible de lire la base de comptes {path}.") from error
    if not isinstance(content, list) or not all(isinstance(item, dict) for item in content):
        raise ValueError("La base de comptes doit contenir une liste d'objets.")
    return content


def _save_records(path: Path, records: list[JsonObject]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    try:
        temporary_path.write_text(
            json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        temporary_path.replace(path)
    except OSError as error:
        temporary_path.unlink(missing_ok=True)
        raise ValueError(f"Impossible d'enregistrer la base de comptes {path}.") from error


def _index_accounts(accounts: list[Account]) -> dict[int, Account]:
    identifiers = [account.id for account in accounts if account.id is not None]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("La base de comptes contient des identifiants dupliqués.")
    next_identifier = max(identifiers, default=0) + 1
    indexed: dict[int, Account] = {}
    for account in accounts:
        if account.id is None:
            account.id = next_identifier
            next_identifier += 1
        indexed[account.id] = account
    return indexed
