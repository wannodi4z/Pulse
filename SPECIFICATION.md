# Operational Pulse 1.2.0 · especificación de la implementación nueva

## Alcance actual

Aplicación local para macOS y VS Code. HTML, CSS y JavaScript sin compilación, FastAPI y SQLite. El ZIP antiguo es referencia funcional únicamente. Esta versión usa su propio esquema y no necesita archivos de versiones anteriores. Interfaz en español de México, sin notificaciones ni datos operativos de muestra.

## Estructura organizacional

- Cuenta: código único y nombre, edición y eliminación sólo si no tiene Grupos ni Managers.
- Manager: persona con rol MANAGER, una Cuenta, cero Grupos mientras se configura y uno o más Grupos cuando se asignan. Los Grupos seleccionables son los de su Cuenta que estén libres o sean propios. Una selección multigrupo se presenta como `Multigrupo · N grupos`.
- Grupo: una Cuenta y, opcionalmente, un Manager de la misma Cuenta. Una columna de propietario evita asignaciones simultáneas a dos Managers.
- Técnico: persona con rol persistido USER, un Grupo, OT y Guardias.
- Lead: identidad USER con is_lead=1, manager_id y group_id=NULL. Es un backup directamente bajo el Manager, máximo uno vigente por Manager; conserva OT, Timer, historial, Claim y ADP propios y no crea Guardias. No es una capa entre Manager y Grupo. Admin asigna/cambia su Manager; cambio motivado, Timer detenido, registros intactos, sesiones invalidadas y delegación revocada.
- Presentación Admin: tarjetas de Cuentas y, al abrir una Cuenta, tarjetas de sus Managers con un espacio propio para el Lead. Grupos y Técnicos sólo se resumen como cantidades; no se despliega el árbol operativo. El modelo persistido de Grupos y Técnicos se conserva.
- Delegación: Manager a su Lead, todos los Grupos actuales/futuros, inicio automático, revocación manual. Sin autoaprobación; la OT del Lead la aprueba su Manager. Recuperación de Lead la atiende Admin; ningún Manager recibe esa solicitud. Analítica/Excel incluyen sus horas en el alcance del Manager y en la persona, sin asignarle un Grupo ficticio.
- Actualización: Leads anteriores se separan de su Grupo hacia el mismo Manager, manteniendo registros y origen. Designaciones heredadas múltiples se conservan para regularización por Admin; nuevas escrituras serializadas no crean un segundo backup.
- Catálogo por Cuenta: specialties con clave normalizada y nombre. Guardar un Grupo con especialidad nueva agrega una sugerencia al catálogo. Formulario plano sin plataforma obligatoria; códigos nuevos país–Cuenta–especialidad; códigos anteriores no se renombran automáticamente.

## Navegación y estado

`nav()` construye el sidebar; `content()` decide todo el contenido central; `app()` construye el marco; `render()` pinta el estado; `bind()` registra una sola vez los controladores delegados. Cada una existe una sola vez. El único controlador de `data-page` cambia la variable `page`, carga el reporte necesario y ejecuta `render()`. No usa hash, páginas separadas ni redirecciones para Organización.

La lectura común se hace mediante `GET /api/state`. Las escrituras son transacciones específicas en el backend: no se permite reemplazar el estado global con `PUT /api/state`. La sincronización de cinco segundos no cambia `page`, no se ejecuta con formularios abiertos ni campos enfocados y conserva la búsqueda de Mi equipo. Los contadores de Timer se actualizan sin recrear la página cada segundo.

## Identidad y autorización

