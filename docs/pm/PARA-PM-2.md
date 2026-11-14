# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Vencido `sabotajes/guardar2.sh`: entregado en `aeb994f`. Sus 11 sabotajes dan rojo, `rc=0`; no queda ningún `vencido`. Nada para decidir

| qué | SHA |
|---|---|
| base (informe de `sabotaje_maria7.sh`) | `0260962` |
| pruebas: un ancla reescrita y mi línea fuera de `sabotajes-conocidos.txt`. **Lo que se entrega** | `aeb994f` |
| tu rama (`5f88fa4`: maria7 aceptado y D250 (a)), sólo `docs/pm/` | `d6f72f3` |
| informe | el commit siguiente |

`producto +0/−0`. `arnés +1/−1`: `scripts/testing/sabotajes/guardar2.sh` y una
línea menos en `docs/pm/herramientas/sabotajes-conocidos.txt`.

El SHA que entrego pasó por un adversario (abajo, «Revisión adversarial»).

Las mediciones son sobre `aeb994f`. Tu rama entró después y no toca ni el
guion ni `sabotajes-conocidos.txt` (`grep -c '^vencido'` sigue en 0 en
`d6f72f3`).

## Decisiones

Nada para decidir. Sin supuestos: no agregué nada que la tarea no pida.

D250 la contestaste con (a) mientras cerraba este informe: la leí en
`PARA-DEV-2.md` con su criterio y va después de D249.

## Lo que cambió

```diff
 sabotaje $M "gana la SIM de otro producto parecido del proveedor" \
-  '            or del_proveedor["producto_key"] != catalog_svc._normalize(recordado.get("descripcion") or "")):' \
+  '            or del_proveedor["producto_key"] != catalog_svc.clave_de_producto(recordado.get("descripcion") or "")):' \
   '            ):' \
   "FAILED $T::test_la_sim_de_otro_producto_parecido_no_gana"
```

Por qué se había perdido: `9622196` (GUARDAR-2) escribió la comparación con
`catalog_svc._normalize(...)`. `6cbd192` (2026-11-10, el catálogo no mezcla
productos en chino) cambió quién da la clave del producto:
`catalog_svc.clave_de_producto(...)`. La comparación quedó en el mismo lugar
(`main.py:10176-10177`, en `_ncm_recordado_con_sim_del_proveedor`).

Antes de reescribir comprobé que la protección sigue existiendo (D195 (a)):
no hay sabotaje para retirar. El ancla nueva es código, está una vez en
`main.py` y el sabotaje saca lo mismo que antes: la condición «es el mismo
producto».

El otro sentido de esa línea (volver de `clave_de_producto` a `_normalize`)
ya lo ataca `sabotajes/catalogo3.sh:169-172`, con su propia prueba. No lo
toqué ni lo corrí.

## Resultado

| qué | antes, guion de `0260962` | ahora, `aeb994f` |
|---|---|---|
| el guion | 10 `ROJO`, 1 `ROTO` («el sabotaje no encontró su patrón»), `sabotajes con falla: 1`; `rc=1` | 11 `ROJO`, `sabotajes con falla: 0`; `rc=0` |
| «gana la SIM de otro producto parecido del proveedor» | `patrón no encontrado una sola vez (0)` | `ROJO … dice «FAILED tests/test_guardar2.py::test_la_sim_de_otro_producto_parecido_no_gana»` |
| mi línea en `sabotajes-conocidos.txt` | estaba | no está; `grep -c '^vencido'` da 0 |

A diferencia de `sabotaje_maria7.sh`, este guion no corta al no encontrar
un patrón: marca `ROTO` y sigue. Los otros 10 sabotajes dan rojo también con
el guion de la base.

La mutación medida a mano, en un worktree descartable, con
`tests/test_guardar2.py` entero (sin mutación: `22 passed`):
`1 failed, 21 passed`. Sólo `test_la_sim_de_otro_producto_parecido_no_gana`,
por aserción:

