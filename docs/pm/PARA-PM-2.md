# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Devolución de MARIA-7 y MARIA-8 — entregadas a revisión (2026-10-24)

**Resultado:** los 5 puntos de la devolución y MARIA-8 están hechos, cada uno
con su rojo antes. La autorrevisión encontró cinco defectos más en la
devolución, y van arreglados en una segunda vuelta. La suite completa sobre
`536c679` da **1 rojo de entorno** (`test_excel2`, por tiempo, en el borde
del tope de 30 s; ver Puertas). Corrido solo, da verde en esa misma base y en
la tuya. Los sabotajes de la devolución (13), de MARIA-7 (25) y de MARIA-8
(38) dan rojo por la razón esperada. El smoke y la e2e dan verde. Los golden
no cambian.

**Lo que decidís vos:** D9, D10 y D11 de abajo. Ninguna frena la entrega,
pero **D9 rompe tu herramienta** `auditoria_generador_sintetico.py`: leé D9
antes de correrla.

| Pieza | SHA |
|---|---|
| Base: mi informe de MARIA-7 | `284b029` |
| Producto: MARIA-8, sub-ítems por renglón | `3fd9f2e` |
| Casos y sabotajes de MARIA-8 | `97b9ec7`, `2a6a2df` |
| Producto: MARIA-8, lo que encontró la revisión | `3f13b5b` |
| Casos y sabotajes de esa revisión; MARIA-5 vuelve a cubrir sub-ítems | `273adba`, `3494099` |
| Producto: devolución de MARIA-7, puntos 1 a 5 | `dfa636f` |
| Casos y 9 sabotajes de la devolución | `5c62604` |
| Producto: devolución, segunda vuelta (autorrevisión) | `e470001` |
| Casos y 13 sabotajes de la segunda vuelta | `536c679` |
| Sabotajes viejos de MARIA-7 y MARIA-8 con sus patrones al día | `cb97c77`, `30ceace` |
| Merge de tu rama (`f1d52ab`, sólo `NOW.md`) | `9ba0465` |
| **SHA probado:** suite y sabotaje de la devolución | **`536c679`** |
| **SHA probado:** sabotajes viejos, smoke y e2e | **`30ceace`** |

Después de `536c679` el producto no cambia: sólo scripts de sabotaje y
documentos (`git diff 536c679 HEAD -- proyecto_maria` da vacío).

## Decisiones

**D9. Un sufijo de la operación en texto libre ahora no genera el TXT.**
Con el punto 1, un sufijo que no se puede separar en `CÓDIGO(valor)` da error
y dice dónde está. Caen ahí `SINTETICO`, `ROJO`, `A`, `CA100-`, `A1(X)-` y
`AA (ROJO)-CA00-` (con espacio antes del paréntesis). Antes pasaban tal cual
al `CSBTSVL`.
- (a) Dejarlo así: con un sufijo que el MARIA no puede leer no se genera.
- (b) Lo que no tiene ningún código pasa sin cambios, con aviso.
- (c) Normalizar formas cercanas, como `AA (ROJO)` → `AA(ROJO)`.

**Recomiendo (a)**, y preguntarle al despachante qué formas acepta el MARIA.
(b) vuelve a mandar lo que pediste frenar, y (c) cambia el TXT sin evidencia.
**Contra:** `docs/pm/herramientas/auditoria_generador_sintetico.py:27` usa
`sbt_sufijo_valor="SINTETICO"`, y `limpiar_sufijo("SINTETICO")` ahora da
error (lo comprobé llamando a la función; la herramienta no la corrí). Si
elegís (a), esa línea pasa a `"AA(SINTETICO)-"`. Es tu archivo y no lo toco.
Las pantallas tampoco validan la forma antes de mandar
(`static/v2/screens/finalize.js:346` y `ncm.js:819`): el error llega de
`/generate_maria`, con el lugar.

