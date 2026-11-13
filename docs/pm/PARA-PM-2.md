# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D226 (a): entregada en `bdb8130` (sólo arnés). Nada para decidir

D223 + D224 sigue entregada en `32f09ba` y espera tu veredicto: su informe
está en `git show 9abd828:docs/pm/PARA-PM-2.md`. Tu rama sigue en `72c297c`
(la miré antes de subir): no hubo nada nuevo que traer. Sigo con el lugar 3,
**`valor1`**.

| qué | SHA |
|---|---|
| base (mi informe anterior) | `9abd828` |
| las tres pantallas sin ruta fija: **el que se entrega** | `bdb8130` |
| informe | el commit siguiente |

**Resultado.**

- `pantalla_catalogo_ncm1.js`, `pantalla_excel1.js` y `pantalla_maria1b.js`
  abren el navegador con `chromium.launch()`, como las otras 24 que ya lo
  hacían. Una línea por archivo.
- Antes (`9abd828`), en el corredor de mi contenedor: las tres `ROJA` con
  `browserType.launch: Failed to launch chromium because executable doesn't exist at /opt/pw-browsers/chromium-1194/chrome-linux/chrome`.
- Ahora (`bdb8130`): las tres `verde`; el corredor entero da
  `resumen: 30 verdes, 0 rojas` (884 s).
- Producto **+0/−0**; arnés +3/−3.

## Decisiones

Ninguna.

## Supuestos (reversibles)

Ninguno: el diff es la línea que pediste, tres veces.

## Para reproducir

```bash
# raíz del repo; PY = python de un venv con requirements.txt; hace falta node
# y el Playwright del contenedor (PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers).

# 1) Las tres:
SOLO="catalogo_ncm1 excel1 maria1b" env -u DATABASE_URL -u ENVIRONMENT PY=$PY \
  bash scripts/testing/correr_pantallas.sh bdb8130 /tmp/d226
#   → `verde catalogo_ncm1 rc=0`, `verde excel1 rc=0`, `verde maria1b rc=0`
#   → `resumen: 3 verdes, 0 rojas`

# 2) El rojo de antes: el mismo comando con 9abd828 en vez de bdb8130
#   → `resumen: 0 verdes, 3 rojas: catalogo_ncm1 excel1 maria1b`
#   (sólo donde no existe /opt/pw-browsers/chromium-1194; en el tuyo, si
#   existe, da verde y eso no dice nada del cambio)

# 3) El corredor entero, ~15 minutos:
env -u DATABASE_URL -u ENVIRONMENT PY=$PY bash scripts/testing/correr_pantallas.sh bdb8130 /tmp/d226-todas
#   → `resumen: 30 verdes, 0 rojas`
```

## Puertas (sobre `bdb8130`)

| puerta | salida |
|---|---|
| las tres en el corredor, antes (`9abd828`) | `resumen: 0 verdes, 3 rojas: catalogo_ncm1 excel1 maria1b`, sale 1 |
| las tres en el corredor | `verde catalogo_ncm1 rc=0 … OK: pantalla CATALOGO-NCM-1`; `verde excel1 rc=0 … OK: pantalla EXCEL-1`; `verde maria1b rc=0 … OK: pantalla MARIA-1b`; `resumen: 3 verdes, 0 rojas`, sale 0 |
| el corredor entero | `resumen: 30 verdes, 0 rojas`, sale 0, 884 s |
| `scripts/testing/anclas_perdidas.py bdb8130` | sale 0; ninguna línea nombra estas tres pantallas |

`chequeo-6.py 9abd828 bdb8130`, entero:

```
chequeo-6 9abd828..bdb8130: avisos para mirar, no un veredicto
producto +0/−0
arnés +3/−3
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

Sin sabotaje propio: no hay caso nuevo ni cambiado, y ningún guion de
sabotaje ni la CI corren estas tres pantallas (`grep` vacío). El rojo con el
arreglo revertido es la primera fila de la tabla.

Archivos de producto tocados: ninguno.

## Hallazgos de la autorrevisión

Un adversario (`adversario-sonnet-medio`: Sonnet, esfuerzo medio; pieza
chica) y `/code-review high` (sus revisores heredan Fable). Sin
`/security-review`: sólo arnés.

| # | quién | qué dice | qué hice |
|---|---|---|---|
| 1 | adversario | Ningún defecto. Corrió las tres en el corredor (3 verdes) y leyó los tres archivos: todo lo que comprueban es DOM, no depende de qué binario abre. | Nada. |
| 2 | code-review | `chromium.launch()` necesita `PLAYWRIGHT_BROWSERS_PATH` heredada: sin ella busca en `~/.cache/ms-playwright` y falla. Y abre el `chromium_headless_shell`, no el Chrome entero de antes. | Cierto, y es la misma condición de las otras 24 pantallas que ya abrían así. Riesgo anotado abajo. |
| 3 | code-review | Las tres no leen `CHROMIUM`, que el corredor exporta y documenta (`correr_pantallas.sh:10`, `:24`). Sólo la leen `pantalla_cliente1.js` y `pantalla_destino1.js`; `pantalla_borrador1.js:41` tiene la ruta fija. | No es de esta pieza: pediste `launch()` sin ruta. Propuesta para la cola, abajo. |
| 4 | code-review | Las tres siguen con `require('/opt/node-tools/node_modules/playwright')`. | Comprobado con `grep`: 12 pantallas lo piden con esa ruta y 18 con `require('playwright')`. No lo toqué: no lo pediste y en los dos contenedores resuelve. Propuesta para la cola. |
| 5 | code-review | `pantalla_maria1b.js:58`: espera fija de 1500 ms después de `CDI.semaforo.refresh()`. Ya estaba. | Cola, abajo. |
| 6 | code-review | `pantalla_excel1.js:36`: espera fija de 300 ms y lee `#toastHost` una vez, con `.catch(() => '')`. Ya estaba. | Cola, abajo. |

