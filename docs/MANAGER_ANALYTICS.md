# Analítica del Manager · v1.0.11

Diseño visual original v1.0.10. El Lead conserva su rol: la analítica del equipo y su participación requieren delegación activa; su analítica personal sigue separada.

## Consultar

Busca por referencia CHG/INC, nombre de Técnico, Employee ID, nombre o código de Grupo. La búsqueda conserva el periodo seleccionado. Para buscar fuera del mes elige Todo el historial; la misma consulta gobierna indicadores, tablas, rankings y exportación.

La tabla por Grupo muestra horas de OT emergente, programada e histórica, Stand By/Guardia neta, OT total y total aprobado. Los conteos de cada tipo representan registros aprobados finalizados (solicitudes aprobadas en Guardia); no son cantidad de personas. Las horas conservan unión de OT y descuento de OT coincidente sobre Guardia.

Ver Técnicos acota el tablero al Grupo. Ver horas abre los registros filtrados de una persona. Los Grupos corresponden a la asignación actual; el detalle conserva la trazabilidad de origen.

## Más y menos horas

Los dos rankings muestran hasta cinco personas y se pueden ordenar por Total aprobado, OT aprobada o Stand By neto. Comparten el periodo, consulta y filtros. Incluyen integrantes con cero horas dentro del alcance consultado. Las diferencias no representan una evaluación de desempeño ni distinguen por sí solas vacaciones, altas, bajas o jornadas contratadas. Un mismo Técnico puede aparecer en ambos extremos si la selección es pequeña.

## Participación de una actividad

Desde Detalle de una OT programada → Ver participantes. Se usa el vínculo real de actividad/ventana, nunca la igualdad del texto CHG/INC. Muestra autor, inscritos visibles, quiénes iniciaron Timer, tramos iniciados, tiempo cerrado individual, estado y horas aprobadas. Una inscripción sin Timer no se presenta como ejecución. El tiempo abierto no suma aprobado. El alcance es la actividad completa; puede diferir del mes filtrado del tablero.

Sólo devuelve personas dentro del alcance actual del Manager o del Lead delegado. El Técnico sin delegación no puede consultar el endpoint del equipo. Al revocar la delegación se rechaza una nueva consulta.

## Comparar

Comparar meses permite agregar hasta 24 meses. La tabla amplía el desglose mensual a OT programada, histórica, emergente, OT total, SB neto y total. La variación compara contra el mes anterior seleccionado; el mes actual conserva el aviso de parcial.

## Entrega

El ZIP estable no incluye las interfaces experimentales rechazadas. Conserva start.command, backend, frontend, fixtures, pruebas y documentación. No incluye bases personales, claves ni entornos.


## Tablero de gestión v1.0.12

La portada resume OT, Stand By neto, proporción de OT programada y personas con horas aprobadas. La lectura ejecutiva identifica la concentración de OT, proporción emergente y diferencia de OT entre los últimos dos meses seleccionados. No se infieren objetivos, productividad ni desempeño.

El mapa ordena Grupos por OT y muestra SB por separado; cada Grupo permite filtrar la consulta. El panel de seguimiento cuenta pendientes, documentación y personas sin horas aprobadas con los filtros vigentes. La comparación usa barras independientes de OT y SB con una escala común. Las cifras por Grupo y persona se consultan en desgloses desplegables. Los totales financieros y permisos mantienen su cálculo anterior.

## Exploración visual v1.0.13

**Comparar periodos:** elige un acceso rápido o marca meses en la cuadrícula. Los accesos rápidos terminan en el mes principal; “Mismo mes · año anterior” selecciona ese mes y su equivalente anterior. Navega entre años sin perder la selección; aplica una vez al terminar. El principal siempre queda incluido, hasta 24 meses. No se agrega automáticamente historial ni cambia la búsqueda.

Las cuatro gráficas abren un modal con resumen, tabla y alcance de la consulta:

