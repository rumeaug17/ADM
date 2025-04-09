"""
Application Flask de gestion d'un catalogue d'applications selon la classification DICP.

Fonctionnalités :
- Ajout, modification, suppression des applications.
- Évaluation via un système de score.
- Génération de graphiques (barres horizontales et radar) pour la synthèse.
- Lecture/écriture des données dans un fichier JSON.
"""

import os
import shutil
import json
import csv
import io
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.path import Path
from matplotlib.colors import LinearSegmentedColormap

import numpy as np

from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, abort, Response, session, flash

# Import du module de base de données
from database import init_db, get_session_factory, Application, Evaluation

app = Flask(__name__)
# Configuration de l'application
app.config["QUESTIONS_FILE"] = "questions.json"
app.config["BACKUP_FILE"] = "applications-prec.json"
app.config["CONFIG"] = "config.json"

# --- Chargement des configurations ---

def load_json_file(path: str) -> Any:
    """Charge un fichier JSON et retourne son contenu."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_questions() -> dict:
    """Charge la configuration des questions depuis le fichier questions.json situé dans le dossier static."""
    questions_path = os.path.join(app.static_folder, app.config["QUESTIONS_FILE"])
    return load_json_file(questions_path)

def load_config() -> List[Dict[str, Any]]:
    """Charge la configuration depuis le fichier config.json."""
    return load_json_file(app.config["CONFIG"])

# Charger les configurations au démarrage
QUESTIONS = load_questions()
config = load_config()
app.secret_key = config["secret_key"]

# --- Calcul des constantes dynamiques ---

def compute_categories(questions: dict) -> dict:
    """
    Extrait pour chaque catégorie la liste des clés des questions,
    en ignorant les clés commençant par un underscore.
    """
    categories = {}
    for category, questions_dict in questions.items():
        q_keys = [key for key in questions_dict.keys() if not key.startswith("_")]
        categories[category] = q_keys
    return categories

def compute_scoring_map(questions: dict) -> dict:
    """
    Construit un dictionnaire qui associe chaque option de réponse à sa note,
    en parcourant toutes les options définies dans questions.json.
    """
    scoring_map = {}
    for _, questions_dict in questions.items():
        for q_key, q_def in questions_dict.items():
            if isinstance(q_def, dict) and "options" in q_def:
                for option in q_def["options"]:
                    if isinstance(option, dict):
                        value = option.get("value")
                        score = option.get("score")
                        scoring_map[value] = score
    return scoring_map

SCORING_MAP: Dict[str, Optional[int]] = compute_scoring_map(QUESTIONS)
CATEGORIES: Dict[str, List[str]] = compute_categories(QUESTIONS)

# --- Initialisation de la connexion à la base de données ---

# La chaîne de connexion est attendue dans la configuration de l'application Flask.
app.config["DB_CONNECTION"] = config.get("sql_connection_url", "mysql+mysqlconnector://root:password@localhost/adm_db")
engine = init_db(app.config["DB_CONNECTION"])
Session = get_session_factory(engine)

# --- Gestion des données ---

# --- Fonctions utilitaires ---

def filter_questions_by_type(questions: dict, type_app: str, hosting: str) -> dict:
    """
    Filtre les questions en s'appuyant sur deux critères indépendants :
      - Si une question contient la clé "app_types", le type_app de l'application doit être 
        dans la liste (après normalisation).
      - Si une question contient la clé "hosting_types", le hosting de l'application doit être 
        dans la liste (après normalisation).
    Si une question ne possède pas l'une ou l'autre de ces clés, le critère correspondant n'est pas appliqué.
    Seules les questions satisfaisant tous les filtres spécifiés seront retournées.
    """
    filtered_questions = {}
    # Normaliser les valeurs de l'application
    type_app_norm = type_app.strip().lower()
    hosting_norm = hosting.strip().lower()
    for category, qs in questions.items():
        filtered_qs = {}
        for key, q_def in qs.items():
            include = True
            # Filtrage sur le type d'application
            if "app_types" in q_def:
                allowed_app = [val.strip().lower() for val in q_def["app_types"]]
                if type_app_norm not in allowed_app:
                    include = False
            # Filtrage sur le type d'hébergement
            if "hosting_types" in q_def:
                allowed_hosting = [val.strip().lower() for val in q_def["hosting_types"]]
                if hosting_norm not in allowed_hosting:
                    include = False
            if include:
                filtered_qs[key] = q_def
        filtered_questions[category] = filtered_qs
    return filtered_questions


def get_version_from_file() -> str:
    """Lit et retourne la version de l'application depuis version.txt situé dans static."""
    version_file = os.path.join(app.static_folder, "version.txt")
    try:
        with open(version_file, "r") as f:
            return f.read().strip()
    except Exception:
        return "v0.0.0"

