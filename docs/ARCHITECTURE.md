# Estructura de Operational Pulse v1.0.10

## Arranque y compatibilidad

Ejecutar `start.command` desde la raíz, o `.venv/bin/python -m uvicorn server:app --host 127.0.0.1 --port 5510`.
`server.py` es una entrada mínima que carga `backend/application.py` en el mismo espacio de nombres. Se conserva así la compatibilidad con los scripts existentes y las pruebas que configuran la base o el reloj. No hay dos implementaciones del servidor.

## Responsabilidades

| Carpeta / archivo | Responsabilidad |
| --- | --- |
| backend/application.py | Sesiones, roles, cuentas, equipos, OT, Timer, Guardias, reglas, autorizaciones, calendario, analítica y cálculos Claim/ADP |
| backend/time_recovery.py | Lectura validada, vista previa, duplicados, recuperación transaccional y respaldos personales |
| frontend/index.html | Entrada HTML y orden de carga de recursos |
| frontend/static/app.js | Estado, vistas, formularios e interacción con API |
| frontend/static/layout.js | Organización del contenido y paginación |
| frontend/static/app.css, design.css, interface.css | Estilos base, componentes y acabado responsive, en ese orden |
| scripts | Preparación explícita de ejemplos y pruebas |
| fixtures | Datos de demostración iniciales |
| tests | Pruebas de comportamiento y navegador |
| docs | Especificación, decisiones, evidencia e historial |

La aplicación principal conserva su cohesión para evitar cambiar la semántica de las transacciones y autorizaciones durante el reordenamiento. No se ha dividido cada función en un archivo artificial. Los módulos de recuperación y frontend están separados físicamente del arranque.

## Datos y rutas

La base `operational_pulse.db` y su `.key` permanecen en la raíz por compatibilidad. `PULSE_DB_PATH`, `PULSE_RECOVERY_KEY_PATH` y `PULSE_TIMEZONE` siguen funcionando. No mover ni eliminar datos existentes para actualizar.
El navegador conserva las URL `/static/...`; el servidor las resuelve a `frontend/static`. No se expone la carpeta backend.

El ZIP contiene sólo archivos versionados: no incluye bases personales, claves, .venv, cachés, capturas temporales ni los Excel enviados por usuarios. Las pruebas y documentación sí se conservan porque son necesarias para mantener y documentar el proyecto.
