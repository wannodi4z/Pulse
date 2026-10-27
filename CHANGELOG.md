# Historial de versiones

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
