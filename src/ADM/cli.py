"""Lancement local de l'application web ADM."""

import argparse
from collections.abc import Sequence

from ADM.app import create_app


def run_server(*, debug: bool = False) -> None:
    """Démarre le serveur de développement Flask."""
    create_app().run(debug=debug)


def parse_debug_option(arguments: Sequence[str] | None = None) -> bool:
    """Retourne le mode de débogage demandé sur la ligne de commande."""
    parser = argparse.ArgumentParser(description="Démarre l'application web ADM.")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="active le mode de débogage du serveur Flask",
    )
    return bool(parser.parse_args(arguments).debug)
