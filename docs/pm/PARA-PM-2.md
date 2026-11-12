# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D198 (b): entregado en `a2af62a` (sólo arnés). 31 de 31 en rojo, sale 0

| qué | SHA |
|---|---|
| base (tu cabeza `fa0f106`, integrada) | `ffb1ec5` |
| el sabotaje 31: saca sólo la validación del flete del endpoint | `900cf63` |
| su comentario, corregido por la autorrevisión | `6d58836` |
| el ancla del flete, una vez para el 28 y el 31 | `a2af62a` |
| **el que se entrega** | `a2af62a` |
| informe | el commit siguiente |

**Resultado.** El guion entero sobre `a2af62a` da 31 `ROJO` y sale 0.
`anclas_perdidas.py a2af62a` no da ninguna fila del guion. Producto:
**+0/−0**.

Debajo de `ffb1ec5` hay dos commits de `catalogo_largo2` (`81e81e0`,
`ac58fb0`): no son de esta entrega, van en la siguiente.

## Decisiones

**D216. Qué caso espera el sabotaje 31.** Con la validación sacada fallan
los dos casos de avisos, pero por razones distintas:
- `[/generate_maria/avisos-flete--500]`: `assert 200 == 400`.
- `[/generate_maria/avisos-flete-inf]` (el que pediste): no llega a
  responder. `TypeError: unsupported operand type(s) for +: 'float' and
  'decimal.Decimal'`, porque el flete queda sin convertir y se suma al
  seguro.

Opciones:
- (a) Queda `inf`, como pediste.
- (b) Espera `-500`. **Recomiendo (b)**: su rojo dice justo lo que falta (un
  200 donde va un 400); el de `inf` es una cuenta que se rompe más adelante.
  Es cambiar un id.

**D217. El seguro del endpoint no tiene sabotaje.** La línea de al lado,
`request.seguro = importe_valido(request.seguro, "Seguro") or 0`, no la
saca ningún sabotaje del guion. Sacándola a mano: `2 failed, 134 passed`,
`[/generate_maria/avisos-seguro-nan]` y
`[/generate_maria/avisos-seguro-1e+308]`. Las pruebas la cubren; ningún
sabotaje las nombra. No medí si al generar hay otra defensa para el seguro
(los casos de `/generate_maria` quedaron verdes, así que alguna hay).
- (a) Un sabotaje más, de un ancla, que espere
  `[/generate_maria/avisos-seguro-nan]`. **Recomiendo (a)**: es el mismo
  hueco que cerraste para el flete.
- (b) Queda como riesgo anotado.

## Supuesto (reversible)

- El ancla del flete del endpoint quedó en una función,
  `sin_flete_en_el_endpoint`, que usan el 28 y el 31. Estaba copiada dos
  veces: si esa línea del producto cambiaba, el guion frenaba en el 28 y el
  31 aparecía recién en la corrida siguiente.

## Para reproducir

```bash
bash scripts/testing/sabotaje_maria3.sh a2af62a <venv>
# VERDE sin sabotaje: 136 passed; 31 líneas ROJO;
# «OK: los 31 sabotajes dan rojo por la razón esperada»; sale 0
python scripts/testing/anclas_perdidas.py a2af62a | grep -c sabotaje_maria3
# 0
python docs/pm/herramientas/chequeo-6.py ffb1ec5 a2af62a
# producto +0/−0, avisos: 0
```

## Puertas

| puerta | sobre | salida |
|---|---|---|
| guion entero | `a2af62a` | `VERDE  sin sabotaje: 136 passed`; 31 `ROJO`; `ROJO   avisos_flete_sin_validar: 2 failed, 134 passed`; `OK: los 31 sabotajes dan rojo por la razón esperada`; `rc=0 segundos=251` |
| guion entero | `900cf63`, `6d58836` | lo mismo: 31 `ROJO`, `rc=0` (244 s cada una) |
| la mutación 31 a mano | `900cf63` | `2 failed, 134 passed`: los dos casos de avisos de arriba; los de `/generate_maria` siguen verdes |
| `anclas_perdidas.py` | `a2af62a` | ninguna fila de `sabotaje_maria3.sh` |
| `chequeo-6.py ffb1ec5 a2af62a` | | abajo, entera |

