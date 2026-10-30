## v1.0.20

- Reordenar gráficas desde Personalizar tablero mediante asa de arrastre o flechas del teclado. Destino resaltado, Escape cancela, orden persistente por usuario/navegador.
- Conserva tamaños y visibilidad anteriores, modales ampliados y selección de leyendas. Restaurar diseño recupera también el orden original.

# v1.0.11 · Analítica del Manager

- Tabla visible de OT/SB por Grupo, OT total y conteos por tipo, con desglose por Técnico.
- Ranking de más/menos horas por total aprobado, OT o SB, con ceros y filtros compartidos.
- Participación por vínculo real de actividad: inscripción, Timer, tiempos y detalle individual; alcance y delegación verificados en el servidor.
- Comparativa mensual con desglose por tipo de OT. La búsqueda respeta el periodo elegido.
- Diseño original v1.0.10 conservado; experimentos visuales excluidos del ZIP estable.

# v1.0.10 · Organización y respaldo propio

- Backend y frontend separados físicamente; entrada server:app, comandos Mac, rutas web y datos existentes compatibles.
- Documentación técnica en docs/ y mapa de arquitectura vigente.
- Descarga personal .pulse separada del Excel .xlsx de aprobados; recuperación retrocompatible, con revisión del Manager.
- ZIP sin bases personales, claves, entornos ni archivos temporales.

# Historial de versiones

La entrega vigente es la primera entrada. Las versiones repetidas en entradas antiguas corresponden a reinicios de numeración solicitados durante el diseño.

## v1.1.4 · 28 de octubre de 2026

- Corrige los ejemplos a dos Managers por Cuenta: cuatro Managers y cuatro Leads, manteniendo los tres accesos originales y a Samuel Alejandro Díaz Chávez como 951357.
- Agregar Manager siempre visible en Cuenta; selector directo de Manager, nombres de Lead completos y botones Editar Manager/Editar Lead diferenciados y alineados.
- Agregar Lead visible en Managers sin backup; al crear una persona se abre su bloque. Agregar Grupo desde Manager preselecciona correctamente su propietario.
- Probada la creación de un tercer Manager y su Lead para verificar que dos Managers es sólo un ejemplo, no un límite.

## v1.1.3 · 28 de octubre de 2026

- Ejemplos ampliados a dos Cuentas, dos Managers, sus dos Leads, doce Técnicos y nueve Grupos; 951357 es Samuel Alejandro Díaz Chávez. Se conservan los tres accesos originales.
- Organización muestra cuatro Grupos en 2×2, con vista detallada disponible. Lead en cabecera del Manager, con Agregar/Editar explícitos.
- Organizador por arrastres con dos Grupos a la vista, búsqueda, alternativa por botones, deshacer, cancelar y revisión de varios movimientos con motivo. Aplicación atómica por Admin, preservando OT/Guardias/historial y validando Timers, permisos y origen vigente.

## v1.1.2 · 28 de octubre de 2026

- ZIP de pruebas con Banorte, seis Grupos y los tres usuarios solicitados ya activos. El primer inicio prepara la base de ejemplo automáticamente sólo si falta la base por defecto; no requiere configurador aparte.
- Una base existente y las rutas PULSE_DB_PATH explícitas nunca se sustituyen. Reiniciar conserva cambios de contraseña, usuarios y datos manuales. La base incluida no tiene sesiones, OT, Guardias, Timers ni delegaciones.

## v1.1.1 · 28 de octubre de 2026

- Lead directamente bajo el Manager, sin Grupo, con OT propia y sin nuevas Guardias. Delegación completa del equipo sin autoaprobación; historial y designaciones anteriores conservados al actualizar.
- Alta/edición/traslado/baja/reactivación del Lead con validaciones y sesiones/permisos actualizados; baja de Manager contempla destino para el backup.
- Catálogo de especialidades por Cuenta: búsqueda y captura manual desde Nuevo Grupo, sin campo Plataforma obligatorio. Códigos nuevos automáticos sin cambiar los anteriores.
- Modales de Grupo y solicitudes vacías más compactos. Configurador Banorte conserva los tres accesos solicitados activos con el nuevo modelo.

## v1.1.0 · 28 de octubre de 2026