- Roles: ADMIN, MANAGER y USER. `is_lead` no es un rol adicional.
- Nuevas personas: pendientes de activación con código mostrado una sola vez. Activación define contraseña de al menos diez caracteres.
- ADMIN es el único que crea y edita estructura y personas; gestiona recuperaciones de Managers, Leads, otros administradores y Técnicos sin Manager activo. Las aprobaciones operativas las realizan Manager y Lead delegado.
- MANAGER consulta a su equipo y gestiona tiempo, backup y recuperaciones de sus Técnicos; no modifica personas. Lead delegado cubre todos los Grupos actuales del Manager hasta revocación manual; permanece Técnico para Mi tiempo, Claim y ADP.
- Sesiones de ocho horas, almacenadas en SQLite, con cookie HttpOnly y SameSite estricto; Secure cuando se sirve por HTTPS. Cambio de contraseña o deshabilitación invalida sesiones. Limitación de intentos de login por identidad.
- Contraseñas y códigos nunca se devuelven en `/api/state`. Almacenamiento PBKDF2-HMAC-SHA256, salt aleatorio, 260 000 iteraciones.
- Recuperación: solicitud, validación por responsable distinto del solicitante, código emitido de quince minutos, uso único y anulación de sesiones.

## Tiempo

- OT: PLANNED, HISTORICAL o EMERGENCY. Estados de revisión: SUBMITTED, APPROVED, REJECTED, DOCUMENTATION. Ejecución: SCHEDULED, RUNNING o COMPLETED.
- PLANNED: aprobación de ventana individual antes de Timer; actual final se reenvía.
- El Manager y Lead delegado revisan y autorizan; no publican actividades. Cada Técnico solicita su propia OT programada. Se conservan las ventanas previas y sus participaciones individuales por compatibilidad histórica; la API rechaza nuevas publicaciones.
- HISTORICAL: intervalo ya terminado, referencia CHG/INC y envío a revisión.
- EMERGENCY: Timer inmediato, detener primero y documentar después.
- Un Timer activo por Técnico, garantizado por índice único en SQLite. Sólo su propietario puede detenerlo. El servidor fija el periodo real.
- Sólo el propietario edita OT; la edición aumenta revisión, invalida aprobación y registra auditoría. El periodo real no se altera.
- Guardia: solicitud independiente con copia inmutable de regla; reglas semanales con vigencia. La edición de una regla se realiza creando otra versión con nueva fecha de vigencia.
- Rechazo exige motivo y queda en auditoría. Los registros operativos no se borran desde la interfaz.
- Contabilidad compartida: unión de intervalos de OT aprobada real; unión de cobertura aprobada; resta de OT sobre cobertura; división en medianoche y límite mensual de zona operativa.
- Claim agrupa sábado–viernes y horas decimales. ADP agrupa domingo–sábado y duración HH:MM. No hay transmisión automática hacia sistemas externos.
- Excel incluye registros aprobados calculados por el mismo motor, respeta alcance y filtros de mes/Grupo/Técnico/tipo y agrega resumen. Los textos se protegen contra fórmulas de hoja de cálculo.

## Persistencia y entrega

SQLite normalizado, claves foráneas activas, transacciones de escritura y auditoría de acciones. Base nueva con sólo admin1/admin2. Reiniciar o instalar no vuelve a crear datos demo ni borra trabajo manual. Pruebas y capturas usan bases temporales que se destruyen al terminar. No se distribuyen bases, sesiones, entornos virtuales ni binarios de navegador en el ZIP.

La compatibilidad con macOS se prepara con comandos estándar Python, `start.command` y depuración VS Code. Las pruebas de esta entrega se realizan en Linux; macOS y Safari requieren validación en el equipo del usuario. La publicación en un servidor global está fuera del alcance de esta etapa local.

## Identidad visual de la base v1.0.0

Azul profundo para navegación, azul para acciones principales, blanco para superficies y turquesa para acentos. Iconos vectoriales y logotipo original de Kyndryl desde sus paquetes oficiales Shidoka, con licencias distribuidas. Créditos del proyecto en un modal propio accesible desde el login y el pie de todas las secciones. La numeración se reinicia sin restablecer la base ni cambiar las reglas operativas.

