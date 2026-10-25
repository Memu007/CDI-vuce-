# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## SEPARADORES-1 y VALOR-1c: entregadas a revisión (2026-10-25)

**Resultado:** las dos van juntas en `a099655`.
- **VALOR-1c:** van los cinco puntos. Cada uno tiene su caso y su sabotaje
  en rojo (26).
- **SEPARADORES-1:** «3.480» es 3480 en la factura y en la pantalla, y
  «1,500» se pregunta. Tiene 17 sabotajes en rojo, 3 de ellos en el
  navegador.
- **El TXT** cambia sólo en lo que pediste:
  - `MDDTFLE` y `MDDTASS` con punto de miles salen enteros
    (SEPARADORES-1);
  - un seguro calculado con otros importes ya no sale sin que se elija;
  - un general que nadie usa no frena (D18 b);
  - sin productos ya no sale un TXT vacío.
- Suite, smoke, e2e y la pantalla de SEPARADORES-1 dan verde.

**Lo que decidís vos:** nada que frene. D19 es nueva y te la dejo para
cuando la ordenes. Abajo, los supuestos reversibles.

**Tenés que saber un rojo mío:** la suite completa sobre `d0bfebc` dio
`2 failed`. Eran dos casos viejos que afirmaban lo que tu tarea cambia, y
los puse al día en `a099655`. Antes no los vi porque perdí la línea final
de la corrida: la había cortado con `tail`. Detalle en «Rojos».

| Pieza | SHA |
|---|---|
| Base: informe de VALOR-1b y MARIA-9 | `a74ee9d` (producto igual a `efa2e08`) |
| D18 renumerada (doc) | `8f529d5` |
| SEPARADORES-1. Producto | `0928ad4` |
| Casos, pantalla y sabotajes | `2145d56` |
| Merges de tu rama (sólo `docs/pm`) | `05768eb`, `eab6a7f` |
| VALOR-1c. Producto | `3df999c` |
| Casos y sabotajes | `ea3200c` |
| Producto: lo que encontró `/code-review` (prefijo «Seguro: ») | `c336508` |
| Casos y sabotajes | `d0bfebc` |
| Dos casos viejos al día (sin productos, D18 b) | `a099655` |
| **SHA probado:** suite, compileall y sabotajes de SEPARADORES-1 | **`a099655`** |
| Smoke, e2e, pantalla y sabotajes de VALOR-1c | `d0bfebc` (de ahí a `a099655` cambian sólo dos archivos de `tests/`, fuera de esos scripts) |

## Decisiones

**D19. Un monto ilegible se manda como 0 (`finalize.js`, `montoDelPedido`).**
Flete, seguro, gastos o ajustes que `leer` no entiende van como 0 al
servidor. Hoy no encontré ningún camino para llegar así a generar:
`review.js` frena al continuar, y lo restaurado pasa por revisión. Lo
confirmó el adversario. Si algún día se entra a validar por otra ruta, sale
0 sin aviso.
- (a) Dejarlo así.
- (b) Mandar el texto crudo. El servidor ya lo rechaza con «Flete: «1,500»
  no es un importe.», como hace `semaforo.js`.

**Recomiendo (b)**, en una pieza aparte: son pocas líneas y quita la
dependencia de que revisión frene. No lo toqué porque está fuera de VALOR-1c.

**D18 (b), D13 (b) y D14 (a):** las tomé como decidiste.

## Lo que se hizo

### VALOR-1c