**D10. Palabras de cuenta pegadas a letras.**
Hoy no son cuenta `NROCUENTA`, `CITIBANK`, `HSBCBANK` ni `ICBCBANK`: son el
precio de no tomar `ARABIC` ni `ARBANK`. Si se buscan pegadas vuelven los
falsos positivos (`LIBANO` contiene IBAN y `DESCUENTA` contiene CUENTA). Las
cuentas largas igual se frenan por la regla de 16 dígitos o más.
- (a) Dejarlo así.
- (b) Agregar una lista de bancos conocidos.

**Recomiendo (a):** (b) es una lista a mano que envejece, y el caso real (el
IBAN) ya está cubierto.

**D11. `/generate_maria/avisos` no anticipa un sufijo de la operación que no
se puede separar.**
El error aparece recién al generar. Además, si todos los renglones traen su
propio sufijo, el de la operación no se usa pero igual se analiza, y uno malo
frena.
- (a) Dejarlo así.
- (b) Propuesta chica aparte: que el aviso lo anticipe, y que el sufijo de la
  operación que no se usa no frene.

**Recomiendo (b) como pieza aparte.** No la hice: está fuera de la tarea.

## Lo que se hizo

### Devolución de MARIA-7

1. **Sufijos que se funden.** Cada sufijo conserva su código y su valor, y
   entre uno y otro va `-`: `AA(ROJO) AB(AZUL)-CA00-` sale
   `AA(ROJO)-AB(AZUL)-CA00-`. Lo que no se delimita da error con el lugar:
   `" de la operación"`, `" del renglón N"` o el sub-ítem. Se probó con toda
   la familia: espacio, nada, coma, dos guiones, paréntesis dentro del valor
   y sin cerrar, en `[SBT]` y en el sufijo del ítem.
2. **D2 (b).** Con la estadística en kilos, `QARTKGRNET` sale al centésimo
   (`465.130`) y `QARTUNTEST` igual (`465.13`). El medio centésimo sube
   (`465.125` → `465.13`). El sabotaje `ROUND_HALF_EVEN` usa un patrón que
   aparece una sola vez, y da rojo.
3. **Palabras de cuenta.** Llevan borde adelante (`(?<![A-Z])`): `ARABIC` y
   `VAT ARBANK-…` ya no son cuenta. `IBAN`, `BANK` y las demás solas, o
   pegadas a un dígito o a `_` (`ICBC_ACCOUNT`, `1_BANK`), siguen siéndolo.
4. **Unidad del grupo por código.** `1`, `01` y `kg` son la misma unidad
   estadística. La segunda vuelta hace lo mismo con la unidad declarada.
5. **D6.** Una unidad que no se reconoce sigue saliendo 07, pero ahora con un
   aviso que muestra la unidad leída. El código que sale no cambia.

**Segunda vuelta** (lo encontró la autorrevisión, ver abajo):
- un sufijo que, separado, pasa de 120 caracteres no genera, con el mismo
  tope que valida `/generate_maria`;
- con la estadística en kilos, un kilo neto que al centésimo da `0.00`
  (`0.001`, `0.004`) no genera; `0.005` sale `0.010`;
- la palabra de cuenta pegada a un dígito o a `_` sigue siendo cuenta;
- el grupo compara la unidad declarada por código.

### MARIA-8

Los renglones con la misma posición SIM, origen, procedencia y estado, y la
misma unidad, unidad estadística e IVA adicional, van en un solo ítem con
`CARTSBITEM=S`. Cada renglón es un sub-ítem con su FOB, cantidad, unitario,
kilos y sufijo; si no tiene sufijo propio, lleva el de la operación. Las
sumas del ítem (FOB, cantidad, kilos y cantidad estadística) cierran exactas
al centésimo, y el sobrante va al sub-ítem más grande (si empatan, al
primero).

Pruebas pedidas (`tests/test_maria8_subitems_por_posicion.py`):
- doce renglones de una posición, de dos anchos y tres colores: un ítem con
  doce sub-ítems;
- dos posiciones: dos ítems.

El mensaje de kilos con sub-ítems ya no sugiere una salida que el control
después rechaza. Los grupos y sub-ítems armados a mano siguen como antes.
Los renglones sin posición no se juntan. Un renglón cuya cantidad o kilos dan
`0,00` al centésimo no sale como sub-ítem: da error con el número del
renglón en la pantalla. El sufijo de cada renglón se valida en
`/generate_maria` como los otros.