- Cuenta primero: Managers dentro de la Cuenta, Grupos por especialidad y Técnicos dentro de cada Grupo. País es metadato de Cuenta; Mainframe y OPEN / Distribuidos clasifican Grupos. Códigos automáticos y consecutivos sin borrar claves anteriores ni historial.
- Configurador explícito de Banorte en la base principal: tres accesos solicitados activos y seis Grupos de prueba; conserva datos existentes y cancela ante conflictos de pertenencia.
- Analítica unificada con registros, búsqueda, totales de los resultados, comparación de varios meses y Excel equivalente. Aprobaciones sólo contiene decisiones pendientes.
- Solicitudes de traslado de Manager a Admin, resolución y movimiento atómicos; OT y Guardias siguen al Técnico con trazabilidad del origen, sesiones y delegaciones actualizadas.
- Línea de tiempo personal en Mi tiempo: orden de actividad, capturas históricas insertadas en su fecha real y programación futura con disponibilidad de Timer.

## v1.0.5 · 28 de octubre de 2026

- Confirmaciones, activación/recuperación y resultados de acceso con tamaño compacto; formularios breves de Guardia y Acerca del proyecto con ancho intermedio.
- OT sin selector de tipo: servidor clasifica periodos finalizados como históricos y futuros como programados. Periodos en curso requieren Timer; se conserva la aprobación y la documentación. Al editar una programación sin ejecutar se recalcula el tipo según las fechas corregidas.
- Programadas futuras indican cuándo estará disponible el Timer. El Manager ve Técnico, Employee ID, Grupo y actividad de todos sus Timers activos.
- Extensiones de OT: solicitud motivada, autorización/rechazo por Manager o Lead delegado, pausa automática exacta al fin autorizado y reanudación manual. Si se autoriza antes del límite, el mismo Timer continúa.
- El registro conserva los tramos y excluye la espera de OT, Guardia neta, analítica, Excel, Claim y ADP. Finalizar cancela las extensiones pendientes y envía sólo el trabajo real a revisión.
- Modo de pruebas explícito y separado con MGR0001, SL0001 y 951357 activos; se conserva la base principal y no se generan registros operativos ni delegaciones.


## v1.0.4 · 28 de octubre de 2026

- Buscador de Grupos por nombre, código, Cuenta y Manager, con resultados directos, búsqueda sin acentos y navegación con teclado. Abre la Cuenta y las páginas necesarias y resalta el Grupo sin alterar su jerarquía.
- Modales de Cuenta y Grupo proporcionados al contenido, con contexto breve, identidad en una fila y acciones explícitas de crear/guardar.
- Mantiene paginación, arrastre de Técnicos, validaciones y permisos de Admin.


## v1.0.3 · 28 de octubre de 2026

- Solicitudes de Guardia: fecha mínima y explicación de vigencia según el inicio solicitado; mensaje de API distingue regla ajena y periodo anterior a vigencia.
- Estado Sin Grupos asignados centrado en todo el bloque del Manager.
- Anterior/Siguiente habilitados en azul; deshabilitados en gris.
- Aprobaciones abre los pendientes de todos los periodos. Tiempo del equipo reúne Analítica e Historial con filtros, detalle y exportación; el historial no duplica botones de aprobación.


## v1.0.2 · 27 de octubre de 2026

- Editor de Guardia: reconstruye la paginación al agregar, quitar o habilitar intervalos; mantiene accesible la configuración sin ocultar filas nuevas.
- Guardado explícito de todos los días habilitados y sus intervalos, incluidos los que están en otra página del editor.
- Indicadores de cobertura por día y resumen semanal en tarjetas; respeta los valores al reabrir la regla.


## v1.0.1 · 27 de octubre de 2026

- El Lead delegado cubre automáticamente todos los Grupos actuales de su Manager, no sólo su Grupo. Se elimina la selección de alcance.
- Autoriza y rechaza OT del equipo, sin autoaprobación ni autoridad sobre otros Managers. La delegación continúa hasta revocación manual.
- Correcciones incrementan v1.0.x; el salto a v1.1.x requiere indicación del usuario.


## v1.0.0 · estabilización · 27 de octubre de 2026

- Versión fijada en v1.0.0 por solicitud del usuario hasta autorización expresa para pasar a v1.1.x.
- Delegación inmediata sin fechas: permanece hasta revocación manual. Se conserva el alcance, Lead independiente y un backup por Manager.
- Las delegaciones antiguas actualmente efectivas pasan a revocación manual con auditoría; las vencidas o revocadas no se reactivan.