APP_VERSION = get_version_from_file()

@app.context_processor
def inject_version():
    """Injecte la version de l'application dans tous les templates."""
    return dict(app_version=APP_VERSION)

def login_required(f):
    """Décorateur pour protéger les routes nécessitant une authentification."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_app_by_name(name: str, session_db) -> Application:
    return session_db.query(Application).filter_by(name=name).first()

def app_to_dict(app_obj: Application) -> dict:
    """
    Convertit un objet Application en dictionnaire pour pouvoir être exploité
    par les fonctions de calcul des métriques et de génération des graphiques.
    """
    return {
        "name": app_obj.name,
        "rda": app_obj.rda,
        "possession": app_obj.possession.isoformat() if app_obj.possession else None,
        "type_app": app_obj.type_app,
        "hosting": app_obj.hosting,
        "criticite": app_obj.criticite,
        "disponibilite": app_obj.disponibilite,
        "integrite": app_obj.integrite,
        "confidentialite": app_obj.confidentialite,
        "perennite": app_obj.perennite,
        "score": app_obj.score,
        "answered_questions": app_obj.answered_questions,
        "last_evaluation": app_obj.last_evaluation.isoformat() if app_obj.last_evaluation else None,
        "responses": app_obj.responses,
        "comments": app_obj.comments
    }
    
# --- Calcul des métriques et graphiques ---

def calculate_risk(app_item: Dict[str, Any]) -> Optional[float]:
    """
    Calcule le risque d'une application à partir de son score et de ses indicateurs DICP.
    La formule est : risque = score * (produit des indicateurs numériques / criticité).
    """
    score = app_item.get("score")
    if score is None:
        return None
    try:
        score = float(score)
    except Exception:
        return None
    try:
        d = int(''.join(filter(str.isdigit, app_item.get("disponibilite", "0"))))
        i = int(''.join(filter(str.isdigit, app_item.get("integrite", "0"))))
        c = int(''.join(filter(str.isdigit, app_item.get("confidentialite", "0"))))
        p = int(''.join(filter(str.isdigit, app_item.get("perennite", "0"))))
    except Exception:
        return None
    try:
        criticite = int(app_item.get("criticite", "0"))
    except Exception:
        criticite = 0
    if criticite == 0:
        return None
    facteur = (d * i * c * p) / (4 * criticite)
    return score * facteur

def update_app_metrics(app_item: Dict[str, Any]) -> None:
    """
    Met à jour 'max_score', 'percentage' et 'risque' pour une application.
    Le score maximum est calculé en supposant 3 points par question répondue.
    """
    if app_item.get("score") is not None and app_item.get("answered_questions", 0) > 0:
        max_score = app_item["answered_questions"] * 3
        percentage = round((app_item["score"] / max_score) * 100, 2)
        app_item["max_score"] = max_score
        app_item["percentage"] = percentage
        app_item["risque"] = calculate_risk(app_item)
    else:
        app_item["max_score"] = None
        app_item["percentage"] = None
        app_item["risque"] = None

def update_all_metrics(apps: List[Dict[str, Any]]) -> None:
    """Met à jour les métriques pour toutes les applications."""
    for app_item in apps:
        update_app_metrics(app_item)

def calculate_category_sums(app_item: Dict[str, Any]) -> Dict[str, int]:
    """
    Calcule la somme des scores pour chaque catégorie, en se basant sur les réponses et SCORING_MAP.
    Les réponses dont le score est None sont ignorées.
    """
    responses = app_item.get("responses", {})
    category_sums = {}
    for category, question_keys in CATEGORIES.items():
        total = 0
        for key in question_keys:
            response_value = responses.get(key, "Non applicable")
            score = SCORING_MAP.get(response_value)
            if score is not None:
                total += score
        category_sums[category] = total
    return category_sums

def calculate_axis_scores(data: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calcule la note moyenne par axe (catégorie) pour une liste d'applications.
    """
    axis_scores: Dict[str, List[float]] = {key: [] for key in CATEGORIES}
    for app_item in data:
        responses = app_item.get("responses", {})
        for category, question_keys in CATEGORIES.items():
            scores = [
                SCORING_MAP[responses.get(q, "Non applicable")]
                for q in question_keys
                if responses.get(q, "Non applicable") in SCORING_MAP and SCORING_MAP[responses.get(q, "Non applicable")] is not None
            ]
            if scores:
                axis_scores[category].append(sum(scores) / len(scores))
    return {key: round(sum(values)/len(values), 2) if values else 0 for key, values in axis_scores.items()}


