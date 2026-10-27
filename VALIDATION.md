# Validación ejecutada · Operational Pulse 1.2.0

Fecha: 27 de octubre de 2026, zona de referencia America/Mexico_City.

## Entorno y comandos

Linux, Python 3.12 y Chromium real headless. SQLite temporal por prueba, sin modificar datos de la instalación local. No se ejecutaron pruebas físicas en macOS, VS Code de Mac ni Safari. Chromium se inició con `/tmp/chromium`, del paquete `@sparticuz/chromium`, mediante la opción `PULSE_CHROMIUM_EXECUTABLE` del script.

```bash
node --check static/app.js
.venv/bin/python -m py_compile server.py tests/test_api.py tests/browser_smoke.py
.venv/bin/python -m unittest discover -s tests -p test_api.py
PULSE_CHROMIUM_EXECUTABLE=/tmp/chromium .venv/bin/python tests/browser_smoke.py
```

## Backend

25 pruebas funcionales aprobadas, sin fallas ni omisiones. Se realizaron llamadas HTTP con FastAPI TestClient y se comprobaron datos persistidos y cálculos, además de sintaxis.

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

Diseño comprobado a 1440 × 1000 y 390 × 844: sin desbordamiento horizontal de la página ni del diálogo de acceso; altura del diálogo dentro del viewport. Se inspeccionaron capturas de los diálogos ampliados. Se utiliza paginación de vistas, listas y pasos de formulario para el contenido extenso.

## Entrega

ZIP completo con código, HTML, CSS, JavaScript, requisitos, README, especificación, validación, configuración VS Code y pruebas. Excluye entornos virtuales, bases SQLite, claves, sesiones y datos de prueba. Se descomprime e importa el servidor del ZIP con una base temporal nueva para comprobar versión, dos administradores iniciales y operación vacía.


## Ajuste de escala v1.0.0

Prueba adicional sin zoom CSS ni transformaciones: el diálogo de baja con un Grupo, destino, instrucciones, reemplazo, motivo, confirmación y acciones mide aproximadamente 601 px de alto. En viewports de 1440×760, 1366×700 y 1280×650 se verificó que cabe completo y que `scrollHeight` del contenido coincide con `clientHeight`: no requiere desplazamiento en ese caso. El navegador usa su escala nativa 100%. Cabecera y botones permanecen visibles; el contenido extenso se organiza por pasos. Las reglas de Guardia muestran un día por vez, conservando todos los intervalos de la semana al guardar. La suite recorrió los siete días y verificó los 13 intervalos persistidos.

Se conservaron pruebas móviles. No se ejecutó Safari ni una Mac física; las alturas de viewport representan el área de contenido disponible después de las barras del navegador.


## Comprobación completa de vistas v1.0.0

`tests/layout_smoke.py`: PASS. Se crearon una Cuenta, tres Grupos, un Manager, doce Técnicos y ocho OT reales aprobadas en SQLite temporal. Se recorrieron 54 combinaciones de rol/ruta/viewport: Admin (5 rutas), Manager (7) y Técnico (6), cada uno a 1440×780, 1366×700 y 1280×650, con zoom nativo 100%. En cada ruta se recorrieron las opciones de Vista y las páginas de las listas visibles. Se verificaron límites de botones, campos, títulos e identidades respecto al área central, sin desbordamiento del documento. También se completó un formulario OT por sus controles Continuar, verificando sus límites y que referencia, descripción e impacto se persistieran sin perder valores. Cero errores JavaScript.

La prueba de navegador general además creó, editó y eliminó una regla desde la interfaz y verificó que la copia de una Guardia existente permaneciera idéntica. El test de API `test_rule_edit_delete_preserves_existing_guard_snapshots` comprobó propiedad, rechazo de Admin/Técnico/otro Manager, intervalos inválidos, copia original y nueva, eliminación, horas sin cambio, nuevas solicitudes rechazadas al eliminarse la regla y auditoría de ambas operaciones.

Se validó sintaxis tanto de app.js como de layout.js. No se ejecutó la aplicación en una MacBook Air M1 física ni Safari: las pruebas de dimensiones se realizaron en Chromium/Linux y representan el área útil del navegador. Las cifras anteriores delimitan exactamente las resoluciones y datos comprobados; no son una afirmación de equivalencia con todos los tamaños de pantalla posibles.


## Limpieza de composición y versión v1.0.0

