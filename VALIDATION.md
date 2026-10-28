# Validación ejecutada · Operational Pulse 1.1.4

## Entrega v1.1.4 · 28 de octubre de 2026

- **59 pruebas API PASS**. El fixture incluye dos Managers por cada Cuenta y cuatro Leads sin Grupo, con login de MGR0001–MGR0004, SL0001–SL0004 y Técnicos de ejemplo. Mantiene registros vacíos y los accesos originales.
- `tests/admin_creation_browser.py`: PASS en Chromium real. Botones de Cuenta/Manager alineados y dentro del área visible, sin superposición, y nombre de Lead sin elipsis a 1440×780, 1366×700 y 1280×650. Creación real de un tercer Manager en Banorte, selección automática del nuevo bloque, Agregar Lead con Manager correcto y sin Grupo, activación, Editar Lead después de asignarlo y Agregar Grupo contextual guardando el propietario correcto. Cero errores JavaScript.
- `tests/organizer_browser.py`: PASS con los cuatro Managers y cuatro Leads. Cuatro Grupos visibles a 1440/1280, alta Lead disponible en Manager vacío, arrastre nativo/borrador/cancelación, alternativa de botones, revisión y traslado entre Cuentas. Diálogos a 1440/1280/390; cero errores JavaScript.
- `tests/layout_smoke.py`: PASS en 54 combinaciones de pantalla/rol/vista, incluyendo arrastre, cancelación, teclado y bloqueo con Timer. Sintaxis JavaScript y compilación Python correctas.
- `tests/browser_smoke.py`: flujo completo PASS, cero errores JavaScript; incluye menús de acciones por teclado, navegación, altas/activaciones, Lead, delegación, OT/Guardias/Timers, aprobaciones, analítica/Excel/Claim/ADP, traslados y baja/reactivación de Manager.
- Linux/Python 3.12/Chromium headless; no se probó físicamente en MacBook Air M1 ni Safari. Los dos Managers por Cuenta son ejemplos; la prueba de un tercero confirma que no es un límite funcional.

## Entrega v1.1.3 · 28 de octubre de 2026

- **59 pruebas API PASS** en Linux/Python 3.12. Incluyen los accesos originales y nuevos sin configurador en una carpeta nueva; nombre de Samuel; conservación en reinicios; lote Admin entre Cuentas con OT/Guardias intactas y nueva autoridad; rollback de todos los movimientos si un Timer está activo; bloqueo de otros roles, Leads, duplicados y origen desactualizado.
- `tests/organizer_browser.py` PASS con Chromium real: cuatro Grupos visibles a 1440×780 y 1280×650 sin controles fuera del área central; Lead en cabecera con Agregar/Editar; arrastre nativo con borrador y cancelación sin escritura; alternativa por botones; revisión y confirmación entre Cuentas. Tablero y revisión medidos a 1440×780, 1280×650 y 390×844; cero errores JavaScript.
- `tests/browser_smoke.py`: flujo completo PASS, cero errores JavaScript; navegación, organización detallada, usuarios/Lead, OT/Guardias, Timers, aprobaciones, analítica, Excel, Claim/ADP y ciclo de baja/reactivación.
- `tests/layout_smoke.py`: 54 combinaciones PASS, arrastre nativo, cancelación, alternativa de teclado y bloqueo con Timer activo.
- Sintaxis de app.js/layout.js y compilación Python correctas. Base incluida sin sesiones, OT, Guardias, Timers ni delegación; usuarios de ejemplo activos.
- No se probó físicamente en MacBook Air M1 ni Safari. Las listas extensas se paginan; se verificaron los tamaños indicados con zoom nativo, sin escalado CSS.

## Entrega v1.1.2 · 28 de octubre de 2026