def generate_radar_chart(avg_axis_scores: Dict[str, float]) -> str:
    """
    Génère un graphique radar (en PNG encodé en base64) à partir des scores moyens par axe.
    """
    categories = list(avg_axis_scores.keys())
    scores = list(avg_axis_scores.values())
    
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    scores += scores[:1]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"projection": "polar"})
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim(-1, 3)
    ax.set_yticks([-1, 0, 1, 2, 3])
    ax.set_yticklabels(["-1", "0", "1", "2", "3"])
    ax.axhline(y=0, color='black', linestyle='--')
    
    ax.plot(angles, scores, color='blue', linewidth=2, linestyle='solid')
    ax.fill(angles, scores, color='blue', alpha=0.25)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    chart_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    plt.close()
    return chart_data

# --- Routes et gestion de l'authentification ---

@app.route('/login', methods=['GET', 'POST'])
def login() -> Any:
    """Route de connexion avec authentification minimale."""
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        if username == config["user"] and password == config["pwd"]:
            session['logged_in'] = True
            flash("Connexion réussie.", "success")
            return redirect(url_for("index"))
        else:
            flash("Identifiants incorrects.", "danger")
    return render_template("login.html")

@app.route('/logout')
def logout() -> Any:
    """Déconnexion et redirection vers la page de connexion."""
    session.pop('logged_in', None)
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for("login"))

@app.route('/')
@login_required
def index():
    session_db = Session()
    try:
        app_objs = session_db.query(Application).all()
        # Convertir les objets ORM en dictionnaires
        applications = [app_to_dict(app) for app in app_objs]
        # Mettre à jour les métriques pour chaque application convertie
        for app_item in applications:
            update_app_metrics(app_item)
        return render_template("index.html", applications=applications)
    finally:
        session_db.close()
        
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_application():
    if request.method == 'POST':
        session_db = Session()
        try:
            # Création d'une nouvelle application
            new_app = Application(
                name=request.form["name"],
                rda=request.form["rda"],
                possession=datetime.strptime(request.form["possession"], "%Y-%m-%d").date(),
                type_app=request.form["type_app"],
                hosting=request.form["hosting"],
                criticite=request.form["criticite"],
                disponibilite=request.form["disponibilite"],
                integrite=request.form["integrite"],
                confidentialite=request.form["confidentialite"],
                perennite=request.form["perennite"],
                score=None,
                answered_questions=0,
                last_evaluation=None,
                responses={},
                comments={}
            )
            session_db.add(new_app)
            session_db.commit()
            return redirect(url_for("index"))
        finally:
            session_db.close()
    return render_template("add.html")

