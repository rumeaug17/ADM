#!/usr/bin/env python3
import json
import re
from pathlib import Path
from typing import Any, cast


def load_json(filename: Path) -> dict[str, Any]:
    with filename.open(encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))


def clean_html(html_text: str | list[str]) -> str:
    """
    Convertit une chaîne HTML en texte brut avec une mise en forme minimale en markdown.
    """
    if isinstance(html_text, list):
        html_text = "\n".join(html_text)
    text = re.sub(r"<br\s*/?>", "\n", html_text, flags=re.IGNORECASE)
    text = re.sub(r"<\s*strong\s*>", "**", text, flags=re.IGNORECASE)
    text = re.sub(r"<\s*/\s*strong\s*>", "**", text, flags=re.IGNORECASE)
    text = re.sub(r"<\s*li\s*>", "- ", text, flags=re.IGNORECASE)
    text = re.sub(r"<\s*/\s*li\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<\s*(ul|ol)\s*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<\s*/\s*(ul|ol)\s*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def option_to_markdown(option: dict[str, Any]) -> str:
    score = option.get("score")
    score_text = str(score) if score is not None else "N/A"
    return f"- {option['value']} (Score: {score_text})"


def generate_markdown(
    questions_config: dict[str, dict[str, dict[str, Any]]],
    info_texts: dict[str, str | list[str]],
) -> str:
    md_lines: list[str] = []
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


def main(project_root: Path) -> None:
    """Régénère la documentation à partir des fichiers statiques du projet."""
    questions_config = load_json(project_root / "static" / "questions.json")
    info_texts = load_json(project_root / "static" / "info_texts.json")

    markdown_text = generate_markdown(questions_config, info_texts)
    with (project_root / "documentation.md").open("w", encoding="utf-8") as f:
        f.write(markdown_text)

    print("Le fichier documentation.md a été généré.")
