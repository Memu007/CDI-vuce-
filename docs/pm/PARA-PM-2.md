# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## SABOTAJE-MARIA8: entregado en `50320ff`. Los 38 dan rojo y el guion sale de los vencidos. El caso 20 quedó reescrito, pero ya no tiene protección que atacar: va como D248

| qué | SHA |
|---|---|
| base (informe de D246 (b)) | `b8571ff` |
| pruebas: re-anclar 18, 19 y 20; sale mi línea de `sabotajes-conocidos.txt` | `b5e61be` |
| pruebas: 19 y 20 no se atan a la línea del 18. **Lo que se entrega** | `50320ff` |
| informe | el commit siguiente |

`producto +0/−0`. `arnés +8/−4`, todo en `scripts/testing/sabotaje_maria8.sh`.

Este guion ya estaba terminado cuando llegó tu orden de D247 (a) antes de
los vencidos (la traje con `f120cac`). Le faltaba sólo el informe; lo cierro
para no dejarlo sin subir y **sigo con D247 (a)**. D245 (a) y D246 (b):
leídas las dos aceptaciones.

## Decisiones

**D248. El caso 20 de `sabotaje_maria8.sh` no tiene protección que atacar.**

El caso sacaba `and not renglones` de un control que pedía el sufijo de la
operación al entrar al generador. Ese control ya no existe: desde MARIA-9 el
sufijo de la operación se busca sólo cuando un renglón no trae el suyo. Lo
que hoy hace que «con todos los sufijos propios no hace falta el de la
operación» es ese orden, no una línea que se pueda sacar.

Para que diera rojo lo reescribí agregando un pedido que el código no tiene
(`if not sufijo:` pasa a `if not sufijo or not sufijo_de_la_operacion():`).
Da rojo por la razón esperada, pero no saca una protección: inventa un
defecto. D195 (a) dice que un sabotaje así «vuelve como D para retirarlo».

Opciones:

- **(a) Retirarlo.** Quedan 37. La misma regla, donde sí hay una línea que
  la sostiene, ya la atacan `sabotaje_maria9.sh` caso 9 (`main.py`,
  `if not sbt_raw and usa_el_general:`) y caso 1 (el de la operación se
  analiza aunque nadie lo use).
- **(b) Queda como está.** 38, rojo, pero es un defecto inventado.
- **(c) Retirarlo y usar el lugar para un hueco que sí existe.** Hoy ningún
  guion nombra `test_sin_sufijo_propio_el_renglon_lleva_el_de_la_operacion`.
  Sacando `or sufijo_de_la_operacion()` de la línea del renglón (el renglón
  sin sufijo deja de heredar el de la operación), sobre `50320ff`:
  `2 failed, 44 passed`, esa prueba y
  `test_el_pedido_de_la_pantalla_sale_en_un_item`. Siguen siendo 38.

**Recomiendo (c).** (a) es la lectura estricta de D195 (a) y también me
sirve; (c) suma un caso, que es alcance, por eso lo decidís vos.

**Error mío:** reescribí el caso antes de preguntarme si la protección
seguía existiendo. Lo encontró `/code-review`; no lo cambié por mi cuenta
porque D195 (a) lo manda como D.

Próxima D: D249.

## Lo que cambió

Las tres anclas se habían perdido porque el generador ya no tiene
`sufijo_sbt`: ahora llama a `sufijo_de_la_operacion()`.

```diff
 # 18. el renglón pierde su sufijo y lleva el de la operación
 reemplazar $F '                sufijo = limpiar_sufijo(str(renglon.get("sufijo") or "").strip(),
-                                        f" del renglón {lugar_en_el_pedido[id(renglon)]}")[0] or sufijo_sbt' '                sufijo = sufijo_sbt'
+                                        f" del renglón {lugar_en_el_pedido[id(renglon)]}")[0] or sufijo_de_la_operacion()' '                sufijo = sufijo_de_la_operacion()'

 # 19. el sufijo del renglón sale sin limpiar
 reemplazar $F '                sufijo = limpiar_sufijo(str(renglon.get("sufijo") or "").strip(),
-                                        f" del renglón {lugar_en_el_pedido[id(renglon)]}")[0] or sufijo_sbt' '                sufijo = str(renglon.get("sufijo") or "").strip() or sufijo_sbt'
+                                        f" del renglón {lugar_en_el_pedido[id(renglon)]}")[0]' '                sufijo = str(renglon.get("sufijo") or "").strip()'

-# 20. vuelve a pedir el sufijo de la operación aunque cada renglón tenga el suyo
-reemplazar $F '        if not subitems and not renglones and not sufijo_sbt:' '        if not subitems and not sufijo_sbt:'
+# 20. pide el sufijo de la operación aunque cada renglón tenga el suyo
+reemplazar $F '                if not sufijo:
+                    raise ValueError(
+                        f"Item {lugar_en_el_pedido[id(renglon)]}: falta' '                if not sufijo or not sufijo_de_la_operacion():
+                    raise ValueError(
+                        f"Item {lugar_en_el_pedido[id(renglon)]}: falta'
```

