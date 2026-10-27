# Historial de versiones

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
