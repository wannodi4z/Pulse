#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  printf '%s\n' 'Prepara primero el entorno Python siguiendo README.md.'
  exit 1
fi
exec .venv/bin/python scripts/restore_organization.py --destination "$PWD"
