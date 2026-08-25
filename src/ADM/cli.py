"""Lancement local de l'application web ADM et commandes d'administration."""

import argparse
import getpass
from collections.abc import Sequence

from ADM.accounts_service import AccountError, create_account
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


def create_account_command(arguments: Sequence[str] | None = None) -> None:
    """Crée un compte local (bootstrap du premier admin ou administration courante).

    Le mot de passe est demandé de manière interactive (getpass) : il ne doit
    jamais transiter par les arguments de la ligne de commande ni apparaître
    dans l'historique du shell ou les journaux.
    """
    parser = argparse.ArgumentParser(description="Crée un compte local ADM.")
    parser.add_argument("--username", required=True, help="nom d'utilisateur du compte")
    parser.add_argument(
        "--role", choices=("admin", "user"), default="admin", help="rôle du compte (US6.1)"
    )
    parsed = parser.parse_args(arguments)

    password = getpass.getpass("Mot de passe : ")
    confirmation = getpass.getpass("Confirmation : ")
    if password != confirmation:
        raise SystemExit("Les mots de passe ne correspondent pas.")
    if not password:
        raise SystemExit("Le mot de passe ne peut pas être vide.")

    application = create_app()
    account_session_factory = application.extensions["adm_account_session_factory"]
    account_session = account_session_factory()
    try:
        create_account(
            account_session, username=parsed.username, password=password, role=parsed.role
        )
        account_session.commit()
    except AccountError as error:
        account_session.rollback()
        raise SystemExit(str(error)) from error
    finally:
        account_session.close()
    print(f"Compte {parsed.username!r} créé avec le rôle {parsed.role!r}.")
