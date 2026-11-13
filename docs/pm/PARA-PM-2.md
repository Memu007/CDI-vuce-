# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## PANTALLAS-MARIA: entregada en `e0d2770` (sólo arnés). Dos decisiones: D225 y D226

**Este informe reemplaza al de `c918f7e`, que subí mal**: lo commiteé en el
mismo comando que traía tu rama, sin leer tu `598919f`. Decía que tu rama no
tenía commits nuevos y que D223 y D224 seguían abiertas; las dos cosas ya eran
falsas. Acá está corregido. Lo técnico no cambió; se suma el corredor y D226
quedó reescrita.

Leído tu veredicto: D218 y D219 aceptadas; D223 (a) y D224 (a), una pieza
después de ésta; `maria7` y `maria1c` son de la Técnica.

| qué | SHA |
|---|---|
| base (mi informe anterior) | `166c46c` |
| los cuatro guiones vuelven a salir 0 | `0ec6343` |
| el CUIT del perfil, en un ayudante (`_cuit_perfil.js`) | `3e195de` |
| de la autorrevisión: token CSRF en el ayudante y los cuatro pesos en `maria5` (último cambio de los guiones) | `7ac0b4e` |
| tu rama integrada hasta `90b66c5`; trae el corredor de la Técnica: **el que se entrega** | `e0d2770` |
| informe | el commit siguiente |

Entre `7ac0b4e` y `e0d2770` mis cinco archivos no cambian
(`git diff 7ac0b4e e0d2770 -- scripts/testing/pantalla_{maria3,maria4,maria5,subitems1}.js scripts/testing/_cuit_perfil.js`
da vacío).

**Resultado.** Los cuatro, cada uno con servidor y base nuevos, sobre
`7ac0b4e`: `maria3` 8 `OK`, `maria4` 7, `maria5` 9, `subitems1` 10; ninguna
`FALLA`; los cuatro salen 0. Producto **+0/−0**; arnés +23/−8.

**En el corredor** (`scripts/testing/correr_pantallas.sh e0d2770`): las cuatro
salen `verde`, con los mismos `OK` (8, 7, 9, 10). Ninguna necesitó cabecera
`// corredor:`. El resumen, en mi contenedor:
`resumen: 25 verdes, 5 rojas: catalogo_ncm1 excel1 maria1b maria1c maria7`
(sale 1). Ninguna de las cinco es de esta pieza: cuatro son D226 y `maria7` es
de la Técnica.

**Ninguna causa es de producto**: no frené. Eran cuatro causas, no dos:

| causa | guiones | el rojo sobre `166c46c` |
|---|---|---|
| 1. Falta el CUIT del importador: «Generar» queda deshabilitado (`finalize.js:606`; la regla es de MARIA-1b, `controles_maria.py:260-268`) | `maria3`, `maria4` | `maria3`: `page.waitForResponse: Timeout 15000ms exceeded while waiting for event "response"` (línea 73). `maria4`: `FALLA: page.click: Timeout 30000ms exceeded.` esperando `#validatingGenerate`. Con una copia que imprime el estado del botón antes del clic, los dos: `DBG {"dis":true,"st":"1 error para corregir","iss":"Errores críticos\n· 1\nFalta el CUIT del importador.…` |
| 2. Falta el CUIT del despachante | `maria5`, `subitems1`, y `maria3` apenas se arregla la 1 | `FALLA: no se generó el TXT: {"detail":"Falta el CUIT del despachante (CDDTAGR): elegí el estudio en la operación o cargá uno en «Mi perfil», «Mis estudios». Sin él no se genera el TXT."}` |
| 3. `maria5` esperaba 25 kg en el primer ítem y MARIA-8 junta en un ítem los dos renglones de la misma posición y origen (`renglones_por_posicion`, `3fd9f2e`). Estaba tapada por la 2 | `maria5` | `FALLA: las 10 notebooks de 2,5 kg declaran 26.000` |
| 4. De entorno: la ruta fija `/opt/pw-browsers/chromium-1194/…` no existe en mi contenedor (hay `chromium` y `chromium-1243`) | los cuatro | `FALLA: browserType.launch: Failed to launch chromium because executable doesn't exist at /opt/pw-browsers/chromium-1194/chrome-linux/chrome` |

