# v1.1.2 · Organización sin scroll interminable

## Explorador

Admin → Cuentas → Abrir Cuenta muestra un directorio de DP/DPE y el equipo seleccionado. Con un solo DP, se abre directamente su lista de DPE. Se muestran hasta ocho responsables por página y seis Managers por página en el detalle. Cada lista tiene su propio contador y navegación.

La búsqueda consulta toda la Cuenta, no sólo la página visible: encuentra DP, DPE, Manager, Lead o Técnico por nombre o Employee ID. Seleccionar un Técnico o Lead lleva al equipo de su Manager; seleccionar un DPE muestra sólo sus Managers. La ruta superior permite volver a la Cuenta o al DP.

**Ver equipo** abre la tarjeta de Manager, su Lead y sus integrantes. Se conservan edición, alta, activación, baja/reactivación y acciones existentes. Las asignaciones pendientes de DP/DPE quedan accesibles desde **Sin asignar**. Los filtros de atención de Admin se conservan.

## Árbol

Alterna **Explorador / Árbol**. El árbol inicia contraído y muestra DP → DPE → Manager → Grupos → Técnicos. El Lead aparece directamente junto al Manager; no se convierte en un cargo oficial ni en un Grupo.

Cada rama se abre de forma individual. Las ramas con más de ocho elementos se paginan, incluido un DP con cincuenta DPE. La búsqueda encuentra personas en cualquier nivel; los resultados conservan sus ramas. **Contraer ramas** vuelve a la visión general. No hay expansión masiva automática.

El modo y las ramas abiertas se mantienen durante la sesión de interfaz por Cuenta. No modifican la base, las autorizaciones, las horas ni el alcance de consulta. En móvil las columnas se acomodan verticalmente.

La demo Banorte conserva su organigrama, los seis accesos solicitados y la ausencia de horas precargadas. Usa una carpeta nueva para iniciar la demo; una organización existente no se reemplaza.

## OT de varios días con horario diario

Manager → Reglas de Guardia → **Horario de OT** configura inicio y fin diarios. El valor sugerido es 21:00–08:00 del día siguiente. Al activar la exigencia, todas las nuevas OT programadas del equipo usan esa franja, aunque el cliente intente omitirla. Sin una política obligatoria guardada, el formulario propone franjas diarias y permite solicitar una ventana continua sujeta a aprobación.

Al registrar OT, el periodo general puede abarcar varias noches. La vista previa enumera las franjas dentro de sus extremos; la primera y última se recortan al periodo. Se permite programar las franjas restantes de un periodo en curso, sin recuperar tiempo anterior ni iniciar antes de la aprobación. La zona horaria queda en la copia de la programación.

El servidor valida cada inicio/reanudación. Al cierre de la franja, corta el tramo y pausa el Timer. Si el servidor estuvo detenido, al volver cierra en el primer límite de aquel tramo, sin sumar el tiempo de la interrupción. El Técnico reanuda explícitamente en otra franja; **Pausar tramo** permite detener la ejecución antes del cierre sin finalizar toda la OT. **Finalizar y enviar** termina el trabajo y devuelve sus horas reales a aprobación.

Cada OT conserva el horario enviado a aprobación. Cambiar la política no altera registros anteriores. Una modificación de la programación requiere nueva aprobación. Los integrantes del Grupo comparten la programación aprobada, pero sus Timers y horas son individuales. Las extensiones conservan la restricción diaria; ampliar el periodo no habilita las horas intermedias. Las emergencias conservan su flujo de Timer inmediato.

Claim, ADP, Analítica y respaldos usan los tramos realmente ejecutados y aprobados. El periodo completo y las horas de espera no suman OT. La Guardia neta descuenta únicamente OT coincidente real.

## Histórica en un solo modal

Si el periodo ya terminó, el mismo formulario cambia sus etiquetas a **Ventana original** y despliega **Trabajo realmente realizado** debajo. No hay otro modal ni pasos. Se indica inicio/fin de cada tramo y se calcula el total; pueden agregarse varios tramos cuando hubo pausas o participación en varias noches.

Se conservan la programación original y los extremos reales por separado. Se rechazan tramos futuros, desordenados, vacíos o traslapados. Las horas enviadas a revisión y contabilizadas tras su aprobación son la suma de los tramos reales. La documentación y justificación de la captura posterior permanecen en el mismo formulario. La edición posterior de horas reales sigue requiriendo motivo y nueva aprobación.

El respaldo personal conserva también la ventana original, cuando existe; la recuperación mantiene los tramos y exige nueva aprobación. El respaldo integral conserva políticas y programaciones.

Las solicitudes antiguas se conservan con sus datos y comportamiento originales; la actualización no inventa ventanas originales o trabajo faltante en registros históricos anteriores.
