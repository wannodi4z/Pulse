#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  printf '%s\n' 'Primero instala el entorno y abre Pulse una vez con start.command.'
  exit 1
fi
printf '%s\n' 'Carga de datos DEMO: cierra Pulse antes de continuar.' 'Se agregan registros sin reemplazar los existentes y se respalda la base en backups/.' 'Octubre de 2026 de Samuel Díaz (951357) permanece intacto.'
.venv/bin/python scripts/populate_demo_records.py
printf '%s\n' 'Carga completada. Abre Pulse con start.command.'