La 4 en tu contenedor no debe pasar: vos llegaste al rojo del CUIT, así que
ahí el navegador abre. `chromium.launch()` sin ruta es lo que usan otros 19
guiones.

**Te contradigo en la fecha.** «Desde MARIA-7 (24/10)» vale para la causa 2
(`67d5688`, `609ec52`) y la 3 (`3fd9f2e`). Para `maria3` y `maria4` no:
en `3dbfb4e` los dos cortan en el mismo paso con el mismo texto que hoy. No
busqué el primer commit rojo ni confirmé la causa en ese commit con la copia
que imprime el botón.

## Decisiones

**D225. El perfil guarda un CUIT de despachante con el dígito verificador
mal, y el TXT sale con él.** `PUT /api/user/profile` (`main.py:2428-2439`)
sólo pide 11 dígitos. El alta de un estudio sí llama a `cuit_valido`
(`main.py:7712-7714`) y el CUIT del importador también
(`controles_maria.py:260-268`). `cuit_valido('20999999998')` da `False`, y es
el que cargan `pantalla_orden1.js:112`, `pantalla_validacion1.js:126`,
`pantalla_cobro_corte1.js:180` y `pantalla_cobro_mp1_v2.js:24`. El adversario
generó un TXT con `CDDTAGR=20999999998`; yo leí el código y corrí
`cuit_valido`, no repetí su corrida. No sé qué hace MARIA al recibirlo. No
encontré el tema en `DECISIONS.md`, `NOW.md`, `COLA-LIMPIEZA.md` ni
`PREGUNTAS-DESPACHANTE.md`.

- (a) Pieza chica de producto: el perfil valida con `cuit_valido`, como los
  estudios. Los cuatro guiones de arriba pasan a un CUIT válido (dos son de
  la Técnica). La pieza decide qué pasa con un perfil ya guardado con CUIT
  inválido.
- (b) Riesgo anotado, o pregunta al despachante.

Recomiendo **(a)**, después de AJUSTE-BORRADOR: es lo que sale en el TXT, y
el producto ya tiene la regla escrita para los otros dos CUIT. En mis
guiones puse `20111111112`, que pasa `cuit_valido`: no dependen de lo que
decidas.

**D226. Cuatro guiones más tienen la ruta fija del navegador, y en mi
contenedor salen rojos en el corredor:** `pantalla_catalogo_ncm1.js:12`,
`pantalla_excel1.js:13`, `pantalla_maria1b.js:18`, `pantalla_maria1c.js:14`.
Los cuatro cortan al abrir: `FALLA: browserType.launch: Failed to launch
chromium because executable doesn't exist at
/opt/pw-browsers/chromium-1194/chrome-linux/chrome`. En el contenedor de la
Técnica abren (su corrida sobre `907e1ed` los dio verdes), así que detrás de
la ruta no hay otra causa conocida: es una línea por guion. El corredor ya le
pasa `CHROMIUM` a cada pantalla.

- (a) Una pieza chica mía: `catalogo_ncm1`, `excel1` y `maria1b` sin la ruta
  fija, y esas tres verdes en el corredor de mi contenedor. `maria1c` es de la
  Técnica: la línea la cambia ella dentro de INTERMITENTES.
- (b) Las cuatro a la Técnica, con el corredor.
- (c) A la cola.

Recomiendo **(a)**: mientras tanto, en mi contenedor el corredor no puede dar
«0 rojas» y hay que comparar por nombre. Retiro lo que dije antes («detrás
había tres causas más»): acá no vale, porque en otro contenedor ya corren.

**D223 y D224: decididas, (a) y (a).** Son mi próxima pieza.

## Supuestos (reversibles)

1. **CUIT en el perfil y no un estudio en la operación** (me lo dejaste a mí):
   es un pedido antes de abrir la pantalla; el camino del estudio ya lo
   recorre `estudio1`.
2. **`maria5`: el segundo renglón de notebooks pasa a origen `US`**, así el TXT
   sigue teniendo los cuatro ítems para los que se escribió el guion (25, 1,
   2 y 1,5 kg). La otra salida era aceptar 26 kg. Con esto el guion no pasa
   por la unión de renglones en pantalla; el generador la tiene en
   `tests/test_maria8_subitems_por_posicion.py` (leído, no corrido en esta
   pieza).
