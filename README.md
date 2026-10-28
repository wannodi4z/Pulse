# Operational Pulse · 1.2.0

Aplicación nueva, creada desde cero. La numeración parte de **v1.0.0** como base del proyecto; esta versión conserva los datos existentes y amplía SQLite con metadatos compatibles. El ZIP v1.4.5 sirvió únicamente como referencia funcional; esta versión no carga sus archivos ni sus parches. Preparada para probar **localmente en macOS con VS Code**, con frontend HTML/CSS/JavaScript, FastAPI y SQLite. No requiere servicios externos, Docker, Node ni una cuenta de nube.

## Perfil Administrador · v1.2.0

La navegación administrativa contiene **Panel, Cuentas, Administradores y Recuperación de acceso**. Cuentas abre tarjetas de cada Cuenta; al entrar muestra sus Managers y el Lead directo de cada uno, sin desplegar Grupos ni Técnicos. Se pueden crear, editar y dar de baja Managers y Leads; las bajas conservan el historial y requieren resolver las transferencias pendientes. Los Administradores también se crean, editan y dan de baja; no puede darse de baja la propia cuenta ni el último Administrador activo. Una Cuenta sólo se elimina si está vacía.

El Panel presenta Cuentas registradas, Managers activos, Leads activos y recuperaciones pendientes (incluidos códigos vencidos). Muestra una gráfica y tabla de Managers por Cuenta, búsqueda por Cuenta/Manager/Lead y filtro por país. Los indicadores generales abarcan toda la organización; los filtros afectan la distribución por Cuenta. Los pendientes permiten abrir Cuentas sin Manager, Managers sin Lead, accesos por activar y recuperaciones.

**Las recuperaciones de Administradores, Managers y Leads corresponden a Admin**, salvo la propia solicitud, que debe resolver otro Administrador. Las de Técnicos siguen llegando a su Manager activo; sin responsable activo las atiende Admin. Se conservan la consulta y regeneración de códigos, su vigencia y el uso único.

Esta entrega se concentra en el perfil Admin. Se conservan los flujos operativos de los demás roles y las herramientas existentes de mantenimiento de estructura; no incorpora todavía un nuevo kanban ni transfiere la administración de Técnicos a Managers.

Descomprime en una **carpeta nueva** para cargar los ejemplos: dos Cuentas, dos Managers por Cuenta, cuatro Leads y doce Técnicos. Los datos de ejemplo no limitan cuántas personas puedes agregar. No reemplaces tu base de trabajo para actualizar: respáldala y conserva su archivo y su clave de recuperación. El arranque no sobrescribe una base existente.

Validación de esta versión: 59 pruebas de API; recorrido Admin en Chromium con indicadores, filtros, creación de Cuenta/Administrador/Manager/Lead, preservación de Grupos al editar Manager y generación/consulta/regeneración de códigos. Se comprobaron límites de pantalla a 1440×780, 1366×700, 1280×650 y 390×844; el Panel inicial de dos Cuentas cabe sin desplazamiento en los tres tamaños de escritorio. Con más registros, el contenido central tiene desplazamiento interno. También se validaron sintaxis JavaScript y compilación Python. No se probó en un Mac físico ni en Safari.

Las notas de versiones anteriores se conservan debajo como historial; prevalece esta sección.

## Ajustes de Organización · v1.1.5

Vista detallada fija sin botón de alternancia. Cada Cuenta muestra todos sus Managers, incluso sin Grupos; se eliminó el selector que ocultaba a los demás. Los botones Editar Lead, su menú y las acciones del Manager comparten fila y altura. Si hay muchos equipos, el área central tiene desplazamiento interno para conservarlos accesibles.

Validación: sintaxis JavaScript, compilación Python y flujo Admin en Chromium a 1440×780, 1366×700 y 1280×650; creación de un tercer Manager, su Lead y su Grupo. No se ejecutaron pruebas en un Mac físico.

## Proyecto completo de pruebas · v1.1.4

Descomprime en una **carpeta nueva**, instala dependencias e inicia con `bash start.command`, F5 o uvicorn. La primera apertura prepara automáticamente **dos Cuentas, dos Managers por Cuenta (cuatro en total), cuatro Leads directos y doce Técnicos** desde la base incluida en `fixtures/banorte_pruebas.sqlite3`.

| Cuenta | Employee ID | Contraseña | Perfil |
| --- | --- | --- | --- |
| Banorte · MX-BNTE | MGR0001 | manager12026 | Yao Pegueros · Manager |
| Banorte · MX-BNTE | SL0001 | lead120261 | Francisco Cervantes Marquez · Lead |
| Banorte · MX-BNTE | 951357 | tecnico12026 | Samuel Alejandro Díaz Chávez · Técnico |
| Banorte · MX-BNTE | TEC0002–TEC0006 | tecnico12026 | Cinco Técnicos adicionales |
| Acme México · MX-ACME | MGR0002 | manager22026 | Mariana Torres · Manager |
| Acme México · MX-ACME | SL0002 | lead220261 | Luis Navarro · Lead |
| Acme México · MX-ACME | TEC0007–TEC0012 | tecnico12026 | Seis Técnicos adicionales |
| Banorte · MX-BNTE | MGR0003 | manager32026 | Roberto Salinas · Segundo Manager |
| Banorte · MX-BNTE | SL0003 | lead320261 | Valeria Mendoza · Lead de MGR0003 |
| Acme México · MX-ACME | MGR0004 | manager42026 | Patricia Ramos · Segundo Manager |
| Acme México · MX-ACME | SL0004 | lead420261 | Diego Ortega · Lead de MGR0004 |