## Acceso: refinamiento v1.0.1

Los modales públicos usan un marco visual propio y accesible, dentro del mismo `dialog` y controlador de eventos de la aplicación. Activar y restablecer separan identidad/código y contraseña; la solicitud de recuperación explica el proceso sin revelar si una cuenta existe. El usuario se conserva durante las transiciones; no se guardan contraseñas ni códigos en el borrador del flujo. Se presentan errores dentro del formulario y resultados de éxito dentro del modal. Mostrar contraseñas no altera sus valores ni las reglas del servidor. No hay cambios en lógica operativa ni esquema de datos.

## Flujos operativos v1.1.0

Las reglas almacenan una lista de segmentos; se admiten días repetidos y cobertura 00:00–00:00 para 24 horas. La captura muestra un bloque por día, permite agregar/quitar intervalos y valida horas antes de guardar. El motor común de contabilidad no cambia.

La asignación de backup se captura dentro de Mi equipo y mantiene alcance y capacidad Lead independientes, inicia al guardar y permanece hasta revocación manual. El servidor impide una segunda asignación pendiente/activa salvo sustitución explícita; la revocación y nueva inserción comparten la transacción de escritura. Lecturas de bases antiguas eligen como máximo una delegación efectiva por Manager sin borrar registros. La revocación de una asignación vigente impide reactivar inadvertidamente una fila antigua.

Las tarjetas del Manager son botones con navegación contextual. El estado «En curso» y el periodo «Todos los periodos» permiten localizar timers aunque se esté consultando otro mes. Los filtros de tipo, Técnico y Grupo se conservan en la pantalla de revisión hasta que se cambian o se navega a otra sección. El Excel sigue correspondiendo a tiempo aprobado del mes seleccionado, tal como indica la pantalla. Las solicitudes concretas del Panel reutilizan el detalle y los endpoints de aprobación existentes.

## Analítica y separación de responsabilidades v1.0.0

`GET /api/analytics` y `/api/analytics.xlsx` requieren Manager o Lead con delegación efectiva. El conjunto de usuarios se obtiene exclusivamente de los Grupos bajo su alcance; la delegación cubre todos los Grupos actuales del Manager y nunca Grupos de otros Managers. Admin y Técnicos sin delegación reciben 403.

`GET /api/my-analytics` y `/api/my-analytics.xlsx` sólo admiten personas con rol USER, fijan el propietario desde la sesión y rechazan filtros de usuario o Grupo. Manager y Admin no usan esta ruta. Tanto JSON como Excel verifican autorización en cada solicitud.

El motor de contabilidad conserva sus cálculos e incorpora el tipo de captura a cada tramo diario. La analítica agrega esos mismos tramos, no las duraciones brutas de registros traslapados. Los totales por Grupo, usuario, tipo y día reconcilian; los usuarios con cero horas pueden aparecer como parte del alcance. Las horas pendientes o programadas sin ejecutar no se contabilizan. Se valida el mes AAAA-MM incluso si el valor está vacío. La agrupación usa el Grupo actual, no una reconstrucción histórica de membresías.

La administración organizacional de personas queda protegida por Admin en el endpoint de escritura, además de retirarse sus botones de Mi equipo. La edición del perfil propio no permite cambiar relaciones ni privilegios.

Las recuperaciones de Técnicos se asignan a su Manager activo; las de Managers/administradores y los casos sin Manager activo se asignan a Admin distinto del solicitante. Lead no tiene permisos de recuperación. La misma regla se usa para filtrar la bandeja, emitir y ver el código.

El código conserva su hash verificador y se agrega un valor cifrado con Fernet en una tabla separada. La clave local se crea con permisos 0600, permanece fuera de SQLite y no se entrega en el ZIP ni Git. Sólo se revela el valor a su responsable autorizado por un endpoint POST auditado. Ver no renueva vigencia; regenerar invalida el anterior; consumir elimina el valor cifrado e invalida sesiones anteriores. Las solicitudes abiertas duplicadas se evitan y los códigos de otras solicitudes del mismo usuario se invalidan al emitir/consumir. Los códigos de versiones previas sin valor cifrado requieren regeneración para consulta.


