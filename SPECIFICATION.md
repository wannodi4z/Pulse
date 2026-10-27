# Operational Pulse 2.0.0 · especificación de la implementación nueva

## Alcance actual

Aplicación local para macOS y VS Code. HTML, CSS y JavaScript sin compilación, FastAPI y SQLite. El ZIP antiguo es referencia funcional únicamente. Esta versión usa su propio esquema y no necesita archivos de versiones anteriores. Interfaz en español de México, sin notificaciones ni datos operativos de muestra.

## Estructura organizacional

- Cuenta: código único y nombre, edición y eliminación sólo si no tiene Grupos ni Managers.
- Manager: persona con rol MANAGER, una Cuenta, cero Grupos mientras se configura y uno o más Grupos cuando se asignan. Los Grupos seleccionables son los de su Cuenta que estén libres o sean propios. Una selección multigrupo se presenta como `Multigrupo · N grupos`.
- Grupo: una Cuenta y, opcionalmente, un Manager de la misma Cuenta. Una columna de propietario evita asignaciones simultáneas a dos Managers.
- Técnico: persona con rol USER, un Grupo y una capacidad opcional `is_lead`. La restricción única de SQLite impide dos Leads en el mismo Grupo. Mover un Lead a un Grupo que tenga otro Lead se rechaza aunque se intente desmarcar la capacidad durante el movimiento.
- Jerarquía visual: Cuenta contiene bloques de Managers; cada Manager contiene sólo sus Grupos; cada Grupo contiene sus Técnicos. Los Grupos libres aparecen bajo `Grupos sin Manager`.
- Lead y Técnico comparten una identidad. La delegación temporal es una entidad independiente con Manager, Lead, alcance por Grupos, inicio, fin y revocación. No se permite autoaprobación.

## Navegación y estado

`nav()` construye el sidebar; `content()` decide todo el contenido central; `app()` construye el marco; `render()` pinta el estado; `bind()` registra una sola vez los controladores delegados. Cada una existe una sola vez. El único controlador de `data-page` cambia la variable `page`, carga el reporte necesario y ejecuta `render()`. No usa hash, páginas separadas ni redirecciones para Organización.

La lectura común se hace mediante `GET /api/state`. Las escrituras son transacciones específicas en el backend: no se permite reemplazar el estado global con `PUT /api/state`. La sincronización de cinco segundos no cambia `page`, no se ejecuta con formularios abiertos ni campos enfocados y conserva la búsqueda de Mi equipo. Los contadores de Timer se actualizan sin recrear la página cada segundo.

## Identidad y autorización

- Roles: ADMIN, MANAGER y USER. `is_lead` no es un rol adicional.
- Nuevas personas: pendientes de activación con código mostrado una sola vez. Activación define contraseña de al menos diez caracteres.
- ADMIN gestiona estructura, administradores y recuperación. Las aprobaciones operativas las realizan Manager y Lead delegado.
- MANAGER sólo ve y gestiona su alcance operativo. Lead delegado sólo recibe los Grupos especificados y durante la vigencia; permanece Técnico para Mi tiempo, Claim y ADP.
- Sesiones de ocho horas, almacenadas en SQLite, con cookie HttpOnly y SameSite estricto; Secure cuando se sirve por HTTPS. Cambio de contraseña o deshabilitación invalida sesiones. Limitación de intentos de login por identidad.
- Contraseñas y códigos nunca se devuelven en `/api/state`. Almacenamiento PBKDF2-HMAC-SHA256, salt aleatorio, 260 000 iteraciones.
- Recuperación: solicitud, validación por responsable distinto del solicitante, código emitido de quince minutos, uso único y anulación de sesiones.

## Tiempo

- OT: PLANNED, HISTORICAL o EMERGENCY. Estados de revisión: SUBMITTED, APPROVED, REJECTED, DOCUMENTATION. Ejecución: SCHEDULED, RUNNING o COMPLETED.
- PLANNED: aprobación de ventana individual antes de Timer; actual final se reenvía.
- Ventanas compartidas: creadas por Manager o Lead delegado. Una participación por Técnico y ventana, con Timer individual.
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
