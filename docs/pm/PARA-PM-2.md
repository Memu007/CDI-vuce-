# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Entrega Holanda→423, vuelta sobre `b3a3bf69` (2026-11-17 00:35 UTC)

**Resultado.** Los cinco criterios de tu devolución se cumplen en `b3a3bf69` (base `a910c5f`).
Un origen guardado o escrito con el 434 («434», «0434», « 434 », el número 434, «434 · HOLANDA»,
«434 - Holanda», «434 · PAISES BAJOS») se ve **423** en el catálogo del proveedor, en el del cliente
y en la procedencia de la revisión; lo demás se ve como vino. Lo guardado no se reescribe, tampoco
al guardar otra cosa de la fila. `producto +20/−8` en cuatro JS: `paises_maria.js` suma
`mostrar(value)` y la usan `catalogo.js`, `clientes.js` y `review.js`.

**Lo que decidís vos** (supuestos; ninguna D nueva, la próxima sería D264):
- **Supuesto 4: se ve el código «423», no la etiqueta «423 · PAISES BAJOS».** Tu criterio dice «lo
  que sale en el TXT», el campo del cliente tiene `maxlength=3`, y mostrar etiquetas es D261.
  Consecuencia que encontró `/code-review`: «434 · PAISES BAJOS» guardado se ve «423», y
  «423 · PAISES BAJOS» guardado se sigue viendo con el nombre. Si preferís la etiqueta para lo
  reemplazado, es cambiar `resolve(value)` por `label(value)` dentro de `mostrar`.
- **Supuesto 5: guardar una fila del catálogo del proveedor manda el origen sólo si se cambió.** Era
  necesario para el criterio 4: la fila muestra «423» y antes mandaba siempre lo que se ve, así que
  cambiar el NCM de una fila «434 · HOLANDA» la guardaba «423» (lo encontraron `/code-review` y los dos
  adversarios; reproducido). Efecto lateral: antes, guardar la fila también pasaba a mayúsculas un
  origen no tocado («Holanda» → «HOLANDA»); ahora queda como estaba. El servidor ya dejaba igual el
  campo que no llega (`catalog_service.update_product`, `if updates.get("origen") is not None`).

### Criterio 1: los lugares

Salen de `grep -rn "origen\|procedencia\|default_origin\|getOriginLabel" proyecto_maria/static
proyecto_maria/templates` y de leer cada uno; el adversario Opus repitió la búsqueda sin encontrar
otro.

| lugar | ¿llega a un TXT hoy? | qué queda |
|---|---|---|
| `catalogo.js:250` → `:270`, catálogo del proveedor (`VendorCatalogProduct.origen`) | sí, por el lookup del catálogo | **`mostrar`**; al guardar la fila, el origen va sólo si se tocó |
| `clientes.js:1427`, catálogo del cliente (`ClientProductHistory.origen_frecuente`) | sí, por el lookup | **`mostrar`** al dibujar y después del PUT de lo escrito (si no se siguió escribiendo) |
| `review.js`, procedencia (`populate` y `onFieldChange`) | sí: el borrador va a `finalize.js:921`, que la resuelve | **`mostrar`** sólo en el campo, al cargar y en `change` (no en cada tecla: «434» es el comienzo de «4340»); el estado de la operación queda como vino |
| `upload.js:586`, `:600-602` y la grilla NCM (`ncm.js:690`, `:988`, `:1019`) | sí | sin cambio: ya muestran `getOriginLabel` = `label` («423 · PAISES BAJOS») y guardan con `getOriginCode` |
| `finalize.js` | — | no muestra el origen de los ítems: sólo lo manda (`:168`, `:859`, `:1288`, `:1383`) |
| `clientes.js:1071`, `:1232`, `:1955`, `default_origin` | no | ningún camino a la generación (el `default_origin` de `pdf_extractor` es otra variable). Riesgo |
| `clientes.js:1139` y `main.py:8466`, «Origen frecuente» de métricas | no | riesgo |
| `clientes.js:1686`, nota «decía «…»» del despacho | no | texto leído del documento cuando falta el origen; el campo queda vacío |
| `templates/public_quote.html:269`, `calculadora.js:112`, `main.py:8350` (`/agrupar`) | no | cotización, select fijo, mensaje que la interfaz no llama |
| `main.py:8767`, Excel del catálogo del cliente | no (no es pantalla) | sigue con lo guardado; lo vio el adversario Opus |

