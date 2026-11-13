# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D199 y `sabotaje_valor1.sh`: entregados en `fe0f1b4` (sólo arnés). D199 cerrada; en `valor1` queda verde el 24 y va como D222

| qué | SHA |
|---|---|
| base (mi entrega anterior) | `0609e14` |
| `valor1`: los cinco sabotajes perdidos, sobre el código de hoy | `38ee8e1` |
| `valor1`: su línea de `sabotajes-conocidos.txt`, con el motivo de hoy | `a625d11` |
| tu cabeza `2de2396`, integrada con `merge` | `6c87747` |
| D199: el sabotaje pasa de `catalogo_largo2.sh` a `catalogo3.sh` | `5eb1540` |
| D199: sale la línea de `catalogo_largo2` de `sabotajes-conocidos.txt` | `a2ec4bc` |
| tu cabeza `08ae965`, integrada con `merge`: **el que se entrega** | `fe0f1b4` |
| informe | el commit siguiente |

**Resultado.** Producto: **+0/−0** en las dos.

- **D199.** La mutación `NFD`→`NFKD` de `_normalize` está ahora en
  `catalogo3.sh`, que corre `tests/test_catalogo3.py`, y espera el id del
  proveedor «Industrias García Nº1». `catalogo3.sh` entero: 51
  `ROJO`, `fallas: 0`, sale 0. `catalogo_largo2.sh` entero con Postgres 16:
  37 `ROJO`, `fallas: 0`, sale 0. Su línea salió de `sabotajes-conocidos.txt`.
- **`sabotaje_valor1.sh`.** Las cinco anclas perdidas (13, 15, 16, 29, 30)
  están otra vez sobre código que existe una sola vez. El guion entero da 30
  `ROJO` y una `FALLA`: el sabotaje 24, que no estaba entre los cinco, queda
  verde con su ancla presente (D222). Con el 24 salteado sólo en una copia
  local: 30 `ROJO`, sale 0. Su línea **sigue** en `sabotajes-conocidos.txt`,
  con el motivo de hoy, hasta que decidas D222.

`anclas_perdidas.py fe0f1b4` no da ninguna fila de los tres guiones.

## Decisiones

**D221. El sabotaje 13 de `valor1` cambió de sentido.** Antes decía «un
ajuste mal escrito viaja como texto (daría 422 al generar)» y cambiaba
`isFinite(n) ? n : null` por `: v`. Esa regla se invirtió a propósito: hoy
`ajusteDelPedido` manda tal cual lo que no se lee, para que el servidor lo
diga, y `test_el_pedido_manda_los_ajustes_y_nunca_algo_que_frene_el_txt`
espera `"mal escrito"` en el pedido. El sabotaje viejo no tiene qué atacar.
Lo reescribí con la regla de hoy: manda vacío lo que no se lee
(`r.error ? null : r.valor`). Rojo: `At index 4 diff: None != 'mal escrito'`.
Lo que encontró `/code-review` y comprobé leyendo: es **la misma mutación**
que la de `sabotaje_separadores1b.sh:102` (`return r.valor;`). En
`montos_ar.js` todo camino con error devuelve `valor: null`, así que las dos
dejan el producto igual; sólo cambia el caso que se espera en rojo.
- (a) Queda reescrito, como está. El caso de `test_valor1.py` conserva un
  sabotaje en su guion para la mitad «viaja tal cual».
- (b) Se retira (tres líneas menos). **Recomiendo (b)**: no distingue nada
  que el otro guion no distinga, y la misma línea del producto queda anclada
  en tres guiones (`valor1`, `separadores1`, `separadores1b`), que se vencen
  juntos. Ese caso de `test_valor1.py` sigue nombrado por el sabotaje 14.
No lo retiré yo: sacar un sabotaje lo decidís vos. Si elegís (b) y D222 (a),
van en la misma vuelta.

