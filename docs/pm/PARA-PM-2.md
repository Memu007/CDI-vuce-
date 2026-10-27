# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## SUFIJOS-1, vuelta de la devolución: entregada a revisión (2026-10-27)

**Resultado:** lo probado es `45a3ea1`; el commit de este informe sólo
toca `PARA-PM-2.md`. Implementé la regla «al generar, lo que va
al TXT por producto es lo que muestra su celda», con H1 a H5 y D23 (c).
Cada uno tiene su caso y su sabotaje. El TXT sin sufijo propio sale idéntico
byte a byte al de `adfe707` en siete casos; el octavo da el mismo error en
las dos bases.

**Lo que decidís vos: nada para decidir.** Los supuestos reversibles van
abajo. D23 ya está contestada y no abro ninguna D nueva.

**Ojo con tu diff desde `97cd2fa`:** también trae SEPARADORES-1c
(`4f2045f`, `d5a3f58`, `9663ac6`). Esa pieza todavía no la entregué; la
informo apenas cierre esta.
- **Lo de esta vuelta:** `despachante.js`, `finalize.js`, `CHANGELOG.md` y
  los tres archivos de prueba de SUFIJOS-1.
- **Lo de SEPARADORES-1c:** `maria_generator.py`, `controles_maria.py`,
  `pdf_extractor.py`, `montos_ar.js`, `test_separadores1b.py`,
  `test_separadores1c.py` y `sabotaje_separadores1c.sh`.
- La suite de abajo corre sobre `45a3ea1`, así que incluye las dos.

| Pieza | SHA |
|---|---|
| Base de la vuelta (lo que revisaste) | `97cd2fa` |
| SEPARADORES-1c, sin entregar (producto, casos, sabotajes) | `4f2045f`, `d5a3f58`, `9663ac6` |
| Producto: lo que viaja es lo que muestra la celda (H1–H5, D23) | `252f04d` |
| Casos, pantalla y sabotajes de la vuelta | `b5d71ea` |
| Merge de tu rama (`842d68a`, sólo `NOW.md`) | `78648f3` |
| Casos: los sabotajes 35 y 47 apuntan a casos que los distinguen | `45a3ea1` |
| **SHA probado:** suite, compileall, casos y sabotajes | **`45a3ea1`** |

## Qué cambió

Los archivos de producto que toqué son
`proyecto_maria/static/v2/screens/despachante.js` y
`proyecto_maria/static/v2/screens/finalize.js`. El generador y el servidor
no cambiaron en esta vuelta.

- **La regla.** `sufijoDe` y `unidadesDe` ahora leen de lo que la celda
  muestra, no de `it.sufijo` ni de una propuesta pedida al generar.
  - Hay una sola función, `filaDe`, que arma lo que muestra cada fila.
  - La celda, los avisos y el pedido salen de ahí.
  - «Generar» ya no vuelve a pedir la propuesta: se quitó `listo()` en
    `onGenerate`.
- **H1.** Si el arancel no contestó, está consultando o hay más de 500
  productos, no viaja nada de la propuesta: ni sufijo ni unidad
  estadística.
  - La celda lo dice en su nota.
  - Los avisos lo dicen con «Ítem N: …».
  - Si el arancel se cae al entrar, el pedido va con `[null, null]` por
    producto.
- **H2.** La celda escrita guarda el sufijo de la operación de ese momento
  (`sufijo_op`). Si después cambia el de la operación, esa fila avisa en la
  celda y en los avisos. Al aceptarlo (volver a tocar la celda), el aviso
  se va.
- **H3 y H4.** Un producto en un grupo, o con sub-ítems, no lleva sufijo
  propio aunque tenga `it.sufijo` guardado. El grupo sale con el de la
  operación y los sub-ítems con el suyo.
- **H5.** Lo escrito en el sufijo de la operación gana.
  - La propuesta sólo agrega los códigos que faltan.
  - Si propone otro valor para un código ya escrito, no lo pisa y la fila
    lo avisa.
  - Ejemplo: con «AA(PROPIA SA)-CA00-» sale `AA(PROPIA SA)`, y la fila dice
    que el arancel proponía otro valor.
