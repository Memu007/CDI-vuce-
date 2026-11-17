# D239 (a): reproducción de la PM

Entrega `196ef370` (informe `0364f07e`, canal `PARA-PM-2.md`). Base `2e69a0b1`. Producto:
`despacho_lector.py` (`origen_iso2` separa el código del nombre y compara países) y `clientes.js`
(origen sin tope de dos letras, etiqueta «Origen», «Origen frecuente» con `mostrar`).
Veredicto: **devolución sobre `196ef370`**, una sola causa (abajo).

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