Hay quince Grupos: nueve en Banorte y seis en Acme. Cada Cuenta tiene dos Managers de ejemplo; **no es un límite**, puedes agregar tantos Managers, Grupos y Técnicos como necesites. Todos los usuarios de ejemplo están activos; no hay OT, Guardias, Timers, delegaciones ni sesiones precreadas. admin1/admin2 conservan sus accesos iniciales. Cada Lead está directamente bajo su Manager, sin Grupo, sólo con OT y autoridad de aprobación únicamente al delegar.

Una base existente **nunca se sustituye al iniciar**. Para incorporar los ejemplos en tu carpeta anterior, detén el servidor y ejecuta `bash configurar_banorte.command`; ahora prepara ambos equipos. Ese configurador explícito conserva a los demás usuarios y sus registros; establece las tres contraseñas originales solicitadas y el nombre de Samuel para 951357. Los accesos adicionales ya existentes conservan sus contraseñas, estado y pertenencia. Los reinicios normales no restauran ejemplos borrados ni restablecen contraseñas.

Una instalación limpia sin ejemplos sigue disponible definiendo `PULSE_DB_PATH` a otra ruta o retirando `fixtures` antes de iniciar. Se crean sólo admin1/admin2.

## Agregar Managers, Grupos y Leads

1. En **Organización**, abre la Cuenta y pulsa **Agregar Manager**, visible en su cabecera. Crea y activa su acceso. Al terminar, la vista selecciona automáticamente al nuevo Manager.
2. En la cabecera del Manager pulsa **Agregar Lead**. El formulario ya trae ese Manager seleccionado y no pide Grupo. Guarda y comparte el código de activación. Puede registrar OT; no solicita Guardias y sólo aprueba al equipo con delegación.
3. Si aparece **Editar Lead**, ese Manager ya tiene uno. Los cuatro Managers de ejemplo lo tienen asignado. El máximo es un Lead vigente por Manager, no dos. Admin puede editarlo o gestionar su baja/cambio con historial conservado; un Manager sin Lead muestra Agregar Lead.
4. **Agregar Grupo** dentro del Manager abre el formulario con Cuenta y Manager seleccionados. El botón de la Cuenta permite elegir el responsable al crear el Grupo.

El selector **Manager / equipo** de la Cuenta permite abrir cualquier Manager directamente. Los botones Editar Manager y Editar Lead tienen etiquetas distintas y espacio propio; se muestra el nombre completo del Lead.

## Organización con cuatro Grupos y organizador por arrastres

La vista inicial muestra **hasta cuatro Grupos en una cuadrícula 2×2** en escritorio. Cada tarjeta muestra nombre y cantidad de Técnicos; pulsa esa cantidad para abrir el detalle. **Vista detallada** conserva las tarjetas individuales y el arrastre habitual. **Ver 4 Grupos** vuelve al resumen. Cuenta y Manager mantienen su jerarquía; el Lead aparece en la cabecera del Manager como backup, con **Agregar Lead** si no hay uno y **Editar Lead** si ya está asignado. Nunca consume un espacio de Grupo.

**Organizar Técnicos** abre un diálogo amplio con dos columnas, origen y destino. Selecciona Grupos incluso de distintas Cuentas, busca por nombre/Employee ID y arrastra; las flechas son la alternativa accesible al arrastre. Puedes preparar varios cambios, deshacerlos, cancelar o revisar el resumen. **Nada se guarda al arrastrar**: indica un motivo y confirma para aplicar todos los movimientos juntos.

Si algún Técnico tiene Timer activo, cambió de Grupo o perdió acceso, el servidor rechaza la operación completa. Leads y usuarios en baja no se arrastran. Se conservan OT, Guardias, historial y origen; se actualiza la autoridad del responsable y se cierran las sesiones de las personas movidas. Las listas del diálogo se paginan según el espacio disponible, sin scroll de página/modal ni reducción del zoom.

## Cambios de esta entrega · v1.1.1

- **Lead directo del Manager, sin Grupo.** Máximo uno por Manager. Puede registrar OT, usar Timer y consultar sus propias horas, Claim y ADP; **no puede solicitar Guardias**. Sólo aprueba/rechaza solicitudes de los Grupos del Manager mientras éste mantenga activa la delegación; nunca su propia OT. El Manager autoriza la OT del Lead.
- Admin crea/edita al Lead desde Organización, bajo su Manager. Puede cambiarlo de Manager con motivo, conservando sus registros y revocando la autoridad anterior. Antes de moverlo debe detenerse su Timer. La baja del Manager exige asignar destino para el Lead además de sus Grupos.
- Las designaciones Lead anteriores dentro de un Grupo pasan a relación directa con el mismo Manager al actualizar. No se eliminan OT, Guardias anteriores, tramos, códigos ni historial. Las Guardias anteriores se conservan para consulta; no habilitan nuevas solicitudes de Guardia del Lead.
- **Nuevo Grupo** tiene Cuenta, Manager, Especialidad y Nombre. Busca una especialidad o escribe una nueva: se incorpora al catálogo de esa Cuenta. Plataforma deja de ser un campo obligatorio visible. Ejemplo: especialidad «Linux y Oracle», Grupo «Distribuidos · Producción», código automático `MX-BNTE-LINUX-Y-ORACLE`. Los códigos existentes conservan su identidad.
- Solicitudes de cambio vacías usan un diálogo compacto. Formularios de Grupo con ancho reducido y código como referencia pequeña.

Para preparar los accesos de ejemplo en la **base principal**, instala dependencias, detén la instancia anterior y ejecuta:

