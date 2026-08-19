"""Point d’entrée de l’application web ADM."""

from ADM.app import create_app


def main() -> None:
    """Démarre le serveur de développement Flask."""
    create_app().run(debug=False)


if __name__ == "__main__":
    main()
