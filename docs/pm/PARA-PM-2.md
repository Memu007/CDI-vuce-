# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D246 (b): entregada en `0224f01`. Salieron el caso 11 de `sabotaje_sufijos1.sh` y su prueba; tus cuatro criterios dan lo que pediste. Pero la prueba que saqué fijaba una cosa que `test_sufijos2.py` no fija: qué código nombra el error. Va como D247

| qué | SHA |
|---|---|
| base (informe de D245 (a)) | `a8d7f7b` |
| pruebas. **Lo que se entrega** | `0224f01` |
| informe | el commit siguiente |

`producto +0/−0`. `arnés +37/−49` en `scripts/testing/sabotaje_sufijos1.sh`
y `tests/test_sufijos1.py`; 36 de las líneas de cada lado son comentarios
renumerados (`# 12.`…`# 47.` pasan a `# 11.`…`# 46.`).

Tu rama no tiene nada nuevo desde `3195a8c`. D245 (a) sigue sin veredicto.

## Decisiones

**D247. El error «está vacío» ya no tiene quién mire qué código nombra.**

La prueba que saqué esperaba `del ítem 1: «AA\( \)» está vacío`: el mensaje
tiene que nombrar el código vacío y nada más. Las de `test_sufijos2.py` que
quedan esperan `«A[AB]\(.*está vacío`, que también acepta el sufijo entero.
Lo encontró `/code-review` y lo reproduje: cambiando en
`maria_generator.py:419` `«{uno[0][:40]}»` por `«{sufijo[:40]}»`, para
`AA(DEMO)-AB()-` el error diría «AA(DEMO)-AB()-» está vacío en vez de
«AB()» está vacío.

| | `test_sufijos1.py` + `test_sufijos2.py` con ese cambio |
|---|---|
| `a8d7f7b` (con la prueba) | `1 failed, 171 passed`: `FAILED tests/test_sufijos1.py::test_un_codigo_con_el_valor_vacio_no_se_genera` |
| `0224f01` (sin la prueba) | `171 passed` |

Lo que no se perdió: que un sufijo vacío no se genera. Eso lo siguen viendo
`test_sufijos2.py` y los dos sabotajes de «Ninguno vacío» de `sufijos2.sh`.

Opciones:

- **(a) Ajustar `test_sufijos2.py`.** `VACIOS` pasa a pares (sufijo, código
  que nombra): `AA()-CA00-` → «AA()», `AA(   )-` → «AA(   )»,
  `AA(DEMO)-AB()-` → «AB()», `AA(--)-` → «AA(--)» (es lo que contesta hoy
  `limpiar_sufijo`, lo corrí), y la expresión exige ese código. Un sabotaje
  más en `sufijos2.sh` con el cambio de arriba. Son archivos de la Técnica:
  lo hace ella o me lo autorizás.
- **(b) Vuelve una prueba a `test_sufijos1.py`** que sólo mire eso, con
  `AA(DEMO)-AB()-`, y su sabotaje en `sabotaje_sufijos1.sh` (vuelve a 47; ya
  no duplica al de `sufijos2.sh` porque el cambio es otro).
- **(c) Queda así.** El texto puede pasar a nombrar el sufijo entero y
  ninguna prueba lo ve.

**Recomiendo (a):** el control queda una sola vez, en el archivo dueño de la
regla, y con las cuatro formas de vacío en vez de una. (b) deja la misma
regla repartida en dos archivos, que es lo que D246 venía a sacar.

**Error mío:** cuando comprobé tu premisa comparé las entradas (`VACIOS`
trae `AA(   )-`) y no lo que cada prueba afirma. La diferencia estaba en la
expresión, no en los datos.

Próxima D: D248.

## Lo que cambió

`scripts/testing/sabotaje_sufijos1.sh`:

```diff
-# 11. un código con el valor vacío se genera
-reemplazar $G '            if not limpio.strip():' '            if False:'
-caso "codigo_vacio_se_genera" "FAILED $T::test_un_codigo_con_el_valor_vacio_no_se_genera"
-
```

El encabezado ya no dice «un código con el valor vacío no se genera» y los
comentarios de los casos que seguían bajan un número. Ninguna otra línea que
no sea comentario cambió.

`tests/test_sufijos1.py`: sale `test_un_codigo_con_el_valor_vacio_no_se_genera`
(7 líneas con sus blancos). Lo que usaba (`pytest`, `PLASTICO`, `LONA`,
`_gen`) lo siguen usando otras pruebas.

