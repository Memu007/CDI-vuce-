# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## SABOTAJE-SUBITEMS1: entregada en `bf6778e`. `sabotaje_subitems1.sh` vuelve a dar rojo en todos sus casos y ahora son 11. Sólo pruebas. Una decisión: D245

| qué | SHA |
|---|---|
| base (informe de CUIT-GENERAR) | `47b8481` |
| pruebas | `4d58129` |
| pruebas. **Lo que se entrega** | `bf6778e` |
| tu rama integrada (`ae3a4b5`, sólo `docs/pm/`) | `027e7a2` |
| informe | el commit siguiente |

`producto +0/−0`. Toqué el guion, `tests/test_subitems1.py` y saqué mi línea
de `sabotajes-conocidos.txt`.

Leí tu veredicto de CUIT-GENERAR al traer tu rama, con esta pieza ya en las
puertas: la cerré y **sigo con D243 (b)**, que pusiste primera. D244 no la
toco.

## Decisiones

**D245. Tres pruebas del semáforo pasan aunque el semáforo reviente.**
`/api/validate/smart` contesta 200 con `{"success": false, "detail": …}`
cuando revienta por dentro (`main.py:4585`). Por eso el caso 8 del guion
había quedado verde. Arreglé la prueba de esta pieza; hay tres más que sólo
miran el 200, o algo que ese cuerpo también cumple:

- `tests/test_punta_a_punta1.py:283-284` (`assert not r.json().get("errores")`)
- `tests/test_generar_maria_txt.py:797-798`
- `tests/test_cobro_corte1.py:534-536`

Medido sobre `bf6778e`, en un worktree descartable, con un `raise` como
primera línea del semáforo: esos tres archivos y `test_subitems1.py` dan
`4 failed, 130 passed, 2 xfailed`, y los cuatro rojos son los de mi prueba.
Las otras llamadas al semáforo en `tests/` (siete archivos) leen `errores`,
`advertencias` o `estadisticas` del cuerpo y caen solas (las leí, no las
saboteé una por una).

- (a) pieza chica de pruebas: las tres afirman `success`, con ese mismo
  `raise` como rojo.
- (b) queda así.
- **Recomiendo (a)**, sin apuro, después de los vencidos: la primera es la
  prueba de punta a punta, y hoy no se entera si el semáforo se rompe. La de
  `test_cobro_corte1` prueba otra cosa (que se pueda validar con el tope
  lleno); si preferís, queda afuera.

## Lo que hice distinto de lo que me escribiste (supuestos reversibles)

Me escribiste reescribir el guion vencido. Además:

1. **Una afirmación nueva en `test_la_validacion_no_revienta_con_subitems_raros`**
   (`success is True`). Sin ella el caso 8 no tiene cómo dar rojo: el
   semáforo se traga el error. La otra salida era sabotear dos lugares a la
   vez para verlo en `/generate_maria`; la descarté porque dejaba la prueba
   del semáforo sin mirar nada.
2. **Dos datos nuevos en esa prueba, `3.5` y `[1]`, y el sabotaje 11.** Los
   encontró el adversario: con sólo `5` y `True`, dos cambios en
   `controles_maria.py` quedaban verdes.
3. **El sabotaje 10** (`sufijo_no_texto`): el dato `[{"sufijo": 5}]` ya
   estaba en la prueba y no tenía negativo.
4. **Un docstring corregido** en `test_subitems_que_no_son_una_lista_dan_400_y_no_500`:
   decía que los controles corren antes que el control de forma, y es al
   revés.
5. **Saqué mi línea de `sabotajes-conocidos.txt`**, como en las piezas
   anteriores.

## Lo que salió mal

La primera versión (`4d58129`) dejaba los dos huecos del punto 2 y no los vi
yo: los encontró el adversario. Van cerrados en `bf6778e`, cada uno con su
rojo medido.

## Resultado

**Por qué dos casos habían quedado verdes** (los tres archivos del guion,
sobre `47b8481`, en un worktree descartable):

| qué se saca | resultado |
|---|---|
| nada | `41 passed, 2 xfailed` |
| sólo el segundo control de forma de `/generate_maria` (lo que hacía el caso 7) | `41 passed, 2 xfailed` |
| sólo el primero | `41 passed, 2 xfailed` |
| los dos | `6 failed, 35 passed, 2 xfailed` |
| sólo `controles_maria.py:127` (lo que hacía el caso 8) | `41 passed, 2 xfailed` |

