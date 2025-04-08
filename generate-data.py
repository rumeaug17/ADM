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

# Types d'application
types = ["Interne", "Interne cloud", "Editeur onPrem", "Editeur cloud", "SaaS"]

def random_dicp(prefix: str) -> str:
    """
    Génère aléatoirement un critère DICP en ajoutant un chiffre entre 1 et 4 au préfixe.
    Exemple : random_dicp("D") -> "D2"
    """
    return prefix + str(random.randint(1, 4))

def random_date_within_days(days=30) -> str:
    """
    Génère une date-heure aléatoire dans les 'days' derniers jours, au format "YYYY-MM-DD HH:MM:SS".
    """
    now = datetime.now()
    delta = timedelta(
        days=random.randint(0, days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )
    return (now - delta).strftime("%Y-%m-%d %H:%M:%S")

def random_date_only(days=365) -> str:
    """
    Génère une date aléatoire dans les 'days' derniers jours, au format "YYYY-MM-DD".
    """
    now = datetime.now()
    delta = timedelta(days=random.randint(0, days))
    return (now - delta).strftime("%Y-%m-%d")

def generate_comment(key: str, app_name: str) -> str:
    """
    Génère un commentaire fictif pour une question donnée et le nom de l'application.
    """
    return f"Commentaire pour {key} de l'application {app_name}"

# Charger la configuration des questions depuis questions.json
with open("static/questions.json", "r", encoding="utf-8") as f:
    questions_config = json.load(f)

# Génération des applications de test
applications = []
for i in range(NUM_APPS):
    app_type = random.choice(types)
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

    # Parcourir toutes les catégories de questions et sélectionner celles applicables
    for category, qs in questions_config.items():
        for q_key, q_def in qs.items():
            # Si la question possède un attribut "app_types", on la conserve uniquement
            # si le type de l'application est dans la liste.
            if "app_types" in q_def and app_type not in q_def["app_types"]:
                continue
            # Choisir aléatoirement une option parmi celles disponibles
            option = random.choice(q_def["options"])
            responses[q_key] = option["value"]
            if option["score"] is not None:
                total_score += option["score"]
                answered_questions += 1
            # Générer un commentaire pour cette question
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
        "type": app_type,
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