1. **Un seguro calculado con otros importes no sale sin que se elija.**
   - **La marca.** Al calcularlo, la pantalla marca la operación
     (`seguro_calculado`). La marca se borra al escribir el seguro a mano
     (`review.js:666`) o al apretar «Dejar el seguro como está».
   - **El control en el servidor.** Con la marca puesta, si el seguro ya no
     es el sugerido con los importes de ahora, `/generate_maria` da 400:
     «Seguro: lo calculó el sistema con otros importes; con los de ahora da
     X y la operación lleva Y. Recalculalo o dejalo como está en «Ajustes y
     seguro».».
   - **El aviso.** `/avisos` lo dice antes, con el mismo texto.
   - **Cuentas en error.** Si las cuentas fallan, dice «…ahora no se puede
     comprobar: {error}…», y el botón «Dejar» también aparece.
   - **Cubre todos los caminos.** El control está en el servidor, así que
     vale para revisión, restauración, otra operación y la tarjeta. Una
     factura nueva reemplaza la operación entera y la marca no sobrevive.
   - **La familia.** El seguro es el único valor que el sistema pone con
     esas cuentas. El descuento (`usarDescuento`) sale de la factura
     (`op.descuento`), no de las cuentas.
   - **La pantalla.** Si generar frena por esto, vuelve a «Ajustes y
     seguro». Lo reconoce por el texto «Seguro: lo calculó el sistema»:
     cualquier otro error, también «Seguro: «abc» no es un importe.», se
     queda en generar. Ese caso lo encontró `/code-review`; lo arreglé en
     `c336508`, con el rojo antes.
2. **D18 (b).** El general que nadie usa no se controla ni se avisa, en
   los dos endpoints. Cuando alguien lo usa, los controles de `=`,
   caracteres de control y largo siguen igual. Los sabotajes 14 a 16
   prueban las dos condiciones.
3. **Kilos.** El error nombra a todos los renglones que dan cero, también
   cuando el cero sale del ajuste del redondeo. Tu caso: 0,005, 0,005,
   0,005 y 0,004 nombra del 1 al 4.
4. **Sin productos.** Los dos endpoints dicen «No hay productos para
   generar: volvé a cargar la factura.»: `/generate_maria` con 400 y
   `/avisos` como aviso.
5. **Pruebas que no distinguían.** Cada mutación de tu lista tiene su
   sabotaje:

   | Mutación | Sabotaje |
   |---|---|
   | flete sin redondear | 21 |
   | firma sin los ítems | 22 |
   | sin `pintarValor(null)` | 23 |
   | `None` por el IVA adicional | 24 |
   | `/avisos` con `request.items` | 25 |
   | renglón de kilos como índice dentro del ítem | 18 |

El CHANGELOG dice sólo lo probado, en dos líneas.

### SEPARADORES-1

- **La factura.** A Gemini se le pide el flete y el seguro como texto, y
  los lee `_monto_factura`.
  - «3.480» y «3.480,00» son 3480.
  - Si la misma factura usa el punto como decimal, el campo queda sin leer
    y se avisa.
- **La pantalla.** `montos_ar.js` lee y escribe los montos a mano (flete,
  seguro, gastos y ajustes): punto de miles y coma decimal.
  - «1,500» no se adivina: la pantalla pregunta «¿1.500 o 1,5?» bajo el
    campo.
  - Con esa pregunta abierta, continuar no avanza.

## Comandos para reproducir

```bash
S=<tu scratchpad>   # con un venv del proyecto en $S/venv y node en el PATH
git fetch origin claude/dev-maria
git diff a099655 origin/claude/dev-maria -- proyecto_maria tests scripts      # vacío
git diff d0bfebc a099655 --stat      # sólo tests/test_maria7_rechazos_24_10.py y tests/test_prelaunch_block1.py
$S/venv/bin/python -m pytest -q --no-cov tests/test_valor1c.py tests/test_valor1.py tests/test_maria9_kilos.py tests/test_separadores1.py
scripts/testing/sabotaje_valor1c.sh     a099655 $S/venv   # «OK: los 26 sabotajes dan rojo por la razón esperada»
scripts/testing/sabotaje_separadores1.sh a099655 $S/venv  # «OK: los 17 sabotajes dan rojo por la razón esperada»
```

- Cada sabotaje lee su script mientras corre. No edites el script durante
  la corrida (ver «Rojos»). Tampoco los corras en paralelo con la suite.