```bash
bash configurar_banorte.command
```

Se reutiliza Banorte/MX-BNTE, con MGR0001 (`manager12026`), Lead directo SL0001 (`lead120261`) y Técnico 951357 (`tecnico12026`), activos, además de seis Grupos de prueba. No se crea delegación automática ni registros operativos. **Conserva tu `operational_pulse.db` y su `.key` al actualizar**; el ZIP no los sustituye. Los inicios normales siguen creando únicamente admin1/admin2 en una base vacía. El configurador explícito establece las contraseñas solicitadas para esos tres accesos; los demás datos y usuarios se conservan.

Las descripciones de ciclos anteriores más abajo son históricas; esta sección y la especificación actual definen el comportamiento vigente del Lead.

## Ejecutarla en tu Mac

Necesitas Python **3.11 o posterior** y VS Code. Puedes comprobarlo en la terminal con `python3 --version`. Si tu Mac tiene varias versiones, usa, por ejemplo, `python3.12` para crear el entorno.

1. Descomprime el ZIP y abre en VS Code la carpeta que contiene `server.py`: **File → Open Folder**. Desde GitHub se llama `Pulse-main`; en el ZIP de la entrega se llama `Operational_Pulse_v1.1.4`.
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
7. Como Manager, crea una regla de Guardia en **Reglas de guardia** y, si hace falta, una delegación hasta revocación manual desde **Mi equipo**.
8. Como Técnico, usa **Mi tiempo** para OT programada, histórica, emergencia o solicitudes de Guardia. **Claim** y **ADP** muestran el tiempo aprobado del mes.
9. Como Manager o Lead delegado, revisa **Aprobaciones**, filtra y aprueba o rechaza con motivo.

### Organización

La interfaz anida **Cuenta → Managers → Grupos → Técnicos**. Los Grupos sin Manager tienen su propia sección dentro de la Cuenta. Un Manager pertenece a una sola Cuenta y puede tener varios Grupos; cada Grupo tiene un único Manager. Lead es una capacidad del mismo Técnico, con el mismo acceso, propiedad de timers e historial; no es otra persona ni otro nivel del organigrama.

Una Cuenta con Grupos no se puede eliminar. Si tiene Managers, primero deben moverse. Un Grupo con Técnicos debe vaciarse antes de eliminarlo; si tiene ventanas de OT compartida se conserva para mantener su historial. Deshabilitar una persona conserva sus registros. No puedes deshabilitar tu propia cuenta administradora ni al último administrador activo.

### OT, Guardias y timers

- **OT programada individual:** la persona define el periodo y referencia CHG/INC. Debe aprobarse antes de iniciar. El botón Iniciar está disponible durante la ventana aprobada. Al detenerse, el tiempo real vuelve a aprobación.
- **OT histórica:** registra tiempo que ya terminó y envíalo a aprobación.
- **OT programada:** cada Técnico solicita su propia OT desde Mi tiempo. El Manager o Lead delegado revisa y autoriza; no publica actividades ni captura OT propia. Las participaciones de publicaciones anteriores se conservan.
- **Emergencia:** Iniciar emergencia crea el Timer inmediatamente. Detener genera un registro pendiente de documentación sin exigir un formulario en ese momento. Luego completa CHG/INC, descripción, justificación, impacto y motivo de no usar tiempo compensatorio para enviarlo.
- Sólo hay un Timer activo por Técnico. El propietario es quien lo detiene. Manager y Lead delegado pueden monitorear los timers de su alcance.
- **Guardias:** cada solicitud es independiente por ID y conserva una copia de la regla aplicable. Las reglas contienen segmentos semanales y fecha de vigencia. Un segmento cuyo fin es igual o anterior al inicio termina al día siguiente.
- **Correcciones:** sólo el propietario edita su OT. Una edición incrementa la revisión y reabre la aprobación, incluso si ya estaba aprobada. El periodo real registrado por Timer no se modifica.
- **Cálculo común:** sólo cuenta tiempo real aprobado. Los intervalos de OT traslapados se cuentan una vez. Las Guardias traslapadas también se unen para no duplicar cobertura. La OT aprobada se descuenta de la Guardia aprobada. Los resultados se dividen por día, incluso al cruzar medianoche o fin de mes.
- **Claim:** semanas de sábado a viernes y horas decimales. **ADP:** semanas de domingo a sábado y duración HH:MM. Son guías de captura, no conexiones externas con SAP o ADP.
- Excel exporta el tiempo aprobado del mes, Grupo, Técnico y tipo seleccionados; no exporta solicitudes pendientes como horas pagables. La exportación usa el mismo cálculo que Panel, Claim y ADP.

### Delegación y recuperación

Ser Lead no da permisos de aprobación. Desde **Mi equipo**, el Manager elige **Delegar** junto a su Lead activo; cubre todos sus Grupos, inicia al guardar y termina por revocación manual. Sólo puede haber una persona delegada por Manager. Al sustituirla, la asignación anterior se revoca de forma atómica y se conserva su historial. El Lead delegado no puede aprobar sus propios registros. Revocar la delegación no quita la capacidad Lead. Cambiar la propiedad del Grupo o mover/quitar la capacidad del Lead revoca las delegaciones afectadas.

En el login, **¿Olvidaste tu contraseña?** registra una solicitud. El Manager valida a sus Técnicos; Administración valida a Managers, otros administradores y Técnicos sin Manager activo. Un Lead no emite ni consulta códigos, aunque tenga delegación operativa. Nadie emite su propio código. El código es de un solo uso y cambiar la contraseña invalida las sesiones anteriores. No se envían correos automáticamente.

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

