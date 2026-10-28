#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  printf '%s\n' 'Primero instala el entorno desde la terminal de VS Code:' 'python3 -m venv .venv' 'source .venv/bin/activate' 'python -m pip install -r requirements.txt'
  exit 1
fi
export PULSE_TEST_DB_PATH="$PWD/pruebas/operational_pulse.db"
export PULSE_DB_PATH="$PULSE_TEST_DB_PATH"
if [ ! -f "$PULSE_TEST_DB_PATH" ]; then
  .venv/bin/python scripts/prepare_test_users.py
fi
printf '%s\n' 'Operational Pulse · base de pruebas separada: http://127.0.0.1:5510' 'Detén primero la otra instancia si usa el puerto 5510. Para detener: Control+C.'
exec .venv/bin/python -m uvicorn server:app --host 127.0.0.1 --port 5510
