# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D245 (a): entregada en `e17c11e`. Las tres pruebas que pasaban por el semáforo sin mirar `success` ahora lo miran. Con un `raise` dentro del `try` del semáforo dan rojo 36 de las 38 pruebas que lo llaman; las otras 2 son `xfail` y quedan `xfailed`, no verdes. Sólo pruebas. Nada para decidir

| qué | SHA |
|---|---|
| base (informe de SABOTAJE-SUFIJOS1) | `1215a8a` |
| pruebas. **Lo que se entrega** | `e17c11e` |
| unión con tu rama hasta `3195a8c` (sólo `docs/pm/`) | `19dcd11` |
| informe | el commit siguiente |

`producto +0/−0`. `arnés +6/−2` en `tests/test_punta_a_punta1.py`,
`tests/test_generar_maria_txt.py` y `tests/test_cobro_corte1.py`.

Leí tu veredicto: SABOTAJE-SUFIJOS1 y D243 (b) aceptadas, D246 (b) decidida.
Sigo con D246 (b).

## Decisiones

Ninguna nueva. Próxima D: D247.

**Lo único que puede no gustarte:** tu criterio dice «ninguna prueba que
llama al semáforo queda verde». Dos quedan `xfailed` (ver «Notas»). Es lo
mismo que mediste vos (`10 failed` y los `2 xfailed` siguen). Si lo querés
cerrado, es otra pieza: decímelo.

## Lo que cambió

Una afirmación por sitio, después de la del 200 que ya estaba.

`tests/test_cobro_corte1.py` (de la Técnica), el diff entero del archivo:

```diff
@@ -531,9 +531,11 @@ def test_con_el_tope_lleno_se_valida_y_se_baja_lo_ya_contado(cuenta):
            ops_used_this_period=15, extra_ops_remaining=0)
 
     assert c.post("/generate_maria/avisos", json=_pedido()).status_code == 200
-    assert c.post("/api/validate/smart", json={"items": [
+    semaforo = c.post("/api/validate/smart", json={"items": [
         {"descripcion": "Lona de PVC", "cantidad": 1, "valor_unitario": 10, "peso_unitario": 1}]}
-    ).status_code == 200
+    )
+    assert semaforo.status_code == 200
+    assert semaforo.json().get("success") is True, semaforo.text
     assert c.get(r.json()["download_url"]).status_code == 200
     # Volver a generar la operación ya contada, igual o corregida, sale.
     assert _generar(c, operacion_id=oid).status_code == 200
```

La respuesta pasa a una variable para poder mirarla dos veces; el pedido y la
afirmación del 200 son los mismos.

`tests/test_generar_maria_txt.py:800`
(`test_sbt_flujo_completo_desde_dashboard`):
`assert val.json().get("success") is True, val.text`.

`tests/test_punta_a_punta1.py:284` (`_Pantalla.revisar`, por donde pasan las
10 pruebas del archivo que llaman al semáforo):
`assert r.json().get("success") is True, r.text[:400]`.

## Resultado

El sabotaje es una línea, `raise RuntimeError("sabotaje")`, al principio del
`try` del semáforo (`proyecto_maria/main.py:4531`), sobre un worktree
descartable. Los 11 archivos son los de `tests/` que llaman a
`/api/validate/smart`. Qué prueba lo llama lo medí con una corrida aparte que
anota el nombre de la prueba desde adentro del semáforo: son 38.

| sobre | qué | salida |
|---|---|---|
| `1215a8a` (base) | los 11 con el `raise` | `26 failed, 556 passed, 2 xfailed`. De las 38 que llaman, 10 **verdes** y 2 `xfailed` |
| `e17c11e` | los tres archivos, sin sabotaje | `166 passed, 2 xfailed`, `rc=0` |
| `e17c11e` | los 11 con el `raise` | `36 failed, 546 passed, 2 xfailed`. De las 38, 36 rojas, 0 verdes, 2 `xfailed` |

Las 10 que pasaron a rojo: 8 de `test_punta_a_punta1`, 1 de
`test_generar_maria_txt`, 1 de `test_cobro_corte1`. Las 10 dan el mismo
texto, el de la afirmación nueva:

```
AssertionError: {"success":false,"detail":"sabotaje"}
assert False is True
```

Ninguna prueba dio rojo sin llamar al semáforo («rojas que no llaman al
semáforo: []»).

## Notas (ninguna pide decisión)