## Administración del ciclo de vida · v1.0.0

Sólo Admin crea, edita, transfiere, da de baja y reactiva personas. **Transferir y dar de baja son acciones independientes.** Manager gestiona tiempo y recuperaciones, sin editar la estructura.

- **Transferir Técnico activo:** en Organización, pulsa Transferir junto a la persona, elige un Grupo con Manager activo y explica el motivo. Conserva identidad, estado e historial. No se permite mover un Técnico con Timer en curso: primero debe detenerlo. Su sesión se invalida para aplicar el acceso nuevo; vuelve a entrar con su contraseña. La capacidad Lead se conserva si no genera un segundo backup para el Manager de destino; para cambiar al backup, Admin debe retirar primero la designación correspondiente.
- **Transferir Grupo activo:** pulsa Transferir en el Grupo. Elige otro Manager activo de la misma Cuenta. Conserva todos los integrantes, registros y timers de los Técnicos en ejecución. Revoca las delegaciones afectadas, sin desactivar a nadie. Si coinciden dos Leads bajo el destino, se rechaza toda la operación; Admin decide antes qué designación retirar.
- **Un Lead por Manager:** el técnico designado es el backup de ese Manager, incluso si administra varios Grupos. Designarlo no otorga aprobación. El Manager activa la delegación para todos sus Grupos y puede revocarla manualmente. Las bases anteriores con varios Leads no se borran ni corrigen silenciosamente: Organización muestra una advertencia y Admin debe retirar las designaciones adicionales. Las nuevas escrituras impiden crear el conflicto.
- **Baja de Manager:** revisa el impacto y asigna cada Grupo a otro Manager activo de la misma Cuenta. Si el reemplazo es nuevo, créalo y activa su acceso primero; el titular permanece activo hasta confirmar el traspaso. Se puede repartir el equipo entre varios Managers. Los Grupos y Técnicos conservan sus IDs e historial y los Técnicos continúan activos; sus timers siguen en ejecución. La operación completa ocurre en una sola transacción.
- **Baja de Técnico:** revisa los pendientes. Si tiene Timer activo, Admin debe autorizar su cierre en ese momento y completar la documentación de cualquier OT de emergencia pendiente. El tiempo ya realizado queda enviado a aprobación del responsable del Grupo. Las OT programadas individuales sin ejecutar se cancelan. Las Guardias aún no iniciadas se cancelan; las que ya iniciaron conservan cobertura hasta la hora de la baja, incluyendo cruces de medianoche. Claim, ADP, Excel y analítica usan ese mismo límite. No se elimina el historial.
- **Seguridad de la baja:** retira acceso, sesiones, activación y capacidad Lead, revoca delegaciones y cancela las recuperaciones propias. No permite la baja del Admin que ejecuta la acción ni del último Admin activo. Los códigos emitidos por el responsable saliente y los de Técnicos que cambian de Manager se invalidan y las solicitudes quedan pendientes para el nuevo responsable. Los códigos no se transfieren.
- **Reactivar:** requiere motivo y genera una activación nueva; la persona define una contraseña nueva. Conserva identidad e historial, pero no restaura Lead, delegaciones, Grupos del antiguo Manager, timers ni coberturas canceladas. Un Manager heredado en baja que aún tiene Grupos requiere regularizar primero el traspaso mediante la revisión de baja.
- **Revisión vigente:** la baja exige un resumen firmado por hash de la situación revisada. Si cambia el equipo o los pendientes, se rechaza con 409; cierra y vuelve a abrir la revisión. Motivos, movimientos, cierres y cambios de acceso quedan en auditoría.

