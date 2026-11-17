# D239 (a): reproducción de la PM

Entrega `196ef370` (informe `0364f07e`, canal `PARA-PM-2.md`). Base `2e69a0b1`. Producto:
`despacho_lector.py` (`origen_iso2` separa el código del nombre y compara países) y `clientes.js`
(origen sin tope de dos letras, etiqueta «Origen», «Origen frecuente» con `mostrar`).
Veredicto: **devolución sobre `196ef370`**, una sola causa (abajo). La vuelta, **aceptada sobre `01c28e83`** (al final).

## Corrido por la PM (2026-11-17, hasta las 03:04 UTC)

| Qué | Resultado |
|---|---|
| `chequeo-6.py 2e69a0b1 196ef370` | producto +19/−15, historia vacía, `avisos: 0`, como en el informe |
| `test_catalogo3.py` + `test_despacho1b.py` sobre `196ef370` | `395 passed` |
| rojo con el arreglo revertido | `1 failed`, «At index 0 diff: '310' != '143'» |
| `sabotajes/sin_sigla.sh` (copia del SHA) | 6/6 `ROJO`, «sabotajes sin rojo: 0», salida 0 |
| `sabotajes/holanda423.sh` (copia del SHA) | 17/17 `ROJO`, «sabotajes sin rojo: 0» |
| `e2e_maria.sh` sobre el SHA | «E2E MARIA OK…», salida 0 |
| `sabotajes/catalogo3.sh` (copia del SHA) | `rc=0`, 65 `ROJO`, 0 «ROJO?» ni sin rojo, «fallas: 0» (03:04) |
| volcado del lector (guion de la Dev, 11348 formas) | 3570 cambian; al TXT sólo 6 cambian de código (435/436 Chipre/Turquía y 511), todas correcciones; 2530 ganan origen y 812 lo pierden (229 + 583), como en el informe |
| tabla entera, «NNN nombre» y «NNN · nombre» | base 502 con origen y 114 sin; `196ef370` 616 con origen y 0 sin |
| negativos míos | «143 - REP. DE SUDAFRICA» → 143; «143\tchina» → ninguno (la base daba CN); «143 sudáfrica» → ninguno; «143.» y «143 ORIGEN» → 143 |

## Adversario (Opus, sin red, `GEMINI_API_KEY` vacía) y lo que reproduje

Una causa: lo que queda después del código y no se reconoce como nombre se descarta, y gana el
código aunque ese resto nombre otro país. Reproducido por mí, base → `196ef370`:

| texto | base | `196ef370` |
|---|---|---|
| «143 CHINA (MAINLAND)» | CN | 143 |
| «310 HONG KONG (TERRITORIO DE CHINA)» | ninguno | CN |
| «212 VATICANO(SANTA SEDE)» | ninguno | US |
| «410 MADEIRA (TERRITORIO DE PORTUGAL)» | ninguno | ES |
| «143,00 310 CHINA» | ninguno | 143 |
| «143 310 CHINA» | ninguno | 143 |
| «143.5 CHINA» | ninguno | 143 |
| «310 (HONG KONG)» | CN | ninguno |

- Nombres de la tabla con paréntesis: unos 30. Los que terminan en punto («212 TERRIT.VINCULADOS
  A FRANCIA AMERIC.») quedan sin origen en los dos.
- Número pegado a otro número: el adversario mostró el camino por `leer_texto` con kilos que se
  superponen con la columna de origen. No lo reproduje con un PDF real. «212,00 310 CHINA» ya daba
  US en la base.
- Patrón cuadrático: el adversario midió 9,2 s de CPU en `leer_texto` con 500 subítems armados a
  mano (base 0,08 s). Yo medí una llamada: 0,018 s contra 0,0001 s. Necesita un PDF fabricado y el
  tope de CPU lo corta: riesgo escrito, no criterio.
- Limpio según el adversario: la tabla entera ida y vuelta, ninguna excepción con entradas raras,
  y el servidor rechaza lo que no está en la tabla aunque el campo no tenga tope.

## Pérdidas con aviso (decidido por la PM: aceptadas)

«402 ALEMANIA», «601 RUSIA», «668 HONG KONG», «653 ARUBA», «432 SERBIA», «250 ARGENTINA»,
«999 CHINA», «143 ZA» y «511 US» pasan de un país a ninguno con aviso. Ninguna pone un país
equivocado. El nombre de la tabla de cada código sigue andando (616/616), y las parejas
«código · nombre» de la pantalla siguen todas con origen.

## No corrido

- Suite completa sobre `196ef370`: la Dev la corrió sobre `1513c4f0` (6198 passed). Va en la vuelta.
- `despacho1b.sh`: ni la Dev ni yo. Va en la vuelta.
- `e2e_maria.sh` sobre la unión con mi rama: mi rama sólo cambia `docs/pm`, así que el producto es
  el mismo que el del SHA.