## v1.2.4 · 27 de octubre de 2026

- Menús de acciones más amplios y con mayor espacio interior; etiquetas largas se ajustan sin tocar el borde y el menú respeta el ancho de pantallas pequeñas.


## v1.2.3 · 27 de octubre de 2026

- Separación de 14 px entre las tarjetas de Grupos y su barra de paginación.


## v1.2.2 · 27 de octubre de 2026

- Retirada la programación de actividades del panel del responsable y bloqueada su creación en API. Cada Técnico solicita su propia OT programada; el responsable revisa y autoriza. Se conservan las publicaciones y participaciones anteriores.


## v1.2.1 · 27 de octubre de 2026

- Cabecera con avatar, nombre, rol e identificador dentro de un único botón de usuario.
- “Programar actividad” sustituye “OT compartida”: el responsable publica la actividad del Grupo; cada Técnico conserva su participación y Timer, con revisión del tiempo real. No se reclasifica como emergente.


## v1.2.0 · 27 de octubre de 2026

- Organización interactiva: Grupos lado a lado y Técnicos que se pueden arrastrar a otro Grupo. Destinos alternativos disponibles durante el arrastre y mediante Mover.
- Acceso directo a edición desde el nombre de la Cuenta, Manager, Grupo y tarjeta del Técnico.
- Traslado con modal contextual: identidad, origen, destino y motivo rápido. Soltar no guarda; confirmar realiza la transferencia. Cancelar conserva la asignación original.
- Nueva operación Admin de traslado con lectura de perfil bajo bloqueo de escritura y comprobación del Grupo de origen; evita sobrescribir datos recientes o trasladar desde una asignación obsoleta.
- Conserva validaciones de Timer activo, Manager activo, Lead único por Manager, permisos, sesiones y delegaciones.
- Diálogos con cabecera contextual y controles consistentes; ajuste a 100% comprobado en ventanas de laptop.


## v1.1.0 · 27 de octubre de 2026

- Nueva interfaz Enterprise luminosa: sidebar blanco y compacto, navegación azul profundo con acentos turquesa y marca Kyndryl en la cabecera corporativa.
- Identidad, cabecera, estados, tablas, menús, acceso y diálogos rediseñados con una hoja visual dedicada: static/design.css.
- Jerarquía organizativa más ligera: Cuenta como contenedor, Managers sobre fondo blanco y Grupos con guía de relación y acento suave.
- Menús de acciones en lista con iconos y sin botones enmarcados; se conservan foco, flechas, Escape y confirmaciones.
- Cuenta nueva: guía breve de incorporación; Agregar Manager es la acción principal inicial. Los Grupos sin Manager siguen pudiendo crearse desde el menú.
- Se conserva SQLite, permisos, recuperación, reglas de Guardia, OT, timers, aprobaciones, analítica, Claim/ADP y Excel. Backend sin cambios de lógica en esta entrega.


## v1.0.1 · 26 de octubre de 2026

- Acabados de interfaz: niveles de Cuenta, Manager y Grupo con superficies, contraste, tipografía, bordes y acentos diferenciados; tablas, formularios, navegación y botones con el mismo lenguaje visual.
- Acciones principales visibles; transferencias, bajas y eliminación en menús contextuales. Menús anclados al elemento, dentro del viewport, con foco, flechas, Escape y cierre exterior.
- Se conservan las mismas acciones y permisos, la composición de información útil y el trabajo al 100% de zoom.
- La lista de Técnicos aprovecha el espacio que queda disponible tras seleccionar un Manager, reduciendo paginaciones innecesarias.
- Movimiento reducido respetado mediante prefers-reduced-motion.


## v1.0.0 · nueva base de versiones · 26 de octubre de 2026

Por solicitud de Samuel, el contador vuelve a v1.0.0. Este reinicio identifica la nueva entrega; conserva los datos, accesos y funciones existentes. Las entradas anteriores quedan como historial de trabajo.

- Resumen de Organización integrado con las Cuentas; una Cuenta abre directamente su estructura y no un resumen vacío.
- Indicadores, filtros y ayudas comparten contexto con sus registros; secciones de contenido sólo para tareas diferenciadas.
- Panel de Admin con Cuentas que se pueden abrir y tareas de recuperación/asignación, sustituyendo la bienvenida decorativa y los pasos redundantes.
- Marca Kyndryl integrada junto a Operational Pulse; versión sólo en el pie principal.
- Configuración usa engranaje oficial Shidoka; Organización conserva el icono de jerarquía.
- Se mantiene el trabajo al 100%, la paginación de listas extensas, los formularios por pasos y el historial operativo.


