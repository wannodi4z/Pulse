# DP, DPE y estructura de la Cuenta · v1.0.21

## Alta desde Admin

1. Abre **Cuentas**, crea o abre una Cuenta y selecciona **Agregar DP**.
2. Completa identidad y correo. Comparte el código de activación por el canal corporativo habitual.
3. En la tarjeta del DP, selecciona **+ DPE** y revisa la Cuenta y el DP responsable.
4. En el DPE, selecciona **+ Manager**. El formulario selecciona ese DPE; los nuevos Managers requieren un DPE de la misma Cuenta.
5. Admin conserva la gestión de Managers y Leads. El Manager mantiene la administración de Grupos y Técnicos.

La estructura se representa como **Cuenta → DP → DPE → Manager → Grupo → Técnico**. El Lead sigue siendo Técnico con la delegación que autorice su Manager.

## Consulta ejecutiva

- **DP:** toda su Cuenta, incluidos todos sus DPE, Managers, Grupos y Técnicos; también incluye Managers existentes pendientes de vincular a un DPE.
- **DPE:** únicamente sus Managers y las personas y Grupos que éstos administran.
- Ambos acceden a **Analítica** y **Consulta de registros**, sin captura OT/SB, Timer, aprobaciones, edición de horas, movimientos ni reglas.
- Pueden mantener sus propios datos de perfil y contraseña; eso no concede permisos sobre otras personas.
- El alcance se recalcula en cada consulta. Una reasignación se refleja incluso en sesiones ya iniciadas.

El DP tiene filtros de DPE y Manager; el DPE, de Manager. Ambos pueden continuar por Grupo, Técnico, tipo y periodo, comparar meses y consultar CHG/INC, documentación, trazabilidad y participantes de OT programadas. Los gráficos superiores separan OT y Stand By por responsable. Al pulsar un responsable se aplica su filtro; **Restablecer** vuelve al alcance completo autorizado.

Las gráficas existentes conservan tamaño, orden, visibilidad por usuario, leyendas interactivas, datos al señalar y ampliación. El Excel de analítica conserva los filtros e incorpora **Por Manager**, con el DPE responsable. Sólo las horas reales aprobadas suman a las métricas; no cambia el cálculo de Guardia neta, Claim ni ADP.

## Actualización de instalaciones existentes

Conserva tu base SQLite y su archivo de clave, como en las actualizaciones anteriores. No sustituyas tu base con la fixture de demostración.

La primera apertura amplía los roles admitidos y agrega el vínculo `parent_id`. Antes de cambiar el esquema de roles, crea una copia SQLite en `backups/antes_v121_*.sqlite3`. La migración conserva IDs, contraseñas, sesiones, relaciones y registros; verifica referencias y revierte la transacción si falla.

**No se inventan responsables para los datos existentes.** En Admin, los Managers anteriores aparecen en **Managers pendientes de vincular a un DPE**. Crea los DP/DPE de la Cuenta y edita cada Manager para asignar su DPE. Su equipo, las aprobaciones y los registros continúan funcionando mientras completas la estructura.

No se puede dar de baja un DP/DPE con dependientes vigentes sin reasignarlos previamente. Tampoco cambiarlo de Cuenta mientras conserve dependientes. Reactivación y recuperación de acceso siguen a cargo de Admin.

## Demo limpia

La entrega no incluye bases de ejemplo ni carga automática de datos. Al abrirla por primera vez sólo existen **admin1 / admin12026** y **admin2 / admin22026**. No hay Cuentas, DP, DPE, Managers, Leads, Técnicos, Grupos, reglas ni horas.

Para empezar desde cero, extrae el ZIP en una carpeta nueva y no copies la base anterior. Una base existente se conserva y migra: nunca se borra al actualizar o reiniciar.

## Árbol organizacional como búsqueda adicional

En **Consulta de registros**, el árbol está disponible junto a los filtros. En **Analítica**, despliega **Árbol organizacional** cuando quieras navegar visualmente. Abre las ramas DPE → Manager → Grupo → Técnico y pulsa **Ver horas** en cualquier nivel. El DPE comienza directamente en sus Managers.

La selección sincroniza los filtros existentes de DPE, Manager, Grupo y Técnico; no los sustituye. Se conservan los meses, tipo, estado y texto de búsqueda. Los resultados, métricas, gráficas y exportación usan ese mismo alcance. El árbol permite buscar nombres, Employee ID o Grupos y mantiene visibles sus ramas superiores. **Toda la Cuenta** / **Todos mis Managers** elimina sólo la selección jerárquica; **Restablecer** limpia todos los filtros.
