# Operational Pulse · 1.1.0

Aplicación nueva, creada desde cero. La numeración parte de **v1.0.0** como base del proyecto; este cambio de versión y diseño conserva el esquema SQLite y los datos existentes. El ZIP v1.4.5 sirvió únicamente como referencia funcional; esta versión no carga sus archivos ni sus parches. Preparada para probar **localmente en macOS con VS Code**, con frontend HTML/CSS/JavaScript, FastAPI y SQLite. No requiere servicios externos, Docker, Node ni una cuenta de nube.

## Ejecutarla en tu Mac

Necesitas Python **3.11 o posterior** y VS Code. Puedes comprobarlo en la terminal con `python3 --version`. Si tu Mac tiene varias versiones, usa, por ejemplo, `python3.12` para crear el entorno.

1. Descomprime el ZIP y abre en VS Code la carpeta que contiene `server.py`: **File → Open Folder**. Desde GitHub se llama `Pulse-main`; en el ZIP de la entrega se llama `Operational_Pulse_v1.1.0`.
2. Abre **Terminal → New Terminal** y ejecuta:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   python -m uvicorn server:app --host 127.0.0.1 --port 5510
   ```

3. Abre `http://127.0.0.1:5510` en tu navegador. No abras `index.html` con doble clic ni uses Live Server: la interfaz necesita el backend.
4. Para detener el servidor, presiona **Control+C** en esa terminal. Para volver a iniciarlo:

   ```bash
   source .venv/bin/activate
   python -m uvicorn server:app --host 127.0.0.1 --port 5510
   ```

También puedes ejecutar `bash start.command` después de instalar las dependencias. No reinstala nada ni borra la base.

### Depuración en VS Code

Instala las extensiones recomendadas Python y Python Debugger. Ejecuta **Python: Select Interpreter** desde la paleta y selecciona `.venv/bin/python`. En **Run and Debug**, selecciona **Operational Pulse · local Mac** y presiona F5. No inicies simultáneamente el servidor en la terminal y con F5 sobre el mismo puerto.

Si el puerto está ocupado, detén la ejecución anterior o cambia `5510` por `5511` en el comando y abre ese mismo puerto. Si no se encuentra `fastapi` o `uvicorn`, revisa que uses el intérprete de `.venv`.

## Acceso inicial

| Usuario | Contraseña inicial |
| --- | --- |
| `admin1` | `admin12026` |
| `admin2` | `admin22026` |

Al crear una base nueva se generan **únicamente esos dos administradores**. Cambia sus contraseñas en Mi perfil antes de usar datos reales. No hay Cuentas operativas, Managers, Grupos, Técnicos, Leads, OT, Guardias ni datos demo. No hay sistema de notificaciones.

La base se crea como `operational_pulse.db` junto a `server.py`. Las sesiones y los datos persisten al reiniciar. La instalación y las pruebas automatizadas no borran datos manuales. El ZIP no incluye una base utilizada durante desarrollo ni sesiones de pruebas.

## Primer recorrido

1. Entra con un administrador y abre **Organización**.
2. Crea una Cuenta y sus Grupos. Puedes crear Managers antes de tener Grupos y asignarlos después.
3. Crea un Manager dentro de esa Cuenta y selecciona sus Grupos disponibles. Otro Manager no podrá seleccionar Grupos que ya tengan propietario.
4. Agrega Técnicos dentro de cada Grupo. Puedes marcar a uno como Lead; el formulario identifica al Lead actual e impide un segundo Lead.
5. Copia el código de activación mostrado al crear cada persona y entrégalo por un canal seguro. Si lo pierdes, **Activación** genera uno nuevo y anula el anterior.
6. Cierra sesión, elige **Activar cuenta**, ingresa el usuario/código y define una contraseña de al menos 10 caracteres. El Employee ID es el usuario de Managers y Técnicos.
7. Como Manager, crea una regla de Guardia en **Reglas de guardia** y, si hace falta, una delegación temporal desde **Mi equipo**.
8. Como Técnico, usa **Mi tiempo** para OT programada, histórica, emergencia o solicitudes de Guardia. **Claim** y **ADP** muestran el tiempo aprobado del mes.
9. Como Manager o Lead delegado, revisa **Tiempo del equipo**, filtra y aprueba o rechaza con motivo.

### Organización

La interfaz anida **Cuenta → Managers → Grupos → Técnicos**. Los Grupos sin Manager tienen su propia sección dentro de la Cuenta. Un Manager pertenece a una sola Cuenta y puede tener varios Grupos; cada Grupo tiene un único Manager. Lead es una capacidad del mismo Técnico, con el mismo acceso, propiedad de timers e historial; no es otra persona ni otro nivel del organigrama.