### Criterio 2: la familia, como datos de un caso

`test_holanda_y_paises_bajos_son_423` (`tests/test_catalogo3.py`), sobre `mostrar` de la pantalla:
- con el 434 → «423»: las formas de `PAISES_BAJOS` que empiezan con 434 o 0434 («434», «0434»,
  «434 · HOLANDA», «434 - Holanda», «434 · PAISES BAJOS»), el número 434 y « 434 »;
- de control → como vinieron: el resto de `PAISES_BAJOS` («HOLANDA», «Holanda», «Países Bajos», «NL»,
  «423 · HOLANDA»…), `NO_SON_HOLANDA` («434.», «４３４», «4340», «00434», «434 · BELGICA»…), «», «XX»,
  «0310», «0423», « Holanda », «Países  Bajos», y None → «».

`scripts/testing/pantalla_holanda423.js` lo mira en el navegador contra una API local:
- guardadas: `434`, `0434`, `434 · HOLANDA`, `434 - Holanda`, `434 · PAISES BAJOS` (y el número 434 en
  el cliente; el proveedor rechaza números) frente a `HOLANDA`, `Holanda`, `Países Bajos`, `NL`,
  `CHINA`, `310`, en los dos catálogos y como procedencia del borrador;
- escritas: «0434» en el proveedor (guardar), «434» en el cliente (Enter), cada una en la procedencia
  (salir del campo), y «4340» tecla por tecla;
- lo que no se toca: cambiar sólo el NCM deja el origen guardado igual (leído de la API), la
  procedencia del borrador queda igual en `CDI.state.operacion`, lo que se vuelve a escribir mientras
  se guarda no se pisa, «nl» y un peso 434 escritos en el cliente y una factura 434 (borrador y
  escrita) se ven como se escribieron.

### Criterio 3: volcado

8042 formas (todos los códigos 000–999 con y sin 0 adelante, con espacios, con « HOLANDA» y «· X»;
cada «código · nombre» y «código - nombre» de la tabla; nombres en mayúsculas, minúsculas y título;
alias, INDEC, ISO3; vacío, XX, None y números). «Antes» es lo que hacían los tres lugares (el valor
como texto); «ahora», `mostrar`. Diff entero:

```
formas: 8042; se ven distinto: 8
' 434 ': ' 434 ' -> '423'
'0434': '0434' -> '423'
'434': '434' -> '423'
'434 - HOLANDA': '434 - HOLANDA' -> '423'
'434 - Holanda': '434 - Holanda' -> '423'
'434 · HOLANDA': '434 · HOLANDA' -> '423'
'434 · PAISES BAJOS': '434 · PAISES BAJOS' -> '423'
434: '434' -> '423'
```

Ningún otro país cambia. «434 · BELGICA», «４３４», «434.», «4340» y «00434» se ven como vinieron, y
el servidor tampoco les da país. El guion del volcado va en «Comandos».

### Criterio 4: lo guardado no se reescribe

Sólo cambia lo que se ve. Tres caminos que podían guardar lo mostrado, y la prueba de cada uno:
- proveedor, guardar la fila: el origen va sólo si se cambió (supuesto 5). Prueba: `soloElNcm`.
- revisión, abrir el borrador: `populate` sincroniza al estado lo normalizado (USD → DOL); `mostrar`
  queda fuera de eso y sólo toca el campo. Lo encontró el adversario Opus en `e7741c37`; arreglado en
  `45e17c26`. Prueba: la procedencia del borrador en `CDI.state.operacion`.
- cliente: el PUT es por campo y sólo en `change`; sin tocar el origen no hay PUT.

Lo escrito sí se guarda como se escribió: «0434» escrito en el proveedor queda «0434» (genera 423).

### Criterio 5: el rojo con el arreglo revertido

El producto de `a910c5f` con las pruebas de `b3a3bf69`:

