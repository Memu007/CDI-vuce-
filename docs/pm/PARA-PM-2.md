# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CATALOGO-PAIS-2 (D275 b) sobre `9459a0d4` (2026-11-20 14:38 UTC)

**Resultado.** Se cumple en `9459a0d4`, contra la base `5e17da02`.
- En los dos catálogos, el campo del origen lleva como `title` lo que tiene en ese momento. Al pasar
  el mouse se ve la etiqueta entera.
- `producto +16/−3`. chequeo-6 da un `AVISO`; va abajo con su porqué.
- Va aparte, en `cbd7718c`, la tarea chica del vencido `catalogo_largo2.sh`: los tres textos ancla son de dos
  sabotajes, los dos dan rojo, y `anclas_perdidas.py 9459a0d4` ya no lo nombra.
- **Nada para decidir.** Los supuestos, abajo, se pueden revertir.

| SHA | qué |
|---|---|
| `5ec05bbf` | fix: `title` del origen en los dos catálogos; CHANGELOG |
| `64fbdf1d` | test: el caso `alPasarElMouse` en `pantalla_holanda423.js` |
| `d5b9e626` | fix: el cliente avisa con `input` al poner la etiqueta después de guardar (de `/code-review`) |
| `83b24a84` | test: después de guardar, el caso espera la etiqueta en los dos catálogos |
| `44dfb249` | merge de tu rama (`25e2f818`) |
| `cbd7718c` | test: anclas de `catalogo_largo2.sh` (tu sección «Vencido») |
| `28d0476a` | test: dos anclas de `holanda423.sh` que rompió mi cambio en `clientes.js` |
| `6bbd67ff` | test: lo escrito con blancos en los bordes (hueco que encontró el adversario) |
| `9459a0d4` | test: sale una comprobación de `__xss` que no podía fallar (de `/code-review`) |

Archivos de producto tocados: `static/v2/paises_maria.js`, `static/v2/screens/catalogo.js`,
`static/v2/screens/clientes.js`.

## Qué cambió

- `CDI.paisesMaria.alPasarElMouse(campo)`:
  - pone `campo.title = campo.value` al enganchar;
  - lo repite en cada `input`, que es lo que dispara escribir, borrar o elegir una sugerencia del
    navegador.
- **Proveedor** (`catalogo.js`): `attachProductHandlers` la llama en cada fila. Al guardar se vuelve a
  dibujar el detalle y la llamada se repite.
- **Cliente** (`clientes.js`):
  - se llama después de dibujar la lista;
  - cuando la pantalla pone la etiqueta por código después de guardar, manda un `input` para que el
    `title` siga al campo. La regla queda en un solo lugar.
  - `title="Origen"` pasa a `aria-label="Origen"`, así el campo conserva su nombre accesible.
- Vacío: `title=""`, el navegador no muestra nada.
- Nada fuera de los catálogos:
  - `ncm.js` también usa `data-field="origen"`, pero los selectores están acotados a la lista de cada
    catálogo;
  - la ficha del cliente (`cfOrigen`) no se toca.

## La prueba

`alPasarElMouse` en `scripts/testing/pantalla_holanda423.js` es un caso para los dos catálogos, con
las entradas como datos. Lee del navegador `getAttribute('title')` contra el valor del campo:
- **lo guardado, en cada fila:** 324 en el proveedor; en el cliente, la familia entera, con siglas
  viejas, texto libre, HTML y los 308 países;
- **lo escrito:** «Países Bajos», «  Ñandú del Perú  » (tildes, eñe y blancos en los bordes), «CHI»,
  HTML, y vacío;
- **lo elegido:** una sugerencia del navegador, con el `InputEvent` `insertReplacementText` que manda
  Chrome al elegirla;
- **lo que queda al guardar «España»:** espera «410 · ESPAÑA» en el campo y mira el `title`.

**Rojo con el arreglo revertido en el mismo SHA.** Los tres archivos de producto vuelven a
`5e17da02` sobre `9459a0d4` (`rojo-revertido-9459a0d4.log`):
```
FALLA: catálogo del proveedor: al pasar el mouse no se ve lo guardado en 324 filas, como «423 · PAISES BAJOS»
rc=1
```
Con el arreglo, la misma pantalla da `OK: pantalla Holanda→423`, `rc=0`.

**Cada parte, rota por separado** (corridas mías y del adversario):

| se rompe | sale |
|---|---|
| sin el listener `input` | `FALLA: catálogo del proveedor: «Países Bajos» escrito se ve «Países Bajos» y al pasar el mouse «212 · ESTADOS UNIDOS»` |
| sin el aviso `input` del cliente al guardar | `FALLA: catálogo del cliente: al pasar el mouse no se ve lo guardado en 2 filas, como «310 · CHINA»` |
| `title = value.trim()` | `FALLA: catálogo del proveedor: «  Ñandú del Perú  » escrito se ve «  Ñandú del Perú  » y al pasar el mouse «Ñandú del Perú»` |
| sin `mostrar()` al enganchar, sin la llamada en `catalogo.js` o en `clientes.js`, `change` en vez de `input`, `toUpperCase()` | rojo (adversario) |

