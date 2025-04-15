# compute.py
# --- Calcul des constantes dynamiques ---

def compute_categories(questions: dict) -> dict:
    """
    Extrait pour chaque catégorie la liste des clés des questions,
    en ignorant les clés commençant par un underscore.
    """
    categories = {}
    for category, questions_dict in questions.items():
        q_keys = [key for key in questions_dict.keys() if not key.startswith("_")]
        categories[category] = q_keys
    return categories

def compute_scoring_map(questions: dict) -> dict:
    """
    Construit un dictionnaire qui associe chaque option de réponse à sa note,
    en parcourant toutes les options définies dans questions.json.
    """
    scoring_map = {}
    for _, questions_dict in questions.items():
        for q_key, q_def in questions_dict.items():
            if isinstance(q_def, dict) and "options" in q_def:
                for option in q_def["options"]:
                    if isinstance(option, dict):
                        value = option.get("value")
                        score = option.get("score")
                        scoring_map[value] = score
    return scoring_map
