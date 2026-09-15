"""Lecture et écriture atomique du questionnaire et de son aide en ligne (US4.3).

Sur le modèle d'``ADM.config_io`` (US4.2) : ``questions.json`` et
``info_texts.json`` sont réécrits à chaud depuis la page de gestion des
questions, potentiellement vers un emplacement persistant hors du paquet
installé (``ADM_QUESTIONS_PATH``/``ADM_INFO_TEXTS_PATH``, voir
``ADM.persistent_paths``).
"""

import json
from pathlib import Path

from ADM.schemas import Questions


def save_questions(path: Path, questions: Questions) -> None:
    """Réécrit intégralement questions.json avec le questionnaire validé.

    Écriture atomique : fichier temporaire puis remplacement, à l'image de
    ``ADM.config_io.save_display_thresholds``.
    """
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    try:
        temporary_path.write_text(
            json.dumps(questions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        temporary_path.replace(path)
    except OSError as error:
        temporary_path.unlink(missing_ok=True)
        raise ValueError(f"Impossible d'enregistrer le questionnaire {path}.") from error


def _load_info_texts(path: Path) -> dict[str, object]:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"Impossible de lire l'aide en ligne {path}.") from error
    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError as error:
        raise ValueError(f"L'aide en ligne {path} n'est pas un JSON valide.") from error
    if not isinstance(raw, dict):
        raise ValueError("Le fichier d'aide en ligne doit contenir un objet JSON.")
    return raw


def _save_info_texts(path: Path, raw: dict[str, object]) -> None:
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    try:
        temporary_path.write_text(
            json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        temporary_path.replace(path)
    except OSError as error:
        temporary_path.unlink(missing_ok=True)
        raise ValueError(f"Impossible d'enregistrer l'aide en ligne {path}.") from error


def get_question_help_text(path: Path, key: str) -> str:
    """Retourne l'aide en ligne actuellement enregistrée pour ``key``, ou une
    chaîne vide si elle n'existe pas encore (pré-remplissage du formulaire
    d'édition)."""
    raw = _load_info_texts(path)
    value = raw.get(key, "")
    if isinstance(value, list):
        return "".join(str(item) for item in value)
    return str(value) if value else ""


def set_question_help_text(path: Path, key: str, help_text: str) -> None:
    """Met à jour l'aide en ligne d'une question, en préservant les autres clés."""
    raw = _load_info_texts(path)
    raw[key] = help_text
    _save_info_texts(path, raw)


def delete_question_help_text(path: Path, key: str) -> None:
    """Retire l'aide en ligne d'une question supprimée, si elle existait.

    Best effort : une question sans aide (jamais renseignée) ne lève pas
    d'erreur.
    """
    raw = _load_info_texts(path)
    if key in raw:
        del raw[key]
        _save_info_texts(path, raw)
