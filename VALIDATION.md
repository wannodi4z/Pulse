# Validación ejecutada · Operational Pulse 1.0.0

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
- `bash start.command`: inició la aplicación con el intérprete del entorno virtual; comprobados health v1.0.0, acceso de admin2, estado operativo vacío y respuestas de HTML/JavaScript.
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
