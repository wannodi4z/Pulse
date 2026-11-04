# Operational Pulse · v1.0.22

Control de OT y Guardias con calendario, Timer, documentación, aprobaciones, historial, analítica, Claim/ADP y respaldos.

La v1.0.22 revisa alineación y estados vacíos, agrega sidebar por secciones y contraíble, vistas de analítica guardadas, configuración SMTP sin envío, respaldo integral cifrado de Admin y acceso web al Timer desde el escritorio. [Guía de configuración y recuperación](docs/SYSTEM_CONFIGURATION.md) · [Revisión y recomendaciones](docs/INTERFACE_REVIEW_v1.0.22.md).

## Demo desde cero

Esta entrega está **limpia**: sin Cuentas, DP, DPE, Managers, Leads, Técnicos, Grupos ni horas precargadas. Sólo incluye los accesos iniciales:

| Usuario | Contraseña inicial |
|---|---|
| admin1 | admin12026 |
| admin2 | admin22026 |

Extrae el ZIP en una carpeta nueva para comenzar la demo completa. No copies una base anterior si buscas empezar sin datos. Si conservas una base existente, Pulse la migra sin borrarla ni sustituir sus registros.

## Arranque local en Mac / VS Code

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn server:app --host 127.0.0.1 --port 5510
```

Abre http://127.0.0.1:5510. También puedes usar `start.command` después de instalar el entorno. Control+C detiene el servidor.

## Organización y roles

Admin configura **Cuenta → DP → DPE → Manager → Grupos → Técnicos**. Desde la Cuenta, crea el DP, sus DPE y después sus Managers. Se generan códigos de activación para que cada persona defina su contraseña. El Manager conserva la administración de sus Grupos y Técnicos; Admin gestiona Managers y Leads.

- **DP:** historial y analítica de toda su Cuenta.
- **DPE:** historial y analítica sólo de sus Managers y equipos.
- **Manager:** gestión, aprobación e información de su equipo.
- **Lead:** Técnico con las facultades que delegue su Manager.
- **Técnico:** actividad y tiempo propios.

DP y DPE no capturan OT/SB, no editan ni autorizan horas. El árbol organizacional es otra forma de buscar: selecciona un nivel para ver sus horas y se sincronizan los filtros habituales. Comparación de meses, gráficas personalizables, ampliación, leyendas y exportación se conservan. [Guía de roles, altas, árbol y actualización](docs/EXECUTIVE_ROLES.md).

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
