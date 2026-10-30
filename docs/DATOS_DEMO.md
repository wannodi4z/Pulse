# Datos de demostración · v1.0.16

La entrega incluye una base **sintética** para probar la herramienta: 949 registros (807 OT y 142 Guardias), 570 tramos de Timer cerrados y cuatro reglas de Guardia de demostración. Son 12 Técnicos y cuatro Leads entre los cuatro Managers. Las referencias/descripciones y la trazabilidad identifican la demostración; las aprobaciones son simuladas.

## Cómo abrirlos

- **Instalación nueva:** `start.command` instala los ejemplos cuando no existe `operational_pulse.db`. Los usuarios y contraseñas de prueba son los mismos de la entrega anterior.
- **Con tu base actual:** cierra Pulse y ejecuta `Cargar_datos_demo.command`; después abre `start.command`. La carga agrega registros para las personas activas que ya existen y guarda un respaldo SQLite en `backups/`. Si la estructura corresponde a una versión anterior, abre esta versión de Pulse una vez para actualizarla y vuelve a cargar los ejemplos.
- La carga puede repetirse sin duplicar los mismos escenarios de una misma fecha. No cambia personas, contraseñas, Grupos, registros ni decisiones existentes. Si hay un Timer activo, se detiene la carga sin agregar registros.

## Periodos y escenarios

| Periodo | Datos |
| --- | --- |
| Mayo–septiembre de 2026 | OT y Guardias de cada Técnico, OT de cada Lead, variación de duraciones entre meses/personas |
| Octubre de 2026 | Mismos ejemplos salvo Samuel Díaz (Employee ID 951357); sus registros existentes se conservan intactos |
| Noviembre de 2026 | OT futuras aprobadas y pendientes para revisar calendario y habilitación del Timer |
| Día de la carga | Actividad preaprobada con ventana cercana para probar el Timer, excepto Samuel cuando intersecta octubre de 2026 |

La ventana del día puede haber terminado cuando abras la herramienta; programa otra actividad si necesitas probar el Timer en otro horario. No se inicia ningún Timer automáticamente.

- Programadas completadas con Timer y aprobación; algunas esperan la revisión de horas reales.
- Actividades de Grupo vinculadas a una misma programación y participaciones individuales con tramos propios.
- Emergencias finalizadas/aprobadas y emergencias por documentar.
- Históricas excepcionales con motivo, en proporción minoritaria, para comprobar seguimiento de captura.
- Planificaciones rechazadas sin ejecución ni horas aprobadas.
- Guardia de un periodo semanal y solicitudes de un día con estados distintos. Los Leads no tienen Guardias.
- Guardias y OT coincidentes permiten comprobar el descuento de OT en Stand By, Claim y ADP.

El cargador conserva octubre de Samuel, incluida la trazabilidad, tramos y correcciones de sus registros existentes. No agrega Guardias que crucen ese mes para Samuel. Una actividad compartida del Grupo no le asigna horas ni ejecuta su Timer automáticamente.

## Implementación

`scripts/populate_demo_records.py` usa identificadores estables por persona/periodo/escenario, una transacción, respaldo previo, validación de claves foráneas y comparación de los registros protegidos antes/después. No elimina ni actualiza filas existentes.

`fixtures/operacion_demo_2026.sqlite3` contiene únicamente los ejemplos distribuidos; `fixtures/banorte_pruebas.sqlite3` conserva la estructura base de pruebas. Las bases reales, claves, sesiones y respaldos locales no se incluyen en el ZIP.
