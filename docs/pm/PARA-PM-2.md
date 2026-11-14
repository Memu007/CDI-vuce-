# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D247 (a): entregada en `4a58c68`. Con «{sufijo[:40]}» el error del vacío da rojo en las cuatro formas. Queda la misma falta en «pide un número» y «cambiaría»: va como D249

| qué | SHA |
|---|---|
| base (informe de SABOTAJE-MARIA8) | `87be8f1` |
| pruebas: `VACIOS` dice qué código nombra el error; un sabotaje más en `sufijos2.sh` | `b597c31` |
| pruebas: la afirmación vuelve a fijar el orden de las frases. **Lo que se entrega** | `4a58c68` |
| tu rama, traída (`f13e5c7`: MARIA8 aceptada, D248 (c)) | `e5e1090` |
| informe | el commit siguiente |

`producto +0/−0`. `arnés +12/−2`: `tests/test_sufijos2.py` y
`scripts/testing/sabotajes/sufijos2.sh`, los dos que autorizaste. Nada más
tocado.

Leí la aceptación de SABOTAJE-MARIA8 y D248 (c): es lo que sigue.

## Decisiones

**D249. Los otros dos errores de `limpiar_sufijo` tampoco fijan qué código nombran.**

Es la misma falta que D247, en las pruebas de al lado
(`tests/test_sufijos2.py`, de la Técnica; D247 no me autorizaba a tocarlas).
Los tres mensajes usan `«{uno[0][:40]}»`. Sobre `4a58c68`, cambiando sólo esa
parte del producto:

| mensaje | cambio | resultado |
|---|---|---|
| «cambiaría de valor» | `«{sufijo[:40]}»` (el sufijo entero) | `171 passed` |
| «pide un número» | `«{sufijo[pos:pos + 40]}»` (desde el código hasta el final) | `171 passed` |
| «pide un número» | `«{sufijo[:40]}»` | `1 failed, 170 passed`: lo ve un solo dato, `AA(X)-ZB(16.384)-CA00-` |
| «está vacío» | `«{uno[0]}»` (sin el recorte a 40) | `171 passed` |

Qué le pasa a quien usa el sistema si eso se rompe: el error le muestra el
sufijo entero y tiene que buscar a ojo cuál de los códigos está mal. No sale
un TXT malo: el error se sigue dando.

- (a) Me autorizás una pieza chica aparte: los datos de esos dos casos como
  pares (sufijo, código que nombra), un código de más de 40 letras, y tres
  sabotajes en `sufijos2.sh`.
- (b) La hace la Técnica, que es la dueña del archivo.
- (c) Queda así.

**Recomiendo (a), después de los vencidos.** Es el mismo arreglo que ya
decidiste para «está vacío» y ya tengo los tres cambios reproducidos. No es
urgente: no cambia lo que sale en el TXT.

## Lo que cambió

`tests/test_sufijos2.py`. `VACIOS` pasó de lista a pares (tu sugerencia): el
sufijo y el código que el error tiene que nombrar. Los nombres de los cuatro
casos no cambian (`[AA()-CA00-]`, `[AA(   )-]`, `[AA(DEMO)-AB()-]`,
`[AA(--)-]`), así que los sabotajes que ya los citaban siguen valiendo.

```python
# sufijo: el código que el error nombra, y no el sufijo entero
VACIOS = {"AA()-CA00-": "AA()", "AA(   )-": "AA(   )", "AA(DEMO)-AB()-": "AB()", "AA(--)-": "AA(--)"}

@pytest.mark.parametrize("vacio", VACIOS)
def test_un_sufijo_vacio_no_se_genera(vacio):
    nombra = re.escape(VACIOS[vacio])
    with pytest.raises(ValueError, match=rf"Sufijo de valor del ítem 2: «{nombra}» está vacío.*no se genera"):
        mg.limpiar_sufijo(vacio, " del ítem 2")
```

Antes la expresión era `«A[AB]\(.*está vacío.*no se genera`: el `.*` se comía
el resto del sufijo.

`scripts/testing/sabotajes/sufijos2.sh`: un sabotaje más, «el error del vacío
nombra el sufijo entero y no el código» (`«{uno[0][:40]}» está vacío` →
`«{sufijo[:40]}» está vacío`), que tiene que dar rojo en los cuatro casos.

**Un error mío, ya arreglado.** En `b597c31` partí la afirmación en dos
(`match="no se genera"` y un `in` aparte). Así dejaba de fijar que «está
vacío» va antes que «no se genera», que la expresión vieja sí fijaba. Lo
marcaron el adversario y `/code-review`. `4a58c68` lo vuelve a una sola
expresión. Con las frases del producto cambiadas de orden: `87be8f1`
`4 failed`, `b597c31` `171 passed` (el hueco), `4a58c68` `4 failed`.