Se volvió a ejecutar `layout_smoke.py` con sus 54 combinaciones de rol/ruta/viewport y datos poblados. Ahora comprueba explícitamente que resumen y Cuenta están visibles juntos y que una sola Cuenta no tiene una pantalla de resumen separada. También comprueba filtros visibles en Tiempo del equipo y analítica. La suite de navegador verifica la firma Kyndryl integrada, el símbolo exclusivo `#settings`, el Panel de Admin sin bienvenida decorativa, el acceso directo de una Cuenta desde ese Panel y la versión v1.0.0. El backend conserva su lógica operativa; el cambio de servidor de esta entrega se limita a la constante de versión.


## Acabados v1.0.1

Se ejecutaron nuevamente las 23 pruebas de backend, la suite general de Chromium y las 54 combinaciones de rol/ruta/viewport de layout_smoke. Los recorridos administrativos ahora abren los menús reales para agregar Managers, transferir Técnicos/Grupos, revisar bajas y reactivar; no se sustituyen esas acciones por escrituras directas al estado.

Prueba adicional de menú: apertura desde la Cuenta, primer botón enfocado, ArrowDown hacia Editar Cuenta, límites dentro de viewport, Escape con devolución de foco y cierre al pulsar fuera. Se mantiene la comprobación de Organización combinada, acceso desde Panel, reglas de Guardia editables, OT, timers, guardias, aprobaciones, Claim/ADP, Excel, analítica y recuperaciones. Sintaxis de ambos módulos JS y compilación Python verificadas. Inspección visual de captura real de Organización, con jerarquía y acciones reagrupadas.

Las pruebas siguen realizándose en Chromium/Linux; no se ejecutaron en una Mac física o Safari. El ZIP excluye bases y claves; importar el servidor extraído con una SQLite nueva verifica la versión v1.0.1 y los dos administradores iniciales.


## Nueva interfaz Enterprise luminosa v1.1.0

Se volvieron a ejecutar las 23 pruebas de backend, la suite funcional Chromium y las 54 combinaciones de rol/ruta/viewport de layout_smoke (1440×780, 1366×700 y 1280×650). Se comprobaron páginas y formularios con datos reales aislados, límites de controles, paginación y conservación de documentación al avanzar por pasos.

La suite verifica ahora explícitamente que el sidebar es blanco, el texto de navegación activa es azul profundo y Kyndryl aparece en la cabecera, sin marca flotante en el sidebar. También comprueba menús con teclado, recuperación, navegación entre roles, altas/traspasos/bajas/reactivación, reglas editables, OT, timers, guardias, aprobaciones, Excel, Claim, ADP y analítica. La creación de Grupos antes de crear Manager se ejecutó mediante el menú de la Cuenta; la incorporación del primer Manager sigue disponible como acción principal.

Se inspeccionaron capturas de la Cuenta vacía, su menú y la estructura poblada. La instalación y el empaquetado no incluyen datos de esas pruebas; las imágenes de documentación son sólo vistas de referencia. Validación de sintaxis de ambos módulos JavaScript y compilación Python completadas. No se ejecutó una prueba física en MacBook Air M1 ni Safari: se utilizó Chromium/Linux con las dimensiones indicadas.


## Organización interactiva v1.2.0

25 pruebas API aprobadas: las dos nuevas verifican que la ruta dedicada de traslado conserva nombre/apellidos/correo actualizados aunque el navegador envíe valores antiguos, no acepta cambios de estado/Lead por esa vía, invalida la sesión del trasladado y rechaza un origen obsoleto con 409. También comprueban permisos Admin, motivo requerido, bloqueo por Timer y conflicto de Leads sin movimiento parcial.

`tests/layout_smoke.py` ejecutó arrastrar y soltar reales con `drag_to` de Playwright: abrir edición con Enter, soltar un Técnico sobre otro Grupo, verificar que aún no se guardó, cancelar con Escape, repetir y confirmar con un motivo frecuente, y regresar mediante Mover por teclado. Se comprobó un Técnico con Timer activo: atributo draggable=false y traslado bloqueado en la interfaz. Se conservaron las 54 combinaciones de rol/ruta/viewport y se comprobaron los controles del modal de traslado a 1440×760, 1366×700 y 1280×650.

La suite general de navegador volvió a recorrer activaciones, navegación, reglas, OT, timers, aprobaciones, analítica, recuperaciones, Excel, Claim/ADP, traspasos de Grupos, baja y reactivación. Cero errores JavaScript capturados. Sintaxis JS y compilación Python verificadas. Pruebas realizadas en Chromium/Linux, no en una Mac física ni Safari.