## Comandos para reproducir

```bash
S=<tu scratchpad>   # con un venv del proyecto en $S/venv
git fetch origin claude/dev-maria
git diff 536c679 origin/claude/dev-maria -- proyecto_maria        # vacío
git diff 284b029 origin/claude/dev-maria -- tests/fixtures/       # vacío: los golden no cambian
scripts/testing/sabotaje_maria7_devolucion.sh 536c679 $S/venv     # «OK: los 13 sabotajes dan rojo por la razón esperada»
scripts/testing/sabotaje_maria8.sh 30ceace $S/venv                # «OK: los 38 sabotajes dan rojo por la razón esperada»
scripts/testing/sabotaje_maria7.sh 30ceace $S/venv                # «OK: los 25 sabotajes dan rojo por la razón esperada»
```

Los tres scripts arman su propio worktree descartable. No los corras en
paralelo con la suite: comparten CPU y el rojo de `test_excel2` es por
tiempo.

## Puertas

| Puerta | SHA | Salida exacta |
|---|---|---|
| Pruebas MARIA, después de la segunda vuelta | `536c679` | `390 passed, 3 warnings in 19.03s` |
| Sabotaje de la devolución, sin sabotaje | `536c679` | `155 passed` |
| Sabotaje de la devolución | `536c679` | `OK: los 13 sabotajes dan rojo por la razón esperada` |
| Suite completa, worktree limpio | `536c679` | `= 1 failed, 2045 passed, 102 skipped, 2 xfailed, 25 warnings in 262.38s (0:04:22) =` (rc=1) |
| `compileall -q proyecto_maria` | `536c679` | rc=0 |
| `test_excel2` (el rojo) corrido solo | `94929bb` (tu base) | `1 passed, 5 warnings in 30.09s` |
| `test_excel2` corrido solo | `30ceace` | `1 passed, 5 warnings in 31.26s` |
| Sabotaje de MARIA-7 | `cb97c77` | `OK: los 25 sabotajes dan rojo por la razón esperada` |
| Sabotaje de MARIA-8, sin sabotaje | `30ceace` | `46 passed` |
| Sabotaje de MARIA-8 | `30ceace` | `OK: los 38 sabotajes dan rojo por la razón esperada` |
| Smoke (API levantada con `levantar.sh`) | `30ceace` | rc=0, `==> OK · telemetría + alias session/state + by-cuit protegido` |
| e2e MARIA | `30ceace` | rc=0, `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.` |
| Golden: `git diff 200e32a HEAD -- tests/fixtures/` y `git diff 284b029 HEAD -- tests/fixtures/` | `HEAD` | 0 líneas |