| Gráfica | Pregunta de gestión | Base |
| --- | --- | --- |
| Líneas | ¿Cómo evolucionan OT y SB? | Horas mensuales aprobadas, misma escala; fechas separadas según distancia real entre meses. Los meses omitidos no son ceros. |
| Barras | ¿Qué Grupos concentran OT y SB? | Dos barras por Grupo; portada muestra hasta 6 Grupos por OT, tabla completa al abrir. |
| Pastel | ¿Qué proporción corresponde a cada concepto? | Programada, histórica, emergente y Guardia neta sobre horas aprobadas. No muestra proporciones sin base. |
| Cascada | ¿Qué tipo de OT explica la diferencia? | OT del primer mes + cambios por tipo = OT del último mes. Los meses intermedios se consultan en líneas. |

Azul en cascada: total inicial/final; naranja: incremento; verde: reducción. Los colores indican dirección, no una valoración de desempeño. Una diferencia por tipo de captura no demuestra una causa de negocio. Histórica no equivale a imprevista. Los periodos en curso son parciales. La analítica personal utiliza únicamente el reporte personal autorizado; el Lead requiere delegación vigente para el tablero del equipo.

## Separación de funciones v1.0.14

**Analítica** muestra exclusivamente indicadores, lecturas y visualizaciones: no incluye tablas, rankings de texto ni buscador de referencias. Sus filtros son periodo, Grupo, Técnico y tipo de horas. **Consulta de registros** reúne búsqueda por CHG/INC, nombre, Employee ID, Grupo, estados y todo el historial, además de exportación y detalle con trazabilidad y participantes. Las aprobaciones se resuelven en su pantalla de Aprobaciones. “Consultar registros”, desde Analítica o desde una gráfica, conserva los filtros y meses vigentes.

Las tablas de respaldo se abren al hacer clic en una gráfica. El Manager y Lead delegado ven ocho visualizaciones; el Técnico ve cinco sobre su propio reporte (líneas, pastel, cascada, área y mapa de calor), sin comparaciones con personas ajenas.

| Nuevos tipos | Uso y límites |
| --- | --- |
| Mapa de calor horario | Detecta franjas con más horas acumuladas. Agrupa fechas y personas; no representa simultaneidad ni una jornada individual. |
| Área acumulada | Muestra cómo se acumulan horas aprobadas en las fechas elegidas. No extrapola ni establece una meta. |
| Pareto | Barras de OT por Técnico y porcentaje acumulado. Hasta ocho personas y el resto agrupado; tabla completa en detalle. Cero horas no implica falta de actividad. |
| Dispersión | Un punto por persona: Stand By neto en X, OT en Y. Escalas etiquetadas y valores completos en el detalle; puntos coincidentes pueden superponerse. |

Los datos personales y del equipo continúan usando los mismos endpoints y controles del servidor. Revocar delegación retira acceso a Analítica del equipo y Consulta del equipo.

## Dashboard y registro oportuno v1.0.15

Los indicadores superiores muestran **el último mes seleccionado** y su variación frente al anterior seleccionado, con el mismo alcance. La proporción programada usa puntos porcentuales (pp); las demás variaciones usan horas. Con un solo mes no se inventa una base previa. Un mes en curso se señala como parcial. Las gráficas abarcan todos los meses seleccionados y conservan sus unidades y detalles.

Las marcas muestran sus valores al pasar el cursor o recibir foco por teclado. En móvil, los datos del detalle se pueden tocar. Escape, cambio de foco o salir de la marca oculta la ayuda. Los colores del mapa de calor y de los indicadores respetan la política de seguridad de contenido, sin habilitar estilos arbitrarios.

**Regla de uso:** la OT prevista se programa antes de ejecutarse y se realiza con Timer; una emergencia se registra con Timer al atenderla. La captura histórica es excepcional y requiere explicar en la justificación por qué se registra después y por qué no se utilizó Timer. La justificación y la aprobación siguen usando el flujo existente. No se bloquean casos legítimos ni se añade una fecha límite sin una política definida.

El indicador de captura oportuna distingue los registros históricos manuales de las recuperaciones desde respaldo. Muestra cantidad/proporción de históricos sobre OT no recuperada y demora media en horas desde el fin registrado hasta crear el registro. Usa registros dentro de los periodos de actividad y filtros consultados, en cualquier estado excepto cancelado; no es un indicador de horas aprobadas ni prueba de incumplimiento. Las recuperaciones se excluyen para no confundir restauración con backlog. No se modifican cálculos financieros ni decisiones de aprobación.

