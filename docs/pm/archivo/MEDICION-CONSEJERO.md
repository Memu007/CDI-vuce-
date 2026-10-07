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
| 2026-10-07 | antes de cambiar una regla | umbral de compactación (pedido de Emi) | 4 | pendiente de Emi | — (recomendó bajar a ~30 % Devs y ~40 % PMs y medir; el 50/60 no tenía razón escrita) | 0 |