```
FAILED tests/test_catalogo3.py::test_holanda_y_paises_bajos_son_423 - subproc...
=========== 1 failed, 1 passed, 107 deselected, 5 warnings in 0.97s ============
FALLA: catálogo del proveedor: «434» guardado se ve «434»
```

El caso falla porque `mostrar` no existe en la base; el rojo que distingue el defecto es el de la
pantalla. Los rojos de cada parte del arreglo, uno por uno, son los sabotajes.

## Sabotajes (§3)

`scripts/testing/sabotajes/holanda423.sh` (nuevo, con `_casos_y_pantalla.sh`): 15 sabotajes, cada uno
con su frase medida.
- `mostrar`: devuelve lo que vino (caso y pantalla), escribe «null» por lo que falta, recorta lo que
  no es el 434 (caso);
- cada llamada: el proveedor muestra lo guardado; el cliente muestra lo guardado y deja lo escrito; la
  procedencia del borrador y la escrita quedan como vinieron;
- lo que no se toca: el proveedor manda el origen sin tocar; el cliente pisa lo que se sigue
  escribiendo; la procedencia del borrador cambia en la operación;
- el alcance: el borrador muestra cada campo con `mostrar`; lo escrito en cualquier campo pasa por
  `mostrar`; el cliente muestra el código de lo escrito («nl» → 423); la procedencia cambia en cada
  tecla.

Sobre `b3a3bf69` (23:57:46 → 00:00:45 UTC): base verde (`109 passed`, «OK: pantalla Holanda→423»),
15 de 15 `ROJO` con su frase, «sabotajes sin rojo: 0», salida 0.

En la puerta sobre `c2fa0546` uno quedó verde: «lo escrito en cualquier campo pasa por `mostrar`».
La prueba escribía en la factura el mismo «434» que traía el borrador, y con el mismo valor no hay
`change`: no distinguía el defecto. Ahora escribe «0434» (`b3a3bf69`, sólo pruebas); medido a mano
verde en la copia buena y «FALLA: la factura «0434» escrita se ve «423»» con el sabotaje.

## Revisión

- **`/code-review high`** sobre `a910c5f..e7741c37`: 8 hallazgos.
  - El proveedor reescribía el origen al guardar la fila: arreglado (`77286ab6`), supuesto 5.
  - El cliente pisaba lo que se seguía escribiendo mientras volvía el PUT: arreglado (`77286ab6`).
  - La pantalla leía el valor del cliente apenas llegaba la respuesta (carrera) y contaba «6» a mano:
    ahora espera una condición y cuenta desde la familia.
  - «434 · PAISES BAJOS» se ve distinto de «423 · PAISES BAJOS»: supuesto 4.
  - `mostrar` analiza dos veces: no lo cambié (una lectura de texto por fila).
  - «Arreglarlo en un solo lugar, en el servidor»: no. Cambiar lo que devuelve la API haría que la
    pantalla mandara de vuelta el 423 y reescribiera lo guardado.
  - «Guion de sabotaje propio fuera de §3»: tu devolución pide §3 fuerte.
- **Adversario Opus alto** (sobre `e7741c37`): confirmó lo del proveedor y encontró que abrir la
  revisión cambiaba la procedencia en la operación (arreglado en `45e17c26`). Sospecha: las llamadas
  nuevas no tienen la guarda `CDI.paisesMaria &&` de otras; ver riesgos. Sin hallazgo: otros lugares,
  XSS («434 · <b>» se ve tal cual, escapado), «4340», 34 entradas contra `codigo_de_pais`.
- **Adversario Sonnet alto** (sobre `e7741c37`, foco en las pruebas): confirmó lo del proveedor, y
  doce mutaciones que dejaban caso y pantalla verdes (null → «null», vacío → «XX», recortar, juntar
  espacios, «0310» → 310, « 434 » no reconocido, el cliente con `resolve`, `mostrar` en otros campos
  de la revisión o del cliente, `comparar` salteando filas). Ahora mueren todas por el caso o la
  pantalla salvo dos: un origen numérico en el proveedor (no se alcanza: la API lo rechaza) y
  `mostrar(p.origen || 'XX')` en el proveedor (el caso cubre el vacío en `mostrar`, no esa llamada). Las del
  caso las medí a mano: `'null' != ''`, `'XX' != ''`, `'Holanda' != ' Holanda '`,
  `'Países Bajos' != 'Países  Bajos'`, `'310' != '0310'`, `' 434 ' != '423'`.
