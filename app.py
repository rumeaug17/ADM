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

app = Flask(__name__)
# Configuration de l'application
app.config["DATA_FILE"] = "applications.json"
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

# --- Gestion des données ---

# Initialisation du fichier de données s'il n'existe pas
if not os.path.exists(app.config["DATA_FILE"]):
    with open(app.config["DATA_FILE"], "w", encoding="utf-8") as f:
        json.dump([], f)

def load_data() -> List[Dict[str, Any]]:
    """Charge la liste des applications depuis le fichier JSON."""
    return load_json_file(app.config["DATA_FILE"])

def save_data(data: List[Dict[str, Any]]) -> None:
    """
    Enregistre la liste des applications dans le fichier JSON.
    Une sauvegarde du fichier existant est effectuée avant l'écriture.
    """
    data_file = app.config["DATA_FILE"]
    if os.path.exists(data_file):
        shutil.copyfile(data_file, app.config["BACKUP_FILE"])
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Fonctions utilitaires ---

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

def get_app_by_name(name: str, data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Retourne l'application dont le nom correspond ou None si non trouvée."""
    return next((app for app in data if app["name"] == name), None)

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
    Génère un graphique radar en polar à partir des scores moyens par axe.
    
    La zone intérieure de la courbe est remplie avec un dégradé radial personnalisé :
      - Bleu au centre (r=0),
      - Dégradé vers jaune pour 1 < r ≤ 2,
      - Dégradé vers rouge pour 2 < r ≤ 3.
    
    Le dégradé est affiché sous forme d'image et clipé à la zone évaluée.
    Retourne l'image PNG encodée en base64.
    """
    # Préparation des données
    categories = list(avg_axis_scores.keys())
    scores = list(avg_axis_scores.values())
    # Fermer la boucle du radar
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    scores += scores[:1]
    angles += angles[:1]
    
    # Création de la figure en projection polaire
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'projection': 'polar'})
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 3)
    ax.set_yticks([0, 1, 2, 3])
    ax.set_yticklabels(["0", "1", "2", "3"])
    ax.axhline(y=0, color='black', linestyle='--')
    
    # Création du colormap personnalisé pour le dégradé radial
    # Le colormap va de bleu (au centre) à jaune (r=1 à r=2) puis à rouge (r=2 à r=3)
    cmap = LinearSegmentedColormap.from_list("radial_gradient", [(0,0,1), (1,1,0), (1,0,0)])
    
    # Créer une grille cartésienne couvrant le disque de rayon 3
    N = 500
    x = np.linspace(-3, 3, N)
    y = np.linspace(-3, 3, N)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    
    # Affichage de l'image de dégradé
    im = ax.imshow(R, extent=[-3, 3, -3, 3], origin='lower',
                   cmap=cmap, alpha=0.5, vmin=0, vmax=3, zorder=1)
    
    # Création de la zone de clipping : conversion de la courbe radar en coordonnées cartésiennes
    cartesian_verts = [(r * np.cos(theta), r * np.sin(theta)) for theta, r in zip(angles, scores)]
    poly = Polygon(cartesian_verts, closed=True, transform=ax.transData)
    im.set_clip_path(poly)
    
    # Tracé de la ligne du radar par-dessus le dégradé
    ax.plot(angles, scores, color='blue', linewidth=2, linestyle='solid', zorder=2)
    
    # Export de l'image dans un buffer et encodage en base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    chart_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    plt.close()
    return chart_data

def generate_radar_chart_basic(avg_axis_scores: Dict[str, float]) -> str:
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
def index() -> Any:
    """
    Affiche la liste des applications et met à jour leurs métriques.
    """
    applications = load_data()
    update_all_metrics(applications)
    return render_template("index.html", applications=applications)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_application() -> Any:
    """
    Permet d'ajouter une nouvelle application.
    En POST, crée et enregistre l'application.
    """
    if request.method == 'POST':
        data = load_data()
        new_app = {
            "name": request.form["name"],
            "rda": request.form["rda"],
            "possession": request.form["possession"],
            "type": request.form["type"],
            "criticite": request.form["criticite"],
            "disponibilite": request.form["disponibilite"],
            "integrite": request.form["integrite"],
            "confidentialite": request.form["confidentialite"],
            "perennite": request.form["perennite"],
            "score": None,
            "answered_questions": 0,
            "last_evaluation": None,
            "responses": {},
            "comments": {},
            "evaluations": []
        }
        data.append(new_app)
        save_data(data)
        return redirect(url_for("index"))
    return render_template("add.html")

@app.route('/edit/<name>', methods=['GET', 'POST'])
@login_required
def edit_application(name: str) -> Any:
    """
    Permet de modifier une application existante.
    Renvoie une erreur 404 si l'application n'est pas trouvée.
    """
    data = load_data()
    app_to_edit = get_app_by_name(name, data)
    if not app_to_edit:
        abort(404, description="Application non trouvée")
    
    if request.method == "POST":
        # Mise à jour des champs modifiables
        for field in ["name", "rda", "possession", "type", "criticite",
                      "disponibilite", "integrite", "confidentialite", "perennite"]:
            app_to_edit[field] = request.form[field]
        save_data(data)
        return redirect(url_for("index"))
    
    return render_template("edit.html", application=app_to_edit)

@app.route('/delete/<name>', methods=['POST'])
@login_required
def delete_application(name: str) -> Any:
    """Supprime une application par nom et redirige vers l'index."""
    data = load_data()
    data = [app for app in data if app["name"] != name]
    save_data(data)
    return redirect(url_for("index"))

@app.route('/score/<name>', methods=['GET', 'POST'])
@login_required
def score_application(name: str) -> Any:
    """
    Permet d'évaluer une application.
    En POST, sauvegarde soit un brouillon, soit l'évaluation finale.
    """
    data = load_data()
    application = get_app_by_name(name, data)
    if not application:
        abort(404, description="Application non trouvée")
    
    # Initialisation de l'historique des évaluations si nécessaire
    application.setdefault("evaluations", [])
    
    if request.method == 'POST':
        responses = request.form.to_dict()
        # Sauvegarde brouillon
        if "save_draft" in request.form:
            application.setdefault("responses", {})
            application.setdefault("comments", {})
            for key, value in responses.items():
                if key.endswith("_comment"):
                    application["comments"][key] = value
                elif value in SCORING_MAP:
                    application["responses"][key] = value
            application["evaluator_name"] = responses.get("evaluator_name", "")
            save_data(data)
            flash("Brouillon enregistré.", "success")
        else:
            # Validation que tous les commentaires sont renseignés
            for key, value in responses.items():
                if key.endswith("_comment") and not value.strip():
                    flash("Tous les commentaires sont obligatoires pour l'évaluation.", "danger")
                    return render_template("score.html", application=application, questions=QUESTIONS)
            # Calcul de l'évaluation finale
            score = 0
            answered_questions = 0
            evaluation_responses = {}
            evaluation_comments = {}
            for key, value in responses.items():
                if key.endswith("_comment"):
                    evaluation_comments[key] = value
                elif value in SCORING_MAP:
                    evaluation_responses[key] = value
                    if SCORING_MAP[value] is not None:
                        score += SCORING_MAP[value]
                        answered_questions += 1
            evaluation = {
                "score": score,
                "answered_questions": answered_questions,
                "last_evaluation": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "evaluator_name": responses.get("evaluator_name", ""),
                "responses": evaluation_responses,
                "comments": evaluation_comments
            }
            application["evaluations"].append(evaluation)
            # Mise à jour rapide de l'affichage
            application["score"] = score
            application["answered_questions"] = answered_questions
            application["last_evaluation"] = evaluation["last_evaluation"]
            application["evaluator_name"] = evaluation["evaluator_name"]
            application["responses"] = evaluation_responses
            application["comments"] = evaluation_comments
            save_data(data)
            flash("Évaluation enregistrée.", "success")
        return redirect(url_for("index"))
    
    return render_template("score.html", application=application, questions=QUESTIONS)

@app.route('/reset/<name>', methods=['POST'])
@login_required
def reset_evaluation(name: str) -> Any:
    """Réinitialise l'évaluation d'une application sans toucher aux réponses enregistrées."""
    data = load_data()
    app_to_reset = get_app_by_name(name, data)
    if not app_to_reset:
        abort(404, description="Application non trouvée")
    app_to_reset["score"] = None
    app_to_reset["answered_questions"] = 0
    app_to_reset["last_evaluation"] = None
    app_to_reset["evaluator_name"] = ""
    save_data(data)
    flash(f"L'évaluation de l'application '{name}' a été réinitialisée.", "success")
    return redirect(url_for("index"))

@app.route('/reevaluate_all', methods=['POST'])
@login_required
def reevaluate_all() -> Any:
    """Réinitialise l'évaluation de toutes les applications."""
    data = load_data()
    for app_item in data:
        app_item["score"] = None
        app_item["answered_questions"] = 0
        app_item["last_evaluation"] = None
        app_item["evaluator_name"] = ""
    save_data(data)
    flash("Toutes les évaluations ont été réinitialisées.", "success")
    return redirect(url_for("index"))

@app.route('/radar/<name>')
@login_required
def radar_chart(name: str) -> Any:
    """
    Génère et retourne un graphique radar pour une application.
    Renvoie une erreur 404 si l'application n'est pas trouvée.
    """
    data = load_data()
    app_item = get_app_by_name(name, data)
    if not app_item:
        abort(404, description="Application non trouvée")
    avg_axis_scores = calculate_axis_scores([app_item])
    chart_data = generate_radar_chart(avg_axis_scores)
    return Response(base64.b64decode(chart_data), mimetype='image/png')

@app.route('/synthese')
@login_required
def synthese() -> Any:
    """
    Affiche la synthèse globale des applications, avec KPI, graphique radar et tableau filtré.
    """
    data = load_data()
    filter_score = request.args.get("filter_score", "above_30")
    for app_item in data:
        update_app_metrics(app_item)
    evaluated_risks = [app["risque"] for app in data if app.get("risque") is not None]
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
    
    # Calcul du pire score par catégorie
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
    for category, (app_name, score) in best_by_category.items():
        if app_name:
            best_grouped.setdefault(app_name, []).append((category, score))
    
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

@app.route('/export_csv')
@login_required
def export_csv() -> Any:
    """Exporte les applications au format CSV pour téléchargement."""
    applications = load_data()
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
            app_item.get("type", ""),
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

@app.route('/resume/<name>')
@login_required
def resume(name: str) -> Any:
    """
    Affiche un résumé détaillé d'une application, incluant les dernières évaluations,
    un graphique radar et la comparaison avec l'évaluation précédente (si disponible).
    """
    data = load_data()
    app_item = get_app_by_name(name, data)
    if not app_item:
        abort(404, description="Application non trouvée")
    if app_item.get("evaluations"):
        last_eval = app_item["evaluations"][-1]
        app_item.update({
            "score": last_eval["score"],
            "answered_questions": last_eval["answered_questions"],
            "last_evaluation": last_eval["last_evaluation"],
            "evaluator_name": last_eval["evaluator_name"],
            "responses": last_eval["responses"],
            "comments": last_eval["comments"]
        })
    update_app_metrics(app_item)
    current_responses = app_item["evaluations"][-1].get("responses", {}) if app_item.get("evaluations") else {}
    current_category_sums = calculate_category_sums({"responses": current_responses})
    if app_item.get("evaluations") and len(app_item["evaluations"]) > 1:
        previous_eval = app_item["evaluations"][-2]
        previous_category_sums = calculate_category_sums({"responses": previous_eval.get("responses", {})})
    else:
        previous_eval = {}
        previous_category_sums = {}
    current_eval = app_item["evaluations"][-1] if app_item.get("evaluations") else {}
    current_axis_scores = calculate_axis_scores([{"responses": app_item.get("responses", {})}])
    radar_chart_data = generate_radar_chart(current_axis_scores)
    return render_template(
        "resume.html",
        app=app_item,
        radar_chart=radar_chart_data,
        category_sums=current_category_sums,
        previous_category_sums=previous_category_sums,
        questions=QUESTIONS,
        current_eval=current_eval,
        previous_eval=previous_eval
    )

if __name__ == '__main__':
    app.run(debug=True)
