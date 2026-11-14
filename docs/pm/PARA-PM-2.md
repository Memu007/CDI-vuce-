# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Vencido `sabotaje_maria7.sh`: entregado en `4477ae3`. Sus 25 sabotajes dan rojo, `rc=0`; queda 1 `vencido`. Una decisión: D250

| qué | SHA |
|---|---|
| base (informe de doc1) | `f3a7d29` |
| pruebas: un ancla reescrita y mi línea fuera de `sabotajes-conocidos.txt`. **Lo que se entrega** | `4477ae3` |
| merge de tu rama (`671c759`), sólo `docs/pm/` | `f433601` |
| informe | el commit siguiente |

`producto +0/−0`. `arnés +1/−1`: `scripts/testing/sabotaje_maria7.sh` y una
línea menos en `docs/pm/herramientas/sabotajes-conocidos.txt`.

El SHA que entrego pasó por un adversario (abajo, «Revisión adversarial»).

## Decisiones

### D250: el aviso «los N sub-ítems llevan el mismo sufijo» compara con el sufijo de la operación ya limpio, y ninguna prueba lo distingue

No es de esta pieza ni del guion `maria7`: es de los avisos de MARIA-8
(`maria_generator.py:2235`, dentro de `supuestos_declarados`). Lo encontró
el adversario y lo medí yo.

Con esa línea sin limpiar
(`or limpiar_sufijo(str(sbt_sufijo_valor or "").strip())[0]` cambiado por
`or str(sbt_sufijo_valor or "").strip()`), los 27 archivos de `tests/` que
usan `sbt_sufijo_valor` dan `1126 passed, 2 xfailed`, igual que sin el cambio.

Lo que cambia a la vista, con tres renglones de la misma posición:

| caso | hoy | con el cambio |
|---|---|---|
| ninguno trae sufijo propio; el de la operación es `AA(MARCA-X)-` | el aviso nombra `«AA(MARCA X)-»`, lo que va al TXT | nombra `«AA(MARCA-X)-»`, que no es lo que va al TXT |
| uno trae `AA(MARCA X)-` y dos heredan `AA(MARCA-X)-` | avisa que llevan el mismo | no avisa |
| el de la operación no se puede separar (`TEXTO LIBRE`) | no avisa (lo dice el error) | avisa «llevan el mismo sufijo» además del error |

Es un aviso: el TXT no cambia en ninguno de los tres.

- **(a)** Pieza chica, después de `guardar2.sh` y de D249: esos tres datos
  en el caso del aviso de `tests/test_maria8_subitems_por_posicion.py` y un
  sabotaje más en `scripts/testing/sabotaje_maria8.sh`. Los dos son míos.
- **(b)** No se hace: una línea en `COLA-LIMPIEZA.md`.

**Recomiendo (a):** es barato y el aviso le muestra al despachante un texto
que tiene que coincidir con el del TXT. Severidad baja: si decidís (b), no
se rompe nada de lo que sale.

Sin supuestos: no agregué nada que la tarea no pida.

## Lo que cambió

```diff
 # 6. el sufijo de la operación sale sin limpiar
-reemplazar $F 'sufijo_sbt = limpiar_sufijo((sbt_sufijo_valor or "").strip(), " de la operación")[0]' 'sufijo_sbt = (sbt_sufijo_valor or "").strip()'
+reemplazar $F 'return limpiar_sufijo((sbt_sufijo_valor or "").strip(), " de la operación")[0]' 'return (sbt_sufijo_valor or "").strip()'
 caso "sufijo_sucio" "FAILED $T::test_dentro_del_sufijo_solo_letras_numeros_y_espacios"
```

Por qué se había perdido: `dfa636f` (devolución de MARIA-7) escribió la
limpieza como una asignación, `sufijo_sbt = limpiar_sufijo(...)`. `4ab6a9b`
(MARIA-9) la mudó a una función interna, `sufijo_de_la_operacion()`
(`maria_generator.py:1520`), que hace `return limpiar_sufijo(...)` (`:1523`)
y a la que llaman el ítem entero (`:1726`), el renglón (`:1701`) y el
sub-ítem (`:1799`). El guion cortaba en el caso 6 y los 19 de después no
corrían.

Antes de reescribir comprobé que la protección sigue existiendo (D195 (a)):
no hay sabotaje para retirar. El ancla nueva es código, está una vez en
`maria_generator.py` y saca lo mismo que sacaba la vieja: la limpieza del
sufijo de la operación.

## Resultado

