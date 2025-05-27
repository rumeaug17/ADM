import mysql.connector
from auth.base import AuthBackend

class MySQLAuthBackend(AuthBackend):
    def __init__(self, config):
        self.config = config

    def authenticate(self, username, password):
        connection = mysql.connector.connect(**self.config)
        cursor = connection.cursor()
        query = "SELECT password FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        if result:
            return password == result[0]  # À remplacer par une comparaison hashée
        return False
