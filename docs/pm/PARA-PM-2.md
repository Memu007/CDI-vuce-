# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D249 (a): entregada en `50dabfa`. `sufijos2.sh` da 49 de 49 en `ROJO`, `sabotaje_sufijos1.sh` sigue en 46. Nada para decidir

| qué | SHA |
|---|---|
| base (informe de `guardar2.sh`) | `279a685` |
| pruebas: 7 casos nuevos en `tests/test_sufijos2.py` y 15 sabotajes en `sufijos2.sh` | `de69dc4` |
| pruebas: un dato cambiado y un sabotaje más, por el hallazgo del revisor. **Lo que se entrega** | `50dabfa` |
| tu rama (`725c083`: guardar2 aceptado), sólo `docs/pm/` | `86131b7` |
| informe | el commit siguiente |

`producto +0/−0`. `arnés +83/−0`: `tests/test_sufijos2.py` (+31) y
`scripts/testing/sabotajes/sufijos2.sh` (+52). No toqué ningún otro archivo.

El SHA que entrego pasó por un adversario, dos veces (abajo).

Las mediciones son sobre `50dabfa`. Tu rama entró después y no toca ninguno
de los dos archivos.

## Decisiones

Nada para decidir.

**Supuestos reversibles** (agregué sin que lo pidas; si sobran, se sacan):

1. Seis sabotajes además de tus diez, de la misma familia. Cinco los
   hicieron visibles los datos largos: «pide» sin recorte, «cambiaría» con
   `en «{sufijo[pos:pos + 40]}»`, «cambiaría» con el código sin recorte,
   «no se puede separar» sin recorte y el aviso sin recorte. El sexto es el
   del revisor: `«{cambiaria[:20]}»` por `«{valor[:20]}»`.
2. El dato `pide` repite el sufijo de un dato que ya estaba
   (`AA(X)-ZB(16.384)-CA00-`) con el texto exacto entre «». Lo dejé porque
   es el único corto que distingue `sufijo[pos:pos + 40]`.

## Qué hay ahora

Un caso, `test_el_error_nombra_el_codigo_que_falla_y_lo_corta`, con seis
datos (sufijo → lo que el error muestra entre «»), y
`test_el_aviso_corta_el_sufijo_que_muestra`. Los datos largos pasan de 40,
de 20 y de 80 letras para que el recorte se vea. `tests/test_sufijos2.py`
pasa de 110 a 117 pruebas; `sufijos2.sh`, de 33 a 49 sabotajes.

| tu cambio | sabotaje en `sufijos2.sh` | prueba que da rojo |
|---|---|---|
| «pide» con `«{sufijo[:40]}»` | el error de los decimales nombra el sufijo entero y no el código | `[pide]`, `[pide_largo]` y la que ya lo veía, `…no_acepta_decimales[AA(X)-ZB(16.384)-CA00-]` |
| «pide» con `«{sufijo[pos:pos + 40]}»` | … nombra también lo que sigue al código | `[pide]` |
| «cambiaría» con `en «{sufijo[:40]}»` | el error del número que cambiaría nombra el sufijo entero y no el código | `[cambiaria]`, `[cambiaria_largo]` |
| `«{cambiaria[:20]}»` por `«{cambiaria}»` | el número que cambiaría sale sin cortar | `[cambiaria_largo]` |
| `«{cambiaria[:20]}»` por `«{sufijo[:20]}»` | en lugar del número que cambiaría sale el principio del sufijo | `[cambiaria]`, `[cambiaria_largo]` |
| «está vacío» sin recorte | el error del vacío nombra el código sin cortarlo | `[vacio_largo]` |
| «cerca de» con `sufijo[:20]` | «cerca de» muestra el principio del sufijo y no dónde se trabó | `[no_se_separa_largo]` |
| «cerca de» con `sufijo[pos:]` | «cerca de» muestra todo lo que sigue, sin cortar | `[no_se_separa_largo]` |
| «no se puede separar» con `sufijo[:10]` | el sufijo que no se separa sale cortado en 10 | `[no_se_separa_largo]` |
| el aviso con `limpio[:10]` | el aviso muestra el sufijo cortado en 10 | `test_el_aviso_corta_el_sufijo_que_muestra` |

