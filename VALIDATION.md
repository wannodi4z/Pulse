# Validación ejecutada · Operational Pulse 1.1.1

Fecha: 26 de octubre de 2026. Implementación nueva desde cero; no se declara equivalencia binaria ni preservación del código del ZIP antiguo.

## Entorno utilizado

- Linux x86_64, Python 3.12.14 y Chromium headless.
- Dependencias instaladas en un entorno virtual nuevo usando `requirements.txt` y `requirements-dev.txt`.
- Pruebas funcionales con SQLite temporal independiente. Las bases de prueba se eliminan al finalizar; no forman parte del ZIP.
- El navegador se ejecutó con el binario Chromium del paquete `@sparticuz/chromium` instalado mediante npm con comprobación de integridad. Se indicó mediante `PULSE_CHROMIUM_EXECUTABLE`. La descarga estándar de Playwright no estaba disponible por la política de red de esta máquina; no se deshabilitó verificación TLS ni se usó una simulación del DOM.

## Resultado

**8 pruebas automatizadas del backend: 8 aprobadas, 0 fallidas, 0 omitidas.** Ejecutadas de nuevo con las dependencias del entorno virtual recién creado.

| Prueba | Comportamiento verificado |
| --- | --- |
| `test_clean_bootstrap_and_reinitialization` | Sólo admin1/admin2 al crear la base; catálogos y operación vacíos; reiniciar conserva una Cuenta manual; el estado no expone hashes; acceso anónimo rechazado. |
| `test_hierarchy_ownership_cross_account_and_delete` | Varios Managers en una Cuenta; varios Grupos por Manager; Grupo ocupado rechazado para otro Manager; mezcla de Cuentas rechazada; Cuenta con Grupos protegida; Cuenta vacía eliminable; Manager no crea Cuentas. |
| `test_one_lead_moves_and_independent_delegation` | Un Lead por Grupo; movimiento a Grupo con Lead rechazado; Lead sin autoridad implícita; delegación con alcance explícito; autoaprobación bloqueada; Grupo fuera del alcance bloqueado; revocación conserva capacidad; quitar capacidad permite designar otro Lead. |
| `test_accounting_midnight_guard_net_unique_ot_and_excel` | Solicitudes de Guardia independientes; cobertura traslapada no duplica horas; OT exacta duplicada rechazada; OT traslapada cuenta una sola vez; resta sobre Guardia; división por medianoche; Excel real abierto con openpyxl y totales comprobados; filtro de tipo respetado. |
| `test_timer_emergency_documentation_reapproval_and_history` | Inicio inmediato; segundo Timer bloqueado; otro usuario no lo detiene; stop genera documentación pendiente; documentar y aprobar; editar reabre aprobación y excluye temporalmente las horas; auditoría de edición y aprobación visible al propietario. |
| `test_shared_planned_individual_participations` | Ventana compartida; dos participaciones diferentes; participación duplicada rechazada; dos timers individuales visibles al Manager; al detener, ambos registros vuelven a aprobación. |
| `test_activation_recovery_password_and_session_invalidation` | Activación de cuentas; recuperación y uso único del código; sesiones anteriores invalidadas; login con contraseña nueva; contraseña actual incorrecta rechazada; cambio de contraseña funcional. |
| `test_authorization_no_state_overwrite_and_external_origin` | Aislamiento entre Grupos; reportes ajenos rechazados; PUT global del estado no permitido; escritura desde origen externo bloqueada; cabeceras de protección; archivos de servidor/base no expuestos como contenido estático. |

Ejemplo numérico comprobado: Guardia de 22:00 a 06:00 y OT de 23:00 a 01:00 producen 2 horas OT y 6 horas de Guardia neta, repartidas entre dos días. Agregar OT traslapada de 00:30 a 02:00 produce 3 horas OT únicas y 5 horas de Guardia neta. Una segunda solicitud de Guardia sobre la misma cobertura conserva su ID sin duplicar el total.

## Navegador real

**`tests/browser_smoke.py`: PASS. Cero errores JavaScript capturados.** No se sustituyeron las llamadas al backend por mocks.

Recorrido ejecutado desde la interfaz:

