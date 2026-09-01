#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_config(config_path):
    """Charge la configuration depuis le fichier config.json."""
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    return config


def backup_database(config):
    """
    Effectue une sauvegarde de la base de données en exécutant mysqldump.
    Les informations de connexion doivent être présentes dans le fichier de configuration.
    """
    # On s'attend à trouver dans la config les clés suivantes :
    #  - db_host
    #  - db_port
    #  - db_user
    #  - db_name
    db_host = config.get("db_host", "localhost")
    db_port = config.get("db_port", 3306)
    db_user = config.get("db_user", "root")
    db_name = config.get("db_name", "adm_db")
    command_environment = _mysql_environment()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_{timestamp}.sql"

    cmd = [
        "mysqldump",
        "-h",
        str(db_host),
        "-P",
        str(db_port),
        "-u",
        db_user,
        db_name,
    ]

    try:
        with open(backup_file, "w", encoding="utf-8") as f:
            subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                env=command_environment,
            )
        print(f"Sauvegarde réalisée avec succès : {backup_file}")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de la sauvegarde :", e.stderr)


def restore_database(config, backup_file):
    """
    Restaure la base de données à partir d'un fichier de sauvegarde, en exécutant mysql.
    """
    db_host = config.get("db_host", "localhost")
    db_port = config.get("db_port", 3306)
    db_user = config.get("db_user", "root")
    db_name = config.get("db_name", "adm_db")
    command_environment = _mysql_environment()

    cmd = [
        "mysql",
        "-h",
        str(db_host),
        "-P",
        str(db_port),
        "-u",
        db_user,
        db_name,
    ]

    try:
        with open(backup_file, encoding="utf-8") as f:
            subprocess.run(
                cmd,
                stdin=f,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                env=command_environment,
            )
        print(f"Restauration réalisée avec succès depuis : {backup_file}")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de la restauration :", e.stderr)


def _mysql_environment():
    password = os.environ.get("ADM_DATABASE_PASSWORD")
    if not password:
        raise RuntimeError("ADM_DATABASE_PASSWORD est obligatoire.")
    return {**os.environ, "MYSQL_PWD": password}


def main():
    parser = argparse.ArgumentParser(
        description="Script de sauvegarde et restauration de la base MySQL."
    )
    parser.add_argument(
        "action",
        choices=["backup", "restore"],
        help="Action à réaliser : 'backup' pour sauvegarder, 'restore' pour restaurer",
    )
    parser.add_argument(
        "--config",
        default=str(PROJECT_ROOT / "src" / "ADM" / "resources" / "config.json"),
        help="Chemin vers le fichier de configuration (par défaut : ressource intégrée au paquet)",
    )
    parser.add_argument(
        "--file", help="Fichier de sauvegarde à restaurer (obligatoire pour l'action 'restore')"
    )
    args = parser.parse_args()

    config = load_config(args.config)

    if args.action == "backup":
        backup_database(config)
    elif args.action == "restore":
        if not args.file:
            print(
                "Pour l'action 'restore', vous devez spécifier le fichier de sauvegarde avec --file"
            )
            return
        restore_database(config, args.file)


if __name__ == "__main__":
    main()
