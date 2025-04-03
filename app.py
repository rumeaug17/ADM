"""
Application Flask de gestion d'un catalogue d'applications selon la classification DICP.

Fonctionnalités :
- Ajout, modification, suppression des applications.
- Évaluation via un système de score.
- Génération de graphiques (barres horizontales et radar) pour la synthèse.
- Lecture/écriture des données dans un fichier JSON.

Améliorations apportées :
- Documentation avec docstrings et commentaires.
- Réduction de la duplication de code grâce à des fonctions d'aide.
- Utilisation de constantes pour les valeurs récurrentes.
- Gestion des erreurs avec abort().
- Annotations de type pour plus de clarté.
"""

import os
import shutil
import json
import csv
import io
import base64
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional

import matplotlib.pyplot as plt
import numpy as np

from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort, Response, session, flash, Response

app = Flask(__name__)
app.config["DATA_FILE"] = "applications.json"
app.config["QUESTIONS_FILE"] = "questions.json"
app.config["BACKUP_FILE"] = "applications-prec.json"
app.config["CONFIG"] = "config.json"

def load_questions() -> dict:
    """Charge la configuration des questions depuis le fichier questions.json."""
    questions_file = os.path.join(app.static_folder, app.config["QUESTIONS_FILE"])
    with open(questions_file, "r", encoding="utf-8") as f:
        return json.load(f)      

# Charger les questions une seule fois au démarrage, ou bien les recharger selon vos besoins.
QUESTIONS = load_questions()

def load_config() -> List[Dict[str, Any]]:
    """Charge et retourne la liste des clés de configuration depuis le fichier JSON."""
    with open(app.config["CONFIG"], "r") as f:
        return json.load(f)

config = load_config()
app.secret_key = config["secret_key"]

# Constantes
SCORING_MAP: Dict[str, Optional[int]] = {
    "Oui total": 0,
    "Non": 0,
    "Partiel": 1,
    "Partiellement": 1,
    "Insuffisant": 2,
    "Majoritairement": 2,
    "Non applicable": None,
    "Totalement": 3,
    "Non total": 3,
}

CATEGORIES: Dict[str, List[str]] = {
    "Urbanisation": ["couplage", "decommissionnement"],
    "Organisation": ["doc", "team", "roadmap"],
    "Obsolescence": ["tech_obsolete", "mco", "support"],
    "Qualité et Développement": ["etat_art", "code_source", "respect", "tests"],
    "Sécurité et Conformité": ["securite", "vulnerabilites", "surveillance"],
    "Exploitation et Performance": ["incidents", "performances", "scalable"],
    "Fonctionnel": ["besoins_metier", "evolutivite", "recouvrement", "fonctions"],
}

# Initialisation du fichier de données s'il n'existe pas
if not os.path.exists(app.config["DATA_FILE"]):
    with open(app.config["DATA_FILE"], "w") as f:
        json.dump([], f)

def get_version_from_file() -> str:
    version_file = os.path.join(app.static_folder, "version.txt")
    try:
        with open(version_file, "r") as f:
            version = f.read().strip()
        return version
    except Exception as e:
        return "v0.0.0"

# Charger la version une seule fois au démarrage de l'application
APP_VERSION = get_version_from_file()

@app.context_processor
def inject_version():
    return dict(app_version=APP_VERSION)
        
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
    
def load_data() -> List[Dict[str, Any]]:
    """Charge et retourne la liste des applications depuis le fichier JSON."""
    with open(app.config["DATA_FILE"], "r") as f:
        return json.load(f)

def save_data(data: List[Dict[str, Any]]) -> None:
    """
    Enregistre la liste des applications dans le fichier JSON.
    Avant d'écrire, une sauvegarde du fichier existant est réalisée sous le nom applications-prec.json.
    """
    data_file = app.config["DATA_FILE"]
    # Si le fichier existe, en faire une sauvegarde
    if os.path.exists(data_file):
        shutil.copyfile(data_file, app.config["BACKUP_FILE"])
    with open(data_file, "w") as f:
        json.dump(data, f, indent=4)