```
chequeo-6 ffb1ec5..HEAD: avisos para mirar, no un veredicto
producto +0/−0
arnés +11/−2
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

No hubo rojos intermedios.

## Hallazgos de la autorrevisión

| quién | hallazgo | severidad | qué hice |
|---|---|---|---|
| adversario Sonnet, medio | En avisos nadie más rechaza el flete; `cuentas_del_valor` lo mira pero devuelve su error adentro de un 200 | — | nada |
| adversario Sonnet, medio | Mi comentario decía «no lo mira nadie más»: falso | baja | arreglado: «no lo rechaza nadie más» |
| adversario Sonnet, medio | El id `inf` da rojo por un `TypeError`; `-500` da el 200 | media | D216 |
| `/code-review high` (revisores Fable, alto) | Lo mismo del id `inf` | baja | D216 |
| `/code-review high` | El seguro del endpoint no tiene sabotaje | baja | D217, reproducido |
| `/code-review high` | El ancla del flete, copiada en el 28 y el 31 | baja | arreglado en `a2af62a` |
| `/code-review high` | El «31» del mensaje final se cambia a mano; otros guiones lo cuentan en `caso` | baja | no lo toqué: ya estaba escrito así. Propongo la línea para la cola de limpieza: «`sabotaje_maria3.sh`: contar los casos en `caso` en vez de escribir el número» |

`/security-review`: no corrido. La pieza no toca producto.

## Qué no corrí y riesgos

- La suite entera: no. Es arnés, producto +0/−0.
- Riesgo: hasta que decidas D216, el rojo que espera el 31 es el del
  `TypeError`.

Archivos de producto tocados: ninguno. Arnés:
`scripts/testing/sabotaje_maria3.sh`.

## `catalogo_largo2`: dónde está (no es esta entrega)

Sigo con ella ahora. Lo medido hasta acá, sobre `ac58fb0`:
- Las siete anclas, re-ancladas: los siete sabotajes dan `ROJO` con su
  texto.
- El guion entero con Postgres, con un sabotaje salteado sólo en una copia
  local: 36 `ROJO`, `fallas: 0`, `rc=0`.
- Ese sabotaje es «la clave junta ﬁ con fi». Queda verde con su ancla
  presente: hoy el producto las junta a propósito. Va como D199, de
  retirarlo, en el informe de esa pieza.
- La prueba de Postgres estaba en rojo sin sabotaje por un dato viejo del
  arnés (`81e81e0`). Va como supuesto en ese informe.

Falta: autorrevisión, `/code-review` e informe.

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn, cabeza fa0f106, ya integrada en ffb1ec5), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. sabotaje_maria3.sh aceptado sobre 29880ee. D198 (b) entregado en a2af62a (informe en el commit siguiente), esperando veredicto: 31 de 31 en rojo, sale 0, producto +0/−0. Abiertas, las decide la PM: D216 (el sabotaje 31 espera el id inf o el de -500), D217 (sabotaje para el seguro del endpoint). Pieza activa: re-anclar sabotajes/catalogo_largo2.sh; commits 81e81e0 (arnés de Postgres) y ac58fb0 (siete anclas), ya subidos; el guion entero sobre ac58fb0 con «la clave junta ﬁ con fi» salteado en una copia local dio 36 ROJO, fallas 0, rc=0; falta anclas_perdidas.py y chequeo-6 sobre la cabeza, adversario, /code-review e informe con D199 (retirar ese sabotaje); su línea queda en herramientas/sabotajes-conocidos.txt hasta que la PM decida. Después, una pieza por guion: valor1, maria8, maria1d, maria5, valor1b, doc1.py, maria7, guardar2. Rango de D: D216 a D225 y D199; próxima libre D218. Una devolución de la PM o la tarea de comparación van primero. Los detalles están en PARA-PM-2.md: el resumen los cita, no los copia. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; las Devs no usan el consejero.
