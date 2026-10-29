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
| 2026-10-07 | antes de aceptar o devolver | MARIA-5 con 14 hallazgos | 7 | 7 | 4 (devolución, no aceptada con agregados; una regla para los dos pesos en vez de puntos sueltos; v1 y exportación a DECISIONS, no a la devolución; reproducir el hallazgo 1 antes de escribir) | 0 |
| 2026-10-07 | antes de cambiar una regla | Emi propone compactar a 60/50 | 6 | 6 | 3 (el umbral se cuantiza por pieza: 30 = cada pieza, 40-60 = cada dos; la PM a 50 sí; lo que molesta es que las Devs se frenan esperando el pegado y que la Dev 1 se mide de más) | 0 |
| 2026-10-29 | antes de aceptar o devolver | DESPACHO-1b vuelta 3 (devolución) y DISCO-1 (aceptada sin integrar) | coincidió con los dos veredictos (el detalle de lo propuesto se perdió al compactar la sesión) | — | no cambió el veredicto; después la PM midió el tope de CPU y sumó esa causa | 0 |
| 2026-10-29 | antes de aceptar o devolver | COBRO-MP-1 (`784e793`) con 17 hallazgos de dos adversarios y un negativo de la PM | 6 | 6 | 4 (afinar D7.2 con una regla en vez de reabrirla; una sola regla para las lecturas de Mercado Pago, 503 si no se pudo leer y `rechazado` si se leyó mal; la recarga con el tope dentro de esta vuelta; comprobar el CHANGELOG por D10) | 0 |
| 2026-10-29 | antes de aceptar o devolver | COBRO-MP-1 vuelta 2 (`4ef59f4`) y ORDEN-1b (`6c459d2`) con cuatro adversarios | 5 | 5 | 4 (la causa de la regresión del cobro sin depender de D30; reconocer que «rechazado» salió de la regla b y que se va lo terminal, no lo visible; en ORDEN-1b devolver pruebas por condición del freno y no el producto; mandar a COBRO-MP-2, D13 c o Emi lo que no es de esta vuelta) | 0 |