No cambies la zona operativa de una base con registros sin revisar el impacto en los límites diarios. Para una copia de respaldo local, detén el servidor y copia `operational_pulse.db` y, si existe, `operational_pulse.key` a una ubicación segura. La clave permite volver a consultar códigos de recuperación vigentes; no debe subirse a GitHub ni compartirse con usuarios. Conserva tu copia antes de sustituir carpetas entre versiones. No se importa automáticamente el esquema del ZIP original v1.4.5. Las bases de esta nueva línea v1.0.x y v1.1.x se conservan al actualizar el código.

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
Operational_Pulse_v1.1.4/
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

`/api/state` entrega el estado compartido según la sesión y el alcance autorizado. El servidor valida cada cambio mediante endpoints específicos; la interfaz no sobrescribe toda la base con un JSON global. Las contraseñas y verificadores de códigos se almacenan mediante PBKDF2 con salt aleatorio. Para consultar un código de recuperación vigente, su valor se guarda además cifrado con Fernet; la clave local se conserva fuera de SQLite y del repositorio. Las sesiones usan cookies HttpOnly y SameSite; los permisos se verifican en el backend. El API local se documenta automáticamente en `/docs`.

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

## Flujos incorporados en el ciclo inicial (referencia histórica)

- **Guardias por intervalos:** cada día admite varios horarios. Usa «Agregar intervalo» o «24 horas»; el Manager define su semana sin horarios operativos precargados. Un fin como 00:00 después de 20:00 corresponde al día siguiente. Los intervalos se muestran agrupados por día al guardar.
- **Delegación junto al equipo:** elige «Delegar» en la fila de un Lead activo. El formulario aparece dentro de Mi equipo, sin modal. Cubre todos los Grupos del Manager y permite sustituir al backup o revocar. Inicia al guardar y no vence automáticamente. Sólo hay una asignación vigente por Manager.
- **Panel que lleva a la acción:** las tarjetas del Manager abren Aprobaciones con tipo y estado ya seleccionados. Pendientes y timers usan «Todos los periodos» para incluir eventos anteriores al mes visible. «Ver actividad» abre el detalle del Timer con contador en vivo.
- **Solicitudes concretas:** el bloque lateral del Panel presenta hasta tres solicitudes para revisar, en lugar de repetir el contador de pendientes. El detalle permite aprobar o rechazar usando las mismas validaciones del servidor.
- **Compatibilidad:** se conserva la base existente. No se agregan datos de ejemplo ni se borran registros. Si una base antigua contiene varios backups simultáneos, sólo la última asignación activa otorga autoridad; al reasignar o revocar se consolidan conservando el historial.

## Enfoque de la herramienta · v1.1.1

Los textos del acceso y Mi tiempo se centran en el control de horas extra (OT), Guardias y sus aprobaciones. Se retiran las referencias a comenzar una jornada; la herramienta no se presenta como un control de asistencia. También se incluye el botón del ojo para mostrar u ocultar la contraseña en el login. No cambia la lógica operativa.

## Analítica mensual · v1.0.0

- **Manager:** «Tiempo del equipo» muestra sus Grupos y Técnicos.
- **Lead:** «Mi resumen» contiene sus horas; «Tiempo del equipo» sólo aparece y funciona con delegación vigente y para todos los Grupos actuales del Manager. Revocar la delegación bloquea las consultas y exportaciones del equipo en el servidor.
- **Técnico:** «Mi resumen» consulta únicamente al propietario de la sesión; no ofrece filtros de otras personas o Grupos.
- **Admin:** administra estructura y accesos; no tiene acceso a esta analítica operativa.

El desglose separa **OT emergente, OT programada, OT histórica y Guardia neta**, con totales por Grupo, Técnico y día. Usa sólo tiempo real aprobado: una OT programada sin ejecutar y las solicitudes pendientes no suman horas. Los traslapes se deduplican antes de agrupar y la Guardia descuenta la OT aprobada que se traslapa. Los totales coinciden con el cálculo de Claim, ADP y Excel. Los registros que cruzan medianoche o fin de mes se dividen en la zona operativa. La agrupación por Grupo usa la asignación actual del Técnico.

Elige el mes; en el equipo, selecciona Grupo y/o Técnico. Las tarjetas abren el detalle por tipo, las filas de Grupo llevan a sus Técnicos y cada Técnico permite abrir sus horas diarias. Excel exporta **Resumen, Por grupo, Por técnico y Detalle**, respetando los mismos filtros y permisos.

## Administración y recuperación · v1.0.0

Las altas y los cambios organizacionales de Cuentas, Managers, Grupos y Técnicos corresponden exclusivamente a Admin. Manager consulta Mi equipo, gestiona el tiempo y asigna/revoca su backup; no crea, mueve ni edita personas. Cada usuario conserva Mi perfil para sus propios datos personales y contraseña, sin poder cambiar allí Employee ID, Grupo, rol ni capacidad Lead.

Las solicitudes se muestran al responsable: **Técnico → su Manager activo; Manager o administrador → otro administrador**. Si un Técnico no tiene Manager activo, lo atiende Administración. Nadie puede emitir o consultar su propio código. Lead no recibe estas solicitudes. No se envía correo automáticamente.

Después de validar identidad, el responsable puede:

- **Generar código:** crea un código de 15 minutos.
- **Ver código:** muestra el mismo código vigente sin extender su plazo.
- **Regenerar:** invalida el anterior y comienza un plazo nuevo.