**D222. El sabotaje 24 de `valor1` (`mal_escrito_se_borra`) queda verde:
retirarlo.** Cambia `!ajusteMalEscrito(op.ajustes_incluir)) {` por `true) {`
en `pintarValor`. Con esa mutación: `75 passed`. Sacando también la guarda de
«a deducir»: `75 passed`.
Por qué: desde que el campo es de texto, `op.ajustes_incluir` guarda lo
escrito tal cual. Lo escriben sólo el propio campo y el botón del descuento
(que también escribe el campo), así que repintar pone lo mismo que ya está.
La guarda del producto no cambia nada que se vea.
- (a) Retirar el sabotaje 24 (tres líneas; el mensaje final pasa a 30).
  **Recomiendo (a)**. Y propongo una línea para la cola de limpieza: sacar
  las dos guardas `!ajusteMalEscrito(...)` de `pintarValor`
  (`finalize.js:451` y `:454`), que hoy no hacen nada.
- (b) Dejarlo y escribir un caso que lo distinga. No lo recomiendo: el único
  estado donde la guarda cambia algo es uno que la pantalla no produce (el
  ajuste mal escrito en la operación y otra cosa en el campo), y ahí la
  guarda deja el campo sin mostrar lo que el aviso dice que está mal.

**Para la cola de limpieza (la escribís vos; son propuestas):**
- `finalize.js`, `pintarValor`: sacar la guarda `!ajusteMalEscrito(...)` de
  las dos líneas que repintan los ajustes; no cambia nada que se vea (D222).
- `sabotaje_valor1.sh`: el sabotaje 10 está anclado en un comentario del
  producto (`// Ya usado como ajuste, no se vuelve a ofrecer.`, línea 108) y
  el ancla del 28 lleva un comentario al final de la línea (187). Ya estaban
  así; no los toqué.

## Supuestos (reversibles)

1. **D199: qué rojo espera.** De tus dos sugerencias tomé el id de
   proveedor: `FAILED …::test_un_proveedor_latino_conserva_su_id[Industrias Garc`.
   Es el daño que se ve: el `vendor_id` guardado deja de coincidir
   (`industrias_garcia_no1` en vez de `industrias_garcia_n_1`). El nombre del
   sabotaje pasó a `«Nº» en el nombre se lee «No» y el proveedor latino
   cambia de id`; el viejo («la clave junta ﬁ con fi») describía algo que el
   producto hace a propósito.
2. **D199: `test_acelerar_no_cambia_ninguna_clave`** también se pone roja con
   esa mutación (abajo), pero ningún guion la espera por nombre; ya era así.
   No sumé un segundo sabotaje: no es de §3 y el rojo queda mostrado una vez
   acá (§6).
3. **`valor1`, sabotaje 13**, reescrito con la regla de hoy (D221). Nombre
   nuevo: `ajuste_mal_escrito_vacio`.
4. **`valor1`, sabotaje 29.** `badInput` ya no existe: el campo es de texto.
   La marca de un ajuste mal escrito sale hoy de `pintarValor`, que arma el
   texto del error. La mutación saca esa línea para «a incluir». Nombre
   nuevo: `mal_escrito_sin_marca`. Espera el mismo caso que antes.
5. **`valor1`, sabotaje 15.** La línea de hoy borra dos marcas
   (`seguro_calculado` y `seguro_dejado`); la mutación saca sólo la primera,
   que es la que mira el caso.
6. En `valor1`, los sabotajes 13 y 14 esperan el mismo caso en rojo. Ya era
   así: `caso` comprueba qué caso falla, no con qué texto. El texto de cada
   rojo lo comprobé a mano (tabla de abajo).

## D199: el rojo a mano

Con `NFD`→`NFKD` en `_normalize`, sobre `6c87747`,
`tests/test_catalogo3.py`: `5 failed, 99 passed`.

```
FAILED tests/test_catalogo3.py::test_un_proveedor_latino_conserva_su_id[Industrias Garc\xeda N\xba1-industrias_garcia_n_1]
FAILED tests/test_catalogo3.py::test_un_proveedor_latino_conserva_su_id[Hermanos 1\xaa SA-hermanos_1_sa]
FAILED tests/test_catalogo3.py::test_lo_que_se_lee_igual_se_encuentra[Tornillo N\xba 8-Tornillo N\xb0 8-exact]
FAILED tests/test_catalogo3.py::test_lo_que_se_lee_igual_se_encuentra[Bolt™ M8-Bolt M8-exact]
FAILED tests/test_catalogo3.py::test_acelerar_no_cambia_ninguna_clave - Asser...
E   AssertionError: assert 'industrias_garcia_no1' == 'industrias_garcia_n_1'
E   AssertionError: assert 'hermanos_1a_sa' == 'hermanos_1_sa'
```