Corrección del paquete de prueba, sin cambios en reglas operativas. Suite completa actual: **56 pruebas API aprobadas**; sintaxis JavaScript y compilación Python correctas. Pruebas nuevas mediante procesos Python separados en carpetas temporales con el código y fixture copiados: primer inicio sin configurador permite login de los tres accesos activos; reinicio conserva contraseña modificada y Cuenta manual; una base anterior limpia nunca se reemplaza. Las pruebas se ejecutan con FastAPI TestClient en Linux, no físicamente en Mac/Safari. Las pruebas funcionales y de Chromium de v1.1.1 se documentan debajo y corresponden a esa entrega previa.

## Entrega v1.1.1 · 28 de octubre de 2026

Linux, Python 3.12 y Chromium real headless `/usr/bin/chromium`, zoom nativo. No se probó físicamente en MacBook Air M1 ni Safari.

- Sintaxis app.js/layout.js y compilación servidor/scripts correctas.
- **53 pruebas API aprobadas**: incluye las regresiones operativas anteriores, Lead directo sin Grupo, OT propia aprobada por Manager, nuevas Guardias bloqueadas, delegación entre Grupos, autoaprobación bloqueada, recuperación sólo por Manager propio, traslado de Lead con registros y origen conservados, migración idempotente de Lead anterior y catálogo personalizado sin Plataforma.
- `tests/direct_lead_browser.py`: PASS con los tres usuarios solicitados. OT del Lead revisada por Manager en interfaz, Guardia ausente/bloqueada para Lead y disponible para Técnico, delegación real desde Mi equipo, Lead fuera de tarjetas de Grupo. Nuevo Grupo personalizado persiste en catálogo y código MX-BNTE-LINUX-Y-ORACLE. Modales medidos a 1440×780, 1280×650 y 390×844; solicitudes vacías compactas; cero errores JavaScript.
- `tests/browser_smoke.py`: flujo completo PASS, cero errores JavaScript; incluye altas y activaciones, Lead directo, delegación, Guardia/OT, Excel/Claim/ADP, analítica y baja de Manager con traslado de backup.
- `tests/layout_smoke.py`: 54 combinaciones PASS; arrastre nativo hacia la bandeja de destinos entre páginas, cancelación, alternativa por teclado, bloqueo con Timer y límites de pantalla a 1440×780, 1366×700 y 1280×650.
- `tests/analytics_browser.py`: PASS; búsqueda con totales y Excel equivalentes, comparación de tres meses y permisos. `tests/ot_browser.py`: PASS; clasificación temporal y modales de acceso/códigos en tres tamaños, inicializador de pruebas idempotente.
- La base normal de desarrollo tiene los accesos Banorte preparados con el configurador explícito. La base de tu Mac se actualiza al ejecutar `bash configurar_banorte.command` allí; no se distribuyen bases ni claves.

Las validaciones de v1.1.0 siguientes corresponden a la entrega anterior. Los apartados de Lead dentro de Grupo quedan sustituidos por la especificación de v1.1.1. Los datos anteriores se conservan; las Guardias heredadas siguen disponibles para consulta, sin autorizar solicitudes nuevas del Lead.

## Entrega v1.1.0 · 28 de octubre de 2026

Validación real en Linux con Python 3.12, SQLite temporal, FastAPI TestClient y Chromium `/usr/bin/chromium` headless, zoom nativo (sin CSS zoom ni reducción de fuente global). No se probó físicamente en MacBook Air M1, VS Code de Mac ni Safari. Las pruebas de navegador sí se ejecutaron; no se limita la verificación a sintaxis.