- **Caso 7.** El control de forma de los sub-ítems está dos veces en
  `/generate_maria` (`main.py:5082` y `:5111`). Sacando uno, el otro sigue
  contestando 400. Con los dos afuera el 500 es real: `Error generando
  archivo MARIA: 'int' object has no attribute 'get'`. El caso ahora saca
  los dos.
- **Caso 8.** En `/generate_maria` el primer control de forma frena antes de
  llegar a `controles_maria.py:127`, así que ahí no se ve. En el semáforo sí
  revienta, pero contestaba 200 y la prueba sólo miraba eso. Con la
  afirmación nueva: `{"success":false,"detail":"'int' object is not
  iterable"}`, `assert False is True`. El caso ahora espera la prueba del
  semáforo.

No corrí el guion viejo entero: reproduje sus dos estados verdes con las
mismas líneas (la tabla). Lo corriste vos sobre `7436c6e5`.

## Negativos

`scripts/testing/sabotaje_subitems1.sh bf6778e`, salida de las puertas:

```
VERDE  sin sabotaje: ================= 43 passed, 2 xfailed, 11 warnings in 10.34s ==================
ROJO   subitem_en_cero: ============= 7 failed, 36 passed, 2 xfailed, 9 warnings in 10.15s =============
ROJO   sin_valor: ============= 3 failed, 40 passed, 2 xfailed, 9 warnings in 9.90s ==============
ROJO   sin_numero_de_subitem: ============= 7 failed, 36 passed, 2 xfailed, 9 warnings in 9.93s ==============
ROJO   grupo_con_subitems: ============= 1 failed, 42 passed, 2 xfailed, 9 warnings in 10.20s =============
ROJO   tres_decimales: ============= 3 failed, 40 passed, 2 xfailed, 9 warnings in 10.06s =============
ROJO   sufijo_sin_subitem: ============= 4 failed, 39 passed, 2 xfailed, 9 warnings in 10.00s =============
ROJO   forma_500: ============ 6 failed, 37 passed, 2 xfailed, 15 warnings in 10.20s =============
ROJO   controles_500: ============= 3 failed, 40 passed, 2 xfailed, 9 warnings in 9.77s ==============
ROJO   numero_de_linea: ============= 3 failed, 40 passed, 2 xfailed, 9 warnings in 9.96s ==============
ROJO   sufijo_no_texto: ============= 1 failed, 42 passed, 2 xfailed, 9 warnings in 9.84s ==============
ROJO   subitem_no_objeto: ============= 1 failed, 42 passed, 2 xfailed, 9 warnings in 9.86s ==============
OK: los 11 sabotajes dan rojo por la razón esperada
```

Los cuatro que cambiaron o son nuevos, con lo que dice cada rojo (medidos
uno por uno, fuera del guion):

| caso | qué se saca | rojo |
|---|---|---|
| 7 `forma_500` | los dos controles de forma | 6: `test_un_pedido_mal_armado_da_400_y_no_500[subitems0]` y `[abc]`, y los cuatro de `test_subitems_que_no_son_una_lista_dan_400_y_no_500`. 500 con `'int' object has no attribute 'get'`, `'str' object has no attribute 'get'`, `'int'`, `'bool'` y `'float' object is not iterable` |
| 8 `controles_500` | el `isinstance(subitems, list)` de `controles_maria.py:127` | 3: `test_la_validacion_no_revienta_con_subitems_raros[5]`, `[True]` y `[3.5]`. `{"success":false,"detail":"'int' object is not iterable"}` |
| 10 `sufijo_no_texto` | el control de que el sufijo del sub-ítem sea un texto (`main.py:5114`) | 1: `test_un_pedido_mal_armado_da_400_y_no_500[subitems2]`, `assert 500 == 400` |
| 11 `subitem_no_objeto` | el salto del sub-ítem que no es un objeto (`controles_maria.py:128`) | 1: `test_la_validacion_no_revienta_con_subitems_raros[subitems3]`, `{"success":false,"detail":"'int' object has no attribute 'get'"}` |

El dato `3.5` distingue además un cambio que el adversario dejó verde (un
control que sólo mirara enteros y booleanos): con él da `1 failed, 26
passed`, `[3.5]`, `'float' object is not iterable`.

## Revisión adversarial

