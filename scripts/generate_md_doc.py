#!/usr/bin/env python3
"""Point d'entrée de génération de la documentation fonctionnelle."""

from pathlib import Path

from ADM.documentation import main

PROJECT_ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    main(PROJECT_ROOT)