Una Cuenta con Grupos no se puede eliminar. Si tiene Managers, primero deben moverse. Un Grupo con Técnicos debe vaciarse antes de eliminarlo; si tiene ventanas de OT compartida se conserva para mantener su historial. Deshabilitar una persona conserva sus registros. No puedes deshabilitar tu propia cuenta administradora ni al último administrador activo.

### OT, Guardias y timers

- **OT programada individual:** la persona define el periodo y referencia CHG/INC. Debe aprobarse antes de iniciar. El botón Iniciar está disponible durante la ventana aprobada. Al detenerse, el tiempo real vuelve a aprobación.
- **OT histórica:** registra tiempo que ya terminó y envíalo a aprobación.
- **OT compartida:** el Manager o Lead delegado publica una ventana para un Grupo. Cada Técnico participa una sola vez y tiene su propio Timer. La publicación autoriza la programación; el tiempo real de cada participante se aprueba después de ejecutarse.
- **Emergencia:** Iniciar emergencia crea el Timer inmediatamente. Detener genera un registro pendiente de documentación sin exigir un formulario en ese momento. Luego completa CHG/INC, descripción, justificación, impacto y motivo de no usar tiempo compensatorio para enviarlo.
- Sólo hay un Timer activo por Técnico. El propietario es quien lo detiene. Manager y Lead delegado pueden monitorear los timers de su alcance.
- **Guardias:** cada solicitud es independiente por ID y conserva una copia de la regla aplicable. Las reglas contienen segmentos semanales y fecha de vigencia. Un segmento cuyo fin es igual o anterior al inicio termina al día siguiente.
- **Correcciones:** sólo el propietario edita su OT. Una edición incrementa la revisión y reabre la aprobación, incluso si ya estaba aprobada. El periodo real registrado por Timer no se modifica.
- **Cálculo común:** sólo cuenta tiempo real aprobado. Los intervalos de OT traslapados se cuentan una vez. Las Guardias traslapadas también se unen para no duplicar cobertura. La OT aprobada se descuenta de la Guardia aprobada. Los resultados se dividen por día, incluso al cruzar medianoche o fin de mes.
- **Claim:** semanas de sábado a viernes y horas decimales. **ADP:** semanas de domingo a sábado y duración HH:MM. Son guías de captura, no conexiones externas con SAP o ADP.
- Excel exporta el tiempo aprobado del mes, Grupo, Técnico y tipo seleccionados; no exporta solicitudes pendientes como horas pagables. La exportación usa el mismo cálculo que Panel, Claim y ADP.

### Delegación y recuperación

Ser Lead no da permisos de aprobación. Desde **Mi equipo**, el Manager elige **Delegar** junto a un Lead activo y define, dentro de la misma página, los Grupos y las fechas. Sólo puede haber una persona delegada por Manager. Al sustituirla, la asignación anterior se revoca de forma atómica y se conserva su historial. El Lead delegado no puede aprobar sus propios registros. Revocar la delegación no quita la capacidad Lead. Cambiar la propiedad del Grupo o mover/quitar la capacidad del Lead revoca las delegaciones afectadas.

En el login, **¿Olvidaste tu contraseña?** registra una solicitud. El Manager, Lead delegado dentro de su alcance o un administrador valida la identidad y emite un código de 15 minutos. Nadie emite su propio código. El código es de un solo uso y cambiar la contraseña invalida las sesiones anteriores. No se envían correos automáticamente.

## Zona horaria y datos locales

La zona operativa predeterminada es **America/Mexico_City**. Los instantes se almacenan con zona horaria y los reportes se dividen por fecha operativa mexicana. Los formularios de fecha/hora se interpretan en esa zona, aunque el sistema de la Mac tenga otra zona configurada.

Puedes seleccionar otra zona operativa antes de iniciar:

```bash
PULSE_TIMEZONE=America/Mexico_City python -m uvicorn server:app --host 127.0.0.1 --port 5510
```

Puedes usar otra base para pruebas manuales sin tocar la principal:

```bash
PULSE_DB_PATH="$PWD/pruebas.db" python -m uvicorn server:app --host 127.0.0.1 --port 5511
```

No cambies la zona operativa de una base con registros sin revisar el impacto en los límites diarios. Para una copia de respaldo local, detén el servidor y copia `operational_pulse.db` a una ubicación segura. Conserva tu copia antes de sustituir carpetas entre versiones. Esta versión no importa automáticamente bases de la implementación anterior.

## Pruebas

Las pruebas usan bases SQLite temporales y aisladas; no requieren ni modifican tu base manual.