1. Login de administrador.
2. Alta de Cuenta, tres Grupos y dos Managers.
3. Grupos físicamente anidados dentro de su Manager; sección de Grupos sin asignar antes de asignarlos; etiqueta multigrupo.
4. Alta de tres Técnicos en un Grupo y uno con capacidad Lead.
5. Selector Lead oculto para otro Técnico cuando ya existe un Lead; visible y seleccionado al editar al actual.
6. Salida de Organización hacia Panel, Administradores, Recuperación y Mi perfil; regreso a Organización; permanencia después del ciclo de sincronización y URL sin hash de navegación.
7. Eliminación de Cuenta con Grupos rechazada con mensaje visible.
8. Sin desbordamiento horizontal del documento en 1440×1000 y 390×844.
9. Activación e inicio de sesión reales para Manager, Técnico y Lead.
10. Búsqueda de Técnicos con filtrado y foco conservado.
11. Creación de regla y solicitud de Guardia.
12. Captura de OT histórica desde el formulario.
13. Inicio y detención de Timer de emergencia desde los botones.
14. Aprobación de Guardia y OT desde Tiempo del equipo.
15. Descarga real del XLSX generado.
16. Claim y ADP muestran las cuatro filas esperadas para el caso de medianoche; Lead mantiene Mi tiempo y no ve Tiempo del equipo sin delegación.

## Instalación, arranque y sintaxis

- `python -m venv .venv` y `python -m pip install -r requirements.txt`: instalación completada en entorno nuevo.
- `python -m pip install -r requirements-dev.txt`: completado.
- `python -m pip check`: sin dependencias rotas.
- `bash -n start.command`: aprobado.
- `bash start.command`: inició la aplicación con el intérprete del entorno virtual; comprobados health v1.0.1, acceso de admin2, estado operativo vacío y respuestas de HTML/JavaScript.
- `node --check static/app.js`: aprobado.
- Compilación de `server.py` y archivos Python de pruebas: aprobada.
- Inspección AST: una sola definición de `nav`, `content`, `app`, `render`, `bind`, `dashboard`, `timePage` y `teamTimePage`.
- Inspección del paquete: proyecto completo, sin base de datos usada, sesiones, datos demo, entorno virtual ni dependencias/binarios de navegador.

## Límites de esta validación

- No ejecutado en hardware macOS, Safari ni VS Code para Mac. Se incluyen comandos y configuración local para que el usuario lo pruebe allí.
- No desplegado en Internet. No se ejecutaron pruebas de carga mundial, de múltiples regiones ni de operación de producción.
- Excel fue generado, descargado y abierto con openpyxl; no se abrió Microsoft Excel para Mac en esta máquina ni se validó un formato corporativo externo de importación.
- Claim y ADP son guías locales de captura; no se conectaron servicios externos.
- La prueba visual responsive comprobó anchuras de documento y se inspeccionaron capturas de Panel y Organización. No equivale a una auditoría completa de accesibilidad ni de todos los navegadores.

## Revisión visual de la base v1.0.0

- Paleta revisada a azul, blanco y turquesa; iconos SVG y logotipo original de Kyndryl servidos localmente. Los recursos del logotipo cargaron correctamente en navegador real.
- Se verificó el cambio de versión en health, login, menú y créditos, sin modificar el esquema ni las reglas del backend.
- Los ocho tests funcionales del backend volvieron a pasar tras el cambio de versión.
- El recorrido de navegador incluye el apartado de autores desde login y sesión iniciada, además de las comprobaciones operativas existentes. Los créditos identifican a Samuel Alejandro Díaz Chávez y Francisco Cervantes Marquez.
- Se mantienen los límites de plataforma: pruebas en Linux/Chromium, sin ejecución física en macOS ni Safari.

## Validación de los modales v1.0.1

- Los ocho tests del backend volvieron a pasar. `server.py` sólo cambia el número de versión; el esquema y las reglas permanecen iguales.
- El recorrido real de navegador comprueba los modales a anchura de escritorio y móvil, foco inicial, mostrar/ocultar contraseña, indicadores de longitud/coincidencia, cierre con Escape y conservación de usuario entre solicitud y código.
- Se solicita recuperación de admin2 desde el login, admin1 emite un código en la interfaz y se restablece la contraseña desde el modal público. Se comprueba error por contraseñas distintas, error por código inválido y éxito con un código real; finalmente se inicia sesión con la nueva contraseña.
- Las activaciones de Manager, Técnico y Lead continúan probándose con sus códigos reales y la nueva pantalla de confirmación. Después se ejecutan los flujos operativos existentes.
- La validación continúa siendo en Linux/Chromium; macOS y Safari no se ejecutaron aquí.

