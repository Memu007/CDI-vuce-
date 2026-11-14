# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## SABOTAJE-SUFIJOS1: entregada en `afeae84`. `sabotaje_sufijos1.sh` vuelve a dar rojo en sus 47 casos y `sufijo_otra1` prueba la operación siguiente con su propio sufijo guardado. Sólo arnés. Una decisión: D246

| qué | SHA |
|---|---|
| base (informe de D243 b) | `4474108` |
| pruebas: el caso 11 del guion, el dato nuevo de la pantalla y la línea de `sabotajes-conocidos.txt` | `c645260` |
| arreglo de lo que encontró `/code-review`. **Lo que se entrega** | `afeae84` |
| informe | el commit siguiente |

`producto +0/−0`. `arnés +18/−10` en `scripts/testing/sabotaje_sufijos1.sh`
y `scripts/testing/pantalla_sufijo_otra1.js`, más una línea menos en
`docs/pm/herramientas/sabotajes-conocidos.txt` (la mía; quedan 7 vencidos).

Tu rama no tiene commits nuevos desde `036e294`.

## Decisiones

**D246. El caso 11 de `sabotaje_sufijos1.sh` quedó igual al sabotaje 3 de
`sabotajes/sufijos2.sh`.** La prueba que el caso 11 esperaba
(`test_un_codigo_con_el_valor_vacio_es_un_codigo_que_falta`) ya no existe: la
reemplazó `test_un_codigo_con_el_valor_vacio_no_se_genera`. El único control
que esa prueba distingue es `if not limpio.strip():` de `limpiar_sufijo`, así
que el caso 11 ahora lo saca con `if False:`. Es la misma línea y el mismo
cambio que `sabotajes/sufijos2.sh:107-110`, y la prueba de `test_sufijos1` es
una versión más angosta de las de `test_sufijos2` (mira sólo «AA( )»; las
otras miran cuatro formas de vacío, ver «Notas»).

- (a) queda como se entrega: 47 casos, el control con dos sabotajes iguales en
  dos guiones.
- (b) en una pieza chica aparte saco el caso 11 y
  `tests/test_sufijos1.py::test_un_codigo_con_el_valor_vacio_no_se_genera`
  (el guion queda en 46). El control sigue cubierto por `test_sufijos2` y su
  guion.
- **Recomiendo (b):** es un ancla menos para perder en dos guiones y no se
  pierde cobertura. La entrega vale con cualquiera de las dos.

Próxima D: D247.

## Lo que cambió

**`sabotaje_sufijos1.sh`, caso 11.** Antes sacaba el filtro
`if v.strip() or len(c) == 4` de `_avisos_del_arancel` y esperaba una prueba
que ya no existe: daba verde. Ahora:

```
# 11. un código con el valor vacío se genera
reemplazar $G '            if not limpio.strip():' '            if False:'
caso "codigo_vacio_se_genera" "FAILED $T::test_un_codigo_con_el_valor_vacio_no_se_genera"
```

El encabezado del guion dice lo mismo. El ancla aparece una vez en
`maria_generator.py` (`:417`).

**`pantalla_sufijo_otra1.js`.** La «operación siguiente» era una sola, sin
sufijo. Ahora son dos datos del mismo caso: una con su sufijo guardado
(`AA(000789)`) y una sin sufijo. Cada una entra después de un freno de la
anterior, y de cada una se mira que entra sin el aviso de la anterior, que
el campo trae el suyo (o vacío) y que frena con el campo vacío (a la que
trae sufijo se le borra antes). El final, que escribe otro sufijo
(`AA(000456)`) y mira avisos y TXT, no cambió.

## Resultado

Sobre `afeae84`:

| qué | salida |
|---|---|
| `sabotaje_sufijos1.sh afeae84` | 47 `ROJO`, `OK: los 47 sabotajes dan rojo por la razón esperada`, `rc=0` |
| el caso 11 | `ROJO   codigo_vacio_se_genera: 1 failed, 61 passed` |
| pantallas `maria9`, `sufijo_borrador1`, `sufijo_otra1` | `resumen: 3 verdes, 0 rojas`, `rc=0` |

En la base `4474108` el guion daba 46 `ROJO`,
`FALLA  codigo_vacio_cargado: quedó verde`, `FALLAN 1 sabotajes`, `rc=1`.

## Negativos

Cada uno es un cambio de una o dos líneas en `finalize.js` sobre un commit
descartable (ninguno subido), con `sufijo_otra1` corrida por
`correr_pantallas.sh`.