| qué | antes, guion de `f3a7d29` | ahora, `4477ae3` |
|---|---|---|
| el guion | `VERDE` (123 passed), 5 `ROJO` y corta: `PATRON NO ENCONTRADO (0 veces)`; `rc=1` | `VERDE` (123 passed), 25 `ROJO`, 0 `FALLA`, `OK: los 25 sabotajes dan rojo por la razón esperada`; `rc=0` |
| caso 6, `sufijo_sucio` | no corría | `ROJO … 1 failed, 122 passed` |
| mi línea en `sabotajes-conocidos.txt` | estaba | no está; queda 1 `vencido` (`guardar2.sh`) |

La mutación del caso 6 medida a mano, en un worktree descartable, con los
cuatro `tests/test_maria7_*.py` del guion: `1 failed, 122 passed`. Sólo
`test_dentro_del_sufijo_solo_letras_numeros_y_espacios`, por aserción:

```
At index 0 diff: 'AA(MARCA)-AI(620G-GREY.008 150CMX50M)-' != 'AA(MARCA)-AI(620G GREY 008 150CMX50M)-'
```

Los casos 7 a 25 no corrían desde `4ab6a9b`. Ahora corrieron los 19 y dieron
rojo nombrando su prueba; no medí a mano cada uno (no cambiaron).

## Revisión adversarial

Pieza chica de arnés: un adversario Sonnet, esfuerzo medio, sobre `4477ae3`,
en un worktree propio que retiró al terminar.

**Defectos del diff: ninguno.** Confirmó el ancla (código, una vez, mutación
mínima), el rojo del caso 6 (`1 failed, 122 passed`) y que la prueba
distingue la limpieza: el producto de la prueba no trae sufijo propio.

Dijo que había cuatro huecos vecinos «que nadie prueba». Corrió sólo los
cuatro archivos del guion; yo medí cada uno con los 27 archivos de `tests/`
que usan `sbt_sufijo_valor` (sin mutación: `1126 passed, 2 xfailed`):

| lo que dijo | su medición | la mía | queda |
|---|---|---|---|
| el renglón hereda el de la operación sin limpiar (`:1701`) | `123 passed` | `4 failed`: uno de `test_maria8_subitems_por_posicion.py` y tres de `test_maria9_sufijo_operacion.py` | no es un hueco |
| ídem el sub-ítem (`:1799`) | `123 passed` | `4 failed`, los cuatro en `test_maria9_sufijo_operacion.py` | no es un hueco |
| el aviso que anticipa el error (`:2219`) cambiado por `pass` | `123 passed` | `7 failed`: uno de `test_maria7_devolucion.py` y seis de `test_maria9_sufijo_operacion.py` | no es un hueco |
| la comparación del aviso «mismo sufijo» (`:2235`) sin limpiar | `123 passed` | `1126 passed, 2 xfailed` | **sí: D250** |

Otras dos cosas de su informe:

- Vio un worktree `sabotaje-maria7` parado en `f3a7d29` y lo tomó por un
  resto de un `trap` que no limpió. Era yo, corriendo en ese momento el
  guion de la base para el bloque de comandos. Al terminar,
  `git worktree list` da el mío y el tuyo de `/tmp/cdi-pm`.
- Contó 26 casos: `grep -c '^caso'` cuenta también la definición de la
  función. Son 25.

No corrí `/code-review`: el SHA que se entrega pasó por el adversario, que es
una de las dos que pediste.

## Comandos

```bash
VENV=/ruta/a/tu/venv
git diff f3a7d29 4477ae3 --stat -- scripts docs/pm/herramientas | tail -1    # 2 files changed, 1 insertion(+), 2 deletions(-)
scripts/testing/sabotaje_maria7.sh 4477ae3 $VENV | tail -1; echo ${PIPESTATUS[0]}
#   OK: los 25 sabotajes dan rojo por la razón esperada
#   0
grep -c sabotaje_maria7 docs/pm/herramientas/sabotajes-conocidos.txt    # 0
grep -c '^vencido' docs/pm/herramientas/sabotajes-conocidos.txt         # 1

# el rojo sin el arreglo: el guion de la base
git show f3a7d29:scripts/testing/sabotaje_maria7.sh > /tmp/m7_base.sh
bash /tmp/m7_base.sh f3a7d29 $VENV 2>&1 | tail -2; echo ${PIPESTATUS[0]}
#   ROJO   kilos_es_cantidad: … 7 failed, 116 passed …
#   PATRON NO ENCONTRADO (0 veces) en proyecto_maria/core/maria_generator.py: 'sufijo_sbt = limpiar_sufijo((sbt_sufijo_valor or "").strip(), " de la operación")[0]'
#   1

# D250: la mutación que queda verde
git worktree add -q --detach /tmp/d250 4477ae3 && cd /tmp/d250
$VENV/bin/python - <<'PY'
p = "proyecto_maria/core/maria_generator.py"
s = open(p, encoding="utf-8").read()
v = '                or limpiar_sufijo(str(sbt_sufijo_valor or "").strip())[0]\n'
assert s.count(v) == 1
open(p, "w", encoding="utf-8").write(s.replace(v, '                or str(sbt_sufijo_valor or "").strip()\n'))
PY
DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
  DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares $VENV/bin/python -m pytest -q --no-cov -p no:cacheprovider --timeout=120 \
  $(grep -l sbt_sufijo_valor tests/*.py) | tail -1    # 1126 passed, 2 xfailed
cd - >/dev/null; git worktree remove --force /tmp/d250
```

