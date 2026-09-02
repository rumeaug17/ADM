"""Backend SQLAlchemy du catalogue ADM."""

from collections.abc import Callable, Mapping
from datetime import date, datetime
from typing import TypeAlias

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

JsonObject: TypeAlias = dict[str, object]
SessionFactory: TypeAlias = Callable[[], Session]


# SQLAlchemy est volontairement ignoré par ``follow_imports`` dans la configuration
# mypy du projet ; son type de base est donc vu comme ``Any`` pendant ce contrôle.
class Base(DeclarativeBase):  # type: ignore[misc]
    """Base déclarative des modèles SQLAlchemy."""


class Application(Base):
    """Application persistée dans la base relationnelle."""

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    rda: Mapped[str] = mapped_column(String(255))
    possession: Mapped[date | None] = mapped_column(Date)
    type_app: Mapped[str] = mapped_column(String(50))
    hosting: Mapped[str] = mapped_column(String(50))
    criticite: Mapped[int] = mapped_column(Integer)
    disponibilite: Mapped[str] = mapped_column(String(2))
    integrite: Mapped[str] = mapped_column(String(2))
    confidentialite: Mapped[str] = mapped_column(String(2))
    perennite: Mapped[str] = mapped_column(String(2))
    score: Mapped[int | None] = mapped_column(Integer, default=None)
    answered_questions: Mapped[int | None] = mapped_column(Integer, default=None)
    last_evaluation: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    responses: Mapped[JsonObject] = mapped_column(JSON, default=dict)
    comments: Mapped[JsonObject] = mapped_column(JSON, default=dict)
    evaluator_name: Mapped[str | None] = mapped_column(String(255))
    evaluations: Mapped[list["Evaluation"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Application(name={self.name}, type_app={self.type_app}, hosting={self.hosting})>"

    def to_dict(self) -> JsonObject:
        """Convertit l'application en structure sérialisable en JSON."""
        return {
            "id": self.id,
            "name": self.name,
            "rda": self.rda,
            "possession": self.possession.isoformat() if self.possession else None,
            "type_app": self.type_app,
            "hosting": self.hosting,
            "criticite": self.criticite,
            "disponibilite": self.disponibilite,
            "integrite": self.integrite,
            "confidentialite": self.confidentialite,
            "perennite": self.perennite,
            "score": self.score,
            "answered_questions": self.answered_questions,
            "last_evaluation": self.last_evaluation.isoformat() if self.last_evaluation else None,
            "responses": self.responses,
            "comments": self.comments,
            "evaluator_name": self.evaluator_name,
            "evaluations": [evaluation.to_dict() for evaluation in self.evaluations],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "Application":
        """Construit une application après validation des données importées."""
        evaluations = _mapping_list(data.get("evaluations"), "evaluations")
        return cls(
            id=_optional_int(data.get("id"), "id"),
            name=_required_string(data.get("name"), "name"),
            rda=_required_string(data.get("rda"), "rda"),
            possession=_optional_date(data.get("possession"), "possession"),
            type_app=_required_string(data.get("type_app"), "type_app"),
            hosting=_required_string(data.get("hosting"), "hosting"),
            criticite=_required_int(data.get("criticite"), "criticite"),
            disponibilite=_required_string(data.get("disponibilite"), "disponibilite"),
            integrite=_required_string(data.get("integrite"), "integrite"),
            confidentialite=_required_string(data.get("confidentialite"), "confidentialite"),
            perennite=_required_string(data.get("perennite"), "perennite"),
            score=_optional_int(data.get("score"), "score"),
            answered_questions=_optional_int(data.get("answered_questions"), "answered_questions"),
            last_evaluation=_optional_datetime(data.get("last_evaluation"), "last_evaluation"),
            responses=_json_object(data.get("responses"), "responses"),
            comments=_json_object(data.get("comments"), "comments"),
            evaluator_name=_optional_string(data.get("evaluator_name"), "evaluator_name"),
            evaluations=[Evaluation.from_dict(item) for item in evaluations],
        )


class Evaluation(Base):
    """Historique d'une évaluation d'application."""

    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"))
    score: Mapped[int] = mapped_column(Integer)
    answered_questions: Mapped[int] = mapped_column(Integer)
    last_evaluation: Mapped[datetime] = mapped_column(DateTime)
    evaluator_name: Mapped[str] = mapped_column(String(255))
    responses: Mapped[JsonObject] = mapped_column(JSON, default=dict)
    comments: Mapped[JsonObject] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    application: Mapped[Application] = relationship(back_populates="evaluations")

    def to_dict(self) -> JsonObject:
        """Convertit l'évaluation en structure sérialisable en JSON."""
        return {
            "id": self.id,
            "application_id": self.application_id,
            "score": self.score,
            "answered_questions": self.answered_questions,
            "last_evaluation": self.last_evaluation.isoformat(),
            "evaluator_name": self.evaluator_name,
            "responses": self.responses,
            "comments": self.comments,
            "created_at": (self.created_at or datetime.now()).isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "Evaluation":
        """Construit une évaluation après validation des données importées."""
        return cls(
            id=_optional_int(data.get("id"), "id"),
            application_id=_optional_int(data.get("application_id"), "application_id"),
            score=_required_int(data.get("score"), "score"),
            answered_questions=_required_int(data.get("answered_questions"), "answered_questions"),
            last_evaluation=_required_datetime(data.get("last_evaluation"), "last_evaluation"),
            evaluator_name=_required_string(data.get("evaluator_name"), "evaluator_name"),
            responses=_json_object(data.get("responses"), "responses"),
            comments=_json_object(data.get("comments"), "comments"),
            created_at=_optional_datetime(data.get("created_at"), "created_at") or datetime.now(),
        )


class Account(Base):
    """Compte utilisateur pour l'authentification locale (US6.1)."""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    auth_generation: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __repr__(self) -> str:
        return f"<Account(username={self.username}, role={self.role}, active={self.active})>"

    def to_dict(self) -> JsonObject:
        """Convertit le compte en structure sérialisable en JSON.

        Le hash du mot de passe est inclus : c'est la forme de stockage du
        backend JSON lui-même (fichier accounts.json, séparé du catalogue).
        Il ne doit jamais transiter par ADM.catalogue_io.
        """
        return {
            "id": self.id,
            "username": self.username,
            "password_hash": self.password_hash,
            "role": self.role,
            "active": self.active,
            "auth_generation": self.auth_generation,
            "created_at": (self.created_at or datetime.now()).isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "Account":
        """Construit un compte après validation des données persistées.

        Le rôle est restreint à un ensemble fermé dès cette étape, contrairement
        aux champs équivalents d'Application : une valeur inattendue ici a un
        impact direct sur les habilitations, pas seulement sur l'affichage.
        """
        return cls(
            id=_optional_int(data.get("id"), "id"),
            username=_required_string(data.get("username"), "username"),
            password_hash=_required_string(data.get("password_hash"), "password_hash"),
            role=_required_role(data.get("role"), "role"),
            active=_required_bool(data.get("active"), "active"),
            auth_generation=_optional_int(data.get("auth_generation"), "auth_generation") or 0,
            created_at=_optional_datetime(data.get("created_at"), "created_at") or datetime.now(),
        )


def get_engine(connection_url: str) -> Engine:
    """Crée un moteur SQLAlchemy vérifiant les connexions avant usage."""
    if not connection_url.strip():
        raise ValueError("L'URL de connexion ne peut pas être vide.")
    return create_engine(connection_url, pool_recycle=3600, pool_pre_ping=True)


def get_session_factory(engine: Engine) -> SessionFactory:
    """Retourne une fabrique de sessions indépendantes."""
    # Les types de SQLAlchemy ne sont pas suivis par mypy dans ce projet.
    return sessionmaker(bind=engine)  # type: ignore[no-any-return]


def init_db(connection_url: str) -> Engine:
    """Crée les tables absentes et retourne le moteur associé."""
    engine = get_engine(connection_url)
    Base.metadata.create_all(engine)
    return engine


def _required_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Le champ {field!r} doit être une chaîne non vide.")
    return value


def _required_role(value: object, field: str) -> str:
    role = _required_string(value, field)
    if role not in {"admin", "user"}:
        raise ValueError(f"Le champ {field!r} doit valoir 'admin' ou 'user'.")
    return role


def _required_bool(value: object, field: str, *, default: bool = True) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError(f"Le champ {field!r} doit être un booléen.")
    return value


def _optional_string(value: object, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Le champ {field!r} doit être une chaîne ou null.")
    return value


def _required_int(value: object, field: str) -> int:
    parsed = _optional_int(value, field)
    if parsed is None:
        raise ValueError(f"Le champ {field!r} est obligatoire.")
    return parsed


def _optional_int(value: object, field: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"Le champ {field!r} doit être un entier ou null.")
    return value


def _optional_date(value: object, field: str) -> date | None:
    if value is None or isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as error:
            raise ValueError(f"Le champ {field!r} doit être une date ISO valide.") from error
    raise ValueError(f"Le champ {field!r} doit être une date ISO ou null.")


def _required_datetime(value: object, field: str) -> datetime:
    parsed = _optional_datetime(value, field)
    if parsed is None:
        raise ValueError(f"Le champ {field!r} est obligatoire.")
    return parsed


def _optional_datetime(value: object, field: str) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError as error:
            raise ValueError(f"Le champ {field!r} doit être une date-heure ISO valide.") from error
    raise ValueError(f"Le champ {field!r} doit être une date-heure ISO ou null.")


def _json_object(value: object, field: str) -> JsonObject:
    if value is None:
        return {}
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"Le champ {field!r} doit être un objet JSON.")
    return dict(value)


def _mapping_list(value: object, field: str) -> list[Mapping[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, Mapping) for item in value):
        raise ValueError(f"Le champ {field!r} doit être une liste d'objets.")
    return value
