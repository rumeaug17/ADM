"""Compatibilité : importer le backend JSON depuis :mod:`ADM.database_json`."""

from ADM.database_json import (
    Application,
    Evaluation,
    JsonQuery,
    JsonSession,
    get_engine,
    get_session_factory,
    init_db,
)

__all__ = [
    "Application",
    "Evaluation",
    "JsonQuery",
    "JsonSession",
    "get_engine",
    "get_session_factory",
    "init_db",
]
