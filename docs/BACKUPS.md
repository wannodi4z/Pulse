# Exportación y respaldo

## Excel de aprobados (.xlsx)

El botón Excel aprobados produce el resultado de captura del mes (Captura, Tiempo aprobado y Resumen). No incorpora la pestaña interna de recuperación. Claim conserva su formato propio. Son archivos de consulta/captura para Excel.

## Respaldo personal de Pulse (.pulse)

En Mi tiempo → Respaldo / Recuperar → Descargar respaldo Pulse se obtiene un archivo `.pulse`, con tipo de contenido propio. Conserva el libro interno de recuperación para no perder compatibilidad ni precisión. Se importa desde el mismo modal; no se abre como pantalla al hacer doble clic en el sistema operativo.

La extensión identifica el uso y evita confundirlo con el Excel de aprobados; no cifra ni hace exclusivo el contenido: una herramienta compatible puede abrirlo renombrándolo a .xlsx. No se presenta como protección de acceso. Mantén el archivo en un lugar privado.

Pulse valida el contenido y Employee ID, no confía sólo en la extensión. Conserva lectura de Excel anteriores para recuperar respaldos existentes. La vista previa no crea horas. La confirmación detecta duplicados/traslapes y devuelve horas al Manager; nunca recupera una aprobación. La OT incompleta requiere documentación.

Este respaldo personal no sustituye una copia integral de `operational_pulse.db` y su `.key` con la aplicación detenida. Una actualización que conserva esa base no requiere reimportar horas.