| cambio en `finalize.js` | sobre | resultado |
|---|---|---|
| `pintarSufijo` esconde el aviso sólo si el campo entra vacío (el que pediste) | base `4474108` | **verde**: la pantalla vieja no lo veía |
| el mismo | `afeae84` | `FALLA: otra operación, con su sufijo guardado, entra con el aviso de la anterior a la vista: «Ingresá el sufijo de valor SBT. Es obligatorio.»` |
| `pintarSufijo` no esconde nunca el aviso | `afeae84` | el mismo texto |
| el aviso se va con `change` y no con `input` | `afeae84` | `FALLA: con el sufijo ya escrito, el aviso sigue a la vista: «Ingresá el sufijo de valor SBT. Es obligatorio.»` |
| borrar el campo no se guarda en la operación | `afeae84` | `FALLA: otra operación, con su sufijo guardado, no frenó con el campo vacío` |
| el sufijo guardado de una operación se arrastra a los pedidos de la siguiente | `c645260` | **verde** (el defecto de mi primera versión, abajo) |
| el mismo | `afeae84` | `FALLA: con «AA(000456)» escrito, los avisos no se pidieron con ese sufijo` |

## Lo que salió mal y arreglé

En `c645260` la operación con sufijo guardado usaba el mismo valor que se
escribe al final (`AA(000456)`). Un sufijo que se arrastrara de esa operación
a la siguiente dejaba verdes los controles finales de avisos y TXT. Lo encontró
`/code-review`, lo reproduje (penúltima fila de la tabla) y en `afeae84` la
operación guardada lleva uno propio, `AA(000789)`. También reescribí un
comentario que afirmaba algo que la pantalla no mira.

## Notas (ninguna pide decisión)

- **El filtro de `maria_generator.py:2013` quedó muerto.** Es tu línea de
  `COLA-LIMPIEZA.md:257` («ver si quedó muerto y sacarlo»). Sí: los sufijos
  que llegan a ese filtro ya pasaron por `limpiar_sufijo` (`:1947`), que
  levanta error con un valor vacío (`:417`), así que `v.strip()` da siempre
  verdadero. Medido: en la base, sacar el filtro deja `test_sufijos1.py` verde
  (es el `quedó verde` del caso 11 viejo). No lo saqué: es producto y está en
  la cola.
- **La prueba de `test_sufijos1` mira una sola forma de vacío** («AA( )»).
  Dos mutantes del control la dejan verde y los frena `test_sufijos2`:
  `if not valor.strip():` da `test_sufijos1.py` `62 passed` y
  `test_sufijos2.py` `2 failed, 108 passed` (los dos de `[AA(--)-]`);
  `if limpio and not limpio.strip():` da `62 passed` y `5 failed, 105 passed`.
  El control está cubierto; lo que sobra es la prueba angosta (D246).

## Revisión adversarial

| quién | modelo y esfuerzo | sobre | qué encontró |
|---|---|---|---|
| `adversario-sonnet-medio` | Sonnet, medio | `c645260` | Medio: la prueba del caso 11 cubre sólo «AA( )» (reproducido, es la segunda nota y D246). Bajo: la pantalla no mira con qué sufijo se piden los avisos de la operación sin sufijo (reproducido, va a «Riesgos»). Corrió `sufijo_otra1` tres veces, verde las tres. Probó además un bucle que no afirma nada, un pedido viejo que satisface la espera de los avisos y el freno de `onGenerate`: nada. Dos corridas suyas se contaminaron entre sí; las repitió limpias y lo informó. |

## `/code-review high`

Sobre `4474108..c645260`, cinco hallazgos:

| hallazgo | qué hice |
|---|---|
| el dato guardado reusa el sufijo del final y tapa un arrastre | real, reproducido y arreglado en `afeae84` |
| el caso 11 duplica `sabotajes/sufijos2.sh:107-110` | cierto: D246 |
| el filtro de avisos se queda sin sabotaje | cierto y esperado: el filtro está muerto (primera nota), ya está en la cola |
| un comentario afirma algo que no se mira | reescrito en `afeae84` |
| el encabezado de la pantalla mezclaba dos cosas en un paréntesis | separado en `afeae84` |

**Ni el adversario ni `/code-review` vieron `afeae84`.** El arreglo son 6
líneas de `pantalla_sufijo_otra1.js` (una constante, un comentario y el
encabezado); lo medí yo con las dos últimas filas de «Negativos» y las
puertas de abajo.

`/security-review`: no corrido. La pieza no toca producto.

## Comandos

```bash
VENV=/ruta/a/tu/venv
bash scripts/testing/sabotaje_sufijos1.sh afeae84 $VENV | tail -1      # OK: los 47 sabotajes dan rojo por la razón esperada   (8 min)
PY=$VENV/bin/python SOLO="maria9 sufijo_borrador1 sufijo_otra1" \
  scripts/testing/correr_pantallas.sh afeae84 /tmp/salida-suf | tail -1 # resumen: 3 verdes, 0 rojas   (3 min)
$VENV/bin/python scripts/testing/anclas_perdidas.py afeae84 | sed -n 2p  # perdida, una línea          6   guiones: 5
$VENV/bin/python docs/pm/herramientas/chequeo-6.py 4474108 afeae84       # producto +0/−0, arnés +18/−10, avisos: 0
git diff 4474108 afeae84 --stat | tail -1                                # 3 files changed, 18 insertions(+), 11 deletions(-)
```