- **D23 (c).** Con el de la operación vacío y todos los productos con
  sufijo propio, aparece este aviso junto al botón, y no frena: «El sufijo
  de la operación está vacío: cada producto sale sólo con lo que pide el
  arancel de ARCA».

## Dos sabotajes que no distinguían

Con los casos de `b5d71ea`, el script dio 45 en rojo y 2 en verde: los
mutantes 35 y 47 daban lo mismo que el producto en esos casos. En
`45a3ea1` agregué un caso para cada uno; los dos casos fallan sólo con su
sabotaje.

- **35** (`filaDe` sin mirar si lo pintado está «ok»): el caso de antes
  cambiaba el único producto, y la propuesta vieja ya no coincidía igual.
  El nuevo tiene dos filas y cambia sólo la segunda. Mientras consulta, la
  primera tampoco lleva la propuesta.
- **47** (lo que viaja sale de lo que llegó y no de lo pintado): sólo se
  distingue si la propuesta del arancel llega y la pantalla todavía no la
  pintó, con lo pintado en «ok». Eso pasa sólo si los productos cambian sin
  repintar mientras la propuesta del cliente no llegó. El caso arma eso a
  mano: el arnés deja colgado el pedido del cliente (`frenarOtras`). Es un
  camino angosto; si te parece que no vale su caso, se retiran el caso y el
  sabotaje.

## Puertas sobre `45a3ea1`

| Puerta | Resultado (salida exacta) | Log |
|---|---|---|
| `tests/test_sufijos1.py` | `62 passed, 3 warnings in 7.37s` | — |
| `sabotaje_sufijos1.sh 45a3ea1` (47 sabotajes) | `OK: los 47 sabotajes dan rojo por la razón esperada`, `salida 0` | `sab_suf1b.log` |
| Suite completa, base limpia, sola | `13 failed, 3077 passed, 302 skipped, 2 xfailed, 94 warnings in 452.55s (0:07:32)` | `suite-45a3ea1.log` |
| `compileall -q proyecto_maria` | rc 0 | — |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` | `smoke252.log` |
| `pantalla_sufijos1.js` | `PANTALLA SUFIJOS-1 OK`; ancho a 390 px: 597, igual que la base | — |
| `pantalla_maria7.js` | `PANTALLA MARIA-7 OK` | `pm7.log` |
| `e2e_maria.js` | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.` | `e2e78.log` |
| TXT sin sufijo propio, `adfe707` contra `252f04d` | `cmp` sin diferencias en 7 casos; `op_vacio` da el mismo error en las dos | — |

Notas sobre dónde corrió cada puerta:
- **Pantalla, smoke y e2e.** Corrieron con la app levantada en `252f04d`.
  Su producto es idéntico al de `45a3ea1`: después sólo entraron `NOW.md`
  y casos.
- **TXT.** Los casos de la comparación de bytes son: lona, cuatro lonas,
  plástico y lona, grupo, sub-ítems, sufijo vacío y `None`, otro sufijo de
  la operación, y operación sin sufijo.
- **Pantalla nueva en el SHA viejo.** `pantalla_sufijos1.js` nueva no corre
  contra `97cd2fa`, porque ahí no existen la nota ni `avisos()`. Lo que
  distingue el defecto lo cubren los casos de pytest y los sabotajes.

**Rojos de la suite:** los 12 conocidos (`test_guardar1` y los 11 del
tope del plan) y uno nuevo que no es de esta vuelta:

- `tests/test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal`
  da `AssertionError: la subida normal dio 400 a los 30.0 s: {"detail":"No pudimos abrir el Excel: tardó demasiado. Probá con otro archivo."}`.
- **Falla igual en tu `842d68a`.** La corrí sola en un worktree limpio de
  tu rama, con la máquina quieta (load 0,90): `normal: 400 en 30.2 s`,
  `1 failed`.
- **Mi diff no toca nada de Excel.** No cambian la validación ni la
  prueba (`git diff 842d68a..45a3ea1 -- tests/test_excel2.py proyecto_maria/security` vacío).
