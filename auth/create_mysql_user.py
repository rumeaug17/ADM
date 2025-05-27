import bcrypt
import mysql.connector
import sys
import json
import os
from urllib.parse import urlparse

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r") as f:
        return json.load(f)

def parse_mysql_url(url):
    """Extrait les infos de connexion depuis une URL SQLAlchemy de type mysql+mysqlconnector://user:password@host/db"""
    parsed = urlparse(url)
    return {
        "host": parsed.hostname,
        "user": parsed.username,
        "password": parsed.password,
        "database": parsed.path.lstrip("/")
    }

def main():
    if len(sys.argv) != 3:
        print("Usage : python create_user.py <username> <password>")
        sys.exit(1)

    username = sys.argv[1]
    plain_password = sys.argv[2]

    # Chargement de la configuration
    config = load_config()

    if config.get("auth_backend") != "mysql":
        print("❌ Seul le backend 'mysql' est supporté par ce script.")
        sys.exit(1)

    # Extraction des paramètres de connexion depuis l’URL SQLAlchemy
    db_config = parse_mysql_url(config["auth_sql_connection_url"])

    # Hash du mot de passe
    hashed_password = bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()

    # Insertion dans la base
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed_password)
        )
        conn.commit()
        print(f"✅ Utilisateur '{username}' créé avec succès.")
    except mysql.connector.Error as err:
        print(f"❌ Erreur MySQL : {err}")
    except Exception as e:
        print(f"❌ Erreur : {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