Usar el código invalida la solicitud y las sesiones anteriores. No se crean solicitudes abiertas duplicadas para la misma persona. Los códigos de versiones anteriores siguen siendo verificables si no vencieron, pero no pueden recuperarse de su hash: deben regenerarse una vez para disponer de «Ver código». La base nueva agrega sólo una tabla de valores cifrados; no borra datos ni reinicia cuentas.

### Actualizar una instalación local

1. Detén el servidor con Control+C y respalda tu `.db` y su `.key`, si existe.
2. Actualiza los archivos del proyecto conservando esos archivos. Si usas una carpeta nueva, lleva allí tu base y su clave antes de iniciar.
3. En la carpeta del proyecto ejecuta:

   ```bash
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   bash start.command
   ```

Si la carpeta no tiene `.venv`, sigue primero la instalación inicial. Esta versión agrega `cryptography`; hay que actualizar dependencias aunque ya tuvieras una versión anterior funcionando. La clave local se genera al emitir el primer código y queda excluida del código fuente y del ZIP. Con `PULSE_DB_PATH`, la clave usa la misma ubicación y nombre base, con extensión `.key`; puede configurarse otra ubicación con `PULSE_RECOVERY_KEY_PATH`.


## Administración del ciclo de vida · v1.0.0

Sólo Admin crea, edita, transfiere, da de baja y reactiva personas. **Transferir y dar de baja son acciones independientes.** Manager gestiona tiempo y recuperaciones, sin editar la estructura.

- **Transferir Técnico activo:** en Organización, pulsa Transferir junto a la persona, elige un Grupo con Manager activo y explica el motivo. Conserva identidad, estado e historial. No se permite mover un Técnico con Timer en curso: primero debe detenerlo. Su sesión se invalida para aplicar el acceso nuevo; vuelve a entrar con su contraseña. La capacidad Lead se conserva si no genera un segundo backup para el Manager de destino; para cambiar al backup, Admin debe retirar primero la designación correspondiente.
- **Transferir Grupo activo:** pulsa Transferir en el Grupo. Elige otro Manager activo de la misma Cuenta. Conserva todos los integrantes, registros y timers de los Técnicos en ejecución. Revoca las delegaciones afectadas, sin desactivar a nadie. Si coinciden dos Leads bajo el destino, se rechaza toda la operación; Admin decide antes qué designación retirar.
- **Un Lead por Manager:** el técnico designado es el backup de ese Manager, incluso si administra varios Grupos. Designarlo no otorga aprobación. La delegación cubre todos los Grupos del Manager; él la activa o revoca manualmente. Las bases anteriores con varios Leads no se borran ni corrigen silenciosamente: Organización muestra una advertencia y Admin debe retirar las designaciones adicionales. Las nuevas escrituras impiden crear el conflicto.
- **Baja de Manager:** revisa el impacto y asigna cada Grupo a otro Manager activo de la misma Cuenta. Si el reemplazo es nuevo, créalo y activa su acceso primero; el titular permanece activo hasta confirmar el traspaso. Se puede repartir el equipo entre varios Managers. Los Grupos y Técnicos conservan sus IDs e historial y los Técnicos continúan activos; sus timers siguen en ejecución. La operación completa ocurre en una sola transacción.
- **Baja de Técnico:** revisa los pendientes. Si tiene Timer activo, Admin debe autorizar su cierre en ese momento y completar la documentación de cualquier OT de emergencia pendiente. El tiempo ya realizado queda enviado a aprobación del responsable del Grupo. Las OT programadas individuales sin ejecutar se cancelan. Las Guardias aún no iniciadas se cancelan; las que ya iniciaron conservan cobertura hasta la hora de la baja, incluyendo cruces de medianoche. Claim, ADP, Excel y analítica usan ese mismo límite. No se elimina el historial.
- **Seguridad de la baja:** retira acceso, sesiones, activación y capacidad Lead, revoca delegaciones y cancela las recuperaciones propias. No permite la baja del Admin que ejecuta la acción ni del último Admin activo. Los códigos emitidos por el responsable saliente y los de Técnicos que cambian de Manager se invalidan y las solicitudes quedan pendientes para el nuevo responsable. Los códigos no se transfieren.
- **Reactivar:** requiere motivo y genera una activación nueva; la persona define una contraseña nueva. Conserva identidad e historial, pero no restaura Lead, delegaciones, Grupos del antiguo Manager, timers ni coberturas canceladas. Un Manager heredado en baja que aún tiene Grupos requiere regularizar primero el traspaso mediante la revisión de baja.
- **Revisión vigente:** la baja exige un resumen firmado por hash de la situación revisada. Si cambia el equipo o los pendientes, se rechaza con 409; cierra y vuelve a abrir la revisión. Motivos, movimientos, cierres y cambios de acceso quedan en auditoría.

El login dice **Planea. Trabaja. Controla.** Los diálogos se ampliaron, los formularios usan columnas en escritorio y muestran instrucciones. Las confirmaciones usan el diálogo de la aplicación. Los formularios extensos se recorren por pasos conservando los campos y sus valores.


### Escala de pantalla v1.0.0

Usa el zoom normal del navegador (100%). Los diálogos ajustan ancho, columnas y espaciado al área disponible, con etiquetas de 14 px y controles de 15 px. La baja de Manager separa destinos de reemplazo/motivo; las acciones quedan al pie y los botones de Organización tienen una fila definida. En reglas de Guardia, selecciona cada día para editarlo: al guardar se conserva la configuración de toda la semana. Si hay muchos pendientes se utilizan pasos y paginación, manteniendo visibles el título y las acciones.


