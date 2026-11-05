# Configuración, respaldo integral y acceso al Timer · v1.0.22

## Admin → Sistema → Configuración

Esta sección sólo está disponible para Administradores. Manager, DP, DPE y Técnico no pueden leer ni modificar sus datos a través de la API.

### Respaldo integral (.pulseorg)

Pulsa **Descargar respaldo completo**, escribe una contraseña de al menos 12 caracteres y confírmala. El archivo incluye Cuentas, jerarquía DP/DPE, usuarios y sus credenciales, Grupos, reglas, OT, Guardias, aprobaciones, trazabilidad y configuración SMTP. La clave local necesaria para descifrar credenciales de integración va dentro del mismo archivo cifrado.

El contenido se protege con Fernet y una clave derivada mediante Scrypt, usando una sal aleatoria. La contraseña del archivo no se guarda en Pulse. Sin ella no se puede recuperar el respaldo.

La copia es consistente mediante la API de backup de SQLite. **No modifica la operación actual.** Las sesiones, actividad de sesión y códigos emitidos de recuperación de acceso se eliminan de la copia; esos códigos vuelven a pendientes. Se compacta la base copiada para no conservar material de sesión eliminado en páginas libres.

Los Timers activos se cierran al instante de corte **sólo en la copia**. Las emergencias quedan por documentar; el trabajo programado queda pendiente de revisión. No se acumula tiempo por el periodo entre el desastre y la restauración. Los registros ya aprobados conservan su autorización. La aplicación original sigue ejecutando sus Timers.

Este archivo es distinto del respaldo personal `.pulse`, que sólo recupera las horas de un Técnico y las devuelve a aprobación.

### Recuperación tras mantenimiento o desastre

1. Detén Pulse y extrae la misma versión o una posterior del proyecto en una carpeta nueva.
2. Prepara su entorno Python según README.md. **No abras Pulse antes de restaurar.**
3. Ejecuta `restaurar_respaldo.command` en macOS. Indica la ruta del `.pulseorg` y escribe su contraseña.
4. Inicia Pulse con `start.command`. Ingresa con los accesos y contraseñas que tenía la organización respaldada.
5. Revisa los trabajos que estaban activos al corte y los códigos de recuperación pendientes.

También puedes usar la terminal:

```bash
.venv/bin/python scripts/restore_organization.py --backup /ruta/archivo.pulseorg --destination /ruta/instalacion_nueva
```

La contraseña se solicita de forma oculta; no se pasa por argumentos. La recuperación valida formato, autenticidad, hash e integridad de SQLite. Rechaza una carpeta que ya contenga base o clave y nunca reemplaza esos archivos. Las preferencias de vistas y sidebar guardadas en el navegador no forman parte de la base del servidor.

### Servidor SMTP para integración futura

Configura servidor, puerto, STARTTLS/SSL/TLS/sin TLS, usuario, remitente y contraseña. La contraseña se cifra con la clave local; nunca vuelve al navegador ni se registra en auditoría. Dejarla vacía conserva la anterior; la casilla específica permite eliminarla.

**La versión v1.0.22 no conecta con SMTP ni envía correos.** Guarda la configuración para una integración futura. No incorpora tareas de notificación ni pruebas de envío. Mantén el archivo `.key` al actualizar; el respaldo integral lo conserva dentro del paquete cifrado.

## Sidebar por secciones

Los menús se agrupan por rol en Operación, Información, Accesos, Administración o Sistema. En escritorio, **Contraer menú** conserva iconos, nombres accesibles, títulos y el indicador de página activa. La preferencia queda asociada al usuario en ese navegador. En móvil se mantiene la navegación horizontal con etiquetas; la preferencia de escritorio no la oculta.

## Vistas de analítica

Manager, DP, DPE y usuarios con gestión delegada personalizan su tablero de equipo. Técnicos y Leads también pueden personalizar su analítica personal, con preferencias separadas.

**Personalizar tablero** permite:

- Mover, redimensionar, ocultar y recuperar cada gráfica.
- Aplicar diseños rápidos: Equilibrado, Comparar meses y Distribución de horas.
- Guardar hasta cinco vistas con nombre, aplicarlas o eliminarlas.

Las vistas guardan orden, tamaño y visibilidad. No alteran periodos, filtros, horas ni permisos. Son locales al usuario y al navegador; no se sincronizan entre dispositivos. Se conservan ampliación, leyendas interactivas y datos emergentes. Restaurar diseño recupera la distribución predeterminada y mantiene las vistas guardadas.

## Enlace y acceso al Timer por actividad

En el detalle de una **OT programada aprobada** o actividad aprobada del Grupo, elige **Enlace y acceso al Timer**. Puedes copiar su enlace `/?activity=IDENTIFICADOR` o descargar `.webloc` para macOS / `.url` para Windows.

- El enlace identifica una actividad; no contiene contraseñas ni concede acceso.
- Con sesión vencida, primero se inicia sesión y luego se abre esa actividad.
- Se comprueban pertenencia, aprobación y horario en el servidor. Cada integrante ejecuta su propio Timer.
- Abrir el enlace no inicia tiempo. **Iniciar mi Timer** confirma el inicio dentro de la ventana autorizada. Si el mismo Timer ya está activo, se muestra su control.
- Antes del horario, puede actualizarse la disponibilidad. Otra actividad activa impide iniciar una segunda.

Pulse debe estar disponible en esa dirección. El acceso no arranca el servidor local. Abrir desde un móvil requiere una dirección de servidor accesible; `127.0.0.1` apunta al dispositivo que abre el enlace. La experiencia móvil dedicada y SSO quedan para una integración futura.