El login dice **Planea. Trabaja. Controla.** Los diálogos se ampliaron, los formularios usan columnas en escritorio y muestran instrucciones. Las confirmaciones usan el diálogo de la aplicación. Los formularios extensos usan pasos y las listas se paginan.


### API administrativa del ciclo de vida

| Método / ruta | Función |
| --- | --- |
| `GET /api/admin/people/{id}/impact` | Vista consistente de Grupos, pendientes y huella `expected`; sólo Admin. |
| `POST /api/admin/people/{id}/offboard` | Motivo, confirmación, huella revisada, mapa `transfers`, autorización `stop_timers` y documentación; operación atómica. |
| `POST /api/admin/people/{id}/reactivate` | Motivo; genera código de activación nuevo. |
| `PUT /api/people/{id}` | Edita o transfiere con `group_id` y `transfer_reason`; no permite cambiar estado de acceso directamente. |
| `PUT /api/groups/{id}` | Edita o transfiere con `manager_id` y `transfer_reason`; valida Cuenta, Manager activo para equipos y Lead único. |


## Presentación y reglas editables v1.0.0

`static/layout.js` controla exclusivamente vistas, paginación y pasos de formularios a escala nativa. Conserva los nodos e inputs y usa delegación de eventos de la aplicación. No modifica datos de OT, horas, aprobaciones, sesiones ni SQLite. La ruta central y los controladores de negocio siguen siendo únicos en app.js. Los cambios de tamaño recalculan la paginación; el contenido se recorre mediante controles visibles, sin depender de scroll de página o diálogo.

`PUT /api/rules/{id}` valida los mismos intervalos que la creación y verifica propiedad Manager dentro de la transacción. `DELETE /api/rules/{id}` verifica rol y propiedad y elimina únicamente la plantilla; registra su contenido anterior en auditoría. Los snapshots JSON de Guards no se actualizan en ninguna de estas operaciones.


### Composición de la interfaz v1.0.0

`PulseLayout.compose` agrupa elementos relacionados por ruta: resumen/estructura de Organización, filtros/registros de Tiempo del equipo, acciones/totales de Mi tiempo, resúmenes/semanas de captura y métricas/gráficas/criterios de analítica. La barra de contenido se oculta cuando sólo hay una tarea o Cuenta. La paginación de tablas calcula el espacio real ocupado por títulos, cabeceras y controles; no asigna una pantalla individual a cada bloque informativo. El contador se reinicia a v1.0.0 sin migraciones de borrado ni cambios del esquema de datos.


### Presentación y acciones v1.0.1

Los menús de entidades conservan los identificadores data-action y los controladores existentes. Se montan sobre el documento con posicionamiento fijo, ajustado a los límites del viewport, para evitar recortes por los contenedores de tarjetas. Se cierran al navegar, volver a renderizar, redimensionar, pulsar Escape o hacer clic fuera. La navegación de teclado recorre los botones y Escape devuelve foco al disparador. Las acciones finales pasan por las mismas validaciones y confirmaciones de la aplicación. El servidor sólo cambia su constante de versión en esta entrega.


### Interfaz Enterprise luminosa v1.1.0

La estructura de navegación se renueva en nav() y app(), conservando una única implementación por función y los mismos data-page/data-action. El sidebar blanco contiene marca de producto, funciones por rol, Configuración y Acerca del proyecto; Kyndryl pasa a la cabecera corporativa. static/design.css es la fuente visual de esta dirección y se carga después de los contratos de estructura de app.css. No se añaden frameworks, dependencias ni servicios externos.

Las opciones de los menús usan los mismos controladores y un icono local. La acción principal de una Cuenta sin Manager es su incorporación; la creación de Grupos permanece disponible en el menú. Los formularios, tablas y acceso utilizan el mismo lenguaje visual. El backend sólo cambia la constante VERSION, sin cambios en el esquema o la lógica de negocio.