El negativo que pediste, a mano sobre un worktree de `afeae84`: en
`proyecto_maria/static/v2/screens/finalize.js`, dentro de `pintarSufijo`,
cambiar `if (aviso) aviso.hidden = true;` por
`if (aviso && !campo.value) aviso.hidden = true;`, commitear ahí y correr
`sufijo_otra1` con `correr_pantallas.sh` sobre ese commit. Tiene que dar la
segunda fila de «Negativos».

## Puertas

Sobre `afeae84`, árbol limpio.

| puerta | salida |
|---|---|
| `sabotaje_sufijos1.sh afeae84` | 47 `ROJO`, `OK: los 47 sabotajes dan rojo por la razón esperada`, `rc=0` |
| `correr_pantallas.sh afeae84`, `maria9`, `sufijo_borrador1`, `sufijo_otra1` | `resumen: 3 verdes, 0 rojas`, `rc=0` |
| `anclas_perdidas.py` en `4474108`, `c645260` y `afeae84` | igual en los tres: `perdida, una línea          6   guiones: 5`, `está                     2479   guiones: 101` |
| `chequeo-6.py 4474108 afeae84` | abajo, `avisos: 0` |

**No corrido:** la suite entera (no cambió producto ni ningún archivo que
pytest junte; busqué en `tests/`, `scripts/` y `.github/` quién lee los tres
archivos: sólo ellos mismos y `correr_pantallas.sh`), `compileall`, las demás
pantallas, `e2e_maria.sh`, `smoke_friccion.sh`, `ataque_aislamiento.sh`,
Postgres, los demás guiones de sabotaje (tampoco `sabotajes/sufijos2.sh`, que
no toqué) y `/security-review`.

## `chequeo-6`

```
chequeo-6 4474108..afeae84: avisos para mirar, no un veredicto
producto +0/−0
arnés +18/−10
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

- **Bajo, anterior a esta pieza.** `sufijo_otra1` no mira con qué sufijo se
  piden los avisos de una operación que no tiene sufijo: un mutante que le
  pone el último sufijo visto al pedido de avisos cuando viene vacío queda
  **verde** sobre `afeae84`. El pedido de avisos sale de `buildMariaRequest`,
  la misma función que arma el del TXT, y el TXT sí se mira; para que pase en
  serio haría falta romper sólo el camino de los avisos. No lo arreglé: no es
  lo que pediste y suma un control más a la pantalla. Si lo querés, es un
  dato más del mismo caso.
- Los revisores no vieron `afeae84` (arriba).
- Las 6 anclas perdidas que quedan son de mis otros vencidos.

## Líneas para COLA-LIMPIEZA

Ninguna nueva. La de `:257` tiene respuesta en la primera nota: el filtro
está muerto, se puede sacar.

## Archivos de producto que toqué

Ninguno.

## Sigo con

D245 (a).

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `036e294`). CUIT-GENERAR aceptada sobre `29327d2`; SABOTAJE-SUBITEMS1 aceptada sobre `bf6778e`. D243 (b) entregada sobre `0dff850` y SABOTAJE-SUFIJOS1 entregada sobre `afeae84` (base `4474108`; sólo arnés, +18/−10; el guion da 47 `ROJO`; `sufijo_otra1` lleva la operación siguiente con su sufijo guardado `AA(000789)`), las dos sin veredicto todavía; si alguna vuelve con devolución, va primero. **D246 abierta** (el caso 11 de `sabotaje_sufijos1.sh` duplica el sabotaje 3 de `sabotajes/sufijos2.sh`: (a) queda, (b) saco el caso y la prueba angosta de `test_sufijos1`; recomendé (b)): no se toca hasta que conteste. Orden de la PM: 1) **D245 (a), pieza activa**, sólo pruebas: sumar la afirmación de `success` del semáforo en `test_punta_a_punta1.py` (`:283`), `test_generar_maria_txt.py` (`:797`) y `test_cobro_corte1.py` (`:534`; este es de la Técnica: sólo esa afirmación, sin cambiar lo que ya mira); se acepta con un `raise` dentro del `try` del semáforo: ninguna prueba que lo llama queda verde en los 11 archivos de `tests/` (la PM midió `10 failed` en esos tres: 8, 1 y 1), y sin él los tres archivos verdes enteros (`166 passed, 2 xfailed`); el informe trae ese rojo medido; sin adversario ni `/security-review`. 2) los demás vencidos míos, uno por pieza (maria8, maria1d, maria5, valor1b, doc1.py, maria7, guardar2). D244, D239 y «Holanda» esperan a Emi: no se tocan. Próxima D: D247. Lecciones: antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada; un dato nuevo de un caso no reusa un valor que otro control del mismo caso espera. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que una D autoriza; subagentes hasta esfuerzo alto y sin consejero.
