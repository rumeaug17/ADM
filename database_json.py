"""
Module database_json.py : Backend de persistance utilisant un fichier JSON.
Ce module implémente une interface identique à celle du module MySQL (database.py).
La "chaîne de connexion" passée est en réalité le chemin vers le fichier JSON.
"""

import os
import json
from datetime import date, datetime

### Classes de Modèles

class Application:
    def __init__(self, id=None, name="", rda="", possession=None, type_app="",
                 hosting="", criticite=None, disponibilite="", integrite="",
                 confidentialite="", perennite="", score=None, answered_questions=0,
                 last_evaluation=None, responses=None, comments=None, evaluations=None):
        self.id = id
        self.name = name
        self.rda = rda
        self.possession = possession  # date (objet ou chaîne "YYYY-MM-DD")
        self.type_app = type_app
        self.hosting = hosting
        self.criticite = criticite  # nombre (1,2,3,4)
        self.disponibilite = disponibilite
        self.integrite = integrite
        self.confidentialite = confidentialite
        self.perennite = perennite
        self.score = score
        self.answered_questions = answered_questions
        self.last_evaluation = last_evaluation  # datetime ou None
        self.responses = responses if responses is not None else {}
        self.comments = comments if comments is not None else {}
        self.evaluations = evaluations if evaluations is not None else []  # Liste d'objets Evaluation

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "rda": self.rda,
            "possession": self.possession.isoformat() if isinstance(self.possession, date) else self.possession,
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
        # Conversion pour possession
        possession = data.get("possession")
        if possession and isinstance(possession, str):
            try:
                possession = datetime.strptime(possession, "%Y-%m-%d").date()
            except Exception:
                pass
        # Conversion pour last_evaluation
        last_eval = data.get("last_evaluation")
        if last_eval and isinstance(last_eval, str):
            try:
                last_eval = datetime.fromisoformat(last_eval)
            except Exception:
                pass
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
        self.last_evaluation = last_evaluation  # datetime
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
        last_eval = data.get("last_evaluation")
        if last_eval and isinstance(last_eval, str):
            try:
                last_eval = datetime.fromisoformat(last_eval)
            except Exception:
                pass
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except Exception:
                pass
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

### Classes « fake ORM » pour JSON

class JSONQuery:
    def __init__(self, model, data_list):
        self.model = model
        self.data_list = data_list  # liste de dictionnaires

    def all(self):
        return [self.model.from_dict(record) for record in self.data_list]

    def filter_by(self, **kwargs):
        filtered = []
        for record in self.data_list:
            match = True
            for k, v in kwargs.items():
                if record.get(k) != v:
                    match = False
                    break
            if match:
                filtered.append(record)
        return JSONQuery(self.model, filtered)

class JSONSession:
    """
    Session "dummy" qui simule l'accès à une base de données via un fichier JSON.
    """
    def __init__(self, db_filename):
        self.db_filename = db_filename
        self._load()
        self._next_id = max((record.get("id", 0) for record in self._data), default=0) + 1
        self._backup = self._data.copy()

    def _load(self):
        if not os.path.exists(self.db_filename):
            self._data = []
            self._save()
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
        return JSONQuery(model, [])

    def add(self, obj):
        if isinstance(obj, Application):
            if obj.id is None:
                obj.id = self._next_id
                self._next_id += 1
            self._data.append(obj.to_dict())
        else:
            raise ValueError("Type d'objet non supporté par JSONSession")

    def add_all(self, objects):
        for obj in objects:
            self.add(obj)

    def delete(self, obj):
        if isinstance(obj, Application):
            self._data = [record for record in self._data if record.get("id") != obj.id]
        else:
            raise ValueError("Type d'objet non supporté par JSONSession")

    def commit(self):
        self._save()
        self._backup = self._data.copy()

    def rollback(self):
        self._data = self._backup.copy()

    def close(self):
        pass  # Aucun nettoyage nécessaire

### Fonctions d'interface pour le backend JSON

def get_engine(connection_url):
    """
    Pour le backend JSON, connection_url correspond au chemin du fichier JSON.
    """
    return None

def get_session_factory(engine, db_filename=None):
    """
    Retourne une factory de sessions pour le backend JSON.
    Si db_filename n'est pas fourni, une valeur par défaut est utilisée.
    """
    if db_filename is None:
        db_filename = "applications.json"
    def session_factory():
        return JSONSession(db_filename)
    return session_factory

def init_db(connection_url):
    """
    Initialise la "base de données" JSON en vérifiant que le fichier existe.
    La valeur connection_url est en réalité le chemin du fichier JSON.
    """
    if not os.path.exists(connection_url):
        with open(connection_url, "w", encoding="utf-8") as f:
            json.dump([], f)
    return None

# Fin du module database_json.py