### Transferencia interactiva v1.2.0

`POST /api/admin/people/{id}/transfer` requiere Admin y recibe `expected_group_id`, `group_id` y `transfer_reason`. La operación reutiliza la validación transaccional de personas, leyendo la identidad vigente bajo el mismo bloqueo. Los campos de perfil enviados por el navegador no se usan en este endpoint. Origen obsoleto devuelve 409; Timer activo, ausencia de motivo, acceso en baja o conflicto Lead se rechazan sin escrituras parciales. Los permisos operativos de Manager y Lead no autorizan esta ruta.

El arrastre HTML nativo se limita a Técnicos de Organización y no modifica el estado ni el DOM de asignación antes de confirmar. Durante la interacción se pausa la actualización silenciosa para mantener los elementos estables. Al cancelar, salir o redimensionar se limpian los indicadores de arrastre. Mover ofrece una alternativa de teclado. Los mismos data-action abren las ediciones directas de entidades desde sus nombres.

### Separación de revisión y consulta v1.0.3

La ruta interna teamTime se presenta como Aprobaciones y abre pendientes de todos los periodos. La ruta analytics se presenta como Tiempo del equipo e integra vistas Analítica e Historial. El historial reutiliza filtros y detalle sin duplicar las acciones de decisión; las autorizaciones del backend permanecen iguales. La solicitud de Guardia compara effective_from contra start_date, conserva validación en servidor y comunica las fechas explícitamente en interfaz.

### Localizador de Grupos v1.0.4

Búsqueda local sobre el estado autorizado de Admin, sin endpoints nuevos. Coincide por tokens sin distinción de acentos en nombre/código de Grupo, Cuenta y nombre/Employee ID del Manager. Hasta cinco resultados visibles según el espacio disponible; si hay más se solicita precisar el texto. Al seleccionar se usa PulseLayout.reveal para abrir Cuenta, Manager y página de Grupos conservando la estructura. Soporta flechas, Enter y Escape y no vuelve a renderizar la aplicación al escribir.

### OT automática y pruebas explícitas v1.0.5

El servidor usa su reloj y fechas conscientes de zona para clasificar nuevos periodos no emergentes y programaciones sin ejecutar que se editan. El cliente sólo anticipa el resultado; no se confía en capture_type enviado por cliente para elegir histórica/programada. Un periodo en curso no se trata como tiempo completado. Los registros ejecutados por Timer conservan sus intervalos reales.

Los usuarios de pruebas únicamente se crean mediante iniciar_pruebas.command/scripts/prepare_test_users.py en una SQLite separada. El inicio normal sigue conteniendo sólo los dos administradores; no se modifican los datos manuales ni se activa autoridad implícita para el Lead.

### Ventanas y extensiones de OT programada

`ot_extensions` conserva fin anterior, fin solicitado, motivo, solicitante y decisión; índice único para una solicitud SUBMITTED por OT. La autorización usa el alcance actual del Manager/Lead delegado y bloquea autoaprobación, Admin operativo, usuarios en baja y decisiones duplicadas o ventanas obsoletas. El nuevo límite debe ser futuro, posterior al anterior y no superar 31 días desde el inicio original.

El ciclo del Timer planificado es SCHEDULED → RUNNING → PAUSED → RUNNING, o COMPLETED al finalizar. Un reloj de servidor y la reconciliación transaccional cierran el tramo exactamente en scheduled_end. Una extensión autorizada actualiza ese límite, pero no reanuda una OT pausada. Se conserva la primera fecha de inicio y cada tramo en timers; la contabilidad une los tramos cerrados, no el intervalo exterior. Históricas y emergencias conservan su cálculo previo. El tiempo real completo requiere aprobación posterior.

API: POST /api/overtime/{id}/extensions, POST /api/extensions/{id}/decision, DELETE /api/extensions/{id}, POST /api/overtime/{id}/finish. El estado filtra extensiones y segmentos por la autoridad vigente. Detener/finalizar revoca solicitudes pendientes; una baja administrativa conserva el trabajo pausado y cierra solicitudes.