Antes de agregar los blancos, `trim()` daba verde: lo encontró el adversario y entró en `6bbd67ff`.

## Puertas sobre `9459a0d4`

| puerta | resultado |
|---|---|
| chequeo-6 `5e17da02 9459a0d4` | `producto +16/−3`, `avisos: 1` (salida entera abajo) |
| `holanda423.sh 9459a0d4` | 34 `ROJO` de 34 sabotajes, `sabotajes sin rojo: 0`, rc=0; la base: `113 passed` y `OK: pantalla Holanda→423` |
| `catalogo_largo2.sh 9459a0d4` con PG16 | 39 `ROJO` de 39, `fallas: 0`, rc=0. Los tres textos ancla son de dos sabotajes, y los dos dan rojo (abajo) |
| `anclas_perdidas.py 9459a0d4` | no nombra `catalogo_largo2.sh` ni `holanda423.sh`; queda `limpieza1.sh:135`, que es de la Dev 1 |
| `e2e_maria.sh` sobre `9459a0d4` | `E2E MARIA OK`, rc=0, 0 cambios en el árbol |
| `e2e_maria.sh` sobre la unión con `35de2344` (`72aa5d52`) | `E2E MARIA OK`, rc=0, 0 cambios en el árbol |
| `/code-review` alto | dos pasadas: `5e17da02..64fbdf1d` y `64fbdf1d..6bbd67ff` (ver hallazgos) |
| adversario Sonnet alto | dos pasadas: `64fbdf1d` y `64fbdf1d..6bbd67ff` |

chequeo-6, salida entera:
```
chequeo-6 5e17da02..9459a0d4: avisos para mirar, no un veredicto
producto +16/−3
arnés +46/−8
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/static/v2/paises_maria.js: 288 → 295
  AVISO creció una función de más de 150: proyecto_maria/static/v2/paises_maria.js:2 <anónima> 286 → 293, 2 en su propio cuerpo (§6: lo nuevo va aparte)
  proyecto_maria/static/v2/screens/catalogo.js: 404 → 405
  proyecto_maria/static/v2/screens/clientes.js: 2219 → 2224
avisos: 1
rc=0
```
- **El `AVISO`:** la «función» es el envoltorio del módulo `paises_maria.js`, la función anónima que
  contiene todo el archivo. Lo nuevo ya va aparte, como función propia de 5 líneas. Las 2 líneas en
  el cuerpo del envoltorio son la declaración y la entrada en `Object.freeze`, no una rama.

No corrí `catalogo3.sh` ni la suite: no toqué el servidor ni `tests/`.

## Hallazgos

| de | modelo y esfuerzo | hallazgo | qué hice |
|---|---|---|---|
| `/code-review` 1 | alto | la regla del `title` estaba en dos lugares (helper y guardado del cliente) | `d5b9e626`: el guardado manda `input` |
| `/code-review` 1 | alto | el proveedor no comprobaba lo que queda al guardar | `83b24a84`: el caso lo espera en los dos |
| `/code-review` 1 | alto | después del caso no se miraba `__xss` | lo agregué en `83b24a84`; la 2.ª pasada mostró que no podía fallar (se escribe en `value` y `title`, que no son HTML) y lo saqué en `9459a0d4` |
| `/code-review` 1 | alto | un `title` sólo se ve con mouse: en táctil o con teclado no aparece | riesgo 1 |
| `/code-review` 1 | alto | el lector de pantalla puede leer el valor dos veces (nombre + descripción) | riesgo 2 |
| adversario 1 | Sonnet alto | el caso no distinguía `trim()` | `6bbd67ff`: blancos en los bordes; rojo arriba |
| adversario 1 | Sonnet alto | sin un camino de hoy con `title` viejo (guardado que falla o sale bien, NCM, peso, borrar, abrir otro) | — |
| adversario 2 | Sonnet alto | el aviso `input` no dispara `change` ni pisa lo que se siguió escribiendo; las anclas nuevas sabotean lo que dicen | — |
| `anclas_perdidas.py` | — | mi cambio en `clientes.js` dejó sin patrón dos sabotajes de `holanda423.sh` | `28d0476a` |

## Supuestos (reversibles)

1. El `title` está siempre, aunque la etiqueta entre. Ponerlo sólo cuando se corta pide medir el campo
   en cada cambio de ancho; al pasar el mouse sobre una etiqueta que entra se ve lo mismo que en el
   campo.
2. En el cliente, con el campo vacío ya no aparece «Origen» al pasar el mouse. El nombre accesible
   sigue en `aria-label`.
3. «Se elige otro»: los catálogos no tienen lista propia. Lo único que se elige son las sugerencias
   del navegador, y el caso las simula con el evento que manda Chrome, no con un clic en la lista
   real.

## Riesgos