Los seis míos: «… nombra el código sin cortarlo» (pide y cambiaría),
«el error del número que cambiaría nombra también lo que sigue al código»,
«en lugar del número que cambiaría sale el principio del valor», «el sufijo
que no se separa sale sin cortar» y «el aviso muestra el sufijo sin cortar».
Cada ancla es código y está una vez en `maria_generator.py`.

## La base, medida

Cada cambio solo, sobre `279a685` (producto y las dos pruebas iguales a
`4a58c68`: `git diff 4a58c68 279a685 -- proyecto_maria/ tests/test_sufijos1.py tests/test_sufijos2.py`
da vacío), con los 8 archivos de `tests/` que miran estos textos (sin
cambio: `425 passed`):

| cambio | en la base |
|---|---|
| pide `sufijo[pos:pos + 40]`, en `sufijo[:40]`, `«{cambiaria}»`, `«{sufijo[:20]}»`, vacío sin recorte, cerca `sufijo[pos:]` | `425 passed` cada uno |
| pide `sufijo[:40]` | `1 failed`: `test_sufijos2.py::test_un_sufijo_que_pide_numero_no_acepta_decimales[AA(X)-ZB(16.384)-CA00-]` (el dato único que dijiste) |
| cerca `sufijo[:20]` | `1 failed`: `test_maria9_bordes.py::test_un_codigo_numerico_tiene_dos_cifras_y_no_tres` |
| separar `sufijo[:10]` | `1 failed`: `test_maria7_devolucion.py::test_el_aviso_dice_que_se_separo_y_no_rompe_con_un_sufijo_malo` |
| aviso `limpio[:10]` | `3 failed`: esa, `test_maria7_rechazos_24_10.py::test_lo_que_se_cambia_en_el_sufijo_se_avisa` y `test_maria8_subitems_por_posicion.py::test_los_avisos_dicen_si_se_limpio_el_sufijo_de_un_renglon` |

O sea: «nadie distingue» vale para las dos pruebas del criterio, que es lo
que pedías. Tres de los siete ya los veía otro archivo. No cambia nada de
la entrega; lo digo para que el acta no diga más de lo medido. Que esos
tres queden verdes con sólo las dos pruebas lo deduzco de dónde están los
rojos, no lo corrí aparte.

## Revisión adversarial

Pieza chica de arnés: un adversario Sonnet, esfuerzo medio, en worktrees
propios que retiró.

**Primera pasada, sobre `de69dc4`:** 52 cambios al producto, 9 en verde.

| cambio que le quedó verde | lo medí | queda |
|---|---|---|
| `«{cambiaria[:20]}»` por `«{valor[:20]}»` | `117 passed` en `de69dc4`: cierto. Mi dato era `AF(-2.5)` y el número estaba al principio del valor | **arreglado en `50dabfa`**: el dato pasa a `AJ(ROLLO 1.500 M)` → `«1.500»`, y tiene su sabotaje |
| `cambiaria[:20].upper()` | no | previo: `.upper()` lo dejaste afuera de D249 |
| `.strip()` en cada fragmento (6) | no | equivalentes con estos datos: riesgo 1 |
| `sufijo[pos:][:20]` | no | es lo mismo que `sufijo[pos:pos + 20]` |

Confirmó las cuentas de los datos largos (37, 20, 70 y 17) y que las anclas
están una vez.

**Segunda pasada, sobre `50dabfa`:** 13 cambios de la parte «cambiaría», 0
en verde. `valor[:20]` da `1 failed, 116 passed` en `[cambiaria]`. Las seis
que antes daban rojo por el dato viejo siguen en rojo. Dos de las 13 no
cuentan (una es un `NameError`). No corrió el guion de sabotajes: los 49
`ROJO` son míos.

A mano, sobre `de69dc4`, los cortes corridos en uno (`[:41]`, `[:39]`,
`[:21]`, `[:19]`, `[:81]`, `[:79]`, `pos + 21`): 10 cambios, cada uno
`1 failed, 116 passed`. No los repetí en `50dabfa`: el dato que cambió no es
ninguno de los largos.

No corrí `/code-review`: el SHA que se entrega pasó por el adversario.

## Comandos

