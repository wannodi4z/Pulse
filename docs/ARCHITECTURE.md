## v1.1.1

`frontend/static/analytics-catalog.js` define veinte análisis y su disponibilidad por alcance. Obtiene todos los valores del reporte ya autorizado, sin consultas fuera de su alcance ni nuevos cálculos de OT/SB. Los filtros se preparan como borrador y se aplican al enviar el modal. Historial utiliza sólo mes o todo el historial; el API de comparación permanece para Analítica.

`backend/demo_banorte.py` inicializa la rama de prueba únicamente con bandera explícita y sin organización existente. Una plantilla JSON local opcional contiene el organigrama completo; se excluye del repositorio público. Roles y dependencias se validan antes de insertar, dentro de una sola transacción con claves foráneas activas. Cada contraseña utiliza su propia sal. No genera horas ni delegaciones.

## v1.1.0 · Módulos adicionales

- `backend/organization_transfers.py`: propuestas, huella de estructura y autorizaciones ejecutivas; aplicación en transacción inmediata. Historial y delegaciones conservan su trazabilidad. No amplía permisos de aprobación de horas.
- `backend/activity_links.py`: consulta autenticada de una actividad y disponibilidad del Timer; el GET no registra tiempo. Inicio e inscripción usan los endpoints operativos existentes.
- `backend/record_exports.py`: exportación de búsqueda separada del libro de analítica, utilizando el mismo reporte autorizado.
- `frontend/static/organization-transfers.js`: preparación visual de propuestas y decisiones por rol.
- `frontend/static/analytics-layout.js`: distribución en píxeles, ratio de ancho y altura continua; migración compatible de preferencias anteriores y adaptación del SVG mediante ResizeObserver.

La única escritura ejecutiva adicional permitida por `current_user` es POST a la decisión de traslado; la ruta verifica que el usuario sea uno de sus revisores. Las escrituras restantes siguen restringidas.

## Configuración y respaldo integral · v1.0.22

`backend/system_admin.py` instala rutas exclusivas de Admin, persiste SMTP en `system_settings` y cifra la contraseña con la clave local existente. No incorpora envío de correo. El respaldo usa SQLite backup sobre una copia temporal, quita sesiones y material de recuperación, cierra Timers activos sólo en la copia y cifra el paquete ZIP con Fernet/Scrypt. `scripts/restore_organization.py` valida y restaura offline a archivos nuevos, con permisos restringidos y rechazo de sobrescrituras. No usa extracción ZIP a rutas suministradas por el archivo.

Los perfiles del tablero y sidebar son preferencias locales por usuario. El modo PERSONAL mantiene un conjunto propio de gráficas y un espacio de preferencias separado de TEAM. El acceso de escritorio es un enlace web; sólo abre controles y deja las operaciones de captura en sus endpoints autenticados existentes.

La entrega v1.0.21 arranca sin fixtures ni carga de ejemplo. `init_db` sólo crea los dos administradores iniciales si no existen usuarios. Las bases existentes se conservan. El árbol usa el mismo estado autorizado y aplica los mismos filtros de analítica; no crea un alcance alternativo ni cambia cálculos.

## Jerarquía ejecutiva · v1.0.21

`backend/hierarchy.py` migra el CHECK de roles en una transacción con copia de SQLite, preservando índices y referencias. `users.parent_id` relaciona DP→DPE→Manager; `account_id` delimita la Cuenta. `read_scope` y `read_visible_users` calculan acceso de consulta sin ampliar `scope`, `visible_users` ni `authorized_target` de gestión. `current_user` rechaza operaciones ejecutivas de escritura salvo perfil, contraseña, cierre y actividad de su propia sesión. Analítica, estado, participantes y exportación resuelven el alcance en cada solicitud.

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
| frontend/static/analytics-visuals.js | Gráficas, resúmenes, leyendas interactivas y datos emergentes sobre el reporte autorizado |
| frontend/static/analytics-layout.js | Tamaños y visibilidad del tablero del equipo; preferencias locales por usuario, sin cambios en datos ni autorización |
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
