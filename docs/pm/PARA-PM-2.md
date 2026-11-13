# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## `valor1` (29 sabotajes, anclas en código): entregada en `0334800` (el trabajo es de `b1a70d1`; sólo arnés). Nada para decidir

Traje tu rama (`ccd4035`) con `merge`. Mi canal no cambió; vi el acta de
D226 (aceptada). D223 + D224 sigue entregada en `32f09ba`, con su informe en
`git show 9abd828:docs/pm/PARA-PM-2.md`, y el de D226 en
`git show a88f62f:docs/pm/PARA-PM-2.md`. Sigo con el lugar 4,
**AJUSTE-BORRADOR**.

| qué | SHA |
|---|---|
| base (mi informe anterior) | `a88f62f` |
| el guion con 29 sabotajes y su línea fuera de `sabotajes-conocidos.txt` | `b1a70d1` |
| tu rama `ccd4035` integrada: **el que se entrega** | `0334800` |
| informe | el commit siguiente |

El guion entero corrió sobre `b1a70d1`. Entre `b1a70d1` y `0334800`, fuera de
`docs/`, sólo cambia `tests/test_excel2d.py` (de la Técnica): ni el producto,
ni `tests/test_valor1.py`, ni el guion. Sobre `0334800` corrí la prueba corta
(`75 passed`) y `anclas_perdidas.py`.

**Resultado.**

- `sabotaje_valor1.sh` entero: **29 `ROJO`, 0 `FALLA`, sale 0** (665 s),
  `OK: los 29 sabotajes dan rojo por la razón esperada`.
- Salieron el 13 (`ajuste_mal_escrito_vacio`) y el 24 (`mal_escrito_se_borra`).
- El 10 (`descuento_solo`) ancla en la línea de código que sigue al
  comentario, `if (ofrece) ofrece.hidden = !(descuento > 0)`, y le antepone la
  misma línea de antes. Da `2 failed`.
- El 28 (`respuesta_vieja`), **que ahora es el 26**, ya no borra la línea con
  su comentario: cambia `if (seq !== avisosSeq) return;` por
  `if (false) return;`. Da `1 failed`.
- Los comentarios `# N.` quedaron de 1 a 29: del viejo 14 en adelante el
  número bajó uno, y del viejo 25 en adelante, dos.
- La línea de `sabotaje_valor1.sh` salió de `sabotajes-conocidos.txt`.
- Producto **+0/−0**; arnés +21/−30.

## Decisiones

Ninguna.

## Supuestos (reversibles)

1. **Renumeré los comentarios y el total del mensaje final** (31 → 29). No lo
   pediste; sin eso el guion decía «los 31 sabotajes» con 29.
2. **El 26 cambia la condición en vez de borrar la línea.** Mismo efecto (la
   respuesta vieja ya no se descarta); el comentario del final de la línea
   queda donde estaba y el ancla es sólo código.
3. **La baja de la línea en `sabotajes-conocidos.txt` va en el mismo commit
   que el guion.** Las dos anteriores (`a2ec4bc`, `e4308e1`) fueron commits
   `docs:` aparte; acá es la misma puerta y la dejé junta.

## Para reproducir

```bash
# raíz del repo en 0334800 (o en b1a70d1: para esto es lo mismo); VENV = carpeta de un venv con requirements.txt; hace falta node.

# 1) El guion entero, ~11 minutos:
env -u DATABASE_URL -u ENVIRONMENT bash scripts/testing/sabotaje_valor1.sh 0334800 $VENV
#   → 29 líneas `ROJO`, ninguna `FALLA`
#   → `OK: los 29 sabotajes dan rojo por la razón esperada`, sale 0

# 2) Ninguna ancla perdida ni en comentario:
$VENV/bin/python scripts/testing/anclas_perdidas.py 0334800 | grep -c sabotaje_valor1.sh
#   → `0`
grep -nE "^ +[\$'\"].*( #|//) +[[:alnum:]ÁÉÍÓÚáéíóú]" scripts/testing/sabotaje_valor1.sh
#   → vacío

# 3) La línea ya no está:
grep -c 'sabotaje_valor1.sh ' docs/pm/herramientas/sabotajes-conocidos.txt
#   → `0`
```

