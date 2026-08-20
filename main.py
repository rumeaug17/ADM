"""Point d’entrée de l’application web ADM."""

from ADM.cli import parse_debug_option, run_server

if __name__ == "__main__":
    run_server(debug=parse_debug_option())
