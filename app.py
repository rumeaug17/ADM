from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import io
import base64

app = Flask(__name__)
DATA_FILE = "applications.json"

# Chargement des données
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def calculate_axis_scores(data):
    categories = {
        "Organisation": ["doc", "team"],
        "Obsolescence": ["tech_obsolete", "mco"],
        "Qualité et Développement": ["etat_art", "code_source"],
        "Sécurité et Conformité": ["securite", "vulnerabilites"],
        "Exploitation et Performance": ["incidents", "performances"],
        "Fonctionnel": ["besoins_metier", "evolutivite"]
    }
    
    axis_scores = {key: [] for key in categories}
    scoring_map = {"Oui total": 0, "Non": 0, "Partiel": 1, "Partiellement": 1, "Insuffisant": 2, "Majoritairement": 2, "Non applicable": None, "Totalement": 3, "Non total": 3}
    
    for app in data:
        if "responses" in app:
            for category, questions in categories.items():
                scores = [scoring_map[app["responses"].get(q, "Non applicable")] for q in questions if app["responses"].get(q, "Non applicable") in scoring_map and scoring_map[app["responses"].get(q, "Non applicable")] is not None]
                if scores:
                    axis_scores[category].append(sum(scores) / len(scores))
    
    avg_axis_scores = {key: round(sum(values) / len(values), 2) if values else 0 for key, values in axis_scores.items()}
    return avg_axis_scores
    
def generate_chart(avg_axis_scores):
    categories = list(avg_axis_scores.keys())
    scores = list(avg_axis_scores.values())
    
    plt.figure(figsize=(8, 5))
    plt.barh(categories, scores, color=['blue', 'green', 'orange', 'red', 'purple', 'cyan'])
    plt.xlabel("Note Moyenne")
    plt.xlim(-1, 3)
    plt.axvline(x=0, color='black', linestyle='--')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    chart_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    return chart_data

def generate_radar_chart(avg_axis_scores):
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
    return chart_data

@app.route('/')
def index():
    applications = load_data()
    for app in applications:
        if "score" in app and app["score"] is not None and "answered_questions" in app and app["answered_questions"] > 0:
            max_score = app["answered_questions"] * 3  # Nombre de questions renseignées * score max par question
            percentage = round((app["score"] / max_score) * 100, 2)
            app["max_score"] = max_score
            app["percentage"] = percentage
        else:
            app["max_score"] = None
            app["percentage"] = None
            
    return render_template("index.html", applications=applications)

@app.route('/add', methods=['GET', 'POST'])
def add_application():
    if request.method == 'POST':
        data = load_data()
        new_app = {
            "name": request.form["name"],
            "rda": request.form["rda"],
            "type" : request.form["type"],
            "disponibilite": request.form["disponibilite"],
            "integrite": request.form["integrite"],
            "confidentialite": request.form["confidentialite"],
            "perennite": request.form["perennite"],
            "score": None,
            "answered_questions": 0,
            "last_evaluation": None,
            "responses": {}  # Stocker les réponses individuelles
        }
        data.append(new_app)
        save_data(data)
        return redirect(url_for("index"))
    return render_template("add.html")
    
@app.route('/edit/<name>', methods=['GET', 'POST'])
def edit_application(name):
    data = load_data()
    # Recherche de l'application par son nom
    app_to_edit = next((app for app in data if app["name"] == name), None)
    if not app_to_edit:
        return "Application non trouvée", 404

    if request.method == "POST":
        # Mettre à jour les champs de l'application
        app_to_edit["name"] = request.form["name"]
        app_to_edit["rda"] = request.form["rda"]
        app_to_edit["type"] = request.form["type"]
        app_to_edit["disponibilite"] = request.form["disponibilite"]
        app_to_edit["integrite"] = request.form["integrite"]
        app_to_edit["confidentialite"] = request.form["confidentialite"]
        app_to_edit["perennite"] = request.form["perennite"]
        save_data(data)
        return redirect(url_for("index"))
    
    return render_template("edit.html", application=app_to_edit)

@app.route('/delete/<name>', methods=['POST'])
def delete_application(name):
    data = load_data()
    data = [app for app in data if app["name"] != name]
    save_data(data)
    return jsonify({"success": True})

@app.route('/score/<name>', methods=['GET', 'POST'])
def score_application(name):
    data = load_data()
    application = next((app for app in data if app["name"] == name), None)
    
    if application is None:
        return "Application non trouvée", 404

    if "comments" not in application:
        application["comments"] = {}  # Initialise le champ des commentaires si absent
        
    if request.method == 'POST':
        responses = request.form.to_dict()
        score = 0
        answered_questions = 0
        scoring_map = {"Oui total": 0, "Non": 0, "Partiel": 1, "Partiellement": 1, "Insuffisant": 2, "Majoritairement": 2, "Non applicable": None, "Totalement": 3, "Non total": 3}
        
        for key, value in responses.items():
            if key.endswith("_comment"):
                application["comments"][key] = value  # Enregistrer le commentaire
            elif value in scoring_map:
                if scoring_map[value] is not None:
                    score += scoring_map[value]
                    answered_questions += 1
                application["responses"][key] = value  # Enregistrer chaque réponse
        
        application["score"] = score
        application["answered_questions"] = answered_questions
        application["last_evaluation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        application["evaluator_name"] = responses["evaluator_name"]
        save_data(data)
        return redirect(url_for("index"))
    
    return render_template("score.html", application=application)

@app.route('/synthese')
def synthese():
    data = load_data()
    filter_score = request.args.get("filter_score", "above_30")
    
    for app in data:
        if "score" in app and app["score"] is not None and "answered_questions" in app and app["answered_questions"] > 0:
            max_score = app["answered_questions"] * 3  # Nombre de questions renseignées * score max par question
            percentage = round((app["score"] / max_score) * 100, 2)
            app["max_score"] = max_score
            app["percentage"] = percentage
        else:
            app["max_score"] = None
            app["percentage"] = None
            
    total_apps = len(data)
    scored_apps = [app for app in data if app["score"] is not None  and app["answered_questions"] > 0]

     # Filtrage des applications en fonction du score
    if filter_score == "above_30":
        scored_apps = [app for app in data if app["percentage"] > 30]
    elif filter_score == "above_60":
        scored_apps = [app for app in data if app["percentage"] > 60]

    avg_score = round(sum(app["score"] for app in data) / len(data), 2) if data else 0
    apps_above_30 = len([app for app in data if app["percentage"] > 30])
    apps_above_60 = len([app for app in data if app["percentage"] > 60])
    avg_axis_scores = calculate_axis_scores(data)
    # chart_data = generate_chart(avg_axis_scores)
    chart_data = generate_radar_chart(avg_axis_scores)
    
    
    # Tri décroissant par score
    scored_apps.sort(key=lambda app: app["score"], reverse=True)
    
    return render_template("synthese.html", applications=scored_apps, total_apps=total_apps, avg_score=avg_score, apps_above_30=apps_above_30, apps_above_60=apps_above_60, filter_score=filter_score, avg_axis_scores=avg_axis_scores, chart_data=chart_data)

if __name__ == '__main__':
    app.run(debug=True)