- `node --check static/app.js`, `node --check static/layout.js` y compilación Python de servidor/scripts/tests: correctas. Un solo nav/content/app/render/bind y una implementación de cada página principal.
- `python -m unittest discover -s tests -p 'test_*.py'`: **47 pruebas funcionales PASS**. Incluye instalación limpia sólo admin1/admin2, reinicio sin demos, relaciones y Lead único; Guardia por intervalos, OT/timers/extensiones; analítica, permisos y libros Excel; códigos internacionales; aprovisionamiento Banorte idempotente y conflictos atómicos; solicitudes y movimientos de Técnicos conservando OT/Guardias.
- `tests/browser_smoke.py`: flujo completo PASS, cero errores JavaScript: navegación, activación, recuperación/regeneración, organización y movimiento, delegación, OT, Guardia, Timer, aprobaciones, analítica, Excel, Claim y ADP.
- `tests/layout_smoke.py`: **54 combinaciones** de pantalla/rol/vista PASS; arrastre real, cancelar, teclado y bloqueo de traslado con Timer activo. Las dimensiones de escritorio incluyen 1440×780, 1366×700 y 1280×650. No hay una segunda vista de Historial: se integra en Analítica.
- `tests/organization_browser.py`: PASS, 26 Grupos, búsqueda por código/nombre/Manager, sin acentos, salto entre Cuentas, teclado/ratón, vacíos y creación de Grupo con código automático. Modales medidos a 1440×780, 1280×650 y 390×844.
- `tests/analytics_browser.py`: PASS, búsqueda global de referencia conserva foco y recalcula registros/totales; pendientes excluidos de horas; comparación de enero/febrero/marzo con 2/3/0 horas y Excel coincidente; Aprobaciones sólo pendientes; vistas y gráficas a 1440/1280/390 sin controles recortados.
- `tests/timeline_browser.py`: PASS, OT histórica incorporada por fecha de trabajo mediante sincronización sin recargar; orden cronológico, privacidad de otros Técnicos, pendientes con cero horas aprobadas; programación futura informa disponibilidad sin Timer anticipado; Detalle y ajuste a 1440/1280/390.
- `tests/transfers_browser.py`: PASS, Manager solicita desde Mi equipo, Admin revisa y ejecuta desde Organización, nuevo Manager ve OT previa pendiente, origen conservado. Modales de solicitud/revisión medidos a 1440/1280/390; formularios extensos se presentan en pasos cuando hace falta, sin scroll del modal.
- `tests/extensions_browser.py`: PASS, dos Técnicos/Grupos con Timer visibles en Panel del Manager, pausa exacta con todas las páginas cerradas, solicitar/autorizar/reanudar/finalizar en UI, espera excluida y refresco diferido al cerrar un diálogo.
- `tests/rules_browser.py`: PASS, cinco intervalos, recarga/reapertura, modificar/agregar/eliminar y guardar; comparación exacta de valores a 1280×650.
- `tests/ot_browser.py`: PASS, confirmaciones/códigos/resultados de acceso en tres dimensiones; clasificación automática pasada/futura/en curso con otra zona horaria del navegador y OT histórica persistida.
- `scripts/prepare_banorte_users.py` ejecutado explícitamente en la base normal del entorno de desarrollo: Banorte/MX-BNTE, seis Grupos Mainframe/OPEN; login real API de MGR0001, SL0001 y 951357 con las contraseñas solicitadas. La base del Mac sólo se actualizará cuando se ejecute `bash configurar_banorte.command` allí. No se incluye SQLite ni claves en la entrega.

Límites: los tamaños comprobados son viewports de navegador, no una reproducción física de la pantalla del Mac. Los registros anteriores sin origen registrado incorporan una referencia marcada como inferida al trasladarse. Analítica agrupa según pertenencia actual del Técnico; Detalle conserva el contexto de origen. No se generaron notificaciones ni se desplegó un servidor público.

Comandos de esta entrega:

```bash
node --check static/app.js
node --check static/layout.js
.venv/bin/python -m compileall -q server.py scripts tests
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
PULSE_CHROMIUM_EXECUTABLE=/usr/bin/chromium .venv/bin/python tests/browser_smoke.py
PULSE_CHROMIUM_EXECUTABLE=/usr/bin/chromium .venv/bin/python tests/layout_smoke.py
.venv/bin/python tests/organization_browser.py
.venv/bin/python tests/analytics_browser.py
.venv/bin/python tests/timeline_browser.py
.venv/bin/python tests/transfers_browser.py
.venv/bin/python tests/extensions_browser.py
.venv/bin/python tests/rules_browser.py
.venv/bin/python tests/ot_browser.py
```

## Registro de validaciones anteriores

Los apartados siguientes son históricos; los conteos y comandos de versiones anteriores no describen la entrega actual.

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