Son los cinco que nombraste. **Rojo antes del arreglo:** en tu acta y en mi
informe anterior, `catalogo_largo2.sh` sobre `204c638` daba
`VERDE | la clave junta ﬁ con fi: la prueba no lo vio`, `fallas: 1`, sale 1.

## `valor1`: qué cambió en cada sabotaje

| # | nombre | dónde está hoy la protección | rojo a mano sobre `38ee8e1` |
|---|---|---|---|
| 13 | `ajuste_mal_escrito_vacio` | `return r.error ? String(v).trim() : r.valor;` en `ajusteDelPedido` | 1 failed: `At index 4 diff: None != 'mal escrito'` |
| 15 | `seguro_a_mano_marcado` | `delete op.seguro_calculado; delete op.seguro_dejado;` en `onFieldChange` (`review.js`) | 1 failed: `Left contains 1 more item: {'seguro_calculado': True}` |
| 16 | `base_fija_en_la_cuenta` | `"fob_factura": fob_factura}[BASE_SEGURO_SUGERIDO]` en `cuentas_del_valor` | 1 failed: `assert (11.0 == 9.0)` |
| 29 | `mal_escrito_sin_marca` | `errores.push('Ajustes a incluir: ' + …)` en `pintarValor` | 1 failed: `assert '' == 'Ajustes a in...es un número.'` |
| 30 | `seguro_con_error` | `ultimoValor.error` en la primera línea de `calcularSeguro`, que ganó `seguro_en_el_precio` | 1 failed: `assert ('seguro_calculado' not in {'seguro_calculado': True})` |

## Para reproducir

```bash
# D199 (necesita node; unos 30 minutos)
PY=<venv>/bin/python bash scripts/testing/sabotajes/catalogo3.sh fe0f1b4
# 51 líneas ROJO, entre ellas
# «ROJO  | «Nº» en el nombre se lee «No» y el proveedor latino cambia de id: dice …[Industrias Garc»;
# fallas: 0; sale 0
# Postgres local y descartable; unos 22 minutos
PY=<venv>/bin/python scripts/testing/con_pg16.sh bash -c \
  'PG_URL="$BACKUP1A_PG_URL" bash scripts/testing/sabotajes/catalogo_largo2.sh fe0f1b4'
# 37 líneas ROJO; fallas: 0; sale 0

# valor1 (unos 14 minutos)
bash scripts/testing/sabotaje_valor1.sh fe0f1b4 <venv>
# 30 líneas ROJO; «FALLA  mal_escrito_se_borra: quedó verde»;
# «FALLAN 1 sabotajes»; sale 1

python scripts/testing/anclas_perdidas.py fe0f1b4 | grep -cE 'sabotaje_valor1\.sh|catalogo_largo2\.sh|catalogo3\.sh'
# 0
python docs/pm/herramientas/chequeo-6.py 0609e14 a625d11    # valor1
python docs/pm/herramientas/chequeo-6.py 6c87747 a2ec4bc    # D199
# los dos: producto +0/−0, avisos: 0
```

Yo corrí los dos guiones de catálogo sobre `5eb1540` y `valor1` sobre
`38ee8e1` (entero) y `a625d11` (con el 24 salteado), **no sobre `fe0f1b4`**.
De ahí a `fe0f1b4` no cambia nada de lo que esos guiones corren o mutan:

```bash
git diff a625d11 fe0f1b4 --stat -- proyecto_maria tests/conftest.py tests/test_valor1.py \
  scripts/testing/sabotaje_valor1.sh scripts/testing/sabotajes/_entorno_comun.sh
git diff 5eb1540 fe0f1b4 --stat -- proyecto_maria tests/conftest.py tests/test_catalogo3.py \
  tests/test_catalogo_largo2.py scripts/testing/sabotajes/catalogo3.sh \
  scripts/testing/sabotajes/catalogo_largo2.sh scripts/testing/catalogo3_postgres.py \
  scripts/testing/con_pg16.sh requirements.txt
# los dos: vacío
```

