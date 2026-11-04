# Revisión transversal de interfaz y proyecto · v1.0.22

## Corregido

| Hallazgo | Ajuste |
|---|---|
| Acciones principales dispersas en el extremo derecho | Barra de acciones a la izquierda, debajo del título; pies de modal y tarjetas coherentes. |
| Estado vacío de Cuentas o Grupos ocupaba una sola columna | Ocupa el ancho disponible; icono y texto centrados. |
| La Cuenta ofrecía crear Manager antes de DP/DPE | El siguiente paso se adapta a la estructura: DP, DPE o Manager. |
| Búsqueda de Admin omitía DP/DPE | Incluye los nombres e IDs de ambos roles. |
| Mi equipo decía que Admin debía asignar los Grupos | Indica al Manager crear su primer Grupo; oculta instrucciones de arrastre sin Grupos. |
| Sidebar largo y sin agrupaciones | Secciones por rol, contracción a iconos, preferencia por usuario y navegación móvil con etiquetas. |
| Analítica personal tenía menos opciones de organización | Ahora tiene tablero personalizable con preferencias independientes. |
| Un único diseño no cubría distintos usos de analítica | Diseños rápidos y hasta cinco vistas guardadas por usuario/alcance. |
| Falta de recuperación de toda la organización | Respaldo cifrado de Admin y restauración offline en una instalación nueva. |
| Configuración de correo no existía | SMTP preparado, contraseña cifrada y envío todavía inactivo. |
| Acceso al Timer requería navegar varias pantallas | Acceso web de escritorio, respetando sesión y ventanas de autorización. |

Se revisaron login, panel, organización, administración de accesos, equipos, aprobaciones, reglas, calendario, Timer, historial, analítica, Claim/ADP, perfiles y modales, incluyendo tamaños de pantalla reducidos. Las pruebas funcionales usan bases temporales; la entrega sigue sin datos precargados.

## Qué conservar

- La separación entre consulta, captura y autorización.
- La organización DP/DPE y su árbol como búsqueda adicional; los filtros siguen disponibles.
- Detalles de registro y participación, documentación pendiente, cálculo único de horas y formatos de Claim/ADP.
- La identidad visual actual de Pulse y el tablero adaptable.

## Mejoras recomendadas para otra etapa

1. **Separar más módulos del frontend.** `app.js` concentra navegación, formularios y flujos. Conviene extraer organización, calendario y configuración en cambios pequeños con pruebas; no rehacer todo a la vez.
2. **Consolidar CSS.** Hay reglas históricas y varias capas de sobrescritura entre `app.css`, `design.css` e `interface.css`. Una limpieza por componente reduciría regresiones; eliminar bloques completos ahora puede afectar vistas que aún los comparten.
3. **Preferencias en servidor, si se necesita movilidad.** Las vistas y el sidebar actuales son por usuario/navegador. Para compartir diseños entre equipos, debe agregarse persistencia autorizada del lado del servidor.
4. **Notificaciones de correo.** Definir destinatarios, eventos, plantillas y reintentos antes de habilitar el envío. Tener SMTP configurado no implica que ya se envíen mensajes.
5. **Operación centralizada.** Si se instala para varios usuarios en un servidor, completar despliegue HTTPS, almacenamiento seguro y programación externa de respaldos. La descarga manual actual no programa copias automáticas.

## Qué sobra en la entrega limpia

Las bases precargadas y lanzadores antiguos de datos de ejemplo ya están excluidos del ZIP. Las fixtures se conservan en el repositorio sólo para regresión. Las presentaciones anteriores son referencia histórica; la documentación v1.0.22 describe las novedades actuales.