## Resultado, contra tu criterio

| criterio | resultado |
|---|---|
| con `«{sufijo[:40]}»` la entrega da rojo en las cuatro formas | `4a58c68`: `4 failed, 167 passed`, los cuatro `test_un_sufijo_vacio_no_se_genera[...]` |
| la base `0224f01` queda verde con ese cambio | `171 passed` |
| `sufijos2.sh` entero en `ROJO`, con uno más (33) | `BASE \| 110 passed`; 33 `ROJO`; `sabotajes sin rojo: 0`; `rc=0` |
| `sabotaje_sufijos1.sh` sigue en 46 | 46 `ROJO`, 0 `FALLA`; `OK: los 46 sabotajes dan rojo por la razón esperada`; `rc=0` |
| anclas en 5 de una línea y 1 de varias | `perdida, una línea 5 guiones: 4`; `perdida, varias líneas 1 guiones: 1` |
| las dos pruebas verdes | `tests/test_sufijos1.py tests/test_sufijos2.py`: `171 passed` |

## Revisión adversarial

Pieza chica de arnés: un adversario, Sonnet, esfuerzo medio, sobre `b597c31`,
en un árbol descartable.

| qué probó | resultado |
|---|---|
| el mensaje del vacío con `{sufijo[:40]}`, `{codigo}`, `{valor}`, `{uno[0][:3]}`, `{uno[0][:2]}`, un espacio de más entre comillas | `4 failed, 167 passed` cada uno |
| `{uno[0][:5]}` | `2 failed, 169 passed` |
| sin tildes / sin `donde` | `9 failed` / `8 failed` |
| los nombres de los cuatro casos | iguales que antes; ningún otro guion los cita |
| el sabotaje nuevo | ancla de código, una sola vez; rojo por la afirmación; no repite otro |
| **verde y no debería:** `{uno[0]}` sin recorte | `171 passed`. Ya estaba así: va en D249 |
| **verde y no debería:** las frases en otro orden | era mi error; arreglado en `4a58c68` |

No encontró defecto de la pieza fuera de esos dos.

## `/code-review high 87be8f1..b597c31`

Sin errores de corrección. Cuatro observaciones, las cuatro reproducidas por
mí:

| observación | qué hice |
|---|---|
| el orden de las frases dejó de fijarse | arreglado en `4a58c68` |
| «cambiaría» acepta el sufijo entero | D249 |
| «pide un número» no fija dónde termina el código | D249 |
| ningún dato pasa de 40 letras: el recorte no se prueba | D249 |

**`4a58c68` no volvió a pasar por subagente ni por `/code-review`.** Es el
arreglo de lo que ellos marcaron (4 líneas de una prueba). Lo comprobé con
las dos mutaciones de arriba (el cambio de tu criterio y el orden) y con
todas las puertas corridas de nuevo sobre ese SHA.

## Comandos

```bash
VENV=/ruta/a/tu/venv
git diff 87be8f1 4a58c68 --stat | tail -1           # 2 files changed, 12 insertions(+), 2 deletions(-)
PY=$VENV/bin/python bash scripts/testing/sabotajes/sufijos2.sh 4a58c68 | grep -c '^ROJO  |'     # 33
PY=$VENV/bin/python bash scripts/testing/sabotajes/sufijos2.sh 4a58c68 | tail -1                # sabotajes sin rojo: 0
bash scripts/testing/sabotaje_sufijos1.sh 4a58c68 $VENV | tail -1
#   OK: los 46 sabotajes dan rojo por la razón esperada   (unos 8 min)
$VENV/bin/python scripts/testing/anclas_perdidas.py 4a58c68 | sed -n 2,3p
#     perdida, una línea          5   guiones: 4
#     perdida, varias líneas      1   guiones: 1

# tu criterio: el cambio, sobre la entrega y sobre la base
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
for sha in 0224f01 4a58c68; do
  git worktree add -q --detach /tmp/wt-d247 $sha && cd /tmp/wt-d247
  sed -i 's|«{uno\[0\]\[:40\]}» está vacío|«{sufijo[:40]}» está vacío|' proyecto_maria/core/maria_generator.py
  git diff --stat | tail -1                         # 1 file changed, 1 insertion(+), 1 deletion(-)
  env -u DATABASE_URL -u ENVIRONMENT $VENV/bin/python -m pytest -q --no-cov -p no:cacheprovider --timeout=120 \
      tests/test_sufijos1.py tests/test_sufijos2.py | tail -1
  cd - && git worktree remove --force /tmp/wt-d247
done
#   0224f01: 171 passed          4a58c68: 4 failed, 167 passed
```

