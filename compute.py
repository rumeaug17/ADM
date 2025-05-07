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

# --- Fonctions utilitaires ---

def filter_questions_by_type(questions: dict, type_app: str, hosting: str) -> dict:
    """
    Filtre les questions en s'appuyant sur deux critères indépendants :
      - Si une question contient la clé "app_types", le type_app de l'application doit être 
        dans la liste (après normalisation).
      - Si une question contient la clé "hosting_types", le hosting de l'application doit être 
        dans la liste (après normalisation).
    Si une question ne possède pas l'une ou l'autre de ces clés, le critère correspondant n'est pas appliqué.
    Seules les questions satisfaisant tous les filtres spécifiés seront retournées.
    """
    filtered_questions = {}
    # Normaliser les valeurs de l'application
    type_app_norm = type_app.strip().lower()
    hosting_norm = hosting.strip().lower()
    for category, qs in questions.items():
        filtered_qs = {}
        for key, q_def in qs.items():
            include = True
            # Filtrage sur le type d'application
            if "app_types" in q_def:
                allowed_app = [val.strip().lower() for val in q_def["app_types"]]
                if type_app_norm not in allowed_app:
                    include = False
            # Filtrage sur le type d'hébergement
            if "hosting_types" in q_def:
                allowed_hosting = [val.strip().lower() for val in q_def["hosting_types"]]
                if hosting_norm not in allowed_hosting:
                    include = False
            if include:
                filtered_qs[key] = q_def
        filtered_questions[category] = filtered_qs
    return filtered_questions

# --- Calcul des métriques et graphiques ---

def calculate_risk(app_item: Dict[str, Any]) -> Optional[float]:
    """
    Calcule le risque d'une application à partir de son score et de ses indicateurs DICP.
    La formule est : risque = score * (produit des indicateurs numériques / criticité).
    """
    score = app_item.get("score")
    if score is None:
        return None
    try:
        score = float(score)
    except Exception:
        return None
    try:
        d = int(''.join(filter(str.isdigit, app_item.get("disponibilite", "0"))))
        i = int(''.join(filter(str.isdigit, app_item.get("integrite", "0"))))
        c = int(''.join(filter(str.isdigit, app_item.get("confidentialite", "0"))))
        p = int(''.join(filter(str.isdigit, app_item.get("perennite", "0"))))
    except Exception:
        return None
    try:
        criticite = int(app_item.get("criticite", "0"))
    except Exception:
        criticite = 0
    if criticite == 0:
        return None
    # moyenne des facteurs dicp
    moy_dicp = (d * i * c * p) / 4
    # réduction de 50% du risque avec l'augmentation du nombre de questions
    facteur = (moy_dicp / criticite) / 2
    return score * facteur

def update_app_metrics(app_item: Dict[str, Any]) -> None:
    """
    Met à jour 'max_score', 'percentage' et 'risque' pour une application.
    Le score maximum est calculé en supposant 3 points par question répondue.
    """
    if app_item.get("score") is not None and app_item.get("answered_questions", 0) > 0:
        max_score = app_item["answered_questions"] * 3
        percentage = round((app_item["score"] / max_score) * 100, 2)
        app_item["max_score"] = max_score
        app_item["percentage"] = percentage
        app_item["risque"] = calculate_risk(app_item)
    else:
        app_item["max_score"] = None
        app_item["percentage"] = None
        app_item["risque"] = None

def update_all_metrics(apps: List[Dict[str, Any]]) -> None:
    """Met à jour les métriques pour toutes les applications."""
    for app_item in apps:
        update_app_metrics(app_item)


