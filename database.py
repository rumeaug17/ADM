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
    
    # Relation avec la table Evaluation
    evaluations = relationship("Evaluation", back_populates="application", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Application(name={self.name}, type_app={self.type_app}, hosting={self.hosting})>"


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
