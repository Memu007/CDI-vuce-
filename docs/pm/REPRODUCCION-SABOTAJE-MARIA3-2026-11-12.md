# Reproducción: re-anclaje de `sabotaje_maria3.sh` (MARIA), 2026-11-12

Entrega `29880eeb` (informe `8c4a4346`), base `3af35be`. Sólo arnés:
producto +0/−0. Revisó la PM principal, en un worktree aparte en `29880eeb`.

## Lo reproducido

| qué | salida |
|---|---|
| `sabotaje_maria3.sh 29880eeb /tmp/cdi-pm/venv`, entero | `VERDE sin sabotaje: 136 passed`; 30 `ROJO`; «OK: los 30 sabotajes dan rojo por la razón esperada»; rc=0, 189 s |
| `anclas_perdidas.py 29880eeb \| grep -c sabotaje_maria3` | `0` |
| `chequeo-6.py 3af35be 29880eeb` | producto +0/−0, arnés +21/−28, historia vacía, avisos: 0 |
| tabla de países | 309 códigos; `100` no está, `999` sí |

## Mis negativos

- **D196, con otro dato.** Cambié «100» por «0100» en una copia y apliqué
  la mutación 18 (saca `codigo in _tabla_oficial()`): `2 failed`
  (`[/generate_maria-0100]` y `[/generate_maria/avisos-0100]`). Sin la
  mutación, los 14 casos de procedencia pasan. El dato prueba la tabla, no
  sólo el «100».
- **D198.** Saqué sólo la validación del flete del endpoint
  (`importe_valido(request.flete, "Flete")`): fallan los dos casos de
  `/generate_maria/avisos` (`flete-inf` y `flete--500`) y los de
  `/generate_maria` siguen verdes. Confirma lo que dice el informe: en avisos
  hay una sola defensa y ningún sabotaje la nombra.
- **La razón del rojo, a mano, en dos re-anclajes puros.** 13: `assert 200 == 401`.
  27: el `ValueError` de «inf» se escapa sin convertirse en 400. Las dos son
  la protección que nombra su comentario.
- **D197: es una mutación equivalente.** `_codigo_de_la_tabla` se usa sólo
  en `origen_iso2` (`despacho_lector.py:259`), y ahí el código después se
  busca en `_iso2_por_codigo_maria()`, que tiene 194 códigos, todos de la
  tabla oficial (0 fuera). Sacar el chequeo de tabla no cambia lo que
  devuelve: ningún caso puede distinguirlo hoy. No corrí las pruebas del
  lector con la mutación (la corrida quedó tapada por ruido de asyncio); la
  cuenta del mapa alcanza.

## No corrí

- La suite entera: pieza de arnés con producto +0/−0.
- El rojo del guion viejo sobre `3af35be` (lo informa la Dev).
- `/security-review`: no toca producto.
- `e2e_maria.sh` y el guion sobre la unión: arnés con producto +0/−0, y la
  unión es igual a `29880eeb` en lo que corre el guion.

## La unión

Integrada en `e3d6be57`. `git diff 29880eeb HEAD` sobre `proyecto_maria/`,
el guion y su prueba da vacío, y `anclas_perdidas.py HEAD` no da filas del
guion: la corrida de arriba vale para la cabeza.

## Escape

Ninguno.
