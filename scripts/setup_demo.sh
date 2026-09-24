#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${ADM_DEMO_VENV:-${PROJECT_ROOT}/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
ENV_FILE="${PROJECT_ROOT}/.adm-demo.env"

cd "${PROJECT_ROOT}"

echo "Création de l'environnement Python de démonstration..."
"${PYTHON_BIN}" -m venv "${VENV_PATH}"
VENV_PYTHON="${VENV_PATH}/bin/python"
"${VENV_PYTHON}" -m pip install --upgrade pip
"${VENV_PYTHON}" -m pip install -e '.[dev]'

echo "Construction de l'artefact..."
rm -rf build dist
"${VENV_PYTHON}" -m build

echo "Exécution des contrôles qualité..."
"${VENV_PYTHON}" -m ruff check .
"${VENV_PYTHON}" -m ruff format --check .
"${VENV_PYTHON}" -m mypy src main.py
"${VENV_PYTHON}" -m pytest

echo "Génération des données fictives..."
"${VENV_PYTHON}" scripts/generate_data_json.py

echo "Configuration du mode démo standalone et création du compte administrateur..."
ADM_DEMO_ENV_FILE="${ENV_FILE}" ADM_DEMO_DATABASE="${PROJECT_ROOT}/applications.json" \
ADM_DEMO_ACCOUNTS="${PROJECT_ROOT}/accounts.json" \
ADM_DEMO_CONFIG_PATH="${ADM_CONFIG_PATH:-}" \
ADM_DEMO_QUESTIONS_PATH="${ADM_QUESTIONS_PATH:-}" \
ADM_DEMO_INFO_TEXTS_PATH="${ADM_INFO_TEXTS_PATH:-}" \
    "${VENV_PYTHON}" - <<'PYTHON'
import os
import secrets
import shlex
from pathlib import Path

environment_path = Path(os.environ["ADM_DEMO_ENV_FILE"])
database_path = os.environ["ADM_DEMO_DATABASE"]
accounts_path = os.environ["ADM_DEMO_ACCOUNTS"]
demo_username = f"demo-{secrets.token_hex(4)}"
demo_password = secrets.token_urlsafe(18)

values = {
    "ADM_DB_BACKEND": "json",
    "ADM_DATABASE_URL": database_path,
    "ADM_SECRET_KEY": secrets.token_urlsafe(48),
    "ADM_ACCOUNTS_URL": accounts_path,
    # La démo locale tourne sur le serveur de développement Flask, en HTTP simple
    # (voir scripts/run_demo.sh) : l'attribut Secure (activé par défaut, US6.3)
    # empêcherait alors le navigateur de renvoyer le cookie de session.
    "ADM_SESSION_COOKIE_SECURE": "false",
}

# Optionnelles : si l'appelant les avait définies avant setup_demo.sh (pour
# stocker config.json/questions.json/info_texts.json hors du paquet installé,
# comme en production -- voir INSTALL.md section 5 et ADM.persistent_paths),
# elles sont reprises telles quelles afin que run_demo.sh les restaure aussi
# (par un simple `source` du fichier généré ci-dessous). Sans cela, ces trois
# variables n'étaient jamais persistées : relancer la démo depuis un nouveau
# terminal (l'usage documenté, voir README.md) perdait silencieusement
# l'intention de l'appelant, et les modifications faites depuis /settings ou
# /settings/questions finissaient par réécrire le config.json/questions.json/
# info_texts.json du paquet installé au lieu de l'emplacement persistant voulu.
for key, env_name in (
    ("ADM_CONFIG_PATH", "ADM_DEMO_CONFIG_PATH"),
    ("ADM_QUESTIONS_PATH", "ADM_DEMO_QUESTIONS_PATH"),
    ("ADM_INFO_TEXTS_PATH", "ADM_DEMO_INFO_TEXTS_PATH"),
):
    value = os.environ.get(env_name, "")
    if value:
        values[key] = value

for key, value in values.items():
    os.environ[key] = value

file_values = dict(values, DEMO_USERNAME=demo_username, DEMO_PASSWORD=demo_password)
content = "".join(f"export {key}={shlex.quote(value)}\n" for key, value in file_values.items())
environment_path.write_text(content, encoding="utf-8")
environment_path.chmod(0o600)

from ADM.accounts_service import create_account
from ADM.app import create_app

application = create_app()
factory = application.extensions["adm_account_session_factory"]
session = factory()
try:
    create_account(session, username=demo_username, password=demo_password, role="admin")
    session.commit()
finally:
    session.close()
PYTHON

rm -f static/version.txt
git describe --tags --abbrev=0 2>/dev/null > src/ADM/resources/static/version.txt || \
    printf 'v0.1.0\n' > src/ADM/resources/static/version.txt

echo "Installation terminée. Lancez la démo avec : scripts/run_demo.sh"