## Interfaz sin desplazamiento · v1.0.0

La aplicación se organiza en vistas dentro del área disponible al 100% de zoom. **Vista**, Anterior y Siguiente permiten recorrer las secciones de una página. Las listas y tablas grandes se paginan: no se eliminan filas ni se reduce artificialmente la escala. En Organización se mantienen Cuenta → Manager → Grupo → Técnico, con controles para recorrer Managers, Grupos y Técnicos.

Los formularios que superan la altura disponible se dividen en pasos. Completa cada paso y pulsa Continuar; puedes regresar sin perder lo escrito. Guardar o Enviar aparece en el último paso. Cambiar de paso no envía datos al servidor. Los campos obligatorios se validan y, si falta uno, se abre su paso antes de señalarlo.

El sidebar contiene la operación diaria; Configuración agrupa las opciones secundarias del rol. Mi perfil y Cerrar sesión están en el menú del usuario, arriba a la derecha. Se conserva la marca Kyndryl y la versión, sin textos repetidos al pie.

**Reglas de Guardia:** el Manager propietario tiene Editar y Eliminar. Editar permite cambiar nombre, vigencia e intervalos. Eliminar retira la plantilla para solicitudes nuevas. Las solicitudes anteriores guardan su propia copia y conservan cobertura, aprobaciones y horas incluso si la regla se modifica o elimina. Eliminar pide confirmación. Otro Manager, Admin y Técnico no pueden editar o eliminar la regla ajena mediante la API.


## Limpieza de flujos y reinicio de versión

Esta entrega se identifica como **v1.0.0** por solicitud del autor. El reinicio es del contador; conserva el modelo SQLite y los datos existentes. El historial de entregas previas permanece en CHANGELOG.

Organización abre el resumen y la estructura juntos. Si existe una sola Cuenta, no se muestra un selector de pantallas; cuando hay varias, se elige la Cuenta desde el mismo espacio. Tiempo del equipo conserva sus filtros junto a los registros; Mi tiempo conserva acciones y totales con OT/Guardias; Claim y ADP presentan el resumen sobre las semanas. Analítica combina totales, gráficas y criterios y mantiene los filtros al cambiar entre desglose por Grupo, Técnico y detalle. El Panel de Admin presenta Cuentas con acceso directo a su estructura y tareas de accesos/asignación. La firma Kyndryl acompaña a la identidad del producto en la parte superior del sidebar; Configuración tiene un engranaje propio y Organización su jerarquía.


## Acabados y acciones · v1.0.1

La versión actual continúa desde la base v1.0.0, manteniendo datos, modelo y flujos. Cuenta, Manager y Grupo tienen niveles visuales diferenciados; se conserva la tipografía legible y el ajuste al 100%.

La acción habitual permanece visible en cada bloque. El botón de tres puntos abre las acciones secundarias:

- Cuenta: Agregar Manager, Editar Cuenta y Eliminar Cuenta.
- Manager: editar datos cuando tiene activación pendiente, o revisar Baja/Reactivar según su estado. La activación o edición habitual permanece en la tarjeta.
- Grupo: Editar Grupo, Transferir Grupo y Eliminar Grupo; Agregar Técnico queda visible.
- Técnico: Transferir Técnico, generar activación cuando corresponda y Baja/Reactivar. Editar queda visible.

Las operaciones de eliminación y baja conservan sus revisiones y confirmaciones. Los menús se cierran con Escape o al hacer clic fuera, permiten navegar con flechas y no se recortan dentro de las tarjetas. No se han movido al menú acciones operativas como detener un Timer o aprobar tiempo.


[Ver capturas del tablero y el traslado](docs/interface-v1.2.0.md)

## Diseño Enterprise luminoso

Nueva interfaz elegida por Samuel: sidebar claro, navegación en azul profundo, acentos turquesa y marca corporativa Kyndryl en la cabecera. Acerca del proyecto está al pie del sidebar; el menú del usuario conserva Mi perfil y Cerrar sesión.

La presentación visual se define en **static/design.css**; **static/app.css** conserva la estructura de componentes y los contratos de ajuste al viewport. La entrega reemplaza el acabado anterior y mantiene un único flujo de navegación y renderizado.

Las Cuentas nuevas ofrecen Agregar Manager como primera acción. Agregar Grupo sigue disponible en el menú de la Cuenta, incluso antes de asignar Manager. Las Cuentas con Managers mantienen Agregar Grupo visible. Los menús presentan opciones con iconos, sin apilar botones enmarcados. Los mismos permisos, validaciones y confirmaciones siguen aplicándose.

Se conserva el ajuste al 100% de zoom, con paginación de listas y pasos para formularios extensos. Las capturas de documentación usan datos de pruebas aislados; la instalación nueva continúa únicamente con admin1 y admin2.


## Organización directa · v1.2.0

En Admin → Organización, los Grupos se muestran lado a lado cuando hay espacio. Arrastra un Técnico desde su asa de puntos y suéltalo sobre otro Grupo. También aparece una bandeja con destinos alternativos y Elegir otro Grupo. Los destinos inválidos se señalan; un Técnico con Timer activo no se puede arrastrar.

Al soltar aparece una revisión con persona, origen y destino. Elige un motivo frecuente o escribe el tuyo y confirma. **Soltar no guarda cambios; cancelar conserva la asignación original.** Si ya soltaste sobre un Grupo, el destino viene seleccionado; Cambiar Grupo permite elegir otro. La acción Mover de la tarjeta ofrece el mismo flujo sin arrastrar, también con teclado.

