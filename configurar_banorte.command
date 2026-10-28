#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  printf '%s\n' 'Instala primero el entorno:' 'python3 -m venv .venv' 'source .venv/bin/activate' 'python -m pip install -r requirements.txt'
  exit 1
fi
.venv/bin/python scripts/prepare_banorte_users.py
exec bash start.command