```
E   AssertionError: assert '73181500900Z' == '73181500'
```

Sale la SIM del otro producto del proveedor donde tenía que quedar el NCM
de 8 dígitos del cliente.

## Revisión adversarial

Pieza chica de arnés: un adversario Sonnet, esfuerzo medio, sobre `aeb994f`,
en worktrees propios que retiró al terminar.

**Defectos del diff: ninguno.** Confirmó, corriéndolo: la protección sigue
en `main.py:10177` y `6cbd192` sólo cambió el nombre de la función en esa
línea; el ancla es código y está una vez; la mutación compila y da
`1 failed, 21 passed` por aserción; el guion da 11 `ROJO` y
`sabotajes con falla: 0`; `^vencido` da 0 y `anclas_perdidas.py` no informa
pérdidas. Revisó las otras 10 anclas del guion: cada una ataca lo que su
nombre dice.

Probó cuatro mutaciones vecinas de la misma condición, sólo con
`tests/test_guardar2.py`. Dos dan rojo. Las dos que le quedaron verdes las
medí yo con los 12 archivos de `tests/` que nombran `catalog/lookup`,
`ncm/sugerir` o `producto_key` (sin mutación: `758 passed`):

| mutación | su medición | la mía | queda |
|---|---|---|---|
| `clave_de_producto` vuelve a `_normalize` | `22 passed` en `test_guardar2.py`; con cinco archivos más, `1 failed` | `1 failed, 757 passed`: `test_catalogo3.py::test_el_ncm_recordado_compara_con_la_clave_del_catalogo`, el dato en chino | no es un hueco; además lo ataca `catalogo3.sh:169-172` |
| sale `not del_proveedor.get("producto_key")` | `22 passed`; «casi seguro es redundante» | `758 passed` | no cambia nada: riesgo 1 |

Una cosa de su informe: el `rc=0` que vio era el de su `tail`, no el del
guion. El mío está en el log entero: `rc=0`.

No corrí `/code-review`: el SHA que se entrega pasó por el adversario, que es
una de las dos que pediste.

## Comandos

```bash
PY=/ruta/a/tu/venv/bin/python
git diff 0260962 aeb994f --stat | tail -1    # 2 files changed, 1 insertion(+), 2 deletions(-)
env -u DATABASE_URL -u ENVIRONMENT PY=$PY scripts/testing/sabotajes/guardar2.sh aeb994f | tail -1; echo ${PIPESTATUS[0]}
#   sabotajes con falla: 0
#   0
grep -c '^vencido' docs/pm/herramientas/sabotajes-conocidos.txt    # 0
$PY scripts/testing/anclas_perdidas.py aeb994f | sed -n 2,4p
#   perdida, una línea          0   guiones: 0
#   perdida, varias líneas      0   guiones: 0
#   otra cantidad               0   guiones: 0

# el rojo sin el arreglo: el guion de la base
env -u DATABASE_URL -u ENVIRONMENT PY=$PY scripts/testing/sabotajes/guardar2.sh 0260962 2>&1 | grep -E 'ROTO|patrón|falla'; echo ${PIPESTATUS[0]}
#   patrón no encontrado una sola vez (0): '            or del_proveedor["producto_key"] != catalog_svc._normalize(recordado.get("descripcion") or "")):'
#   ROTO  | gana la SIM de otro producto parecido del proveedor: el sabotaje no encontró su patrón
#   sabotajes con falla: 1
#   1
```

Corrí cada guion una vez, con `HEAD` parado en el SHA que mide y la salida
entera a un archivo; esas son sus líneas. Los `| tail`, `| sed` y `| grep`
de arriba no los corrí así: leí las mismas líneas del archivo.

## Puertas

Sobre `aeb994f`, árbol limpio.