- **Las dos `xfail(strict=True)` de `test_punta_a_punta1.py`**
  (`test_pdf_de_punta_a_punta_da_el_archivo_real_sin_cambios`, `:442`, y
  `test_subitems_dan_la_referencia_de_la_factura_del_archivo_real`, `:524`)
  pasan por `revisar`. Con el `raise` fallan antes, en la afirmación nueva,
  y pytest las cuenta `xfailed` igual que sin sabotaje: no distinguen. No
  tiene arreglo barato (`raises=AssertionError` tampoco distingue: su falla
  esperada también es una afirmación). Las otras 8 del mismo archivo, que
  pasan por la misma función, sí dan rojo.
- **Fuera de estos tres archivos, 22 de las 26 pruebas dan rojo de rebote.**
  Con el `raise`, las de `test_catalogo_ncm1`, `test_devolucion2_maria5_ncm`,
  `test_maria1b_controles`, `test_maria1b_devolucion`,
  `test_maria5_devolucion`, `test_separadores1c` y `test_separadores1d`
  fallan con `KeyError: 'advertencias'` o `KeyError: 'errores'`: leen una
  clave que la respuesta de error no trae. Sólo las 4 de `test_subitems1`
  y las 10 de esta pieza miran `success`. Hoy alcanza; una prueba nueva que
  lea con `.get("errores")` vuelve a abrir el agujero. Va como línea
  propuesta para la cola.

## `/code-review high`

Sobre `1215a8a..e17c11e`. Ningún defecto. Volvió a medir por su cuenta: los
tres archivos con el `raise` `10 failed, 156 passed, 2 xfailed`; en los 11,
38 llegan al semáforo, 36 fallan, 2 `XFAIL`. Tres observaciones bajas:

| observación | qué hice |
|---|---|
| las dos `xfail` absorben la afirmación nueva | cierto: primera nota |
| la misma afirmación queda copiada en cuatro archivos con dos formas (`["success"]` en `test_subitems1.py:103`, `.get("success")` en las tres nuevas) | cierto. No la junté: un ayudante común iría en `tests/conftest.py` o tocaría más de `test_cobro_corte1.py`, los dos de la Técnica y fuera de lo que autorizaste. Línea propuesta para la cola |
| los otros siete archivos dan rojo de rebote y nada obliga a una prueba nueva a mirar `success` | cierto, lo medí: segunda nota y la misma línea de la cola |

Revisión adversarial y `/security-review`: no corridas, las eximiste para
esta pieza.

## Comandos

```bash
VENV=/ruta/a/tu/venv
git diff 1215a8a e17c11e -- tests/test_cobro_corte1.py     # el diff de «Lo que cambió»: 4 líneas más, 2 menos
git diff 1215a8a e17c11e --stat | tail -1                   # 3 files changed, 6 insertions(+), 2 deletions(-)
git worktree add -q --detach /tmp/wt-d245 e17c11e && cd /tmp/wt-d245
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
PT="env -u DATABASE_URL -u ENVIRONMENT $VENV/bin/python -m pytest -q --no-cov -p no:cacheprovider --timeout=120"
$PT tests/test_punta_a_punta1.py tests/test_generar_maria_txt.py tests/test_cobro_corte1.py | tail -1
#   166 passed, 2 xfailed   (1 min 20 s)
sed -i 's|^        items_data = body.get("items", \[\])$|        raise RuntimeError("sabotaje")\n&|' proyecto_maria/main.py
git diff --stat | tail -1                                   # 1 file changed, 1 insertion(+)
$PT tests/test_catalogo_ncm1.py tests/test_cobro_corte1.py tests/test_devolucion2_maria5_ncm.py \
    tests/test_generar_maria_txt.py tests/test_maria1b_controles.py tests/test_maria1b_devolucion.py \
    tests/test_maria5_devolucion.py tests/test_punta_a_punta1.py tests/test_separadores1c.py \
    tests/test_separadores1d.py tests/test_subitems1.py | tail -1
#   36 failed, 546 passed, 2 xfailed   (2 min 25 s)
cd - && git worktree remove --force /tmp/wt-d245
```

Las corridas de pytest las hice con el `raise` puesto por un guion de Python
que exige que el ancla esté una sola vez. El `sed` de arriba lo probé aparte
sobre `e17c11e`: `1 file changed, 1 insertion(+)`, la línea queda justo
debajo del `try:` de `smart_validation` y `main.py` compila. No corrí pytest
con el `sed`: el archivo que deja es el mismo.

