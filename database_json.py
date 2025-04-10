"""
Module database_json.py : Backend de persistance utilisant un fichier JSON.
Ce module implémente une interface identique à celle du backend MySQL (database.py),
pour que l'application Flask puisse fonctionner sans changement selon le backend sélectionné.
La "chaine de connexion" dans ce cas est le chemin vers le fichier JSON.
"""

import os
import json
from datetime import datetime, date

### CLASSES MODELES

class Application:
    def __init__(self, id=None, name="", rda="", possession=None, type_app="",
                 hosting="", criticite=None, disponibilite="", integrite="",
                 confidentialite="", perennite="", score=None, answered_questions=0,
                 last_evaluation=None, responses=None, comments=None, evaluator_name="", evaluations=None):
        self.id = id
        self.name = name
        self.rda = rda
        self.possession = possession  # objet date ou chaîne "YYYY-MM-DD"
        self.type_app = type_app
        self.hosting = hosting
        self.criticite = criticite  # numérique (ex: 1,2,3,4)
        self.disponibilite = disponibilite
        self.integrite = integrite
        self.confidentialite = confidentialite
        self.perennite = perennite
        self.score = score
        self.answered_questions = answered_questions
        self.last_evaluation = last_evaluation  # datetime ou None
        self.responses = responses if responses is not None else {}
        self.comments = comments if comments is not None else {}
        self.evaluator_name = evaluator_name
        self.evaluations = evaluations if evaluations is not None else []  # Liste d'objets Evaluation

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "rda": self.rda,
            # Si possession est un objet date ou datetime, on le convertit en chaîne ISO.
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
            "evaluator_name": self.evaluator_name,  # Ajout dans le dictionnaire
            "evaluations": [ev.to_dict() for ev in self.evaluations]
        }

    @classmethod
    def from_dict(cls, data):
        # Conversion de la possession en objet date si nécessaire
        possession = data.get("possession")
        if possession and isinstance(possession, str):
            try:
                possession = datetime.strptime(possession, "%Y-%m-%d").date()
            except Exception:
                pass
        # Conversion de la dernière évaluation en datetime
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
            evaluator_name=data.get("evaluator_name", ""),  # Importation de l'attribut evaluator_name
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
            "last_evaluation": self.last_evaluation.isoformat() if self.last_evaluation and hasattr(self.last_evaluation, "isoformat") else self.last_evaluation,
            "evaluator_name": self.evaluator_name,
            "responses": self.responses,
            "comments": self.comments,
            "created_at": self.created_at.isoformat() if self.created_at and hasattr(self.created_at, "isoformat") else self.created_at
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

### CLASSE JSONQueryCustom

class JSONQueryCustom:
    def __init__(self, objects):
        self.objects = objects  # Liste d'instances "live"

    def all(self):
        return self.objects

    def filter_by(self, **kwargs):
        filtered = []
        for obj in self.objects:
            match = True
            for k, v in kwargs.items():
                if getattr(obj, k, None) != v:
                    match = False
                    break
            if match:
                filtered.append(obj)
        return JSONQueryCustom(filtered)

    def first(self):
        return self.objects[0] if self.objects else None

### CLASSE JSONSession AVEC TRACKING DES OBJETS LIVE

class JSONSession:
    """
    Une session qui simule une base de données via un fichier JSON.
    Elle charge les données du fichier et crée des instances "live" stockées dans _tracked.
    Les modifications sur ces instances sont synchronisées dans le fichier lors du commit.
    """
    def __init__(self, db_filename):
        self.db_filename = db_filename
        self._load()
        self._next_id = max((record.get("id", 0) for record in self._data), default=0) + 1
        self._tracked = {}  # Dictionnaire d'objets déjà créés, indexés par leur id.
        # Créer les objets trackés à partir de _data
        for record in self._data:
            obj = Application.from_dict(record)
            self._tracked[obj.id] = obj
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
            # Retourne les objets trackés sous forme d'une requête personnalisée.
            return JSONQueryCustom(list(self._tracked.values()))
        return JSONQueryCustom([])

    def add(self, obj):
        if isinstance(obj, Application):
            if obj.id is None:
                obj.id = self._next_id
                self._next_id += 1
            self._tracked[obj.id] = obj
        else:
            raise ValueError("Type d'objet non supporté par JSONSession")

    def add_all(self, objects):
        for obj in objects:
            self.add(obj)

    def delete(self, obj):
        if isinstance(obj, Application):
            if obj.id in self._tracked:
                del self._tracked[obj.id]
            self._data = [record for record in self._data if record.get("id") != obj.id]
        else:
            raise ValueError("Type d'objet non supporté par JSONSession")

    def commit(self):
        # Mettre à jour self._data en synchronisant tous les objets trackés
        id_to_index = {record.get("id"): i for i, record in enumerate(self._data)}
        for obj in self._tracked.values():
            if obj.id in id_to_index:
                self._data[id_to_index[obj.id]] = obj.to_dict()
            else:
                self._data.append(obj.to_dict())
        self._save()
        self._backup = self._data.copy()

    def rollback(self):
        self._data = self._backup.copy()
        # Recharger les objets trackés à partir de _data
        self._tracked = {}
        for record in self._data:
            obj = Application.from_dict(record)
            self._tracked[obj.id] = obj

    def close(self):
        pass  # Aucun nettoyage particulier nécessaire

### Fonctions d'interface

def get_engine(connection_url):
    """
    Dans ce backend, connection_url est le chemin vers le fichier JSON.
    """
    return None

def get_session_factory(engine, db_filename=None):
    if db_filename is None:
        db_filename = "applications.json"
    def session_factory():
        return JSONSession(db_filename)
    return session_factory

def init_db(connection_url):
    """
    Initialise la "base" JSON. Ici, connection_url est le chemin vers le fichier JSON.
    """
    if not os.path.exists(connection_url):
        with open(connection_url, "w", encoding="utf-8") as f:
            json.dump([], f)
    return None

# Fin du module database_json.py