Corrí cada uno una vez, con la salida a un archivo; esas son sus líneas. El
árbol descartable lo armé en mi carpeta de trabajo, no en `/tmp/wt-d247`.

## Puertas

Sobre `4a58c68`, árbol limpio.

| puerta | salida |
|---|---|
| `sufijos2.sh 4a58c68` | `BASE \| 110 passed`; 33 `ROJO`, ningún `VERDE`, `ROTO` ni `ROJO?`; `sabotajes sin rojo: 0`; `rc=0` |
| `sabotaje_sufijos1.sh 4a58c68` | 46 `ROJO`, 0 `FALLA`; `rc=0` |
| `tests/test_sufijos1.py tests/test_sufijos2.py` | `171 passed` |
| `anclas_perdidas.py 4a58c68` | `103 guiones, 2490 anclas medidas y 11 llamadas sin medir`; 5 y 1; `rc=0` |
| `chequeo-6.py 87be8f1 4a58c68` | abajo, `avisos: 0` |

**No corrido:** la suite entera (cambiaron una prueba y un guion, ningún
producto), `compileall`, las pantallas, `e2e_maria.sh`, `smoke_friccion.sh`,
`ataque_aislamiento.sh`, Postgres y `/security-review`.

## `chequeo-6`

```
chequeo-6 87be8f1..4a58c68: avisos para mirar, no un veredicto
producto +0/−0
arnés +12/−2
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

- Lo de D249: tres cambios del texto de error que hoy quedan en verde. No
  afectan el TXT.
- `4a58c68` sin segunda revisión independiente (arriba).
- Toqué dos archivos de la Técnica. Si ella tiene cambios sin subir sobre
  `VACIOS` o sobre el bloque «Ninguno vacío» de `sufijos2.sh`, va a haber
  conflicto al unir.

## Líneas para COLA-LIMPIEZA

Ninguna.

## Archivos de producto que toqué

Ninguno.

## Sigo con

D248 (c): en `sabotaje_maria8.sh` sale el caso 20 y en su lugar va «el
renglón sin sufijo propio deja de heredar el de la operación». Después los 6
vencidos, uno por pieza, empezando por `sabotaje_maria1d.sh`.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `f13e5c7`). Aceptadas: CUIT-GENERAR sobre `29327d2`, SABOTAJE-SUBITEMS1 sobre `bf6778e`, D243 (b) sobre `0dff850`, SABOTAJE-SUFIJOS1 sobre `afeae84`, D245 (a) sobre `e17c11e`, D246 (b) sobre `0224f01`, SABOTAJE-MARIA8 sobre `50320ff`. Entregada sin veredicto: **D247 (a) sobre `4a58c68`** (base `87be8f1`; sólo `tests/test_sufijos2.py` y `sabotajes/sufijos2.sh`, arnés +12/−2; 33 y 46 `ROJO`; anclas 5 y 1), con **D249 abierta**: «pide un número» y «cambiaría» tampoco fijan qué código nombran, ni el recorte a 40 (opciones: (a) pieza chica mía aparte, recomendada, después de los vencidos; (b) la Técnica; (c) queda). Si vuelve con devolución, va primero. **Pieza activa: D248 (c)**, decidida por la PM: en `scripts/testing/sabotaje_maria8.sh` sale el caso 20 y en su lugar va el sabotaje «el renglón sin sufijo propio deja de heredar el de la operación», en `ROJO` por `test_sin_sufijo_propio_el_renglon_lleva_el_de_la_operacion`; el guion sigue en 38 `ROJO` y 0 `FALLA`; anclas no empeoran (5 y 1); su ancla cuelga del final de la línea del 18 y está bien así; sugerencia suya, no criterio: la misma herencia en el ítem entero y en el sub-ítem, como datos del caso, si entran sin tocar otro guion. Después, uno por pieza: maria1d, maria5, valor1b, doc1.py, maria7, guardar2. D244, D239 y «Holanda» esperan a Emi: no se tocan. Próxima D: D250. Lecciones: antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada; un dato nuevo de un caso no reusa un valor que otro control del mismo caso espera; antes de escribir el informe se trae la rama de la PM; antes de sacar una prueba por duplicada se compara lo que afirma cada una, no sólo sus entradas; antes de reescribir un sabotaje con el ancla perdida se mira si la protección que atacaba sigue existiendo: si no, es una D (D195 (a)); al ajustar una afirmación, la nueva tiene que seguir afirmando todo lo que afirmaba la vieja (el orden también), y una mutación que «mueve» una frase la tiene que sacar de donde estaba. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que una D autoriza; subagentes hasta esfuerzo alto y sin consejero.
