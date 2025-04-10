# database.py

import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

# Utilisation du type JSON natif de SQLAlchemy si disponible, sinon on peut utiliser TEXT.
try:
    from sqlalchemy import JSON as SA_JSON
except ImportError:
    SA_JSON = Text

# Base de déclaration
Base = declarative_base()


class Application(Base):
    __tablename__ = 'applications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    rda = Column(String(255), nullable=False)
    possession = Column(Date)
    type_app = Column(String(50), nullable=False)  # Exemple: "Interne", "Editeur", "Open source"
    hosting = Column(String(50), nullable=False)   # Exemple: "On prem", "Cloud", "SaaS"
    criticite = Column(Integer, nullable=False)
    disponibilite = Column(String(2), nullable=False)  # Ex. "D1", "D2", "D3", "D4"
    integrite = Column(String(2), nullable=False)       # Ex. "I1", "I2", ...
    confidentialite = Column(String(2), nullable=False) # Ex. "C1", "C2", ...
    perennite = Column(String(2), nullable=False)         # Ex. "P1", "P2", ...
    score = Column(Integer, default=None)
    answered_questions = Column(Integer, default=None)
    last_evaluation = Column(DateTime, default=None)
    responses = Column(SA_JSON)
    comments = Column(SA_JSON)
    evaluator_name = Column(String(255)) 
    
    # Relation avec la table Evaluation
    evaluations = relationship("Evaluation", back_populates="application", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Application(name={self.name}, type_app={self.type_app}, hosting={self.hosting})>"

    def to_dict(self) -> dict:
        """Convertit l'objet Application en dictionnaire serialisable en JSON."""
        return {
            "id": self.id,
            "name": self.name,
            "rda": self.rda,
            "possession": self.possession.isoformat() if self.possession and hasattr(self.possession, "isoformat") else self.possession,
            "type_app": self.type_app,
            "hosting": self.hosting,
            "criticite": self.criticite,
            "disponibilite": self.disponibilite,
            "integrite": self.integrite,
            "confidentialite": self.confidentialite,
            "perennite": self.perennite,
            "score": self.score,
            "answered_questions": self.answered_questions,
            "last_evaluation": self.last_evaluation.isoformat() if self.last_evaluation and hasattr(self.last_evaluation, "isoformat") else self.last_evaluation,
            "responses": self.responses,
            "comments": self.comments,
            "evaluator_name": self.evaluator_name,
            "evaluations": [ev.to_dict() for ev in self.evaluations]
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Crée une instance de Application à partir d'un dictionnaire."""
        # Conversion de la date de possession
        possession = data.get("possession")
        if possession and isinstance(possession, str):
            try:
                possession = datetime.strptime(possession, "%Y-%m-%d").date()
            except Exception:
                possession = None

        # Conversion de last_evaluation
        last_eval = data.get("last_evaluation")
        if last_eval and isinstance(last_eval, str):
            try:
                last_eval = datetime.fromisoformat(last_eval)
            except Exception:
                last_eval = None

        # Importation de l'historique des évaluations
        evaluations_data = data.get("evaluations", [])
        evaluations = [Evaluation.from_dict(ev) for ev in evaluations_data]

        return cls(
            id=data.get("id"),
            name=data.get("name"),
            rda=data.get("rda"),
            possession=possession,
            type_app=data.get("type_app"),
            hosting=data.get("hosting"),
            criticite=data.get("criticite"),
            disponibilite=data.get("disponibilite"),
            integrite=data.get("integrite"),
            confidentialite=data.get("confidentialite"),
            perennite=data.get("perennite"),
            score=data.get("score"),
            answered_questions=data.get("answered_questions"),
            last_evaluation=last_eval,
            responses=data.get("responses", {}),
            comments=data.get("comments", {}),
            evaluator_name=data.get("evaluator_name"),
            evaluations=evaluations
        )

class Evaluation(Base):
    __tablename__ = 'evaluations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey('applications.id'), nullable=False)
    score = Column(Integer, nullable=False)
    answered_questions = Column(Integer, nullable=False)
    last_evaluation = Column(DateTime, nullable=False)
    evaluator_name = Column(String(255), nullable=False)
    responses = Column(SA_JSON)
    comments = Column(SA_JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relation vers l'application évaluée
    application = relationship("Application", back_populates="evaluations")
    
    def __repr__(self):
        return f"<Evaluation(app_id={self.application_id}, score={self.score}, evaluator={self.evaluator_name})>"

    def to_dict(self) -> dict:
        """Convertit l'objet Evaluation en dictionnaire serialisable en JSON."""
        return {
            "id": self.id,
            "application_id": self.application_id,
            "score": self.score,
            "answered_questions": self.answered_questions,
            "last_evaluation": self.last_evaluation.isoformat() if self.last_evaluation and hasattr(self.last_evaluation, "isoformat") else self.last_evaluation,
            "evaluator_name": self.evaluator_name,
            "responses": self.responses,
            "comments": self.comments,
            "created_at": self.created_at.isoformat() if self.created_at and hasattr(self.created_at, "isoformat") else self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Crée une instance d'Evaluation à partir d'un dictionnaire."""
        last_eval = data.get("last_evaluation")
        if last_eval and isinstance(last_eval, str):
            try:
                last_eval = datetime.fromisoformat(last_eval)
            except Exception:
                last_eval = None

        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except Exception:
                created_at = None

        return cls(
            id=data.get("id"),
            application_id=data.get("application_id"),
            score=data.get("score"),
            answered_questions=data.get("answered_questions", 0),
            last_evaluation=last_eval,
            evaluator_name=data.get("evaluator_name", ""),
            responses=data.get("responses", {}),
            comments=data.get("comments", {}),
            created_at=created_at
        )

def get_engine(connection_url):
    """
    Retourne un engine SQLAlchemy pour se connecter à la base MySQL,
    en s'assurant que les connexions expirées soient renouvelées via pool_pre_ping.
    """
    engine = create_engine(
        connection_url,
        echo=False,
        pool_recycle=3600,    # recycle la connexion après 3600 secondes
        pool_pre_ping=True    # vérifie la validité de la connexion avant son utilisation
    )
    return engine


def get_session_factory(engine):
    """
    Retourne une session factory (scoped_session) pour obtenir des sessions SQLAlchemy.
    """
    return scoped_session(sessionmaker(bind=engine))


def init_db(connection_url=None):
    """
    Initialise la base de données en créant toutes les tables définies dans Base.metadata
    si elles n'existent pas déjà.
    """
    engine = get_engine(connection_url)
    Base.metadata.create_all(engine)
    return engine


if __name__ == '__main__':
    # Exemple de test : création de la base et insertion d'une application de test.
    engine = init_db()  # Utilise la chaîne de connexion par défaut ou celle passée en paramètre
    Session = get_session_factory(engine)
    session = Session()
    
    # Création d'une application de test
    new_app = Application(
        name="Test Application",
        rda="Test RDA",
        possession=datetime.strptime("2021-01-01", "%Y-%m-%d").date(),
        type_app="Interne",
        hosting="On prem",
        criticite=1,
        disponibilite="D1",
        integrite="I1",
        confidentialite="C1",
        perennite="P1",
        score=0,
        answered_questions=0,
        last_evaluation=None,
        responses={},
        comments={}
    )
    session.add(new_app)
    session.commit()
    print("Nouvelle application ajoutée :", new_app)
    session.close()
