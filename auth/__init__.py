from auth.mysql_backend import MySQLAuthBackend

def get_auth_backend(config):
    auth_backend = config.get("auth_backend", "mysql").lower()
    if auth_backend == "mysql":
        return MySQLAuthBackend(config["auth_sql_connection_url"])
    else:
        raise ValueError("Auth Backend inconnu ou non configuré")
