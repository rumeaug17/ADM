"""Point d'entrée de l'application web ADM."""

from ADM.app import app


def main() -> None:
    """Démarre le serveur de développement Flask."""
    app.run(debug=False)


if __name__ == "__main__":
    main()
