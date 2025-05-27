
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

from compute import *
from auth import get_auth_backend

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

# --- Injection de la dépendance du backend de données ---

# Selon la configuration, choisir le backend à utiliser.
# Par convention, le fichier config.json devrait contenir une clé "db_backend"
# qui peut avoir la valeur "mysql" pour utiliser le module MySQL (database.py)
# ou "json" pour utiliser le module JSON (par exemple, database_json.py).
db_backend = config.get("db_backend", "mysql").lower()
if db_backend == "mysql":
    from database import init_db, get_session_factory, Application, Evaluation
    # La chaîne de connexion est attendue dans la configuration de l'application Flask.
    app.config["DB_CONNECTION"] = config.get("sql_connection_url", "mysql+mysqlconnector://root:password@localhost/adm_db")

elif db_backend == "json":
    # Assurez-vous d'avoir un module database_json.py qui implémente l'interface de database.
    from database_json import init_db, get_session_factory, Application, Evaluation
    # La chaîne de connexion est attendue dans la configuration de l'application Flask.
    app.config["DB_CONNECTION"] = config.get("json_connection_url", "applications.json")

else:
    abort(500, description="Configuration du backend incorrecte")

# --- Initialisation de la connexion à la base de données ---
engine = init_db(app.config["DB_CONNECTION"])
Session = get_session_factory(engine)

# --- Initialisation de l'authentification ---
auth_backend = get_auth_backend(config)
    
def get_question_def(q_key: str) -> dict:
    """
    Recherche dans le dictionnaire global QUESTIONS la définition 
    de la question ayant pour clé q_key.
    Renvoie un dictionnaire vide si non trouvé.
    """
    for category, qs in QUESTIONS.items():
        if q_key in qs:
            return qs[q_key]
    return {}
    
SCORING_MAP: Dict[str, Optional[int]] = compute_scoring_map(QUESTIONS)
CATEGORIES: Dict[str, List[str]] = compute_categories(QUESTIONS)

# --- Fonctions utilitaires ---

def app_to_dict(app_obj: Application) -> dict:
    return {
        "name": app_obj.name,
        "rda": app_obj.rda,
        "possession": app_obj.possession.isoformat() if app_obj.possession else None,
        "type_app": app_obj.type_app,
        "hosting": app_obj.hosting,
        "criticite": str(app_obj.criticite) if app_obj.criticite is not None else None,
        "disponibilite": app_obj.disponibilite,
        "integrite": app_obj.integrite,
        "confidentialite": app_obj.confidentialite,
        "perennite": app_obj.perennite,
        "score": app_obj.score,
        "answered_questions": app_obj.answered_questions,
        "last_evaluation": app_obj.last_evaluation.isoformat() if app_obj.last_evaluation else None,
        "responses": app_obj.responses,
        "comments": app_obj.comments,
        "evaluator_name": app_obj.evaluator_name,
        "evaluations": [
            {
                "score": ev.score,
                "answered_questions": ev.answered_questions,
                "last_evaluation": ev.last_evaluation.isoformat() if ev.last_evaluation else None,
                "evaluator_name": ev.evaluator_name,
                "responses": ev.responses,
                "comments": ev.comments,
                "created_at": ev.created_at.isoformat() if ev.created_at else None,
            }
            for ev in app_obj.evaluations
        ]
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
    # moyenne des facteurs dicp
    moy_dicp = (d * i * c * p) / 4
    # réduction de 50% du risque avec l'augmentation du nombre de questions
    facteur = (moy_dicp / criticite) / 2
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
    responses = app_item.get("responses", {})
    category_sums = {}
    for category, question_keys in CATEGORIES.items():
        total = 0
        for key in question_keys:
            response_value = responses.get(key, "Non applicable")
            # Récupérer la définition de la question pour obtenir le poids (par défaut 1)
            q_def = get_question_def(key)
            weight = q_def.get("weight", 1)
            score = SCORING_MAP.get(response_value)
            if score is not None:
                total += score * weight
        category_sums[category] = total
    return category_sums

def calculate_axis_scores(data: List[Dict[str, Any]]) -> Dict[str, float]:
    axis_scores: Dict[str, List[float]] = {key: [] for key in CATEGORIES}
    for app_item in data:
        responses = app_item.get("responses", {})
        for category, question_keys in CATEGORIES.items():
            weighted_scores = []
            for q in question_keys:
                if q in responses:
                    q_def = get_question_def(q)
                    weight = q_def.get("weight", 1)
                    opt_score = SCORING_MAP.get(responses.get(q, "Non applicable"))
                    if opt_score is not None:
                        weighted_scores.append(opt_score * weight)
            if weighted_scores:
                axis_scores[category].append(sum(weighted_scores) / len(weighted_scores))
    return {key: round(sum(values) / len(values), 2) if values else 0 for key, values in axis_scores.items()}
    

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



def generate_radar_chart(avg_axis_scores: Dict[str, float]) -> str:
    """
    Génère un graphique radar (en PNG encodé en base64) à partir des scores moyens par axe.
    L'échelle s'adapte dynamiquement en fonction du score maximal.
    """
    categories = list(avg_axis_scores.keys())
    scores = list(avg_axis_scores.values())

    import math

    # Détermine le score maximal et s'assure qu'il est un entier
    max_score = math.ceil(max(scores)) if scores else 3  # Arrondi vers le haut pour inclure toutes les valeurs

    # Boucler les scores pour fermer le graphique radar
    scores += scores[:1]
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]
    
    # Création du graphique
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"projection": "polar"})
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim(-1, max_score)  # Ajuste l'échelle Y au score maximal
    ax.set_yticks(range(-1, max_score + 1))  # Crée des ticks jusqu'au score maximal
    ax.set_yticklabels([str(i) for i in range(-1, max_score + 1)])
    ax.axhline(y=0, color='black', linestyle='--')
    
    # Tracer les données
    ax.plot(angles, scores, color='blue', linewidth=2, linestyle='solid')
    ax.fill(angles, scores, color='blue', alpha=0.25)
    
    # Sauvegarder l'image dans un buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    chart_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    plt.close()
    return chart_data
    