def calculate_risk(app_item: Dict[str, Any]) -> Optional[float]:
    """
    Calcule le risque d'une application.
    Le risque est défini comme : risque = score * (produit des indicateurs DICP / criticité)
    
    Les indicateurs DICP sont : disponibilite, integrite, confidentialite, perennite.
    On extrait la partie numérique de chaque indicateur (par exemple, "D1" -> 1).
    La criticité est convertie en entier (attendu sous forme de "1", "2", etc.).
    
    Si le score ou la criticité n'est pas défini ou invalide, retourne None.
    """
    score = app_item.get("score")
    if score is None:
        return None
    try:
        # Conversion du score en float pour s'assurer d'un calcul numérique
        score = float(score)
    except Exception:
        return None
    try:
        # Extraction des valeurs numériques des indicateurs DICP
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
        return None  # Évite la division par zéro
    facteur = (d * i * c * p) / (4 * criticite)
    risque = score * facteur
    return risque

def update_app_metrics(app_item: Dict[str, Any]) -> None:
    """
    Met à jour les champs 'max_score' et 'percentage' pour une application donnée,
    en fonction du score et du nombre de questions répondues.
    """
    if app_item.get("score") is not None and app_item.get("answered_questions", 0) > 0:
        max_score = app_item["answered_questions"] * 3  # Score maximum possible
        percentage = round((app_item["score"] / max_score) * 100, 2)
        app_item["max_score"] = max_score
        app_item["percentage"] = percentage
        app_item["risque"] = calculate_risk(app_item)
    else:
        app_item["max_score"] = None
        app_item["percentage"] = None
        app_item["risque"] = None


def update_all_metrics(apps: List[Dict[str, Any]]) -> None:
    """Met à jour les métriques de chaque application dans la liste."""
    for app_item in apps:
        update_app_metrics(app_item)


def calculate_category_sums(app_item: Dict[str, Any]) -> Dict[str, int]:
    """
    Calcule la somme des scores pour chaque catégorie pour une application donnée.
    Pour chaque catégorie (dimension), on parcourt les questions et on additionne les scores
    en utilisant le mapping SCORING_MAP. Les réponses dont le score est None (par exemple "Non applicable")
    sont ignorées.
    """
    responses = app_item.get("responses", {})
    category_sums = {}
    for category, questions in CATEGORIES.items():
        total = 0
        for q in questions:
            # Récupération de la réponse pour la question q
            response_value = responses.get(q, "Non applicable")
            score = SCORING_MAP.get(response_value)
            if score is not None:
                total += score
        category_sums[category] = total
    return category_sums


def calculate_axis_scores(data: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calcule la note moyenne pour chaque axe de classification DICP (et autres) pour une liste d'applications.
    """
    axis_scores: Dict[str, List[float]] = {key: [] for key in CATEGORIES}
    
    for app_item in data:
        responses = app_item.get("responses", {})
        for category, questions in CATEGORIES.items():
            scores = [
                SCORING_MAP[responses.get(q, "Non applicable")]
                for q in questions
                if responses.get(q, "Non applicable") in SCORING_MAP and SCORING_MAP[responses.get(q, "Non applicable")] is not None
            ]
            if scores:
                axis_scores[category].append(sum(scores) / len(scores))
    
    avg_axis_scores = {
        key: round(sum(values) / len(values), 2) if values else 0 for key, values in axis_scores.items()
    }
    return avg_axis_scores


def generate_chart(avg_axis_scores: Dict[str, float]) -> str:
    """
    Génère un graphique à barres horizontal à partir des scores moyens par axe.
    Retourne le graphique encodé en base64 (format PNG).
    """
    categories = list(avg_axis_scores.keys())
    scores = list(avg_axis_scores.values())
    
    plt.figure(figsize=(8, 5))
    plt.barh(categories, scores, color=['blue', 'green', 'orange', 'red', 'purple', 'cyan'][:len(categories)])
    plt.xlabel("Note Moyenne")
    plt.xlim(-1, 3)
    plt.axvline(x=0, color='black', linestyle='--')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    chart_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    plt.close()  # Ferme la figure pour libérer la mémoire
    return chart_data


def generate_radar_chart(avg_axis_scores: Dict[str, float]) -> str:
    """
    Génère un graphique radar à partir des scores moyens par axe.
    Retourne le graphique encodé en base64 (format PNG).
    """
    categories = list(avg_axis_scores.keys())
    scores = list(avg_axis_scores.values())
    
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    # Pour fermer le radar, on répète le premier élément
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

    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        # Identifiants fixes pour cette authentification minimale
        if username == config["user"] and password == config["pwd"]:
            session['logged_in'] = True
            flash("Connexion réussie.", "success")
            return redirect(url_for("index"))
        else:
            flash("Identifiants incorrects.", "danger")
    return render_template("login.html")


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for("login"))


@app.route('/')
@login_required
def index():
    """
    Affiche la page d'accueil avec la liste des applications.
    Met à jour les métriques de chaque application avant affichage.
    """
    applications = load_data()
    update_all_metrics(applications)
    return render_template("index.html", applications=applications)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_application():
    """
    Route pour ajouter une nouvelle application.
    En POST, crée une nouvelle application et enregistre les données.
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
            "responses": {},  # Stockage des réponses individuelles
            "comments": {},       # Initialisation du champ "comments"
            "evaluations": []     # (Optionnel) pour conserver l'historique des évaluations
        }
        data.append(new_app)
        save_data(data)
        return redirect(url_for("index"))
    return render_template("add.html")