```bash
PY=/ruta/a/tu/venv/bin/python
git diff 279a685 50dabfa --stat | tail -1    # 2 files changed, 83 insertions(+)
env -u DATABASE_URL -u ENVIRONMENT PY=$PY scripts/testing/sabotajes/sufijos2.sh 50dabfa > s2.log 2>&1; echo $?   # 0
grep -c '^ROJO' s2.log                        # 49
grep -E '^BASE|sin rojo' s2.log
#   BASE  | … 117 passed …
#   sabotajes sin rojo: 0
env -u DATABASE_URL -u ENVIRONMENT scripts/testing/sabotaje_sufijos1.sh 50dabfa /ruta/a/tu/venv > s1.log 2>&1; echo $?   # 0
grep -c '^ROJO' s1.log; tail -1 s1.log
#   46
#   OK: los 46 sabotajes dan rojo por la razón esperada
$PY scripts/testing/anclas_perdidas.py 50dabfa | sed -n 2,4p
#   perdida, una línea          0   guiones: 0
#   perdida, varias líneas      0   guiones: 0
#   otra cantidad               0   guiones: 0
```

Corrí cada guion una vez con `HEAD` en `50dabfa` y la salida entera a un
archivo; los `grep`, `tail` y `sed` de arriba no los corrí así: leí esas
líneas del archivo. `sabotaje_sufijos1.sh` recibe el venv como segundo
argumento y no por `PY`; la primera vez lo llamé mal y cortó con
`rc=127` antes de correr nada (`/tmp/cdi-dev2/venv/bin/python: No such file
or directory`): error mío de llamada, no un rojo.

## Puertas

Sobre `50dabfa`, árbol limpio.

| puerta | salida |
|---|---|
| `sabotajes/sufijos2.sh 50dabfa` | `BASE … 117 passed`; 49 `ROJO`; `sabotajes sin rojo: 0`; `rc=0` |
| `sabotaje_sufijos1.sh 50dabfa` | 46 `ROJO`; «OK: los 46 sabotajes dan rojo por la razón esperada»; `rc=0` |
| `tests/test_sufijos1.py tests/test_sufijos2.py` | `178 passed` |
| `anclas_perdidas.py 50dabfa` | `103 guiones, 2509 anclas medidas y 11 llamadas sin medir`; 0, 0 y 0; `rc=0`. Contra `279a685` sólo cambia 2493 → 2509 |
| `chequeo-6.py 279a685 50dabfa` | abajo, `avisos: 0` |
| `bash -n scripts/testing/sabotajes/sufijos2.sh` | sin errores |

**No corrido:** la suite entera (no cambió producto), `compileall`, las
pantallas, `e2e_maria.sh`, `smoke_friccion.sh`, `ataque_aislamiento.sh`,
Postgres, los demás guiones de sabotaje, `/code-review` y
`/security-review` (el diff no toca producto).

## `chequeo-6`