El 19 ya no incluye el final de la línea (`or …`): si esa parte vuelve a
cambiar, se pierde sólo el 18. Las pruebas que espera cada caso son las
mismas de antes.

`docs/pm/herramientas/sabotajes-conocidos.txt`: saqué mi línea de
`sabotaje_maria8.sh`. Quedan 6, todas mías.

## Resultado

Sobre `50320ff`:

```
VERDE  sin sabotaje: 46 passed
ROJO   sufijo_de_la_operacion: 4 failed, 42 passed
ROJO   sufijo_sucio: 2 failed, 44 passed
ROJO   pide_sufijo_operacion: 2 failed, 44 passed
OK: los 38 sabotajes dan rojo por la razón esperada
```

38 líneas `ROJO`, 0 `FALLA`, `rc=0`. El 20 falla con
`ValueError: Item 1: falta el sufijo de valor (CSBTSVL).` en
`test_con_todos_los_sufijos_propios_no_hace_falta_el_de_la_operacion`; de
arrastre pone roja `test_sin_ningun_sufijo_el_error_dice_el_numero_de_la_pantalla`.

## Revisión adversarial

Uno, Sonnet, esfuerzo medio (pieza chica), sobre `b5e61be`, en un worktree
descartable.

| qué probó | resultado |
|---|---|
| los tres cambios reescritos, uno por uno | fallan por una afirmación de valor o por el `ValueError` esperado; ninguno por error de nombre o de sintaxis |
| repetidos con otros guiones | no hay; con `sabotaje_maria9.sh` caso 1 se tocan en parte |
| anclas | todas son código |
| cambiar `{lugar_en_el_pedido[id(renglon)]}` por `{n}` en la etiqueta con que se limpia el sufijo del renglón | **sobrevive**: lo reproduje, `253 passed` en `test_maria8`, `test_maria9_sufijo_operacion`, `test_maria9_bordes`, `test_sufijos1` y `test_sufijos2`. Ver Riesgos |
| sacar el `.strip()` del sufijo del renglón | dice que sobrevive porque `limpiar_sufijo` lo cubre. No lo comprobé |

## `/code-review high`

Sobre `b8571ff..b5e61be`. Corrió el guion por su cuenta (38 `ROJO`). Tres
observaciones, las tres reproducidas:

| observación | qué hice |
|---|---|
| el 20 agrega un pedido en vez de sacar una protección | **D248** |
| 18, 19 y 20 colgaban de la misma línea entera: un cambio ahí perdía los tres | arreglado en `50320ff` |
| ningún guion nombra `test_sin_sufijo_propio_el_renglon_lleva_el_de_la_operacion` | cierto y anterior a esta pieza. Es la opción (c) de D248 |

`50320ff` no pasó por subagente ni por `/code-review`: aplica la segunda
observación y lo prueba el guion entero.

`/security-review`: no corresponde, no hay producto.

## Comandos

```bash
VENV=/ruta/a/tu/venv
git diff b8571ff 50320ff --stat | tail -1          # 2 files changed, 8 insertions(+), 5 deletions(-)
bash scripts/testing/sabotaje_maria8.sh 50320ff $VENV | tail -1
#   OK: los 38 sabotajes dan rojo por la razón esperada   (unos 5 min)
$VENV/bin/python scripts/testing/anclas_perdidas.py 50320ff | sed -n 2,3p
#     perdida, una línea          5   guiones: 4
#     perdida, varias líneas      1   guiones: 1

# D248 (c): el hueco que hoy ningún guion ataca
git worktree add -q --detach /tmp/wt-m8 50320ff && cd /tmp/wt-m8
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
sed -i 's|id(renglon)\]}")\[0\] or sufijo_de_la_operacion()|id(renglon)]}")[0]|' proyecto_maria/core/maria_generator.py
git diff --stat | tail -1                           # 1 file changed, 1 insertion(+), 1 deletion(-)
env -u DATABASE_URL -u ENVIRONMENT $VENV/bin/python -m pytest -q --no-cov -p no:cacheprovider --timeout=120 \
    tests/test_maria8_subitems_por_posicion.py | tail -1
#   2 failed, 44 passed
cd - && git worktree remove --force /tmp/wt-m8
```

