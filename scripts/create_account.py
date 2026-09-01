#!/usr/bin/env python3
"""Point d'entrée de création d'un compte local (bootstrap ou administration, US6.1)."""

import sys
from pathlib import Path


def main() -> None:
    """Exécute la commande avec le paquet provenant du checkout courant."""
    project_source = Path(__file__).resolve().parents[1] / "src"
    sys.path.insert(0, str(project_source))

    from ADM.cli import create_account_command

    create_account_command()


if __name__ == "__main__":
    main()