## Ajuste v1.2.1

- Ejecutados nuevamente `tests/browser_smoke.py` y `tests/layout_smoke.py` en Chromium: ambos PASS, 54 combinaciones de pantalla y cero errores JavaScript.
- Validadas sintaxis de app.js/layout.js y compilación de server.py.
- Cambios limitados a presentación, terminología y versión; conserva la participación individual en actividades programadas. Mac/Safari no ejecutados.

## Flujo operativo v1.2.2

- 25 pruebas API PASS, incluida denegación de nuevas publicaciones para Manager, Técnico y Admin, y conservación de participaciones históricas con Timers individuales.
- Prueba funcional completa `tests/browser_smoke.py` en Chromium PASS, cero errores JavaScript; incluye aprobaciones, Timer emergente, recuperación, administración y analítica.
- Sintaxis JavaScript y compilación de server.py correctas. Mac/Safari no ejecutados.

## Espaciado v1.2.3

- `tests/layout_smoke.py` ejecutado en Chromium: PASS, 54 combinaciones de pantalla, cero errores JavaScript. Incluye arrastre, cancelación, alternativa por teclado y bloqueo de Timer activo.
- Sintaxis de app.js y compilación de server.py correctas. Cambio visual de separación entre Grupos y paginación; Mac/Safari pendientes.

## Menús v1.2.4

- Prueba funcional completa `tests/browser_smoke.py` en Chromium PASS, cero errores JavaScript.
- Medición visual de la opción Generar código de activación con CSS real a 1440, 1280, 390 y 320 px: sin desbordamiento, con espacio interior derecho.
- Sintaxis de app.js y compilación de server.py correctas. Mac/Safari pendientes.

## Estabilización v1.0.0 · delegación manual

- 26 pruebas API: se comprueba delegación sin fechas, vigencia sin vencimiento automático, revocación que retira permisos y conserva Lead.
- Prueba funcional completa en Chromium PASS y 54 combinaciones de pantalla PASS; formulario sin campos de fecha.
- Migración de delegaciones comprobada en SQLite aislado: vigente pasa a manual, vencida/revocada no se reactiva; reinicio no duplica auditoría.
- Sintaxis JavaScript y compilación Python correctas. Mac/Safari pendientes.

## Backup completo v1.0.1

- Chromium: prueba funcional completa PASS, cero errores JavaScript; formulario sin fechas ni selección de Grupos y analítica de todos los Grupos del Manager.
- API: aprobación y rechazo de OT de otro Grupo del mismo Manager; inclusión automática de Grupo nuevo; bloqueo de registros de otro Manager, autoaprobación y revocación.
- Sintaxis JavaScript y compilación Python correctas. Mac/Safari no ejecutados.

## Intervalos de Guardia v1.0.2

- `tests/rules_browser.py`: PASS en Chromium a 1280×650, zoom nativo. Crear cinco intervalos, guardar mediante botón, recargar, reabrir, modificar, agregar, eliminar y guardar nuevamente; comparación exacta de todos los valores almacenados y recuperados. Cuerpo del modal sin desbordamiento.
- `tests/browser_smoke.py`: PASS, cero errores JavaScript; incluye semana con 13 intervalos, cruce de medianoche, domingo 24 horas, edición/eliminación y conservación de solicitudes previas.
- `tests/layout_smoke.py`: PASS, 54 combinaciones de pantalla y roles.
- 27 pruebas API PASS; sintaxis JavaScript y compilación Python correctas. Mac/Safari no ejecutados.
- En el diagnóstico no se reprodujo pérdida de persistencia: sí se reprodujo contenido fuera del área visible al añadir intervalos. Se corrigió la actualización de paginación y se comprobó el ciclo completo de guardado/reapertura.

## Claridad y revisión v1.0.3

