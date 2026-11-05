# Operational Pulse · v1.1.3

Control de OT y Guardias con calendario, Timer, documentación, aprobaciones, historial, analítica, Claim/ADP y respaldos.

La v1.1.3 corrige la escritura en los buscadores de Explorador y Árbol: conserva el campo, cursor, selección y composición de acentos mientras actualiza únicamente los resultados. Incluye todas las mejoras de la v1.1.2. [Guía de la versión](docs/RELEASE_v1.1.3.md).

## Demo Banorte · México

`start.command` habilita la demo de prueba sólo si aún no hay una organización. El ZIP de demo incluye la plantilla del organigrama de 346 personas; el repositorio público contiene únicamente los seis accesos de prueba especificados, sin la plantilla privada adjunta. No hay OT, Guardias ni delegaciones precargadas.

[Accesos y estructura de prueba](docs/DEMO_BANORTE.md). Los Admin iniciales siguen siendo `admin1 / admin12026` y `admin2 / admin22026`.

Una base existente **no se mezcla, no se borra ni se reinicializa**. Para comenzar esta demo, extrae el ZIP en una carpeta nueva. Para arrancar sin la demo usa `PULSE_DEMO_BANORTE=0 ./start.command`, o uvicorn sin esa variable.

## Arranque local en Mac / VS Code

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
PULSE_DEMO_BANORTE=1 python -m uvicorn server:app --host 127.0.0.1 --port 5510
```

Abre http://127.0.0.1:5510. También puedes usar `start.command` después de instalar el entorno. Control+C detiene el servidor.

## Organización y roles

Admin configura **Cuenta → DP → DPE → Manager → Grupos → Técnicos**. Desde la Cuenta, crea el DP, sus DPE y después sus Managers. Se generan códigos de activación para que cada persona defina su contraseña. El Manager conserva la administración de sus Grupos y Técnicos; Admin gestiona Managers y Leads.

- **DP:** historial y analítica de toda su Cuenta.
- **DPE:** historial y analítica sólo de sus Managers y equipos.
- **Manager:** gestión, aprobación e información de su equipo.
- **Lead:** Técnico con las facultades que delegue su Manager.
- **Técnico:** actividad y tiempo propios.

DP y DPE no capturan OT/SB, no editan ni autorizan horas. Sí revisan las propuestas de traslado organizacional que les corresponden. El árbol organizacional es otra forma de buscar: selecciona un nivel para ver sus horas y se sincronizan los filtros habituales. Comparación de meses, gráficas personalizables, ampliación, leyendas y exportación se conservan. [Guía de roles, altas, árbol y actualización](docs/EXECUTIVE_ROLES.md).

## Actualizaciones y respaldo

Conserva tu base SQLite y su archivo `.key` al actualizar si deseas mantener los registros. Antes de ampliar los roles de una base anterior, Pulse crea una copia en `backups/antes_v121_*.sqlite3`. Los Managers existentes quedan pendientes de vincular a un DPE sin alterar sus equipos.

El Excel de aprobados y el respaldo personal `.pulse` son archivos distintos. Recuperar horas requiere revisión del Manager. [Guía de respaldos](docs/BACKUPS.md).

## Archivos del proyecto

- `server.py`: punto de entrada estable.
- `backend/application.py`: API, permisos y cálculo de horas.
- `backend/hierarchy.py`: migración de roles preservando datos y referencias.
- `backend/time_recovery.py`: respaldo y recuperación de horas.
- `frontend/`: interfaz y módulos de visualización.
- `docs/`: guías, arquitectura y validación; las presentaciones de versiones anteriores son material de referencia.
- `tests/`: comprobaciones; las pruebas que requieren fixtures históricas se ejecutan desde el repositorio de desarrollo.

La entrega no contiene bases de ejemplo, claves, sesiones ni respaldos privados. Las herramientas históricas de desarrollo no se ejecutan al iniciar Pulse.
