#!/usr/bin/env python3
import json
import os
import random
import sys
from datetime import datetime, timedelta

# Importer les fonctions du module database pour initialiser la base et obtenir une session
from database import Application, get_session_factory, init_db

# Listes pour générer des noms d'applications
adjectives = [
    "Alpha",
    "Beta",
    "Gamma",
    "Delta",
    "Sigma",
    "Omega",
    "Tech",
    "Info",
    "Net",
    "Data",
    "Service",
]
nouns = [
    "Manager",
    "App",
    "System",
    "Suite",
    "Portal",
    "Service",
    "Platform",
    "Engine",
    "Truc",
    "Machin",
    "Bidule",
]

# Listes pour générer des noms de RDA (responsables)
first_names = [
    "Laurent",
    "Bernard",
    "Eric",
    "Antoine",
    "François",
    "Alice",
    "Julien",
    "Sophie",
    "Nicolas",
    "Camille",
    "Guillaume",
    "Léon",
    "Caroline",
    "Michel",
    "Omar",
    "Alexandra",
    "Michèle",
]
last_names = [
    "Labit",
    "Campan",
    "Cantona",
    "Dupond",
    "Beranger",
    "Martin",
    "Durand",
    "Bernard",
    "Lefevre",
    "Petit",
    "Dupont",
    "Lhabit",
    "Ben Hamida",
    "Leveaux",
    "Legrand",
    "Sy",
]

# Nouveaux critères pour la séparation
type_apps = ["Interne", "Editeur", "Open source"]
hostings = ["On prem", "Cloud", "SaaS"]


def random_dicp(prefix: str) -> str:
    """Génère aléatoirement une valeur DICP, par exemple 'D2'."""
    return prefix + str(random.randint(1, 4))


def random_date_within_days(days=30) -> str:
    """Génère une date-heure au format 'YYYY-MM-DD HH:MM:SS' dans les derniers 'days' jours."""
    now = datetime.now()
    delta = timedelta(
        days=random.randint(0, days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return (now - delta).strftime("%Y-%m-%d %H:%M:%S")


def random_date_only(days=365) -> str:
    """Génère une date au format 'YYYY-MM-DD' dans les derniers 'days' jours."""
    now = datetime.now()
    delta = timedelta(days=random.randint(0, days))
    return (now - delta).strftime("%Y-%m-%d")


def generate_comment(key: str, app_name: str) -> str:
    """Génère un commentaire fictif pour une question donnée."""
    return f"Commentaire pour {key} de l'application {app_name}"


def generate_applications(num_apps, questions_config):
    """
    Génère une liste d'applications de test (objets Application) avec des réponses et commentaires générés pour chaque question.
    """
    applications = []
    for _ in range(num_apps):
        # Choix aléatoire pour type d'application et hébergement
        type_app = random.choice(type_apps)
        hosting = random.choice(hostings)

        # Génération du nom de l'application et du RDA
        name = f"{random.choice(adjectives)} {random.choice(nouns)} {random.randint(1, 100)}"
        rda = random.choice(first_names) + " " + random.choice(last_names)
        possession = datetime.strptime(random_date_only(365), "%Y-%m-%d").date()
        criticite = random.choice([1, 2, 3, 4])
        disponibilite = random_dicp("D")
        integrite = random_dicp("I")
        confidentialite = random_dicp("C")
        perennite = random_dicp("P")

        # Génération des réponses et commentaires en parcourant les questions
        responses = {}
        comments = {}
        for qs in questions_config.values():
            for q_key, q_def in qs.items():
                # Si des options existent, choisir une option aléatoirement
                opts = q_def.get("options", [])
                if opts:
                    option = random.choice(opts)
                    responses[q_key] = option.get("value")
                else:
                    responses[q_key] = ""
                comments[q_key + "_comment"] = generate_comment(q_key, name)

        # Création de l'application
        app_obj = Application(
            name=name,
            rda=rda,
            possession=possession,
            type_app=type_app,
            hosting=hosting,
            criticite=criticite,
            disponibilite=disponibilite,
            integrite=integrite,
            confidentialite=confidentialite,
            perennite=perennite,
            score=None,
            answered_questions=0,
            last_evaluation=None,
            responses=responses,
            comments=comments,
        )
        applications.append(app_obj)
    return applications


def main(num_apps=5):
    connection_url = os.environ.get("ADM_DATABASE_URL")
    if not connection_url:
        raise RuntimeError("ADM_DATABASE_URL est obligatoire.")

    # Charger la configuration des questions (supposé dans le dossier static, ajustez le chemin si nécessaire)
    questions_file = os.path.join(os.path.dirname(__file__), "static", "questions.json")
    with open(questions_file, encoding="utf-8") as f:
        questions_config = json.load(f)

    # Initialiser la base (création des tables si nécessaire)
    engine = init_db(connection_url)
    Session = get_session_factory(engine)
    session_db = Session()

    try:
        apps = generate_applications(num_apps, questions_config)
        session_db.add_all(apps)
        session_db.commit()
        print(f"{num_apps} applications de test ont été insérées dans la base de données.")
    except Exception as e:
        session_db.rollback()
        print(f"Erreur lors de l'insertion : {e}")
    finally:
        session_db.close()


if __name__ == "__main__":
    # Le nombre d'applications est facultatif ; la connexion vient exclusivement
    # de la variable d'environnement ADM_DATABASE_URL.
    if len(sys.argv) >= 2:
        try:
            num_apps = int(sys.argv[1])
        except ValueError:
            print("Le second argument doit être un entier représentant le nombre d'applications.")
            sys.exit(1)
    else:
        num_apps = 5

    main(num_apps)