- **`/security-review`**: no lo corrí. El diff no suma rutas ni cambia permisos; el único dato nuevo
  que va al servidor es *no* mandar un campo. El adversario Opus miró XSS.

## Puertas

| puerta | SHA | resultado |
|---|---|---|
| suite completa, worktree limpio, `test.db` borrada | `c2fa0546` | `6197 passed, 110 skipped, 3 xfailed` en 18:28 (23:52:50 → 00:11:23 UTC), salida 0 |
| `e2e_maria.sh` | `c2fa0546` | «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.», salida 0 |
| `sabotajes/holanda423.sh` | `b3a3bf69` | «sabotajes sin rojo: 0», 15 de 15 `ROJO`, salida 0 (3 minutos) |
| `sabotajes/seguro2.sh` | `c2fa0546` | base `78 passed`, «sabotajes sin rojo: 0», 19 de 19 `ROJO`, salida 0 |
| `sabotajes/catalogo3.sh` | `c2fa0546` | «fallas: 0», 65 de 65 `ROJO`, salida 0 (32 minutos) |
| `anclas_perdidas.py`, `chequeo-6.py` | `b3a3bf69` | 2569 anclas, 0 perdidas; 0 avisos |

De `c2fa0546` a `b3a3bf69` cambian sólo `pantalla_holanda423.js` y `holanda423.sh`
(`git diff --stat c2fa0546 b3a3bf69`), que no entran en la suite, en `e2e_maria.sh`, en `seguro2.sh`
ni en `catalogo3.sh`: esas cuatro valen para `b3a3bf69`. El rojo revertido y el volcado los volví a
correr sobre `b3a3bf69`, con los comandos de abajo tal como están.

`anclas_perdidas.py b3a3bf69`: 2569 anclas medidas, perdidas 0, 0 y 0. De los guiones que nombran los
archivos tocados, sólo `seguro2.sh` ancla una línea que cambié (`const normalized = valorEnLaRevision(key, op);`,
que sigue igual): corrió. No corrí `avisos1`, `cliente1`, `despacho1a`, `foco_cliente1`, `pa1`,
`sabotaje_separadores1`, `sabotaje_valor1` ni `sabotaje_valor1b`: anclan otras líneas de esos
archivos y sus anclas están. Tampoco `test_despacho1b` (lo medís vos).

## Comandos

