"""
Module database.py alternatif utilisant un fichier JSON comme backend
pour persister les données (applications et évaluations) sans modifier
le reste de l'application Flask.
"""

import os
import json
from datetime import datetime

# Définition du nom du fichier JSON pour la "base de données"
DB_FILENAME = "applications.json"


### CLASSES MODELES

class Application:
    def __init__(self, id=None, name="", rda="", possession=None, type_app="",
                 hosting="", criticite=None, disponibilite="", integrite="",
                 confidentialite="", perennite="", score=None, answered_questions=0,
                 last_evaluation=None, responses=None, comments=None, evaluations=None):
        self.id = id
        self.name = name
        self.rda = rda
        self.possession = possession  # objet date ou chaîne "YYYY-MM-DD"
        self.type_app = type_app
        self.hosting = hosting
        self.criticite = criticite  # numérique
        self.disponibilite = disponibilite
        self.integrite = integrite
        self.confidentialite = confidentialite
        self.perennite = perennite
        self.score = score
        self.answered_questions = answered_questions
        self.last_evaluation = last_evaluation  # datetime ou None
        self.responses = responses if responses is not None else {}
        self.comments = comments if comments is not None else {}
        self.evaluations = evaluations if evaluations is not None else []  # liste d'objets Evaluation

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "rda": self.rda,
            "possession": self.possession.isoformat() if isinstance(self.possession, datetime) else self.possession,
            "type_app": self.type_app,
            "hosting": self.hosting,
            "criticite": self.criticite,
            "disponibilite": self.disponibilite,
            "integrite": self.integrite,
            "confidentialite": self.confidentialite,
            "perennite": self.perennite,
            "score": self.score,
            "answered_questions": self.answered_questions,
            "last_evaluation": self.last_evaluation.isoformat() if isinstance(self.last_evaluation, datetime) else self.last_evaluation,
            "responses": self.responses,
            "comments": self.comments,
            "evaluations": [ev.to_dict() for ev in self.evaluations]
        }

    @classmethod
    def from_dict(cls, data):
        # Convertir possession et last_evaluation en objets datetime si nécessaire
        possession = None
        if data.get("possession"):
            try:
                possession = datetime.strptime(data["possession"], "%Y-%m-%d").date()
            except Exception:
                possession = data["possession"]
        last_eval = None
        if data.get("last_evaluation"):
            try:
                last_eval = datetime.fromisoformat(data["last_evaluation"])
            except Exception:
                last_eval = data["last_evaluation"]

        evaluations = []
        for ev_dict in data.get("evaluations", []):
            evaluations.append(Evaluation.from_dict(ev_dict))
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            rda=data.get("rda", ""),
            possession=possession,
            type_app=data.get("type_app", ""),
            hosting=data.get("hosting", ""),
            criticite=data.get("criticite"),
            disponibilite=data.get("disponibilite", ""),
            integrite=data.get("integrite", ""),
            confidentialite=data.get("confidentialite", ""),
            perennite=data.get("perennite", ""),
            score=data.get("score"),
            answered_questions=data.get("answered_questions", 0),
            last_evaluation=last_eval,
            responses=data.get("responses", {}),
            comments=data.get("comments", {}),
            evaluations=evaluations
        )

    def __repr__(self):
        return f"<Application id={self.id} name={self.name}>"


class Evaluation:
    def __init__(self, id=None, application_id=None, score=None, answered_questions=0,
                 last_evaluation=None, evaluator_name="", responses=None, comments=None, created_at=None):
        self.id = id
        self.application_id = application_id
        self.score = score
        self.answered_questions = answered_questions
        self.last_evaluation = last_evaluation  # datetime object
        self.evaluator_name = evaluator_name
        self.responses = responses if responses is not None else {}
        self.comments = comments if comments is not None else {}
        self.created_at = created_at if created_at is not None else datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "score": self.score,
            "answered_questions": self.answered_questions,
            "last_evaluation": self.last_evaluation.isoformat() if self.last_evaluation else None,
            "evaluator_name": self.evaluator_name,
            "responses": self.responses,
            "comments": self.comments,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data):
        last_eval = None
        if data.get("last_evaluation"):
            try:
                last_eval = datetime.fromisoformat(data["last_evaluation"])
            except Exception:
                last_eval = data["last_evaluation"]
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except Exception:
                created_at = data["created_at"]
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

    def __repr__(self):
        return f"<Evaluation id={self.id} score={self.score}>"


