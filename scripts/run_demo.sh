#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${ADM_DEMO_VENV:-${PROJECT_ROOT}/.venv}"
ENV_FILE="${PROJECT_ROOT}/.adm-demo.env"

if [[ ! -f "${ENV_FILE}" || ! -x "${VENV_PATH}/bin/python" ]]; then
    echo "La démo n'est pas configurée. Exécutez d'abord scripts/setup_demo.sh." >&2
    exit 1
fi

cd "${PROJECT_ROOT}"
# Le fichier local est créé avec des droits restreints par setup_demo.sh et n'est pas versionné.
source "${ENV_FILE}"
exec "${VENV_PATH}/bin/python" main.py
