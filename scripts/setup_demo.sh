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

echo "Configuration du mode démo standalone..."
ADM_DEMO_ENV_FILE="${ENV_FILE}" ADM_DEMO_DATABASE="${PROJECT_ROOT}/applications.json" \
    "${VENV_PYTHON}" - <<'PYTHON'
import os
import secrets
import shlex
from pathlib import Path

environment_path = Path(os.environ["ADM_DEMO_ENV_FILE"])
database_path = os.environ["ADM_DEMO_DATABASE"]
values = {
    "ADM_DB_BACKEND": "json",
    "ADM_DATABASE_URL": database_path,
    "ADM_SECRET_KEY": secrets.token_urlsafe(48),
    "ADM_USERNAME": f"demo-{secrets.token_hex(4)}",
    "ADM_PASSWORD": secrets.token_urlsafe(18),
}
content = "".join(f"export {key}={shlex.quote(value)}\n" for key, value in values.items())
environment_path.write_text(content, encoding="utf-8")
environment_path.chmod(0o600)
PYTHON

git describe --tags --abbrev=0 2>/dev/null > static/version.txt || \
    printf 'v0.1.0\n' > static/version.txt

echo "Installation terminée. Lancez la démo avec : scripts/run_demo.sh"