### CLASSES D'ORM "FAKE"

class JSONQuery:
    def __init__(self, model, data_list):
        self.model = model
        self.data_list = data_list  # Liste de dictionnaires

    def all(self):
        # Retourne une liste d'instances du modèle créées à partir des dictionnaires
        return [self.model.from_dict(record) for record in self.data_list]

    def filter_by(self, **kwargs):
        # Filtre la liste en fonction des paires clé=valeur
        filtered = []
        for record in self.data_list:
            match = True
            for k, v in kwargs.items():
                # On considère égalité simple
                if record.get(k) != v:
                    match = False
                    break
            if match:
                filtered.append(record)
        return JSONQuery(self.model, filtered)

class JSONSession:
    """
    Une session "dummy" qui simule l'accès à une base de données via un fichier JSON.
    Elle charge les données du fichier lors de l'initialisation et
    écrit les modifications lors du commit.
    """
    def __init__(self, db_filename=DB_FILENAME):
        self.db_filename = db_filename
        self._load()

        # Pour la gestion d'auto-incrément, on calcule le maximum id existant
        self._next_id = max((record.get("id", 0) for record in self._data), default=0) + 1
        # Pour simplifier, nous gérons ici uniquement les objets Application
        # Les évaluations sont stockées sous forme de liste dans chaque application

        # Garder une copie initiale pour rollback
        self._backup = self._data.copy()

    def _load(self):
        if not os.path.exists(self.db_filename):
            self._data = []
            self._save()  # Créer un fichier vide
        else:
            with open(self.db_filename, "r", encoding="utf-8") as f:
                try:
                    self._data = json.load(f)
                except Exception:
                    self._data = []

    def _save(self):
        with open(self.db_filename, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=4, ensure_ascii=False)

    def query(self, model):
        if model == Application:
            return JSONQuery(Application, self._data)
        # Si d'autres modèles sont nécessaires, on peut les ajouter ici
        return JSONQuery(model, [])

    def add(self, obj):
        if isinstance(obj, Application):
            # Si l'objet n'a pas d'ID, on lui en assigne un
            if obj.id is None:
                obj.id = self._next_id
                self._next_id += 1
            # On stocke l'objet sous forme de dictionnaire
            self._data.append(obj.to_dict())
        else:
            raise ValueError("Le type d'objet n'est pas supporté par JSONSession")

    def add_all(self, objects):
        for obj in objects:
            self.add(obj)

    def delete(self, obj):
        if isinstance(obj, Application):
            self._data = [record for record in self._data if record.get("id") != obj.id]
        else:
            raise ValueError("Le type d'objet n'est pas supporté par JSONSession")

    def commit(self):
        self._save()
        # Mettre à jour la sauvegarde pour un futur rollback
        self._backup = self._data.copy()

    def rollback(self):
        self._data = self._backup.copy()

    def close(self):
        pass  # Rien de particulier à faire ici

def get_engine(connection_url):
    """
    Dans cette version JSON, nous n'utilisons pas réellement la chaîne de connexion.
    On retourne simplement None.
    """
    return None

def get_session_factory(engine):
    """
    Retourne une fonction (factory) qui instancie une JSONSession.
    """
    def session_factory():
        return JSONSession()
    return session_factory

def init_db(connection_url):
    """
    Initialise la "base" JSON en s'assurant que le fichier existe.
    Retourne un "engine" factice (None).
    """
    if not os.path.exists(DB_FILENAME):
        with open(DB_FILENAME, "w", encoding="utf-8") as f:
            json.dump([], f)
    return None

# Pour tester ce module indépendamment, on peut ajouter un bloc de test
if __name__ == '__main__':
    # Exemple de test : insérer une application de test
    engine = init_db("dummy")
    Session = get_session_factory(engine)
    session = Session()

    app1 = Application(
        name="Test Application JSON",
        rda="Test RDA",
        possession="2025-04-09",
        type_app="Interne",
        hosting="On prem",
        criticite=4,
        disponibilite="D4",
        integrite="I4",
        confidentialite="C4",
        perennite="P4",
        score=None,
        answered_questions=0,
        last_evaluation=None,
        responses={},
        comments={},
        evaluations=[]
    )

    session.add(app1)
    session.commit()

    # Interroger et afficher les applications
    apps = session.query(Application).all()
    for a in apps:
        print(a)