Lo que entra después de `5eb1540` es `sabotajes-conocidos.txt` y tu rama
(`abuso1.sh`, `abuso2.sh`, `datos1.sh`, `reset3.sh`, `test_abuso1.py`,
`test_datos1.py` y documentos).

La copia local de `valor1` con el 24 salteado no está en el repo. Es el guion
de `a625d11` con este cambio:

```diff
-reemplazar $JS '!ajusteMalEscrito(op.ajustes_incluir)) {' 'true) {'
-caso "mal_escrito_se_borra" "FAILED $T::test_un_numero_que_el_campo_no_entiende_queda_marcado_y_a_la_vista"
+echo "SALTEADO mal_escrito_se_borra"
-echo "OK: los 31 sabotajes dan rojo por la razón esperada"
+echo "OK: los 30 sabotajes corridos dan rojo por la razón esperada (1 salteado)"
```

## Puertas

| puerta | sobre | salida |
|---|---|---|
| `catalogo3.sh` entero (D199) | `5eb1540` | 51 `ROJO`, `fallas: 0`, `rc=0 segundos=1796`. La línea nueva: `ROJO  | «Nº» en el nombre se lee «No» y el proveedor latino cambia de id: dice «FAILED tests/test_catalogo3.py::test_un_proveedor_latino_conserva_su_id[Industrias Garc»` |
| `catalogo_largo2.sh` entero, Postgres 16 (D199) | `5eb1540` | 37 `ROJO`, `fallas: 0`, `rc=0 segundos=1323` |
| `sabotaje_valor1.sh` entero, commiteado | `38ee8e1` | 30 `ROJO`, `FALLA  mal_escrito_se_borra: quedó verde`, `rc=1 segundos=814` |
| `sabotaje_valor1.sh`, copia local con el 24 salteado | `a625d11` | 30 `ROJO`, `SALTEADO mal_escrito_se_borra`, `OK: los 30 sabotajes corridos dan rojo por la razón esperada (1 salteado)`, `rc=0 segundos=719` |
| `anclas_perdidas.py` | `fe0f1b4` | `rc=0`; filas de `sabotaje_valor1.sh`, `catalogo_largo2.sh` o `catalogo3.sh`: 0 |
| `chequeo-6.py 0609e14 a625d11` | `valor1` | `producto +0/−0`, `arnés +9/−11`, `avisos: 0` |
| `chequeo-6.py 6c87747 a2ec4bc` | D199 | `producto +0/−0`, `arnés +4/−4`, `avisos: 0` |

`chequeo-6` va por tramo, porque en el medio y al final está tu rama
(`6c87747` y `fe0f1b4` son uniones):

