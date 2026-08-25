#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${ADM_DEMO_VENV:-${PROJECT_ROOT}/.venv}"
ENV_FILE="${PROJECT_ROOT}/.adm-demo.env"
DEBUG_MODE="off"

if [[ ${1:-} == "--debug-mode" && $# -eq 2 ]]; then
    DEBUG_MODE="$2"
elif [[ $# -ne 0 ]]; then
    echo "Usage : scripts/run_demo.sh [--debug-mode on|off]" >&2
    exit 2
fi

if [[ "${DEBUG_MODE}" != "on" && "${DEBUG_MODE}" != "off" ]]; then
    echo "Le mode de débogage doit valoir 'on' ou 'off'." >&2
    exit 2
fi

if [[ ! -f "${ENV_FILE}" || ! -x "${VENV_PATH}/bin/python" ]]; then
    echo "La démo n'est pas configurée. Exécutez d'abord scripts/setup_demo.sh." >&2
    exit 1
fi

cd "${PROJECT_ROOT}"
# Le fichier local est créé avec des droits restreints par setup_demo.sh et n'est pas versionné.
source "${ENV_FILE}"
if [[ -n "${DEMO_USERNAME:-}" && -n "${DEMO_PASSWORD:-}" ]]; then
    echo "Identifiants de démonstration : ${DEMO_USERNAME} / ${DEMO_PASSWORD}"
fi
MAIN_ARGUMENTS=(main.py)
if [[ "${DEBUG_MODE}" == "on" ]]; then
    MAIN_ARGUMENTS+=(--debug)
fi
exec "${VENV_PATH}/bin/python" "${MAIN_ARGUMENTS[@]}"
