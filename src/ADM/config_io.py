"""Lecture et écriture atomique de la configuration non sensible (US4.2)."""

import json
from pathlib import Path

from ADM.schemas import DisplayThresholds, display_thresholds_to_dict


def save_display_thresholds(config_path: Path, thresholds: DisplayThresholds) -> None:
    """Réécrit uniquement la clé display_thresholds de config.json.

    Préserve db_backend et json_connection_url tels quels. Écriture atomique :
    fichier temporaire puis remplacement, à l'image de
    ADM.database_json._save_records.
    """
    try:
        raw_text = config_path.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"Impossible de lire la configuration {config_path}.") from error
    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError as error:
        raise ValueError(f"La configuration {config_path} n'est pas un JSON valide.") from error
    if not isinstance(raw, dict):
        raise ValueError("Le fichier de configuration doit contenir un objet JSON.")

    raw["display_thresholds"] = display_thresholds_to_dict(thresholds)

    temporary_path = config_path.with_suffix(f"{config_path.suffix}.tmp")
    try:
        temporary_path.write_text(
            json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        temporary_path.replace(config_path)
    except OSError as error:
        temporary_path.unlink(missing_ok=True)
        raise ValueError(f"Impossible d'enregistrer la configuration {config_path}.") from error
