# Validación ejecutada · Operational Pulse 1.3.1

Fecha: 26 de octubre de 2026, zona de referencia America/Mexico_City.

## Entorno y comandos

Linux, Python 3.12 y Chromium real headless. SQLite temporal por prueba, sin modificar datos de la instalación local. No se ejecutaron pruebas físicas en macOS, VS Code de Mac ni Safari. Chromium se inició con `/tmp/chromium`, del paquete `@sparticuz/chromium`, mediante la opción `PULSE_CHROMIUM_EXECUTABLE` del script.

```bash
node --check static/app.js
.venv/bin/python -m py_compile server.py tests/test_api.py tests/browser_smoke.py
.venv/bin/python -m unittest discover -s tests -p test_api.py
PULSE_CHROMIUM_EXECUTABLE=/tmp/chromium .venv/bin/python tests/browser_smoke.py
```

## Backend

22 pruebas funcionales aprobadas, sin fallas ni omisiones. Se realizaron llamadas HTTP con FastAPI TestClient y se comprobaron datos persistidos y cálculos, además de sintaxis.

- Base nueva: sólo admin1 y admin2; catálogos y operación vacíos; reinicializar conserva datos manuales. Sin migraciones que creen datos demo.
- Jerarquía: varios Managers por Cuenta, varios Grupos por Manager, varios Técnicos por Grupo, propiedad exclusiva del Grupo, mezcla de Cuentas rechazada y eliminación de Cuenta ocupada bloqueada.
- Un Lead por Manager entre distintos Grupos; segundo Lead rechazado. Un Lead puede cambiar de Grupo dentro de su Manager con motivo; no se permite reunir dos Leads al transferir una persona, un Grupo o los Grupos de un Manager durante su baja. Los rechazos revierten toda la transacción.
- Capacidad Lead independiente de aprobación, alcance explícito de delegación, autoaprobación bloqueada, revocación y cambio de designación con historial. Datos heredados conservados; Admin puede reducir tres designaciones anteriores a una.
- Transferencia de Técnico activo conserva ID y estado e invalida su sesión; Manager no puede ejecutar cambios de personas. Transferencia de Grupo activo conserva integrantes y estado.
- Baja de Manager con dos Grupos: exige todos los destinos, conserva activos a sus Técnicos y un Timer en ejecución, revoca acceso y delegación anterior, traslada pendientes al nuevo responsable e invalida códigos de recuperación conocidos por el anterior. Nuevo Manager puede aprobar tiempo del equipo transferido.
- Reemplazo pendiente de activación rechazado; después de activarse puede recibir Grupos. Cambios posteriores a la revisión provocan 409. Baja de la propia cuenta Admin bloqueada.
- Baja de Técnico con Timer de emergencia: sin confirmación de cierre o documentación, no modifica el Timer. Con documentación completa, cierra el Timer y envía el tiempo a aprobación. Guardia que cruza medianoche se limita al momento de la baja; Guardia futura se cancela.
- Ejemplo de baja comprobado con reloj controlado: Guardia de lunes 22:00 a martes 06:00; Timer de lunes 23:00 a martes 01:00; baja martes 01:00. Resultado aprobado: 2 h OT y 1 h Guardia neta. La reactivación no reanuda cobertura cancelada.
- Baja invalida activación pendiente; reactivación genera código distinto y exige nueva contraseña, conservando ID e historial.
- Intervalos múltiples por día, domingo 24 h, deduplicación de traslapes, descuento OT sobre Guardia y separación por medianoche. Excel generado se abre con openpyxl y se comprueban totales.
- OT compartida con participaciones individuales; timers inmediatos, detención, documentación, aprobación/rechazo e historial.
- Analítica mensual por Grupo, Técnico, día y tipo; incluye tipos emergente, programada, histórica y Guardia neta. Conciliación con contabilidad y Excel. Técnico limitado a sus propios datos; Lead sólo al alcance delegado y mientras esté vigente; Admin no obtiene permiso operativo por administrar usuarios.
- Recuperación de acceso según responsable, ver/regenerar código autorizado, código de un solo uso, invalidación de sesiones y clave cifrada separada. Lead delegado no gestiona recuperaciones.
- Aislamiento de reportes, origen externo bloqueado, estado global no sobrescribible y archivos internos no servidos por HTTP.

## Navegador real

`tests/browser_smoke.py`: PASS, cero errores JavaScript capturados. Llamadas reales al servidor y SQLite, sin reemplazar el backend por mocks.

Recorrido: marca Kyndryl y ambos autores; versión; mostrar/ocultar contraseña; activación y recuperación con validación y foco; altas y jerarquía anidada; selector Lead bloqueado también desde otro Grupo del mismo Manager; navegación desde Organización sin rebotes; búsqueda conserva foco; reglas con 13 intervalos; delegación dentro de Mi equipo; solicitudes, OT histórica, Timer de emergencia, aprobaciones y accesos desde tarjetas del Panel; Excel descargado; analítica y filtros, Excel analítico, separación personal/equipo y revocación; Claim y ADP; recuperaciones con ver/regenerar código.

También ejecutó desde la interfaz: transferencia de Técnico activo a otro Grupo, transferencia de Grupo a otro Manager, baja del Manager con traspaso de su Grupo restante y reactivación con código nuevo. Se verificaron los estados e IDs mediante `/api/state`.

Diseño comprobado a 1440 × 1000 y 390 × 844: sin desbordamiento horizontal de la página ni del diálogo de acceso; altura del diálogo dentro del viewport. Se inspeccionaron capturas de los diálogos ampliados. No se afirma ausencia de scroll en todas las resoluciones o cantidades de pendientes: los formularios extensos y las pantallas pequeñas conservan desplazamiento.

## Entrega

ZIP completo con código, HTML, CSS, JavaScript, requisitos, README, especificación, validación, configuración VS Code y pruebas. Excluye entornos virtuales, bases SQLite, claves, sesiones y datos de prueba. Se descomprime e importa el servidor del ZIP con una base temporal nueva para comprobar versión, dos administradores iniciales y operación vacía.


## Ajuste de escala v1.3.1

Prueba adicional sin zoom CSS ni transformaciones: el diálogo de baja con un Grupo, destino, instrucciones, reemplazo, motivo, confirmación y acciones mide aproximadamente 601 px de alto. En viewports de 1440×760, 1366×700 y 1280×650 se verificó que cabe completo y que `scrollHeight` del contenido coincide con `clientHeight`: no requiere desplazamiento en ese caso. El navegador usa su escala nativa 100%. Cabecera y botones quedan fuera de la zona desplazable para casos con muchos pendientes. Las reglas de Guardia muestran un día por vez, conservando todos los intervalos de la semana al guardar. La suite recorrió los siete días y verificó los 13 intervalos persistidos.

Se conservaron pruebas móviles. No se ejecutó Safari ni una Mac física; las alturas de viewport representan el área de contenido disponible después de las barras del navegador.
