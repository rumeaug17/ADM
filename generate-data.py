#!/usr/bin/env python3
import json
import random
from datetime import datetime, timedelta

# Nombre d'applications à générer (environ 20)
NUM_APPS = 20

# Listes pour générer des noms d'applications
adjectives = ["Alpha", "Beta", "Gamma", "Delta", "Sigma", "Omega", "Tech", "Info", "Net", "Data", "Service"]
nouns = ["Manager", "App", "System", "Suite", "Portal", "Service", "Platform", "Engine", "Truc", "Machin", "Bidule"]

# Listes pour générer des noms de RDA (utilisateurs responsables)
first_names = ["Laurent", "Bernard", "Eric", "Antoine", "François", "Alice", "Julien", "Sophie", "Nicolas", "Camille", "Guillaume", "Léon", "Caroline", "Michel", "Omar", "Alexandra", "Michèle"]
last_names = ["Labit", "Campan", "Cantona", "Dupond", "Beranger", "Martin", "Durand", "Bernard", "Lefevre", "Petit", "Dupont", "Lhabit", "Ben Hamida", "Leveaux", "Legrand", "Sy"]

# Types d'application
types = ["Interne", "Interne cloud", "Editeur onPrem", "Editeur cloud", "SaaS"]

# Fonction pour générer un critère DICP aléatoire (Disponibilité, Intégrité, Confidentialité, Pérennité)
def random_dicp(prefix: str) -> str:
    return prefix + str(random.randint(1, 4))

def random_date_within_days(days=30) -> str:
    """Génère une date aléatoire dans les 'days' derniers jours."""
    now = datetime.now()
    delta = timedelta(
        days=random.randint(0, days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )
    return (now - delta).strftime("%Y-%m-%d %H:%M:%S")

def generate_comment(key: str, app_name: str) -> str:
    return f"Commentaire pour {key} de l'application {app_name}"

# Charger la configuration des questions depuis questions.json
with open("questions.json", "r", encoding="utf-8") as f:
    questions_config = json.load(f)

# Construire la liste des clés de questions et une table de correspondance pour les scores
question_keys = []      # Liste de toutes les clés de questions
question_options = {}   # Mapping : clé -> liste des options (chaque option est un dict avec 'value' et 'score')
scoring_map = {}        # Mapping global des valeurs de réponses aux scores

for category, qs in questions_config.items():
    for q_key, q_def in qs.items():
        question_keys.append(q_key)
        question_options[q_key] = q_def["options"]
        for option in q_def["_
