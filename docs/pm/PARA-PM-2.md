# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Arnés de pantalla del 402: entregado en `899f9ee` (sólo pruebas)

| qué | SHA |
|---|---|
| base | `d49a436` |
| el arnés lanza el 402 como el producto, y el caso comprueba el motivo | `918a50d` |
| **entregado**: el arnés toma el 402 del cliente real (lo que encontró `/code-review`) | **`899f9ee45c0d`** |
| tu rama traída con `merge` (`18168c3`, después `47aacdb`) | `f36cc83`, `b558b66` |
| D149, cuatro guiones cortos, **adelantado** (abajo) | `f2709a2` |
| informe | el commit siguiente a `b558b66` |

**Resultado.** Los casos `-402` de la pantalla Listo ahora prueban el camino
de verdad: el plan vencido se avisa con el motivo que manda el servidor, no
como «Error de red».

- Antes el arnés lanzaba un error sin `code`, y el caso pasaba por el camino
  de la falla de red. Con el arnés viejo y el caso nuevo: `4 failed, 81 passed`.
- En `918a50d` el arnés lanzaba el 402 con la forma del producto, pero
  escrita a mano. `/code-review` marcó que eso se puede volver a desfasar.
- En `899f9ee` el arnés le pide el error al `CDI.api` real, una vez por
  corrida, y lo repite. Si el cliente cambia el código o el mensaje, los
  casos `-402` se ponen rojos.
- Producto: **+0/−0**.

**Nada para decidir.** Supuestos reversibles:

1. `899f9ee` toca `tests/front422_pantalla.js` (arnés de FRONT-422, mío): en
   el modo `api`, si `CDI.api` lanza, devuelve `{"lanza": {code, message}}`
   en vez de terminar con error. `test_front422.py` y `front422.sh` siguen
   igual (abajo).
2. Arreglé los cuatro hallazgos de `/code-review` dentro de la pieza en vez
   de mandarte una D: el primero era la causa de la pieza.
3. `f2709a2` se adelantó a «una pieza a la vez»: el hook de cierre pedía el
   árbol limpio y ya tenía esos cuatro guiones editados. No lo cuento como
   entregado: va con D149.

## Para reproducir

```bash
PY=<venv>/bin/python bash scripts/testing/sabotajes/despacho1c.sh 899f9ee   # 19 ROJO, «fallas: 0», ~2 min
PY=<venv>/bin/python bash scripts/testing/sabotajes/front422.sh 899f9ee     # 17 ROJO, «sabotajes con falla: 0», ~3 min
python -m pytest -q --no-cov tests/test_despacho1c.py tests/test_front422.py   # 118 passed
python docs/pm/herramientas/chequeo-6.py f36cc83 899f9ee                    # producto +0/−0, avisos: 0
```

## Puertas

| puerta | sobre | salida |
|---|---|---|
| arnés viejo + caso nuevo (el rojo de la pieza) | `d49a436` + el caso | `4 failed, 81 passed, 3 warnings in 5.02s` |
| arnés a mano, con `err.code = 'http_402'` en `app_v2.js` (el rojo del arreglo) | `918a50d` | `85 passed, 5 warnings in 4.86s`: no lo veía |
| `test_despacho1c.py` + `test_front422.py` | `899f9ee` | `118 passed, 3 warnings in 12.36s` |
| `despacho1c.sh` | `899f9ee` | 19 `ROJO`, `fallas: 0`, 2 min 13 s |
| `front422.sh` | `899f9ee` | `BASE  \| en verde`, 17 `ROJO`, `sabotajes con falla: 0` |
| suite completa, árbol limpio | `f36cc83` | `6077 passed, 110 skipped, 3 xfailed, 102 warnings in 1101.02s (0:18:21)` |
| chequeo-6 `d49a436 918a50d` | | `producto +0/−0`, `arnés +17/−6`, historia vacío, `avisos: 0` |
| chequeo-6 `f36cc83 899f9ee` | | `producto +0/−0`, `arnés +35/−10`, historia vacío, `avisos: 0` |

Los rojos del 402 en `despacho1c.sh`, copiados:

```
ROJO  | el plan vencido no avisa que no se guardó: dice «FAILED tests/test_despacho1c.py::test_ninguna_falla_deja_un_exito_a_la_vista[listo-con-cliente-402]»
ROJO  | el plan vencido se avisa como una falla de red: dice «'detalle': 'Error de red»
ROJO  | el plan vencido no dice el motivo del servidor: dice «'detalle': 'Plan vencido»
ROJO  | el cliente no marca el plan vencido con su código: dice «'detalle': 'Error de red»
ROJO  | el cliente lanza el plan vencido sin el motivo del servidor: dice «'detalle': 'payment_required'»
```

Los dos sabotajes que pediste son el segundo y el tercero: `err.code ===
'payment_required'` por `false`, y `err.message` por `err.motivo`. Los dos
últimos son nuevos y sabotean `app_v2.js`. El patrón de «aprender el catálogo
no avisa un 400» quedó al día (`ok: res.ok,`): en `d49a436` el guion daba 2
`ROTO`.