Pieza chica de pruebas: un adversario, `adversario-sonnet-alto` (Sonnet,
alto), sobre `4d58129`. Leyó y corrió.

| hallazgo | qué hice |
|---|---|
| los 10 casos de esa versión dan rojo por el motivo que dicen; no encontró cómo el guion dice OK sin que lo sea | |
| conviene: sacar `if not isinstance(sub, dict): continue` dejaba todo verde (también `593 passed` en 10 archivos) | dato `[1]` y sabotaje 11 |
| nota: un control `… if not isinstance(subitems, (int, bool)) else []` dejaba todo verde | dato `3.5` |
| ninguna entrada distingue los dos controles de forma por el estado: sacando sólo el segundo, 0 diferencias en 364 pedidos; sacando sólo el primero sigue el 400 y cambia cuál error gana | el segundo es código muerto: línea para la cola, abajo |
| los tres datos de `test_el_error_del_sufijo_dice_que_subitem` caen juntos: sacar sólo el tope de 120 caracteres o sólo el de caracteres de control queda verde | riesgo. Ya era así; no es de esta pieza |
| no hay caso con sub-ítems vacíos que no son lista (`{}`, `""`, `0`, `False`): cambiar `is not None` por «si hay algo» en los dos controles queda verde | riesgo, ídem |
| `test_un_pedido_mal_armado_da_400_y_no_500` sólo mira el estado, y `_pedir` no manda CUIT del despachante: un pedido bueno también daría 400 | riesgo. No encontró un cambio que quede verde por eso |

## `/code-review high` sobre `47b8481..4d58129`

Los revisores heredan Fable. Cinco hallazgos, ningún defecto en el diff.

| # | hallazgo | qué hice |
|---|---|---|
| 1 | otras pruebas del semáforo sólo miran el 200 | D245 |
| 2 | el caso 7 depende de que el control esté dos veces: cuando la cola deje uno, el guion corta con `PATRON NO ENCONTRADO` | riesgo. Corta fuerte, no en silencio; lo digo en la línea de la cola |
| 3 | el docstring viejo | corregido en `bf6778e` |
| 4 | `caso` sólo busca el nombre de la prueba en la línea `FAILED`: no distingue un 500 de otro estado que no sea 400 | riesgo. Es el patrón del guion desde antes |
| 5 | el semáforo dice `success: true` y ningún error para sub-ítems mal armados (`5`, `[1]`, `"abc"`) que `/generate_maria` rechaza con 400: el control de forma vive en el endpoint y no en `controles_antes_de_generar` | línea para la cola. Sólo se llega con un pedido armado a mano |

`bf6778e` (dos datos, un sabotaje, un docstring) no volvió a pasar por
`/code-review` ni por el adversario: lo revisé yo contra el diff y lo
cubren las puertas.

## Comandos

```bash
# desde la raíz del repo, con esta rama; VENV es tu entorno con las dependencias
export VENV=/ruta/al/venv
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake
# 1. el guion: «VERDE sin sabotaje: 43 passed, 2 xfailed», 11 «ROJO» y «OK: los 11 sabotajes…» (dos minutos y medio)
env -u DATABASE_URL -u ENVIRONMENT bash scripts/testing/sabotaje_subitems1.sh bf6778e $VENV
# 2. las pruebas: «27 passed»
env -u DATABASE_URL -u ENVIRONMENT $VENV/bin/python -m pytest -q --no-cov -p no:cacheprovider tests/test_subitems1.py
# 3. igual que la base: «perdida, una línea 10 guiones: 8»
$VENV/bin/python scripts/testing/anclas_perdidas.py bf6778e | head -8
# 4. producto y avisos
python docs/pm/herramientas/chequeo-6.py 47b8481 bf6778e
```

## Puertas

Todas sobre `bf6778e`, de a una.

| puerta | salida |
|---|---|
| suite completa de pytest | `6145 passed, 110 skipped, 3 xfailed` en 0:20:10, `rc=0`. Son los 6143 de `29327d2` más los dos datos nuevos |
| `compileall -q proyecto_maria` | `rc=0`, sin salida |
| `sabotaje_subitems1.sh bf6778e` | `rc=0`, arriba |
| `anclas_perdidas.py` | `perdida, una línea 10 guiones: 8`, las mismas diez que en `47b8481` |
| `chequeo-6.py 47b8481 bf6778e` | abajo, entera |

