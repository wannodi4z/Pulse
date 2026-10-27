#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  printf '%s\n' 'Primero instala el entorno desde la terminal de VS Code:' 'python3 -m venv .venv' 'source .venv/bin/activate' 'python -m pip install -r requirements.txt'
  exit 1
fi
printf '%s\n' 'Operational Pulse local: abre http://127.0.0.1:5510 en tu navegador.' 'Para detener: Control+C.'
exec .venv/bin/python -m uvicorn server:app --host 127.0.0.1 --port 5510