3. **Archivo nuevo `_cuit_perfil.js`** (8 líneas): el mismo pedido y su
   chequeo iban a quedar en tres guiones.
4. **`maria4` no carga el CUIT del perfil**: intercepta `/generate_maria`.
5. **La segunda operación de `maria3` (`F-M3B`) queda sin CUIT del
   importador**: sólo mira los avisos.
6. **No pedidos, de la autorrevisión** (`7ac0b4e`): el ayudante manda
   `X-CSRF-Token`, y `maria5` compara la lista entera de pesos.

## Para reproducir

```bash
# raíz del repo en e0d2770; PY = python de un venv con requirements.txt.
# 1) En el corredor, unos 15 minutos:
PY=$PY scripts/testing/correr_pantallas.sh e0d2770
#   → «verde» en maria3, maria4, maria5 y subitems1. Las rojas del resumen no son de esta pieza (tabla de puertas):
#     se comparan por nombre.
# 2) Las cuatro solas, sin el corredor, unos 5 minutos:
for g in maria3 maria4 maria5 subitems1; do
  D=$(mktemp -d); P=$("$PY" -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')
  ENVIRONMENT=development DATABASE_URL="sqlite+aiosqlite:///$D/p.db" CDI_DATA_DIR="$D/data" \
    JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef EMAIL_VERIFICATION_REQUIRED=false \
    GEMINI_API_KEY= MP_ACCESS_TOKEN= VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
    DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares \
    ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x \
    "$PY" -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port "$P" > "$D/api.log" 2>&1 &
  API=$!
  curl -sf --noproxy '*' --retry 90 --retry-connrefused --retry-delay 1 -o /dev/null "http://127.0.0.1:$P/health"
  BASE_URL="http://127.0.0.1:$P" node scripts/testing/pantalla_$g.js 2>&1 | tail -1; echo "$g sale ${PIPESTATUS[0]}"
  kill $API; wait $API 2>/dev/null
done
```

Lo corrí tal cual sobre `7ac0b4e`. Salida entera:

```
OK: pantalla MARIA-3
maria3 sale 0
OK: pantalla MARIA-4
maria4 sale 0
OK: pantalla MARIA-5
maria5 sale 0
OK: pantalla SUBITEMS-1
subitems1 sale 0
```

Los rojos de hoy: el mismo bloque en un worktree de `166c46c` da los textos
de las causas 1 y 2 (en mi contenedor, antes, la 4). Los dos de `7ac0b4e`:

```bash
# el mismo bloque con CSRF_ENFORCE=true entre las variables y el ayudante de 3e195de:
# maria3 → FALLA: CUIT del perfil: 403 {"detail":"Token CSRF invalido o ausente. Recarga la pagina.","code":"csrf_failed"}
# con el de 7ac0b4e: OK: pantalla MARIA-3, sale 0

# en pantalla_maria5.js, el segundo renglón de notebooks de vuelta en origen 'CN':
# FALLA: los pesos por ítem son 26.000, 2.000, 1.500 y se esperaba 25, 1, 2 y 1,5 kg

python docs/pm/herramientas/chequeo-6.py 166c46c 7ac0b4e   # producto +0/−0, arnés +23/−8, avisos: 1
```

## Puertas (las solas, sobre `7ac0b4e`; el corredor, sobre `e0d2770`)

| puerta | salida |
|---|---|
| `pantalla_maria3.js`, servidor y base nuevos | 8 `OK`, 0 `FALLA`, sale 0 |
| `pantalla_maria4.js`, ídem | 7 `OK`, 0 `FALLA`, sale 0 |
| `pantalla_maria5.js`, ídem | 9 `OK`, 0 `FALLA`, sale 0; `pesos: 25.000, 1.000, 2.000, 1.500` |
| `pantalla_subitems1.js`, ídem | 10 `OK`, 0 `FALLA`, sale 0 |
| `maria3` con `CSRF_ENFORCE=true` | 8 `OK`, sale 0 |
| `anclas_perdidas.py 7ac0b4e` | sale 0; ninguna fila de un archivo de esta pieza (no toca guiones de sabotaje) |
| `correr_pantallas.sh e0d2770` (02:44→02:58 UTC) | `verde maria3 rc=0 … OK: pantalla MARIA-3`, `verde maria4 rc=0 … OK: pantalla MARIA-4`, `verde maria5 rc=0 … OK: pantalla MARIA-5`, `verde subitems1 rc=0 … OK: pantalla SUBITEMS-1`; `resumen: 25 verdes, 5 rojas: catalogo_ncm1 excel1 maria1b maria1c maria7`, sale 1 |
| el mismo corredor (copia de `4e98c86`, idéntica por `cmp`) sobre `636da47`, antes de integrar sus cabeceras | las cuatro `verde`; `resumen: 24 verdes, 6 rojas: catalogo_ncm1 csrf1 excel1 maria1b maria1c maria7` |

