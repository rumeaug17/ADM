import json
import os
from auth.mysql_backend import MySQLAuthBackend

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    with open(config_path, "r") as f:
        return json.load(f)

def get_auth_backend():
    config = load_config()
    backend = config.get("auth_backend")

    if backend == "mysql":
        return MySQLAuthBackend()
    else:
        raise ValueError(f"Backend inconnu : {backend}")