@app.route('/edit/<name>', methods=['GET', 'POST'])
@login_required
def edit_application(name):
    session_db = Session()
    try:
        app_to_edit = get_app_by_name(name, session_db)
        if not app_to_edit:
            abort(404, description="Application non trouvée")
        if request.method == "POST":
            # Mise à jour des champs modifiables
            app_to_edit.rda = request.form["rda"]
            app_to_edit.possession = datetime.strptime(request.form["possession"], "%Y-%m-%d").date()
            app_to_edit.type_app = request.form["type_app"]
            app_to_edit.hosting = request.form["hosting"]
            app_to_edit.criticite = request.form["criticite"]
            app_to_edit.disponibilite = request.form["disponibilite"]
            app_to_edit.integrite = request.form["integrite"]
            app_to_edit.confidentialite = request.form["confidentialite"]
            app_to_edit.perennite = request.form["perennite"]
            session_db.commit()
            return redirect(url_for("index"))
        return render_template("edit.html", application=app_to_edit)
    finally:
        session_db.close()

@app.route('/delete/<name>', methods=['POST'])
@login_required
def delete_application(name):
    session_db = Session()
    try:
        app_to_delete = get_app_by_name(name, session_db)
        if not app_to_delete:
            abort(404, description="Application non trouvée")
        session_db.delete(app_to_delete)
        session_db.commit()
        return redirect(url_for("index"))
    finally:
        session_db.close()

@app.route('/score/<name>', methods=['GET', 'POST'])
@login_required
def score_application(name):
    session_db = Session()
    try:
        app_item = get_app_by_name(name, session_db)
        if not app_item:
            abort(404, description="Application non trouvée")
            
        # En POST, on traite le formulaire d'évaluation
        if request.method == 'POST':
            # --- Validation des commentaires ---
            for key, value in request.form.items():
                if key.endswith("_comment") and not value.strip():
                    flash("Tous les commentaires sont obligatoires pour l'évaluation.", "danger")
                    return render_template("score.html", application=app_item, questions=QUESTIONS)
            
            # Traitement des réponses et calcul du score
            evaluation_responses = {}
            evaluation_comments = {}
            score = 0
            answered_questions = 0
            
            for key, value in request.form.items():
                if key.endswith("_comment"):
                    evaluation_comments[key] = value
                elif value in SCORING_MAP:
                    evaluation_responses[key] = value
                    if SCORING_MAP[value] is not None:
                        score += SCORING_MAP[value]
                        answered_questions += 1
            
            new_eval = Evaluation(
                score=score,
                answered_questions=answered_questions,
                last_evaluation=datetime.now(),
                evaluator_name=request.form.get("evaluator_name", ""),
                responses=evaluation_responses,
                comments=evaluation_comments
            )
            
            # Ajout de la nouvelle évaluation à l'application et mise à jour des indicateurs
            app_item.evaluations.append(new_eval)
            app_item.score = score
            app_item.answered_questions = answered_questions
            app_item.last_evaluation = new_eval.last_evaluation
            app_item.responses = evaluation_responses
            app_item.comments = evaluation_comments
            session_db.commit()
            flash("Évaluation enregistrée.", "success")
            return redirect(url_for("index"))
        
        return render_template("score.html", application=app_item, questions=QUESTIONS)
    finally:
        session_db.close()

@app.route('/reset/<name>', methods=['POST'])
@login_required
def reset_evaluation(name):
    session_db = Session()
    try:
        app_to_reset = get_app_by_name(name, session_db)
        if not app_to_reset:
            abort(404, description="Application non trouvée")
        # Réinitialiser les évaluations de l'application
        app_to_reset.score = None
        app_to_reset.answered_questions = 0
        app_to_reset.last_evaluation = None
        app_to_reset.responses = {}
        app_to_reset.comments = {}
        session_db.commit()
        flash(f"L'évaluation de l'application '{name}' a été réinitialisée.", "success")
        return redirect(url_for("index"))
    finally:
        session_db.close()