## v1.4.0 · 26 de octubre de 2026

- Páginas organizadas en vistas y listas/tablas paginadas para trabajar al 100% sin desplazamiento de página.
- Formularios extensos divididos en pasos, con valores preservados y validación antes de avanzar o enviar.
- Sidebar simplificado: operación principal, configuración agrupada y acciones personales en el menú superior.
- Editar y eliminar reglas de Guardia propias; solicitudes existentes y sus cálculos conservados mediante snapshots.
- Pruebas nuevas de viewport con datos reales para Admin, Manager y Técnico y de integridad al editar/eliminar reglas.


## v1.3.1 · 26 de octubre de 2026

- Distribución de diálogos a zoom nativo 100%, sin escalado artificial: controles de 15 px, etiquetas de 14 px y espaciado reducido.
- Reglas de Guardia organizadas por selector de día, manteniendo la semana completa al guardar.
- Cabecera y acciones siempre visibles; sólo el contenido puede desplazarse en casos extensos.
- Baja de Manager con transferencias a la izquierda, reemplazo y motivo a la derecha; botón de crear separado de Confirmar/Cancelar.
- Acciones de Organización ordenadas en una fila propia, con tamaños de clic y separación consistentes.


## v1.3.0 · 26 de octubre de 2026

- Un Lead por Manager entre todos sus Grupos; delegación independiente, conflictos de transferencias rechazados y advertencia para datos heredados.
- Transferencias de Técnicos y Grupos activos desde Organización, con motivo y trazabilidad.
- Baja revisada y atómica: traspaso de Grupos a Managers activos, cierre documentado de Timer propio, límite de Guardias, cancelación de compromisos futuros y revocación de acceso/códigos/delegaciones.
- Reactivación mediante código nuevo, sin restaurar autoridad anterior ni eliminar historial.
- Login «Planea. Trabaja. Controla.»; diálogos ampliados y guiados, confirmaciones internas y diseño adaptable.


## v1.2.0 · 26 de octubre de 2026

- Analítica mensual con horas por Grupo, Técnico, día y tipo: emergente, programada, histórica y Guardia neta.
- Separación de «Mi resumen» personal y «Analítica del equipo» para Manager o Lead con delegación vigente; permisos verificados también para exportación.
- Desglose diario desde tarjetas y tablas, filtros de Grupo/Técnico, gráficas y Excel de cuatro hojas.
- Altas y edición organizacional de personas exclusivamente por Admin; Mi equipo conserva consulta y delegación.
- Recuperaciones de Técnico a su Manager; de Manager/administrador a otro Admin; fallback a Admin si no hay Manager activo.
- Consulta de código vigente y regeneración, con invalidación del anterior, uso único y almacenamiento cifrado local para poder volver a mostrarlo.
- Diecisiete pruebas de backend y recorrido Chromium ampliado para alcance, permisos, cálculos, recuperaciones y exportaciones.

## v1.1.1 · 26 de octubre de 2026

- Acceso enfocado en «Control de OT y guardias», con textos coherentes en el mensaje de bienvenida, Mi tiempo y Acerca del proyecto.
- Se retiran las referencias a comenzar una jornada laboral.
- Botón de mostrar/ocultar contraseña en el login, con etiqueta accesible y conservación del valor escrito.
- Sin cambios en reglas operativas, permisos ni datos.

## v1.1.0 · 26 de octubre de 2026

- Reglas de Guardia con varios intervalos por día, agregar/quitar horarios y cobertura explícita de 24 horas.
- Delegación inline junto a las personas de Mi equipo, sin modal y con una sola asignación vigente/programada por Manager.
- Sustitución atómica del backup, revocación y conservación de historial, incluida compatibilidad con múltiples filas de versiones anteriores.
- Tarjetas del Panel que abren los registros con filtros relevantes; eventos pendientes y en curso accesibles sin depender del mes visible.
- Detalle de actividad con Timer en vivo y decisiones de aprobación desde el detalle.
- Solicitudes concretas para revisar en el Panel, en lugar de un segundo contador de pendientes.
- Once tests del backend y recorrido real de Chromium ampliados para los nuevos flujos.