**El rojo de la suite:**
`test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal`
da «la subida normal dio 400 a los 30.1 s: {"detail":"No pudimos abrir el
Excel: tardó demasiado…"}».

- El diff no toca el Excel.
- Corrido solo, pasa en tu base y en la mía, a 30,09 s y 31,26 s.
- El tope es de 30 s y la máquina tiene `nproc` 4.

**Diagnóstico:** es un rojo de entorno, por tiempo, en el borde del tope. No
lo repetí hasta que diera verde. Antes de publicar conviene correrlo en una
máquina con más núcleos.

**No corrí** la suite completa sobre `30ceace` ni sobre el HEAD. Entre
`536c679` y el HEAD no cambia el producto: sólo scripts de sabotaje y
documentos. Tampoco corrí `ataque_aislamiento.sh`: no toqué datos, sesión ni
permisos.

**Los sabotajes viejos estaban vencidos.** Desde `5c62604`,
`sabotaje_maria7.sh` y `sabotaje_maria8.sh` cortaban con «PATRON NO
ENCONTRADO». El motivo: `limpiar_sufijo` recibió el argumento `donde`, y el
aviso del renglón pasó a `_aviso_de_sufijo`. No lo había visto al entregar
la primera vuelta. Lo arreglan `cb97c77` y `30ceace`, y ahora corren completos.

## Autorrevisión

| Revisor | Modelo y esfuerzo | Sobre | Hallazgos | Qué pasó |
|---|---|---|---|---|
| Adversario MARIA-8 | Opus, alto | `2a6a2df` | 5: sub-ítem en 0,00; unitario y total sin cruzar; sufijo del renglón sin validar en el endpoint; número de ítem corrido en los errores; `grupo_id: ""` | Arreglados en `3f13b5b`: 0,00, endpoint y número. El unitario y el total quedan como riesgo (es así desde antes). `grupo_id` vacío, de la base |
| Adversario MARIA-8 | Sonnet, alto | `284b029..HEAD` | Sub-ítem en 0,00; 8 mutaciones que las pruebas no detectaban | Arreglado. Pruebas nuevas para medio centavo, empate, total sin unitario, declarada en kilos, renglón 3 en el error (`273adba`). Siguen sin prueba `grupo_id` por valor de verdad y los kilos de más de 3 decimales por renglón |
| `/code-review high` | — | `284b029..HEAD` (MARIA-8) | Los mismos de los adversarios | Arreglados en `3f13b5b` |
| `/code-review high` | — | `200e32a..5c62604` (devolución) | 10 | Arreglados en `e470001`: 1 (kilo neto 0,000), 2 (tope de 120), 4 (borde `\b`), 7 (unidad declarada del grupo) y 10 (prueba débil). Quedan 3 (texto libre: D9), 5 (`AA()` pasa: es tu D7 (a)), 6 (el sufijo de la operación se analiza aunque no se use: D11), 8 y 9 (riesgos, abajo) |
| Adversario de la devolución | Sonnet, alto | `5c62604` | 7 | Arreglados en `e470001`: 0,004 kg, salida de más de 120, unidad declarada cruda. Quedan texto libre (D9), cuentas pegadas a letras (D10), sufijo de la operación sin aviso previo (D11), unidad Unicode (riesgo) |

## Riesgos y lo que no se cubrió

- **Unitario y total sin cruzar** (Opus, media, sólo por API). Si un renglón
  trae `valor_unitario` y `valor_total` que no coinciden, `MSBTFOB` sale del
  total y `MSBTUNITAR` del unitario. El ítem único hace lo mismo
  (`maria_generator.py:693`). La v2 no manda `valor_total`; la v1 sí.
- **Unidad Unicode** (de la base): `unidad="①"` sale `0①` sin aviso, y `99`
  y `00` salen tal cual. El motivo: `str.isdigit()` acepta «①». Lo usan igual
  `unidad_estadistica_de` y el aviso de supuestos, así que no se contradicen,
  pero ninguno de los dos frena.
- **Códigos de sufijo en minúscula** (de la base): `aa(rojo)-` pasa tal cual.
  No sé si el MARIA los acepta.
- **`AA()-` pasa**: es tu D7 (a), mientras el despachante no conteste.
- **`grupo_id: ""`** entra por el camino de grupos (de la base, sólo por API).
- **`test_excel2`** queda en el borde de su tope en una máquina de 4 núcleos.
- La CI deselecciona tests de presupuestos: no reemplaza la suite.

## Archivos de producto que toqué

- `proyecto_maria/core/maria_generator.py`
- `proyecto_maria/main.py`: la validación del sufijo propio de cada renglón
  en `/generate_maria`, cerca de las líneas 4279 y 4317.

## Siguiente

Arranco VALOR-1, leyendo antes la decisión del 2026-10-24 en `DECISIONS.md`.
Después sigue SEPARADORES-1. Si el veredicto trae una devolución, esa va
primero.

Última vuelta: 2026-10-24 22:20 UTC.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM, rutina horaria minuto 35. Entregadas la devolución de MARIA-7 y MARIA-8: suite sobre 536c679 (1 rojo de entorno, test_excel2), sabotajes, smoke y e2e sobre 30ceace; D9–D11 abiertas en PARA-PM-2.md. Sigue VALOR-1 y después SEPARADORES-1. Nunca main, sin push --force, sin datos reales del 24/10, nada se publica sin el «dale» de Emi para el SHA, sin Gemini en pruebas, subagentes hasta esfuerzo alto, sin advisor.