## Ajuste de contraste v1.0.2

- Se oscurecieron únicamente colores de primer plano para textos, etiquetas, ayudas, placeholders y estados. La distribución y los tamaños no cambiaron.
- Las ayudas y textos secundarios de los modales se ajustaron a un contraste calculado de al menos 4.8:1 respecto al fondo de referencia claro `#f5f9ff`. Se conservaron los textos claros sobre superficies oscuras. Esta comprobación no equivale a una auditoría completa de accesibilidad de todas las combinaciones.
- Se inspeccionó la captura actualizada de activación y se repitió el recorrido funcional existente en Chromium, sin errores JavaScript.
- Sintaxis JavaScript y Python: correctas. El backend sólo cambia la versión; sus ocho tests de lógica pasaron en la entrega anterior y no se repitieron para este ajuste de color.

## Flujos v1.1.0

**Suite completa: 11 tests aprobados, 0 fallidos, 0 omitidos.** Se mantienen los ocho originales y se agregan:

- `test_multiple_weekday_intervals_full_sunday_and_net_guard`: guarda exactamente los trece intervalos del ejemplo (dos de lunes a sábado y domingo completo), obtiene 71 horas de cobertura semanal y 69 horas netas después de dos horas de OT totalmente contenidas en la cobertura. Valida datos de hora inválidos y forma de segmentos.
- `test_single_backup_atomic_replacement_and_history`: rechaza una segunda asignación, mantiene la primera ante una sustitución inválida, sustituye de forma explícita, verifica autoridad exclusiva del nuevo backup, conserva ambas filas y mantiene la capacidad Lead al revocar.
- `test_legacy_multiple_backups_never_grant_simultaneous_authority`: simula una base anterior con dos filas activas, conserva la información al inicializar, autoriza sólo la última y comprueba que revocar no reactive la anterior.

**Recorrido Chromium: PASS, cero errores JavaScript.** Además de los flujos anteriores:

1. Activa dos Leads de diferentes Grupos, asigna el primero desde su fila de Mi equipo y lo sustituye por el segundo sin abrir un dialog. Comprueba que sólo una fila siga vigente, las dos personas conserven capacidad Lead y revocar retire la asignación.
2. Captura desde la interfaz los trece segmentos semanales, agrega/quita un intervalo, selecciona domingo 24 horas, verifica el ancho del formulario en móvil y lee los segmentos reales guardados en SQLite a través del API.
3. Una sesión independiente de Técnico inicia un Timer y registra una OT de un periodo anterior. Desde el Panel del Manager se abre la tarjeta de timers mientras está seleccionado otro mes: el filtro pasa a Todos los periodos y se muestra la actividad real. El detalle muestra En curso y su contador.
4. La tarjeta de pendientes localiza la OT del periodo anterior; el Manager aprueba desde el detalle y la fila deja de aparecer en el filtro de pendientes. La sesión del Técnico detiene su propio Timer.
5. Continúan pasando guardias, OT histórica, emergencia, aprobación, descarga Excel, Claim, ADP, navegación, activación, recuperación y las comprobaciones existentes.

No se ejecutó esta versión en macOS físico ni Safari. Las pruebas usan bases temporales; no se reinicia la base manual del usuario.

## Acceso enfocado en OT y Guardias · v1.1.1

- Se actualizan los textos de login, Mi tiempo y Acerca del proyecto para describir control de OT y Guardias. Se retiran las referencias a comenzar una jornada.
- Se agrega el botón de mostrar/ocultar contraseña del login, reutilizando el controlador existente: la prueba real de navegador verifica ambos tipos de campo, el valor conservado, etiquetas accesibles y que el botón no envíe el formulario.
- La suite de navegador existente continúa con activación, recuperación, organización, reglas multintervalo, delegación inline, tarjetas, timers, aprobaciones, Excel, Claim y ADP. Resultado: PASS, sin errores JavaScript.
- Sintaxis JavaScript y Python verificadas. El backend sólo cambia el número de versión; los once tests de lógica pasaron en v1.1.0 y no se repitieron para este ajuste de texto y control visual.
