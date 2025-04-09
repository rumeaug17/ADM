#!/usr/bin/env python3
import subprocess
import argparse
import json
import os
from datetime import datetime

def load_config(config_path):
    """Charge la configuration depuis le fichier config.json."""
    with open(config_path, "r", encoding="utf-8") as f:
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
    #  - db_password
    #  - db_name
    db_host = config.get("db_host", "localhost")
    db_port = config.get("db_port", 3306)
    db_user = config.get("db_user", "root")
    db_password = config.get("db_password", "")
    db_name = config.get("db_name", "adm_db")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_{timestamp}.sql"
    
    cmd = [
        "mysqldump",
        "-h", str(db_host),
        "-P", str(db_port),
        "-u", db_user,
        f"-p{db_password}",
        db_name
    ]
    
    try:
        with open(backup_file, "w", encoding="utf-8") as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True, check=True)
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
    db_password = config.get("db_password", "")
    db_name = config.get("db_name", "adm_db")
    
    cmd = [
        "mysql",
        "-h", str(db_host),
        "-P", str(db_port),
        "-u", db_user,
        f"-p{db_password}",
        db_name
    ]
    
    try:
        with open(backup_file, "r", encoding="utf-8") as f:
            result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True, check=True)
        print(f"Restauration réalisée avec succès depuis : {backup_file}")
    except subprocess.CalledProcessError as e:
        print("Erreur lors de la restauration :", e.stderr)

def main():
    parser = argparse.ArgumentParser(
        description="Script de sauvegarde et restauration de la base MySQL."
    )
    parser.add_argument("action", choices=["backup", "restore"], 
                        help="Action à réaliser : 'backup' pour sauvegarder, 'restore' pour restaurer")
    parser.add_argument("--config", default="config.json", 
                        help="Chemin vers le fichier de configuration (default: config.json)")
    parser.add_argument("--file", help="Fichier de sauvegarde à restaurer (obligatoire pour l'action 'restore')")
    args = parser.parse_args()

    config = load_config(args.config)

    if args.action == "backup":
        backup_database(config)
    elif args.action == "restore":
        if not args.file:
            print("Pour l'action 'restore', vous devez spécifier le fichier de sauvegarde avec --file")
            return
        restore_database(config, args.file)

if __name__ == "__main__":
    main()