No hay otra referencia a la prueba ni al caso en `tests/`, `scripts/`,
`docs/pm/herramientas/`, `.claude/` ni `.github/`. No tenía línea que sacar
de `sabotajes-conocidos.txt`.

## Resultado

Sobre `0224f01`:

| criterio tuyo | salida |
|---|---|
| `sabotaje_sufijos1.sh` en 46 `ROJO` | 46 líneas `ROJO`, 0 `FALLA`, `OK: los 46 sabotajes dan rojo por la razón esperada`, `rc=0` |
| `sabotajes/sufijos2.sh` entero en `ROJO` | `BASE  \| 110 passed`, 32 líneas `ROJO`, `sabotajes sin rojo: 0`, `rc=0` |
| `anclas_perdidas.py` en 6 | `perdida, una línea 6 guiones: 5` |
| `test_sufijos1.py` y `test_sufijos2.py` verdes | `171 passed`, `rc=0` (61 y 110) |

Los dos sabotajes de «Ninguno vacío» de `sufijos2.sh`, copiados del log:

```
ROJO  | un sufijo vacío pasa: «test_un_sufijo_vacio_no_se_genera» «test_un_sufijo_vacio_no_genera_y_dice_donde»
ROJO  | sólo se mira el vacío como vino, no después de limpiar: «test_un_sufijo_vacio_no_se_genera[AA(   )-]» «test_un_sufijo_vacio_no_se_genera[AA(--)-]»
```

## Revisión adversarial

Uno, Sonnet, esfuerzo medio (pieza chica). Trabajó en un worktree
descartable. No encontró nada del commit.

| qué probó | resultado |
|---|---|
| seis cambios sobre `if not limpio.strip():` (`if False:`, `if not limpio:`, `if not valor:`, `and codigo != "AA"`, `and not partes`, `and pos == 0`) | los seis dan rojo en `0224f01` (entre 2 y 9 pruebas). En los dos últimos la prueba que saqué quedaba verde: miraba menos que `test_sufijos2.py` |
| camino de la prueba sacada | el mismo `_gen` y el mismo «del ítem 1» que `test_un_sufijo_vacio_no_genera_y_dice_donde`. Leído, no corrido |
| referencias colgadas, renumerado (1 a 46 sin saltos, 46 `caso`), cosas huérfanas | nada |
| `tests/test_sufijos1.py:23` importa `_bloques` y no lo usa | cierto y anterior a esta pieza (en `a8d7f7b` ya estaba sin uso). Línea propuesta para la cola |

Sólo cambió la línea del control. No probó cambios en el texto del error:
por eso no vio lo de D247.

## `/code-review high`

Sobre `a8d7f7b..0224f01`. Volvió a correr por su cuenta las dos pruebas
(`171 passed`) y los dos guiones (46 `ROJO`; 32 `ROJO`, `sabotajes sin rojo: 0`).
Dos observaciones:

| observación | qué hice |
|---|---|
| la prueba sacada era la única que fijaba qué código nombra el error | cierto, reproducido. No lo puedo arreglar donde corresponde (`test_sufijos2.py` no es mío): **D247** |
| los comentarios numerados obligan a renumerar 36 líneas para sacar un caso; «el caso 11» escrito en `REPRODUCCION-SABOTAJE-SUFIJOS1-2026-11-14.md` y en tu canal ahora cae en `letra_como_no_esta` | cierto. No lo cambié acá: sacar los números es tocar las 46 líneas otra vez. Línea propuesta para la cola |

`/security-review`: no corresponde, no hay producto.

## Comandos

```bash
VENV=/ruta/a/tu/venv
git diff a8d7f7b 0224f01 --stat | tail -1          # 2 files changed, 37 insertions(+), 49 deletions(-)
git diff a8d7f7b 0224f01 | grep -E '^[+-]' | grep -vE '^[+-]# [0-9]+\. |^(\+\+\+|---)'
#   sólo el encabezado, el bloque del caso sacado y la prueba
bash scripts/testing/sabotaje_sufijos1.sh 0224f01 $VENV | tail -1
#   OK: los 46 sabotajes dan rojo por la razón esperada   (unos 8 min)
PY=$VENV/bin/python bash scripts/testing/sabotajes/sufijos2.sh 0224f01 | tail -1
#   sabotajes sin rojo: 0
$VENV/bin/python scripts/testing/anclas_perdidas.py 0224f01 | sed -n 2p
#     perdida, una línea          6   guiones: 5

# D247: el cambio que ya nadie ve
git worktree add -q --detach /tmp/wt-d246 0224f01 && cd /tmp/wt-d246
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
sed -i 's|«{uno\[0\]\[:40\]}» está vacío|«{sufijo[:40]}» está vacío|' proyecto_maria/core/maria_generator.py
git diff --stat | tail -1                           # 1 file changed, 1 insertion(+), 1 deletion(-)
env -u DATABASE_URL -u ENVIRONMENT $VENV/bin/python -m pytest -q --no-cov -p no:cacheprovider --timeout=120 \
    tests/test_sufijos1.py tests/test_sufijos2.py | tail -1
#   171 passed      (el mismo sed sobre a8d7f7b: 1 failed, 171 passed)
cd - && git worktree remove --force /tmp/wt-d246
```

