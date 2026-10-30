# Orbit y Prisma · interfaces reconstruidas sobre v1.0.10

Son proyectos completos con nueva composición de pantallas. La versión estable de la raíz no cambia su interfaz.

## Orbit: escritorio operativo

- Sin menú lateral: cabecera de producto y navegación horizontal.
- Dashboard en tres áreas: columna de indicadores, gráfica central y prioridades.
- Kanban horizontal con desplazamiento; los Grupos conservan el mismo tamaño.
- Formularios amplios como paneles de edición laterales; confirmaciones compactas centradas.
- Calendario, Timers, acciones y totales en un mismo recorrido vertical, sin selector de contenido.
- Nuevo login con formulario a la izquierda y presentación a la derecha.

## Prisma: espacio de cristal

- Cabecera flotante con menú hamburguesa; no hay sidebar permanente.
- Lanzador de navegación en tarjetas, con foco de teclado, Escape y acceso Ctrl/Cmd+K.
- Dock inferior con accesos adecuados al rol.
- Dashboard asimétrico: indicadores en cuadrícula, gráfica amplia y prioridades.
- Grupos en filas, con Técnicos desplazables horizontalmente dentro de cada Grupo; se conserva el arrastre entre Grupos.
- Superficies translúcidas, fondo con profundidad y modales centrados de cristal.
- Login centrado, nueva jerarquía visual y accesos de activación/recuperación conservados.

## Funciones preservadas

El backend, `server.py`, `frontend/static/app.js` y `frontend/static/layout.js` conservan sus bytes originales. El módulo de presentación redefine la estructura visual del shell y login; reutiliza las vistas, formularios, atributos de acción y API existentes. No sustituye permisos ni cálculos.

La navegación se deriva del mismo menú autorizado por rol. Se mantienen altas/edición/bajas, activación, movimientos, delegación, reglas, OT/Guardias, Timer y documentación, aprobaciones, analítica, Claim, ADP, Excel y respaldo .pulse. El cambio visual despliega las secciones en un lienzo desplazable; las filas filtradas o condicionalmente ocultas siguen ocultas.

## Validación

103 pruebas API aprobadas. En cada alternativa se realizaron 80 comprobaciones mediante navegación real para cuatro roles y cuatro resoluciones, junto con alta/activación/edición de un Técnico, arrastre y movimiento confirmado, OT histórica, aprobación, selección de Guardia arrastrando fechas, Timer de emergencia y documentación pendiente, formularios con pie visible en móvil y pantalla baja, gráfica ampliada, Claim/ADP, descarga .pulse y protección de duplicados. Sin errores JavaScript.

## Ejecutar

Extraer cada ZIP en una carpeta separada, instalar el entorno siguiendo README.md y ejecutar `start.command`. Abrir una alternativa a la vez en el puerto 5510. Los datos de demostración se incluyen; la base personal y su clave no se distribuyen. Conservar la carpeta estable.

Para generar ambas desde el repositorio: `python3 scripts/build_alternatives.py --output /tmp/pulse-reinvention`.

La capa de presentación queda en `frontend/static/presentation.js`, `presentation-base.css` y `alternative.css`; el HTML identifica la experiencia. Las capturas y la comparativa están en docs/experiences.