```bash
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -p 'test_api.py' -v
```

Prueba real de navegador con Chromium:

```bash
python -m playwright install chromium
python tests/browser_smoke.py
```

La prueba inicia y detiene su propio servidor local. No necesitas dejar la aplicación abierta. Los resultados ejecutados en la entrega se documentan en `VALIDATION.md`. No se ha ejecutado esta entrega en una Mac física; la validación disponible usa Linux y Chromium. Puedes probar Safari manualmente con el mismo servidor local.

Para validar sintaxis JavaScript, si tienes Node instalado opcionalmente:

```bash
node --check static/app.js
python -m py_compile server.py
```

## Estructura

```text
Operational_Pulse_v1.1.0/
  index.html
  server.py
  requirements.txt
  requirements-dev.txt
  README.md
  SPECIFICATION.md
  VALIDATION.md
  CHANGELOG.md
  THIRD_PARTY_NOTICES.md
  start.command
  .gitignore
  .vscode/
  static/
    app.js
    app.css
    favicon.svg
    kyndryl-logo.svg
    icons.svg
  tests/
    test_api.py
    browser_smoke.py
```

`/api/state` entrega el estado compartido según la sesión y el alcance autorizado. El servidor valida cada cambio mediante endpoints específicos; la interfaz no sobrescribe toda la base con un JSON global. Las contraseñas y los códigos se almacenan mediante PBKDF2 con salt aleatorio. Las sesiones usan cookies HttpOnly y SameSite; los permisos se verifican en el backend. El API local se documenta automáticamente en `/docs`.

## Más adelante: servidor

Esta entrega inicia en `127.0.0.1`, accesible sólo desde tu Mac. No publica nada en Internet. La preparación para usuarios de varias regiones —dominio, HTTPS, política de zonas horarias, copias automáticas, monitoreo, correo, capacidad y posible migración de base— se realizará como una etapa posterior. No se ha validado despliegue, carga multiusuario de producción ni compatibilidad con formatos corporativos específicos de importación.

## Identidad visual y créditos

Interfaz en azul, blanco y turquesa, con iconografía SVG de Shidoka y logotipo de Kyndryl incluido localmente. No requiere fuentes, imágenes ni servicios externos para mostrar la interfaz. El apartado **Acerca del proyecto y autores** está disponible al pie de la aplicación; también puede abrirse desde el login. Las atribuciones de los recursos se incluyen en `THIRD_PARTY_NOTICES.md`.

Autores del proyecto:

- Samuel Alejandro Díaz Chávez
- Francisco Cervantes Marquez

## Novedades de v1.0.1

Activación y recuperación ahora tienen modales propios con información por secciones, ayuda para el código, botones para mostrar la contraseña, comprobación de coincidencia y confirmaciones al terminar. El flujo de recuperación conserva el usuario y explica que el código lo entrega el responsable por un canal corporativo. La contraseña continúa requiriendo al menos 10 caracteres. El historial y el criterio de numeración están en `CHANGELOG.md`.

## Ajuste de lectura v1.0.2

Se aumenta el contraste de textos secundarios, etiquetas, ayudas y placeholders, manteniendo la composición, tamaños y paleta existentes. Los textos claros sobre fondos azules oscuros se conservan.

## Novedades de v1.1.0

- **Guardias por intervalos:** cada día admite varios horarios. Usa «Agregar intervalo» o «24 horas»; el Manager define su semana sin horarios operativos precargados. Un fin como 00:00 después de 20:00 corresponde al día siguiente. Los intervalos se muestran agrupados por día al guardar.
- **Delegación junto al equipo:** elige «Delegar» en la fila de un Lead activo. El formulario aparece dentro de Mi equipo, sin modal. Permite cambiar vigencia y alcance, sustituir al backup y revocar. Sólo hay una asignación vigente o programada por Manager; guardar otra sustituye la anterior inmediatamente, incluso si la nueva comienza después.
- **Panel que lleva a la acción:** las tarjetas del Manager abren Tiempo del equipo con tipo y estado ya seleccionados. Pendientes y timers usan «Todos los periodos» para incluir eventos anteriores al mes visible. «Ver actividad» abre el detalle del Timer con contador en vivo.
- **Solicitudes concretas:** el bloque lateral del Panel presenta hasta tres solicitudes para revisar, en lugar de repetir el contador de pendientes. El detalle permite aprobar o rechazar usando las mismas validaciones del servidor.
- **Compatibilidad:** se conserva la base existente. No se agregan datos de ejemplo ni se borran registros. Si una base antigua contiene varios backups simultáneos, sólo la última asignación activa otorga autoridad; al reasignar o revocar se consolidan conservando el historial.