**xlwt.** Instalado en mi venv. La suite pasó de `5832 passed, 355 skipped`
(`f45243a`) a `6077 passed, 110 skipped`: 245 casos más corren.

**No corrido.**

- La suite completa no se repitió sobre `899f9ee`. Después de `f36cc83`
  cambiaron cuatro archivos de pruebas (los dos arneses, `test_despacho1c.py`
  y `despacho1c.sh`); nadie más usa esos arneses, y sus dos archivos de
  prueba corrieron sobre `899f9ee`. El merge `b558b66` trae sólo `docs/pm/`.
- Smoke y ataque de aislamiento: no hay backend tocado.
- `/security-review`: no hay producto tocado.

## Revisión

| quién | hallazgo | qué hice |
|---|---|---|
| adversario Sonnet, esfuerzo medio | sin hallazgos altos ni medios | |
| ídem, bajo | el `CDI.api` real además abre `CDI.confirm`; el arnés de Listo no lo modela | queda: es otra pantalla, fuera de la pieza |
| ídem, bajo | `MOTIVO_402` repetido en JS y Python | arreglado en `899f9ee`: queda sólo en Python |
| `/code-review high` (hereda el modelo de la sesión) | 1. el 402 del arnés es una copia a mano de lo que lanza `CDI.api` | arreglado: lo toma del cliente real; dos sabotajes nuevos lo muestran |
| ídem | 2. dos sabotajes esperaban el texto entero del producto | arreglado: fragmento corto del detalle. No puse el `FAILED …[caso]`: es el mismo en los tres sabotajes del 402 y no distingue el motivo |
| ídem | 3. `MOTIVO_402` duplicado | arreglado |
| ídem | 4. un sabotaje que no cambia nada salía como `VERDE` | arreglado: sale `ROTO` |

Mientras arreglaba el 1 se me pisó un nombre (`opciones`) dentro del arnés y
el 402 salía como falla de red. Lo mostraron los mismos cuatro casos `-402`
en rojo; corregido antes del commit.

## Archivos tocados

Sólo pruebas: `tests/despacho1c_pantalla.js`, `tests/test_despacho1c.py`,
`tests/front422_pantalla.js`, `scripts/testing/sabotajes/despacho1c.sh`.

## D149: lo adelantado en `f2709a2` (no es la entrega)

| guion | sobre | resultado |
|---|---|---|
| `maria1b.sh` | `918a50d` | 34 `ROJO`, `sabotajes con falla: 0`, 535 s |
| `entradas1.sh` | `918a50d` | 32 `ROJO`, `sabotajes con falla: 0`, 853 s |
| `abuso1.sh` | `f2709a2` | 34 `ROJO`, `sabotajes sin rojo: 0`, 920 s |
| `catalogolargo1.sh` | `f36cc83` | 7 `ROJO`, **1 `ROJO?`**, 1 `SALTO \| sin PG_URL`, `fallas: 1` |

El `ROJO?` de `catalogolargo1` es el sabotaje viejo, no el producto. Saca el
tope del historial y espera rojo también en guardar-uso, pero guardar-uso
tiene el tope dos veces (`main.py:10479` pasa por
`catalog_svc.texto_para_guardar`). Lo comprobé una vez, en un worktree
aparte: con los dos controles quitados, `test_guardar_uso…[2001]` y
`[nfc-que-crece]` se ponen rojos (`7 failed, 6 passed`). Lo arreglo dentro de
D149: el sabotaje pasa a ser sólo del historial.

Faltan de D149: `despacho1b`, `cobro_mp2`, `sesion1`, y CR8 (`datos1.sh`
ancla tres sabotajes en comentarios).

## Riesgos

- Bajo: en el modo `api` de `front422_pantalla.js`, un error inesperado de
  `CDI.api` ya no imprime la traza; el caso igual queda rojo, con menos
  detalle.
- Bajo: el arnés de Listo no modela el modal de `CDI.confirm` del 402.

## D167

Desde tu veredicto de las 21:59 compacté dos veces. Lo que achiqué: la lista
de tareas vieja, y los resúmenes citan logs y archivos por ruta en vez de
copiarlos; no releo este archivo entero. Lo que no puedo achicar: después de
cada compactación se vuelven a cargar la lista de comandos y las definiciones
de herramientas. No tengo forma de medir cuántos tokens son; no invento el
número.

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn, cabeza 47aacdb), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. Arnés de pantalla del 402 entregado en 899f9ee (informe en el commit siguiente a b558b66), esperando veredicto. Sigue D149 (a) con CR8: arreglar el sabotaje viejo de catalogolargo1, aplicar el parche de despacho1b, cobro_mp2 y sesion1, y reanclar datos1.sh en código; después D145 (a). Próxima D libre: D168. Los detalles están en PARA-PM-2.md: el resumen los cita, no los copia. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; las Devs no usan el consejero.
