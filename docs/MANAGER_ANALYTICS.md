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