[Vista previa del dashboard v1.0.15](previews/Analytics_v1.0.15.png). Imagen generada con datos de prueba aislados; no corresponde a registros productivos.

## Lectura directa v1.0.17

El primer panel muestra **Tendencia mensual** (líneas de OT y Stand By) junto a **Horas mensuales por tipo** (barras apiladas de los cuatro conceptos). Cada mitad abre su propio detalle. Se apilan verticalmente en móvil y cada panel usa su altura necesaria.

**Acumulado por tipo de hora** utiliza franjas apiladas para Stand By neto, OT programada, histórica y emergente. La altura total es la suma acumulada. La ayuda por fecha incluye acumulado por tipo y aporte del día; la leyenda muestra los cuatro totales y la tabla desglosa cada acumulado. Aumento del acumulado significa incorporación de horas aprobadas a lo largo de las fechas, no variación respecto de otro mes. Las fechas omitidas no se convierten en horas cero.

**OT aprobada por Técnico** muestra nombre y horas en cada barra, con la participación porcentual sobre toda la OT del alcance. Se ordena de mayor a menor; la portada muestra hasta ocho personas y el detalle incluye todas. Se incluyen personas con cero horas. Se ha reemplazado el anterior Pareto con doble eje para facilitar la lectura; no mide desempeño.

[Vista previa v1.0.17](previews/Analytics_v1.0.17.png), con datos aislados de prueba.

## Aislar una categoría desde la leyenda · v1.0.18

Abre el detalle de **Acumulado por tipo**, **Horas mensuales por tipo**, **Composición** o **Tendencia**. Pulsa la categoría en su leyenda para mostrarla sola; por ejemplo, OT histórica. La gráfica cambia de escala y el resumen, los valores emergentes y la tabla muestran esa selección. Para recuperar la vista completa, vuelve a pulsar la misma categoría o usa **Ver todos**.

Las leyendas indican el total de cada categoría dentro del alcance original del dashboard; los botones restantes permanecen disponibles para cambiar de categoría. En el anillo, la única categoría visible representa 100% de esa selección; Ver todos restaura sus proporciones originales. Si no existen horas del tipo seleccionado, se indica sin inventar datos.

Esta selección no modifica los filtros del dashboard ni recalcula Stand By bruto: conserva el Stand By neto ya calculado. Al cerrar y volver a abrir una gráfica se muestran todos los tipos. **Consultar registros** desde el detalle traslada el tipo elegido a la consulta para revisar sus registros. La autorización personal/de equipo continúa aplicándose en el servidor.

## Personalizar el tablero · v1.0.19

1. En Analítica del equipo, pulsa **Personalizar tablero**.
2. Usa las opciones de Gráficas visibles para mostrar u ocultar cada gráfica. También puedes pulsar **Ocultar** en una tarjeta.
3. Elige **Ancho** y **Altura** en cada tarjeta. En escritorio puedes arrastrar su esquina inferior derecha para ajustar ambas dimensiones; las flechas del teclado también funcionan al enfocar la esquina. Escape cancela el arrastre.
4. Pulsa **Listo** para salir de la edición. Los cambios se guardan automáticamente, sin modificar los filtros ni los datos.

**Restaurar diseño** recupera las nueve gráficas con tamaño predeterminado. Si ocultas todas, permanece disponible **Elegir gráficas**. Tendencia mensual y barras mensuales se personalizan de forma independiente.

Los tamaños se ajustan a una cuadrícula para evitar solapamientos: ancho de un tercio, mitad, dos tercios o completo; alturas compacta, normal, alta o muy alta. Las tarjetas con más contenido permiten desplazarse en su interior y mantienen visible el acceso al detalle. En pantallas pequeñas las tarjetas ocupan el ancho disponible sin cambiar el tamaño guardado para escritorio.

El diseño se almacena **por usuario en el almacenamiento de este navegador**, separado para cada Manager o Lead delegado. No se sincroniza entre dispositivos ni forma parte del respaldo de horas; limpiar los datos del navegador elimina esa preferencia. Si el navegador impide guardarla, la interfaz informa y mantiene los cambios durante la sesión. La selección de leyendas sigue siendo local al modal; ampliar una gráfica no cambia su tamaño guardado.

[Vista previa de personalización v1.0.19](previews/Analytics_v1.0.19.png), con datos aislados de prueba.
