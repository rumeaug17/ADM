#!/usr/bin/env python3
"""Sauvegarde et restauration de la base MySQL configurée pour ADM.

Les paramètres de connexion (hôte, port, utilisateur, base, mot de passe) sont
dérivés de ``ADM_DATABASE_URL`` -- la même variable d'environnement que celle
utilisée par l'application et par Alembic (voir INSTALL.md, section 5) -- afin
qu'une sauvegarde ou une restauration cible toujours la base réellement
configurée, jamais une base locale par défaut.
"""

import argparse
import os
import subprocess
from datetime import datetime
from urllib.parse import unquote, urlsplit


class ConnectionConfigError(RuntimeError):
    """Signale une configuration de connexion MySQL absente ou invalide."""


def load_connection_from_environment() -> dict:
    """Extrait les paramètres de connexion MySQL de ``ADM_DATABASE_URL``.

    ``ADM_DATABASE_URL`` doit être définie avec la même valeur que celle du
    processus applicatif, au format
    ``mysql+mysqlconnector://<utilisateur>:<mot-de-passe>@<hote>[:<port>]/<base>``.
    Le mot de passe n'est jamais affiché ni journalisé.
    """
    database_url = os.environ.get("ADM_DATABASE_URL")
    if not database_url:
        raise ConnectionConfigError(
            "ADM_DATABASE_URL est obligatoire : utilisez la même valeur que celle "
            "configurée pour l'application (voir INSTALL.md, section 5)."
        )
    parsed = urlsplit(database_url)
    if "mysql" not in parsed.scheme:
        raise ConnectionConfigError(
            "ADM_DATABASE_URL ne décrit pas une connexion MySQL "
            f"(schéma {parsed.scheme!r})."
        )
    if not parsed.hostname or not parsed.username or not parsed.path.lstrip("/"):
        raise ConnectionConfigError(
            "ADM_DATABASE_URL est incomplète : hôte, utilisateur et nom de base sont "
            "obligatoires."
        )
    password = unquote(parsed.password) if parsed.password else os.environ.get(
        "ADM_DATABASE_PASSWORD"
    )
    if not password:
        raise ConnectionConfigError(
            "Aucun mot de passe trouvé : incluez-le dans ADM_DATABASE_URL ou "
            "définissez ADM_DATABASE_PASSWORD."
        )
    return {
        "db_host": parsed.hostname,
        "db_port": parsed.port or 3306,
        "db_user": unquote(parsed.username),
        "db_name": parsed.path.lstrip("/"),
        "db_password": password,
    }


def _mysql_environment(password: str) -> dict:
    return {**os.environ, "MYSQL_PWD": password}


def backup_database(connection: dict) -> None:
    """Sauvegarde la base via ``mysqldump``, sans exposer le mot de passe."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_{timestamp}.sql"
    cmd = [
        "mysqldump",
        "-h",
        str(connection["db_host"]),
        "-P",
        str(connection["db_port"]),
        "-u",
        connection["db_user"],
        connection["db_name"],
    ]
    try:
        with open(backup_file, "w", encoding="utf-8") as handle:
            subprocess.run(
                cmd,
                stdout=handle,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                env=_mysql_environment(connection["db_password"]),
            )
        print(f"Sauvegarde réalisée avec succès : {backup_file}")
    except subprocess.CalledProcessError as error:
        print("Erreur lors de la sauvegarde :", error.stderr)


def restore_database(connection: dict, backup_file: str) -> None:
    """Restaure la base via ``mysql``, sans exposer le mot de passe."""
    cmd = [
        "mysql",
        "-h",
        str(connection["db_host"]),
        "-P",
        str(connection["db_port"]),
        "-u",
        connection["db_user"],
        connection["db_name"],
    ]
    try:
        with open(backup_file, encoding="utf-8") as handle:
            subprocess.run(
                cmd,
                stdin=handle,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                env=_mysql_environment(connection["db_password"]),
            )
        print(f"Restauration réalisée avec succès depuis : {backup_file}")
    except subprocess.CalledProcessError as error:
        print("Erreur lors de la restauration :", error.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Sauvegarde ou restaure la base MySQL désignée par ADM_DATABASE_URL "
            "(mêmes clients requis : mysqldump / mysql)."
        )
    )
    parser.add_argument(
        "action",
        choices=["backup", "restore"],
        help="Action à réaliser : 'backup' pour sauvegarder, 'restore' pour restaurer",
    )
    parser.add_argument(
        "--file", help="Fichier de sauvegarde à restaurer (obligatoire pour l'action 'restore')"
    )
    args = parser.parse_args()

    try:
        connection = load_connection_from_environment()
    except ConnectionConfigError as error:
        print(f"Configuration invalide : {error}")
        return

    if args.action == "backup":
        backup_database(connection)
    elif args.action == "restore":
        if not args.file:
            print(
                "Pour l'action 'restore', vous devez spécifier le fichier de sauvegarde avec --file"
            )
            return
        restore_database(connection, args.file)


if __name__ == "__main__":
    main()
