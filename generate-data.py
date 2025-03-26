#!/usr/bin/env python3
import json
import random
from datetime import datetime, timedelta

def random_date():
    """Génère une date aléatoire dans le mois précédent."""
    now = datetime.now()
    delta = timedelta(
        days=random.randint(0, 30),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    date = now - delta
    return date.strftime("%Y-%m-%d %H:%M:%S")

# Quelques options pour remplir les champs
types = ["Web", "Mobile", "Desktop", "Service"]
criticite_options = ["1", "2", "3", "4"]
rating_prefixes = {
    "disponibilite": "D",
    "integrite": "I",
    "confidentialite": "C",
    "perennite": "P"
}
rating_levels = ["1", "2", "3", "4"]

applications = []
# Générer par exemple 20 applications
for i in range(20):
    # On décide aléatoirement si l'application a déjà été évaluée ou non
    evaluated = random.choice([True, False])
    app = {
        "name": f"Application {i+1}",
        "rda": f"RDA{random.randint(1,5)}",
        "type": random.choice(types),
        "criticite": random.choice(criticite_options),
        "disponibilite": rating_prefixes["disponibilite"] + random.choice(rating_levels),
        "integrite": rating_prefixes["integrite"] + random.choice(rating_levels),
        "confidentialite": rating_prefixes["confidentialite"] + random.choice(rating_levels),
        "perennite": rating_prefixes["perennite"] + random.choice(rating_levels),
        "score": None,
        "answered_questions": 0,
        "last_evaluation": None,
        "responses": {},
        "evaluator_name": ""
    }
    if evaluated:
        # Pour les applications évaluées, on définit un score et un nombre de questions répondues
        app["answered_questions"] = random.randint(5, 10)
        max_score = app["answered_questions"] * 3  # score maximum possible
        app["score"] = random.randint(0, max_score)
        app["last_evaluation"] = random_date()
        app["evaluator_name"] = f"Evaluateur {random.randint(1,5)}"
        # Vous pouvez également remplir app["responses"] avec des réponses fictives si besoin

    applications.append(app)

# Sauvegarde dans le fichier JSON (indenté pour plus de lisibilité)
with open("applications.json", "w") as f:
    json.dump(applications, f, indent=4)

print("Fichier applications.json généré avec succès.")