@app.route('/edit/<name>', methods=['GET', 'POST'])
@login_required
def edit_application(name: str):
    """
    Route pour modifier une application existante.
    Si l'application n'est pas trouvée, renvoie une erreur 404.
    """
    data = load_data()
    app_to_edit = next((app for app in data if app["name"] == name), None)
    if not app_to_edit:
        abort(404, description="Application non trouvée")
    
    if request.method == "POST":
        # Ici, on autorise la modification de tous les champs (si souhaité, le nom peut être en lecture seule)
        app_to_edit["name"] = request.form["name"]
        app_to_edit["rda"] = request.form["rda"]
        app_to_edit["possession"] = request.form["possession"]
        app_to_edit["type"] = request.form["type"]
        app_to_edit["criticite"] = request.form["criticite"]
        app_to_edit["disponibilite"] = request.form["disponibilite"]
        app_to_edit["integrite"] = request.form["integrite"]
        app_to_edit["confidentialite"] = request.form["confidentialite"]
        app_to_edit["perennite"] = request.form["perennite"]
        save_data(data)
        return redirect(url_for("index"))
    
    return render_template("edit.html", application=app_to_edit)


@app.route('/delete/<name>', methods=['POST'])
@login_required
def delete_application(name: str):
    """
    Supprime l'application dont le nom correspond à 'name'.
    Retourne un JSON indiquant le succès de l'opération.
    """
    data = load_data()
    data = [app for app in data if app["name"] != name]
    save_data(data)
    return redirect(url_for("index"))

@app.route('/score/<name>', methods=['GET', 'POST'])
@login_required
def score_application(name: str):
    data = load_data()
    application = next((app for app in data if app["name"] == name), None)
    if application is None:
        abort(404, description="Application non trouvée")
    
    # Initialisation du champ 'evaluations' s'il n'existe pas déjà
    if "evaluations" not in application:
        application["evaluations"] = []
    
    if request.method == 'POST':
        responses = request.form.to_dict()
        
        # Sauvegarde en brouillon (mise à jour temporaire, sans ajouter dans l'historique)
        if "save_draft" in request.form:
            # On stocke les réponses et commentaires dans des champs existants pour le brouillon
            application.setdefault("comments", {})
            application.setdefault("responses", {})
            for key, value in responses.items():
                if key.endswith("_comment"):
                    application["comments"][key] = value
                elif value in SCORING_MAP:
                    application["responses"][key] = value
            application["evaluator_name"] = responses.get("evaluator_name", "")
            save_data(data)
            flash("Brouillon enregistré.", "success")
        else:
            # Pour l'évaluation finale, vérifier que tous les commentaires sont remplis
            for key, value in responses.items():
                if key.endswith("_comment") and not value.strip():
                    flash("Tous les commentaires sont obligatoires pour l'évaluation.", "danger")
                    return render_template("score.html", application=application)
            
            # Calcul du score et collecte des réponses et commentaires spécifiques à cette évaluation
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
            
            # Création du dictionnaire représentant l'évaluation
            evaluation = {
                "score": score,
                "answered_questions": answered_questions,
                "last_evaluation": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "evaluator_name": responses.get("evaluator_name", ""),
                "responses": evaluation_responses,
                "comments": evaluation_comments
            }
            # Ajout de cette évaluation à l'historique
            application["evaluations"].append(evaluation)
            
            # Optionnel : mise à jour des champs principaux pour afficher la dernière évaluation rapidement
            application["score"] = score
            application["answered_questions"] = answered_questions
            application["last_evaluation"] = evaluation["last_evaluation"]
            application["evaluator_name"] = evaluation["evaluator_name"]
            
            # IMPORTANT : mise à jour des champs utilisés dans le formulaire (affichage des dernières réponses et commentaires)
            application["responses"] = evaluation_responses
            application["comments"] = evaluation_comments
            
            save_data(data)
            flash("Évaluation enregistrée.", "success")
            
        return redirect(url_for("index"))
    
    return render_template("score.html", application=application, questions=QUESTIONS)

