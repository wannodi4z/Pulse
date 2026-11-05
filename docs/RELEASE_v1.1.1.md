# v1.1.1 · Tablero enfocado y demo Banorte

- Cuatro gráficas sugeridas por defecto. Catálogo de 20 análisis para DP/DPE, 18 de equipo para Manager/Lead delegado y 11 personales para Técnico/Lead. La disponibilidad nunca amplía permisos.
- Catálogo agrupado por periodo, composición, organización y personas; búsqueda y selección múltiple. Cancelar no cambia el tablero. Se conservan vistas por usuario/navegador.
- Anchos ⅓, ½, ⅔ o completo, y cuatro alturas. El tirador y el teclado ajustan entre esos tamaños alineados; el contenido se adapta. Persisten mover, ocultar, ampliación, leyendas y datos emergentes.
- Se reinicia la vista principal anterior a cuatro gráficas para evitar trasladar una pantalla saturada. Las vistas con nombre se conservan; al abrirlas sus tamaños libres anteriores se ajustan a los más cercanos de la cuadrícula.
- Analítica muestra sólo el contexto y los botones Filtros / Comparar meses; la estructura ejecutiva se consulta desde un modal.
- Historial conserva la barra de búsqueda y usa Filtros para alcance, concepto, estado y mes/todo el historial. No incluye comparación de meses. Consultar registros desde una gráfica lleva al mes principal y conserva alcance y tipo.
- Traslados organizacionales aparece en Administración, también para DP/DPE y Lead.
- Inicialización optativa de Banorte México mediante `PULSE_DEMO_BANORTE=1`, predeterminada en el lanzador Mac. No modifica bases con una organización existente. La plantilla completa privada conserva los seis accesos solicitados y no carga horas.

Los análisis por Cuenta se limitan a la Cuenta del usuario y sus filtros. Un DPE ve solamente sus Managers; no se agregan datos de otra Cuenta. Ranking y volumen no son medidas de desempeño. Los periodos parciales se indican y la Guardia neta continúa descontando la OT coincidente.