```
chequeo-6 0609e14..a625d11: avisos para mirar, no un veredicto
producto +0/−0
arnés +9/−11
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0

chequeo-6 6c87747..a2ec4bc: avisos para mirar, no un veredicto
producto +0/−0
arnés +4/−4
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

**`valor1`, rojo antes del arreglo:** el guion viejo sobre `0609e14` dio 12
`ROJO` y frenó en el 13: `PATRON NO ENCONTRADO (0 veces) en
proyecto_maria/static/v2/screens/finalize.js: '        return isFinite(n) ? n : null;'`,
`rc=1`.

**`valor1`, rojo que queda, diagnosticado (no repetí hasta verde):** el guion
entero sobre `38ee8e1` dio 30 `ROJO` y `FALLA  mal_escrito_se_borra: quedó
verde`, `rc=1`. Causa: D222. El ancla del 24 nunca se perdió; el guion viejo
frenaba en el 13 y no llegaba a correrlo.

## Hallazgos de la autorrevisión

| quién | pieza | hallazgo | severidad | qué hice |
|---|---|---|---|---|
| adversario (Sonnet, medio) | D199 | ninguno serio. Reprodujo la mutación (`5 failed, 99 passed`); no duplica al sabotaje de «º», «ª» y «µ» (ese muta `_sufijo`); el texto esperado `[Industrias Garc` es ASCII y sale igual con `LC_ALL=C` y `PYTHONIOENCODING=ascii`; `grep -qF` toma el `[` literal y un solo parámetro empieza así; en `catalogo_largo2.sh` no quedó nada colgado; ningún código lee `sabotajes-conocidos.txt` | — | sin cambios. **No corrió** los dos guiones enteros, ni `anclas_perdidas.py`, ni otras versiones de pytest, ni miró `test_catalogo_largo2.py` prueba por prueba |
| adversario (Sonnet, medio) | D199 | el nombre del sabotaje habla sólo de «Nº», y la mutación también rompe «1ª», `Bolt™` y `test_acelerar_no_cambia_ninguna_clave` | baja | no lo cambié: el texto esperado ancla justo el caso que dice el nombre (supuesto, arriba) |
| `/code-review high 6c87747..a2ec4bc` (revisores en Fable, permitido) | D199 | ninguno (`[]`). Corrió `catalogo3.sh a2ec4bc` entero: 51 `ROJO`, `fallas: 0`, sale 0. Por lectura: «ﬁ»→«fi» sigue cubierto por `tests/test_catalogo3.py:145` y `catalogo3.sh:102`; el sabotaje nuevo no duplica al de `_compatible` | — | sin cambios. **No corrió** `catalogo_largo2.sh`. Usó tu entorno `/tmp/cdi-pm/venv/bin/python` sólo para ejecutar (no se lo indiqué yo); después miré: nada nuevo en `/tmp/cdi-pm` fuera de `venv/lib`, y su árbol de trabajo sigue mostrando sólo `?? venv` |
| adversario (Sonnet, medio) | `valor1` | el 24 queda verde: el guion no da «31 en rojo» | alta | reproducido antes de que lo dijera (`75 passed` con la mutación); va como D222 |
| adversario (Sonnet, medio) | `valor1` | el 13 se solapa con `separadores1b.sh:102` | baja | confirmado; D221 |
| adversario (Sonnet, medio) | `valor1` | los otros dos `delete op.seguro_calculado` de `finalize.js` (362 y 429) no tienen mutación en este guion | media, por lectura | no es un hueco: el 362 lo muta `sabotaje_valor1c.sh:134`; el 429 lo saqué a mano y da `2 failed, 180 passed` en `test_seguro1.py::test_el_calculado_se_borra_al_pasar_a_cif_y_queda_para_completar`. No sumé nada |
| adversario (Sonnet, medio) | `valor1` | 13, 15, 16, 29 y 30: cada uno saca la protección que dice su comentario y da rojo por eso | — | sin cambios. Corrió el guion hasta el 24 y 29 y 30 a mano; **no vio del 25 al 28 ni el 31** (los cubre mi corrida entera) |
| `/code-review high` (revisores en Fable, permitido) | `valor1` | el 24 queda verde | alta | D222 |
| `/code-review high` | `valor1` | el 13 es la misma mutación que `separadores1b.sh:102` | media | confirmado leyendo `montos_ar.js`; cambió mi recomendación de D221 a (b) |
| `/code-review high` | `valor1` | el 29 saca sólo la línea de «a incluir»; la de «a deducir» no tiene sabotaje en ningún guion | baja | la saqué a mano: `1 failed, 74 passed`, `test_las_cuentas_se_ven_y_el_error_tambien`, `- Ajustes a deducir: no es un número. Ajustes a deducir: x` / `+ Ajustes a deducir: x`. No sumé un sabotaje: no es de §3 y el rojo queda mostrado acá una vez (§6). El 29 viejo tampoco lo distinguía |
| `/code-review high` | `valor1` | el 10 está anclado en un comentario y el 28 lleva uno en el ancla (ya estaban) | baja | propuesto para la cola, arriba |

`/security-review`: no corrido. Ninguna de las dos toca producto.

## Qué no corrí y riesgos

- La suite entera: no. Es arnés, producto +0/−0.
- Ningún otro guion vencido: van uno por pieza.
- `sabotaje_valor1.sh` commiteado **sale 1** hasta que decidas D222: quien lo
  corra entero ve una `FALLA`. Por eso su línea sigue en
  `sabotajes-conocidos.txt`. La copia con el 24 salteado no está en el repo:
  la armás con el diff de arriba.
- El adversario de `valor1` no llegó a ver los sabotajes 25 a 28 ni el 31
  (límite de tiempo de su entorno). No cambiaron en esta pieza y dan `ROJO`
  en mis dos corridas enteras.
- `catalogo_largo2.sh` entero, sin el sabotaje, lo corrí sólo yo (una vez,
  sobre `5eb1540`). `catalogo3.sh` entero tiene dos corridas: la mía sobre
  `5eb1540` y la del revisor sobre `a2ec4bc`.
- Ninguna corrida es sobre `fe0f1b4`: lo que lo separa de los SHAs corridos
  está en «Para reproducir», con los dos `git diff` vacíos. Sobre `fe0f1b4`
  corrí sólo `anclas_perdidas.py`.
- La mutación `NFD`→`NFKD` da rojo en cinco pruebas, pero el guion espera una
  sola por nombre. Si alguien saca el parámetro «Industrias García Nº1» de
  `test_un_proveedor_latino_conserva_su_id`, el guion escribe `ROJO? | …
  rojo, pero sin «…»`, suma una falla y sale 1 (no pasa callado; leído en
  `catalogo3.sh:49-53`, no corrido).
- El texto esperado termina en `Garc` para no depender de cómo pytest escribe
  la «í» en el id del parámetro. Otras versiones de pytest: no probadas.
- Un revisor de `/code-review` ejecutó con el Python de tu entorno
  (`/tmp/cdi-pm/venv`). No encontré nada escrito ahí, pero no puedo
  descartar un `.pyc` nuevo dentro de `venv/lib`.

Archivos de producto tocados: ninguno. Arnés:
`scripts/testing/sabotaje_valor1.sh`, `scripts/testing/sabotajes/catalogo3.sh`,
`scripts/testing/sabotajes/catalogo_largo2.sh` y
`docs/pm/herramientas/sabotajes-conocidos.txt` (sale la línea de
`catalogo_largo2`; la de `valor1`, con el motivo de hoy).

Sigo con D218 y D219, una pieza, como dice tu canal, salvo que llegue una
devolución o la tarea de comparación.

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn, cabeza 08ae965, ya integrada en fe0f1b4), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. Entregado en fe0f1b4 (informe en el commit siguiente), esperando veredicto, dos cosas en un informe: D199 (el sabotaje NFD→NFKD pasó de sabotajes/catalogo_largo2.sh a sabotajes/catalogo3.sh; los dos guiones salen 0 y la línea de catalogo_largo2 salió de herramientas/sabotajes-conocidos.txt) y el re-anclaje de sabotaje_valor1.sh (30 en rojo; el 24, «mal_escrito_se_borra», queda verde y está salteado sólo en una copia local: sale 0). Producto +0/−0. Abiertas, las decide la PM: D221 (el 13 de valor1 es la misma mutación que separadores1b.sh:102: recomiendo retirarlo), D222 (retirar el 24 de valor1; su línea queda en sabotajes-conocidos.txt hasta entonces). Ya decididas por la PM: D218 (a) y D219 (a), una pieza, la que arranco ahora (en D219, si uso en el comentario del caso que _migrate_catalogo_claves rearma los vendor_id largos, lo corro; si no, digo «leído»); D220 es riesgo para Emi, no tarea. Después, una pieza por guion vencido: maria8, maria1d, maria5, valor1b, doc1.py, maria7, guardar2; puerta de cada una: guion entero todo ROJO y sale 0, sin filas en anclas_perdidas.py, y sale su línea de sabotajes-conocidos.txt. Próxima D libre: D223. Una devolución de la PM o la tarea de comparación van primero. Los detalles están en PARA-PM-2.md: el resumen los cita, no los copia. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; las Devs no usan el consejero.
