#!/usr/bin/env python3
import json
import re

def load_json(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def clean_html(html_text):
    """
    Convertit une chaîne HTML en texte brut avec une mise en forme minimale en markdown.
    Cette fonction fait des remplacements simples pour <br>, <strong>, <ul>/<li>...
    """
    # Si le texte est une liste, on la joint
    if isinstance(html_text, list):
        html_text = "\n".join(html_text)
    # Remplacer <br> par un saut de ligne
    text = re.sub(r'<br\s*/?>', '\n', html_text, flags=re.IGNORECASE)
    # Remplacer <strong> et </strong> par des astérisques pour le gras
    text = re.sub(r'<\s*strong\s*>', '**', text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*/\s*strong\s*>', '**', text, flags=re.IGNORECASE)
    # Convertir les listes HTML : <li> en "- " et supprimer les tags ul/ol
    text = re.sub(r'<\s*li\s*>', '- ', text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*/\s*li\s*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*(ul|ol)\s*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*/\s*(ul|ol)\s*>', '', text, flags=re.IGNORECASE)
    # Supprimer les autres balises HTML restantes
    text = re.sub(r'<[^>]+>', '', text)
    # Nettoyage des espaces superflus
    return text.strip()

def option_to_markdown(option):
    score = option.get("score")
    score_text = str(score) if score is not None else "N/A"
    return f"- {option['value']} (Score: {score_text})"

def generate_markdown(questions_config, info_texts):
    md_lines = []
    md_lines.append("# Documentation des Questions\n")
    # Parcourir les catégories dans questions.json
    for category, qs in questions_config.items():
        md_lines.append(f"## Catégorie : {category}\n")
        # Pour chaque question dans cette catégorie
        for q_key, q_def in qs.items():
            label = q_def.get("label", q_key)
            q_type = q_def.get("type", "inconnu")
            options = q_def.get("options", [])
            app_types = q_def.get("app_types", None)
            
            md_lines.append(f"### Question : {label}\n")
            md_lines.append(f"**Clé :** `{q_key}`  ")
            md_lines.append(f"**Type :** {q_type}\n")
            if app_types:
                md_lines.append(f"**Applicable pour :** {', '.join(app_types)}\n")
            md_lines.append("**Options :**\n")
            for option in options:
                md_lines.append(option_to_markdown(option))
            md_lines.append("")  # ligne vide

            # Rechercher une aide associée dans info_texts en se basant sur la clé
            help_text_raw = info_texts.get(q_key)
            if help_text_raw:
                help_text = clean_html(help_text_raw)
                md_lines.append("**Aide :**\n")
                md_lines.append(f"> {help_text}\n")
            else:
                md_lines.append("**Aide :** _Aucune aide disponible._\n")
            md_lines.append("---\n")

    return "\n".join(md_lines)

if __name__ == "__main__":
    # Charger la configuration des questions et l'aide associée
    questions_config = load_json("static/questions.json")
    info_texts = load_json("static/info_texts.json")
    
    # Générer le contenu Markdown
    markdown_text = generate_markdown(questions_config, info_texts)
    
    # Sauvegarder dans documentation.md
    with open("documentation.md", "w", encoding="utf-8") as f:
        f.write(markdown_text)
    
    print("Le fichier documentation.md a été généré.")
