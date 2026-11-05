# v1.1.0 · Operación y controles

## Traslados organizacionales

Admin abre **Movimientos → Traslados organizacionales → Preparar traslado**. Selecciona Manager o Lead, origen y destino. Arrastra la tarjeta a Destino o utiliza **Preparar propuesta**. El arrastre sólo prepara la propuesta: no mueve personas.

Para un Manager, cada Grupo puede acompañarlo o quedarse bajo otro Manager de la Cuenta de origen. El Lead puede acompañarlo o quedarse con otro Manager sin Lead. Los Técnicos siguen a su Grupo. Para un Lead, se elige un Manager destino sin otro Lead. Los responsables deben estar activos y vinculados a una jerarquía válida.

Revisa el impacto, indica el motivo y envía. DP y DPE de **origen y destino** reciben la propuesta en **Autorizaciones**. Si una persona representa ambos lados, decide una sola vez. Una negativa cierra el proceso. No basta con que Admin cree la propuesta: todas las autorizaciones deben estar aprobadas antes de que Admin pueda aplicarla.

La estructura y las delegaciones se verifican nuevamente al decidir y al aplicar. Un cambio relevante deja obsoleta la propuesta: cancélala y prepara otra. Los Timers activos del equipo afectado y traslados técnicos pendientes impiden aplicar. Las horas pendientes se muestran como impacto y siguen su revisión normal con el responsable vigente.

La aplicación es una transacción: conserva usuarios, contraseñas, sesiones, Técnicos, registros, autorizaciones de horas y trazabilidad de origen. Se retiran las delegaciones anteriores para que el nuevo responsable conceda las necesarias. El historial conserva su atribución original; el alcance actual se recalcula con la estructura vigente. Cambiar Cuenta/DPE del Manager o responsable del Lead mediante edición directa se bloquea; debe usarse este flujo. La vinculación inicial de un Manager antiguo sin DPE sigue permitida.

DP y DPE sólo autorizan el **traslado organizacional**. No aprueban OT/SB ni capturan tiempo.

## Tablero flexible

En **Personalizar tablero**, arrastra el tirador para mover una gráfica o su esquina para cambiar ancho y alto de forma continua. El contenido se ajusta al tamaño disponible. Las tarjetas se acomodan en huecos libres sin superponerse. Puedes ocultarlas, recuperarlas y guardar vistas por usuario/navegador. Se conservan las leyendas interactivas, los datos al pasar el cursor y la ampliación con resumen y tabla.

Se mantienen límites de legibilidad (220 px de ancho cuando caben, 180 px de alto) y el ancho disponible de la pantalla. El alto admite hasta 6000 px. En móvil se usa el ancho completo; no se sobrescribe el diseño de escritorio.

## Exportaciones y accesos

- **Analítica:** métricas y detalle de horas aprobadas; respeta su alcance, periodo y filtros.
- **Consulta de registros:** registros coincidentes y filtros, incluidos estados pendientes o rechazados cuando se seleccionan. No sustituye el respaldo personal ni el integral.
- **Actividad aprobada:** enlace y acceso de escritorio contextual. Requiere sesión, permisos y horario; abrir el enlace no registra horas. El usuario confirma el inicio del Timer.

## Actualización

Conserva la base y su `.key`. Haz un respaldo `.pulseorg` antes del mantenimiento. La nueva tabla de propuestas se crea al iniciar sin borrar datos. Una instalación nueva sólo tiene los dos Admin iniciales; no carga horas ni personas de prueba.

La configuración SMTP continúa sin enviar correo. La página móvil dedicada y SSO siguen pendientes para producción.