# --- Routes et gestion de l'authentification ---

@app.errorhandler(Exception)
def handle_exception(e):
    # Loggez l'erreur (optionnel)
    app.logger.error("Unhandled Exception: %s", e)
    # Récupération d'un code d'erreur si disponible, sinon 500
    code = getattr(e, "code", 500)
    # Affichez le template error.html en passant le message d'erreur
    return render_template("error.html", error_message=str(e)), code


@app.route('/login', methods=['GET', 'POST'])
def login() -> Any:
    """Route de connexion avec authentification minimale."""
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        if auth_backend.authenticate(username, password):
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
            
        if request.method == 'POST':
            # Mode brouillon : on ne vérifie pas que tous les commentaires sont remplis
            if "save_draft" in request.form:
                draft_responses = {}
                draft_comments = {}
                for key, value in request.form.items():
                    if key.endswith("_comment"):
                        draft_comments[key] = value
                    elif value in SCORING_MAP:
                        draft_responses[key] = value
                # Enregistrer le brouillon sans validation stricte des commentaires.
                app_item.responses = draft_responses
                app_item.comments = draft_comments
                # On peut enregistrer aussi le nom de l'évaluateur (facultatif)
                app_item.evaluator_name = request.form.get("evaluator_name", "")
                # Si vous souhaitez enregistrer un brouillon, vous ne mettez pas à jour le score final.
                session_db.commit()
                flash("Brouillon enregistré.", "success")
                return redirect(url_for("index"))
            else:
                # Mode évaluation finale : on vérifie que tous les commentaires sont renseignés
                for key, value in request.form.items():
                    if key.endswith("_comment") and not value.strip():
                        flash("Tous les commentaires sont obligatoires pour l'évaluation.", "danger")
                        return render_template("score.html", application=app_item, questions=QUESTIONS)
                
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
                            # Récupérer la définition de la question pour déterminer le poids (par défaut 1)
                            q_def = get_question_def(key)
                            weight = q_def.get("weight", 1)
                            score += SCORING_MAP[value] * weight
                            answered_questions += weight
                
                new_eval = Evaluation(
                    score=score,
                    answered_questions=answered_questions,
                    last_evaluation=datetime.now(),
                    evaluator_name=request.form.get("evaluator_name", ""),
                    responses=evaluation_responses,
                    comments=evaluation_comments
                )
                # Ajoute la nouvelle évaluation à l'historique de l'application
                app_item.evaluations.append(new_eval)
                # Met à jour l'application avec la nouvelle évaluation
                app_item.evaluator_name = new_eval.evaluator_name
                app_item.score = score
                app_item.answered_questions = answered_questions
                app_item.last_evaluation = new_eval.last_evaluation
                app_item.responses = evaluation_responses
                app_item.comments = evaluation_comments
                session_db.commit()
                flash("Évaluation enregistrée.", "success")
                return redirect(url_for("index"))
        
        
        # return render_template("score.html", application=app_item, questions=QUESTIONS)
        # Filtrer les questions à afficher en fonction du type d'application
        filtered_questions = filter_questions_by_type(QUESTIONS, app_item.type_app, app_item.hosting)
        return render_template("score.html", application=app_item, questions=filtered_questions)
        
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
        app_to_reset.evaluator_name = None
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
            app_item.evaluator_name = None
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