```bash
VENV=/ruta/al/venv   # el tuyo
# 1. el rojo con el arreglo revertido: producto de a910c5f, pruebas de b3a3bf69
R=/tmp/rojo423; git worktree add -f -q --detach $R b3a3bf69 && cd $R && git checkout a910c5f -- proyecto_maria
git diff --cached --shortstat                     # «4 files changed, 8 insertions(+), 20 deletions(-)»
env -u DATABASE_URL -u ENVIRONMENT GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
  PYTHONPATH=. $VENV/bin/python -B -m pytest -q --no-cov -p no:cacheprovider tests/test_catalogo3.py -k holanda | tail -1
#    «1 failed, 1 passed, 107 deselected»
T=$(mktemp -d); P=8423
env GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares \
  PYTHONPATH=. ENVIRONMENT=development DATABASE_URL="sqlite+aiosqlite:///$T/p.db" CDI_DATA_DIR="$T/data" \
  JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef EMAIL_VERIFICATION_REQUIRED=false \
  ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x \
  $VENV/bin/python -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port $P > $T/api.log 2>&1 < /dev/null & A=$!
until curl -fsS http://127.0.0.1:$P/health >/dev/null 2>&1; do sleep 0.3; done
BASE_URL=http://127.0.0.1:$P node scripts/testing/pantalla_holanda423.js | tail -1
#    «FALLA: catálogo del proveedor: «434» guardado se ve «434»»
kill $A; cd - >/dev/null; git worktree remove -f $R; rm -rf $T

# 2. sabotajes (acá: holanda423 3 minutos, seguro2 6, catalogo3 32)
PATH=$VENV/bin:$PATH PY=$VENV/bin/python bash scripts/testing/sabotajes/holanda423.sh b3a3bf69 | tail -1
#    «sabotajes sin rojo: 0»
PY=$VENV/bin/python bash scripts/testing/sabotajes/seguro2.sh b3a3bf69 | tail -1
#    «sabotajes sin rojo: 0»
PY=$VENV/bin/python bash scripts/testing/sabotajes/catalogo3.sh b3a3bf69 | tail -1
#    «fallas: 0»

# 3. anclas y §6
python3.12 scripts/testing/anclas_perdidas.py b3a3bf69 | grep -E '^revisión|perdida'
#    «2569 anclas medidas», perdidas 0, 0 y 0
python3.12 docs/pm/herramientas/chequeo-6.py a910c5f b3a3bf69
#    «producto +20/−8», «arnés +252/−0», «avisos: 0»

# 4. el volcado (antes = el valor como texto; ahora = mostrar)
PYTHONPATH=. $VENV/bin/python - <<'PY'
import json, re, subprocess
from proyecto_maria.core import maria_generator as mg
from proyecto_maria.core.paises_iso3 import ISO3_A_ISO2

js = mg._PAISES_PANTALLA.read_text(encoding="utf-8")
countries = json.loads(re.search(r"const COUNTRIES = (\[.*?\]);", js).group(1))
aliases = json.loads(re.search(r"const ALIASES = (\{.*?\});", js).group(1))
formas = {*mg.PAISES_INDEC, *aliases, *ISO3_A_ISO2, *(c["name"] for c in countries)}
for n in range(1000):
    formas |= {f"{n:03d}", f"0{n:03d}", f"{n:03d} · X", f"{n} - HOLANDA", f"{n:03d} HOLANDA", f" {n:03d} "}
for c in countries:
    formas |= {f"{c['code']} · {c['name']}", f"{c['code']} - {c['name']}", c["name"].lower(), c["name"].title()}
formas |= {"Holanda", "holanda", "434 · HOLANDA", "434 - Holanda", "423 · HOLANDA", "434 · PAISES BAJOS", "00434",
           "4340", "434.", "４３４", "", "XX", "434 · BELGICA"}
valores = sorted(formas) + [434, 423, 310, None]
nodo = (f"global.window = {{}}; require({str(mg._PAISES_PANTALLA)!r}); const P = window.CDI.paisesMaria;"
        "const v = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
        "console.log(JSON.stringify(v.map(x => P.mostrar(x))));")
vistos = json.loads(subprocess.run(["node", "-e", nodo], input=json.dumps(valores), check=True,
                                   capture_output=True, text=True).stdout)
antes = ["" if v is None else str(v) for v in valores]
distintos = [(v, a, d) for v, a, d in zip(valores, antes, vistos) if a != d]
print(f"formas: {len(valores)}; se ven distinto: {len(distintos)}")
for v, a, d in distintos:
    print(f"{v!r}: {a!r} -> {d!r}")
PY
#    «formas: 8042; se ven distinto: 8», las ocho de arriba
```

El 3, como lo medí:

```
chequeo-6 a910c5f..b3a3bf69: avisos para mirar, no un veredicto
producto +20/−8
arnés +252/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/static/v2/paises_maria.js: 50 → 56
  proyecto_maria/static/v2/screens/catalogo.js: 403 → 404
  proyecto_maria/static/v2/screens/clientes.js: 2211 → 2213
  proyecto_maria/static/v2/screens/review.js: 1195 → 1198
avisos: 0
```

El grep de historia de §6 sobre `proyecto_maria/` da vacío. Producto +12 netas.