```
chequeo-6 279a685..50dabfa: avisos para mirar, no un veredicto
producto +0/−0
arnés +83/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

1. **Ningún dato tiene espacios en los bordes de lo que se muestra**: un
   `.strip()` de más o de menos en esos fragmentos no lo ve nadie. Bajo: no
   cambia qué código nombra el error.
2. **El camino donde el número que cambiaría sale de alrededor del valor**
   (el caso `AF(-2.5)`) ya no tiene texto exacto: queda sólo bajo la prueba
   que ya estaba, que mira con comodín. Bajo; si lo querés fijo, es un dato
   más en el mismo caso.
3. **`.upper()` y el texto de la instrucción**: previos, los dejaste afuera.

## Archivos de producto que toqué

Ninguno.

## Sigo con

D250 (a): `tests/test_maria8_subitems_por_posicion.py` y
`scripts/testing/sabotaje_maria8.sh`, con tu criterio. D244, D239 y
«Holanda» esperan a Emi.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `725c083`). Aceptadas: CUIT-GENERAR sobre `29327d2`, SABOTAJE-SUBITEMS1 sobre `bf6778e`, D243 (b) sobre `0dff850`, SABOTAJE-SUFIJOS1 sobre `afeae84`, D245 (a) sobre `e17c11e`, D246 (b) sobre `0224f01`, SABOTAJE-MARIA8 sobre `50320ff`, D247 (a) sobre `4a58c68`, D248 (c) sobre `3fcc9c4`, los vencidos `sabotaje_maria1d.sh` sobre `6e4e658`, `sabotaje_maria5.sh` sobre `c0505cc`, `sabotaje_valor1b.sh` sobre `70eb5dc`, `sabotaje_doc1.py` sobre `d4c6b73` `sabotaje_maria7.sh` sobre `4477ae3` y `sabotajes/guardar2.sh` sobre `aeb994f` (no queda ningún vencido). Entregada sin veredicto: **D249 (a) sobre `50dabfa`** (base `279a685`; sólo `tests/test_sufijos2.py`, de 110 a 117 pruebas, y `scripts/testing/sabotajes/sufijos2.sh`, de 33 a 49 sabotajes; arnés +83/−0; `sufijos2.sh` 49 `ROJO`, `sabotaje_sufijos1.sh` 46, las dos pruebas `178 passed`, anclas 0, 0 y 0; un adversario Sonnet medio revisó `de69dc4` y `50dabfa`; su hallazgo, `valor[:20]`, quedó arreglado). Si vuelve con devolución, va primero. **Pieza activa: D250 (a).** **D250 (a)**, decidida por la PM, criterio en `PARA-DEV-2.md`: la familia de entradas del aviso «los N sub-ítems llevan el mismo sufijo» como datos de un solo caso de `tests/test_maria8_subitems_por_posicion.py` (el texto que muestra, cuándo sale y cuándo no); mi sabotaje de `maria_generator.py:2235` (`limpiar_sufijo(str(sbt_sufijo_valor or "").strip())[0]` por `str(sbt_sufijo_valor or "").strip()`) en `sabotaje_maria8.sh` da `ROJO` con una prueba nombrada; `sabotaje_maria8.sh` entero en `ROJO` con la cuenta exacta; las anclas no empeoran. D244, D239 y «Holanda» esperan a Emi: no se tocan. Próxima D: D251. Lecciones: antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada; un dato nuevo de un caso no reusa un valor que otro control del mismo caso espera; antes de escribir el informe se trae la rama de la PM; antes de sacar una prueba por duplicada se compara lo que afirma cada una, no sólo sus entradas; antes de reescribir un sabotaje con el ancla perdida se mira si la protección que atacaba sigue existiendo: si no, es una D (D195 (a)); al ajustar una afirmación, la nueva tiene que seguir afirmando todo lo que afirmaba la vieja (el orden también), y una mutación que «mueve» una frase la tiene que sacar de donde estaba; una medición corre sobre el conjunto más angosto de pruebas que contesta la pregunta; antes de cambiar un número que la PM fijó como criterio se lee por qué lo fijó; un comentario o un mensaje de commit no afirma lo que el guion no obliga, y su porqué se comprueba con `git show`, no se supone; que «nadie cubría» algo se mide antes de escribirlo, y con todas las pruebas que usan ese dato, no sólo las del guion (un adversario que corre cuatro archivos dice «hueco» donde otra prueba lo atrapa); `anclas_perdidas.py` mide un commit: el arreglo se commitea antes de medir; el SHA que se entrega pasa por subagente o `/code-review`, y si el gancho de parada ya subió el commit, lo que siga va en un commit nuevo; después de un commit nuevo o de corregir uno, las puertas corren otra vez sobre ese SHA; un ancla lleva sólo el texto que saca más lo mínimo que la ata a su lugar; la cuenta escrita a mano en el último `echo` de un guion se compara con sus líneas `ROJO`; una mutación se mide a mano con el archivo de pruebas entero, para ver que pone en rojo sólo lo suyo y por aserción; `anclas_perdidas.py` sólo lee los `.sh`; un worktree que aparece en `git worktree list` mientras corre un guion mío es de ese guion, no un resto; una espera de 110 vueltas de 5 s no alcanza para tres corridas de 4 minutos: se vuelve a esperar la marca de fin, no se relanza; mientras haya una D mía sin contestar, el informe siguiente la repite arriba; el dato que fija «qué pedazo se muestra» no tiene ese pedazo al principio de donde sale, o cortar el todo da lo mismo; `sabotaje_sufijos1.sh` recibe el venv como segundo argumento, no por `PY`; regla de la PM: en un vencido de sólo arnés, un último commit que cambia únicamente comentarios no necesita revisor si el informe lo dice, cualquier otro cambio sí. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que una D autoriza; subagentes hasta esfuerzo alto y sin consejero.