@app.route('/resume/<name>')
@login_required
def resume(name):
    session_db = Session()
    try:
        app_obj = get_app_by_name(name, session_db)
        if not app_obj:
            abort(404, description="Application non trouvée")
            
        # Convertir l'objet Application en dictionnaire pour faciliter le calcul des métriques
        app_item = app_to_dict(app_obj)
        
        # Tri des évaluations par date de création (si created_at est nul, on utilise datetime.min)
        evaluations_sorted = sorted(
            app_obj.evaluations, 
            key=lambda ev: ev.created_at if ev.created_at is not None else datetime.min
        )
        
        # Si au moins une évaluation existe, on utilise la plus récente
        if evaluations_sorted:
            last_eval_obj = evaluations_sorted[-1]
            last_eval = {
                "score": last_eval_obj.score,
                "answered_questions": last_eval_obj.answered_questions,
                "last_evaluation": last_eval_obj.last_evaluation.isoformat() if last_eval_obj.last_evaluation else None,
                "evaluator_name": last_eval_obj.evaluator_name,
                "responses": last_eval_obj.responses,
                "comments": last_eval_obj.comments
            }
            # Mettez à jour les données affichées avec la dernière évaluation
            app_item.update(last_eval)
        update_app_metrics(app_item)
        
        current_responses = app_item.get("responses", {}) if evaluations_sorted else {}
        current_category_sums = calculate_category_sums({"responses": current_responses})
        
        # Si au moins deux évaluations existent, on récupère l'évaluation précédente
        if len(evaluations_sorted) > 1:
            previous_eval_obj = evaluations_sorted[-2]
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
            current_eval=last_eval if evaluations_sorted else {},
            previous_eval=previous_eval
        )
    finally:
        session_db.close()

@app.route('/export_all')
@login_required
def export_all():
    session_db = Session()
    try:
        # Récupérer toutes les applications via la session (quelle que soit leur origine)
        db_apps = session_db.query(Application).all()
        # Convertir les objets en dictionnaire (incluant l'historique des évaluations)
        apps_list = [app_to_dict(app) for app in db_apps]
        # Exporter au format JSON avec une mise en forme lisible
        json_data = json.dumps(apps_list, indent=4, ensure_ascii=False)
        # Retourne une réponse avec les en-têtes appropriés pour télécharger un fichier
        return Response(
            json_data,
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=export_all.json"}
        )
    finally:
        session_db.close()

@app.route('/import_data', methods=['GET', 'POST'])
@login_required
def import_data():
    if request.method == 'POST':
        # Vérifier que le fichier a bien été transmis
        if 'file' not in request.files:
            flash("Aucun fichier n'a été sélectionné.", "danger")
            return redirect(url_for('import_data'))
        file = request.files['file']
        if file.filename == '':
            flash("Aucun fichier n'a été sélectionné.", "danger")
            return redirect(url_for('import_data'))
        try:
            # Charger le contenu JSON du fichier transmis
            data = json.load(file)
        except Exception as e:
            flash("Erreur lors du traitement du fichier : " + str(e), "danger")
            return redirect(url_for('import_data'))

        # Ouvrir une session pour effectuer la réimportation
        session_db = Session()
        try:
            # 1. Supprimer toutes les applications existantes.
            apps_to_delete = session_db.query(Application).all()
            for app_obj in apps_to_delete:
                session_db.delete(app_obj)
            session_db.commit()
            
            # 2. Réimporter toutes les applications depuis le fichier JSON.
            for record in data:
                new_app = Application.from_dict(record)
                session_db.add(new_app)
            session_db.commit()
            flash("Les données ont été réimportées avec succès.", "success")
        except Exception as e:
            session_db.rollback()
            flash("Erreur lors de l'importation : " + str(e), "danger")
        finally:
            session_db.close()
        return redirect(url_for("index"))
    # En GET, on affiche le formulaire de sélection de fichier avec modale.
    return render_template("import_data.html")


if __name__ == '__main__':
    app.run(debug=False)