- 28 pruebas API PASS, incluida reproducción exacta del periodo 26 sep–2 oct con regla desde 26 oct: rechazo con ambas fechas; solicitud desde 26 oct aceptada.
- `tests/browser_smoke.py` en Chromium PASS, cero errores JavaScript. Comprueba aviso de vigencia antes del envío, Aprobaciones con pendientes/todos los periodos y cambio Analítica↔Historial sin acciones duplicadas de aprobación.
- `tests/layout_smoke.py` en Chromium PASS: 57 combinaciones de pantalla, rol y vista, incluidas las tres dimensiones de Historial; cero errores JavaScript.
- Medición con CSS real: estado vacío centrado en todo el bloque del Manager (desviación 0 px), botones activos azules y deshabilitados grises.
- Sintaxis de ambos JavaScript y compilación Python correctas. No se ejecutó Mac/Safari.

## Organización directa v1.0.4

- 28 pruebas API PASS. Prueba funcional completa en Chromium PASS, cero errores JavaScript.
- `tests/layout_smoke.py`: PASS en 57 combinaciones de pantalla/vista/rol, con arrastre, cancelación y bloqueo por Timer activo.
- `tests/organization_browser.py`: PASS con SQLite aislado y 26 Grupos. Búsqueda por código, nombre sin acentos y Manager; salto entre Cuentas/páginas; resultados vacíos; Escape; teclado y ratón. Comprobación de modales y creación real a 1440×780, 1280×650 y 390×844, sin controles recortados.
- Sintaxis de app.js/layout.js y compilación Python correctas. Mac/Safari no ejecutados. Las capturas sólo contienen datos de prueba aislados.

## OT automática y diálogos v1.0.5

- 34 pruebas API PASS (incluye extensiones): tipo inferido según periodo aunque el cliente envíe el contrario; edición de programación pasada convierte a histórica y devuelve a revisión; periodo en curso rechazado.
- `tests/ot_browser.py` PASS en Chromium: diálogos de confirmación, código y resultados de acceso a 1440×780, 1280×650 y 390×844 sin desbordamiento del modal ni controles recortados; previsualización pasada/futura/en curso en navegador con otra zona horaria; guardado real de histórica sin selector de tipo.
- Usuarios MGR0001, SL0001 y 951357 creados y login API verificado con las contraseñas solicitadas. Repetir el inicializador conserva datos y hashes. Lead sin aprobación implícita; tablas operativas de la base de pruebas vacías.
- `tests/layout_smoke.py` PASS: 57 combinaciones de pantalla/rol/vista, arrastre y bloqueos por Timer.
- `tests/browser_smoke.py` completo PASS en Chromium, cero errores JavaScript; incluye recuperación, activación, Guardia, OT, aprobaciones, Excel, Claim/ADP, analítica y administración.
- Sintaxis de app.js/layout.js, compilación Python y sintaxis de iniciar_pruebas.command correctas. Mac/Safari no ejecutados.

### Extensiones y disponibilidad · pruebas ejecutadas

- `unittest discover -s tests -p 'test_*.py'`: **34 pruebas PASS**. Incluye rechazo, autorización por Manager/Lead delegado, bloqueo de otros Managers/Admin y autoaprobación, revocación de delegación, solicitudes duplicadas, cancelación al finalizar o dar de baja y continuidad si se autoriza antes del límite.
- Regresión de cálculo: 60 minutos antes de la pausa + 30 minutos después = **90 minutos OT**; una hora de espera no se factura como OT. Guardia de 360 minutos queda en **270 minutos netos**, no 210. Excel y analítica reconcilian.
- `tests/extensions_browser.py`: PASS en Chromium. Disponibilidad futura y habilitación al llegar el horario; dos Técnicos/Grupos simultáneos visibles para Manager; todas las páginas cerradas al límite y comprobación directa SQLite de pausa exacta, sin depender de otra petición API. Solicitud, autorización, reanudación y cierre mediante interfaz; dos segmentos y espera excluida.
- Prueba funcional completa `tests/browser_smoke.py` PASS y `tests/layout_smoke.py` PASS en **57 combinaciones** de pantalla/rol/vista; cero errores JavaScript.

- Si la pausa se recibe con un diálogo abierto, se conserva la captura y la vista pendiente se actualiza al cerrarlo; regresión comprobada mediante la interfaz.
