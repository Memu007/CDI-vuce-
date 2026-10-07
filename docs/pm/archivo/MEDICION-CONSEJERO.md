# Medición del consejero

Una fila por consulta al consejero (`/advisor`) de la PM principal.

- **Propuso:** cuántas cosas concretas propuso.
- **Adoptadas:** cuántas se hicieron.
- **Cambió el resultado:** cuántas cambiaron lo que se hizo o se decidió; es
  lo que vale, y se cuenta con honestidad, no a favor.
- **Equivocadas:** cuántas resultaron mal al comprobarlas.

| Fecha | Momento | Qué | Propuso | Adoptadas | Cambió el resultado | Equivocadas |
|---|---|---|---|---|---|---|
| 2026-10-06 | antes de la auditoría | plan de auditoría y pausa de la Dev | 10 | 10 | 5 (rutina que avanzaba sola, choque entre subagentes en el mismo puerto/base, VUCE/Tarifar salían a internet por defecto, pausar también la pieza «apenas entregues», CI en GitHub confirma que Cloud Run nunca desplegó) | 1 (el plan apuntaba a una copia vieja del producto; ni la PM ni el consejero lo vieron) |
| 2026-10-06 | algo no cierra | producto real en CDI-vuce- y canal de PM de septiembre | 9 | 9 | 4 (rutina neutralizada antes de su vuelta, barrido de secretos en el repo público, corrección durable en NOW.md, confirmar en vez de re-preguntar a Emi) | 0 |
| 2026-10-06 | antes de cambiar reglas | mudanza del método a CDI-vuce- y reglas en un solo lugar | 10 | 10 | 4 (probar el push antes de escribir; las reglas llegan a `main` recién al publicar, y hasta entonces la vieja manda empujar a `main`; partir de la plantilla y no de la copia de CDI; congelar con fecha) | 0 |
| 2026-10-07 | antes de escribir | roadmap mientras responde el despachante | 7 | 7 | 4 (D3 y los secretos sin pieza; columna de prueba por pieza que separa Fase A de Fase B; mapa de choque por archivo para recomendar una o dos Devs; prender «Wait for CI») | 0 |
| 2026-10-07 | antes de entregar | roadmap terminado | 5 | 5 | 3 (cómo se vuelve atrás sin forzar `main`; la cuenta de impagas la confirma Emi, no la PM; la publicación de ensayo sí cambia el MARIA y se dice) | 0 |
| 2026-10-07 | antes de cambiar una regla | umbral de compactación (pedido de Emi) | 4 | 4 | 2 (Emi eligió 30/40; medir el contexto por pieza; también se corrigió la rutina de la PM, que seguía apuntando a la rama vieja de la Dev y al roadmap «sin aprobar») | 0 |
| 2026-10-07 | antes de cambiar el plan | orden nuevo de Emi (TXT, cobro, seguridad al final) | 6 | 6 | 4 (decir la condición de seguridad antes y ponerla como puerta; reescribir el roadmap entero; EXCEL-1 y PUNTA-A-PUNTA-1 nuevas, MARIA-1b a la Dev 1; Emi prueba con facturas reales al cerrar la Fase 1) | 0 |
| 2026-10-07 | antes de cambiar el plan | simplificar el roadmap (pedido de Emi) | 4 | 4 | 3 (una pantalla para Emi con «está lista cuando…» por fase y el detalle abajo; fusionar sólo RENDIMIENTO+DEPENDENCIAS, MARIA-4+4b y MARIA-6+7; no renombrar lo que está en curso) | 0 |
| 2026-10-07 | antes de escribir | dos respuestas cortas del despachante y la pregunta de Emi sobre subagentes | 6 | 6 | 4 (PSAD por operación como el banco; la reducción del IVA no va en el TXT y la exclusión queda como «ventaja no nombrada»; MARIA-6 se achica; atacar ya el candidato del ensayo con un Opus alto) | 0 |
| 2026-10-07 | algo no cierra | informe del ataque al ensayo | 6 | 6 | 4 (la lista de Railway en el orden en que Emi la hace, con la copia primero; verificar el remedio de su cuenta antes de dárselo; repetir sobre la cabeza real; a Emi, de noche, sólo dos líneas) | 0 |
| 2026-10-07 | antes de escribir | «el nomenclador lo podés bajar de Google» con ARCA bloqueado | 7 | 7 | 4 (el ZIP de julio ya era el de 2018: decirlo; dos caminos, habilitar el sitio o adjuntar; la PM no corre el importador; no mencionar una enmienda 2027 sin confirmar) | 0 |
| 2026-10-07 | antes de publicar | «dale 5cb03ab» con la rama ya en `a47cd14` | 4 | 4 | 3 (publicar exactamente el SHA aprobado con un avance directo de `main`, sin merge; si el push se rechaza, preguntar antes de publicar otro SHA; qué mira Emi después) | 0 |
