"""Compatibilité : importer le backend SQL depuis :mod:`ADM.database`."""

from ADM.database import Application, Base, Evaluation, get_engine, get_session_factory, init_db

__all__ = [
    "Application",
    "Base",
    "Evaluation",
    "get_engine",
    "get_session_factory",
    "init_db",
]