## Puertas

| puerta | sobre | salida |
|---|---|---|
| `sabotaje_valor1.sh` entero | `b1a70d1` | 29 `ROJO`, 0 `FALLA`, `OK: los 29 sabotajes dan rojo por la razón esperada`, sale 0, 665 s |
| `descuento_solo` (reanclado) | `b1a70d1` | `ROJO   descuento_solo: … 2 failed, 73 passed` |
| `respuesta_vieja` (reanclado) | `b1a70d1` | `ROJO   respuesta_vieja: … 1 failed, 74 passed` |
| `anclas_perdidas.py` | `b1a70d1` y `0334800` | sale 0; `101 guiones, 2451 anclas medidas` (antes 2453); ninguna línea de `sabotaje_valor1.sh` |
| el `grep` de la familia D168 sobre el guion | `b1a70d1` | vacío |
| `tests/test_valor1.py` | `0334800` | `75 passed, 3 warnings in 20.36s` |

`chequeo-6.py a88f62f b1a70d1`, entero:

```
chequeo-6 a88f62f..b1a70d1: avisos para mirar, no un veredicto
producto +0/−0
arnés +21/−30
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

Con la unión (`a88f62f 0334800`) da lo mismo salvo `arnés +32/−38`: la
diferencia es `tests/test_excel2d.py`, de la Técnica.

Sin sabotaje propio: el guion es el sabotaje. Archivos de producto tocados:
ninguno.

## Hallazgos de la autorrevisión

Un adversario (`adversario-sonnet-medio`: Sonnet, esfuerzo medio; pieza
chica) y `/code-review high` (sus revisores heredan Fable). Sin
`/security-review`: sólo arnés.

| # | quién | qué dice | qué hice |
|---|---|---|---|
| 1 | adversario | Ningún defecto. Las 29 anclas están en `b1a70d1` las veces que el guion declara (corrió una copia con pytest anulado: mide anclas, no rojos); ninguna toca un comentario; las pruebas nombradas en `caso` son las mismas 28 antes y después; nada vivo cita estos sabotajes por número. | Nada. |
| 2 | code-review | Ningún defecto del cambio. Corrió el guion entero por su cuenta sobre `b1a70d1`: 29 `ROJO`, sale 0. La mutación del 13 retirado, a mano, da 5 failed (los cuatro `[…-ajusteDelPedido]` de `test_separadores1b.py` y la prueba del pedido): la cobertura existe. | Nada. No es una corrida independiente: corre dentro de mi sesión. |
| 3 | code-review | El guion no comprueba que la base esté en verde antes de sabotear (ya estaba): sin node, toda prueba de pantalla da `FAILED` y `caso` anota `ROJO` sin que la mutación distinga nada. | No es de esta pieza. En mis corridas la base está verde (`75 passed`, y 17 de los 29 casos dan `1 failed, 74 passed`). Cola, abajo. |
| 4 | code-review | Sin el 24, la mitad «y a la vista» de `test_un_numero_que_el_campo_no_entiende_queda_marcado_y_a_la_vista` no tiene negativo, y las guardas de `finalize.js:451` y `:454` quedan sin sabotaje. | Es lo que decidiste en D222 (a). Lo cubre o lo retira AJUSTE-BORRADOR, que arranco ahora. Riesgo, abajo. |
| 5 | code-review | El negativo de «lo mal escrito viaja tal cual» vive sólo en el sabotaje 5 de `sabotaje_separadores1b.sh` (de la Técnica); nada lo ata a `test_valor1.py` salvo el mensaje del commit. | Es D221 (b). Riesgo, abajo. |
| 6 | code-review | El total y los números se llevan a mano: sacar dos sabotajes obligó a renumerar 17 comentarios. | Cierto. No lo cambié: no lo pediste. Cola, abajo. |

**Líneas que propongo para `COLA-LIMPIEZA.md`** (no la toco):

- `scripts/testing/sabotaje_valor1.sh`: correr la prueba una vez sin sabotear
  y cortar si no está verde, como `sabotaje_separadores1b.sh`; hoy un rojo de
  entorno (sin node) cuenta como `ROJO`.
- `scripts/testing/sabotaje_valor1.sh`: contar los casos en `caso` en vez de a
  mano (misma línea que ya tiene `sabotaje_maria3.sh`).

## Qué no corrí y riesgos

- **Ni pytest entero, ni `compileall`, ni `smoke_friccion.sh`, ni
  `ataque_aislamiento.sh`, ni `e2e_maria.sh`**: la pieza no toca producto.
- **El guion entero no lo corrí sobre `0334800`**: corrió sobre `b1a70d1`, y
  lo que la unión cambia no lo usa (arriba).
- **`sabotaje_separadores1b.sh` no lo corrí** (es de la Técnica): que su
  sabotaje 5 cubre al 13 retirado lo confirmaste vos en D221 y lo volvió a ver
  el revisor aplicando la mutación a mano.
- **Las guardas de `finalize.js:451` y `:454` quedan sin sabotaje** hasta
  AJUSTE-BORRADOR (hallazgo 4).
- **Si `sabotaje_separadores1b.sh` se retira o vence**, lo mal escrito que
  viaja en el pedido queda sin negativo y ningún guion lo avisa (hallazgo 5).
- **Un rojo de entorno pasaría por `ROJO`** (hallazgo 3): al reproducir, en
  mi corrida el caso que más falla da `14 failed, 61 passed`; decenas de
  fallas en todos sería el entorno.

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn, cabeza ccd4035, ya integrada en 0334800), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. Aceptadas: D218, D219, PANTALLAS-MARIA y D226 (acta REPRODUCCION-D226-2026-11-13.md; todavía sin veredicto en mi canal). Entregadas y esperando veredicto: D223 + D224 en 32f09ba (informe en 9abd828) y valor1 en 0334800 (el trabajo es de b1a70d1; sólo arnés +21/−30; el guion entero da 29 ROJO y sale 0; su línea salió de sabotajes-conocidos.txt). Nada abierto para decidir. Ya decididas: D221 (b), D222 (a), D223 (a), D224 (a), D225 (a), D226 (a). Orden de la PM, una pieza a la vez: la que arranco ahora es AJUSTE-BORRADOR (producto en static/v2: primero un caso de pantalla en rojo sobre el código de hoy —ajuste mal escrito, borrador guardado, recargar, recuperar; el campo tiene que mostrar lo que el aviso nombra—; guardarBorrador en app_v2.js:1082, adoptarBorrador, guardas en finalize.js:451 y :454; si da rojo se arregla, sugerencia: sacar las dos guardas; si no reproduce se informa con la salida y las guardas van a la cola; corre e2e_maria.sh). Después: CUIT-PERFIL (D225: producto con datos, revisión fuerte; primero el rojo de hoy; PUT /api/user/profile rechaza un CUIT inválido y la pantalla muestra el error; decir qué pasa con los perfiles ya guardados sin cambiar datos; orden1, validacion1, cobro_corte1 y cobro_mp1_v2 pasan a _cuit_perfil.js; pantalla_orden1.js es mía para esa pieza); y los vencidos de sabotajes-conocidos.txt, uno por pieza. No son míos: maria7, maria1c, correr_pantallas.sh, forzar_arranque.js, forzar_orden1.js, pantalla_borrador1.js. Próxima D libre: D227. Una devolución de la PM o la tarea de comparación van primero. Los detalles están en PARA-PM-2.md: el resumen los cita, no los copia. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; las Devs no usan el consejero.