## Vuelta sobre `01c28e83` (informe `42cad854`): aceptada (2026-11-17)

Una causa arreglada: el resto después del código se compara con el índice de nombres y alias; si
nombra otro país o no se reconoce, no hay origen (con aviso). Producto `despacho_lector.py`.

| Qué | Resultado (corrido por la PM) |
|---|---|
| `chequeo-6.py 2e69a0b1 01c28e83` | producto +57/−14, «AVISO producto suma 43 líneas netas», arnés +148/−5, historia vacía, `avisos: 1`, como en el informe |
| rojo con el arreglo revertido | `1 failed, 1 passed`, «At index 7 diff: None != 'RESTO (AFRICA)'» |
| suite completa sobre `01c28e83` | `6199 passed, 110 skipped, 3 xfailed`, salida 0 (1109 s) |
| `sabotajes/sin_sigla.sh` (copia del SHA) | 16/16 `ROJO`, «sabotajes sin rojo: 0», salida 0 |
| `sabotajes/holanda423.sh` (copia del SHA) | 17/17 `ROJO`, «sabotajes sin rojo: 0», salida 0 |
| `e2e_maria.sh` sobre el SHA | «E2E MARIA OK…», salida 0 |
| `despacho1b.sh` con Postgres (`pm_d239`) | en curso: 11 `ROJO` y 0 sin rojo a las 08:51 UTC; la Dev lo corrió entero. Se completa en la próxima vuelta; un «sin rojo» reabre la pieza |
| volcado del lector (11348 formas) | 0 diferencias contra `196ef370` |
| anclas perdidas | 1 en base y en `01c28e83` (`limpieza1.sh:135`), igual |
| tabla entera ida y vuelta | 616 con origen |
| cada código × cada nombre o alias del índice (728), 4 formas, ~900 000 | base 434 918 con país equivocado (422 038 código de otro país + 12 880 un tercero); `01c28e83` 0 equivocados (2940 por código, 2181 por nombre, el resto sin origen) |
| ejemplo no dado «212 ARUBA (TERRITORIO DE PAISES BAJOS)» | ninguno (en `196ef370` daba US) |
| pérdidas con aviso nuevas | «310 12», «310 12,5 KG», «143 - REP. DE SUDAFRICA» → ninguno |

El «0 equivocados» vale para los nombres y alias que el índice conoce.

## Adversario de la vuelta (Opus alto, sin red, `GEMINI_API_KEY` vacía) y lo que reproduje

Unas 2,5 millones de formas. Reproducido por mí, base → `01c28e83`:

| texto | base | `01c28e83` | |
|---|---|---|---|
| «３１０ ＢＲ» (dígitos de ancho completo) | ninguno | BR | nuevo de esta vuelta (`196ef370` daba ninguno) |
| «435 República Dominicana» | ninguno | 435 (Chipre) | vino con la primera entrega (`196ef370` igual) |
| «233 REPUBLICA DOMINICANA», «212 REP. DOMINICANA», «309 REPUBLICA POPULAR DEMOCRATICA DE COREA», «118 GUINEA BISAU», «310 NUEVA ZELANDA», «310 KENIA» | DM, US, KR, GN, CN, CN | igual | ya estaba en la base |
| «100 KG», «100 TON», «050 BOL» | KG, TO, BO | igual | ya estaba (como D267) |

- Ancho completo: `re.match(r"(\d{3})…")` acepta dígitos Unicode y `codigo_de_pais` sólo [0-9];
  el texto cae en la rama de fuera de la tabla, que después de NFKD saltea la regla de sigla ASCII.
  Con ASCII no sale. Riesgo escrito.
- Con ASCII el adversario no encontró país equivocado en separadores, mayúsculas y acentos,
  códigos fuera de la tabla, dos nombres, ISO3, ceros a la izquierda ni nombres partidos.
- CPU: ningún texto pasa 0,05 s; lo largo es lineal.

## Riesgos escritos (decidido por la PM)

- **D266, ampliado:** un nombre que el índice no conoce, en inglés o en castellano («435 República
  Dominicana» → 435), deja ganar al código. D264 (a) extendió esa clase a los códigos sin sigla.
  Hoy no hay camino: `origen_iso2` sólo lee el campo «Origen Pais / Provincia» del despacho
  impreso por el sistema oficial, que trae el nombre de la tabla (los ejemplos de prueba dicen
  «310 CHINA», «900 ATLANTIDA»), y lo que se escribe en pantalla o catálogo pasa por
  `origen_para_catalogo`, no por `origen_iso2`. Va a Emi como propuesta de alias, junto con el
  ancho completo.
- **D267** («900 SD» da Sudán, y SN, NO, SI, ROU): ya estaba en la base.
- Tope de CPU de `test_despacho1b` bajo carga: no es de esta pieza.

## No corrido

- `despacho1b.sh` entero por la PM: en curso (arriba).