Las rojas del corredor, por nombre:

| pantalla | última línea | de quién |
|---|---|---|
| `catalogo_ncm1`, `excel1`, `maria1b`, `maria1c` | `FALLA: browserType.launch: Failed to launch chromium because executable doesn't exist at /opt/pw-browsers/chromium-1194/chrome-linux/chrome` | D226; de entorno: en mi contenedor esa ruta no existe |
| `maria7` | `FALLA: la pregunta por la fecha no aparece al subir` | de la Técnica (INTERMITENTES). Dato para ella: en mi contenedor dio roja en las dos corridas, 2 de 2 |
| `csrf1` (sólo sobre `636da47`) | `FALLA: «Salir» rechazado no avisó y la página fue a /` | le faltaba la cabecera `// corredor: servidor CSRF_ENFORCE=true`, que llegó con tu rama. Comprobado: sola, con `CSRF_ENFORCE=true`, da `OK: CSRF-1 en el navegador`; sobre `e0d2770` sale `verde` |

`chequeo-6`, entero:

```
chequeo-6 166c46c..7ac0b4e: avisos para mirar, no un veredicto
producto +0/−0
arnés +23/−8
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  AVISO creció una función de más de 150: scripts/testing/pantalla_subitems1.js:23 <anónima> 180 → 181, 1 en su propio cuerpo (§6: lo nuevo va aparte)
avisos: 1
```

El `AVISO` queda: la línea que suma es la llamada al ayudante, que tiene que
ir dentro del guion después del registro. Lo nuevo ya está aparte, en
`_cuit_perfil.js` (en `0ec6343` eran 3 líneas). Partir esa función va a la
cola.

## Hallazgos de la autorrevisión

Adversario: `adversario-sonnet-medio` (Sonnet, esfuerzo medio); corrió
`maria5` una vez, el resto lo leyó. `/code-review high` sobre
`166c46c..3e195de`: sus revisores heredan Fable.

| # | quién | hallazgo | qué hice |
|---|---|---|---|
| 1 | code-review, adversario | El ayudante no manda el token CSRF: con el CSRF en bloqueo da 403 | **Confirmado** con el rojo de arriba. Arreglado en `7ac0b4e` |
| 2 | code-review | `maria5` no comprueba los cuatro ítems, sólo el primer peso | Arreglado en `7ac0b4e`, con su rojo |
| 3 | adversario | El perfil acepta un CUIT con el verificador mal | Producto, fuera de la pieza: **D225** |
| 4 | code-review | Otros cuatro guiones con la ruta fija; mi commit `0ec6343` dice «como los demás guiones de pantalla» y no es exacto (de 30, hoy: 23 sin ruta contando los míos, 4 con la de 1194, 3 con otra) | Fuera de la pieza: **D226**. El mensaje ya está subido |
| 5 | code-review | «En un solo lugar» (`3e195de`) vale para mis tres guiones: otros cuatro siguen con el pedido escrito a mano | Fuera de la pieza: línea para la cola, atada a D225 |
| 6 | code-review, adversario | En `maria4` el CUIT de la operación no es el del cliente, y los CUIT de los dos clientes no pasan `cuit_valido` | Queda, baja: la validación no los compara y el guion mira banco y estado. Línea para la cola |
| 7 | code-review | En `maria4` las altas de cliente y de operación anterior no se chequean (líneas 18-23 y 82-87, de antes) | Queda, baja: si fallan, el guion corta en «no propone el último banco», lejos de la causa. Línea para la cola |
| 8 | adversario | `maria5` ya no pasa por la unión de renglones | Supuesto 2 |
| 9 | adversario | Dijo que `sabotaje_maria4.sh` y `sabotaje_subitems1.sh` corren estos guiones | **No confirmado**: sólo los nombran en comentarios (líneas 4 y 6). Tu «ningún guion los corre» se sostiene |