## v1.0.2 · 26 de octubre de 2026

- Se oscurecen textos secundarios, etiquetas, ayudas, placeholders y mensajes de los modales para mejorar su lectura.
- Se conserva la paleta azul, blanco y turquesa, así como los textos claros del menú y las superficies oscuras.
- Sin cambios de distribución, tamaños, flujos ni datos.

## v1.0.1 · 26 de octubre de 2026

- Rediseño de los modales de activación, solicitud de recuperación y restablecimiento de contraseña, con encabezados propios, iconografía y secciones de información.
- Ayuda contextual para identificar el código necesario, quién lo entrega y su vigencia.
- Mostrar u ocultar cada contraseña y comprobación visual de longitud mínima y coincidencia, conservando las reglas de validación existentes.
- Estados de envío, errores visibles dentro del formulario y confirmaciones después de activar o restablecer el acceso.
- El usuario ingresado se conserva al pasar de solicitar recuperación a utilizar un código y al volver al login.
- Diseño adaptable a móvil, nombres accesibles y foco inicial en el campo de usuario.
- Sin cambios en el esquema SQLite, permisos ni lógica de OT, Guardias, timers, aprobaciones, Claim, ADP y Excel.

## v1.0.0 · 26 de octubre de 2026

- Base inicial del proyecto con identidad azul, blanco y turquesa.
- Logotipo original de Kyndryl e iconografía SVG local del sistema Shidoka.
- Créditos para Samuel Alejandro Díaz Chávez y Francisco Cervantes Marquez.
- Organización, accesos, tiempo operativo, reportes y persistencia SQLite.

## Criterio de numeración

- Ajustes y mejoras pequeñas: `v1.0.1`, `v1.0.2`, etc.
- Mejoras importantes o nuevas funciones: `v1.1.0`, `v1.2.0`, etc.
- Ajustes posteriores a una entrega: por ejemplo, `v1.2.1` después de `v1.2.0`.

La versión se actualiza en backend, interfaz y referencias de recursos para evitar inconsistencias de caché. Las versiones no reinician ni borran la base local.


## v1.0.12 — Analítica de gestión

Tablero del Manager reorganizado: lectura ejecutiva, concentración de OT por Grupo, mezcla de captura, pendientes, comparación con OT y Stand By separados y desgloses progresivos. Conserva cálculos, alcance, historial y diseño general. Sin metas ni evaluaciones de desempeño inferidas.

## v1.0.13 — Analítica visual y comparación directa

- Comparación por periodos rápidos: 2, 3, 6, 12 meses, año hasta el mes principal o mismo mes del año anterior. Cuadrícula de meses seleccionables y navegación entre años; conserva el principal y el límite de 24 meses.
- Cuatro gráficas con detalle al clic: tendencia de líneas OT/SB, barras independientes por Grupo, pastel por tipo y cascada de variación de OT.
- Cada gráfica abre una lectura del periodo, datos tabulares y contexto de filtros. La cascada compara primer/último mes y separa variación programada, histórica y emergente; no atribuye causas.
- Disponible para Manager, Lead delegado y analítica personal del Técnico según su alcance autorizado. Sin cambios en cálculo financiero ni permisos.

## v1.0.14 — Analítica visual separada de consulta

- Dos destinos independientes: Analítica (sin tablas en la página) y Consulta de registros (buscador CHG/INC, persona, Grupo, estados e historial). Técnico: Mi analítica y Mis registros; Lead delegado conserva alcance de equipo.
- Se eliminan tablas, listados y rankings de texto de la portada analítica. Los datos tabulares permanecen en los modales de detalle. Acceso a Consulta conserva periodo y filtros del análisis.
- Ocho visualizaciones del equipo: líneas, barras, pastel, cascada, mapa de calor horario, área acumulada, Pareto de OT y dispersión OT/SB. Cinco visualizaciones personales, sin comparativas entre personas ajenas.
- Cada nueva gráfica explica su base, unidades, límites y datos subyacentes. Sin metas, previsiones ni evaluaciones de desempeño inventadas. Cálculos financieros y permisos sin modificaciones.

## v1.0.15 — Dashboard compacto, datos emergentes y captura oportuna