1. Baja: en táctil o con teclado el `title` no se ve. La tarea dice «al pasar el mouse».
2. Baja: con `aria-label` o `<label>`, el `title` pasa a ser la descripción accesible y repite el
   valor. No lo probé con un lector de pantalla.
3. Baja: el caso lee el atributo. El tooltip nativo no se ve en un navegador sin ventana, así que no
   lo vi aparecer.

## Comandos para vos

Desde tu copia, con `PY` apuntando a tu venv.

```bash
python3 docs/pm/herramientas/chequeo-6.py 5e17da02 9459a0d4 | sed -n '2p;$p'
#   producto +16/−3   y   avisos: 1
python3 scripts/testing/anclas_perdidas.py 9459a0d4 | grep -cE 'catalogo_largo2|holanda423'
#   0
PY=$PY scripts/testing/sabotajes/holanda423.sh 9459a0d4 2>&1 | awk '/^ROJO/{n++} /^(VERDE|ROTO)|sin rojo/{print} END{print n" ROJO"}'
#   sabotajes sin rojo: 0
#   34 ROJO
PY=$PY scripts/testing/con_pg16.sh bash -c 'PG_URL="$BACKUP1A_PG_URL" scripts/testing/sabotajes/catalogo_largo2.sh 9459a0d4' 2>&1 | awk '/^ROJO/{n++} /^(VERDE|ROTO)|transacción|ítems a text|^fallas/{print} END{print n" ROJO"}'
#   ROJO  | el arranque traba las tablas en una transacción: dice «FALLA | el arranque y una escritura como guardar-uso andan los dos»
#   ROJO  | el arranque no pasa el origen de los ítems a text: dice «FALLA | operation_items.origen pasa a text y la fila vieja queda igual»
#   fallas: 0
#   39 ROJO
```

El rojo con el arreglo revertido, en un worktree descartable (puerto 8862). Lo corrí tal cual:
```bash
D=$(mktemp -d); git worktree add -q --detach $D/wt 9459a0d4 && cd $D/wt
git checkout 5e17da02 -- proyecto_maria/static/v2/paises_maria.js proyecto_maria/static/v2/screens/catalogo.js proyecto_maria/static/v2/screens/clientes.js
mkdir $D/data; env ENVIRONMENT=development JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef EMAIL_VERIFICATION_REQUIRED=false \
  GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares \
  ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x \
  DATABASE_URL=sqlite+aiosqlite:///$D/l.db CDI_DATA_DIR=$D/data $PY -m uvicorn proyecto_maria.main:app --port 8862 > $D/api.log 2>&1 &
until curl -s -o /dev/null http://127.0.0.1:8862/dashboard; do sleep 0.5; done
BASE_URL=http://127.0.0.1:8862 CDI_DB=$D/l.db node scripts/testing/pantalla_holanda423.js | tail -1; echo "rc=${PIPESTATUS[0]}"
kill %1; cd - >/dev/null; git worktree remove --force $D/wt
#   FALLA: catálogo del proveedor: al pasar el mouse no se ve lo guardado en 324 filas, como «423 · PAISES BAJOS»
#   rc=1
```
Sin la línea `git checkout 5e17da02 -- …`, da `OK: pantalla Holanda→423` y `rc=0`.

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5, rama `claude/dev-maria`; rutina trig_01Ukttby1fc4sGVQfSn1jC9U (/respondio), apagada: me despierta la PM. PM principal session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `35de2344`. Aceptadas: las de antes (… CATALOGO-PAIS sobre `8140f496`, D275 (a); ORIGEN-2 sobre `0d7401ed`, D276 (a), D277 (a)). Entregada, en revisión: CATALOGO-PAIS-2 (D275 b) sobre `9459a0d4` (title del origen en los dos catálogos), con el vencido de `catalogo_largo2.sh` en `cbd7718c`. Sin pieza marcada «apenas entregues». Próxima D: D278. Lecciones (además de las del historial de este archivo): el negativo de un arreglo va en el mismo SHA con el arreglo vaciado; cada número del informe sale de un log, también las cuentas de líneas («25 ROJO» eran 24); `anclas_perdidas.py <SHA>` después de tocar líneas que anclan sabotajes; un ancho en `ch` depende de la fuente: medir con Inter y con Liberation Sans (`fuente/arial.conf`); una regla de pantalla se mide en cada ancho de disposición; un sabotaje que falla en el primer elemento de una lista no prueba los de atrás; no editar `scripts/` mientras corre un guion de sabotaje: cortar las puertas y relanzarlas sobre el SHA nuevo; un valor puesto por código no dispara `input`; un campo de texto pierde los saltos de línea; puertas con `setsid nohup`; horas, sólo de `date -u`; los comandos para la PM se prueban antes de escribirlos; un borrador con huecos no se sube. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica; subagentes hasta esfuerzo alto, sin consejero, nunca Fable; detener los subagentes después de su informe. Letra ancha: tabla U+FF01..FF5E, no NFKC («№» da Noruega).
