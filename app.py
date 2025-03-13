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
import io
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional

import matplotlib.pyplot as plt
import numpy as np

from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort, Response, session, flash

app = Flask(__name__)
app.config["DATA_FILE"] = "applications.json"
app.config["BACKUP_FILE"] = "applications-prec.json"
app.config["CONFIG"] = "config.json"

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
    "Fonctionnel": ["besoins_metier", "evolutivite", "recouvrement"],
}

# Initialisation du fichier de données s'il n'existe pas
if not os.path.exists(app.config["DATA_FILE"]):
    with open(app.config["DATA_FILE"], "w") as f:
        json.dump([], f)

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
    else:
        app_item["max_score"] = None
        app_item["percentage"] = None


def update_all_metrics(apps: List[Dict[str, Any]]) -> None:
    """Met à jour les métriques de chaque application dans la liste."""
    for app_item in apps:
        update_app_metrics(app_item)


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
            "type": request.form["type"],
            "criticite": request.form["criticite"], 
            "disponibilite": request.form["disponibilite"],
            "integrite": request.form["integrite"],
            "confidentialite": request.form["confidentialite"],
            "perennite": request.form["perennite"],
            "score": None,
            "answered_questions": 0,
            "last_evaluation": None,
            "responses": {}  # Stockage des réponses individuelles
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
    """
    Route pour évaluer une application.
    En POST, met à jour les réponses, le score, le nombre de questions répondues et la date de la dernière évaluation.
    """
    data = load_data()
    application = next((app for app in data if app["name"] == name), None)
    if application is None:
        abort(404, description="Application non trouvée")

    if "comments" not in application:
        application["comments"] = {}  # Initialisation du champ des commentaires
        
    if request.method == 'POST':
        responses = request.form.to_dict()
        
        # Si le formulaire contient le champ 'save_draft', on enregistre en brouillon sans calcul du score.
        if "save_draft" in request.form:
            for key, value in responses.items():
                if key.endswith("_comment"):
                    application["comments"][key] = value  # Enregistrement du commentaire
                elif value in SCORING_MAP:
                    application["responses"][key] = value  # Enregistrement de la réponse
            # On peut mettre à jour l'évaluateur mais pas la date
            application["evaluator_name"] = responses.get("evaluator_name", "")
            # On laisse score, answered_questions et last_evaluation inchangés
            save_data(data)
            flash("Brouillon enregistré.", "success")
        else:
            # Pour l'évaluation finale, vérifier que tous les commentaires sont non vides
            for key, value in responses.items():
                if key.endswith("_comment"):
                    if not value.strip():
                        flash("Tous les commentaires sont obligatoires pour l'évaluation.", "danger")
                        return render_template("score.html", application=application)
            # Calcul du score
            score = 0
            answered_questions = 0
            for key, value in responses.items():
                if key.endswith("_comment"):
                    application["comments"][key] = value  # Enregistrement du commentaire
                elif value in SCORING_MAP:
                    if SCORING_MAP[value] is not None:
                        score += SCORING_MAP[value]
                        answered_questions += 1
                    application["responses"][key] = value  # Enregistrement de la réponse
            application["score"] = score
            application["answered_questions"] = answered_questions
            application["last_evaluation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            application["evaluator_name"] = responses.get("evaluator_name", "")
            save_data(data)
            
        return redirect(url_for("index"))
    
    return render_template("score.html", application=application)


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
    
    return render_template(
        "synthese.html",
        applications=scored_apps,
        total_apps=total_apps,
        avg_score=avg_score,
        apps_above_30=apps_above_30,
        apps_above_60=apps_above_60,
        filter_score=filter_score,
        avg_axis_scores=avg_axis_scores,
        chart_data=chart_data
    )

if __name__ == '__main__':
    app.run(debug=True)