- Composición BI basada en las referencias del usuario: indicadores superiores con variación, paneles compactos y alineados, tendencia amplia, distribución en columnas y anillo de composición. Menús y consulta permanecen separados.
- Indicadores del mes más reciente seleccionado, comparados con el anterior seleccionado. Las gráficas integran el conjunto de meses; se explica esta diferencia y los periodos parciales.
- Datos emergentes en marcas de gráficas, medidores y mapa de calor: cursor, foco de teclado y toque en móvil. Dentro de modales, sin perder detalle tabular. Colores y tooltip compatibles con la política de seguridad de contenido existente.
- Regla de uso: programar antes de ejecutar, usar Timer para la actividad y comenzar Timer ante emergencias; la captura histórica es excepcional y se justifica para revisión. No se introduce un plazo arbitrario ni un bloqueo retroactivo.
- Seguimiento de registros históricos y demora media desde fin de actividad hasta creación. Excluye cancelados y recuperaciones de respaldo; no cambia horas, aprobaciones, Claim ni ADP. Se muestra contexto en consulta y revisión del registro.

## v1.0.16 — Datos completos de demostración

807 OT, 142 Guardias y 570 tramos cerrados para 12 Técnicos y cuatro Leads, cuatro Managers y dos Cuentas. Historial mayo–octubre y programaciones futuras de noviembre; octubre de Samuel Díaz (951357) excluido y conservado. Actividades compartidas, aprobaciones simuladas, pendientes, rechazo, documentación y capturas históricas excepcionales.

Nueva base sintética para instalaciones sin base existente. Cargador aditivo con respaldo, identificadores estables, transacción y protección de octubre para quien conserva su base; no reemplaza personas ni registros. Sin Timers activos automáticos ni delegaciones nuevas. [Uso de los datos](DATOS_DEMO.md).

## v1.0.17 — Acumulación por tipo y lectura directa

- El panel mensual combina dos gráficas lado a lado: tendencia de líneas OT/SB y barras mensuales apiladas por Stand By, OT programada, histórica y emergente. En móvil se apilan; se elimina la altura sobrante.
- Acumulación con áreas apiladas por los cuatro tipos, totales por color, datos emergentes diarios/acumulados y tabla de acumulados por tipo. No se confunde acumulación con variación mensual.
- La concentración de OT se simplifica a un ranking horizontal con nombre, horas y porcentaje directamente visibles. Se retiran la línea de porcentaje acumulado, doble eje y números que obligaban a buscar nombres en otra leyenda.
- Sin cambios en datos, cálculos, permisos ni ejemplos; se conserva la protección de octubre de Samuel.

## v1.0.18 — Leyendas interactivas

- En los modales de acumulado, barras mensuales, anillo y tendencia, pulsar una categoría la muestra sola. Repetir la pulsación o elegir Ver todos restablece la vista completa.
- Se ajustan escala, resumen, valores emergentes y tabla a la serie elegida; las categorías sin horas tienen estado vacío explícito.
- La selección se limita al modal y no cambia el reporte ni filtros del dashboard. Consultar registros lleva el tipo seleccionado a la pantalla de consulta, conservando su periodo y alcance autorizado.
- Botones con foco, estado accesible y uso por teclado/toque. Se conservan cálculos, datos de demostración y octubre de Samuel.

## v1.0.19 — Tablero personalizable del Manager

- Personalizar tablero permite mostrar/ocultar cada una de las nueve gráficas y asignar ancho/altura. Tendencia y barras mensuales tienen tamaño y visibilidad independientes.
- Cuatro anchos (tercio, mitad, dos tercios, completa) y cuatro alturas; esquina para redimensionar con ratón o flechas. Escape cancela el arrastre y el refresco silencioso no interrumpe el ajuste.
- Preferencias guardadas automáticamente por usuario en este navegador, separadas de los datos y filtros. Restaurar diseño recupera todas las gráficas y tamaños predeterminados. Un tablero sin gráficas conserva una vía clara para recuperarlas.
- En móvil el ancho se adapta sin sobrescribir las preferencias del escritorio; selectores de tamaño siguen disponibles. El Lead delegado personaliza su propio tablero de equipo; la vista personal conserva su diseño.
- Se mantienen ampliación en modal, selección de series en la leyenda, datos emergentes, consultas, cálculos y registros. Foco de leyendas ajustado para evitar que una actualización asíncrona interrumpa la navegación por teclado.
