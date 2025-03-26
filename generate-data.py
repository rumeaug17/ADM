#!/usr/bin/env python3
import json
import random
from datetime import datetime, timedelta

# Nombre d'applications à générer (environ 20)
NUM_APPS = 20

# Listes pour générer des noms d'applications
adjectives = ["Alpha", "Beta", "Gamma", "Delta", "Sigma", "Omega", "Tech", "Info", "Net", "Data"]
nouns = ["Manager", "App", "System", "Suite", "Portal", "Service", "Platform", "Engine"]

# Listes pour générer des noms de RDA (utilisateurs responsables)
first_names = ["Laurent", "Bernard", "Eric", "Antoine", "François", "Alice", "Julien", "Sophie", "Nicolas", "Camille"]
last_names = ["Labit", "Campan", "Cantona", "Dupond", "Beranger", "Martin", "Durand", "Bernard", "Lefevre", "Petit"]

# Types d'application
types = ["Interne", "Externe", "SaaS", "Editeur", "Service", "Cloud"]

# Fonction pour générer un critère DICP aléatoire à partir d'un préfixe (ex: "D", "I", "C", "P")
def random_dicp(prefix: str) -> str:
    return prefix + str(random.randint(1, 4))

# Liste des clés pour les réponses et les commentaires associés
response_keys = [
    "doc", "team", "roadmap", "tech_obsolete", "mco", "support",
    "etat_art", "respect", "code_source", "tests", "securite",
    "vulnerabilites", "surveillance", "incidents", "performances",
    "scalable", "besoins_metier", "recouvrement", "evolutivite",
    "fonctions", "couplage", "decommissionnement"
]

# Options possibles pour les réponses
response_options = [
    "Oui total", "Non", "Partiel", "Partiellement", "Insuffisant",
    "Majoritairement", "Non applicable", "Totalement", "Non total"
]

# Table de correspondance pour calculer le score
SCORING_MAP = {
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

def generate_comment(key: str, app_name: str) -> str:
    return f"Commentaire pour {key} de l'application {app_name}"

def random_date_within_days(days=30) -> str:
    """Génère une date aléatoire dans les 'days' derniers jours."""
    now = datetime.now()
    delta = timedelta(
        days=random.randint(0, days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )
    date = now - delta
    return date.strftime("%Y-%m-%d %H:%M:%S")

applications = []
for _ in range(NUM_APPS):
    # Générer un nom d'application aléatoire
    app_name = f"{random.choice(adjectives)} {random.choice(nouns)} {random.randint(1, 99)}"
    # Générer un nom de RDA aléatoire
    rda_name = f"{random.choice(first_names)} {random.choice(last_names)}"
    
    # Choix aléatoire du type d'application
    app_type = random.choice(types)
    
    # Générer les critères DICP aléatoirement
    disponibilite = random_dicp("D")
    integrite = random_dicp("I")
    confidentialite = random_dicp("C")
    perennite = random_dicp("P")
    
    # Criticité aléatoire parmi "1", "2", "3", "4"
    criticite = str(random.randint(1, 4))
    
    # Décider aléatoirement si l'application est évaluée
    evaluated = random.choice([True, False])
    
    # Générer le dictionnaire des réponses
    responses = { key: random.choice(response_options) for key in response_keys }
    # Calculer le score à partir des réponses
    score = 0
    answered_questions = 0
    for resp in responses.values():
        value = SCORING_MAP.get(resp)
        if value is not None:
            score += value
            answered_questions += 1

    # Si non évaluée, on force les valeurs correspondantes
    if not evaluated:
        score = None
        answered_questions = 0
        last_evaluation = None
    else:
        last_evaluation = random_date_within_days(30)
    
    # Générer le dictionnaire des commentaires
    comments = { f"{key}_comment": generate_comment(key, app_name) for key in response_keys }
    
    # Créer le dictionnaire complet pour l'application
    app = {
        "name": app_name,
        "type": app_type,
        "rda": rda_name,
        "disponibilite": disponibilite,
        "integrite": integrite,
        "confidentialite": confidentialite,
        "perennite": perennite,
        "score": score,
        "answered_questions": answered_questions,
        "last_evaluation": last_evaluation,
        "criticite": criticite,
        "evaluator_name": rda_name,
        "responses": responses,
        "comments": comments
    }
    
    applications.append(app)

# Sauvegarder dans le fichier applications.json avec encodage UTF-8
with open("applications.json", "w", encoding="utf-8") as f:
    json.dump(applications, f, indent=4, ensure_ascii=False)

print("Fichier applications.json généré avec succès avec environ 20 applications et un score calculé.")