**Líneas que propongo para `COLA-LIMPIEZA.md`** (no la toco):

- `pantalla_subitems1.js`: la función principal mide 181 líneas; partirla.
- `pantalla_orden1.js:112`, `pantalla_validacion1.js:126`,
  `pantalla_cobro_corte1.js:180`, `pantalla_cobro_mp1_v2.js:24`: usar
  `_cuit_perfil.js` (después de D225: hoy cargan un CUIT inválido).
- `pantalla_maria4.js`: chequear las altas del armado y usar CUIT válidos, el
  mismo en el cliente y en la operación.

## Qué no corrí y riesgos

- **Nada de pytest, `compileall`, `smoke_friccion.sh`, `ataque_aislamiento.sh`
  ni `e2e_maria.sh`**: la pieza no toca producto ni ninguna prueba que ellos
  corran.
- Con `CSRF_ENFORCE=true` corrí sólo `maria3`. `maria4` hace cuatro `POST`
  directos sin token (de antes): leído, ahí daría 403.
- Los cuatro contra un mismo servidor, uno atrás de otro: no corrido.
- Los cuatro guiones de D226: corridos sólo dentro del corredor, donde cortan
  al abrir el navegador. Qué hacen después de abrir, en mi contenedor, no lo vi.
- **Al corredor no lo llama nada** (`grep` de `correr_pantallas` en `.sh`,
  `.py`, `.yml` y la CI: sólo `docs/pm/`). Mis cuatro vuelven a estar verdes y
  se ven rojas sólo si alguien lo corre.
- `chequeo-6` y `anclas_perdidas.py` corrieron sobre `7ac0b4e`, no sobre
  `e0d2770`: entre los dos sólo está tu rama integrada.
- El rojo de la causa 4 lo volví a sacar con el guion de `166c46c` sin
  servidor: corta al abrir el navegador, antes de necesitarlo.

Archivos de producto tocados: ninguno.

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn, cabeza 90b66c5, ya integrada en e0d2770), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. Aceptadas: D218 y D219. Entregada y esperando veredicto: PANTALLAS-MARIA en e0d2770 (guiones de 7ac0b4e; sólo arnés, producto +0/−0; pantalla_maria3, maria4, maria5 y subitems1 salen 0 solas y verdes en scripts/testing/correr_pantallas.sh). Abiertas, las decide la PM: D225 (el perfil guarda un CUIT de despachante con el verificador mal y el TXT sale con él: recomiendo (a), pieza chica de producto) y D226 (catalogo_ncm1, excel1, maria1b y maria1c con la ruta fija del navegador, rojas en el corredor de mi contenedor: recomiendo (a), las tres primeras mías). Ya decididas: D221 (b), D222 (a), D223 (a), D224 (a). No son mías: maria7 y maria1c (de la Técnica, tarea INTERMITENTES), ni correr_pantallas.sh. Orden de la PM, una pieza a la vez: la que arranco ahora es D223 + D224 (un sabotaje del advisory lock de _migrate_catalogo_claves en sabotajes/catalogo_largo2.sh, con el lock_timeout como riesgo anotado; y dos datos más en la prueba de _vendor_key: clave de 60 entera, de 61 cortada). Después: retirar el 13 y el 24 de sabotaje_valor1.sh y reanclar en código el 10 (comentario, línea 108) y el 28 (comentario al final de la línea 187), puerta: valor1 entero da 29 ROJO y sale 0, y su línea sale de sabotajes-conocidos.txt; AJUSTE-BORRADOR (producto en static/v2: primero un caso de pantalla en rojo; corre e2e_maria.sh); y los vencidos de sabotajes-conocidos.txt, uno por pieza. Próxima D libre: D227. Una devolución de la PM o la tarea de comparación van primero. Los detalles están en PARA-PM-2.md: el resumen los cita, no los copia. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; las Devs no usan el consejero.
