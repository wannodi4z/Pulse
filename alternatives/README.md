# Dos alternativas de interfaz · base v1.0.10

La versión estable conserva su interfaz. Cada propuesta se aplica como última hoja CSS en un proyecto completo e independiente. Backend, app.js y layout.js se mantienen idénticos: no se alteran funciones, permisos, datos, cálculos ni eventos de arrastre.

## Atlas

Consola operativa: navegación lateral azul noche, acentos cobalto, jerarquía marcada y superficies de datos claras. Login oscuro con tarjeta blanca de acceso. Estilo geométrico y compacto.

## Studio

Espacio editorial: navegación superior en escritorio, lienzo cálido, verde bosque y tipografía serif en títulos. Formularios y datos mantienen tipografía de lectura rápida. Login luminoso y composición más tranquila.

## Alcance

Ambas cubren los cuatro roles, login, activación y recuperación, paneles, organización, Kanban, calendario, formularios y modales, Timer, Guardias, aprobaciones, analítica, Claim, ADP y respaldo. Colores de estado y de los tipos de registro conservan su significado. Interacción por teclado, vistas móviles y preferencias de movimiento reducido se conservan.

## Generar los ZIP completos

Desde el repositorio: `python3 scripts/build_alternatives.py --output /tmp/pulse-alternatives`.
Se empaquetan archivos versionados; no se incluyen .venv, bases personales ni claves. Cada carpeta contiene LEEME_ALTERNATIVA.md y el arranque habitual start.command.

Para comparar, ejecuta una alternativa a la vez (puerto local 5510) y usa primero los datos de demostración. No sustituir la carpeta estable. Las dos propuestas son alternativas visuales de v1.0.10, no versiones con funcionalidades diferentes.

## Vistas previas y validación

[Comparativa visual PDF](../docs/alternatives/Pulse_Atlas_y_Studio_Comparativa.pdf) · [Vista rápida](../docs/alternatives/Pulse_Dos_Alternativas.jpg).

Se verificaron 80 combinaciones de rol/página/resolución en cada opción (160 en total), login en cinco resoluciones con movimiento reducido, formularios de una sola vista, calendario con rangos arrastrables, inicio del Timer, alta/edición de Técnicos y traslados mediante arrastre y aceptación del receptor, cuatro gráficas ampliables para Manager/Técnico/Lead delegado y respaldo/recuperación con documentación y duplicados. Las pruebas utilizan bases temporales, nunca datos de trabajo.

La navegación superior de Studio se compacta en pantallas de poca altura para mantener accesibles los destinos del Kanban. En móvil ambas opciones conservan navegación horizontal y calendarios de siete columnas.

La comprobación de entrega compara byte por byte backend/application.py, backend/time_recovery.py, server.py, frontend/static/app.js y frontend/static/layout.js con la versión estable. La diferencia funcional no depende de una segunda implementación: sólo se incorpora una hoja visual y su enlace en el HTML.
