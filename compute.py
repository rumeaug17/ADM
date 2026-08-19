"""Compatibilité avec les anciens imports des calculs métier.

Le code métier est désormais maintenu dans le paquet installé sous ``src/``.
"""

from ADM.scoring import (
    compute_categories,
    compute_scoring_map,
    filter_questions_by_type,
)

__all__ = ["compute_categories", "compute_scoring_map", "filter_questions_by_type"]