- Para `e2e_maria.sh`, poné `$S/venv/bin` primero en el `PATH`.

## Puertas

| Puerta | SHA | Salida |
|---|---|---|
| Suite completa (worktree limpio, sola) | `a099655` | `2280 passed, 102 skipped, 2 xfailed, 25 warnings in 287.49s (0:04:47)`, rc=0 |
| `compileall -q proyecto_maria` | `a099655` | rc=0 |
| `sabotaje_separadores1.sh` | `a099655` | `OK: los 17 sabotajes dan rojo por la razón esperada`, rc=0 |
| `sabotaje_valor1c.sh` | `d0bfebc` | `OK: los 26 sabotajes dan rojo por la razón esperada`, rc=0 |
| Smoke (`levantar.sh d0bfebc 8791`) | `d0bfebc` | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| `e2e_maria.sh` | `d0bfebc` | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.` |
| `pantalla_separadores1.js` | `d0bfebc` | `OK el TXT sale con MDDTFLE=2750.00 y MDDTASS=1234.50` / `PANTALLA SEPARADORES-1 OK` |

**No corrí:**
- `ataque_aislamiento.sh`: no toqué datos, sesión ni permisos.
- Una pantalla de VALOR-1c en el navegador. El botón «Dejar» y la vuelta a
  las cuentas están probados con el arnés de node de `test_valor1c.py`, no
  en Chromium.

## Autorrevisión

| Revisor | Modelo y esfuerzo | Sobre | Hallazgos | Qué pasó |
|---|---|---|---|---|
| `/code-review high` | — | `a74ee9d..ea3200c` | 10 | Arreglado: (5) el prefijo «Seguro: » lo comparte un error de `importe_valido` (`c336508`, caso y sabotaje 8b en `d0bfebc`). (1) es D19. (2) la familia: falso, el descuento sale de la factura. (3), (4), (6) a (8) en «Riesgos». (9) «1,234,567» se acepta: aceptable. (10) duplicación: no se toca |
| Adversario | Sonnet, alto | `a74ee9d..ea3200c` | 4, todos bajos (3 reproducidos, 1 por lectura) | Nada para arreglar dentro de la tarea. (1) «3.480» sin pista de decimal se lee 3480 sin marca; (2) Gemini con número JSON 3.480 da 3.48; (3) «.5» y «3 480» se rechazan; (4) `montoDelPedido` (D19). Sin hallazgo en: el control del seguro contra los dos endpoints (11 casos), D18 (fuzz de 4000 pedidos: 0 casos de un general «no usado» que sale en el TXT), unos 50 casos de `leer`/`escribir` y 45 de `_monto_factura` |
| Revisión de seguridad | Sonnet (subagente general) | `a74ee9d..ea3200c` | 0 vulnerabilidades | `/security-review` no corre en esta sesión. Sin XSS, sin cambios de sesión ni permisos. `seguro_calculado` lo pone el cliente y no es un límite de seguridad: sólo hace frenar, no habilita nada. El general que nadie usa no llega al TXT: `limpiar_sufijo` es la barrera |

## Rojos

- **La suite sobre `d0bfebc`:** `2 failed, 2278 passed, 102 skipped, 2
  xfailed`.
  - `test_prelaunch_block1::test_generate_maria_sin_items_genera_vacio`:
    `assert 400 == 200`. Afirmaba el 200 con un TXT vacío, lo que pide
    cambiar tu punto 4. Ahora se llama `…_sin_items_da_error_claro` y
    espera el 400 con el texto exacto.
  - `test_maria7_rechazos_24_10::test_lo_que_se_cambia_en_el_sufijo_se_avisa`:
    `assert False`. Pedía el aviso del general en un pedido donde el
    sub-ítem trae su propio sufijo, o sea que nadie usa el general. Con
    D18 (b) no se avisa. Ahora el aviso del general se prueba con la lona
    sola, que sí lo usa. El del sub-ítem queda igual.
  - Los dos son de producto, por mi pieza, y los vi tarde. La corrida
    anterior sobre el árbol de trabajo la corté con `tail` y la línea final
    se perdió entre el ruido de asyncio. No se repitió hasta pasar: se
    leyó el motivo y se cambiaron los casos.
- **`sabotaje_valor1c.sh` sobre `ea3200c`** cortó después de 13 rojos con
  «line 133: syntax error near unexpected token `;'».
  - La causa fue que edité el script, agregando el 8b, mientras bash lo
    leía. Bash lee el script de a pedazos.
  - Corrido desde una copia fija sobre `d0bfebc`, dio los 26 en rojo,
    rc=0.