Abre la edición desde el nombre de la Cuenta, Manager o Grupo, o desde la tarjeta del Técnico. Los diálogos tienen cabecera contextual y mantienen las validaciones actuales.

Sólo Admin puede trasladar personas. Se requiere un Manager de destino activo, se conserva la capacidad Lead y no se permite reunir dos Leads bajo un mismo Manager. Primero detén el Timer activo. El traslado conserva identidad e historial, revoca la delegación afectada y actualiza el acceso, solicitando nuevo inicio de sesión al Técnico.

El servidor comprueba el Grupo original dentro de la transacción. Si alguien ya movió a la persona, rechaza con 409 y pide actualizar la vista. El traslado utiliza los datos vigentes de identidad, sin reescribirlos con una copia antigua del navegador.

## Política de versión

Durante la estabilización se incrementan correcciones dentro de **v1.0.x**. Sólo se cambiará a **v1.1.x** cuando el usuario lo indique explícitamente.

## Backup del Manager · v1.0.1

Delegar cubre automáticamente **todos los Grupos actuales del Manager**. No se seleccionan Grupos y no hay vencimiento automático. El Lead puede aprobar y rechazar OT del equipo, con bloqueo de autoaprobación; nunca recibe autoridad sobre otros Managers. Los Grupos nuevos del Manager se incluyen automáticamente. El Manager puede revocar desde Mi equipo.

## Reglas de Guardia · v1.0.2

Cada día indica cuántos intervalos tiene configurados. Agregar o eliminar intervalos actualiza la paginación del editor sin descartar los valores de otras páginas o días. Las tarjetas resumen la semana; al editar se recuperan todos los intervalos guardados.

Regresión de navegador: `PULSE_CHROMIUM_EXECUTABLE=/usr/bin/chromium .venv/bin/python tests/rules_browser.py` (usa una SQLite temporal, no modifica la base de trabajo).

## Revisión y consulta · v1.0.3

- **Aprobaciones** abre las solicitudes pendientes de todos los periodos.
- **Tiempo del equipo** agrupa las pestañas Analítica e Historial. La analítica suma horas reales aprobadas; el historial conserva estados, filtros y trazabilidad, incluyendo las solicitudes pendientes. Excel mantiene su alcance y exporta tiempo aprobado.
- Una regla de Guardia vigente hoy no aplica a solicitudes que empiezan antes de su fecha de vigencia. El formulario muestra las fechas en texto, limita la fecha mínima y explica el problema antes de enviar.

## Localizar Grupos y editar estructura · v1.0.4

En Organización, escribe el nombre o código del Grupo, Cuenta o Manager. Selecciona un resultado para abrirlo directamente, incluso si está en otra Cuenta o página. Las flechas del teclado seleccionan resultados; Enter abre el Grupo y Escape cierra la lista. Si hay muchos resultados, precisa la búsqueda. Se conserva la jerarquía y el arrastre de Técnicos.

Los diálogos de Cuenta y Grupo usan anchos proporcionales y botones Crear Cuenta/Crear Grupo. La administración continúa siendo exclusiva de Admin.

[Ver capturas de la búsqueda y los diálogos](docs/interface-v1.0.4.md).

## Banorte y usuarios activos en la base principal · v1.1.0

Después de instalar dependencias, **detén el servidor actual con Control+C** y ejecuta desde la carpeta del proyecto:

```bash
bash configurar_banorte.command
```

El comando configura la **base principal**, conserva los datos existentes y abre http://127.0.0.1:5510. No depende del modo separado de pruebas de v1.0.5.

| Employee ID | Contraseña inicial | Perfil |
| --- | --- | --- |
| MGR0001 | manager12026 | Manager |
| SL0001 | lead120261 | Lead directo del Manager, sin Grupo; sólo OT |
| 951357 | tecnico12026 | Técnico |

Primero crea o reutiliza Banorte (clave BNTE, país MX). Dentro de esa Cuenta crea o reutiliza el Manager y seis Grupos de prueba: z/OS, CICS/MQ, Db2, Linux, Unix y Oracle. Asigna los Técnicos a sus Grupos; si ya pertenecen a ese equipo, conserva su pertenencia, nombres e historial. El Lead requiere que su Manager active Delegar para aprobar.

Este comando **explícito** establece las contraseñas solicitadas, activa esos tres accesos y conserva a los demás usuarios. Si detecta un rol, baja o equipo incompatible, cancela toda la configuración sin transferir personas automáticamente. No crea OT, Guardias, reglas, Timers ni delegación. Ejecutarlo otra vez no duplica los Grupos ni reinicia los datos operativos. Para los inicios siguientes basta `bash start.command`.

El ZIP contiene código y este configurador, **no tu base ni sesiones**. Para actualizar tu Mac, conserva `operational_pulse.db` junto a `server.py` (y su archivo de clave si ya existe). El inicio normal sigue creando sólo admin1/admin2 en una base vacía. El antiguo `iniciar_pruebas.command` continúa disponible como opción aislada de desarrollo; no es el configurador de Banorte.

## Cuentas y especialidades internacionales

**Cuenta → Managers → Grupos por especialidad → Técnicos**, con un Lead como backup directo de cada Manager. País es un dato de la Cuenta; puede haber varias Cuentas en el mismo país.

Elige país y clave al crear la Cuenta: `MX-BNTE`. Al crear un Grupo, selecciona Cuenta, Manager, especialidad (busca o escribe una nueva) y nombre. El código se genera automáticamente: `MX-BNTE-LINUX-Y-ORACLE`, y recibe `-02`, `-03` si se repite. El catálogo guarda las especialidades por Cuenta. Mainframe/OPEN ya no se exige en el formulario; las clasificaciones y códigos anteriores se mantienen para compatibilidad. Un Manager puede tener cualquier combinación de especialidades de su Cuenta.