- **Mi lectura:** es una prueba de tiempo. Ocho libros pesados entran al
  validador delante de la subida normal, que tiene un tope de 30 s, y en
  este contenedor de 4 núcleos no llega. En tu suite sobre `97cd2fa` no
  apareció. No la persigo porque está fuera de la tarea; si en tu máquina
  también falla, es de la cola de Excel.

**No se corrió:**
- **Subagentes adversariales y `/code-review`:** no hay cuota hasta el
  28/10 a las 18:00 UTC. En su lugar hice una autorrevisión del diff
  completo desde `97cd2fa`. La revisión independiente queda en vos.
- **`ataque_aislamiento.sh`:** esta vuelta no toca datos, sesión ni
  permisos.

## Comandos para reproducir

```bash
git fetch origin claude/dev-maria && git checkout 45a3ea1
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov -p no:randomly tests/test_sufijos1.py   # 62 passed
scripts/testing/sabotaje_sufijos1.sh 45a3ea1 <venv>                    # «OK: los 47 sabotajes dan rojo…»
git diff 97cd2fa..45a3ea1 -- proyecto_maria/static/v2/screens/        # lo de producto de esta vuelta
BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_sufijos1.js   # PANTALLA SUFIJOS-1 OK
```

## Supuestos reversibles

- **H2 y H5 también en los avisos.** Además de avisar en la fila, aparecen
  en la lista de avisos junto al botón, como H1. La devolución pedía la
  fila.
- **Grupos.** Un grupo sale siempre con el sufijo de la operación más lo
  que proponga el arancel. No le agregué una celda propia.
- **`sufijo_op`.** Es un campo nuevo por producto en el estado de la
  pantalla. No va al servidor ni al TXT.
- **Texto de D23.** Es el que propuse. Si una persona escribió el sufijo
  de algún producto, decir «sale sólo con lo que pide el arancel» queda
  impreciso.

## Riesgos

- **H2 sólo con lo nuevo.** Avisa sólo cuando quedó guardado `sufijo_op`.
  Una celda escrita antes de esta versión no avisa si cambia el de la
  operación. Severidad: baja, porque el estado es de la sesión de la
  pantalla.
- **Aceptar H2.** Hoy se acepta volviendo a tocar la celda; no hay un botón
  «aceptar».
- **Reintento del arancel.** Si el arancel no contestó, sólo se reintenta
  al volver a entrar a la pantalla. Mientras tanto no viaja nada de la
  propuesta, que es lo pedido, pero la persona tiene que salir y volver.
- **Avisos del botón.** Se refrescan después de pintar la pantalla. Entre
  medio, el botón puede mostrar los avisos anteriores por un instante. El
  pedido no se ve afectado, porque sale de lo pintado.
- **Aviso de H5 de más.** Si `limpiar_sufijo` deja un valor apenas distinto
  del que propone el arancel (espacios, signos), H5 puede avisar de más.
  Nunca pisa lo escrito.
- **Anotado, sin arreglar,** como pediste:
  - `combinar` con códigos repetidos o «AA00»;
  - el «-» final que siempre se agrega;
  - el BOM, que separa en JS y no en Python.

**Lo que sigue:** cierro SEPARADORES-1c, que ya está en la rama, con su
suite, su smoke y su informe. Ahí van a ir D24 y D25.

Última vuelta: Tue Oct 27 19:27:54 UTC 2026

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM, rutina horaria minuto 35. Entregada la vuelta de SUFIJOS-1, probada en 45a3ea1 (62 casos, 47 sabotajes, suite, compileall, smoke, pantallas, e2e y TXT idéntico a adfe707); nada para decidir. Sigo con SEPARADORES-1c (D21 b, en PARA-DEV-2.md; producto en 4f2045f/d5a3f58/9663ac6, 10 sabotajes en rojo; falta suite, smoke e informe con D24 miles en _numero_factura y D25 leer con más de 2 decimales). Sin cuota de subagentes ni /code-review hasta 28/10 18:00 UTC. Nunca main, sin push --force, sin datos reales del 24/10, nada se publica sin el «dale» de Emi para el SHA, sin Gemini en pruebas, subagentes hasta esfuerzo alto, sin advisor.
