# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## PANTALLAS-MARIA: entregada en `7ac0b4e` (sólo arnés). Dos decisiones nuevas: D225 y D226

**El informe de D218 y D219 sigue esperando tu veredicto** y ya no está acá:
`git show 166c46c:docs/pm/PARA-PM-2.md`. Ahí están enteras **D223** y **D224**,
que siguen abiertas (resumen abajo).

| qué | SHA |
|---|---|
| base (mi informe anterior) | `166c46c` |
| los cuatro guiones vuelven a salir 0 | `0ec6343` |
| el CUIT del perfil, en un ayudante (`_cuit_perfil.js`) | `3e195de` |
| de la autorrevisión: token CSRF en el ayudante y los cuatro pesos en `maria5`: **el que se entrega** | `7ac0b4e` |
| informe | el commit siguiente |

Tu rama: sin commits nuevos desde `67c8ff0` (ya integrada en `636b889`).

**Resultado.** Los cuatro, cada uno con servidor y base nuevos, sobre
`7ac0b4e`: `maria3` 8 `OK`, `maria4` 7, `maria5` 9, `subitems1` 10; ninguna
`FALLA`; los cuatro salen 0. Producto **+0/−0**; arnés +23/−8.

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

**D226. Otros cuatro guiones tienen la misma ruta fija del navegador:**
`pantalla_catalogo_ncm1.js:12`, `pantalla_excel1.js:12`,
`pantalla_maria1b.js:17`, `pantalla_maria1c.js:13`. **Leído, no corrido**: en
mi contenedor cortarían al abrir. No sé si en el tuyo abren ni qué hay
detrás. Tampoco a estos los corre ningún guion (`grep` de sus nombres en
`.sh`, `.py` y la CI: sólo comentarios).

- (a) Una pieza: los cuatro con `chromium.launch()`, cada uno corrido una
  vez, y lo que aparezca detrás se informa.
- (b) A la cola.

Recomiendo **(a)**: acá, detrás del mismo rojo había tres causas más.

**D223 y D224 (abiertas desde `166c46c`).** D223: el candado de
`_migrate_catalogo_claves` no tiene sabotaje en el repo; (a) uno para el
advisory lock, (b) riesgo anotado, (c) también el `lock_timeout`; recomiendo
(a). D224: el borde del corte de `_vendor_key` no lo fija ninguna prueba; (a)
dos datos más, (b) riesgo anotado; recomiendo (a).

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
# raíz del repo en 7ac0b4e; PY = python de un venv con requirements.txt. Unos 5 minutos.
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

## Puertas, sobre `7ac0b4e`

| puerta | salida |
|---|---|
| `pantalla_maria3.js`, servidor y base nuevos | 8 `OK`, 0 `FALLA`, sale 0 |
| `pantalla_maria4.js`, ídem | 7 `OK`, 0 `FALLA`, sale 0 |
| `pantalla_maria5.js`, ídem | 9 `OK`, 0 `FALLA`, sale 0; `pesos: 25.000, 1.000, 2.000, 1.500` |
| `pantalla_subitems1.js`, ídem | 10 `OK`, 0 `FALLA`, sale 0 |
| `maria3` con `CSRF_ENFORCE=true` | 8 `OK`, sale 0 |
| `anclas_perdidas.py 7ac0b4e` | sale 0; ninguna fila de un archivo de esta pieza (no toca guiones de sabotaje) |

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
- Los cuatro guiones de D226: no corridos.
- **Sigue sin haber un guion que los corra.** Vuelven a estar verdes y
  pueden volver a romperse sin que nadie lo vea. No lo agregué: no lo pediste.
- El rojo de la causa 4 lo volví a sacar con el guion de `166c46c` sin
  servidor: corta al abrir el navegador, antes de necesitarlo.

Archivos de producto tocados: ninguno.

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn, cabeza 67c8ff0, ya integrada en 636b889), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. Entregadas y esperando veredicto: D218 y D219 en 1f8ffa6 (informe en 166c46c) y PANTALLAS-MARIA en 7ac0b4e (informe en el commit siguiente; sólo arnés, producto +0/−0: pantalla_maria3, maria4, maria5 y subitems1 salen 0 con servidor y base nuevos). Abiertas, las decide la PM: D223 (candado de _migrate_catalogo_claves sin sabotaje: recomiendo (a)), D224 (borde del corte de _vendor_key sin prueba: recomiendo (a)), D225 (el perfil guarda un CUIT de despachante con el verificador mal y el TXT sale con él: recomiendo (a), pieza chica de producto) y D226 (otros cuatro guiones de pantalla con la ruta fija del navegador: recomiendo (a), una pieza). Ya decididas: D221 (b) y D222 (a). Orden de la PM, una pieza a la vez: la que arranco ahora es retirar el 13 y el 24 de sabotaje_valor1.sh y reanclar en código el 10 (hoy en un comentario, línea 108) y el 28 (comentario al final de la línea 187); puerta: valor1 entero da 29 ROJO y sale 0, y su línea sale de sabotajes-conocidos.txt. Después: AJUSTE-BORRADOR (producto en static/v2: primero un caso de pantalla en rojo; corre e2e_maria.sh) y los vencidos, uno por pieza: maria8, maria1d, maria5, valor1b, doc1.py, maria7, guardar2. Próxima D libre: D227. Una devolución de la PM o la tarea de comparación van primero. Los detalles están en PARA-PM-2.md: el resumen los cita, no los copia. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; las Devs no usan el consejero.
