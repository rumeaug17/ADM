from auth.mysql_backend import MySQLAuthBackend

def get_auth_backend(config):
    if config["auth_backend"] == "mysql":
        return MySQLAuthBackend(config["DB_CONNECTION"])
    else:
        raise ValueError("Auth Backend inconnu ou non configuré")