El adversario dijo además que el pie del commit debería nombrar otro modelo:
no hay regla que lo pida, descartado.

**Líneas que propongo para `COLA-LIMPIEZA.md`** (no la toco):

- `scripts/testing/pantalla_*.js`: tres maneras de abrir el navegador
  (`launch()` en 27, `process.env.CHROMIUM || …` en `cliente1` y `destino1`,
  ruta fija en `borrador1.js:41`) y dos de pedir Playwright (12 con
  `/opt/node-tools/…`, 18 con `require('playwright')`). El corredor exporta
  `CHROMIUM` y 27 pantallas no la leen: unificar o dejar de exportarla.
- `scripts/testing/pantalla_maria1b.js:58` y `:65`: esperas fijas (1500 y
  300 ms); la primera puede esperar la respuesta de `/api/validate/smart`.
- `scripts/testing/pantalla_excel1.js:36`: espera fija de 300 ms antes de
  leer `#toastHost` una sola vez.

## Qué no corrí y riesgos

- **Ni pytest, ni `compileall`, ni `smoke_friccion.sh`, ni
  `ataque_aislamiento.sh`, ni `e2e_maria.sh`**: la pieza no toca producto ni
  `tests/`.
- **Verde sólo en mi contenedor**, que es la puerta que pusiste. En uno con
  `PLAYWRIGHT_BROWSERS_PATH` sin definir, o sin el navegador de la versión del
  Playwright instalado, las tres dan rojo al abrir, igual que las otras 24
  (hallazgo 2). No lo probé en otro contenedor.
- **Las tres corren ahora en el navegador sin ventana de Playwright**
  (`chromium_headless_shell`), no en el Chrome entero de la ruta vieja. Lo
  que comprueban es DOM y dio lo mismo; no comparé capturas.
- **El rojo de antes depende del contenedor**: donde exista
  `/opt/pw-browsers/chromium-1194`, `9abd828` da verde.
- Las esperas fijas de `maria1b` y `excel1` siguen (hallazgos 5 y 6).

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn, cabeza 72c297c, ya integrada), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. Aceptadas: D218, D219 y PANTALLAS-MARIA. Entregadas y esperando veredicto: D223 + D224 en 32f09ba (informe en 9abd828) y D226 (a) en bdb8130 (sólo arnés, +3/−3; corredor entero 30 verdes, 0 rojas). Nada abierto para decidir. Ya decididas: D221 (b), D222 (a), D223 (a), D224 (a), D225 (a), D226 (a). Orden de la PM, una pieza a la vez: la que arranco ahora es valor1 (retirar el 13 y el 24 de sabotaje_valor1.sh y reanclar en código el 10, comentario en la línea 108, y el 28, comentario al final de la línea 187; puerta: valor1 entero da 29 ROJO y sale 0, y su línea sale de sabotajes-conocidos.txt). Después: AJUSTE-BORRADOR (producto en static/v2: primero un caso de pantalla en rojo; corre e2e_maria.sh); CUIT-PERFIL (D225: producto con datos, revisión fuerte; primero el rojo de hoy; PUT /api/user/profile rechaza un CUIT inválido y la pantalla muestra el error; decir qué pasa con los perfiles ya guardados sin cambiar datos; orden1, validacion1, cobro_corte1 y cobro_mp1_v2 pasan a _cuit_perfil.js; pantalla_orden1.js es mía para esa pieza); y los vencidos de sabotajes-conocidos.txt, uno por pieza. No son míos: maria7, maria1c, correr_pantallas.sh, forzar_arranque.js, forzar_orden1.js. Próxima D libre: D227. Una devolución de la PM o la tarea de comparación van primero. Los detalles están en PARA-PM-2.md: el resumen los cita, no los copia. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; las Devs no usan el consejero.