**No corrí:** las pantallas, `e2e_maria.sh`, `smoke_friccion.sh` ni
`ataque_aislamiento.sh` (no hay cambio de producto ni de `static/`);
Postgres; los demás guiones de sabotaje; `/security-review` (no toca plata,
sesión, permisos ni datos). Las puertas corrieron sobre `bf6778e`; tu rama
entró después y sólo trae `docs/pm/`.

## `chequeo-6`

```
chequeo-6 47b8481..bf6778e: avisos para mirar, no un veredicto
producto +0/−0
arnés +20/−7
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

- El caso 7 está atado a que el control esté dos veces. Cuando se saque
  uno, el guion corta con `PATRON NO ENCONTRADO` y hay que borrarle una
  línea.
- `caso` no distingue un 500 de otro estado que no sea 400.
- Los tres riesgos del adversario de la tabla (el tope de 120 y los
  caracteres de control del sufijo sin negativo propio; los sub-ítems vacíos
  que no son lista sin caso; `_pedir` sin CUIT del despachante).
- El control de que el sufijo **del renglón** sea un texto, sacado, deja
  `test_subitems1.py` en verde (`25 passed`): no es de este archivo y no
  busqué si otro lo cubre.
- D245: hasta que se decida, la prueba de punta a punta no se entera si el
  semáforo revienta.

## Líneas que propongo para `COLA-LIMPIEZA.md` (no la toco)

- En lugar de la línea 255 («`main.py` (`/generate_maria`): el control de
  forma de los sub-ítems está dos veces…»): «`main.py` (`/generate_maria`):
  el control de forma de los sub-ítems está dos veces (`:5082` y `:5111`
  sobre `bf6778e`). El segundo es código muerto: el primero corre antes y
  frena todo lo que el segundo frenaría (adversario: 0 diferencias en 364
  pedidos). Sale el segundo, y del caso 7 de `sabotaje_subitems1.sh` sale su
  línea. Lo del semáforo ya está contestado: nada lo frenaba, el endpoint
  devuelve 200 con `success: false`.»
- Nueva: «El control de forma de los sub-ítems vive en `/generate_maria` y
  no en `controles_antes_de_generar`: el semáforo (`/api/validate/smart`)
  dice que está todo bien con sub-ítems mal armados que generar rechaza.
  Una sola copia, en la función que usan los dos.»

## Archivos de producto que toqué

Ninguno.

## Sigo con

D243 (b): las cuatro anclas en `estudio1.sh`, `estudio1b.sh` y `excel2.sh`,
con los tres guiones enteros y `anclas_perdidas.py` de vuelta a 6. Después
`sabotaje_sufijos1.sh` con el dato nuevo de `sufijo_otra1`.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `ae3a4b5`). CUIT-GENERAR aceptada sobre `29327d2`; D243 (b) decidida; D244, D239 y «Holanda» esperan a Emi: no se tocan. SABOTAJE-SUBITEMS1 entregada sobre `bf6778e` (base `47b8481`; pruebas `4d58129` y `bf6778e`; sólo pruebas; suite `6145 passed`; el guion da 11 rojos), con D245 (tres pruebas del semáforo que pasan aunque reviente: `test_punta_a_punta1.py:283`, `test_generar_maria_txt.py:797`, `test_cobro_corte1.py:534`; recomiendo (a), pieza chica de pruebas) sin contestar. Si vuelve con devolución, va primero. Orden de la PM: 1) **D243 (b), pieza activa**: cambio yo las cuatro anclas de `sabotajes/estudio1.sh:77`, `estudio1b.sh:70` y `:74` y `excel2.sh:167` con las líneas de la tabla de mi informe de CUIT-GENERAR (`git show 47b8481:docs/pm/PARA-PM-2.md`); se acepta con los tres guiones corridos enteros sobre el SHA nuevo, cada sabotaje en ROJO, y `anclas_perdidas.py` de vuelta a 6; fuera de esas cuatro líneas, los archivos de la Técnica no se tocan. 2) `sabotaje_sufijos1.sh`, que lleva como dato de `sufijo_otra1` la siguiente operación con su propio sufijo guardado: entra sin el aviso de la anterior y con su sufijo en el campo (su rojo: `pintarSufijo` que esconde el aviso sólo cuando el campo entra vacío). 3) los demás vencidos míos, uno por pieza. Próxima D: D246. Lecciones: antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que autoriza D243 (b); subagentes hasta esfuerzo alto y sin consejero.