## Riesgos y lo que no se cubrió

**De VALOR-1c:**
- **La marca es del cliente.** Un cliente que no la manda (por API, o una
  pantalla vieja en caché) genera con el seguro que traiga, como antes de
  VALOR-1c.
- **Una operación restaurada conserva la marca.** El servidor la vuelve a
  comprobar con los importes de ahora: si cambiaron, frena y ofrece
  «Dejar».
- **Con las cuentas en error, frena** aunque el error sea de un ajuste y
  no del seguro. Hay salida con «Dejar». Supuesto reversible.
- `pintarValor` pone `op.ajustes_incluir` tal cual. Un número restaurado
  como 1.125 se mostraría «1.125», y `leer` lo tomaría como 1125. Riesgo
  bajo: la pantalla siempre guarda lo que escribe `escribir`.
- `escribir` con números ≥1e21 o menores de 0,005 no da la vuelta: no son
  montos reales.
- Kilos: con 4 × 0,004, todos dan cero solos y se nombra a los cuatro.
  Está bien así.

**De SEPARADORES-1:**
- Con `decimal=None`, la factura no da pista del separador decimal. Ahí
  «3.480» es 3480 sin marca, como en la regla pedida. Un monto en moneda de
  tres decimales saldría ×1000.
- Si Gemini devuelve el flete como número JSON, `3.480` llega como 3.48 y
  ya no se puede distinguir. El prompt pide texto; no hay `parse_float=str`.
- `_MONEDAS` no tiene todas las monedas: un código raro pegado al número
  deja el campo sin leer.
- «.5», «5.» y «3 480» se rechazan con «Debe ser un numero». El campo
  queda marcado: no se pierde nada.

**Los que anotaste en la tarea**, sin tocar.

**General:** la CI deselecciona tests de presupuestos y no reemplaza la
suite.

## Archivos de producto que toqué

- `proyecto_maria/main.py`: `MariaRequest`, `/generate_maria`, `/avisos`,
  `_seguro_calculado_viejo`.
- `proyecto_maria/core/maria_generator.py`: `supuestos_declarados` y el
  error de kilos.
- `proyecto_maria/pdf_extractor.py`: `_monto_factura` y el prompt.
- `proyecto_maria/static/v2/montos_ar.js`: nuevo.
- `proyecto_maria/static/v2/screens/finalize.js`
- `proyecto_maria/static/v2/screens/review.js`
- `proyecto_maria/templates/dashboard_v2.html`

## Siguiente

No hay pieza marcada «apenas entregues». Espero tu veredicto; si trae una
devolución, esa va primero.

Última vuelta: 2026-10-25 06:31 UTC.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM, rutina horaria minuto 35. Entregadas SEPARADORES-1 y VALOR-1c en a099655 (suite y 17 sabotajes de SEPARADORES-1 sobre a099655; 26 sabotajes de VALOR-1c, smoke, e2e y pantalla sobre d0bfebc, que difiere sólo en dos tests); D19 (montoDelPedido manda 0) abierta en PARA-PM-2.md; D18 (b), D13 (b) y D14 (a) decididas. Sin pieza siguiente: esperar veredicto. Nunca main, sin push --force, sin datos reales del 24/10, nada se publica sin el «dale» de Emi para el SHA, sin Gemini en pruebas, subagentes hasta esfuerzo alto, sin advisor.
