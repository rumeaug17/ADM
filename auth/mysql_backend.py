import mysql.connector
import bcrypt
import json
import os
from urllib.parse import urlparse
from auth.base import AuthBackend

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
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

class MySQLAuthBackend(AuthBackend):
    def __init__(self):
        config = load_config()
        if config.get("auth_backend") != "mysql":
            raise ValueError("Le backend configuré n'est pas 'mysql'")
        self.db_config = parse_mysql_url(config["auth_sql_connection_url"])

    def authenticate(self, username, password):
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            query = "SELECT password FROM users WHERE username = %s LIMIT 1"
            cursor.execute(query, (username,))
            result = cursor.fetchone()
            cursor.close()
            connection.close()

            if result:
                stored_hash = result[0]
                return bcrypt.checkpw(password.encode(), stored_hash.encode())
            return False
        except Exception as e:
            print(f"Erreur d'authentification : {e}")
            return False