@app.route('/reevaluate_all', methods=['POST'])
@login_required
def reevaluate_all():
    session_db = Session()
    try:
        applications = session_db.query(Application).all()
        for app_item in applications:
            app_item.score = None
            app_item.answered_questions = 0
            app_item.last_evaluation = None
            app_item.responses = {}
            app_item.comments = {}
        session_db.commit()
        flash("Toutes les évaluations ont été réinitialisées.", "success")
        return redirect(url_for("index"))
    finally:
        session_db.close()

# --- Nouvelle route : Radar Chart ---
@app.route('/radar/<name>')
@login_required
def radar_chart(name):
    session_db = Session()
    try:
        app_obj = get_app_by_name(name, session_db)
        if not app_obj:
            abort(404, description="Application non trouvée")
        # Pour générer le graphique radar, on utilise les réponses stockées.
        # On suppose que la fonction calculate_axis_scores attend un dictionnaire avec la clé "responses".
        avg_axis_scores = calculate_axis_scores([{"responses": app_obj.responses}])
        chart_data = generate_radar_chart(avg_axis_scores)
        return Response(base64.b64decode(chart_data), mimetype='image/png')
    finally:
        session_db.close()

# --- Nouvelle route : Synthèse ---
@app.route('/synthese')
@login_required
def synthese():
    session_db = Session()
    try:
        filter_score = request.args.get("filter_score", "above_30")
        db_apps = session_db.query(Application).all()
        # Conversion des objets ORM en dictionnaires
        data = [app_to_dict(app) for app in db_apps]
        
        # Mise à jour des métriques pour chaque application
        for app_item in data:
            update_app_metrics(app_item)
        evaluated_risks = [app_item.get("risque") for app_item in data if app_item.get("risque") is not None]
        global_risk = round(sum(evaluated_risks) / len(evaluated_risks), 2) if evaluated_risks else None
        total_apps = len(data)
        
        if filter_score == "above_30":
            scored_apps = [app for app in data if app.get("percentage") and app["percentage"] > 30]
        elif filter_score == "above_60":
            scored_apps = [app for app in data if app.get("percentage") and app["percentage"] > 60]
        else:
            scored_apps = data.copy()
            
        avg_score = round(sum(app["score"] for app in data if app.get("score") is not None) / len(data), 2) if data else 0
        apps_above_30 = len([app for app in data if app.get("percentage") and app["percentage"] > 30])
        apps_above_60 = len([app for app in data if app.get("percentage") and app["percentage"] > 60])
        avg_axis_scores = calculate_axis_scores(data)
        chart_data = generate_radar_chart(avg_axis_scores)
        scored_apps.sort(key=lambda app: app.get("score") or 0, reverse=True)
        
        # Calcul des pires scores (ou meilleurs, selon la logique)
        best_by_category = {}
        for category in CATEGORIES:
            best_app = None
            best_score = -1
            for app_item in data:
                cat_score = calculate_category_sums(app_item).get(category, 0)
                if cat_score > best_score:
                    best_score = cat_score
                    best_app = app_item.get("name")
            best_by_category[category] = (best_app, best_score)
        best_grouped = {}
        for category, (app_name, score_val) in best_by_category.items():
            if app_name:
                best_grouped.setdefault(app_name, []).append((category, score_val))
        
        return render_template(
            "synthese.html",
            applications=scored_apps,
            total_apps=total_apps,
            avg_score=avg_score,
            apps_above_30=apps_above_30,
            apps_above_60=apps_above_60,
            filter_score=filter_score,
            avg_axis_scores=avg_axis_scores,
            chart_data=chart_data,
            global_risk=global_risk,
            best_grouped=best_grouped
        )
    finally:
        session_db.close()