El `sed` lo corrí tal cual sobre `0224f01` y sobre `a8d7f7b`, con esas
salidas.

## Puertas

Sobre `0224f01`, árbol limpio.

| puerta | salida |
|---|---|
| `tests/test_sufijos1.py tests/test_sufijos2.py` | `171 passed`, `rc=0` |
| `sabotaje_sufijos1.sh 0224f01` | 46 `ROJO`, 0 `FALLA`, `rc=0` |
| `sabotajes/sufijos2.sh 0224f01` | 32 `ROJO`, `sabotajes sin rojo: 0`, `rc=0` |
| `anclas_perdidas.py 0224f01` | `2489 anclas medidas`; `perdida, una línea 6 guiones: 5`, `perdida, varias líneas 3 guiones: 2`. En `a8d7f7b`, `2490` y lo mismo: la que falta es la del caso sacado |
| `chequeo-6.py a8d7f7b 0224f01` | abajo, `avisos: 0` |

**No corrido:** la suite entera (cambiaron un guion y un archivo de pruebas,
ningún producto), `compileall`, las pantallas, `e2e_maria.sh`,
`smoke_friccion.sh`, `ataque_aislamiento.sh`, Postgres y `/security-review`.

## `chequeo-6`

```
chequeo-6 a8d7f7b..0224f01: avisos para mirar, no un veredicto
producto +0/−0
arnés +37/−49
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

- **Bajo, lo deja esta pieza.** D247: el error de un sufijo vacío puede pasar
  a nombrar el sufijo entero sin que una prueba lo vea. El control en sí
  sigue cubierto.
- Las 6 anclas perdidas que quedan son de mis vencidos.

## Líneas para COLA-LIMPIEZA

Dos, propuestas:

> `scripts/testing/sabotaje_sufijos1.sh`: sacar el número de los comentarios
> de cada caso. Cada uno ya se llama por su `caso` y los cuenta `CASOS`; con
> números, sacar o agregar uno en el medio obliga a renumerar todos los que
> siguen y lo escrito «el caso N» queda apuntando a otro. Visto en D246 (b).

> `tests/test_sufijos1.py:23`: `from tests.test_maria8_subitems_por_posicion
> import _bloques` no se usa.

## Archivos de producto que toqué

Ninguno.

## Sigo con

Los 7 vencidos, uno por pieza; primero `sabotaje_maria8.sh`.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `3195a8c`). Aceptadas: CUIT-GENERAR sobre `29327d2`, SABOTAJE-SUBITEMS1 sobre `bf6778e`, D243 (b) sobre `0dff850`, SABOTAJE-SUFIJOS1 sobre `afeae84`. Entregadas sin veredicto: **D245 (a) sobre `e17c11e`** y **D246 (b) sobre `0224f01`** (base `a8d7f7b`; sólo pruebas, +37/−49; 46 `ROJO`, `sufijos2.sh` 32 `ROJO`, anclas en 6, 171 verdes), con **D247 abierta**: la prueba sacada era la única que fijaba qué código nombra el error «está vacío» (opciones: (a) ajustar `test_sufijos2.py` y un sabotaje en `sufijos2.sh`, de la Técnica, recomendada; (b) vuelve una prueba a `test_sufijos1.py`; (c) queda así). Si una vuelve con devolución, va primero. **Pieza activa: el primer vencido, `scripts/testing/sabotaje_maria8.sh`**; después, uno por pieza: maria1d, maria5, valor1b, doc1.py, maria7, guardar2. D244, D239 y «Holanda» esperan a Emi: no se tocan. Próxima D: D248. Lecciones: antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada; un dato nuevo de un caso no reusa un valor que otro control del mismo caso espera; antes de escribir el informe se trae la rama de la PM; antes de sacar una prueba por duplicada se compara lo que afirma cada una, no sólo sus entradas. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que una D autoriza; subagentes hasta esfuerzo alto y sin consejero.