Corrí cada uno una vez, con la salida a un archivo; esas son sus líneas. El
guion nuevo lo corrí con `HEAD` parado en `4477ae3` y la salida entera; el de
la base, desde una copia en mi carpeta de trabajo, no en `/tmp`. El bloque
de D250 lo corrí como está escrito, con el worktree en mi carpeta de trabajo
en lugar de `/tmp/d250`: `1126 passed, 2 xfailed`, `rc=0`.

## Puertas

Sobre `4477ae3`, árbol limpio.

| puerta | salida |
|---|---|
| `sabotaje_maria7.sh 4477ae3` | `VERDE`, 25 `ROJO`, 0 `FALLA`; `rc=0` |
| `tests/test_anclas_perdidas.py` | `27 passed` |
| `anclas_perdidas.py 4477ae3` | `103 guiones, 2493 anclas medidas y 11 llamadas sin medir`; `perdida, una línea 1 guiones: 1` (`guardar2.sh:74`), `perdida, varias líneas 0`, `otra cantidad 0`; `rc=0` |
| `chequeo-6.py f3a7d29 4477ae3` | abajo, `avisos: 0` |
| `bash -n scripts/testing/sabotaje_maria7.sh` | sin errores |

**No corrido:** la suite entera (cambió un guion, ningún producto ni prueba),
`compileall`, las pantallas (`pantalla_maria7.js` es de la Técnica),
`e2e_maria.sh`, `smoke_friccion.sh`, `ataque_aislamiento.sh`, Postgres, los
demás guiones de sabotaje, `/code-review` y `/security-review` (el diff no
toca producto). Después del merge de tu rama (`f433601`, sólo `docs/pm/`) no
volví a correr nada: no cambia ni el guion ni el producto.

## `chequeo-6`

```
chequeo-6 f3a7d29..4477ae3: avisos para mirar, no un veredicto
producto +0/−0
arnés +1/−1
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

1. **Tres anclas del guion llevan un comentario adentro** (previas, no las
   toqué): el caso 16 (`# «26/08/07»`), el 24 (`break  # «2015-02-30»`) y el
   25 (`# %Y no rellena`). La regla dice que el ancla es código. Si alguien
   edita esos comentarios, el guion corta con `PATRON NO ENCONTRADO`: hace
   ruido, no queda verde en silencio. Severidad baja.
2. **El `25` del último `echo` está escrito a mano.** Hoy coincide: 25
   líneas `ROJO`. Previo.
3. **El venv por defecto del guion es `/tmp/cdi-dev2/venv`**, que no existe
   en una máquina nueva: hay que pasarlo como segundo argumento. Previo.
4. **D250**, arriba: un hueco de pruebas en un aviso, fuera de este guion.

## Líneas para `COLA-LIMPIEZA.md`

- `scripts/testing/sabotaje_maria7.sh`: las anclas de los casos 16, 24 y 25
  incluyen un comentario del producto; el `25` del último `echo` está escrito
  a mano; el venv por defecto es una ruta de otra máquina.

## Archivos de producto que toqué

Ninguno.

## Sigo con