# --- Nouvelle route : Export CSV ---
@app.route('/export_csv')
@login_required
def export_csv():
    session_db = Session()
    try:
        db_apps = session_db.query(Application).all()
        applications = [app_to_dict(app) for app in db_apps]
        update_all_metrics(applications)
        for app_item in applications:
            app_item["risque"] = calculate_risk(app_item)
        si = io.StringIO()
        writer = csv.writer(si, delimiter=';')
        header = ["Nom", "Type", "RDA", "Criticité", "Disponibilité", "Intégrité", "Confidentialité",
                  "Pérennité", "Score", "Max Score", "Pourcentage", "Dernière évaluation", "Évaluateur", "Risque"]
        writer.writerow(header)
        for app_item in applications:
            row = [
                app_item.get("name", ""),
                f"{app_item.get('type_app', '')} / {app_item.get('hosting', '')}",
                app_item.get("rda", ""),
                app_item.get("criticite", ""),
                app_item.get("disponibilite", ""),
                app_item.get("integrite", ""),
                app_item.get("confidentialite", ""),
                app_item.get("perennite", ""),
                app_item.get("score", ""),
                app_item.get("max_score", ""),
                app_item.get("percentage", ""),
                app_item.get("last_evaluation", ""),
                app_item.get("evaluator_name", ""),
                "" if app_item.get("risque") is None else round(app_item.get("risque"))
            ]
            writer.writerow(row)
        output = si.getvalue()
        si.close()
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=applications_export.csv"}
        )
    finally:
        session_db.close()

# --- Nouvelle route : Resume ---
@app.route('/resume/<name>')
@login_required
def resume(name):
    session_db = Session()
    try:
        app_obj = get_app_by_name(name, session_db)
        if not app_obj:
            abort(404, description="Application non trouvée")
            
        app_item = app_to_dict(app_obj)
        
        if app_obj.evaluations:
            # Utilisation de la dernière évaluation
            last_eval_obj = app_obj.evaluations[-1]
            last_eval = {
                "score": last_eval_obj.score,
                "answered_questions": last_eval_obj.answered_questions,
                "last_evaluation": last_eval_obj.last_evaluation.isoformat() if last_eval_obj.last_evaluation else None,
                "evaluator_name": last_eval_obj.evaluator_name,
                "responses": last_eval_obj.responses,
                "comments": last_eval_obj.comments
            }
            app_item.update(last_eval)
        update_app_metrics(app_item)
        
        current_responses = app_item.get("responses", {}) if app_obj.evaluations else {}
        current_category_sums = calculate_category_sums({"responses": current_responses})
        if app_obj.evaluations and len(app_obj.evaluations) > 1:
            previous_eval_obj = app_obj.evaluations[-2]
            previous_eval = {
                "score": previous_eval_obj.score,
                "answered_questions": previous_eval_obj.answered_questions,
                "last_evaluation": previous_eval_obj.last_evaluation.isoformat() if previous_eval_obj.last_evaluation else None,
                "evaluator_name": previous_eval_obj.evaluator_name,
                "responses": previous_eval_obj.responses,
                "comments": previous_eval_obj.comments
            }
            previous_category_sums = calculate_category_sums({"responses": previous_eval.get("responses", {})})
        else:
            previous_eval = {}
            previous_category_sums = {}
        current_axis_scores = calculate_axis_scores([{"responses": app_item.get("responses", {})}])
        radar_chart_data = generate_radar_chart(current_axis_scores)
        
        return render_template(
            "resume.html",
            app=app_item,
            radar_chart=radar_chart_data,
            category_sums=current_category_sums,
            previous_category_sums=previous_category_sums,
            questions=QUESTIONS,
            current_eval=last_eval if app_obj.evaluations else {},
            previous_eval=previous_eval
        )
    finally:
        session_db.close()


if __name__ == '__main__':
    app.run(debug=True)