@app.route('/reset/<name>', methods=['POST'])
@login_required
def reset_evaluation(name: str):
    data = load_data()
    # Recherche de l'application par son nom
    app_to_reset = next((app for app in data if app["name"] == name), None)
    if app_to_reset is None:
        abort(404, description="Application non trouvée")
    
    # Réinitialiser les champs d'évaluation sans toucher aux réponses et commentaires
    app_to_reset["score"] = None
    app_to_reset["answered_questions"] = 0
    app_to_reset["last_evaluation"] = None
    app_to_reset["evaluator_name"] = ""
    
    save_data(data)
    flash(f"L'évaluation de l'application '{name}' a été réinitialisée.", "success")
    return redirect(url_for("index"))

@app.route('/reevaluate_all', methods=['POST'])
@login_required
def reevaluate_all():
    """
    Réinitialise l'évaluation de toutes les applications en une seule opération,
    c'est-à-dire en mettant à None le score, à 0 le nombre de questions répondues,
    et en réinitialisant la date de dernière évaluation et l'évaluateur.
    """
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
def radar_chart(name: str):
    """
    Génère et retourne un graphique radar pour l'application spécifiée.
    Si l'application n'est pas trouvée, renvoie une erreur 404.
    """
    data = load_data()
    app_item = next((app for app in data if app["name"] == name), None)
    if not app_item:
        abort(404, description="Application non trouvée")
        
    # Calcule les scores par axe pour cette application en utilisant la fonction existante
    avg_axis_scores = calculate_axis_scores([app_item])
    chart_data = generate_radar_chart(avg_axis_scores)
    img_bytes = base64.b64decode(chart_data)
    return Response(img_bytes, mimetype='image/png')