## Puertas

Sobre `e17c11e`, árbol limpio.

| puerta | salida |
|---|---|
| los tres archivos, sin sabotaje | `166 passed, 2 xfailed`, `rc=0` |
| los 11 archivos con el `raise` | `36 failed, 546 passed, 2 xfailed`; de las 38 que llaman al semáforo, ninguna verde |
| `anclas_perdidas.py e17c11e` | `perdida, una línea 6 guiones: 5`, `perdida, varias líneas 3 guiones: 2`: igual que en la base |
| guiones de sabotaje anclados en las líneas que cambié | ninguno (busqué en `scripts/testing/`) |
| `chequeo-6.py 1215a8a e17c11e` | abajo, `avisos: 0` |

**No corrido:** la suite entera (cambiaron tres archivos de pruebas y ningún
producto; corrí enteros los 11 que llaman al semáforo), `compileall`, las
pantallas, `e2e_maria.sh`, `smoke_friccion.sh`, `ataque_aislamiento.sh`,
Postgres (tampoco `cobro_corte1_postgres.py`, que importa ayudantes de
`test_cobro_corte1.py` que no toqué), los guiones de sabotaje, el adversario
y `/security-review`. Nada corrido sobre `19dcd11`: sobre `e17c11e` sólo suma
tus cinco archivos de `docs/pm/`.

## `chequeo-6`

```
chequeo-6 1215a8a..e17c11e: avisos para mirar, no un veredicto
producto +0/−0
arnés +6/−2
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

- **Bajo.** Las dos `xfail` no distinguen un semáforo roto (primera nota).
- **Bajo, anterior a esta pieza.** El semáforo sigue contestando 200 con
  `success: false` ante cualquier excepción (`main.py`, el `except` del final
  de `smart_validation`). Las pruebas ahora lo ven; el producto no cambió.
  Qué hace la pantalla con esa respuesta no lo miré: no era la pieza.
- Las 6 anclas perdidas que quedan son de mis vencidos.

## Líneas para COLA-LIMPIEZA

Una, propuesta:

> Pruebas del semáforo: un solo ayudante que llame a `/api/validate/smart` y
> afirme 200 y `success`. Hoy la afirmación está copiada en cuatro archivos
> (`test_subitems1.py:103`, `test_cobro_corte1.py:538`,
> `test_generar_maria_txt.py:800`, `test_punta_a_punta1.py:284`) y otras 22
> pruebas de siete archivos dan rojo ante un error tragado sólo por
> `KeyError`. Medido en D245 (a).

## Archivos de producto que toqué

Ninguno.

## Sigo con

D246 (b); después los 7 vencidos, primero `sabotaje_maria8.sh`.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `3195a8c`). Aceptadas: CUIT-GENERAR sobre `29327d2`, SABOTAJE-SUBITEMS1 sobre `bf6778e`, D243 (b) sobre `0dff850`, SABOTAJE-SUFIJOS1 sobre `afeae84`. **D245 (a) entregada sobre `e17c11e`** (base `1215a8a`; sólo pruebas, +6/−2; con el `raise` en el `try` del semáforo, 36 de las 38 pruebas que lo llaman dan rojo y 2 `xfail` quedan `xfailed`), sin veredicto todavía; si vuelve con devolución, va primero. Orden de la PM: 1) **D246 (b), pieza activa**: sacar el caso 11 de `scripts/testing/sabotaje_sufijos1.sh` y `tests/test_sufijos1.py::test_un_codigo_con_el_valor_vacio_no_se_genera`; se acepta con `sabotaje_sufijos1.sh` en 46 `ROJO`, `sabotajes/sufijos2.sh` entero en `ROJO` (es de la Técnica: se corre, no se toca), `anclas_perdidas.py` en 6 y `test_sufijos1.py` y `test_sufijos2.py` verdes. 2) los 7 vencidos míos, uno por pieza (maria8, maria1d, maria5, valor1b, doc1.py, maria7, guardar2). D244, D239 y «Holanda» esperan a Emi: no se tocan. Próxima D: D247. Lecciones: antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada; un dato nuevo de un caso no reusa un valor que otro control del mismo caso espera; antes de escribir el informe se trae la rama de la PM. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que una D autoriza; subagentes hasta esfuerzo alto y sin consejero.