Se conservan IDs, claves anteriores, integrantes e historial. Una Cuenta anterior sin país debe editarse para asignarlo antes de crear Grupos con códigos automáticos. Un cambio de Manager dentro de la Cuenta conserva la clave del Grupo.

## Analítica e historial en un mismo lugar

**Analítica** reúne registros y métricas. Buscar una referencia, persona, Employee ID, Grupo o texto recalcula la lista y las horas sobre los mismos resultados. La búsqueda inicial consulta todo el historial; puedes limitar el periodo, Grupo, Técnico, tipo o estado. Pendientes y rechazados se ven como registros, pero no suman horas aprobadas. Guardia neta siempre descuenta la OT aprobada que se traslapa, aunque la búsqueda oculte esa OT.

**Comparar meses** agrega dos o más periodos con los mismos filtros (hasta 24 meses). **Ver gráficas** muestra comparación mensual y distribución por Grupo/Técnico; Excel contiene los mismos resultados y periodos. Sólo Manager o Lead con delegación activa acceden al equipo; el Técnico conserva su resumen personal.

**Aprobaciones** muestra exclusivamente solicitudes y extensiones pendientes de todos los periodos. Las consultas históricas pertenecen a Analítica; los Timers del equipo siguen visibles en Panel.

## Cambios de Grupo y especialidad · v1.1.0

Admin puede mover un Técnico activo desde Organización, arrastrándolo o con Mover Técnico. También puede atender solicitudes del Manager: **Mi equipo → Solicitar cambio**, indicando destino y motivo; Admin abre **Organización → Solicitudes de cambio → Revisar y trasladar**, selecciona el Grupo definitivo y confirma. Puede rechazar con motivo; el Manager consulta el resultado en Mis solicitudes de cambio.

La solicitud no cambia permisos ni pertenencia. El traslado conserva la identidad, OT, Guardias, aprobaciones, capturas y tramos del Técnico. El nuevo responsable ve sus pendientes y registros; el Técnico conserva su historial y horas personales. Las capturas nuevas guardan el Grupo de origen; los registros anteriores sin esa información incorporan una referencia explícitamente marcada como **Grupo al incorporar trazabilidad**, sin inventar su origen histórico. La analítica de equipo usa la pertenencia actual del Técnico; Detalle y auditoría permiten revisar el origen/movimiento.

Admin revisa el destino incluso si pertenece a otra Cuenta. Se exige Manager de destino activo y se valida el Lead único. Antes de mover debe detenerse cualquier Timer en curso; no se pierde el tiempo registrado. Se revoca la delegación anterior y se cierran las sesiones para aplicar permisos nuevos. Una solicitud duplicada, resuelta o desactualizada no puede volver a trasladar al Técnico; aprobación de solicitud y traslado se guardan juntos.

## Línea de tiempo personal

En **Mi tiempo**, la OT aparece ordenada por fecha real o planificada de actividad. Una captura histórica tardía se inserta en su fecha de trabajo, no en el día de captura. La vista indica cuándo se capturó, estado de aprobación, actividad planificada, en curso o pausada y acceso a Detalle y controles disponibles. Respeta el mes seleccionado y contempla actividades que cruzan meses. Se actualiza al guardar y con la sincronización de cinco segundos cuando no estás editando ni tienes un diálogo abierto. La OT pendiente no suma horas aprobadas; una programación futura indica cuándo estará disponible su Timer.

## Tipo de OT automático

Al capturar inicio y fin, el formulario muestra el tipo detectado usando la zona operativa. El servidor vuelve a determinarlo al guardar:

- Si el periodo terminó, es OT histórica y se envía a revisión con esas horas reales.
- Si comienza en el futuro, es OT programada y requiere aprobación antes del Timer.
- Si está en curso, se indica usar el Timer de emergencia o registrar el histórico después de terminar.

La documentación de una OT ejecutada conserva los tiempos reales de su Timer.

## Ventana autorizada y extensión del Timer · v1.0.5

Una OT programada indica la fecha y hora en que estará disponible su Timer; necesita aprobación antes de iniciar. El Panel y Aprobaciones del Manager muestran los Timers de todos sus Grupos, con Técnico, Employee ID, Grupo y actividad.

1. El Técnico puede **Solicitar extensión** antes o después del fin autorizado, indicando un motivo y la nueva fecha/hora de fin.
2. El Manager o Lead delegado la autoriza o rechaza en **Aprobaciones → Extensiones pendientes**. No se permite autoaprobación.
3. Si llega el fin autorizado, el servidor **pausa exactamente en ese límite**, incluso con el navegador cerrado. El contador no sigue sumando.
4. Si se autoriza después de la pausa, el Técnico pulsa **Reanudar**; no arranca automáticamente. Si se autoriza antes del límite, el Timer continúa hasta el nuevo fin.
5. Si no necesita continuar, puede **Finalizar tiempo trabajado**. Si rechazan la extensión, puede finalizar o solicitar otra. Detener/finalizar cancela las extensiones aún pendientes.

Cada reanudación crea un tramo real separado. **La espera no suma OT ni se descuenta de Guardia**. Analítica, Excel, Claim y ADP usan esos mismos tramos. La programación y la extensión no aprueban automáticamente el tiempo real: éste vuelve a revisión al finalizar. En Detalle/Ver tramos queda la trazabilidad.