@app.route('/synthese')
@login_required
def synthese():
    """
    Affiche la synthèse des applications avec :
    - Des indicateurs clés (KPI)
    - Un graphique radar global
    - Un tableau listant les applications filtrées selon leur score.
    """
    data = load_data()
    
    filter_score = request.args.get("filter_score", "above_30")
    
    for app_item in data:
        update_app_metrics(app_item)

    # Calculer le risque global sur les applications évaluées
    evaluated_risks = [app["risque"] for app in data if app.get("risque") is not None]
    if evaluated_risks:
        global_risk = round(sum(evaluated_risks) / len(evaluated_risks), 2)
    else:
        global_risk = None
        
    total_apps = len(data)
    # Filtrer selon le pourcentage
    if filter_score == "above_30":
        scored_apps = [app for app in data if app.get("percentage") is not None and app.get("percentage") > 30]
    elif filter_score == "above_60":
        scored_apps = [app for app in data if app.get("percentage") is not None and app.get("percentage") > 60]
    else:
        scored_apps = data.copy()
    
    avg_score = round(sum(app["score"] for app in data if app.get("score") is not None) / len(data), 2) if data else 0
    apps_above_30 = len([app for app in data if app.get("percentage") is not None and app.get("percentage") > 30])
    apps_above_60 = len([app for app in data if app.get("percentage") is not None and app.get("percentage") > 60])
        
    # Calcul global des scores moyens par axe pour le graphique radar global
    avg_axis_scores = calculate_axis_scores(data)
    chart_data = generate_radar_chart(avg_axis_scores)
    
    # Tri décroissant par score pour le tableau
    scored_apps.sort(key=lambda app: app["score"] if app.get("score") is not None else 0, reverse=True)
    
    # calcul du pire score par catégorie ---
    best_by_category = {}
    for category in CATEGORIES:
        best_app = None
        best_score = -1  # On initialise à -1 pour que 0 soit considéré
        for app in data:
            cat_score = calculate_category_sums(app).get(category, 0)
            if cat_score > best_score:
                best_score = cat_score
                best_app = app.get("name")
        best_by_category[category] = (best_app, best_score)
        
    # Regrouper par application
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
def export_csv():
    # Charger et mettre à jour les applications
    applications = load_data()
    update_all_metrics(applications)
    for app_item in applications:
        app_item["risque"] = calculate_risk(app_item)
    
    # Utiliser StringIO pour créer un buffer en mémoire
    si = io.StringIO()
    writer = csv.writer(si, delimiter=';')
    
    # Définir les en-têtes du CSV
    header = [
        "Nom", "Type", "RDA", "Criticité",
        "Disponibilité", "Intégrité", "Confidentialité", "Pérennité",
        "Score", "Max Score", "Pourcentage",
        "Dernière évaluation", "Évaluateur", "Risque"
    ]
    writer.writerow(header)
    
    # Pour chaque application, écrire une ligne
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
    
    # Retourner le fichier CSV avec un header pour le téléchargement
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=applications_export.csv"}
    )

@app.route('/resume/<name>')
@login_required
def resume(name: str):
    """
    Affiche un résumé détaillé d'une application.
    Le résumé regroupe toutes les informations présentes sur la page index et sur la page synthèse.
    """
    data = load_data()
    # Recherche l'application par son nom
    app_item = next((app for app in data if app["name"] == name), None)
    if not app_item:
        abort(404, description="Application non trouvée")
        
    # Si des évaluations existent, mettre à jour les champs pour l'affichage rapide
    if "evaluations" in app_item and app_item["evaluations"]:
        last_eval = app_item["evaluations"][-1]
        app_item["score"] = last_eval["score"]
        app_item["answered_questions"] = last_eval["answered_questions"]
        app_item["last_evaluation"] = last_eval["last_evaluation"]
        app_item["evaluator_name"] = last_eval["evaluator_name"]
        # Mise à jour des réponses et commentaires pour afficher le dernier formulaire rempli
        app_item["responses"] = last_eval["responses"]
        app_item["comments"] = last_eval["comments"]
    
    # Recalcul des métriques, y compris le risque
    update_app_metrics(app_item)
    
    # Calcul des scores par dimension pour l'évaluation courante à partir des réponses de la dernière évaluation
    if "evaluations" in app_item and app_item["evaluations"]:
        current_responses = app_item["evaluations"][-1].get("responses", {})
    else:
        current_responses = {}
    current_category_sums = calculate_category_sums({"responses": current_responses})
    
    # Calcul des scores par dimension pour l'évaluation précédente (si disponible)
    previous_category_sums = {}
    if "evaluations" in app_item and len(app_item["evaluations"]) > 1:
        previous_eval = app_item["evaluations"][-2]
        # On crée un dictionnaire temporaire pour utiliser la fonction existante
        previous_category_sums = calculate_category_sums({"responses": previous_eval.get("responses", {})})
    
    # Calcul et génération du graphique radar pour l'évaluation courante
    current_axis_scores = calculate_axis_scores([{"responses": app_item.get("responses", {})}])
    radar_chart_data = generate_radar_chart(current_axis_scores)
    
    return render_template(
        "resume.html",
        app=app_item,
        radar_chart=radar_chart_data,
        category_sums=current_category_sums,
        previous_category_sums=previous_category_sums
    )
    
    
if __name__ == '__main__':
    app.run(debug=True)