| commit | qué |
|---|---|
| `11f223bf` fix | `mostrar` y sus cuatro llamadas; CHANGELOG |
| `e7741c37` test | caso, pantalla y `holanda423.sh` |
| `77286ab6` fix | el proveedor manda el origen sólo si se tocó; el cliente no pisa lo que se sigue escribiendo |
| `2ef75b78` test | sus pruebas y sabotajes |
| `45e17c26` fix | la revisión no cambia la procedencia de la operación |
| `0dd5bd1b` test | su prueba y sabotaje |
| `c2fa0546` test | la familia de control y el alcance (lo de Sonnet) |
| `b3a3bf69` test | la factura escrita distinta de la del borrador (el sabotaje de `mostrar` en cualquier campo quedaba verde en la puerta). **Lo que se entrega** |
| informe | el commit siguiente |

## Riesgos

- **«Origen frecuente» de las métricas del cliente y `default_origin`** muestran lo guardado tal cual;
  no llegan al TXT hoy. Si vuelven a la generación, tienen que pasar por `mostrar`. Sin código (D261).
- **Sin guarda `CDI.paisesMaria &&`** en las llamadas nuevas: si `paises_maria.js` no cargara, la
  revisión y los catálogos tirarían un error al dibujar. El orden no es riesgo (todo es `defer` y se
  dibuja después); `?v=` cambia con cada arranque.
- **«434 · PAISES BAJOS» se ve «423»** y «423 · PAISES BAJOS» se ve con nombre: supuesto 4.
- **El Excel del catálogo del cliente** (`main.py:8767`) sigue con lo guardado: no es pantalla.
- **Previo, no de esta pieza:** escribir en el NCM del catálogo del proveedor tira
  `Cannot create property '__cdiMaskNcmApplied' on string` (`catalogo.js` le pasa un texto a
  `CDI.maskNcm`); lo vio el adversario Opus. Lo propongo para la cola.
- **Dos mutaciones sin prueba** (Sonnet): `mostrar(p.origen || 'XX')` en el proveedor (un origen vacío
  se vería «XX»; ninguna fila de la pantalla lo tiene vacío), y la rama de un origen numérico en el
  proveedor, que la API rechaza hoy.
- **`mostrar(0)` da «0»**: antes, un origen 0 en el catálogo del proveedor se veía vacío
  (`p.origen || ''`). Ningún origen guardado es número en el proveedor; en el cliente se veía «XX» y
  se sigue viendo «XX».
- **Lo guardado en producción no se midió.** Las filas con «434» se ven 423 y generan 423; no sé
  cuántas hay.
- **El despachante puede seguir usando 434** (tu DECISIONS de las 19:39): no lo verifiqué.
- La CI deselecciona tests de presupuestos y Railway no la espera: no es red.

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5, rama `claude/dev-maria`, rutina trig_01Ukttby1fc4sGVQfSn1jC9U; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `2e69a0b1`). Aceptadas: las de antes (CUIT-GENERAR `29327d2` … D257 (b) `3c7eb14`), D244 (a) y Holanda→423 sobre `b3a3bf69` (supuestos 4 y 5 aceptados; acta `REPRODUCCION-HOLANDA-423-2026-11-16.md`, «Vuelta»). Activa: D239 (a), códigos sin sigla en el lector de despachos (`PARA-DEV-2.md`, seis criterios; el 6 es el «Origen frecuente» de `clientes.js:1139` con 434 → 423). Paso: recién arrancada, base `2e69a0b1` (merge en mi rama); primero el rojo de cada criterio, después el producto. Revisión §3 fuerte: `/security-review`, adversarios, suite completa, `e2e_maria.sh` y los guiones que anclen lo tocado, sobre el SHA que se entrega. Después: D263 (validación mira `origen`, el generador usa `pais_origen`). D262 (a) está en la cola de limpieza; D261 la lleva la PM. `test_despacho1b`: lo mide la PM. Próxima D: D264. Lecciones (además de las de antes, que siguen en el historial de este archivo): no editar un guion de sabotaje mientras corre (el arnés lo lee de la copia de trabajo); un `fill` con el mismo valor que ya tiene el campo no dispara `change`: la prueba escribe algo distinto de lo cargado; el toast es la condición observable de que el handler terminó; el volcado de formas de país está en el informe de Holanda→423 («Comandos», paso 4) y sirve de base para el criterio 4; horas, sólo de `date -u`. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica; subagentes hasta esfuerzo alto, sin consejero, nunca Fable; detener los subagentes después de su informe.