Los corrí tal cual, con esas salidas.

## Puertas

Sobre `50320ff`, árbol limpio.

| puerta | salida |
|---|---|
| `sabotaje_maria8.sh 50320ff` | `VERDE sin sabotaje: 46 passed`; 38 `ROJO`, 0 `FALLA`; `rc=0` |
| `tests/test_anclas_perdidas.py tests/test_maria8_subitems_por_posicion.py tests/test_maria9_sufijo_operacion.py` | `100 passed`, `rc=0` |
| `anclas_perdidas.py 50320ff` | `103 guiones, 2489 anclas medidas`; `perdida, una línea 5 guiones: 4`, `perdida, varias líneas 1 guiones: 1`. En `b8571ff`: 6 y 3. `sabotaje_maria8.sh` ya no aparece |
| `chequeo-6.py b8571ff 50320ff` | abajo, `avisos: 0` |

**No corrido:** la suite entera (cambió un guion, ningún producto ni
prueba), `compileall`, las pantallas, `e2e_maria.sh`, `smoke_friccion.sh`,
`ataque_aislamiento.sh`, Postgres y `/security-review`.

## `chequeo-6`

```
chequeo-6 b8571ff..50320ff: avisos para mirar, no un veredicto
producto +0/−0
arnés +8/−4
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

- **Bajo, anterior a esta pieza.** Si el generador nombrara mal el renglón
  en un error de sufijo (`{n}` en vez del lugar en el pedido), ninguna
  prueba lo ve. Por la API no llega a verse: `main.py` valida antes el
  sufijo de cada ítem con su número. Lo probé con un solo error (4 ítems en
  2 posiciones, el 4 con un sufijo de 121 caracteres): original y cambiado
  contestan `400 Item 4: El sufijo de valor SBT no puede superar los 120
  caracteres.` Con otros errores de sufijo no lo probé.
- **Para D247 (a):** tu criterio dice «anclas en 6». Después de esta pieza
  la cuenta de una línea es 5; en D247 voy a informar contra 5.
- Las 5 y 1 anclas perdidas que quedan son de mis otros vencidos.

## Líneas para COLA-LIMPIEZA

Ninguna.

## Archivos de producto que toqué

Ninguno.

## Sigo con

D247 (a). Después los 6 vencidos que quedan, uno por pieza: maria1d,
maria5, valor1b, doc1.py, maria7, guardar2.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `f120cac`). Aceptadas: CUIT-GENERAR sobre `29327d2`, SABOTAJE-SUBITEMS1 sobre `bf6778e`, D243 (b) sobre `0dff850`, SABOTAJE-SUFIJOS1 sobre `afeae84`, D245 (a) sobre `e17c11e`, D246 (b) sobre `0224f01`. Entregada sin veredicto: **SABOTAJE-MARIA8 sobre `50320ff`** (base `b8571ff`; sólo arnés, +8/−4; 38 `ROJO`; anclas de una línea en 5, de varias en 1), con **D248 abierta**: el caso 20 no tiene protección que atacar (opciones: (a) retirarlo, 37; (b) queda reescrito; (c) retirarlo y usar el lugar para sacar `or sufijo_de_la_operacion()` del renglón, `2 failed, 44 passed`, recomendada). Si vuelve con devolución, va primero. **Pieza activa: D247 (a)**, decidida por la PM: tocar sólo `tests/test_sufijos2.py` y `scripts/testing/sabotajes/sufijos2.sh` (de la Técnica, autorizados para esto); se acepta si con `«{uno[0][:40]}»` → `«{sufijo[:40]}»` la entrega da rojo en las cuatro formas de `VACIOS` y `0224f01` queda verde, `sufijos2.sh` entero en `ROJO` con un sabotaje más (33), `sabotaje_sufijos1.sh` sigue en 46, las dos pruebas verdes; anclas: ella escribió 6, hoy son 5 por maria8; sugerencia suya, no criterio: `VACIOS` como pares (sufijo, código que nombra). Después, uno por pieza: maria1d, maria5, valor1b, doc1.py, maria7, guardar2. D244, D239 y «Holanda» esperan a Emi: no se tocan. Próxima D: D249. Lecciones: antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada; un dato nuevo de un caso no reusa un valor que otro control del mismo caso espera; antes de escribir el informe se trae la rama de la PM; antes de sacar una prueba por duplicada se compara lo que afirma cada una, no sólo sus entradas; antes de reescribir un sabotaje con el ancla perdida se mira si la protección que atacaba sigue existiendo: si no, es una D (D195 (a)). Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que una D autoriza; subagentes hasta esfuerzo alto y sin consejero.
