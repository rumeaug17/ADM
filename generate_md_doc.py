#!/usr/bin/env python3
import json
import re

def load_json(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def clean_html(html_text):
    """
    Convertit une chaîne HTML en texte brut avec une mise en forme minimale en markdown.
    """
    if isinstance(html_text, list):
        html_text = "\n".join(html_text)
    text = re.sub(r'<br\s*/?>', '\n', html_text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*strong\s*>', '**', text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*/\s*strong\s*>', '**', text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*li\s*>', '- ', text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*/\s*li\s*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*(ul|ol)\s*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<\s*/\s*(ul|ol)\s*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def option_to_markdown(option):
    score = option.get("score")
    score_text = str(score) if score is not None else "N/A"
    return f"- {option['value']} (Score: {score_text})"

def generate_markdown(questions_config, info_texts):
    md_lines = []
    md_lines.append("# Documentation des Questions\n")
    for category, qs in questions_config.items():
        md_lines.append(f"## Catégorie : {category}\n")
        for q_key, q_def in qs.items():
            label = q_def.get("label", q_key)
            q_type = q_def.get("type", "inconnu")
            options = q_def.get("options", [])
            
            md_lines.append(f"### Question : {label}\n")
            md_lines.append(f"**Clé :** `{q_key}`  ")
            md_lines.append(f"**Type :** {q_type}\n")
            
            # Afficher le filtre sur le type d'application si présent
            if "app_types" in q_def:
                allowed_app = ", ".join(q_def["app_types"])
                md_lines.append(f"**Applicable pour le type d'application :** {allowed_app}\n")
            # Afficher le filtre sur le type d'hébergement si présent
            if "hosting_types" in q_def:
                allowed_hosting = ", ".join(q_def["hosting_types"])
                md_lines.append(f"**Applicable pour le type d'hébergement :** {allowed_hosting}\n")
                
            md_lines.append("**Options :**\n")
            for option in options:
                md_lines.append(option_to_markdown(option))
            md_lines.append("")  # ligne vide
            
            # Recherche de l'aide associée
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
    questions_config = load_json("static/questions.json")
    info_texts = load_json("static/info_texts.json")
    
    markdown_text = generate_markdown(questions_config, info_texts)
    with open("documentation.md", "w", encoding="utf-8") as f:
        f.write(markdown_text)
    
    print("Le fichier documentation.md a été généré.")