El último vencido, `scripts/testing/sabotajes/guardar2.sh` (1 ancla que no
está, la de la línea 74, en `main.py`). Primero miro si la protección sigue
existiendo.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `671c759`). Aceptadas: CUIT-GENERAR sobre `29327d2`, SABOTAJE-SUBITEMS1 sobre `bf6778e`, D243 (b) sobre `0dff850`, SABOTAJE-SUFIJOS1 sobre `afeae84`, D245 (a) sobre `e17c11e`, D246 (b) sobre `0224f01`, SABOTAJE-MARIA8 sobre `50320ff`, D247 (a) sobre `4a58c68`, D248 (c) sobre `3fcc9c4`, los vencidos `sabotaje_maria1d.sh` sobre `6e4e658`, `sabotaje_maria5.sh` sobre `c0505cc`, `sabotaje_valor1b.sh` sobre `70eb5dc` y `sabotaje_doc1.py` sobre `d4c6b73`. Entregada sin veredicto: **el vencido `sabotaje_maria7.sh` sobre `4477ae3`** (base `f3a7d29`; sólo el ancla del caso 6, que ahora es el `return limpiar_sufijo(…)[0]` de `sufijo_de_la_operacion()` en `maria_generator.py:1523`, y mi línea fuera de `sabotajes-conocidos.txt`; arnés +1/−1; 25 `ROJO`, `rc=0`; a mano, 1 failed y 122 passed, sólo su prueba; un adversario Sonnet medio revisó `4477ae3`, sin defectos del diff; **D250 abierta**: el aviso «llevan el mismo sufijo» de `maria_generator.py:2235` sin limpiar el de la operación deja verdes los 27 archivos que usan `sbt_sufijo_valor`; recomendé (a), datos en `test_maria8_subitems_por_posicion.py` y un sabotaje en `sabotaje_maria8.sh`, después de guardar2 y D249). Si vuelve con devolución, va primero. **Pieza activa: el vencido `scripts/testing/sabotajes/guardar2.sh`** (1 ancla que no está, línea 74, en `main.py`: `or del_proveedor["producto_key"] != catalog_svc._normalize(recordado.get("descripcion") or "")):`; primero se mira si la protección sigue existiendo); al arreglarlo saco mi línea de `docs/pm/herramientas/sabotajes-conocidos.txt`, que es la última `vencido`. Después **D249 (a)**, decidida por la PM: sólo `tests/test_sufijos2.py` y `scripts/testing/sabotajes/sufijos2.sh`, criterio entero en `docs/pm/PARA-DEV-2.md`, sección D247 (la familia de fragmentos «…» de `limpiar_sufijo`, un sabotaje por cambio, `sufijos2.sh` entero en `ROJO` con la cuenta exacta, `sabotaje_sufijos1.sh` en 46, anclas que no empeoran: el criterio dice 5 y 1 y hoy son 1 y 0). D244, D239 y «Holanda» esperan a Emi: no se tocan. Próxima D: D251. Lecciones: antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada; un dato nuevo de un caso no reusa un valor que otro control del mismo caso espera; antes de escribir el informe se trae la rama de la PM; antes de sacar una prueba por duplicada se compara lo que afirma cada una, no sólo sus entradas; antes de reescribir un sabotaje con el ancla perdida se mira si la protección que atacaba sigue existiendo: si no, es una D (D195 (a)); al ajustar una afirmación, la nueva tiene que seguir afirmando todo lo que afirmaba la vieja (el orden también), y una mutación que «mueve» una frase la tiene que sacar de donde estaba; una medición corre sobre el conjunto más angosto de pruebas que contesta la pregunta; antes de cambiar un número que la PM fijó como criterio se lee por qué lo fijó; un comentario o un mensaje de commit no afirma lo que el guion no obliga, y su porqué se comprueba con `git show`, no se supone; que «nadie cubría» algo se mide antes de escribirlo, y con todas las pruebas que usan ese dato, no sólo las del guion (un adversario que corre cuatro archivos dice «hueco» donde otra prueba lo atrapa); `anclas_perdidas.py` mide un commit: el arreglo se commitea antes de medir; el SHA que se entrega pasa por subagente o `/code-review`, y si el gancho de parada ya subió el commit, lo que siga va en un commit nuevo; después de un commit nuevo o de corregir uno, las puertas corren otra vez sobre ese SHA; un ancla lleva sólo el texto que saca más lo mínimo que la ata a su lugar; la cuenta escrita a mano en el último `echo` de un guion se compara con sus líneas `ROJO`; una mutación se mide a mano con el archivo de pruebas entero, para ver que pone en rojo sólo lo suyo y por aserción; `anclas_perdidas.py` sólo lee los `.sh`; un worktree que aparece en `git worktree list` mientras corre un guion mío es de ese guion, no un resto; regla de la PM: en un vencido de sólo arnés, un último commit que cambia únicamente comentarios no necesita revisor si el informe lo dice, cualquier otro cambio sí. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que una D autoriza; subagentes hasta esfuerzo alto y sin consejero.
