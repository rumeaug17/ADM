from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os

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
            "disponibilite": request.form["disponibilite"],
            "integrite": request.form["integrite"],
            "confidentialite": request.form["confidentialite"],
            "perennite": request.form["perennite"],
            "score": None,
            "answered_questions": 0,
            "last_evaluation": None
        }
        data.append(new_app)
        save_data(data)
        return redirect(url_for("index"))
    return render_template("add.html")

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
    
    if request.method == 'POST':
        responses = request.form.to_dict()
        score = 0
        answered_questions = 0
        scoring_map = {"Oui total": 0, "Non": 0, "Partiel": 1, "Partiellement": 1, "Insuffisant": 2, "Majoritairement": 2, "Non applicable": None, "Totalement": 3}
        
        for key, value in responses.items():
            if value in scoring_map and scoring_map[value] is not None:
                score += scoring_map[value]
                answered_questions += 1
        
        application["score"] = score
        application["answered_questions"] = answered_questions
        application["last_evaluation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_data(data)
        return redirect(url_for("index"))
    
    return render_template("score.html", application=application)

@app.route('/synthese')
def synthese():
    data = load_data()
    total_apps = len(data)
    scored_apps = [app for app in data if app["score"] is not None  and app["answered_questions"] > 0]
    avg_score = round(sum(app["score"] for app in scored_apps) / len(scored_apps), 2) if scored_apps else 0
    apps_above_30 = len([app for app in scored_apps if app["percentage"] > 30])
    apps_above_60 = len([app for app in scored_apps if app["percentage"] > 60])
    
    return render_template("synthese.html", applications=data, total_apps=total_apps, avg_score=avg_score, apps_above_30=apps_above_30, apps_above_60=apps_above_60)

if __name__ == '__main__':
    app.run(debug=True)