| puerta | salida |
|---|---|
| `sabotajes/guardar2.sh aeb994f` | 11 `ROJO`, `sabotajes con falla: 0`; `rc=0` |
| `tests/test_anclas_perdidas.py` | `27 passed` |
| `anclas_perdidas.py aeb994f` | `103 guiones, 2493 anclas medidas y 11 llamadas sin medir`; `perdida, una línea 0`, `perdida, varias líneas 0`, `otra cantidad 0`; `rc=0` |
| `chequeo-6.py 0260962 aeb994f` | abajo, `avisos: 0` |
| `bash -n scripts/testing/sabotajes/guardar2.sh` | sin errores |

Con esto `anclas_perdidas.py` da 0, 0 y 0 y la lista no tiene ninguna
línea `vencido`.

**No corrido:** la suite entera (cambió un guion, ningún producto ni prueba),
`compileall`, las pantallas, `e2e_maria.sh`, `smoke_friccion.sh`,
`ataque_aislamiento.sh`, Postgres, los demás guiones de sabotaje (tampoco
`catalogo3.sh`, que ataca la misma línea), `/code-review` y
`/security-review` (el diff no toca producto).

## `chequeo-6`

```
chequeo-6 0260962..aeb994f: avisos para mirar, no un veredicto
producto +0/−0
arnés +1/−1
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

1. **`not del_proveedor.get("producto_key")` (`main.py:10176`) no lo
   distingue ninguna prueba** (previo, de `9622196`; no es de este diff).
   Leyendo el código, sobra: `match_items` siempre pone la clave (`None` o
   una clave del catálogo, `catalog_service.py:378`, `:390`, `:410`) y
   `clave_de_producto` nunca devuelve vacío, así que con `None` la
   comparación de la línea siguiente ya devuelve el NCM del cliente. Lo
   sostengo con la lectura y con los `758 passed`; no escribí una prueba
   que lo demuestre. Severidad baja: no hay un comportamiento sin proteger,
   hay una condición de más.
2. **El guion no fija cuántos sabotajes tiene**: termina con
   `sabotajes con falla: 0` y no dice que fueron 11. Si alguien borra un
   sabotaje, sigue saliendo 0. Previo; la cuenta la da
   `grep -c '^ROJO  |'` sobre la salida.

## Líneas para `COLA-LIMPIEZA.md`

- `proyecto_maria/main.py:10176`: `not del_proveedor.get("producto_key")`
  parece sobrar (la comparación de la línea siguiente ya cubre el `None`);
  sacarlo, o dejarlo con una prueba que lo distinga.
- `scripts/testing/sabotajes/guardar2.sh`: el final no dice cuántos
  sabotajes corrieron.

## Archivos de producto que toqué

Ninguno.

## Sigo con

D249 (a): `tests/test_sufijos2.py` y `scripts/testing/sabotajes/sufijos2.sh`,
con el criterio de la sección D247 de `PARA-DEV-2.md`. Después, D250 (a).
D244, D239 y «Holanda» esperan a Emi.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `5f88fa4`). Aceptadas: CUIT-GENERAR sobre `29327d2`, SABOTAJE-SUBITEMS1 sobre `bf6778e`, D243 (b) sobre `0dff850`, SABOTAJE-SUFIJOS1 sobre `afeae84`, D245 (a) sobre `e17c11e`, D246 (b) sobre `0224f01`, SABOTAJE-MARIA8 sobre `50320ff`, D247 (a) sobre `4a58c68`, D248 (c) sobre `3fcc9c4`, los vencidos `sabotaje_maria1d.sh` sobre `6e4e658`, `sabotaje_maria5.sh` sobre `c0505cc`, `sabotaje_valor1b.sh` sobre `70eb5dc`, `sabotaje_doc1.py` sobre `d4c6b73` y `sabotaje_maria7.sh` sobre `4477ae3`. Entregada sin veredicto: **el vencido `sabotajes/guardar2.sh` sobre `aeb994f`** (base `0260962`; sólo el ancla del sabotaje «gana la SIM de otro producto parecido del proveedor», que ahora busca `catalog_svc.clave_de_producto(…)` en `main.py:10177`, y mi línea fuera de `sabotajes-conocidos.txt`, que queda sin ningún `vencido`; arnés +1/−1; 11 `ROJO`, `rc=0`; a mano, 1 failed y 21 passed, sólo su prueba; `anclas_perdidas.py` en 0, 0 y 0; un adversario Sonnet medio revisó `aeb994f`, sin defectos del diff). Si vuelve con devolución, va primero. **Pieza activa: D249 (a)**, decidida por la PM, y después D250 (a): sólo `tests/test_sufijos2.py` y `scripts/testing/sabotajes/sufijos2.sh`, criterio entero en `docs/pm/PARA-DEV-2.md`, sección D247 (la familia de fragmentos «…» de `limpiar_sufijo`, un sabotaje por cambio, `sufijos2.sh` entero en `ROJO` con la cuenta exacta, `sabotaje_sufijos1.sh` en 46, anclas que no empeoran: el criterio dice 5 y 1 y hoy son 0 y 0). **D250 (a)**, decidida por la PM, criterio en `PARA-DEV-2.md`: la familia de entradas del aviso «los N sub-ítems llevan el mismo sufijo» como datos de un solo caso de `tests/test_maria8_subitems_por_posicion.py` (el texto que muestra, cuándo sale y cuándo no); mi sabotaje de `maria_generator.py:2235` (`limpiar_sufijo(str(sbt_sufijo_valor or "").strip())[0]` por `str(sbt_sufijo_valor or "").strip()`) en `sabotaje_maria8.sh` da `ROJO` con una prueba nombrada; `sabotaje_maria8.sh` entero en `ROJO` con la cuenta exacta; las anclas no empeoran. D244, D239 y «Holanda» esperan a Emi: no se tocan. Próxima D: D251. Lecciones: antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada; un dato nuevo de un caso no reusa un valor que otro control del mismo caso espera; antes de escribir el informe se trae la rama de la PM; antes de sacar una prueba por duplicada se compara lo que afirma cada una, no sólo sus entradas; antes de reescribir un sabotaje con el ancla perdida se mira si la protección que atacaba sigue existiendo: si no, es una D (D195 (a)); al ajustar una afirmación, la nueva tiene que seguir afirmando todo lo que afirmaba la vieja (el orden también), y una mutación que «mueve» una frase la tiene que sacar de donde estaba; una medición corre sobre el conjunto más angosto de pruebas que contesta la pregunta; antes de cambiar un número que la PM fijó como criterio se lee por qué lo fijó; un comentario o un mensaje de commit no afirma lo que el guion no obliga, y su porqué se comprueba con `git show`, no se supone; que «nadie cubría» algo se mide antes de escribirlo, y con todas las pruebas que usan ese dato, no sólo las del guion (un adversario que corre cuatro archivos dice «hueco» donde otra prueba lo atrapa); `anclas_perdidas.py` mide un commit: el arreglo se commitea antes de medir; el SHA que se entrega pasa por subagente o `/code-review`, y si el gancho de parada ya subió el commit, lo que siga va en un commit nuevo; después de un commit nuevo o de corregir uno, las puertas corren otra vez sobre ese SHA; un ancla lleva sólo el texto que saca más lo mínimo que la ata a su lugar; la cuenta escrita a mano en el último `echo` de un guion se compara con sus líneas `ROJO`; una mutación se mide a mano con el archivo de pruebas entero, para ver que pone en rojo sólo lo suyo y por aserción; `anclas_perdidas.py` sólo lee los `.sh`; un worktree que aparece en `git worktree list` mientras corre un guion mío es de ese guion, no un resto; una espera de 110 vueltas de 5 s no alcanza para tres corridas de 4 minutos: se vuelve a esperar la marca de fin, no se relanza; mientras haya una D mía sin contestar, el informe siguiente la repite arriba; regla de la PM: en un vencido de sólo arnés, un último commit que cambia únicamente comentarios no necesita revisor si el informe lo dice, cualquier otro cambio sí. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que una D autoriza; subagentes hasta esfuerzo alto y sin consejero.
