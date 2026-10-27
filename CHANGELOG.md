# Historial de versiones

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
