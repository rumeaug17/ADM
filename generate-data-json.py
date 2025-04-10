#!/usr/bin/env python3
import json
import random
from datetime import datetime, timedelta

# Nombre d'applications à générer
NUM_APPS = 20

# Listes pour générer des noms d'applications
adjectives = ["Alpha", "Beta", "Gamma", "Delta", "Sigma", "Omega", "Tech", "Info", "Net", "Data", "Service"]
nouns = ["Manager", "App", "System", "Suite", "Portal", "Service", "Platform", "Engine", "Truc", "Machin", "Bidule"]

# Listes pour générer des noms de RDA (utilisateurs responsables)
first_names = ["Laurent", "Bernard", "Eric", "Antoine", "François", "Alice", "Julien", "Sophie", "Nicolas", "Camille", "Guillaume", "Léon", "Caroline", "Michel", "Omar", "Alexandra", "Michèle"]
last_names = ["Labit", "Campan", "Cantona", "Dupond", "Beranger", "Martin", "Durand", "Bernard", "Lefevre", "Petit", "Dupont", "Lhabit", "Ben Hamida", "Leveaux", "Legrand", "Sy"]

# Nouveaux critères : type d'application et type d'hébergement
type_apps = ["Interne", "Editeur", "Open source"]
hostings = ["On prem", "Cloud", "SaaS"]

def random_dicp(prefix: str) -> str:
    """Génère une valeur DICP aléatoire avec le préfixe (ex. 'D2')."""
    return prefix + str(random.randint(1, 4))

def random_date_within_days(days=30) -> str:
    """Génère une date aléatoire dans les 'days' derniers jours au format 'YYYY-MM-DD HH:MM:SS'."""
    now = datetime.now()
    delta = timedelta(
        days=random.randint(0, days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )
    return (now - delta).strftime("%Y-%m-%d %H:%M:%S")

def random_date_only(days=365) -> str:
    """Génère une date au format 'YYYY-MM-DD' dans les 'days' derniers jours."""
    now = datetime.now()
    delta = timedelta(days=random.randint(0, days))
    return (now - delta).strftime("%Y-%m-%d")

def generate_comment(key: str, app_name: str) -> str:
    return f"Commentaire pour {key} de l'application {app_name}"

# Charger la configuration des questions depuis questions.json
with open("static/questions.json", "r", encoding="utf-8") as f:
    questions_config = json.load(f)

# Construire la liste des clés de questions et les options associées (pour générer des réponses)
question_keys = []      # Liste de toutes les clés de questions
question_options = {}   # Mapping : clé -> liste d'options

for category, qs in questions_config.items():
    for q_key, q_def in qs.items():
        question_keys.append(q_key)
        question_options[q_key] = q_def["options"]

applications = []
for i in range(NUM_APPS):
    # Choix aléatoire pour les deux propriétés
    type_app = random.choice(type_apps)
    hosting = random.choice(hostings)
    
    name = f"{random.choice(adjectives)} {random.choice(nouns)} {random.randint(1, 100)}"
    rda = random.choice(first_names) + " " + random.choice(last_names)
    possession = random_date_only(365)
    criticite = str(random.choice([1, 2, 3, 4]))
    disponibilite = random_dicp("D")
    integrite = random_dicp("I")
    confidentialite = random_dicp("C")
    perennite = random_dicp("P")
    
    responses = {}
    comments = {}
    total_score = 0
    answered_questions = 0

    # Parcourir les questions
    for category, qs in questions_config.items():
        for q_key, q_def in qs.items():
            # Filtrer les questions n'étant pas concernées par le type d'application ou d'hébergement est géré
            # au niveau du filtrage dans l'application elle-même. Ici, nous générons une réponse
            # pour chaque question.
            option = random.choice(q_def["options"])
            responses[q_key] = option["value"]
            if option["score"] is not None:
                total_score += option["score"]
                answered_questions += 1
            comments[q_key + "_comment"] = generate_comment(q_key, name)
    
    last_evaluation = random_date_within_days(30)
    evaluator_name = rda

    evaluation = {
        "score": total_score,
        "answered_questions": answered_questions,
        "last_evaluation": last_evaluation,
        "evaluator_name": evaluator_name,
        "responses": responses,
        "comments": comments
    }
    
    app_item = {
        "name": name,
        "rda": rda,
        "possession": possession,
        "type_app": type_app,       # Nouveau champ pour le type d'application
        "hosting": hosting,         # Nouveau champ pour le type d'hébergement
        "criticite": criticite,
        "disponibilite": disponibilite,
        "integrite": integrite,
        "confidentialite": confidentialite,
        "perennite": perennite,
        "score": total_score,
        "answered_questions": answered_questions,
        "last_evaluation": last_evaluation,
        "responses": responses,
        "comments": comments,
        "evaluations": [evaluation]
    }
    applications.append(app_item)

# Sauvegarder les données générées dans applications.json
with open("applications.json", "w", encoding="utf-8") as f:
    json.dump(applications, f, indent=4, ensure_ascii=False)

print(f"{NUM_APPS} applications générées dans applications.json")
