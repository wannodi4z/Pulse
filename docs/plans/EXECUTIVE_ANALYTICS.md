# Analítica e historial para DP y DPE

Estado: implementado en v1.0.21; ver docs/EXECUTIVE_ROLES.md para uso y validación.

## Requisitos confirmados

- Manager y superiores no capturan OT ni Stand By.
- DP y DPE necesitan analítica e historial, sin facultades de aprobación implícitas.
- Desglose desde el alcance ejecutivo hasta Manager, Grupo, Técnico y registro.
- Mantener comparación de meses, gráficas personalizables, leyendas y detalles de participación.
- Admin configura usuarios y sus alcances; los superiores no alteran la estructura ni horas.

## Estructura y alcance confirmados

- Jerarquía: Cuenta → DP → DPE → Manager → Grupo → Técnico.
- DPE: sus Managers y todos sus Grupos y Técnicos; sin visibilidad de otros DPE.
- DP: toda su Cuenta, incluidos sus DPE, sus Managers, Grupos y Técnicos.
- Sin asignación: mostrar estado sin alcance, nunca asumir acceso global.
- Admin debe registrar explícitamente las relaciones de Cuenta, DP, DPE y Manager.

## Hallazgos del proyecto actual

La tabla users sólo admite ADMIN, MANAGER y USER. scope y visible_users comparten alcance con operaciones de gestión. authorized_target comprueba ese alcance para operaciones sobre registros. Por ello, extender directamente esos helpers a los ejecutivos sin separar lectura y escritura otorgaría autoridad accidental.

Se requiere separar autorización de consulta de autorización de gestión/aprobación antes de habilitar los roles. Los endpoints de analítica, exportación, estado, participantes y detalle deben aplicar exactamente el mismo alcance de lectura. Los de edición, Timer, OT, SB, aprobación, traslado y reglas deben seguir rechazando usuarios ejecutivos, aunque invoquen la API directamente.

## Experiencia prevista

Acceso a Analítica y Consulta de registros; árbol organizacional como búsqueda adicional junto a los filtros. Filtros de Manager, Grupo, Técnico, tipo y periodo encadenados al alcance autorizado. Gráficas de OT/SB por Manager y por Grupo, composición por tipo y comparación mensual; acceso al detalle de registros y participantes. Sin menús de captura o aprobación.

## Validación necesaria

Migración preservando usuarios, sesiones, claves e historial. Pruebas con dos Cuentas, varios Managers, DP, DPE, asignación vacía y revocación. Comprobar aislamiento en consultas, exportaciones y participantes; rechazo de escritura directa; sumas reconciliadas con los reportes de Managers y conservación de la interfaz existente.