## Estándar internacional y orden de administración · v1.1.0

La Cuenta se crea primero; contiene varios Managers. Cada Manager contiene Grupos por especialidad y cada Grupo contiene Técnicos. País es un atributo de la Cuenta, no una capa adicional de navegación. Plataforma clasifica el Grupo, no añade una capa entre Manager y Técnico. Un Manager puede administrar especialidades de Mainframe y OPEN / Distribuidos de su misma Cuenta.

Varias Cuentas pueden pertenecer al mismo país. Código de Cuenta: `MX-BNTE`. Código de Grupo: `MX-BNTE-MF-ZOS`, `MX-BNTE-MF-CICS-MQ`, `MX-BNTE-MF-DB2`, `MX-BNTE-OPEN-LINUX`, `MX-BNTE-OPEN-UNIX`, `MX-BNTE-OPEN-ORACLE`. El sistema genera el código y añade `-02`, `-03` si se repite la especialidad. Se permiten especialidades adicionales.

Las claves, IDs, relaciones e historial anteriores se conservan; las claves estandarizadas son metadatos adicionales de las entidades existentes. Un cambio de Manager dentro de la misma Cuenta no cambia el código de sus Grupos.

## Consulta unificada y cronología personal · v1.1.0

Analítica une historial y métricas: filtros, búsqueda y selección de meses determinan registros y horas aprobadas. Comparaciones de hasta 24 meses y Excel usan idénticos criterios. Pendientes/rechazados no aportan horas. Aprobaciones sólo muestra solicitudes/extensiones pendientes. El acceso al equipo requiere Manager o Lead delegado; el Técnico sólo consulta sus registros.

Mi tiempo ordena OT por inicio real o programado, no por creación. Capturas históricas tardías se insertan cronológicamente y conservan fecha de captura. Incluye periodos que cruzan el mes seleccionado. Usa las mismas funciones de detalle, Timer, aprobación y extensión existentes; no crea registros ni cuenta tiempo programado como trabajado. Actualiza después de guardar y con la sincronización habitual de estado.

## Solicitudes de cambio y continuidad del Técnico · v1.1.0

Manager solicita Grupo/especialidad de destino y motivo para un Técnico propio. No se expone el directorio ajeno ni se modifica la persona al solicitar. Admin revisa todas las solicitudes desde Organización y ejecuta usando el traslado existente o rechaza con motivo. La ejecución valida estado pendiente, Técnico/origen vigentes, Timer detenido, destino con Manager activo y Lead único; resolución y traslado se guardan en una transacción. Los Managers sólo ven sus solicitudes.

Los registros permanecen ligados al mismo user_id. Nueva autoridad: responsable actual del Técnico; el anterior pierde acceso. OT/Guardias mantienen datos, aprobaciones y tramos. record_origins conserva el contexto en creación; registros anteriores lo incorporan al trasladarse con marca inferred, sin afirmar un origen que no se había registrado. Detalle muestra la referencia de origen; analítica agrega por pertenencia actual. No se reescriben los tiempos ni snapshots de las reglas de Guardia.

## Distribución de pruebas v1.1.2

El fixture SQLite contiene únicamente los dos administradores, los tres accesos de ejemplo activos, Banorte y seis Grupos, además de auditoría de configuración. No hay sesiones, registros de tiempo ni delegaciones. Se copia atómicamente a la base predeterminada sólo si ésta no existe y no se definió PULSE_DB_PATH. Una base existente gana incluso si otra instancia la creó durante el inicio. Nunca se reponen contraseñas ni se restauran ejemplos en reinicios. El modo limpio sigue disponible con ruta explícita o sin fixtures.

## Organización y ejemplos v1.1.3

