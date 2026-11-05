# Banorte · México · Demo v1.1.1

## Accesos indicados para prueba

| Nombre | Función Pulse | Employee ID | Contraseña de prueba |
|---|---|---|---|
| Eric Perez | DP | DP00001 | manager12026 |
| Octavio Lopez | DPE | DPE0001 | manager12026 |
| Yao Pegueros | Manager | MGR0001 | manager12026 |
| Francisco Javier Cervantes Marquez | Lead | SL0001 | lead120261 |
| Samuel Alejandro Díaz Chávez | Técnico | 951357 | tecnico12026 |
| Marco Antonio Flores Rosas | Técnico | 951358 | tecnico12026 |

Los tres primeros forman DP → DPE → Manager. Francisco es Lead directo de Yao; Samuel y Marco pertenecen al Grupo **Mainframe · Pruebas**, junto con los demás Técnicos de esa rama cuando se incluye el organigrama completo.

Ser Lead es una asignación de Pulse independiente del cargo oficial. La demo no concede automáticamente facultades delegadas: Yao debe otorgarlas para probar ese flujo. El Lead conserva su captura individual de OT y no captura Stand By.

## Organigrama completo de prueba

El paquete de demo añade `demo/banorte_organization.json`, generado del Excel suministrado. Incluye 346 personas: 1 DP, 8 DPE, 106 Managers, 230 Técnicos y 1 Lead. Los Grupos de prueba se crean para los 10 Managers con Técnicos. Las ramas cortas quedan como Managers sin equipo por completar.

Por instrucción del usuario, los roles se asignan según el nivel del archivo, no según palabras del cargo. Excepto los seis identificadores anteriores, los Employee ID son inventados para prueba: DPE0002…, MGR0002…, TEC0001…. Contraseña de prueba: `manager12026` para DP/DPE/Managers y `tecnico12026` para Técnicos. No son identificadores corporativos reales.

La pertenencia a Banorte México, los Grupos y el reparto de funciones son una configuración de demo, no una validación del organigrama corporativo. No se cargan horas ni reglas de Guardia. Los Managers de la demo tienen activa la franja diaria de OT 21:00–08:00, que pueden configurar. La plantilla contiene nombres y dependencias, sin el Excel original, y se entrega sólo en el ZIP privado de demo; no se publica en el repositorio de código.

## Arranque y conservación

1. Extrae el ZIP en una carpeta nueva e instala las dependencias según README.
2. Abre `start.command`. La primera creación completa puede tardar unos 30 segundos mientras se protegen las contraseñas con hash y sal individual.
3. Abre http://127.0.0.1:5510 e ingresa con los accesos de la tabla.

Por terminal: `PULSE_DEMO_BANORTE=1 .venv/bin/python -m uvicorn server:app --host 127.0.0.1 --port 5510`.

Para instalación vacía: `PULSE_DEMO_BANORTE=0 ./start.command`. Al reiniciar se preservan personas, contraseñas, horas y configuración existentes. Si ya hay una organización, la demo no se aplica. Para llevarla a otra versión, utiliza el respaldo integral `.pulseorg`.