Vista inicial de cuatro Grupos en 2×2, probada a 1440×780 y 1280×650. Detalle accesible desde el conteo de personas o selector de densidad. Lead en cabecera de Manager con acción directa Agregar/Editar, fuera de la cuadrícula de Grupos. Recuento de Técnicos excluye Leads.

Organizador Admin con origen/destino, búsqueda de personas, arrastre nativo y alternativa por botones, cambios temporales deshacibles y revisión con motivo. POST /api/admin/organization/transfers valida de uno a cien movimientos únicos en una transacción SQLite: Admin, Técnico vigente sin capacidad Lead, origen actual, destino con Manager activo y sin Timer en ejecución. Si falla uno no se aplica ninguno. Preserva los registros y sus snapshots, actualiza pertenencia, revoca autoridad anterior, reabre recuperaciones cuando cambia responsable, invalida sesiones y registra auditoría por persona y lote. No decide automáticamente solicitudes administrativas anteriores; una solicitud desactualizada se revisa/rechaza explícitamente.

La base de ejemplo contiene Banorte y Acme México, un Manager y un Lead directo por Cuenta, doce Técnicos y nueve Grupos. 951357 corresponde a Samuel Alejandro Díaz Chávez. scripts/prepare_example_teams.py es un configurador explícito para instalaciones anteriores, usado por configurar_banorte.command. El inicio ordinario sólo copia el fixture si no existe la base predeterminada y no se especificó PULSE_DB_PATH.

## Altas visibles y ejemplos v1.1.4

Dos Cuentas de ejemplo, dos Managers por Cuenta, un Lead directo por Manager: cuatro Managers, cuatro Leads, doce Técnicos y quince Grupos. No hay límite de dos Managers en código: es sólo la composición del fixture. Credenciales originales conservadas; nuevos MGR0003/SL0003 en Banorte y MGR0004/SL0004 en Acme.

Agregar Manager y Agregar Grupo visibles en Cuenta. Selector Manager/equipo sincronizado con la navegación interna y búsqueda; no hay otra página ni otra sesión. Cabecera de Manager con Editar Manager y Agregar Grupo contextual; Lead sin elipsis, con Editar Lead, o Agregar Lead si está libre. Crear Manager/Lead revela automáticamente el bloque correspondiente. El alta contextual de Grupo preselecciona Cuenta y Manager correctos. La unicidad de Lead sigue validada por servidor.

## Perfil y Panel administrativo · v1.2.0

Admin crea, edita y elimina Cuentas vacías; crea, edita y da de baja Administradores, Managers y Leads. Las bajas conservan identidad e historial; las de Manager requieren reasignación de dependencias. Se impide la baja de la propia cuenta y del último Admin activo. Los Leads dados de baja se consultan en el archivo de su Manager; la reactivación requiere disponibilidad del responsable y de su plaza de Lead.

Cuatro accesos visibles en el sidebar: Panel, Cuentas, Administradores y Recuperación de acceso. Panel: totales generales de Cuentas registradas, Managers activos, Leads activos y recuperaciones pendientes/vencidas. Distribución por Cuenta con gráfica de barras y tabla (Managers activos, Leads activos y Managers activos sin Lead); la búsqueda y el país filtran ambas vistas. Pendientes accionables: Managers vigentes sin Lead, Cuentas sin Manager vigente, accesos administrativos por activar y recuperaciones. Cada Cuenta puede abrirse desde tabla, gráfica o tarjetas. Los formularios administrativos no cambian Grupos al guardar sólo la identidad de un Manager: omitir group_ids conserva la asignación existente.

La recuperación de Admin, Manager y Lead se asigna exclusivamente a Admin, sin autoemisión ni autoconsulta de códigos. Los Técnicos mantienen su flujo anterior. El cambio del perfil Manager y el kanban de Técnicos no forman parte de esta entrega del perfil Admin. Las herramientas previas de mantenimiento y los registros operativos se conservan.
