# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ORG-1 + ORG-1b + DESPACHO-1a: **entregada** en `3aaa3c4` (2026-10-28, 16:37 UTC)

**Por qué ahora y no a las 18:00:** Emi escribió en tu sesión a las 16:20:19 UTC
«Háganlo ahora que hay q gastar cupo tenés 2 horas antes q se reinicie», y vos
me pasaste la orden a las 16:20. Lo verifiqué en tu sesión. Mi canal todavía
dice «espera a las 18:00»: uso la palabra de Emi verificada.

**Resultado:** la pieza es `4ce6d22` (base `fb11735`, tabla de abajo), más un
arreglo dentro de la tarea que encontró la autorrevisión:
- `6b9762e` fix (producto + CHANGELOG): invitar valida el email con el mismo
  criterio que el registro y con el largo de la columna (100). Antes bastaba
  una «@»: esa invitación no la podía usar nadie (el registro la rechaza y el
  email está fijo desde ORG-1b) y ocupaba un lugar 7 días. Con más de 100
  caracteres daba 500 en Postgres.
- `3aaa3c4` test: 6 emails malos dan 400 y no ocupan lugar; 2 buenos se
  invitan y se registran.
  - Rojo con el `main.py` anterior: «6 failed, 1 passed, 46 deselected».
  - Verde: `test_org1.py` + `test_despacho1a.py`, «66 passed, 3 warnings in 40.22s».
- **No corrí** la suite completa sobre `3aaa3c4` ni los sabotajes de nuevo; la
  suite de `4ce6d22` está en la tabla de abajo.

**Decide la PM:** la D40 (abajo de esta tabla).

| Revisor | Modelo y esfuerzo | Hallazgos | Qué hice |
|---|---|---|---|
| org1-sonnet | Sonnet alto | R1 media: email sólo con «@» (regresión). R2 baja: dos registros a la vez con dos tokens del mismo email → 500, sin pérdida. R3 baja: plan fuera de la lista → 500 (hoy no hay camino que lo escriba) | R1 arreglado (`6b9762e`); R2 y R3, riesgos |
| org1-opus | Opus alto | R1 media: una pendiente para un email que ya tiene cuenta ocupa lugar 7 días; y si X entra con t1, t2 sigue pendiente, así que sacar a X no libera el lugar. R2 = email. R3 baja: email > 100 → 500 en PG. R4 = R2 de Sonnet. R5 baja, fuera: `inf`/`nan` salen como celda vacía en el xlsx | R2 y R3 arreglados; R1 → **D40**; R4 y R5, riesgos |
| `/code-review high` sobre `fb11735..4ce6d22` | Opus, en fork | 10 sin verificar: los dos de arriba (asiento ocupado, email), plan desconocido → 500, `with_for_update` no hace nada en SQLite, xlsx sync en ruta async, `clientes.js:1549` llama `res.json()` con `res` null, consulta y descarga duplicadas, el nombre de archivo del JS no coincide con el del servidor, el tope carga emails en vez de `count()` | Email arreglado; el resto, riesgos bajos (SQLite no es producción; lo demás es limpieza) |
| `/security-review` sobre el mismo rango | Opus alto | Sin altas ni medias. La skill falló al arrancar: «fatal: ambiguous argument 'origin/HEAD...': unknown revision or path not in the working tree.»; la revisión se hizo a mano sobre el diff. Probó inyección de fórmulas en el xlsx (todo sale como texto), `Content-Disposition`, XSS en la landing y el toast | Nada que arreglar |

**D40 — invitaciones que ocupan lugar sin poder usarse (ORG-1, org1-opus R1).**
Una invitación pendiente cuenta para el tope de 3 hasta que vence (7 días).
Hay dos casos en los que no la puede usar nadie: el email ya tiene cuenta en
otro estudio (el registro dice «Email ya registrado»), o ya entró con otra
invitación al mismo email.
- (1) Al invitar, rechazar el email que ya tiene cuenta, y al registrarse con
  una invitación, dar por usadas las otras pendientes del mismo email en ese
  estudio. Es chico, con su rojo antes, en esta misma pieza.
- (2) Dejarlo para la D26 (cancelar invitaciones), que resuelve esto y más.
- (3) Dejarlo como está: vence a los 7 días.

Recomiendo la (1): sin eso, un estudio de 3 puede quedar trabado una semana
por un error de tipeo del admin, y la D26 no tiene fecha.

**Riesgos que quedan (bajos):**
- Dos registros simultáneos con dos tokens del mismo email: uno da 500 en vez de 400. No se pierde nada.
- Un plan fuera de la lista da 500 al invitar y al registrarse; hoy no hay camino que lo escriba.
- En SQLite `with_for_update` no hace nada; en Postgres la carrera está cubierta por `org1_postgres.py`.
- El xlsx se arma de forma síncrona dentro de la ruta async: un catálogo enorme frena el servidor mientras se genera.
- `inf` y `nan` salen como celda vacía en el xlsx.
- `clientes.js:1549` llama `res.json()` con `res` null cuando la red falla: el toast muestra un error genérico.

## DESTINO-1: **entregada** en `f887b4a` (2026-10-28, 16:41 UTC)

**Resultado:** la pieza es `f887b4a` (base `4ce6d22`): producto `7526be9`,
pruebas y sabotajes hasta `f887b4a`. Suite completa sobre `f887b4a`: 3697
passed, 336 skipped, 2 xfailed, 0 failed; sabotajes 15/15 en rojo
(`destino1.sh`). La autorrevisión no encontró nada alto ni medio dentro de la
tarea: **no hay arreglo nuevo** y el SHA es el mismo de la tabla de abajo.

**Decide la PM:** nada. La D28 (ocho pruebas comparan el golden entero, no
seis) ya la anoté en la sección «hecha» de abajo.

| Revisor | Modelo y esfuerzo | Hallazgos | Qué hice |
|---|---|---|---|
| destino1-sonnet | Sonnet alto | Nada reproducible. Tres bajas que ya estaban: el aviso por defecto, `despachante.js:369`, `NONE`/`N/A` en `iva_adicional` | Riesgos |
| destino1-opus | Opus alto | Ningún par de Ganancias o IVA adicional fuera de los tres, ni una mezcla de destinos sin aviso: 100 combinaciones de renglones juntados y grupos, valores viejos o raros (`None`, `''`, minúsculas, `NONE`, `\x00`), sub-ítems y mezcla en un pedido. Dos bajas: (1) `despachante.js:74/357/369` compara con `===` y el servidor normaliza mayúsculas y espacios: un `'ivaad1'` en el estado local muestra «Igual que la operación» y sale USOPAR+IVAAD1; la pantalla nunca guardó minúsculas, sólo se llega editando `cdi_v2_state`. (2) El destino de un sub-ítem se ignora (vale el del ítem); la pantalla no lo ofrece y el MARIA declara un par por ítem | Riesgos |
| `/code-review high` sobre `4ce6d22..f887b4a` | Opus alto, en fork | Todo bajo. (1) Reproducido, ya estaba: el aviso «COMERC + NO_VALIDA por defecto» sale con la operación vacía aunque todos los ítems hayan elegido el suyo (`maria_generator.py:2156`); la pieza sólo cambió el texto. (2) Dos dicts paralelos: si uno pierde una clave, `KeyError` → 500. (3) La lista de destinos del JS es una copia a mano. (4) La regla ítem/operación está en tres lugares y «Ítem N» cuenta distinto. (5) La lista `PRUEBAS` de `destino1.sh` es manual (hoy completa). (6) Un nombre de test viejo | Riesgos. Descartado: que un `IVAAD1` guardado pase a USOPAR; lo pide la tarea |
| `/security-review` sobre el mismo rango | Opus alto | Sin hallazgos. La skill falló al arrancar: «fatal: ambiguous argument 'origin/HEAD...': unknown revision or path not in the working tree.»; se hizo a mano sobre el diff | Nada |

**Riesgos que quedan (bajos):** los de la tabla. El que más engaña es el
aviso por defecto con la operación vacía: dice «COMERC + NO_VALIDA» aunque
cada ítem haya elegido el suyo. El TXT sale bien; el aviso, no. Ya estaba
antes de la pieza.

```bash
git diff --stat 4ce6d22..f887b4a -- . ':!docs'
PY=python bash scripts/testing/sabotajes/destino1.sh f887b4a   # 15/15 en rojo
```

## SUFIJOS-2: **entregada** en `bd76f9f` (2026-10-28, 17:03 UTC)

**Resultado:** la pieza es `4ca6829` (base `4905cd8`) más un arreglo
encima de HEAD, como ORG-1: producto y `CHANGELOG.md` `91f0fb6`, pruebas
y sabotajes `15566a0`, `4821fff` y `bd76f9f`. El arreglo sale de dos
medias reproducidas en la autorrevisión: **un número al que el MARIA le
saca el signo, la barra o un punto de miles salía cambiado de valor en
el TXT.** Ahora no se genera y el aviso dice dónde. Rojo con el producto
viejo y las pruebas nuevas: «19 failed, 41 passed». Sabotajes
`sufijos2.sh` sobre `bd76f9f`: 17 de 17 en rojo, «sabotajes sin rojo: 0».
Suite completa sobre `4821fff`: «4005 passed, 336 skipped, 2 xfailed», `compileall 0`, 0 failed. Entre `4821fff` y `bd76f9f` sólo cambia `sufijos2.sh`, que pytest no junta; la suite sobre `bd76f9f` no la corrí.

**Decide la PM:** nada. Lo que el arreglo deja afuera va en riesgos.

| Revisor | Modelo y esfuerzo | Hallazgos | Qué hice |
|---|---|---|---|
| sufijos2-sonnet | Sonnet alto | R1 media, dentro: `ZA(.5)` salía `ZA( 5)`, `ZA(-5)` salía `ZA( 5)` y `AF(-2.5)` salía `AF( 2,5)`. R2 media-baja: el error del sufijo de un ítem no sale en los avisos. R3 baja: `ZA(5.0)` rechazado (D29 a). R4 baja: dígitos que no son ASCII dicen «está vacío». R5 baja: coma en `V1.5`, `AR(12.2027)` | R1 arreglado. Lo demás, riesgos |
| `/code-review high` sobre `4905cd8..4ca6829` | Opus alto, en fork | (1) media, reproducida: un Z no entero sin coma salía cambiado: `ZA(1/2)` → `ZA(1 2)`, `ZA(1,000.50)` → `ZA(1 000 50)`, `ZA(16.384.000)`, `ZA(2-5)`, `ZA(1½)` → `ZA(11 2)`. (2) media, reproducida: el punto de miles se tomaba como coma: `AJ(ROLLO 1.500 M)` → `AJ(ROLLO 1,500 M)`. (3) media, reproducida: los errores nuevos del sufijo de un ítem (vacío, Z con decimales) no salen en `supuestos_declarados`. (4) baja: `AB(MODELO V2.5)` → `V2,5`, `AI(6.2G)` → `6,2G`. (5) baja: `AA(华为)` dice «vacío». (6) baja: `AF(1.5²)` → `1,52`. (7) baja: hay Z de texto (`GRANULOMETRIA`) y Z con decimales normales (`ESPESOR`, `QUILATES`). (8) sospecha: Z en décimas de mm, decimales implícitos | (1), (2) y (6) arreglados. Lo demás, riesgos |
| `/security-review` | no corrido | La pieza no toca dinero, sesión, permisos ni datos. Inyección en el TXT, a mano: los caracteres que no son del MARIA ya salían como espacio; nada nuevo | Nada |

No corrí un adversario Opus aparte para esta pieza: el `/code-review` ya
fue Opus alto.

**Qué cambia con el arreglo** (`proyecto_maria/core/maria_generator.py` y
`proyecto_maria/core/sufijos_arca.py`):
- En un Z sólo pasa un entero: un signo, una barra, un punto o una coma
  junto a un dígito da el error «pide un número sin decimales… Escribilo
  entero, sin punto, coma, signo ni barra».
- En un libre, un número que cambiaría de valor da el error «en «AF(…»,
  «-5» cambiaría de valor… Escribí los decimales con coma y los miles sin
  separador (1500, no 1.500)». Cuenta como que cambiaría: un signo pegado
  al número (`-5`, `.5`), una barra (`1/2`), más de un separador
  (`1,000.50`, `16.384.000`), un punto seguido de tres dígitos sin cero
  adelante (`1.500`) y un dígito que no es ASCII pegado a un número
  (`1½`, `1.5²`).
- Sigue igual: `AJ(0.750)` → `AJ(0,750)`, `AJ(1,500)` igual,
  `AB(RT-AC68U)` → `AB(RT AC68U)`, `AI(123-456)` → `AI(123 456)`,
  `AI(V1.2.3)` → `AI(V1 2 3)`, `AJ(1,5 M²)` → `AJ(1,5 M2)`. El golden no
  cambió.

**Riesgos que quedan:**
- **Media, de diseño:** un error del sufijo de un ítem frena la generación,
  pero no sale en `supuestos_declarados` (code-review 3, sonnet R2). El
  error de la generación sí llega como 400 y dice dónde.
- **Baja:** en un libre, `2-5` o `38-40` (un rango) sale `2 5`; lo dejé
  pasar porque `123-456` es un código de pieza común. `V2.5` sale `V2,5`
  y `6.2G` sale `6,2G`. `AA(华为)` dice «vacío». Varios separadores pegados
  a una letra (`V1.2.3`) salen con espacios, como antes.
- **Para el despachante (D29):** hay Z que son texto (`GRANULOMETRIA`): con
  el arreglo, un `10-20` en un Z da error. Y puede haber Z con decimales
  implícitos (décimas de mm).

**Archivos de producto:** `proyecto_maria/core/maria_generator.py`,
`proyecto_maria/core/sufijos_arca.py`.

**Corrección:** la hora de entrega de DESTINO-1 fue 16:41 UTC, no 16:50
(commit `eacf591`, 16:41:09). La corregí en su encabezado.

```bash
git diff --stat 4905cd8..4ca6829 -- . ':!docs'       # la pieza
git diff --stat eacf591..bd76f9f -- . ':!docs'       # el arreglo: 5 files changed, 142 insertions(+), 9 deletions(-)
PY=python bash scripts/testing/sabotajes/sufijos2.sh bd76f9f   # «sabotajes sin rojo: 0»
```

Arriba de `bd76f9f` ya están `bf6e1d7` y `5dfaf47`: el arreglo de SEGURO-1, que va en su propia entrega, la que sigue.

## SEGURO-1: **entregada** en `5dfaf47` (2026-10-28, 17:10 UTC)

**Resultado:** la pieza es `371cde2` (base `1948207`) más un arreglo
encima de HEAD, como ORG-1: producto y `CHANGELOG.md` `bf6e1d7`, caso y
sabotaje `5dfaf47` (base del arreglo: `bd76f9f`). El arreglo sale de una
media reproducida en la autorrevisión: **si los avisos no contestaban (400
o red), la pantalla ofrecía «Dejar el seguro» con CIF, y el 1 % calculado
salía en el TXT.** Ahora no se ofrece. Rojo del caso nuevo con el producto
de `bd76f9f`: `assert False is True` (el botón se mostraba). Sabotajes
`seguro1.sh` sobre `5dfaf47`: 11 de 11 en rojo, «sabotajes sin rojo: 0».
Suite completa sobre `5dfaf47`, desde un worktree limpio: «4007 passed, 336 skipped, 2
xfailed», 0 failed, `compileall 0`.

**Decide la PM:** nada. La D30 ya está contestada (a); el hallazgo alto
del code-review es esa misma D y va en riesgos.

| Revisor | Modelo y esfuerzo | Hallazgos | Qué hice |
|---|---|---|---|
| seguro1-opus | Opus alto | R1 media, dentro: avisos con 400 → la pantalla queda sin `seguro_en_el_precio` → «Dejar el seguro» con CIF → `/generate_maria` 200 con `MDDTASS 93.13` (reproducido con el arnés `_pantalla` de `test_valor1.py`). R2 baja, fuera: DAT, DDU, DES, DEQ y DAF con 1 %; `review.js:160` sin DPU. R3 baja (D30): CIF con seguro vacío sale `MDDTASS 0.00` | R1 arreglado. Lo demás, riesgos |
| seguro1-sonnet | Sonnet alto | R1 media, fuera: DAT, DAF, DES, DEQ y DDU sin la regla. R2 media: `review.js:160/604` avisa «ya incluye seguro» con una lista sin DPU: contradice a la pantalla del valor. R3 media (D30): CIF con seguro 0, el servidor no avisa. R4 baja: la pestaña vieja con el botón da 400 | Riesgos |
| `/code-review high` + `/security-review` | Opus alto, en fork; la security a mano porque la skill falló con `fatal: ambiguous argument 'origin/HEAD...'` | (1) **alta**: calcular con CFR y pasar a CIF borra el seguro, viaja vacío, el servidor no frena y sale `MDDTASS 0` con un aviso del semáforo (es la D30). (2) media = opus R1. (3) baja: DAT…DDU. (4) baja: el texto «No pudimos leer el seguro». (5) baja: un aviso transitorio viejo (`finalize.js:431`). (6) baja: `review.js:160`. (7) calidad. (8) sospecha: con un pedido en vuelo de otra firma, 400 sin salida. Security: nada | (2) arreglado. Lo demás, riesgos |

**Qué cambia con el arreglo** (`proyecto_maria/static/v2/screens/finalize.js`,
`pintarValor`): «Dejar el seguro» no se ofrece cuando el error es
`SIN_CUENTAS` («No se pudieron hacer las cuentas: mirá los avisos.»), que
la pantalla pone cuando los avisos dan 400 o fallan por red. Sin
respuesta no se sabe si el incoterm lleva el seguro en el precio.

**Supuesto reversible:** con `SIN_CUENTAS` tampoco se ofrece con CFR o
FOB; se ofrece de nuevo cuando los avisos contestan. Distinguir por
`op.incoterm` contradiría «la pantalla sigue al servidor».

**Riesgos que quedan:**
- **Alta, ya decidida (D30 (a)):** con CIF, un seguro vacío sale
  `MDDTASS 0.00`; la pantalla avisa y no frena. Pasa también al calcular
  con CFR y cambiar a CIF. Frenarlo es SEGURO-2.
- **Media, fuera:** DAT, DDU, DES, DEQ y DAF (incoterms viejos) siguen con
  el 1 %. `review.js:160` (`INCOTERM_INCLUYE_FLETE`, sin DPU) y su aviso de
  la línea 604 ya existían y contradicen la regla nueva en DPU.
- **Baja:** el semáforo dice «No pudimos leer el seguro» cuando lo borró
  el sistema; un aviso transitorio viejo en `finalize.js:431`; la pestaña
  abierta antes del despliegue muestra el botón y da 400 (no sale el 1 %);
  sospecha sin reproducir: con un pedido en vuelo de otra firma, 400 sin
  salida.

**Archivos de producto:** `proyecto_maria/core/maria_generator.py`,
`proyecto_maria/main.py`, `proyecto_maria/static/v2/screens/finalize.js`,
`CHANGELOG.md`.

```bash
git diff --stat 1948207..371cde2 -- . ':!docs'   # la pieza: 8 files changed, 406 insertions(+), 15 deletions(-)
git diff --stat bd76f9f..5dfaf47                  # el arreglo: 4 files changed, 23 insertions(+)
PY=python bash scripts/testing/sabotajes/seguro1.sh 5dfaf47   # 11 ROJO, «sabotajes sin rojo: 0»
python -m pytest -q --no-cov tests/test_seguro1.py             # 48 passed
```

## DESPACHO-1b: **entregada** en `e59e1a8` (2026-10-28, 17:11 UTC)

**Resultado:** la pieza como está en `e59e1a8` (base `49f8e29`), sin
arreglo: no me alcanzó el tiempo antes de las 18:00 para arreglar con rojo,
sabotaje y suite. Suite completa sobre `e59e1a8`: 3827 passed, 336
skipped, 2 xfailed, 0 failed. Sabotajes `despacho1b.sh`: 24/24 en rojo.
Lo que encontraron los revisores va abajo como riesgos; ninguno es una
regresión (es lectura nueva), pero tres son medias dentro de la pieza.

**Decide la PM:** D41.

- **D41 (DESPACHO-1b):** las tres medias de abajo (lectura cuadrática,
  peso infinito y fusión de renglones con NCM distinto). (1) Las arreglo
  después de las 18:00, encima de la cadena, antes de publicar
  (recomendada: el 500 del catálogo y la fusión dejan datos mal guardados
  en la memoria del cliente). (2) Se publica así y van a una pieza nueva.

| Revisor | Modelo y esfuerzo | Hallazgos | Qué hice |
|---|---|---|---|
| despacho1b-sonnet | Sonnet alto | 1 media: `_valores_por_columna` es cuadrática (`despacho_lector.py:144-171`): un PDF de 97 KB con 20 000 valores tarda 25,6 s; cinco subidas llenan el pool de lectura de PDF, compartido (504 a otros). 2 media: peso = kilo/cantidad puede dar `inf` (cantidad `1e-320`) y el GET del catálogo de productos da 500 (`despacho_lector.py:468`). 3 media: guardar funde renglones con NCM distinto por el respaldo por descripción (`client_memory.py:109-126`); mi informe decía «mismo NCM». 4 baja-media: 500 renglones tardan 8 a 29 s y guardar no es idempotente (`veces_usado` 2 al guardar dos veces). 5 baja: NCM con puntos queda en varias formas. 6 baja: sufijos cortados por un salto de hoja se pierden | Riesgos (D41) |
| `/code-review high` + `/security-review` | Opus alto, en fork; la security a mano porque la skill falló con `fatal: ambiguous argument 'origin/HEAD...'` | Medias: una línea de sufijo que no se entiende pierde las siguientes (`despacho_lector.py:310`); el salto de página corta sufijos (`:267`); el upsert por parecido funde productos con NCM distinto y `guardados` los cuenta (`main.py:8066`); una línea de rótulos sin valores se come la siguiente (`:279`). Baja-media: guardar no idempotente; NCM con y sin puntos; pool de lectura de PDF bloqueable. Bajas: `startswith` de CONCEPTOS; mensaje naranja en `clientes.js:1661`; muchas consultas; guardar sin tope de pedidos (security) | Riesgos (D41) |

Los tiempos y el 500 del Sonnet salen de sus corridas; lo demás es
lectura. Yo no los reproduje.

**Riesgos que quedan:** todo lo de la tabla. Lo que más pesa: un PDF
grande traba la lectura de PDF de todos (también el lector de facturas);
un renglón con cantidad casi cero deja el catálogo en 500; y guardar puede
fundir dos productos de NCM distinto en la memoria del cliente.

**Archivos de producto:** `proyecto_maria/core/despacho_lector.py` (nuevo),
`proyecto_maria/main.py`, `proyecto_maria/static/v2/app_v2.css`,
`proyecto_maria/static/v2/screens/clientes.js`,
`proyecto_maria/templates/dashboard_v2.html`, `CHANGELOG.md`.

```bash
git diff --stat 49f8e29..e59e1a8 -- . ':!docs'   # 9 files changed, 1747 insertions(+), 2 deletions(-)
PY=python bash scripts/testing/sabotajes/despacho1b.sh e59e1a8   # 24 ROJO, «sabotajes sin rojo: 0»
```

## DATOS-1: **entregada** en `c996ad4` (2026-10-28, 17:13 UTC)

**Resultado:** la pieza como está en `c996ad4` (base `d01f95c`), sin
arreglo. Suite completa sobre `c996ad4`: 3836 passed, 336 skipped, 2
xfailed, 0 failed; `compileall` 0. Sabotajes `datos1.sh`: 12/12 en rojo.
Postgres 16: «fallas: 3» antes, «fallas: 0» después. Detalle en «DATOS-1:
hecha» más abajo.

**Lo que es lectura y lo que corrí:** los hallazgos son lectura de los
revisores; no reproduje ninguno.

**Decide la PM:** nada nuevo. Los hallazgos van como riesgos.

| Revisor | Modelo y esfuerzo | Hallazgos | Qué hice |
|---|---|---|---|
| datos1-sonnet | Sonnet alto | Nada dentro. Bajas, fuera: el `HEALTHCHECK` del `Dockerfile` también ve el 503; los 502 de `main.py:8687` y `:8897` llevan `{err}`; el dashboard viejo muestra `<pre>{e}</pre>` (`main.py:2306`) | Riesgos |
| `/code-review high` + `/security-review` | Opus alto, en fork; la security a mano porque la skill falló con `fatal: ambiguous argument 'origin/HEAD...'` | (1) media: el manejador tapa sólo los 500; los 502 de `main.py:8687` y `:8897` devuelven el texto de un tercero tal cual, así que la D6 queda incompleta. (2) media, sospecha: el borrado filtra por `owner_username`, y una fila vieja con dueño `NULL` sobrevive y daría 500 de FK en Postgres. (3) media: `/health` con 503 haría que Railway rechace la publicación. (4) baja: carrera entre compartir y borrar. (5) baja: cascada a mano. (6) baja: una traza en el log por cada `/health` sin base. (7) baja: el 500 no lleva un id para buscarlo en el log. (8 a 10) pruebas: la limpieza ignora errores del `DELETE`, otro loop, psycopg2 sin cerrar | Riesgos. La (3) la contradigo abajo |

**La (3) no cambia lo que ya informé:** si la base no contesta al
arrancar, `init_db` corre sin `try` y uvicorn sale con código 3, así que
`/health` no contesta nunca, con o sin 503. El 503 sólo aparece si la base
se cae con la app ya andando. Lo del Railway sigue sin verificar
(`docs.railway.com` bloqueado desde acá); Emi lo tiene que saber antes de
publicar.

**Riesgos que quedan:** los 502 con texto de un tercero (fuera de la D6,
que era de los 500); la sospecha de las filas con dueño `NULL` en Postgres,
sin reproducir; el `HEALTHCHECK` del `Dockerfile` marca el contenedor como
no sano mientras la base no contesta; la carrera entre compartir y borrar,
que es lectura del revisor y no la reproduje. La pantalla vieja
(`app.js`) sigue sin avisar que se borran los links.

**Archivos de producto:** `proyecto_maria/main.py`,
`proyecto_maria/static/v2/screens/clientes.js`,
`proyecto_maria/static/v2/screens/finalize.js`, `CHANGELOG.md`.

```bash
git diff --stat d01f95c..c996ad4 -- . ':!docs'   # 7 files changed, 568 insertions(+), 24 deletions(-)
PY=python bash scripts/testing/sabotajes/datos1.sh c996ad4   # 12 ROJO, «sabotajes sin rojo: 0»
python -m pytest -q --no-cov tests/test_datos1.py             # 9 passed
```

## DISCO-1: **entregada** en `88b22c8` (2026-10-28, 17:14 UTC)

**Resultado:** la pieza como está en `88b22c8` (base `cf84a76`), sin
arreglo. Suite completa sobre `88b22c8`: 3847 passed, 336 skipped, 2
xfailed, 0 failed. Sabotajes `disco1.sh`: 20/20 en rojo. Detalle en
«DISCO-1: hecha» más abajo. **Hay una regresión leída y no reproducida:
no recomiendo publicar sin arreglarla (D42).**

**Decide la PM:** D42.

- **D42 (DISCO-1):** dos hallazgos dentro de la pieza. (a) La regresión:
  en `sugerir_ncm` (`main.py:9382`, `:9401`, `:9407`) los pasos 1 y 2
  atrapan la excepción sin `rollback`; en Postgres la transacción queda
  abortada y el historial que se lee después sale vacío, sin aviso. Antes
  el historial era un archivo y eso no pasaba. (b) Un carácter NUL en una
  descripción hace que Postgres rechace la fila: el archivo entero no
  carga y se reintenta en cada arranque, y guardar-uso da 500. (1) Los
  arreglo después de las 18:00, encima de la cadena, con rojo en Postgres
  16 y sabotaje, antes de publicar (recomendada: (a) deja sin sugerencias
  sin que nadie se entere). (2) Se publica así y van a una pieza nueva.

| Revisor | Modelo y esfuerzo | Hallazgos | Qué hice |
|---|---|---|---|
| disco1-sonnet | Sonnet alto | R1 media, dentro: NUL (`\u0000`) en la descripción, Postgres rechaza (`CharacterNotInRepertoireError`), el archivo no carga y se reintenta en cada arranque; guardar-uso da 500. R2 baja: un surrogate (`\ud800`) da `UnicodeEncodeError` y el archivo no carga (`main.py:9047`). R3 baja: sin tope de tamaño, un archivo de 64 MB traba el arranque 50 s. La carrera con 3 procesos en Postgres, bien | D42 (b); lo demás, riesgos |
| `/code-review high` + `/security-review` | Opus alto, en fork; la security a mano porque la skill falló con `fatal: ambiguous argument 'origin/HEAD...'` | (1) alta, sin confirmar: sin volumen en Railway el primer deploy pierde los historiales (es la D33, contestada (a)). (2) media, regresión, leída: `sugerir_ncm` sin `rollback`. (3) media: `_sumar_uso_ncm` sin proteger da 500, y suma antes de `_get_owned_client`: con un `client_id` ajeno suma y después da 404 (`:9481`). (4) baja-media: las pruebas sin `CDI_DATA_DIR` migran el `data/` real del dev; los huérfanos se reintentan y se loguean en cada arranque (`:1398`). (5) media, sospecha: deadlock entre dos importaciones simultáneas (`:9088`). (6 a 10) bajas. Security: un huérfano lo hereda quien registre ese nombre de usuario en el próximo deploy (`:9076`, `:9156`); 500 con `str(exc)` del driver (`:9612`) | (2) D42 (a); lo demás, riesgos |

**Lo que es lectura y lo que corrió cada uno:** el NUL, el surrogate y los
64 MB salen de las corridas del Sonnet; la regresión de `sugerir_ncm` es
lectura del code-review. Yo no reproduje ninguno.

**Riesgos que quedan:** la D33 (el primer deploy pierde los historiales
salvo que Emi los rescate); el 500 de guardar-uso y la suma con un
`client_id` ajeno; la herencia del huérfano por quien registre su nombre;
la sospecha de deadlock entre importaciones; el arranque lento con un
archivo enorme; las pruebas que pueden migrar el `data/` real de quien
las corre sin `CDI_DATA_DIR`.

**Archivos de producto:** `proyecto_maria/database/models.py`,
`proyecto_maria/main.py`, `CHANGELOG.md`.

```bash
git diff --stat cf84a76..88b22c8 -- . ':!docs'   # 8 files changed, 990 insertions(+), 42 deletions(-)
PY=python bash scripts/testing/sabotajes/disco1.sh 88b22c8   # 20 ROJO, «sabotajes sin rojo: 0»
python -m pytest -q --no-cov tests/test_disco1.py
```

## OBSERVABILIDAD-1: **entregada** en `39be45e` (2026-10-28, 17:14 UTC)

**Resultado:** la pieza como está en `39be45e` (base `88b22c8`; el código
es el de `7ae35ab`), sin arreglo. Suite completa sobre `39be45e`: 3855
passed, 336 skipped, 2 xfailed, 0 failed. Sabotajes `observabilidad1.sh`:
16/16 en rojo. Detalle en «OBSERVABILIDAD-1: hecha» más abajo.

**Decide la PM:** nada nuevo. La D34 ya está contestada (a).

| Revisor | Modelo y esfuerzo | Hallazgos | Qué hice |
|---|---|---|---|
| observabilidad1-sonnet | Sonnet medio | Nada dentro. Bajas: sin FK (igual que el modelo); `CREATE INDEX` sin `CONCURRENTLY`; un índice parcial con ese nombre cuenta como existente | Riesgos |
| `/code-review high` + `/security-review` | Opus alto, en fork; la security a mano porque la skill falló con `fatal: ambiguous argument 'origin/HEAD...'` | (1) media: `MetricsMiddleware` no graba `owner_username` (es la D34 (a); la prueba afirma `None`). (2) baja-media, sospecha: el `ALTER` y el `CREATE INDEX` van en la misma transacción y bloquean `api_logs`; sin `statement_timeout`, contra los 60 s del healthcheck. (3) un índice `INVALID` o parcial pasa el chequeo. (4) `current_schema` contra `regclass`. (5) dos arranques a la vez dejan un log confuso. (6) sin FK. (7) un comentario. Security: el token de invitación queda en `api_logs.endpoint` y se ve en `/api/dev/stats` (sólo admin); es código previo que la pieza vuelve a hacer andar | Riesgos |

**Lo que es lectura y lo que corrí:** los hallazgos son lectura de los
revisores; no reproduje ninguno.

**Riesgos que quedan:**
- **Media, security:** con las métricas andando de nuevo, la URL de
  la invitación (`/api/invitations/{token}`) queda guardada con el token
  en `api_logs` y la ve el admin en `/api/dev/stats`. Antes de esta pieza,
  en una base sin la columna, no se guardaba nada porque cada insert
  fallaba. Propuesta (otra pieza): guardar la ruta sin el token.
- **Propuesta de la D34:** que `MetricsMiddleware` lea el dueño del token
  y lo grabe; toca sesión y autenticación.
- **Baja:** con una `api_logs` grande, el primer arranque bloquea la
  tabla mientras crea el índice (sin medir); un índice inválido o parcial
  con ese nombre no se rehace.

**Archivos de producto:** `proyecto_maria/main.py`, `CHANGELOG.md`.

```bash
git diff --stat 88b22c8..39be45e -- . ':!docs'   # 5 files changed, 760 insertions(+)
PY=python bash scripts/testing/sabotajes/observabilidad1.sh 39be45e   # 16 ROJO, «sabotajes sin rojo: 0»
python -m pytest -q --no-cov tests/test_observabilidad1.py
```

## SESION-1: **entregada** en `895ee73` (2026-10-28, 17:15 UTC)

**Resultado:** la pieza como está en `895ee73` (base `f5160d7`), sin
arreglo. Suite completa sobre `895ee73`: 3872 passed, 336 skipped, 2
xfailed, 0 failed. Sabotajes `sesion1.sh`: 19/19 en rojo. Detalle en
«SESION-1: hecha» más abajo. **No recomiendo publicarla sin la D43.**

**Decide la PM:** D43.

- **D43 (SESION-1):** cuatro hallazgos dentro de la pieza. (a) Carrera:
  un login con la clave vieja que termina después del cambio de clave
  deja una sesión válida, porque gana el último que escribe `active_jti`
  (`main.py:2073-2077`, `1622-1623`, `2788-2790`); el revisor la
  reprodujo 9 de 12 veces en Postgres y 7 de 8 en SQLite. No es regresión
  (antes no se cortaba nada), pero la pieza promete cortar. (b) El cambio
  de clave no corta una cookie copiada (mismo `jti`), y el toast y el
  `CHANGELOG` dicen «cierra las otras». (c) `change-password` con la clave
  actual mal da 401 y `app_v2.js:36` manda al login. (d) Si la base no
  contesta, `logout` da 500 y no borra la cookie; antes la borraba
  siempre. (1) Los arreglo después de las 18:00, encima de la cadena, con
  rojo y sabotaje, antes de publicar (recomendada: es sesión, y (a) y (b)
  hacen que el texto prometa algo que no pasa). (2) Se publica así con el
  texto corregido y lo demás va a otra pieza.

| Revisor | Modelo y esfuerzo | Hallazgos | Qué hice |
|---|---|---|---|
| sesion1-opus | Opus alto | (1) media/alta, dentro: la carrera de D43 (a), reproducida: Postgres con cambio de clave 9/12, SQLite 7/8, Postgres con reset 1/8. (2) media: la cookie copiada, D43 (b). (3) baja/media, fuera: `/logout` de la v1 sin el header CSRF da 403 con `CSRF_ENFORCE` y el token sigue (`static/app.js:4094`). (4) **alta, fuera, ya existía:** si `ADMIN_USERNAMES` tiene un email, cambiar el email propio a ese da admin al reiniciar (`main.py:1457`). (5) baja: mi informe nombraba `token_jti` y otro SHA de puertas. Sospecha: `hash_password` fuera del threadpool en el reset | D43; lo demás, riesgos |
| sesion1-sonnet | Sonnet alto | R1 media/baja, dentro: `logout` da 500 sin borrar la cookie si cae la base (D43 (d)). R2 baja: el `PUT` del perfil sirve para probar claves sin límite (igual que `change-password`, de antes). R3 baja: un token sin `jti` con `active_jti` NULL saca al propio al cambiar la clave. R4 baja: cookie vieja más Bearer, `logout` no revoca el Bearer. R5 baja, fuera: un reset pendiente sobrevive al cambio de clave | D43 (d); lo demás, riesgos |
| `/code-review high` + `/security-review` | Opus alto, en fork; la security a mano porque la skill falló con `fatal: ambiguous argument 'origin/HEAD...'` | (1) media: D43 (c). (2) media, de antes: `GET /auth/me` no compara `active_jti`, así que un token revocado da 200 (contradice el `CHANGELOG`). (3) media, de antes: el token de `/auth/verify-email` dura 24 h, se puede reusar y crea una sesión nueva sin clave: se vuelve a entrar después de un reset o un logout. (4) = opus (3). (5) = sonnet R3. (6) baja, de antes: duplicado de email exacto; los links de reset sobreviven (sospecha). (7) calidad: el JWT se decodifica tres veces. Security: la telemetría toma el `sub` sin mirar `active_jti` (info) | D43 (c); lo demás, riesgos |

**Lo que es lectura y lo que corrió cada uno:** la carrera la reprodujo
el Opus con sus scripts; el 500 de `logout` y el `PUT` sin límite salen de
las corridas del Sonnet; lo demás es lectura. Yo no reproduje ninguno.

**Riesgos que quedan:**
- **Alta, fuera, de antes:** la subida a admin por email
  (`ADMIN_USERNAMES`, `main.py:1457`). Emi tiene que saber si esa variable
  tiene un email en producción.
- **Medias, de antes:** `/auth/me` acepta un token revocado; el token de
  verificar email sirve para volver a entrar durante 24 h después de un
  reset o un logout. Con esto, «cerrar las otras sesiones» no es completo
  aunque se arregle la D43.
- **Bajas:** el `logout` de la v1 sin CSRF; el `PUT` del perfil sin
  límite; un reset pendiente que sobrevive al cambio de clave.

**Archivos de producto:** `proyecto_maria/auth/dependencies.py`,
`proyecto_maria/main.py`, `proyecto_maria/static/v2/screens/profile.js`,
`proyecto_maria/templates/dashboard_v2.html`, `CHANGELOG.md`.

```bash
git diff --stat f5160d7..895ee73 -- . ':!docs'   # 10 files changed, 971 insertions(+), 35 deletions(-)
PY=python bash scripts/testing/sabotajes/sesion1.sh 895ee73   # 19 ROJO, «sabotajes sin rojo: 0»
python -m pytest -q --no-cov tests/test_sesion1.py
```

## ABUSO-1: **entregada** en `43916a7` (2026-10-28, 17:16 UTC)

**Resultado:** la pieza como está en `43916a7` (base `c702655`), sin
arreglo. Suite completa sobre `43916a7`: 3930 passed, 336 skipped, 2
xfailed, 0 failed. Sabotajes `abuso1.sh`: 27/27 en rojo. Detalle en
«ABUSO-1: hecha» más abajo. **Hay una regresión reproducida por el
revisor: no recomiendo publicar sin arreglarla (D44).**

**Decide la PM:** D44.

- **D44 (ABUSO-1):** el login ahora toma dos conexiones: la de la sesión
  del pedido y otra de `engine.begin` para sumar o limpiar el contador
  (`main.py:2770`, `2778`, `2827`). Con 120 logins malos a la vez desde IPs
  distintas, el revisor midió en Postgres 16 `401:96 / 500:24` y
  `401:85 / 500:35`, `/health` en 33,9 s y 33,1 s, y en el log «QueuePool
  limit of size 20 overflow 30 reached ... timeout 30.00»; sobre
  `c702655`, `401:120` y sin QueuePool. El fallo que termina en 500 no se
  cuenta. Hacen falta unas 100 IPs (slowapi deja 5 por minuto por IP).
  Es el mismo mecanismo que los «50 de 50 con 40 logins» de la D39, pero
  ahora con el número que muestra que lo agrava esta pieza. (1) Lo
  arreglo después de las 18:00, encima de la cadena: el contador usa la
  conexión del pedido, con rojo de concurrencia en Postgres 16 y sabotaje,
  antes de publicar (recomendada: es un 500 nuevo que traba también
  `/health`). (2) Se publica así y queda con la D39.

| Revisor | Modelo y esfuerzo | Hallazgos | Qué hice |
|---|---|---|---|
| abuso1-opus | Opus alto | (1) media, regresión, reproducida: la D44. (2) media, del diseño de la D35 (b): el tope de recuperar usuario (3 por hora por email, ventana fija) deja a la víctima sin mail 1 h con 4 pedidos desde otra IP; con el email en MAYÚSCULAS el pedido no encuentra cuenta pero el contador pasa a minúsculas (`main.py:1587`). (3) media, de antes (fila 14): el login correcto borra el contador de la IP; 4 fallos y un login propio por minuto nunca bloquean (unos 5700 intentos por día por IP). (4) baja, decidida: eventos anónimos, 240 filas y 1 920 000 caracteres en `props` en un minuto desde una IP. (5) baja: deadlock en Postgres entre el `DELETE` de vencidas y el upsert (`limites_auth.py:78`, `:92`): 18 de 400 con ventanas de 10 a 100 ms, 0 de 16 000 con 1 a 2 s. Sospechas: IPv6 /64; varios `X-Forwarded-For`; `TRUSTED_PROXY_HOPS=2` con acceso directo. **Aviso:** tocó la base `adv_email1_opus` (usuario `advpool1`, 60 logins fallidos desde 10.8.0.x) en el puerto 24817, local y descartable | D44; lo demás, riesgos |
| abuso1-sonnet | Sonnet alto | R1 media: `change-password` y el `PUT` del perfil sin límite (30 intentos, nunca 429). R2 media: el reset sin tope por email, unos 110 mails por día a una víctima desde una IP. R3 media: = opus (2). R4 media, fuera: = opus (3). R5 baja: invitaciones y verify-email sin tope. R6 baja: telemetría antes del login, 8000 caracteres sin retención. Sospechas: varias entradas de `X-Forwarded-For` en Railway dan una IP común; el puerto en la IP | Riesgos |
| `/code-review high` + `/security-review` | Opus alto, en fork; la security a mano porque la skill falló con `fatal: ambiguous argument 'origin/HEAD...'` | (1) media: = opus (1). (2) media: = opus (5). (3) baja: los topes de recuperar usuario y de registro sólo valen si `limiter.enabled`, que se apaga sólo en `conftest`: es un atajo de prueba en el producto (`main.py:1582`, `:2943`). (4) baja: los eventos sin sesión aceptan un token revocado (`main.py:2501`). (5) baja: cada 429 deja un WARNING. (6) baja: `logging_middleware` toma la primera entrada de `X-Forwarded-For`. (7 a 9) bajas. Security: el login ignora lo que devuelve `sumar_fallo`, así que al vencer el bloqueo una ráfaga prueba hasta 5 claves por IP cada 15 min (`main.py:2760`); `TRUSTED_PROXY_HOPS` mal puesto (D35, runbook); los topes son sólo por IP | D44; lo demás, riesgos |

**Lo que es lectura y lo que corrió cada uno:** el pool, el deadlock y
los eventos los midió el Opus con sus scripts; los 30 intentos sin 429 y
los mails por día salen del Sonnet; lo demás es lectura. Yo no reproduje
ninguno.

**Riesgos que quedan:**
- **Medias:** el tope por email de recuperar usuario silencia a la
  víctima; el reset sin tope por email; `change-password` y el perfil sin
  límite; el login correcto limpia el contador (de antes); el deadlock
  ocasional con ventanas cortas (con ventanas de 1 a 2 s no apareció en
  16 000; con las de producción no se midió).
- **Baja, regla de `CLAUDE.md`:** `limiter.enabled` funciona como atajo de
  prueba dentro del producto. Propuesta: que los topes propios no dependan
  de esa bandera.
- **Bajas:** lo demás de la tabla.

**Archivos de producto:** `proyecto_maria/core/limites_auth.py`,
`proyecto_maria/core/rate_limit.py`, `proyecto_maria/database/models.py`,
`proyecto_maria/main.py`, `HANDOFF.md`, `CHANGELOG.md`.

```bash
git diff --stat c702655..43916a7 -- . ':!docs'   # 13 files changed, 1454 insertions(+), 90 deletions(-)
PY=python bash scripts/testing/sabotajes/abuso1.sh 43916a7   # 27 ROJO, «sabotajes sin rojo: 0»
python -m pytest -q --no-cov tests/test_abuso1.py
```

## EMAIL-1: **entregada** en `2b93071` (2026-10-28, 17:16 UTC)

**Resultado:** la pieza como está en `2b93071` (base `e22a5cf`), sin
arreglo. Suite completa sobre `2b93071`: 3954 passed, 336 skipped, 2
xfailed, 0 failed. Sabotajes `email1.sh`: 13/13 en rojo, y `abuso1.sh`
sobre `2b93071`: 27/27. Detalle en «EMAIL-1: hecha» más abajo.

**Decide la PM:** D45.

- **D45 (EMAIL-1):** en Postgres, un email con «İ» (U+0130) esquiva el
  tope por email de recuperar usuario: Python y Postgres pasan esa letra
  a minúsculas distinto, y el revisor sacó 12 mails con un tope de 3. En
  SQLite no pasa. (1) Lo arreglo después de las 18:00, encima de la
  cadena, con rojo en Postgres 16 y sabotaje, antes de publicar
  (recomendada: es un tope que la pieza dice cumplir). (2) Se publica así
  y va a otra pieza.

| Revisor | Modelo y esfuerzo | Hallazgos | Qué hice |
|---|---|---|---|
| email1-opus | Opus alto | R1 media, dentro: la D45, reproducida en Postgres. R2 baja: el bootstrap de admin compara exacto (falla del lado seguro). Fuera: el alta de estudio y la invitación no validan el formato del email | D45; lo demás, riesgos |
| email1-sonnet | Sonnet alto | Nada dentro. Bajas: `func.lower` sin índice (el barrido lo acotan los topes por IP, `main.py:1524`); bootstrap de admin exacto, a propósito (`:1478`); `Client.email` exacto (fuera, `:6948`); un cambio sólo de mayúsculas se ignora con 200 (supuesto); `dev_token_hint` y el tiempo del SMTP, de antes | Riesgos |
| `/code-review high` + `/security-review` | Opus alto, en fork; la security a mano porque la skill falló con `fatal: ambiguous argument 'origin/HEAD...'` | (1) media, sospecha: sin índice único sobre `lower(email)`, una carrera crea un par y traba la recuperación y el login de las dos (es la D38 (3), que espera el conteo de Emi). (2) baja: `email1_motores.py:268-272` no distingue el defecto (pytest sí). (3) baja: `REGISTER_TEST_EMAIL_REPLACE` archiva variantes antes de validar. (4) baja: no recorta el guardado. (5) baja: el perfil no normaliza (D38). (6) `func.lower` sin índice. (7 y 8) consultas dobles y tiempo. (9) bootstrap exacto. (10) el script de motores no cierra la conexión. Security: el reset sin tope por email (de antes; está en ABUSO-1) | Riesgos |

**Lo que es lectura y lo que corrió cada uno:** los 12 mails los sacó el
Opus en su Postgres; lo demás es lectura. Yo no reproduje ninguno.

**Riesgos que quedan:** la carrera que crea pares hasta el índice de la
D38 (3); quien ya tiene un par y escribe otras mayúsculas no recupera
hasta la D38 (3); el perfil guarda el email como viene; el script de
motores no distingue el defecto en un punto (lo distingue pytest).

**Archivos de producto:** `proyecto_maria/main.py`, `CHANGELOG.md`.

```bash
git diff --stat e22a5cf..2b93071 -- . ':!docs'   # 6 files changed, 832 insertions(+), 25 deletions(-)
PY=python bash scripts/testing/sabotajes/email1.sh 2b93071   # 13 ROJO, «sabotajes sin rojo: 0»
python -m pytest -q --no-cov tests/test_email1.py
```

## CONEXIONES-1: **entregada** en `30c0e97` (2026-10-28, 17:18 UTC)

**Resultado:** la pieza como está en `30c0e97` (base `2b93071`), sin
arreglo. No cambia producto ni pytest. Sabotajes `conexiones1.sh`: «3 OK,
`FALLAS 0`» (una corrida limpia que da 0 y dos fugas que dan 1). Detalle en «CONEXIONES-1: medida» más abajo. **Los dos revisores
dicen que mi conclusión no se sostiene, y tienen razón en lo que leyeron:
la medición no prueba que el corte sea del `TestClient` (D46).**

**Decide la PM:** D46.

- **D46 (CONEXIONES-1):** lo que la medición no prueba. (a) La fase
  `cortes_del_cliente` puede quedar «quieta» antes de que el servidor
  procese los pedidos; el Sonnet vio 60 logins procesados después de
  «quieto», y el medidor no compara `api_logs` con los pedidos. Eso es un
  falso verde posible en el mecanismo de la D37. (b) Ningún pedido se
  cortó en vuelo: `cancelados = 0` sin un control que muestre que el
  medidor ve una cancelación cuando la hay, y ningún sabotaje cancela el
  `close`. Por eso «el corte es del `TestClient`» es una hipótesis, no un
  resultado; la D37 sigue abierta para el servidor real. (1) Rehago la
  medición después de las 18:00: espero a que `api_logs` tenga todos los
  pedidos en vez de «quieto», agrego un sabotaje que cancela el `close` y
  tiene que dar rojo, y corto pedidos en vuelo de verdad (recomendada:
  hoy el informe dice más de lo que midió). (2) Se acepta como está, con
  la conclusión retirada y la D37 abierta en riesgos.

**Lo que ya corrigo acá:** la frase «El corte del `close` es del
`TestClient` de las pruebas, no del servidor» de «CONEXIONES-1: medida»
queda retirada; vale lo de la D46. También el «no quedan conexiones tomadas» del resultado vale sólo con
los límites de arriba: es lo que vio el medidor (0 tomadas al final, 3544
cierres sin cancelar), no una prueba de que no haya fuga.

**Relación con la D39 y la D44:** la medición de la D39 (2), logins malos
de 60 a 100 a la vez con pedidos normales, ya la hizo en parte el
revisor de ABUSO-1: con 120, 24 a 35 respuestas 500 y `/health` en 33 s.
Está en la D44.

| Revisor | Modelo y esfuerzo | Hallazgos | Qué hice |
|---|---|---|---|
| conexiones1-sonnet | Sonnet alto | R1 media: «quieto» puede ser vacuo (D46 (a)). R2 media: la conclusión no se sostiene (D46 (b)); un `close` que entra por `__aexit__` dentro de un `shield` no se cuenta. R3 baja: los sabotajes no simulan un `close` cancelado. R4 baja: las versiones del venv no quedan registradas; sin Redis, Sentry ni proxy. R5 baja: quedan temporales `conexiones1_*` sin borrar | D46; lo demás, riesgos |
| `/code-review high` | Opus alto, en fork; sin `/security-review` porque sólo cambia scripts de prueba | (1) **alta**, leída: = Sonnet R1, falso verde. (2) media: la salida 1, reservada para una fuga, la usan también los errores del medidor. (3) media: ningún sabotaje cancela el `close` y la base exige `cancelados = 0`. (4) baja-media, sospecha: cierres contados dos veces. (5) `urllib` bloquea el loop. (6) la base no se borra si falla antes del `try`. (7) con `--n` de 140 o más se recicla el worker. (8) `pg_stat_activity` sin `backend_type`. (9) el 401 sin mirar el `detail`. (10) partir la URL pierde `?sslmode` | D46; lo demás, riesgos |

**Lo que es lectura y lo que corrió cada uno:** los 60 logins después de
«quieto» salen de una corrida del Sonnet; lo demás es lectura. Yo no
reproduje ninguno.

**Riesgos que quedan:** la D37 sigue abierta en el servidor real hasta
la D46; el medidor confunde sus errores con una fuga (salida 1); los
temporales que deja.

**Archivos de producto:** ninguno (sólo `scripts/testing/`).

```bash
git diff --stat 2b93071..30c0e97 -- . ':!docs'   # 3 files changed, 486 insertions(+)
PY=python scripts/testing/sabotajes/conexiones1.sh postgresql://<usuario>@127.0.0.1:<puerto>/postgres
#   tres «OK    |» y «FALLAS 0»
```

## Entregas preparadas para las 18:00 UTC (2026-10-28)

Recibí la D37 (2) en `20fb535`. En ABUSO-1 la pasé a riesgos, con lo que
pediste.

Recibí la D38 y la D39 en `669e120`: D38 (1), como está hecha, y la (3)
espera el conteo de Emi; D39 (1) por ahora, en riesgos de CONEXIONES-1, y
la medición chica no la empiezo sin el sí de Emi. Abierta: la D40, en ORG-1
(arriba). Mi próxima D es la D41.

Las doce piezas, en el orden de entrega, con su suite completa sobre el SHA
que se entrega. Desde la base limpia: cada corrida es un worktree nuevo en
ese SHA, con `test.db` vacía. Comprobé que la cadena es lineal: cada SHA
contiene al anterior, y los merges de tu rama que hay entre las piezas sólo
tocan `docs/`. A las 18:00 queda sólo la autorrevisión con subagentes,
`/code-review` y, donde corresponde, `/security-review`.

| # | Pieza | SHA que se entrega | Base para el diff | Suite sobre ese SHA | Sabotajes |
|---|---|---|---|---|---|
| 1 | ORG-1 + ORG-1b + DESPACHO-1a | `4ce6d22` | `fb11735` | 3670 passed, 336 skipped, 2 xfailed, 0 failed | org1, org1b y despacho1a en sus apartados |
| 2 | DESTINO-1 | `f887b4a` | `4ce6d22` | 3697 passed, 336 skipped, 2 xfailed, 0 failed | 15/15 |
| 3 | SUFIJOS-2 | `4ca6829`; entregada en `bd76f9f` con el arreglo | `4905cd8`; el arreglo, sobre `eacf591` | 3731 passed, 336 skipped, 2 xfailed, 0 failed; con el arreglo, 4005 passed sobre `4821fff` | 9/9; con el arreglo, 17/17 |
| 4 | SEGURO-1 | `371cde2`; entregada en `5dfaf47` con el arreglo | `1948207`; el arreglo, sobre `bd76f9f` | 3777 passed, 336 skipped, 2 xfailed, 0 failed; con el arreglo, 4007 passed sobre `5dfaf47` | 10/10; con el arreglo, 11/11 |
| 5 | DESPACHO-1b | `e59e1a8`, **entregada** | `49f8e29` | 3827 passed, 336 skipped, 2 xfailed, 0 failed | 24/24 |
| 6 | DATOS-1 | `c996ad4`, **entregada** | `d01f95c` | 3836 passed, 336 skipped, 2 xfailed, 0 failed | 12/12 |
| 7 | DISCO-1 | `88b22c8`, **entregada** | `cf84a76` | 3847 passed, 336 skipped, 2 xfailed, 0 failed | 20/20 |
| 8 | OBSERVABILIDAD-1 | `39be45e`, **entregada** | `88b22c8` | 3855 passed, 336 skipped, 2 xfailed, 0 failed | 16/16 |
| 9 | SESION-1 | `895ee73`, **entregada** | `f5160d7` | 3872 passed, 336 skipped, 2 xfailed, 0 failed | 19/19 |
| 10 | ABUSO-1 | `43916a7`, **entregada** | `c702655` | 3930 passed, 336 skipped, 2 xfailed, 0 failed | 27/27 |
| 11 | EMAIL-1 | `2b93071`, **entregada** | `e22a5cf` | 3954 passed, 336 skipped, 2 xfailed, 0 failed | email1 13/13; abuso1 27/27 sobre `2b93071` |
| 12 | CONEXIONES-1 | `30c0e97`, **entregada** | `2b93071` | no cambia producto ni pytest; la conclusión no se sostiene (D46) | 3 OK, `FALLAS 0` |

- **Base de ORG-1: `fb11735`, no `ea64a9c`.** `git diff ea64a9c..4ce6d22`
  arrastra EXCEL-3f de la Dev técnica (`main.py`, `test_excel3.py`,
  `excel3.sh`, `cliente1c.sh` y otros), que entró con tus merges. Contra
  `fb11735`, que es lo último de tu rama que tiene `4ce6d22`, quedan sólo
  mis 13 archivos. Los subrangos del apartado de ORG-1 (`ea64a9c..ddfc798`,
  `373ef55..5d42909` y `fe1571c..51890cd`) no traen nada de la Dev técnica.
- **SEGURO-1:** la suite del informe era de `a08de1f`. Entre ese SHA y
  `371cde2` sólo cambia `seguro1.sh`, pero igual la corrí sobre `371cde2`: «3777 passed, 336 skipped, 2 xfailed, 94 warnings in 498.52s», `compileall 0`.

```bash
git diff --stat fb11735..4ce6d22 -- . ':!docs'   # 13 files changed, 1736 insertions(+), 10 deletions(-)
git diff --name-only fb11735..4ce6d22 -- . ':!docs' | grep -ci 'excel\|cliente1c'   # 0
git diff --stat 43916a7 e22a5cf -- . ':!docs'    # vacío: entre ABUSO-1 y EMAIL-1 sólo hay docs
```

## CONEXIONES-1: medida, **sin entregar** (2026-10-28)

**Resultado: no quedan conexiones tomadas. No cambié el producto.** Con
gunicorn y uvicorn, como arranca el `Dockerfile`, el `close` de la sesión no
se canceló ni una vez en 3544 cierres. Con 720 respuestas 401, 104
normales y 60 pedidos cortados por el cliente, el pool volvió siempre a 0 tomadas, y en Postgres quedaron las 20
conexiones `idle`. El corte del `close` es del `TestClient` de las pruebas,
no del servidor. El aviso de las pruebas sigue en riesgos, como pediste.

Va en su propio `/entregar`, después del de EMAIL-1, con subagentes y
`/code-review high`. **No hace falta que la revises todavía.** SHA probado:
`30c0e97`, que suma sólo el medidor a EMAIL-1. Para ver sólo esta pieza:
`git diff 2b93071..30c0e97 -- . ':!docs'` (3 archivos, 486 inserciones,
todos en `scripts/testing/`).

### Decisiones

**D39 contestada en `669e120`: (1) por ahora.** Va a riesgos, abajo. La
(2) es pieza nueva que la PM le propone a Emi; no la empiezo sin su sí. Lo
que escribí:

**D39. Muchos logins fallidos a la vez llenan el pool** (está fuera de la
tarea: lo vi midiendo). Con 40 logins con clave mala a la vez, desde IP
distintas, un solo worker llegó a 50, 49 y 50 conexiones tomadas (tres
corridas). El techo es 50: `pool_size=20` más `max_overflow=30`
(`database/connection.py:68`). No hubo errores ni esperas que se vieran en
el log (`QueuePool limit`: 0), pero no medí cuánto espera un pedido normal
cuando el pool está lleno.

| Opción | Qué pasa | Costo |
|---|---|---|
| (1) Queda en riesgos | Nada cambia. | Si alguien junta muchas IP, puede hacer esperar a los demás hasta 30 s (`pool_timeout=30`, `connection.py:70`) o hacerles dar 500. |
| **(2) Pieza chica para medirlo** | Con el mismo medidor: logins malos con concurrencia de 60 a 100 y pedidos normales a la vez, midiendo cuánto tardan los normales y si alguno da 500. Si pasa, se propone el arreglo (por ejemplo, soltar la conexión antes del `bcrypt`). | Una pieza de medición, sin producto. |

**Recomiendo (2).** Es el mismo medidor con otro número y dice si hay un
problema real antes de tocar código.

### Qué medí y cómo

- **Servidor:** el comando del `CMD` del `Dockerfile`, leído del archivo.
  Sólo cambio el bind a `127.0.0.1` y agrego `-c` con la sonda. El comando
  que corrió:
  `proyecto_maria.main:app --bind 127.0.0.1:57805 --workers 1 --worker-class uvicorn.workers.UvicornWorker --timeout 120 --max-requests 1000 --max-requests-jitter 50 --access-logfile - --error-logfile - --log-level info -c …/conexiones1_sonda.py`.
  `railway.json` construye con ese `Dockerfile` y no cambia el comando.
  `ENVIRONMENT=production`, los servicios de afuera en modo simulado.
- **Base:** Postgres 16 descartable (puerto 55432). Cada corrida crea su
  base `conexiones1_<hex>` y la borra al final.
- **Sonda** (`scripts/testing/conexiones1_sonda.py`, es un archivo de
  configuración de gunicorn): en el worker lee el pool desde otro hilo
  (tomadas, libres, desborde) y cuenta los `AsyncSession.close()` y
  cuántos terminaron cancelados. No toca la app.
- **Fases**, con 40 pedidos a la vez: 120 sin token, 120 con token mal
  firmado, 120 de un usuario que no existe, 120 con token revocado, 120
  logins con clave mala, 80 normales, una mezcla de 144 y 60 pedidos que el
  cliente corta sin leer la respuesta. Las IP del login van al azar en
  `X-Forwarded-For`: sin un proxy delante, la app toma la última, y así el
  tope por IP de ABUSO-1 no corta la fase.
- **Espera:** después de cada fase espera a que se vea todo quieto: 0
  tomadas en el pool, todas las conexiones `idle` en `pg_stat_activity` y
  la misma cantidad en Postgres que libres en el pool. Pregunta cada 0,1 s,
  con un plazo de 60 s. No hay esperas fijas.
- **Busca en el log del servidor:** `non-checked-in connection`,
  `Task was destroyed but it is pending`, `QueuePool limit`,
  `CancelledError`, `Event loop is closed`, `Exception in ASGI application`,
  `Error logging metrics` y `Traceback`.

### Números, sobre `30c0e97`

| Fase | Respuestas | Máx. tomadas | Quieto en | Al final |
|---|---|---|---|---|
| sin token | 120 × 401 | 20 | 0,0 s | tomadas=0 libres=20 desborde=0 / `{'idle': 20}` |
| token mal firmado | 120 × 401 | 10 | 0,0 s | igual |
| usuario inexistente | 120 × 401 | 22 | 0,0 s | igual |
| token revocado | 120 × 401 | 20 | 0,0 s | igual |
| login con clave mala | 120 × 401 | **50** | 0,0 s | igual |
| normal | 80 × 200 | 40 | 0,0 s | igual |
| mezcla | 24 de cada uno (120 × 401, 24 × 200) | 44 | 0,0 s | igual |
| cortes del cliente | 60 cortados | 0 | 0,39 s | igual |

- `cierres de sesión: 3544, cancelados: 0`.
- `filas en api_logs: 885`, y 825 respuestas en el log de acceso fuera de
  `/health`. La diferencia son los 60 cortes: llegaron a la app, que los
  anotó aunque el cliente no leyó la respuesta.
- Las ocho señales del log: 0. Salida `sin conexiones tomadas`, código 0.
- Hice otras dos corridas sobre `c2be841`, con el mismo producto: también
  sin conexiones tomadas y con 0 cancelados. En la segunda los máximos
  fueron 20, 9, 25, 18, 49, 42, 44 y 0.

### Por qué no se fuga, aunque se cancelara

`get_async_session` (`database/connection.py:99`) abre la sesión con
`async with AsyncSessionLocal() as session:`. En SQLAlchemy 2.0.25, la
versión fijada en `requirements.txt`, la salida de ese `async with` cierra la
sesión en una tarea aparte protegida de la cancelación
(`AsyncSession.__aexit__`: `asyncio.create_task(self.close())` y
`asyncio.shield`). Si se cancelara el `await session.close()` del `finally`,
el `async with` la volvería a cerrar igual. Esto lo leí en el código: en el
servidor no hubo cancelaciones, así que no se puso a prueba.

En las pruebas, el loop del `TestClient` puede terminar antes que ese
cierre, y ahí sale `Event loop is closed`. En producción el loop vive
mientras vive el worker.

### Sabotajes: el medidor ve una fuga cuando la hay

`scripts/testing/sabotajes/conexiones1.sh` sobre `30c0e97`, en un worktree:

| Corrida | Lo que tiene que dar | Resultado |
|---|---|---|
| sin sabotaje | código 0, «sin conexiones tomadas», «cancelados: 0» | OK |
| la sesión no se cierra y queda viva | código 1, «QUEDAN CONEXIONES TOMADAS», la fase en «NO» | OK |
| la sesión no se cierra y se suelta | código 1, «QUEDAN CONEXIONES TOMADAS» | OK |

`FALLAS 0`. En la primera versión, el medidor salía con «LA MEDICIÓN NO
VALE» cuando había fuga: el pool lleno daba 500, y eso tapaba la fuga.
Ahora la fuga y una medición inválida son dos salidas distintas (1 y 2) y
corta en la primera fase con fuga.

### Puertas

| Puerta | Resultado |
|---|---|
| `conexiones1_medir.py` sobre `30c0e97` | `sin conexiones tomadas`, código 0 (tabla de arriba) |
| `sabotajes/conexiones1.sh` sobre `30c0e97` | 3 OK, `FALLAS 0` |
| Suite completa | No la corrí para esta pieza: no cambia el producto ni las pruebas de pytest. La de `2b93071` (EMAIL-1) está en su apartado. |
| Prueba con rojo antes y verde después | No corresponde: no hay arreglo. |
| `/code-review high` y subagentes | **No corridos:** no hay cupo hasta las 18:00 UTC. Van en el `/entregar`. |

```bash
git diff --stat 2b93071..30c0e97 -- . ':!docs'   # 3 files changed, 486 insertions(+)
<venv>/bin/python scripts/testing/conexiones1_medir.py postgresql://<usuario>@127.0.0.1:<puerto>/postgres
#   «cierres de sesión: N, cancelados: 0» y la última línea «sin conexiones tomadas»
PY=<venv>/bin/python scripts/testing/sabotajes/conexiones1.sh postgresql://<usuario>@127.0.0.1:<puerto>/postgres
#   tres «OK    |» y «FALLAS 0»
```

### Riesgos

- **La medición vale para estas versiones:** gunicorn 26.2.0, uvicorn
  0.54.0 (con uvloop 0.23.0 y httptools 0.9.0, como `uvicorn[standard]`),
  starlette 1.10.0 y fastapi 0.162.0. En `requirements.txt` esas van con
  `>=`, así que Railway toma la última al construir. SQLAlchemy 2.0.25 y
  asyncpg 0.29.0 están fijadas.
- **El aviso de las pruebas sigue:** `Event loop is closed` en
  `_connection_worker_thread`, más o menos 1 de cada 3 corridas parciales
  (D37). La medición dice que no es de producción.
- **Sentry:** nadie llama a `init_sentry` al arrancar (sólo aparece en un
  ejemplo dentro de un texto, `sentry_integration.py:219`), así que no
  envuelve la app ni en la medición ni en producción. Si alguien lo activa,
  agrega una capa que no medí.
- **Los cortes no se ven en el máximo de tomadas:** terminan antes de que
  la sonda pregunte (cada 0,05 s). Sí se ve que el pool queda en 0 después.
- **Un solo worker y una sola réplica**, como hoy. Con más workers cada uno
  tiene su propio pool de 50, y Postgres tiene que aceptar la suma.
- **El pool llega al techo con logins fallidos a la vez** (D39 (1)): con
  40 logins con clave mala a la vez desde IP distintas, 50, 49 y 50
  tomadas de 50 en tres corridas. No medí cuánto espera un pedido normal
  con el pool lleno: puede esperar hasta 30 s (`pool_timeout=30`) o dar
  500. Medirlo es la pieza que la PM le propone a Emi.

Archivos de producto que toqué: ninguno.

## EMAIL-1: hecha, **sin entregar** (2026-10-28)

**Estado.** Hecha encima de `e1b3129`, en mi rama después de ABUSO-1 y del
merge `e22a5cf`. Va en su propio `/entregar`, después del de ABUSO-1, con
subagentes, `/code-review high` y `/security-review` (autenticación: revisión
fuerte). SHA probado: `2b93071`. Para ver sólo esta pieza:
`git diff e22a5cf..2b93071 -- . ':!docs'` (6 archivos, 832 inserciones y 25 borrados).

### Decisiones

**D38 contestada en `669e120`: (1)**, como está hecha. La (3) espera el
conteo de Emi en producción: si da cero, el índice entra como paso nuevo
sin tocar datos; si no, decide Emi. Lo que escribí:

**D38. Qué hacer cuando un pedido encuentra dos cuentas** cuyo email
difiere sólo en mayúsculas (cuentas de antes; desde EMAIL-1 no se pueden
crear nuevas).

| Opción | Qué pasa | Costo |
|---|---|---|
| **(1) Gana la exacta; sin exacta, ninguna** (lo que está hecho) | Si alguna de las dos coincide exacto con lo escrito, es esa. Si ninguna coincide exacto, no sale correo ni token, el login da 401 y la respuesta es la misma que la de un email que no existe. Queda un aviso en el log, sin el email. | Esa persona tiene que escribir el email exacto o su usuario. |
| (2) Recuperar le escribe a cada cuenta | Sin exacta, recuperar manda a cada cuenta lo suyo a su propia dirección guardada. El login sigue como en (1). | Más correo y más código. Si el proveedor distingue mayúsculas, la otra persona recibe un correo que no pidió, aunque sólo con su propia cuenta. |
| (3) Unificar los pares e índice único en `lower(email)` | Cuando Emi cuente los pares en producción: se renombra o se fusiona cada par y se agrega el índice. | Migración de datos. Necesita el conteo y una decisión por par. |

**Recomiendo (1) ahora y (3) después del conteo.** Si el conteo da 0, el
índice entra sin tocar datos. (1) no le da a nadie la cuenta de otro y es
reversible. (2) sólo vale la pena si el conteo da pares y alguien no puede
recuperar.

### SHAs

| SHA | Qué |
|---|---|
| `56ab458` | producto y CHANGELOG (`fix:`) |
| `855e8ac` | pruebas: `tests/test_email1.py`, `email1_motores.py`, `sabotajes/email1.sh` |
| `c2be841` | pruebas: invitación con un miembro de email viejo en mayúsculas, y el sabotaje del registro saca las dos normalizaciones |
| `2b93071` | pruebas: el caso de recuperar usuario de ABUSO-1 sigue a EMAIL-1 (abajo) |

### Qué cambia

- **`_cuenta_por_email`** (`main.py:1509`) primero busca exacto y después sin
  mirar mayúsculas ni espacios. Con más de una cuenta posible y ninguna
  exacta, no elige ninguna (D38 (1)).
- **Recuperar contraseña** (`:1552`) y **recuperar usuario** (`:1613`) usan
  ese helper. El correo sale a la dirección guardada, no a la escrita. La
  respuesta no cambia exista o no.
- **Login:** si lo escrito tiene `@` y no coincide exacto con ningún usuario
  ni email, usa el mismo helper (`:2800`).
- **Perfil** (`:2015` y `:2049`): el duplicado se busca sin mirar
  mayúsculas. Un email igual al propio salvo mayúsculas no es un cambio: no
  pide contraseña y no reescribe nada.
- **Registro de prueba con reemplazo** (`REGISTER_TEST_EMAIL_REPLACE`,
  `:2997`): archiva todas las cuentas de ese email. Antes archivaba una sola
  y la otra hacía fallar el alta con 500.
- **Ya miraban sin mayúsculas, y ahora tienen prueba:** registro (`:2996`),
  alta de estudio (`:9883`), invitación (`:10052`) y registro con invitación
  (`:3084`). En todos lados la comparación es `lower(email)`, de un lado y
  del otro.

Inventario (`grep` de `User.email`, `.email ==` y `Invitation.email` en
`proyecto_maria/`): no queda ninguna comparación exacta de email de cuenta
fuera del helper y del bootstrap de admin (riesgos). `client_service.py:140`
y `main.py:6948` son emails de clientes, no de cuentas.

### Puertas, sobre `2b93071`

| Puerta | Resultado |
|---|---|
| `tests/test_email1.py` (24 casos, SQLite) | `24 passed` |
| Rojo antes: la misma prueba sobre `e22a5cf` | `12 failed, 12 passed`: recuperar usuario ×3, recuperar contraseña ×3, login, la respuesta no cambia ×2, el par guarda el perfil, el perfil no toma `Gabi@`, registro de prueba con reemplazo. Las 12 que pasan son reglas que ya se cumplían y quedan de guarda. |
| `email1_motores.py sqlite` (servidor uvicorn real) | `sqlite: todo OK` (21 OK) |
| `email1_motores.py pg` (Postgres 16, puerto 55432) | `pg: todo OK` (21 OK) |
| Rojo antes en los dos motores (sin el arreglo) | `sqlite: FALLAS: 11` y `pg: FALLAS: 11`, las mismas fallas en los dos |
| `sabotajes/email1.sh 2b93071` | 13 «ROJO  |», `sabotajes sin rojo: 0` |
| `sabotajes/abuso1.sh 2b93071` (cambió un caso suyo) | 27 «ROJO  |», `sabotajes sin rojo: 0` |
| Suite completa sobre `c2be841`, worktree nuevo | `1 failed, 3953 passed, 336 skipped, 2 xfailed`; `compileall 0`. El rojo, abajo. |
| Suite completa sobre `2b93071`, worktree nuevo | `3954 passed, 336 skipped, 2 xfailed, 96 warnings in 570.20s`; `compileall 0` (`$S/suite_email1b.log`) |
| `/code-review high`, `/security-review` y subagentes | **No corridos:** no hay cupo hasta las 18:00 UTC. Van en el `/entregar`. |
| smoke y `ataque_aislamiento.sh` | **No corridos**. Van en el `/entregar`. |

**El rojo de la suite sobre `c2be841`** fue
`tests/test_abuso1.py::test_s6_recuperar_usuario_corta_en_silencio_por_email`:
`assert ['ab1t_0aee25...ejemplo.test'] == ['ab1t_0aee2526@ejemplo.test']`,
`Left contains 2 more items`. El caso de ABUSO-1 pedía recuperar con el
email en mayúsculas, con la primera letra en mayúscula y exacto, y esperaba
un solo correo: antes de EMAIL-1 sólo el exacto encontraba la cuenta. Ahora
los tres la encuentran y los tres correos van a la dirección guardada, que
es lo que pide EMAIL-1. El caso ahora espera tres correos en la hora y
ninguno en el cuarto pedido; lo que vigila (el tope cuenta el email sin
mirar mayúsculas) no cambió. Si el tope distinguiera mayúsculas, el cuarto
pedido sería el segundo de su clave y saldría un cuarto correo. Va en
`2b93071`. No lo vi antes porque corrí `test_email1.py` y no la suite.

En la primera vuelta de sabotajes, tres no dieron el rojo esperado. Los
diagnostiqué:
- *No gana el exacto* dio rojo, pero en `test_par_el_exacto_gana` y no en
  `test_par_login`. Eso es correcto: el login ya busca exacto antes del
  helper. Corregí el texto esperado.
- *La invitación busca tal cual* dio verde porque el alta de estudio ya
  guarda en minúsculas, así que la comparación exacta también coincidía. La
  prueba ahora usa un miembro con el email viejo en mayúsculas, puesto por
  SQL.
- *El registro no pasa a minúsculas* dio verde porque el registro normaliza
  dos veces (`:2983` y `:2995`): sacar una sola no es un defecto. El
  sabotaje ahora saca las dos.

```bash
git diff --stat e22a5cf..2b93071 -- . ':!docs'           # 6 files changed, 832 insertions(+), 25 deletions(-)
PY=<venv>/bin/python scripts/testing/sabotajes/email1.sh 2b93071   # 13 «ROJO  |», «sabotajes sin rojo: 0»
PY=<venv>/bin/python scripts/testing/sabotajes/abuso1.sh 2b93071   # 27 «ROJO  |» y «sabotajes sin rojo: 0»
<venv>/bin/python scripts/testing/email1_motores.py sqlite        # «sqlite: todo OK»
<venv>/bin/python scripts/testing/email1_motores.py pg postgresql://<usuario>@127.0.0.1:<puerto>/postgres   # «pg: todo OK»
```

### Supuestos reversibles

- **Login por email sin mayúsculas.** La tarea dice «todo lugar que busque»
  un email, y el login lo busca. Son dos líneas; si no lo querés, se sacan.
- **No se pueden cambiar sólo las mayúsculas del propio email.** El perfil
  lo toma como «sin cambio». Así no reescribe el email de una cuenta vieja
  cada vez que se guarda la pantalla, que siempre lo manda en minúsculas.
- **Registro de prueba con reemplazo:** archiva todas las cuentas del email.
  Sólo corre con `REGISTER_TEST_EMAIL_REPLACE` y una lista de emails de
  prueba.

### Riesgos

- **Sin índice único** (por la tarea, hasta el conteo de Emi). Dos altas a
  la vez con el mismo email y distintas mayúsculas pueden pasar las dos el
  chequeo. Con las mismas mayúsculas lo frena el `unique` de hoy. Se cierra
  con la D38 (3).
- **El bootstrap de `ADMIN_USERNAMES`** (`main.py:1478`) compara exacto. Si
  la variable trae un email con otras mayúsculas, no da admin. Lo dejo así a
  propósito: sin mirar mayúsculas, con un par le daría admin a la otra
  cuenta.
- **SQLite y Postgres no bajan igual lo que no es ASCII.** El `lower()` de
  SQLite sólo baja ASCII; el de Postgres baja también acentos. Los emails
  nuevos pasan una regex ASCII. Uno viejo con letras no ASCII podría
  compararse distinto en un motor y en el otro. No lo probé.
- **Pedir el reset sólo tiene tope por IP**, y es de antes. Con EMAIL-1 las
  variantes de mayúsculas encuentran la cuenta, pero el email exacto ya se
  podía pedir desde muchas IP: no abre un camino nuevo. Recuperar usuario
  cuenta por email en minúsculas, así que las variantes suman al mismo tope.
- **Quien tenga un par sin exacta** no recupera ni entra escribiendo el
  email con otras mayúsculas, hasta la D38 (3). Es el costo de la D38 (1).
- **Cierra lo de la D36:** los dos lugares que comparaban exacto y el PUT
  que dejaba crear pares (riesgos de ABUSO-1).

Archivos de producto que toqué: `proyecto_maria/main.py` y `CHANGELOG.md`.

## ABUSO-1: hecha, **sin entregar** (2026-10-28)

**Estado.** La D35 está hecha entera, como la contestaste en `f600ed4`, con
S5 adentro. Va en su propio `/entregar`, después del de SESION-1, con
subagentes, `/code-review high` y `/security-review` cuando vuelva el cupo.
**No hace falta que la revises todavía.** SHA probado: `43916a7`. Para ver
sólo esta pieza: `git diff c702655..43916a7 -- . ':!docs'`.

### Decisiones

Nada para decidir. **D36** la contestaste en `eaee1b1` y **D37** en `20fb535`: las dos (2) por ahora; están en riesgos. Mi próxima D es la D38.

### SHAs

| SHA | Qué |
|---|---|
| `584b8d1` | S5: tope de 16 KB en `/api/ui/event` y `/api/session/state` (lee por partes y corta, haya o no `Content-Length`; lo que se pasa da 413 y no se guarda); deja de escribirse `logs/ui_events.jsonl` |
| `25158c6`, `8c37653` | S5: pruebas y sabotajes; `HANDOFF.md:57` y `CHANGELOG.md` |
| `ca7eee9` | D35a: un solo helper de IP (`core/rate_limit.py`) para slowapi y los contadores: la última de `X-Forwarded-For`, descontando `TRUSTED_PROXY_HOPS` (1 por defecto); el 429 del login deja en el log la IP y cuántas entradas traía |
| `790dd8e` | D35e: tabla `limites_auth` (`clave`, `cuenta`, `bloqueado_hasta`, `vence`), sola en su commit |
| `a3abd92` | D35b, d y e: login y reset pasan a la tabla; límites de registro, recuperar usuario y eventos; sin sesión, sólo las tres acciones de la landing; `_migrate_limites_auth` borra las vencidas al arrancar |
| `a2fc7f0` | pruebas de todo lo anterior |
| `777ebc8` | arreglo: recuperar contraseña con pedidos simultáneos (hallazgo 1) |
| `74ccb76` | pruebas de pedidos simultáneos, arnés en los dos motores y un sabotaje por regla |
| `44b43db` | arreglo: una IP de más de 120 caracteres (hallazgo 2) |
| `43916a7` | pruebas y sabotajes de la IP larga |

Archivos de producto: `proyecto_maria/core/limites_auth.py` (nuevo),
`core/rate_limit.py`, `database/models.py`, `main.py`, `HANDOFF.md`,
`CHANGELOG.md`.

### Qué quedó, regla por regla

| Ruta | Límite | Dónde vive |
|---|---|---|
| `/auth/login` | 5 fallos por IP → 15 min; vencido el bloqueo, un fallo más vuelve a bloquear; la cuenta se olvida a las 24 h sin fallos; el login correcto la borra | tabla |
| `/auth/login` | 5 por minuto (slowapi) | memoria, sin cambios |
| `/auth/request-password-reset` | el 5.º pedido por IP → 15 min | tabla |
| `/auth/register` | 5 por hora y 20 por día por IP | tabla |
| `/auth/recover-username` | 5 cada 15 min por IP (429) y 3 por hora por email (en silencio: misma respuesta, no busca ni manda) | tabla |
| `/api/ui/event`, `/api/session/state` | 120 por minuto por IP, cada una; 16 KB por evento; sin sesión, sólo `pricing_cta_clicked`, `hero_cta_clicked` y `register_pending_verify` | memoria (slowapi) |

**Tabla.** Cada escritura es un único `INSERT … ON CONFLICT DO UPDATE …
RETURNING` en su propia transacción: dos pedidos simultáneos no leen la
misma cuenta. Antes de escribir se borran las vencidas, y al arrancar
también (`_migrate_limites_auth`, con el patrón de las otras `_migrate_*`).
Un solo camino, haya o no Redis. `--max-requests` no se tocó.

**Por qué alcanzan los números.**

- **Registro, 5 por hora.** Los tres invitados de ORG-1 desde una oficina
  son 3. Una demo con más de 5 altas desde la misma red en una hora choca:
  es la opción 2 de la D35b, que no elegiste.
- **Recuperar usuario, 5 cada 15 min.** Quien se olvidó el usuario prueba
  uno o dos emails. El de 3 por hora por email frena que alguien le llene la
  casilla a otro.
- **Eventos, 120 por minuto.** El front manda un evento por clic: los 14
  `track(…)` de `static/v2/app_v2.js` y el de `landing.html:561`; ninguno
  por temporizador, scroll ni tecla. 120 son dos clics por segundo durante
  un minuto. Detrás de un NAT con mucha gente, el tope se comparte (riesgos).

**S6 queda mitigada, no cerrada.** Los mensajes del registro siguen
distinguiendo «Usuario ya existe» y «Email ya registrado» (D35c): con 20
por día por IP, enumerar sigue siendo posible, sólo que lento.

### Hallazgos nuevos, cada uno con su rojo antes del arreglo

**1. Recuperar contraseña dejaba pasar pedidos simultáneos.** El código
chequeaba el bloqueo y después sumaba: 20 pedidos a la vez pasaban todos.
Rojo sobre `74ccb76` con el producto de `a3abd92`, en los dos motores:

```
INFO  | concurrencia: 20 recuperar contraseña simultáneos → [200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200], cuenta 20
FALLA | concurrencia: 20 recuperar contraseña simultáneos pasan 5
pg: FALLAS: 1                    (sqlite: FALLAS: 1, la misma)
```

Con `777ebc8` se suma antes de seguir, y el que ve una cuenta mayor que el
tope también se corta: `[200, 200, 200, 200, 200, 429 × 15]`.

**2. Una IP de más de 120 caracteres daba 500 en Postgres.** La IP sale de
`X-Forwarded-For` y la columna `clave` es de 120. Rojo sobre `43916a7` con
el producto de `74ccb76`, en PG16 (`$S/motores_pg_larga_rojo.log`):

```
login, reset, recuperar, registro → [500, 500, 500, 500]; 5 logins más → [500, 500, 500, 500, 429]
FALLA | una IP larga no rompe las rutas con contador
FALLA | una IP larga también se bloquea al quinto fallo
pg: FALLAS: 2
```

En SQLite no da 500: SQLite no respeta el largo de la columna. Ahí el rojo
lo dan los sabotajes: guardar la clave cortada sin hash hace que dos IPs
largas con el mismo comienzo se pisen. Con `44b43db`, una clave de más de
120 se guarda como sus primeros 50 caracteres, «:» y su sha256 (115 en
total).

### Puertas, sobre `43916a7`

| Qué | Salida |
|---|---|
| `tests/test_abuso1.py` sobre la base, con las pruebas nuevas (rojo antes, `$S/rojo_d35.log`) | `25 failed, 19 passed, 3 warnings in 11.65s` |
| `tests/test_abuso1.py` | `58 passed, 3 warnings in 26.99s` |
| `abuso1.sh 43916a7` | 27 `ROJO`, ninguno `ROJO?`; `sabotajes sin rojo: 0`, `salida 0` |
| `abuso1_motores.py sqlite` | `sqlite: todo OK` |
| `abuso1_motores.py pg` (PG16, 55432) | `pg: todo OK` |
| `sesion1_motores.py sqlite` y `pg` | `sqlite: todo OK`, `pg: todo OK` |
| suite completa (`$S/suite_43916a7.log`) | `3930 passed, 336 skipped, 2 xfailed, 94 warnings in 543.33s (0:09:03)`. Entre las advertencias, las 32 `SAWarning` de conexiones aiosqlite que ya estaban en la base; la advertencia de hilo de la D37 no salió en esta corrida (0) |

No corrí todavía: `smoke_friccion.sh`, `ataque_aislamiento.sh`, subagentes,
`/code-review` ni `/security-review`. Van en el `/entregar`.

### Riesgos y fuera de alcance

- **El límite de 5 por minuto del login sigue en memoria** (slowapi), como
  pediste: el reciclado del worker lo borra. El bloqueo de 5 fallos sí está
  en la tabla.
- **Login: chequea y después suma.** Con pedidos paralelos pasan algunos
  fallos de más antes del bloqueo; cada uno queda contado y el siguiente
  pedido ve el bloqueo. En reset sí lo arreglé, porque ahí el tope es el
  pedido mismo.
- **`logging_middleware` sigue tomando la primera IP** de
  `X-Forwarded-For` para el log de acceso. No decide nada; sólo el log.
- **Si Railway no manda `X-Forwarded-For`** (corrección a lo que dije en la
  D35a): sin el encabezado se usa `client.host`, el proxy, y todos comparten
  el contador. Pero si el cliente manda su propio `X-Forwarded-For` y
  Railway no lo toca, la última entrada la escribe el cliente y la IP se
  falsifica. El log del 429 del login (IP y cantidad de entradas) es lo que
  lo muestra después del deploy.
- **La tabla crece con IPs inventadas** si el cliente controla la última
  entrada (el caso anterior): una fila por IP, que se borra al vencer.
- **Menos entradas que saltos:** con `TRUSTED_PROXY_HOPS` mayor que las
  entradas, se toma la primera (`partes[0]`), que la escribe el cliente.
- **Los límites de registro, recuperar usuario y eventos se apagan con
  `limiter.enabled`**; login y reset se aplican siempre.
- **120 por minuto compartido detrás de un NAT.** Una oficina grande en una
  IP comparte el tope de eventos; lo que se pasa da 429 y no se guarda.
- **Recuperar por email no cuenta si la IP ya se pasó:** el 429 por IP
  corta antes.
- **Los registros rechazados cuentan** para el tope por hora y por día.
- **El olvido de los fallos del login es de 24 h deslizantes:** cada fallo
  lo corre 24 h.
- **Un token revocado sigue firmando eventos** hasta que vence
  (`_jwt_sub_from_token_text` no mira la revocación). Sólo telemetría; es de
  antes.
- **Emails que difieren sólo en mayúsculas** (D36, (2) por ahora). Dos
  cuentas pueden tener el mismo email cambiando sólo mayúsculas
  (`users.email` es `unique` y en Postgres distingue mayúsculas). Comparan
  exacto `/auth/request-password-reset` (`main.py:1529`) y
  `/auth/recover-username` (`:1591`): quien escribe su email con otras
  mayúsculas no recupera nada. El PUT del perfil (`:2027`) busca el
  duplicado con `User.email == raw_email` (ya en minúsculas) y deja crear
  pares. El contador de 3 por hora por email sí va en minúsculas.
- **Un `close` de sesión cancelado al terminar el pedido** (D37, (2) por
  ahora; es de antes de ABUSO-1). El `await session.close()` del `finally`
  de `get_async_session` (`database/connection.py:107`) se cancela después
  de mandar la respuesta. Lo rastreé con un plugin que registra cada
  operación de aiosqlite cancelada (`$S/plug/rastro_aiosqlite.py`).
  - **Ya pasaba en la base `895ee73`:** con static, auth_login y sesion1
    (34 passed), se cancela en 2 de 2 corridas («=== CANCELADA close en
    tests/test_auth_login.py::test_login_email_inexistente»,
    `$S/rastrobase_1.log` y `_2.log`). Ahí la advertencia no apareció en
    ninguna de 4 corridas (`$S/warnbase_*.log`).
  - **Con ABUSO-1** aparece la advertencia
    `PytestUnhandledThreadExceptionWarning … (_connection_worker_thread) …
    RuntimeError: Event loop is closed`. Sale más o menos en 1 de cada 3
    corridas (`$S/warn_*.log`), en pruebas distintas cada vez, porque
    ABUSO-1 abre más conexiones en el camino del 401 y del 429. En la
    suite completa sobre `43916a7` no salió. La advertencia queda a la
    vista: sin `filterwarnings` y sin repetir corridas.
  - **Quién cancela no está confirmado.** La hipótesis son los
    `BaseHTTPMiddleware` (`main.py:1664` y `:1782`); no la probé y no los
    toqué.
  - **No medimos si en producción deja conexiones de Postgres colgadas.**
    Medirlo con uvicorn, Postgres 16 y `pg_stat_activity` es una pieza
    nueva, que le proponés a Emi.
- **Fila 14 de Argon y X1:** fuera de alcance, no los toqué.

### Supuestos reversibles

- El 413 corta a los 16 KB por evento, aunque `props` ya se recortaba a 8000.
- La clave de una IP larga es su comienzo y su sha256 (hallazgo 2).
- La clave del contador por email es el sha256 del email, no el email, para
  no guardar emails en la tabla.

### Comandos

```bash
git fetch origin claude/dev-maria && git checkout --detach 43916a7
# venv con requirements; Postgres descartable en 55432
PY=python bash scripts/testing/sabotajes/abuso1.sh 43916a7   # «sabotajes sin rojo: 0»
python scripts/testing/abuso1_motores.py sqlite              # «sqlite: todo OK»
python scripts/testing/abuso1_motores.py pg postgresql://cdi@127.0.0.1:55432/postgres   # «pg: todo OK»
```

## SESION-1: hecha, **sin entregar** (2026-10-28)

Encima de OBSERVABILIDAD-1 y de tu `486e655` (merge `f5160d7`): producto y
`CHANGELOG.md` `7dfe144`; casos, arnés de dos motores, pantalla y sabotajes
`014a3e4`; arreglo de producto `4c1ae09` y sabotajes ajustados `895ee73`.
**SHA probado: `895ee73`.** Para ver sólo esta pieza:
`git diff f5160d7..895ee73`. Va en su propio `/entregar`, después del de
OBSERVABILIDAD-1, con subagentes, `/code-review high` y `/security-review`
cuando vuelva el cupo. **No hace falta que la revises todavía.**

Nada para decidir. Supuestos abajo.

### Premisa: confirmada, en SQLite y en Postgres 16 (55432)

Servidor real sobre `39be45e`, usuario inventado (`$S/ses/premisa.py`,
fuera del repo). Mismo resultado en los dos motores:

```
[base] dos logins: T1 401 (revocada por el segundo), T2 200
[A cambiar clave con T2] 200; active_jti=None; T1 200, T2 200
[login nuevo T3] T1 401, T2 401, T3 200
[B resetear clave] pedir 200, reset 200; active_jti=None; T1 200, T2 200, T3 200
[C cerrar sesión T4] /auth/logout 200, /logout 200; T4 después 200
[D cambiar email sin contraseña con T4] 200; email en la base=atacante@example.com
```

Es peor de lo que dice S3: cambiar o resetear la clave ponía `active_jti`
en NULL, y NULL quiere decir «aceptar cualquier token» (usuarios de antes
de la columna). **Revocar resucitaba las sesiones ya revocadas** (T1 volvió
a entrar). Cerrar sesión sólo borraba la cookie: el token seguía entrando.
Y cualquiera con una sesión abierta cambiaba el email sin la clave, y con
eso, el reset.

### Qué cambió

Se usa el único mecanismo que había: `users.active_jti` y el chequeo de
`get_current_user`.

- `auth/dependencies.py`: `revocar_sesiones(user, conservar_jti=None)`
  nunca escribe NULL; para revocarlas todas guarda un jti nuevo que ningún
  token tiene. `revocar_sesion_de_la_request` toma el token de la cookie o
  del Bearer, como `get_current_user`, y lo revoca **sólo si es el
  vigente**: un token vencido, inválido o ya revocado no toca nada (si no,
  quien tenga uno viejo podría sacar a la sesión buena).
  `get_current_user` deja el jti en `request.state.token_jti`.
- `main.py`:
  - `POST /api/user/change-password`: cierra las otras y conserva la de
    quien la cambió. Con la clave actual mal no toca nada.
  - `POST /auth/reset-password`: cierra todas.
  - `POST /auth/logout` y `POST /logout`: revocan ese token y borran la
    cookie; sin token o con basura, 200 como antes.
  - `PUT /api/user/profile`: si el email cambia (sin distinguir mayúsculas
    ni espacios; vaciarlo también es cambiarlo), pide `current_password`.
    Sin ella: 400 «Para cambiar el email ingresá tu contraseña actual»;
    equivocada: 400 «La contraseña actual es incorrecta». En los dos casos
    no cambia nada, tampoco el nombre. El formato se valida antes de pedir
    la clave.
- Pantalla de perfil v2 (`profile.js`, `dashboard_v2.html`): el campo
  «Contraseña actual» aparece sólo si el email cambió; sin clave avisa y no
  manda nada; al guardar bien se vacía y se oculta.

### Rojo antes del producto (`39be45e`)

- `tests/test_sesion1.py`: `11 failed, 6 passed`.
- `sesion1_motores.py`: `FALLAS: 12` en SQLite y `FALLAS: 12` en Postgres;
  fallan cerrar la otra al cambiar la clave, `active_jti` no NULL (×2), el
  reset cierra la vigente y no resucita, los cuatro logouts (Bearer y
  cookie en las dos rutas) y el email sin clave, con clave mal y vaciándolo.
- `pantalla_sesion1.js`: `FALLA: cambiar el email no muestra el campo de
  la clave`.

### Puertas sobre `895ee73`

| Puerta | Resultado |
|---|---|
| suite completa (`pytest -q --no-cov --timeout=120`) | `3872 passed, 336 skipped, 2 xfailed`, 0 failed, `pytest salida 0` |
| `compileall` | `compileall 0` |
| `sesion1_motores.py sqlite` | 26 `OK`, `sqlite: todo OK`, salida 0 |
| `sesion1_motores.py pg postgresql://cdi@127.0.0.1:55432/postgres` | 26 `OK`, `pg: todo OK`, salida 0 |
| `sabotajes/sesion1.sh` (14 de backend, 5 de pantalla) | 19 `ROJO`, `sabotajes sin rojo: 0`, salida 0 (la base verde de pantalla incluida) |
| `smoke_friccion.sh` | `smoke salida 0` |
| `ataque_aislamiento.sh` | 22 `OK`, `ataque salida 0` |
| pantalla sola (verde, sobre `014a3e4`) | 3 de 3 `OK: el perfil pide la contraseña sólo al cambiar el email y no saca a nadie al login` |

**Rojo de la suite sobre `014a3e4`, mío y arreglado:** `1 failed, 3871
passed, 336 skipped, 2 xfailed`. Falló
`test_auth_invalid_plan.py::test_get_current_user_with_invalid_plan_falls_back_to_premium`
con `AttributeError: 'MockRequest' object has no attribute 'state'`: yo
había hecho que `get_current_user` escribiera el jti en `request.state`, y
ese test le pasa un request falso sin `state`. Ningún código de producto
llama así, pero era un efecto lateral escondido entre la dependencia y la
ruta. En `4c1ae09` lo saqué: `change-password` lee el jti del token con
`jti_de_la_request` (cookie o Bearer, como `get_current_user`). El test
viejo no lo toqué. Sobre `895ee73`: ese test y los de la pieza `32
passed`; motores 26 `OK` en los dos; smoke y ataque salida 0 (22 `OK`).

Un sabotaje que **no** sirve, y por qué: quitar sólo el chequeo de «sin
clave» no rompe la regla, porque `verify_password` igual rechaza `None` (da
400 «incorrecta»). El sabotaje que quedó es el defecto real: verificar sólo
si viene una clave.

No corrí: subagentes, `/code-review` ni `/security-review` (sin cupo hasta
las 18:00 UTC). Una primera corrida de navegador, antes de esta versión del
script, no mandó el PUT; no encontré la causa y no se repitió en las
siguientes.

### Riesgos (fuera de alcance; ninguno lo empeora esta pieza)

- `REPRODUCCION-ARGON` fila 10: `verify-email` se puede reusar y abre una
  sesión.
- Fila 13.2: el reset con una cookie vieja da 403 (CSRF).
- Fila 14: `/auth/me` no mira el jti (un token revocado sigue viendo sus
  datos ahí); los tokens de reset no se anulan entre sí; el contador de
  intentos de login.
- La telemetría (`_jwt_sub_from_token_text`) atribuye eventos a tokens
  revocados.
- Un usuario con `active_jti` NULL (nunca hizo login desde la columna)
  acepta cualquier token suyo hasta su próximo login, cambio de clave o
  cierre de sesión.
- Cambiar el email no cierra las otras sesiones (la tarea no lo pide).
- `/logout` no está exento de CSRF y `/auth/logout` sí: igual que antes.
- `change-password` y `PUT /api/user/profile` no tienen límite de
  intentos: sirven para probar claves con una sesión robada. **Alta.**
- El límite de login por IP sale de `X-Forwarded-For`: cambiándolo se
  saltea (ya era así; lo usé para que el arnés no choque con el límite).
  **Alta.**
- Si la base falla al cerrar sesión, da 500 y no borra la cookie.
- Un usuario sin hash de clave válido no puede cambiar su email.
- `change-password` con la clave mal sigue dando 401, y la pantalla lo
  toma como sesión vencida y manda al login. No lo toqué.

### Supuestos reversibles

- 400 y no 401 para la clave equivocada en el perfil: la pantalla toma
  cualquier 401 como sesión vencida.
- El email se compara sin mayúsculas ni espacios, y vaciarlo pide la clave.
- El formato del email se valida antes de pedir la clave.
- El aviso al cambiar la clave dice «Cerramos tus otras sesiones abiertas.
  Usá la nueva la próxima vez que ingreses.».
- `test_user_profile_coverage.py`: el caso que cambiaba el email sin clave
  ahora espera 400; el de email inválido mira el texto «Email no válido».

### Archivos de producto que toqué

`proyecto_maria/auth/dependencies.py`, `proyecto_maria/main.py`,
`proyecto_maria/static/v2/screens/profile.js`,
`proyecto_maria/templates/dashboard_v2.html`, `CHANGELOG.md`.

### Comandos

```bash
# con las variables de prueba de siempre (VUCE_MODE=fake, etc.)
python -m pytest -q --no-cov tests/test_sesion1.py tests/test_user_profile_coverage.py
#   → todo passed, 0 failed
python scripts/testing/sesion1_motores.py sqlite
#   → 26 líneas OK y «sqlite: todo OK»
python scripts/testing/sesion1_motores.py pg postgresql://cdi@127.0.0.1:55432/postgres
#   → 26 líneas OK y «pg: todo OK» (sólo acepta un Postgres local)
NODE_PATH=$(npm root -g) PY=$(which python) scripts/testing/sabotajes/sesion1.sh 014a3e4
#   → 19 líneas ROJO y «sabotajes sin rojo: 0» (~4 min; sin node+playwright sale con error)
```

## OBSERVABILIDAD-1: hecha, **sin entregar** (2026-10-28)

Encima de DISCO-1 (`88b22c8`): producto y `CHANGELOG.md` `8b1ce3b`;
casos, arnés de arranque y sabotajes `7ae35ab`; merge de tu rama
(`4e7896d`, sólo `NOW.md` y `PARA-DEV.md`) `39be45e`. **SHA probado:
`39be45e`** (el código es el de `7ae35ab`). Para ver sólo esta pieza:
`git diff 88b22c8..7ae35ab`. Va en su propio `/entregar`, después del de
DISCO-1, con subagentes, `/code-review high` y `/security-review` cuando
vuelva el cupo. **No hace falta que la revises todavía.**

### Decisiones

- **D34: contestada (a) en tu `486e655`.** La pieza sólo hace que la
  columna exista; atribuir cada métrica a su usuario queda fuera.

### Premisa: confirmada en Postgres 16 (55432)

Base con `api_logs` sin la columna y 3 filas; arranco la app, registro un
admin, pido `/robots.txt`, hago login y pido `/api/dev/stats`
(`$S/obs/premisa.py`, fuera del repo).

- **`88b22c8` (antes):** `registro 200`, `robots 200`, `login 200`,
  `stats (500, …)`, `filas antes/después: 3 3`. En el log, por cada
  pedido: `⚠️ Error logging metrics: (…) UndefinedColumnError'>: column
  "owner_username" of relation "api_logs" does not exist`. **Ningún pedido
  falla; se pierde cada métrica y el panel de admin da 500.**
- **`39be45e` (después):** `cols antes: []`, `stats (200, …)`,
  `filas antes/después: 3 6`, y en el log `✅ Migracion: agregada columna
  api_logs.owner_username` y `✅ Migracion: agregado indice
  ix_api_logs_owner_username`.

### Cómo se aplican hoy los cambios de esquema

- **Uno solo, automático:** al arrancar, `lifespan` corre `init_db`
  (`create_all`: crea tablas que no existen, no agrega columnas) y después
  los `_migrate_*` de `main.py` (19 de esquema), que agregan columnas a tablas
  viejas en SQLite y Postgres. El `Dockerfile` arranca gunicorn directo;
  `railway.json` no tiene paso de deploy. Usé ese mecanismo: no hizo
  falta preguntar.
- `proyecto_maria/scripts/migrate_add_owner.py` es manual y sólo SQLite
  (`sqlite3`, `--db`); su docstring dice «No toca PostgreSQL de producción
  — eso se hace con alembic aparte», pero **en el repo no hay alembic**
  (ni `alembic.ini` ni versiones): no compite.
- **¿Corrió en producción?** Con el repo: no pudo, producción es Postgres.
  Y el log del 24/10 muestra que a `api_logs` le falta la columna, o sea
  que nadie la agregó por otro lado. **Supuesto:** no veo la base.

### Qué hace (`_migrate_add_api_logs_owner_column`, `main.py:1288`)

- Corre al arrancar después de `_migrate_add_unidad_column`, en una
  transacción.
- Lee las columnas de `api_logs`. Si la tabla no existe, no hace nada
  (`create_all` ya la crea completa).
- Si falta, `ADD COLUMN owner_username VARCHAR(50)`: acepta vacío, sin
  default, no toca filas. En Postgres con `IF NOT EXISTS`.
- Si no hay **un índice cuya primera columna sea `owner_username`** (se
  llame `ix_api_logs_owner_username`, como lo nombra `create_all`, o
  `ix_api_logs_owner`, como el script viejo), crea
  `ix_api_logs_owner_username`.
- Si ya está todo, no hace nada **y no pide el lock** de la tabla.
- En Postgres, `lock_timeout` de 5 s: con la tabla tomada por otra
  conexión, falla al rato en vez de colgar el arranque.
- Si algo falla: `logging.exception("[OBSERVABILIDAD-1] no se pudo agregar
  api_logs.owner_username; la app arranca igual, pero las métricas no se
  graban hasta que exista")`, con el motivo, y la app sigue. El próximo
  arranque reintenta.

### Puertas sobre `39be45e`

| Puerta | Salida |
|---|---|
| `tests/test_observabilidad1.py` (SQLite, 8 casos) | `8 passed` |
| Arranque real con uvicorn, SQLite y Postgres 16 | 38 `OK`, `fallas 0`, salida 0 |
| Sabotajes `observabilidad1.sh` con `PG_URL` (sobre `7ae35ab`) | 16 `ROJO`, `sabotajes sin rojo: 0; no corridos: 0`, salida 0 |
| Suite completa, desde worktree limpio | `3855 passed, 336 skipped, 2 xfailed, 95 warnings in 515.51s`, `compileall 0`, `pytest salida 0` |
| Smoke | `==> OK · telemetría + alias session/state + by-cuit protegido`, salida 0 |
| Ataque de aislamiento | `Bloqueado: 22 · Fugas: 0`, `✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.`, salida 0 |
| Subagentes, `/code-review high`, `/security-review` | **No corridos:** sin cupo hasta las 18:00 UTC |

El arranque prueba, en cada motor: base vieja con filas → columna
`VARCHAR(50)` nullable sin default, un único índice, filas iguales y sin
dueño inventado, la métrica de `/robots.txt` grabada, sin «Error logging
metrics», `/api/dev/stats` 200; segundo arranque (en Postgres, con una
lectura abierta sobre `api_logs`) → esquema y filas iguales y nada en el
log. Falla simulada (SQLite: `api_logs` es una vista; Postgres: otra
conexión con `LOCK … ACCESS EXCLUSIVE`) → la app arranca (~8 s en
Postgres), el log trae el motivo y `/robots.txt` da 200; en Postgres, al
soltar la tabla el próximo arranque la agrega.

Los 16 sabotajes, uno por regla: el arranque no la llama; no agrega la
columna (SQLite y Postgres); NOT NULL o DEFAULT con dueño; no crea el
índice (SQLite y Postgres); busca el índice por nombre (duplica el del
script viejo); agrega la columna aunque ya esté; pide el lock aunque ya
esté; sin tabla no se va antes; la falla se propaga; la falla frena el
arranque; la falla no va al log; va al log sin el motivo; espera el lock
sin límite.

### Comandos

```bash
# Postgres 16 descartable en 127.0.0.1:55432, rol cdi (sólo acepta host local)
python -m pytest -q --no-cov tests/test_observabilidad1.py
#   → 8 passed
python scripts/testing/observabilidad1_arranque.py postgresql://cdi@127.0.0.1:55432/postgres
#   → 38 líneas OK y «fallas 0» (sin URL corre sólo SQLite)
PY=$(which python) PG_URL=postgresql://cdi@127.0.0.1:55432/postgres \
  scripts/testing/sabotajes/observabilidad1.sh 7ae35ab
#   → 16 «ROJO» y «sabotajes sin rojo: 0; no corridos: 0» (~5 min)
```

### Riesgos

Otras columnas del modelo que una base vieja podría no tener: las que
agrega `migrate_add_owner.py` y ningún `_migrate_*`. Si falta una, toda
consulta a esa tabla da `UndefinedColumn`:

- `clients.owner_username`: supuesto, en producción está, porque el
  aislamiento por dueño funciona y sin ella fallaría todo.
- `ncm_notes.owner_username` (y su índice `ix_ncm_notes_owner_ncm`); el
  script además rehace la tabla para que `client_id` acepte vacío, y eso
  tampoco lo hace ningún helper.
- `client_product_history.owner_username` (e `ix_cph_owner_client`).
- `system_backups.owner_username` (e `ix_system_backups_owner`).

Ya cubiertas por helpers: `operations.owner_username`, `op_code`,
`source`, `extra` (`_migrate_sync_operations_columns`) y `clients.notes`,
`favorite` (`_migrate_sync_clients_columns`). Las tablas creadas después
(`vendor_catalog_products`, `telemetry_events`, `estudios`,
`ncm_historial`…) las crea `create_all` completas: supuesto: el clon es
superficial y no llega a cuándo se crearon.

De esta pieza:

- El `CREATE INDEX` no es `CONCURRENTLY`: con un `api_logs` grande, el
  primer arranque tarda lo que tarde construirlo, con la tabla bloqueada
  para escritura. `lock_timeout` acota la espera del lock, no la
  construcción. Desde que falta la columna la tabla no crece; cuántas
  filas tiene de antes, no lo sé.
- En Postgres, si falla el índice se revierte también la columna; el
  próximo arranque reintenta las dos.
- El arranque puede demorarse hasta 5 s si otra conexión tiene la tabla.
- Con más de un worker (`WEB_CONCURRENCY` en `gunicorn_conf.py`; el
  `Dockerfile` usa 1), dos arranques a la vez: uno puede fallar y dejarlo
  en el log, y el esquema queda bien. **No probado.**
- D34 (a): las métricas siguen sin dueño. Propuesta para otra pieza: que
  `MetricsMiddleware` grabe el usuario leyendo el token ya verificado; toca
  sesión y autenticación, con su revisión.

### Supuestos reversibles

- La columna va sin la clave foránea a `users` que tiene el modelo:
  agregarla valida todas las filas y puede fallar con datos viejos.
- `lock_timeout` de 5 s.
- Se acepta como índice el `ix_api_logs_owner` del script viejo.
- Dueño vacío (D34 (a)).

### Archivos de producto que toqué

`proyecto_maria/main.py`, `CHANGELOG.md`.

## DISCO-1: hecha, **sin entregar** (2026-10-28)

Encima de DATOS-1 (`c996ad4`) y del merge de tu rama `1f6e0de`
(`cf84a76`): producto y `CHANGELOG.md` `bd53fc4`; casos y sabotajes
`0f1161a`; prueba en Postgres y textos de dos sabotajes `88b22c8`.
**SHA probado: `88b22c8`.** Para ver sólo esta pieza:
`git diff cf84a76..88b22c8`. Va en su propio `/entregar`, la última,
después del de DATOS-1, con subagentes, `/code-review high` y
`/security-review` cuando vuelva el cupo. **No hace falta que la revises
todavía.**

### Decisiones

- **D33: contestada (a) en `a3efc3a`.** El riesgo que pediste está en
  «Riesgos».
- **D33. ¿Se rescatan los historiales que hoy están en el contenedor de
  producción?** El primer arranque con DISCO-1 es un deploy, y ese deploy
  borra los archivos como cualquier otro deploy.
  - (a) **Se aceptan perdidos** (recomiendo): es un caché de sugerencias,
    cada deploy ya lo borró hasta hoy, y rescatarlo toca producción a mano.
  - (b) Antes del deploy, Emi copia los `ncm_historial_*.json` del
    contenedor que corre y los pone en el `DATA_DIR` del nuevo (o en un
    volumen), y reinicia: el cargador los toma una vez. Toca producción:
    lo decide Emi.

### Premisa: `DATA_DIR` no es persistente (confirmado con código)

- `DATA_DIR = os.getenv("CDI_DATA_DIR") or os.path.join(basedir, 'data')`
  (`proyecto_maria/main.py:34`): sin la variable, `/app/data` en la imagen.
- `Dockerfile`: `WORKDIR /app` y `RUN mkdir -p data generated backups logs`
  (línea 46); copia sólo `proyecto_maria` y `gunicorn_conf.py` (42-43).
- `railway.json` no declara volumen (builder DOCKERFILE, 1 réplica,
  healthcheck `/health`). `docker-compose.yml` monta `./data:/app/data`,
  pero es sólo local.
- **Supuesto:** no veo las variables ni los volúmenes de Railway. Si
  hubiera un volumen montado en `/app/data`, o `CDI_DATA_DIR` apuntando a
  uno, la premisa cae para ese caso y el primer arranque cargaría los
  archivos (ver abajo).

### Lo demás que se escribe en `DATA_DIR` (o al lado), una línea cada uno

- `descargas/<hash>/` (`DOWNLOADS_DIR`, `main.py:47`): TXT de MARIA y
  Excel. **Temporal**: se regeneran; un link de descarga viejo da 404
  después de un deploy.
- `generated/` (`main.py:8184`, `8224`): plantillas Excel con fecha.
  **Temporal.**
- `localStorage_backup.json` (`BACKUP_FILE`, `main.py:36`): no se usa en
  ningún lado.
- `Operation.generated_file`: columna que nunca se escribe (sólo se lee en
  7143 y 7224).
- `excel_generator.py:102`: escribe en `DATA_DIR` sólo si lo llaman sin
  `output_dir` (scripts y pruebas). **Temporal.**
- Fuera de `DATA_DIR` y también efímero: `proyecto_maria/data/error_notes.json`
  (`core/error_notes_tracker.py`, estadística de notas de error del
  admin). **Dato del usuario que se pierde** en cada deploy; no es de esta
  tarea, va como riesgo. `maria.log` si el log a archivo está prendido.
- Archivos subidos: `tempfile.mkstemp` (`main.py:8287`). **Temporal.**

### Qué hace

- Tabla nueva `ncm_historial` (`database/models.py`, `NcmHistorial`):
  dueño (clave foránea a `users.username`), clave, descripción, NCM y
  cuenta; única por dueño y clave. La clave es el sha256 de la
  descripción **tal cual se guardaba** (sin normalizar), para que la
  unicidad no dependa del largo del texto. El orden de sugerencia es el de
  inserción, como en el archivo.
- Confirmar (`guardar-uso`): un solo `INSERT … ON CONFLICT DO UPDATE` que
  suma uno y actualiza la NCM. Sin leer antes: dos confirmaciones a la vez
  no pierden cuenta.
- Importar: suma y cuenta duplicados igual que antes; lo ya existente
  conserva la cuenta y toma la NCM nueva. Todo en un commit: si falla, 500
  «No se pudo guardar» y no queda nada a medias.
- Sugerir: lee sólo lo del dueño; si la lectura falla, sigue sin historial.
- Al arrancar: carga una vez cada `ncm_historial_*.json` de `DATA_DIR` a
  su dueño con `ON CONFLICT DO NOTHING` (no suma dos veces ni pisa lo
  confirmado después) y lo renombra a `.migrado`. Ya no lo vuelve a leer.
  Un archivo roto, con un nombre que corresponde a más de un usuario o a
  ninguno, o con una cuenta que no entra en la columna, va al log (sin
  copiar descripciones) y queda en su lugar; nunca frena el arranque.

### Qué pasa en producción el primer arranque

- `create_all` crea sólo `ncm_historial`; las demás tablas no se tocan
  (en Postgres conservan sus filas, abajo).
- El cargador busca archivos en `DATA_DIR`. Sin volumen, el contenedor
  nuevo arranca vacío: no carga nada y no escribe nada en el log.
- Lo acumulado en el contenedor que corre desde el último deploy se pierde
  en este deploy, igual que en todos los anteriores. Es la D33.
- Con varios workers el cargador corre en cada uno; es idempotente (el
  segundo no inserta y el que pierde el renombre lo anota en el log). Hoy
  es uno solo (`--workers 1`, `gunicorn_conf.py`).

### Puertas sobre `88b22c8`

| Puerta | Salida exacta |
|---|---|
| Suite completa (worktree limpio) | `3847 passed, 336 skipped, 2 xfailed, 94 warnings in 502.78s (0:08:22)`; `compileall 0` |
| Sabotajes `scripts/testing/sabotajes/disco1.sh 88b22c8` | 20 líneas `ROJO`; `sabotajes sin rojo: 0` |
| `scripts/testing/disco1_postgres.py` (Postgres 16 local, parte de `c996ad4` con datos) | 20 `OK`; `fallas: 0`; no queda base |
| El mismo, con confirmar «leer y después escribir» (sabotaje a mano) | `FALLA \| 16 confirmaciones a la vez cuentan 16: [500] [('Rodamiento sintetico', '8482.10.10', 7)]`; `fallas: 1` |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| `ataque_aislamiento.sh` (Postgres) | `Bloqueado: 22 · Fugas: 0`; `✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.` |
| `tests/test_disco1.py` sobre `c996ad4` | rojo al importar: `cannot import name 'NcmHistorial'` |

Lo que discrimina de verdad son los 20 sabotajes (uno por regla: suma,
NCM, commit, que no escriba el archivo, clave tal cual, dueño, carrera,
importar ×4, cargar dos veces, pisar, renombrar, roto ×4, ambiguo,
arranque) y el script de Postgres, que primero comprueba que la versión
anterior escribía archivos. **No corrido:** subagentes, `/code-review` y
`/security-review` (sin cupo hasta las 18:00 UTC).

```bash
# sabotajes: 20 «ROJO», última línea «sabotajes sin rojo: 0»
scripts/testing/sabotajes/disco1.sh 88b22c8
# Postgres 16 local en 55432, con un venv que tenga uvicorn y psycopg2: «fallas: 0»
python scripts/testing/disco1_postgres.py postgresql://cdi@127.0.0.1:55432/postgres
# el test nuevo: «11 passed»
python -m pytest -q --no-cov tests/test_disco1.py
```

### Riesgos

- **D33 (a):** si nadie hace (b), el primer deploy con DISCO-1 pierde los
  historiales que haya, igual que todos los deploys hasta hoy.
- Las pruebas usan `./data` como `DATA_DIR` y cada arranque del
  `TestClient` corre el cargador ahí. Restos locales de otras pruebas con
  usuarios que no están en la base de prueba quedan donde están; un
  checkout limpio no tiene ninguno.
- Un archivo con una cuenta que no entra en un entero de Postgres se
  rechaza entero, va al log y queda en su lugar (probado).
- Nombres ambiguos: la validación de usuario (`^[a-zA-Z0-9_-]{3,30}$`)
  los hace teóricos; igual no se le cargan a nadie.
- `error_notes.json` sigue siendo efímero (fuera de la tarea).

### Supuestos reversibles

- La clave es el sha256 de la descripción exacta; la descripción se
  guarda como vino.
- Las entradas salteadas al cargar (sin descripción o sin NCM) no se
  copian al log, sólo cuántas.
- Una cuenta inválida en el archivo (no entero, booleano o menor que 1)
  se carga como 1.

### Archivos de producto que toqué

`proyecto_maria/main.py`, `proyecto_maria/database/models.py`,
`CHANGELOG.md`. Casos existentes adaptados: `tests/test_catalogo_ncm1.py`,
`tests/test_ncm_sugerir_catalog.py`.

## DATOS-1: hecha, **sin entregar** (2026-10-28)

Encima de DESPACHO-1b (`e59e1a8`) y del merge de tu rama con la D32 (a)
(`d01f95c`): producto y `CHANGELOG.md` `7d09c6f`; casos `4416076`; prueba en
Postgres y sabotajes `162d277`; arreglo de los casos, que gastaban el cupo
de `test_user`, `c996ad4`. **SHA probado: `c996ad4`.** Para ver sólo esta
pieza: `git diff d01f95c..c996ad4`. Va en su propio `/entregar`,
después del de DESPACHO-1b, con subagentes, `/code-review` y
`/security-review` cuando vuelva el cupo. **No hace falta que la revises
todavía.** La D32 está contestada (a) en `0a6e887`: es lo que hice.

- **D5 / D32 (a), borrar un cliente con presupuesto compartido**
  (`delete_cliente`, `main.py`): antes de borrar las operaciones del
  cliente, borra los presupuestos compartidos de esas operaciones (y sólo
  de esas), en la misma transacción que el cliente. Si algo falla a mitad,
  el rollback que ya estaba deja todo como antes.
  - **En Postgres** (`scripts/testing/datos1_postgres.py`, 16.15 local y
    descartable): sobre el código anterior (`d01f95c`) el dueño recibe
    **500** y no se borra nada («fallas: 3»); sobre `162d277`, 200, no
    quedan cliente, operaciones ni presupuestos, el link da 404 y siguen
    andando el presupuesto de otro cliente del mismo dueño y el de otro
    dueño («fallas: 0»). Otro dueño recibe 404 y el presupuesto sigue. Una
    falla simulada al borrar el cliente da 500 y no borra nada.
  - **Pantalla** (`clientes.js`, la v2, que ya avisaba qué se borra): ahora
    dice «…y dejarán de andar los links de presupuestos que compartiste.
    Esta acción no se puede deshacer.». La vieja (`app.js`) no avisa nada y
    no se tocó, como dijiste.
- **D2, `/health`:** sin base responde **503** con `database: "error"` y
  `status: "degraded"`, sin `db_error`. El texto del error va al log
  (`logging.exception`). Con base, 200 igual que antes. `railway.json` no se
  tocó; `/admin/health/detailed` tampoco.
- **D6, los 500:** los dos manejadores (el de `HTTPException` 500 y el de
  excepciones no manejadas) devuelven sólo el mensaje amigable y
  `code: "internal_error"`; el detalle, con su traza, va al log. Los 4xx
  siguen con su `detail` tal cual (hay prueba con uno de la app y otro
  armado). `finalize.js` mostraba `dev_detail` en el aviso: ahora muestra
  `detail` y corta en 200 caracteres en vez de 100, porque el mensaje
  amigable mide 131.
- **Archivos de producto:** `proyecto_maria/main.py`,
  `proyecto_maria/static/v2/screens/clientes.js`,
  `proyecto_maria/static/v2/screens/finalize.js` y `CHANGELOG.md`.

**Qué hace Railway con una publicación nueva si la base no contesta (no
verificado: `docs.railway.com` está bloqueado desde acá).** Según
`railway.json`, Railway prueba `/health` al publicar, con 60 s de tope, y no
pasa el tráfico a la publicación nueva hasta que responda 200. Pero lo que
pasa de verdad acá es otra cosa, y eso sí lo vi: **si la base no contesta al
arrancar, la app ni siquiera levanta.** `init_db` corre en el arranque sin
`try`, uvicorn sale con código 3 y `/health` no contesta nunca. La
publicación nueva falla y, hasta donde sé, queda la anterior. El 503 sólo
cambia algo si la base se cae con la app ya andando: ahí `/health` lo dice,
pero Railway, hasta donde sé, no vuelve a mirar `/health` después de
publicar, así que no la reinicia por eso. Lo útil del 503 es para quien
mire `/health` desde afuera (un monitor), no para Railway.

**Puertas** (sobre `c996ad4`, salvo Postgres, smoke y ataque, que corrí
sobre `162d277`: entre los dos sólo cambia `tests/test_datos1.py`):

| Puerta | Resultado |
|---|---|
| `tests/test_datos1.py` | 9 passed (en rojo sobre el código anterior: 4 fallas por el motivo de la tarea) |
| Suite completa (`--timeout=120`) y `compileall`, `c996ad4` | `3836 passed, 336 skipped, 2 xfailed, 95 warnings in 497.50s (0:08:17)`, pytest salida 0; `compileall 0` |
| Suite completa sobre `162d277` (antes del arreglo) | `6 failed, 3830 passed, 336 skipped, 2 xfailed`, salida 1: abajo |
| `scripts/testing/datos1_postgres.py` (Postgres 16 local, base `datos1a`) | `d01f95c`: «fallas: 3», salida 1 (500 al borrar). `162d277`: «fallas: 0», salida 0 |
| Sabotajes `scripts/testing/sabotajes/datos1.sh c996ad4` | 12 líneas ROJO, «sabotajes sin rojo: 0», salida 0 |
| `smoke_friccion.sh` (puerto 8862) | salida 0, «OK · telemetría + alias session/state + by-cuit protegido» |
| `ataque_aislamiento.sh` (puerto 8863) | salida 0, «PUERTA G3 PASADA. Ningún despachante ve datos de otro.» |

El primer intento del ataque salió 1 por entorno: el script busca
`./venv/bin/python` y, si no está, usa `python3` del sistema, que no tiene
`fastapi` (`ModuleNotFoundError: No module named 'fastapi'`). Con el venv
en el `PATH`, salida 0.

**La suite sobre `162d277` salió en rojo por mis casos, no por el
producto.** Seis casos de otros archivos
(`test_op_code_and_fill_if_empty.py`, `test_operations_manual.py` y cuatro
de `test_prelaunch_block1.py::TestOperacionManual`) recibían **402**
«Alcanzaste el límite de 15 operaciones del plan Premium». Las pruebas de
borrado de `test_datos1.py` creaban operaciones como `test_user`, que
comparte toda la suite, y le gastaban 4 de su cupo: lo medí al final de una
corrida de ese archivo solo, 4 sobre `162d277` y 0 sobre `c996ad4`, sin
clientes, operaciones ni presupuestos sobrantes. El arreglo (`c996ad4`):
cada prueba usa dueños propios y borra al terminar lo que creó. Con eso,
suite en verde y los 12 sabotajes siguen en rojo.

**Sabotajes (12, uno por regla), todos en rojo:** `/health` sin base sigue
en 200; `/health` vuelve a mostrar el error de la base; `/health` no deja
el error en el log; cada 500 vuelve a mandar `dev_detail` (uno por
manejador); cada 500 no deja el detalle en el log (uno por manejador); los
4xx pierden su motivo; no se borran los presupuestos del cliente; se
borran también los ajenos; el borrado no es una sola transacción; otro
dueño puede borrar el cliente.

**Comandos:**

```bash
git diff d01f95c..c996ad4 --stat        # 7 archivos
python -m pytest -q --no-cov -p no:randomly tests/test_datos1.py
#   9 passed
PY=<venv>/bin/python scripts/testing/sabotajes/datos1.sh c996ad4
#   12 líneas ROJO y al final «sabotajes sin rojo: 0»
python scripts/testing/datos1_postgres.py postgresql://cdi@127.0.0.1:<puerto>/<base>
#   8 líneas OK y «fallas: 0» (sólo acepta un Postgres local)
```

**Riesgos y lo que no hice:**
- **Un link compartido deja de andar** cuando se borra su cliente (es la
  D32 (a)): quien lo abra ve 404. Está en `CHANGELOG.md` y la pantalla v2
  lo avisa; la vieja no.
- **Previo, fuera de la pieza:** si alguien de un equipo cargó operaciones
  sobre el cliente, el borrado sólo toca las del dueño. En Postgres, las de
  otro miembro seguirían bloqueando el borrado del cliente por la clave
  foránea (500 y nada borrado). No lo probé.
- Los 502 y 503 de la app siguen pasando su `detail` tal cual: D6 habla de
  los 500 y no los toqué.
- La falla a mitad está probada con una falla simulada al borrar el
  cliente, el último paso. No probé una caída de la base a mitad.
- El texto nuevo de la pantalla no lo vi en el navegador: está en el código
  (`clientes.js:1816`) y no tiene prueba automática.
- **Fuera de la pieza: la suite está cerca del límite de `test_user`.** El
  resto de los archivos ya le gasta por lo menos 11 de sus 15 operaciones
  (con mis 4, caían). Un caso nuevo que cree unas pocas operaciones como
  `test_user` va a romper casos ajenos, con un 402 que no apunta al
  culpable. No lo toqué.
- Sin correr todavía: subagentes, `/code-review` y `/security-review`.
  Vuelven a las 18:00 UTC.

## DESPACHO-1b: hecha, **sin entregar** (2026-10-28)

Commits encima de SEGURO-1 (`371cde2`), de mi informe (`de9cb24`) y del
merge de tu rama (`49f8e29`): producto y `CHANGELOG.md` `0591722`; casos,
pantalla y sabotajes `e59e1a8`. **SHA probado: `e59e1a8`.** Para ver sólo
esta pieza: `git diff 49f8e29..e59e1a8`. Va en su propio `/entregar`,
después del de SEGURO-1, con subagentes y `/code-review` cuando vuelva el
cupo. **No hace falta que la revises todavía.** La D31 está contestada
(a) en `3da0a8b`: es lo que hice, sin cambios.

**La premisa: confirmada, sin Gemini y sin librería nueva.** El repo ya saca
texto de PDF con `pypdf` (el lector de facturas, `pdf_extractor.py`) y lo
corre aparte con su tope de tiempo (`_leer_pdf_aparte`). Uso lo mismo, con
los mismos topes de página.

- **Qué lee** (`proyecto_maria/core/despacho_lector.py`, nuevo): por
  renglón, posición SIM, descripción, sufijos, origen, unidad, cantidad,
  valor unitario y kilo neto. **Por rótulo:** busca la línea del rótulo y
  toma el valor de abajo en la misma columna. Hay una prueba con los
  rótulos en otro orden y otra con un valor vacío en el medio: sin kilo, el
  origen sigue siendo el origen (leyendo por posición, caería en el kilo).
- **Números** `1.234,56`. Otra forma (`12.5`, `1,234.56`) no se adivina:
  queda faltante, con un aviso.
- **Subítems:** con unidad `SUBITEM`, un renglón por subítem con su valor,
  descripción y sufijos. La posición y el origen se toman del ítem, y el
  aviso lo dice. Lo que al subítem le falta no se toma del ítem.
- **Lo que falta** queda en `faltantes`, vacío y marcado en pantalla. Nada
  se rellena: sin kilo, el peso queda vacío, no cero ni una cuenta.
- **Escaneado:** sin texto, avisa «El PDF no tiene texto que se pueda leer:
  parece escaneado…» y no devuelve renglones. Un PDF que no es despacho o
  está roto, también avisa.
- **Tilde rota** («Las dem?s»): la descripción queda como vino, con un
  aviso para que la corrijan en la revisión.
- **Divisa:** la del FOB, no la del flete (hay prueba con las dos
  distintas).
- **Pantalla** (Catálogo del cliente, `clientes.js`): «Cargar desde
  despacho» abre el selector, muestra los renglones editables con lo
  faltante marcado y guarda sólo al tocar «Guardar en el catálogo». La
  prueba de pantalla falla si se pide guardar antes del clic. Probada en
  1280 y 390 px.
- **Guardar** es todo o nada: si un renglón no sirve, 422 con qué le falta
  a cada uno y no se guarda ninguno. Pide posición con sus 8 dígitos y
  descripción; el origen, si viene, tiene que ser un país de la tabla. Tope
  de renglones (400 si se pasa). Lista vacía, 400.
- **De quién:** leer y guardar usan `_get_owned_client`: un cliente ajeno o
  de otro dueño da 404 y no se toca nada.
- **Nunca** arma un TXT ni una operación: hay pruebas que cuentan las
  operaciones antes y después y que fallan si se llama al generador. El
  lector de facturas sigue rechazando un despacho (prueba con el sintético).
- **Datos:** el sintético lo arma la prueba con la forma de
  `DESPACHOS-FORMA.md` y valores inventados: dos ítems, uno con subítems,
  un `AI` con espacios, «Las dem?s», FOB y flete en divisas distintas y un
  renglón sin kilo neto. Ningún despacho real.
- **Archivos de producto:** `proyecto_maria/core/despacho_lector.py`
  (nuevo), `proyecto_maria/main.py`, `proyecto_maria/static/v2/screens/clientes.js`,
  `proyecto_maria/static/v2/app_v2.css`,
  `proyecto_maria/templates/dashboard_v2.html` y `CHANGELOG.md`.

**Supuestos reversibles:**
- Los rótulos del subítem («Nº Subitem» y sus valores) son supuestos: los
  despachos de muestra no los traían con su rótulo. Están escritos en la
  cabecera de `despacho_lector.py`.
- La unidad, la cantidad y el valor unitario salen de «VALOR MERCADERIA».
- El peso que guarda el catálogo es por unidad: kilo neto dividido
  cantidad, si están los dos.

**Puertas sobre `e59e1a8`:**

| Puerta | Resultado |
|---|---|
| `tests/test_despacho1b.py` | 50 passed |
| Suite completa (`--timeout=120`) y `compileall` | 3827 passed, 336 skipped, 2 xfailed, 0 failed; `compileall` 0 |
| Sabotajes `scripts/testing/sabotajes/despacho1b.sh e59e1a8` | 24 líneas ROJO, «sabotajes sin rojo: 0», salida 0 |
| Pantalla `scripts/testing/pantalla_despacho1b.js` | OK en 1280 px (panel 644 px) y 390 px (panel 308 px) |
| `smoke_friccion.sh` (puerto 8855) | salida 0, «OK · telemetría + alias session/state + by-cuit protegido» |
| `ataque_aislamiento.sh` (puerto 8857) | salida 0, «PUERTA G3 PASADA. Ningún despachante ve datos de otro.» (cubre clientes y descargas; lo de esta pieza lo cubren sus pruebas de 404) |

La suite suma los 50 casos nuevos a los 3777 de SEGURO-1. Los 32 avisos
«Task was destroyed but it is pending!» de su salida ya estaban en las
suites de `4ca6829` y `a08de1f`: no son de esta pieza. Los sabotajes
corrieron también en `9dcd5cc` (mismo árbol que `e59e1a8`), con los mismos 24
rojos.

**Sabotajes (24, uno por regla), todos en rojo:** el subítem toma lo que le
falta del ítem; lo que falta no se marca; se lee por posición; se aceptan
números con otra forma; un número que no se entiende se lee igual; los
subítems no se separan; la posición heredada no se avisa; la divisa es la
del flete; un sufijo con espacios no se lee; un escaneado no avisa; sin
kilo se inventa el peso; leer no mira el dueño; guardar no mira el dueño;
se guarda lo bueno y se descarta el resto; guardar acepta una lista vacía;
guardar no tiene tope; leer acepta lo que no es PDF; guardar arma un TXT;
guardar crea una operación; el lector de facturas acepta despachos; el
botón no está conectado; el faltante no se marca en pantalla; se guarda al
leer, sin revisar; el panel es más ancho que la pantalla.

**Comandos:**

```bash
git diff 49f8e29..e59e1a8 --stat        # 9 archivos, ninguno en tests/fixtures
python -m pytest -q --no-cov tests/test_despacho1b.py
#   50 passed
PY=<venv>/bin/python scripts/testing/sabotajes/despacho1b.sh e59e1a8
#   24 líneas ROJO y al final «sabotajes sin rojo: 0»
PY=<venv>/bin/python BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_despacho1b.js
#   OK en 1280 y 390
```

**Riesgos y lo que no hice:**
- **No se probó con un despacho real** (no entran). Si el sistema del
  despachante pega dos columnas con un solo espacio, el valor puede quedar
  faltante: falla hacia «falta», no hacia un dato cambiado.
- **Costos de la D31 (a), decidida por la PM:**
  1. **El valor unitario queda sin divisa** en el catálogo: si el despacho
     estaba en otra moneda, la pantalla de revisión la muestra, pero el
     catálogo la pierde y su promedio puede mezclar monedas.
  2. **Dos subítems que sólo difieren en sufijos** (el `AI`) **se funden
     en un producto**, porque el catálogo junta por NCM y descripción
     parecida.
  Los sufijos, la unidad y la posición completa tampoco se guardan; se ven
  en la revisión.
- Dos renglones con el mismo NCM y descripción parecida (Jaccard ≥ 0,80,
  la regla de siempre del catálogo) se funden en uno: `guardados` puede
  decir más de lo que aparece.
- Guardar en un producto que ya existe promedia sus valores, como el
  aprendizaje de hoy.
- `leer` tiene el límite de pedidos del resto; `guardar` no, igual que el
  aprendizaje de hoy.
- El rechazo del lector de facturas pasa por Gemini, simulado en la prueba.
- Previos, no de esta pieza: `--t-12` no está definido en el CSS; el
  tablero mide 523 px de ancho en 390.
- La pantalla muestra en notación exponencial un número absurdo
  (`1e21`); no cambia lo que se guarda.
- Sin correr todavía: subagentes, `/code-review` y `/security-review`.
  Vuelven a las 18:00 UTC.

## SEGURO-1: hecha, **sin entregar** (2026-10-28)

Commits encima de SUFIJOS-2 (`4ca6829`) y del merge de tu rama
(`1948207`): producto y `CHANGELOG.md` `4f75f3d`; casos y sabotajes
`a08de1f`; un sabotaje con su patrón arreglado `371cde2`. **SHA probado:
`371cde2`.** Sabotajes 10/10 en rojo en `371cde2`
(`scripts/testing/sabotajes/seguro1.sh`) y suite completa en `a08de1f`:
3777 passed, 336 skipped, 2 xfailed, 0 failed (`compileall` limpio). Entre `a08de1f` y `371cde2` sólo cambia el script de
sabotajes, que pytest no junta. Va en su propio `/entregar`, después del de SUFIJOS-2,
con `/security-review` porque es un campo de dinero. **No hace falta que la
revises todavía.** La D30 ya está contestada (a).

**La premisa: confirmada.** `cuentas_del_valor` no conocía el incoterm,
pero quien la llama (`_cuentas_del_valor` en `main.py`) tiene
`request.incoterm`. Se lo paso: la regla vive en el servidor sin salir del
alcance.

- **La regla, en el servidor:** `INCOTERMS_CON_SEGURO = ("CIF", "CIP",
  "DPU", "DAP", "DDP")` en `maria_generator.py`. Con esos, las cuentas
  traen `seguro_sugerido: None` y `seguro_en_el_precio: true`. Con los
  demás, el 1 % como antes. Mayúsculas, minúsculas y espacios dan lo mismo
  (`" cif "` es CIF); vacío o desconocido (`"XYZ"`, `"C I F"`), con 1 %.
- **La pantalla sigue al servidor**, no al incoterm de la operación: sin
  `seguro_en_el_precio` hay botón aunque la operación diga CIF (hay una
  prueba que lo fija). Con CIF no hay «Calcular seguro» ni «Dejar el
  seguro», y `calcularSeguro()` no pone nada. La nota dice «Con CIF el
  seguro ya está en el precio: el sistema no lo calcula.» y agrega que lo
  carguen en la revisión si no hay seguro.
- **El seguro se sigue declarando:** una operación CIF con seguro 14,88
  sale con `MDDTASS 14.88` y `CDDTINCOTE CIF`. Un seguro escrito de 93,13
  (el mismo número que daría el 1 %) con CIF también genera: es de la
  persona.
- **Cambio de incoterm con el seguro calculado:** cuando llegan las cuentas
  del pedido de ahora con `seguro_en_el_precio` y la operación tiene
  `seguro_calculado`, la pantalla borra el seguro, saca la marca, lo agrega
  a `campos_sin_leer` (el mismo mecanismo que un campo que el lector no
  leyó) y lo saca de `campos_completados`. El semáforo dice «No pudimos leer
  el seguro de la factura: completalo.». Con cuentas de otro pedido no
  borra nada. El leído o escrito no se toca. De CIF a CFR vuelve el botón y
  no pone nada solo.
- **El servidor también frena:** un pedido con `seguro_calculado` y uno de
  los cinco da 400 «Seguro: lo calculó el sistema, pero con CIF el seguro ya
  está en el precio y no se calcula. Cargá el de la factura en la
  revisión.», en `/generate_maria` y en los avisos, aunque las cuentas
  estén en error. Cubre una pestaña con el `finalize.js` viejo.
- **El golden no se tocó:** `git diff 1948207..a08de1f -- tests/fixtures`
  sale vacío.
- **Dos pruebas existentes cambiaron, sin cambiar lo que miden:** en
  `tests/test_valor1.py` la expectativa de las cuentas suma
  `"seguro_en_el_precio": False`, y la función nueva
  `borrarSeguroCalculado` se suma a las listas de los arneses de pantalla de
  `test_valor1.py` y `test_valor1c.py` (extraen funciones por nombre).
- **Archivos de producto:** `proyecto_maria/core/maria_generator.py`,
  `proyecto_maria/main.py`, `proyecto_maria/static/v2/screens/finalize.js` y
  `CHANGELOG.md`.

**Supuestos reversibles:**
- El borrado usa `campos_sin_leer`, que es la lista del lector. Por eso el
  semáforo dice «No pudimos leer el seguro de la factura», aunque lo que
  pasó es que el sistema lo borró. Si preferís otro texto, es un aviso
  propio en `semaforo.js`.
- La nota nombra el incoterm de la operación («Con CIF…»); si falta, dice
  «este incoterm».
- El 400 del servidor con un calculado y CIF no estaba pedido: es la regla
  «vive en el servidor» aplicada a `seguro_calculado`. Sin él, una pestaña
  vieja mandaría el 1 % con CIF.

**Sabotajes (uno por regla):** DPU fuera de la lista; el incoterm sin
normalizar; `main.py` no pasa el incoterm; la pantalla decide por
`op.incoterm`; el botón calcula con CIF; `pintarValor` no borra; el
servidor no frena el calculado con CIF; se borra también el escrito; se
borra sin mirar la firma del pedido; el borrado deja el seguro como
completado. En la primera corrida, el del incoterm en `main.py` no
encontraba su patrón (la línea aparece cuatro veces): lo arreglé en
`371cde2` con un patrón que aparece una sola vez.

**Comandos:**

```bash
git diff 1948207..371cde2 --stat                 # 8 archivos; tests/fixtures no aparece
git diff 1948207..371cde2 -- tests/fixtures | wc -l   # 0
PY=<venv>/bin/python scripts/testing/sabotajes/seguro1.sh 371cde2
#   10 líneas ROJO y al final «sabotajes sin rojo: 0»
python -m pytest -q --no-cov tests/test_seguro1.py tests/test_valor1.py tests/test_valor1c.py
#   151 passed
```

**Riesgos y lo que no hice:**
- **Seguro 0 en el TXT si nadie lo completa** (D30, contestada (a)): un seguro «para completar» avisa en pantalla y no frena el TXT. Frenarlo es SEGURO-2.
- `finalize.js` se carga con `?v={{ version }}`; una pestaña abierta antes
  del despliegue sigue con el JS viejo y muestra el botón con CIF. Si lo
  aprieta, el servidor da el 400 de arriba: no sale el 1 % en el TXT.
- Sin correr todavía: subagentes, `/code-review` y `/security-review`.
  Vuelven a las 18:00 UTC.

## SUFIJOS-2: hecha, **sin entregar** (2026-10-28)

Commits encima de `4905cd8`: casos en rojo `a12aae3`; producto y
`CHANGELOG.md` `79dc0c6`; sabotajes `b5c63c8`; un caso más en rojo
`34ff7f0`, su arreglo `0118f5f` y su sabotaje `f2e09d8`; el comentario en
líneas cortas `4ca6829`. **SHA probado: `4ca6829`.** Sabotajes 9/9 en rojo
(`scripts/testing/sabotajes/sufijos2.sh`) y suite completa en `4ca6829`:
3731 passed, 336 skipped, 2 xfailed, 0 failed. Va en su propio `/entregar`, después del de DESTINO-1, cuando
vuelva el cupo. **No hace falta que la revises todavía.** La D29 ya
está contestada (a).

- **Sufijo libre:** un número con decimales sale con coma. `AF(2.5)` sale
  `AF(2,5)`. Un punto o una coma cuentan como decimal sólo entre dígitos y
  una sola vez: `V1.2.3` sale `V1 2 3`, como antes, y `ROJO, AZUL` sale con
  espacio. Vale también para la propuesta que arma el arancel.
- **Sufijo que pide número** (los `Z`, D29 contestada (a)) con decimales: no se
  genera. El error dice dónde (operación, ítem, sub-ítem o renglón) y cuál
  sufijo, y llega como 400.
- **Ninguno vacío:** `AA()`, `AA(   )` o `AA(--)` (que queda vacío al
  limpiar) no se generan. Mismo tipo de error.
- **Lo que sigue igual:** los `Z` enteros con la forma del archivo aceptado
  (`ZA(016384)`…) y los sufijos que ya traían coma. El golden no cambió:
  `git diff 4905cd8..4ca6829 -- tests/fixtures` sale vacío.
- **Una prueba existente cambió:**
  `tests/test_sufijos1.py::test_un_codigo_con_el_valor_vacio_es_un_codigo_que_falta`
  esperaba que `AA( )` generara con el aviso de un código que falta. La
  regla nueva dice que no se genera: ahora es
  `test_un_codigo_con_el_valor_vacio_no_se_genera`.
- **Archivos de producto:** `proyecto_maria/core/maria_generator.py` y
  `proyecto_maria/core/sufijos_arca.py`.

**La premisa.** Que la coma no rompe el campo sí se sabe desde el repo: el
TXT es `CLAVE=valor` por línea, y el archivo real de 2026 ya trae una coma
en `LDDTNOMFOD`. El paréntesis se toma entero, en el generador y en
`despachante.js`, así que la coma de adentro no parte el sufijo. Cuáles
piden número **no** se sabe desde el repo: es la D29.

**Rojo encontrado en la autorrevisión.** `\d` en Python también toma
dígitos que no son ASCII. Con eso, `٣.٥` salía `٣,٥` en el TXT. Primero el
caso en rojo (`34ff7f0`), después el arreglo con `[0-9]` (`0118f5f`) y su
sabotaje.

**Riesgos y lo que no hice:**
- En un sufijo libre, `1.234` con punto de miles sale `1,234`, que se lee
  como 1 con decimales. No hay forma de distinguirlos.
- En un `Z`, `1.234` da error y no se lee como 1234. Es a propósito: no se
  adivina.
- Fuera de alcance, sin tocar: un `Z` con texto (`16 GB`, `2 5`) pasa; el
  generador no rellena con ceros a seis dígitos como el archivo aceptado.
  Si querés, lo propongo como pieza.
- Sin correr todavía: subagentes, `/code-review` y `/security-review`.
  Vuelven a las 18:00 UTC.

## DESTINO-1: hecha, **sin entregar** (2026-10-28)

Producto `7526be9`, pruebas y sabotajes hasta `f887b4a`, encima de
`4ce6d22`. Sabotajes 15/15 en rojo (`scripts/testing/sabotajes/destino1.sh`)
y suite completa en `f887b4a`: 3697 passed, 0 failed. Va en su propio
`/entregar`, después del de ORG-1, cuando vuelva el cupo. **No hace falta que
la revises todavía.** Ojo con D28: no eran seis pruebas las que comparan el
golden entero, son ocho (se sumaron `test_maria1b_controles` y
`test_maria3_antes_de_generar`); las dos con el mismo criterio de (a).

## ORG-1, ORG-1b y DESPACHO-1a: listas, **sin entregar** (2026-10-28)

**DESPACHO-1a está hecha** (producto `e438dad`, probado en `51890cd`), en
commits aparte sobre ORG-1b. Va en el mismo `/entregar` que ORG-1 y ORG-1b,
con su propio apartado y su diff: «DESPACHO-1a», abajo.

**ORG-1b (D27 b) está hecha**, en commits aparte, con su propio SHA de
producto (`f8616cf`). Va en el mismo `/entregar` que ORG-1. Detalle en
«ORG-1b», abajo.

**ORG-1. Estado:** los cinco puntos están hechos. Tienen casos en SQLite, un script
contra Postgres, sabotajes y suite completa. **No la entrego todavía.** Tu
canal dice «`/entregar` espera a que vuelva el cupo», y el cupo de
subagentes y `/code-review` vuelve el 28/10 a las 18:00 UTC. Ahí corro la
autorrevisión independiente y `/security-review`, reproduzco lo que
encuentren y entrego con el timbre. Subo ahora para que el trabajo no se
pierda si el contenedor muere. **No hace falta que la revises todavía.**

## Decisiones

**D32 — qué pasa con el presupuesto compartido al borrar su cliente (DATOS-1, D5).**
Hoy borrar un cliente ya borra sus operaciones (es lo que dice el código
desde antes). Un presupuesto compartido (`public_quotes`) apunta a una
operación y no puede quedar sin ella (`operation_id` es obligatorio), así
que para borrar el cliente hay que elegir. El presupuesto guarda una copia
con la descripción, cantidad y valor de cada producto del cliente, el
costo calculado y el nombre del usuario.

- **(a) Recomiendo esta.** Se borran también los presupuestos compartidos de
  las operaciones del cliente, en la misma transacción. El link deja de
  andar (404) antes de vencer. Es coherente con lo que ya hace el borrado
  (borra las operaciones) y es lo único que cumple un pedido de supresión:
  la copia tiene datos del cliente. Pierde: el link compartido.
- **(b)** Las operaciones con presupuesto compartido quedan sin cliente
  (`client_id` vacío) y el presupuesto sigue hasta que venza. Pierde menos
  hoy, pero no cumple la supresión: quedan la operación y la copia, y como
  los vencidos sólo se borran si alguien abre el link, quedan para siempre.
  Esas operaciones no aparecen en ningún cliente.
- **(c)** No borrar: responder 409 «tiene presupuestos compartidos» en vez
  del 500. No pierde nada, pero no hay forma de dar de baja un presupuesto,
  así que el cliente sigue sin poder borrarse: no resuelve D5.

**D31 — contestada (a) en `3da0a8b`.** El catálogo guarda lo que ya tiene
columna; los dos costos están en los riesgos de DESPACHO-1b.

**D30 — contestada (a) en `53e1e86`.** Un seguro «para completar» sigue siendo un aviso; SEGURO-2 no la empiezo hasta verla en tu canal.

**D29 — contestada (a) en `3d3ab47`.** `PIDE_NUMERO = ("Z",)` queda.

**D28 — contestada (a) en `be1cac2`.** DESTINO-1 rompe seis pruebas que
comparan el golden entero. No
frena la entrega de ORG-1, ORG-1b y DESPACHO-1a; frena DESTINO-1, que
arranco apenas entregue. Lo aviso ahora porque pediste que avise antes de
cambiar una prueba que compara el golden.

Estas pruebas generan con `iva_adicional="IVAAD1"` y comparan contra
`maria_golden_anon.TXT` todo el archivo, byte a byte. El golden trae
`COMERC` + `IVAAD1`:

- `tests/test_generar_maria_txt.py::test_golden_reproduce_estructura_real`
- `tests/test_maria1b_controles.py::test_el_archivo_real_sale_identico_por_la_ruta`
- en `tests/test_punta_a_punta1.py`, las cuatro que comparan con
  `_GOLDEN_PATH`: líneas 433, 438, 445 y 478.

Con DESTINO-1, `IVAAD1` se lee como bien de uso de una persona. Eso da
`USOPAR` + `IVAAD1`, que difiere del golden en una línea: el `MCPL` de
`GANANCIASOP3`. Ningún par permitido da `COMERC` + `IVAAD1`, así que no
hay entrada que reproduzca el golden entero. El golden de subítems trae
`COMERC` + `NO_VALIDA`, que es un par permitido, y no cambia.

- **(a) Recomiendo esta.** El golden no se toca. Las seis pruebas comparan
  el archivo entero salvo esa línea, y la prueba exige que esa línea diga
  exactamente `USOPAR`. Así cualquier otro cambio sigue apareciendo y la
  diferencia queda escrita, con referencia a la pregunta 7 al despachante.
- **(b)** Las pruebas siguen generando con comercialización. Ahí la línea
  que difiere pasa a ser la de `IVAADICIONAL1` (`NO_VALIDA` en vez de
  `IVAAD1`). El arreglo de las pruebas es el mismo de (a), pero muestra un
  caso que el MARIA nunca vio.
- **(c)** DESTINO-1 espera la respuesta a la pregunta 7.

D26 y D27 ya están contestadas: D26 (a) por ahora, D27 (b) como ORG-1b.

| Pieza | SHA |
|---|---|
| Casos en rojo antes del producto | `9d727e7` |
| Producto y `CHANGELOG.md` | `e43810b` |
| Sabotajes (9, uno por motivo) | `18f7f25` |
| Carrera de dos invitaciones a la vez, en Postgres | `ddfc798` |
| **SHA probado:** suite, compileall, smoke, aislamiento | **`18f7f25`** |
| ORG-1b: la prueba de pantalla, en rojo antes del producto | `9ad42e4` |
| **ORG-1b: producto y `CHANGELOG.md`** | **`f8616cf`** |
| ORG-1b: sabotajes (7, uno por motivo) | `b7a7927` |
| ORG-1b: arreglo de la prueba (dos sabotajes no daban su rojo) | `5d42909` |
| **ORG-1b, SHA probado:** pantalla y sabotajes | **`5d42909`** |

Entre `18f7f25` y `ddfc798` sólo cambia `scripts/testing/org1_postgres.py`,
que pytest no junta. Tu diff de revisión de ORG-1 parte de `ea64a9c`, la
punta de tu rama.

ORG-1b está encima de `ddfc798`, pero no pegada a él. En el medio quedan mi
informe (`de8d175`) y el merge de tu rama (`373ef55`). Ninguno de los dos
toca producto. Para ver sólo ORG-1b: `git diff 373ef55..5d42909`.

Toqué estos archivos de producto:
- `proyecto_maria/main.py` (ORG-1)
- `proyecto_maria/templates/landing.html` (ORG-1b)
- `CHANGELOG.md` (las tres)
- `proyecto_maria/main.py`, `proyecto_maria/templates/dashboard_v2.html` y
  `proyecto_maria/static/v2/screens/clientes.js` (DESPACHO-1a)

## 1. La premisa: confirmada

Corrí `org1_postgres.py` contra un Postgres 16 local con el código de
`ea64a9c`. El resultado fue `fallas: 15`. Cada 500 trae en el log
`TypeError: can't compare offset-naive and offset-aware datetimes` (15
veces). Es tu sospecha: asyncpg devuelve `expires_at` con zona, y se compara
con `datetime.utcnow()`, que no tiene zona. Validar, registrarse, una
vencida y una usada daban 500 en Postgres. Invitar no daba 500, porque no
compara fechas.

## 2. Qué cambió, por punto

Todo está en `proyecto_maria/main.py`.

1. **Sin 500 en las dos bases.** El registro y `validate_invitation`
   comparan `_utc(expires_at) < datetime.now(timezone.utc)`. `_utc` ya
   existía y toma una fecha sin zona como UTC. Así entran los registros
   viejos de SQLite y los de Postgres, que vienen con zona.
2. **Atada al email.** Al registrarse con `invite_token`, el email del
   registro, ya con `strip().lower()`, tiene que ser el de la invitación. Si
   no, responde 400 «Esta invitación es para otro email. Registrate con el
   email al que te invitaron.». La invitación sigue pendiente y no se crea el
   usuario. Una invitación sin email no deja entrar a nadie. El otro camino
   que pone `organization_id` es `/api/organizations/create`, que es el
   dueño creando su estudio. Sacar un miembro lo vuelve a `None`. No hay
   camino para que una cuenta existente se sume.
3. **Tope del plan.** El tope sale de
   `billing_service.get_plan(org.plan or "premium")["users"]`. Un helper
   nuevo, `_emails_de_miembros`, cuenta los usuarios del estudio, dueño
   incluido.
   - Al invitar: responde 400 «El estudio ya ocupa los {tope} usuarios de
     su plan, contando las invitaciones pendientes.» si miembros más
     pendientes sin vencer llegan al tope.
   - Al registrarse: responde 400 «El estudio ya tiene los {tope} usuarios
     de su plan.» si los miembros ya llegaron. Hace rollback y la invitación
     queda pendiente.
4. **Un solo uso.** Pasos del registro:
   - Gasta la invitación con
     `UPDATE invitations SET status='accepted' WHERE id=… AND status='pending'`.
   - Comprueba `rowcount == 1`; si no, hace rollback y responde 400 «Esta
     invitación ya fue usada».
   - Recién después cuenta el tope.
   - Hace un solo commit con el usuario.

   El estudio se lee con `FOR UPDATE` al invitar y al registrarse.

## 3. Qué deja una carrera

| Carrera | Antes (`ea64a9c`) | Ahora |
|---|---|---|
| Dos registros con la misma invitación, SQLite | `[(200, ''), (500, 'No pudimos procesar tu solicitud…')]` | `[200, 400 «ya fue usada»]`, un usuario, invitación `accepted` |
| Lo mismo, Postgres | dos 500 (el `TypeError`) | `[(200, ''), (400, 'Esta invitación ya fue usada')]` |
| Dos registros con invitaciones distintas por el último lugar, SQLite | `[(200, ''), (200, '')]`: entran los dos | `[200, 400 «los 2 usuarios»]`, miembros 2, `['accepted', 'pending']` |
| Lo mismo, Postgres | dos 500 | `[(200, ''), (400, 'El estudio ya tiene los 2 usuarios de su plan.')], miembros 2, ['accepted', 'pending']` |
| Dos invitaciones enviadas a la vez por el último lugar, Postgres | `[(200, ''), (200, '')], pendientes 2` | `[(200, ''), (400, 'El estudio ya ocupa los 2 usuarios de su plan, contando las invitaciones pendientes.')], pendientes 1` |
| Lo mismo, SQLite | — | **No está protegido** (riesgo abajo) |

Cómo se serializa cada base:
- **SQLite:** el primer `UPDATE` del registro toma el candado de escritura
  de la base. Por eso el tope se cuenta después de gastar la invitación: el
  otro registro espera y cuenta con el primero ya adentro.
- **Postgres:** el `FOR UPDATE` sobre el estudio serializa los registros y
  las invitaciones del mismo estudio.

Las carreras son reales, no secuenciales. En SQLite, dos hilos esperan
juntos en una barrera después del hash de la clave. En Postgres, cada
invitación espera en su commit, ya pasado el control del tope. Espera a que
la otra también llegue al commit o quede frenada en el candado, mirado en
`pg_stat_activity`. No hay esperas fijas: el plazo de 20 s sólo corre si no
pasa ninguna de las dos.

## Supuestos reversibles

- **Las pendientes cuentan por email distinto.** Una pendiente de alguien
  que ya es miembro no cuenta. Reinvitar a un email pendiente no ocupa otro
  lugar y responde 200, como hoy.
- **El `FOR UPDATE` sobre el estudio**, al invitar y al registrarse. Es una
  fila por estudio y por pedido, no un candado global.
- **Los tres textos de error nuevos** (arriba).
- **Una invitación «expired» con fecha futura** responde «ya fue usada»,
  porque no está pendiente. Hoy sólo `validate_invitation` marca «expired»,
  y lo hace con la fecha vencida, así que no debería existir.

## D26 y D27: contestadas

- **D26 (a) por ahora.** No hay forma de cancelar una invitación pendiente.
  Se lo proponés a Emi. No la empiezo sin tu aviso.
- **D27 (b): es ORG-1b**, abajo.

## ORG-1b: el registro con invitación trae el email invitado

En `landing.html`, cuando `/api/invitations/{token}` responde válida y trae
email:
- El email del registro se completa con ese email.
- Queda `readOnly`, no `disabled`, así viaja en el envío.
- Debajo aparece «Es el email al que te invitaron.».

Sin `invite`, con un token que no existe, con uno ya usado o con una
respuesta válida sin email, el campo queda como antes: vacío y editable. El
servidor no cambia, y su 400 sigue siendo la guarda.

**La prueba** es `scripts/testing/pantalla_org1b.js`. Usa Playwright, la API
local de verdad y datos inventados. Los casos van en este orden:

1. Sin `invite`, y con un token que no existe: el campo queda vacío y
   editable, y la línea no se ve. El registro se abre con el botón del
   inicio, como lo haría una persona.
2. Respuesta válida sin email: igual que el caso 1. Es el único caso con la
   respuesta simulada (`page.route`), porque la API no deja invitar sin
   email.
3. Invitación válida con el email cambiado a mano en el DOM (se le sacan
   `readOnly` y `disabled`): da 400, y el error dice «otro email».
4. Invitación válida:
   - el email viene completo, es de sólo lectura y no `disabled`;
   - la línea se ve;
   - escribir encima no lo cambia;
   - el registro da 200, manda el email y el token, y la invitada queda en
     el estudio.
5. El mismo token ya usado: igual que el caso 1.

**Rojo antes del producto** (contra `373ef55`): `FALLA: con invitación
válida el email no viene completo: {"value":"","readOnly":false,"disabled":false}`.

**Dos sabotajes no daban su rojo en la primera vuelta**, y los arreglé en la
prueba (`5d42909`):
- **«La línea se ve siempre»:** sin invitación válida, el registro está
  cerrado, así que «no se ve» era cierto para cualquier cosa. Ahora la
  prueba abre el registro antes de mirar.
- **«Además disabled»:** caía antes, en el caso del DOM, con un 422. Ahora
  ese caso saca también `disabled`, como haría quien edita el DOM.

| Sabotaje (`sabotajes/org1b.sh`) | Rojo |
|---|---|
| no se completa el email | «con invitación válida el email no viene completo» |
| el email completo queda editable | «con invitación válida el email no es de sólo lectura» |
| además `disabled` (no viaja en el envío) | «con invitación válida el email está disabled» |
| la línea del email invitado no aparece | «con invitación válida no se ve la línea del email invitado» |
| la línea se ve siempre | «sin invite: se ve la línea del email invitado» |
| se bloquea aunque la invitación no traiga email | «válida sin email: el email no queda vacío y editable» |
| el servidor deja de exigir el email invitado | «con el email cambiado en el DOM el registro dio 200, no 400» |

**Supuesto reversible:** el texto «Es el email al que te invitaron.».

La captura a 390 px se ve bien. El campo de sólo lectura se ve igual que uno
editable; lo explica la línea de abajo. No le cambié el estilo, porque no lo
pediste.

## DESPACHO-1a: el catálogo del cliente en Excel

En la pestaña Catálogo del cliente, arriba de «Productos aprendidos», hay un
botón «Descargar en Excel». Baja `GET /api/clientes/{id}/catalogo/productos.xlsx`:
- un renglón por producto de `ClientProductHistory` de ese cliente y ese
  dueño, en el orden de la pantalla (el último usado primero);
- columnas: Posición, Descripción, Origen, Valor unitario promedio,
  Cantidad promedio, Peso unitario promedio, Veces usado, Última vez;
- un cliente ajeno o que no existe da el mismo 404 que
  `/catalogo/productos` (`_get_owned_client`); sin sesión, 401;
- todo texto se escribe como texto. El que empieza con `=`, `+`, `-` o
  `@` además lleva el apóstrofo invisible (`quotePrefix`), así sigue
  siendo texto si alguien edita la celda;
- la posición va como texto y con formato de texto (`@`), tal como está
  guardada: `01012100`, `0402100Z`, `0101.21.00`.

Toqué `proyecto_maria/main.py` (el endpoint y `_catalogo_xlsx`),
`proyecto_maria/templates/dashboard_v2.html` (el botón),
`proyecto_maria/static/v2/screens/clientes.js` (la descarga) y
`CHANGELOG.md`.

| Pieza | SHA |
|---|---|
| Casos en rojo antes del producto | `ee82997` |
| **Producto y `CHANGELOG.md`** | **`e438dad`** |
| Prueba en el navegador y sabotajes (14, uno por motivo); ajuste del mensaje del caso de aislamiento | `51890cd` |
| **SHA probado** | **`51890cd`** |

Su diff propio parte del merge de tu rama que trajo la tarea:
`git diff fe1571c..51890cd`.

**Rojo antes del producto:**
- `tests/test_despacho1a.py` contra `fe1571c`: `13 failed, 5 warnings in 0.70s`;
  todos por la ruta que no existía (`{"detail":"Not Found"}`).
- `pantalla_despacho1a.js` contra `fe1571c`:
  `FALLA: 1280 px: no se ve «Descargar en Excel»`, salida 1.

**Los casos** (`tests/test_despacho1a.py`, 13 con los parametrizados):
- el archivo se abre con openpyxl y trae lo guardado, fila por fila y en
  orden;
- la posición como texto, con ceros y letra;
- el catálogo vacío trae sólo los encabezados;
- `=HYPERLINK(...)`, `+1+1`, `-2+3` y `@SUMA(A1)` en la descripción, y
  `=1` en el origen, quedan como texto con `quotePrefix`;
- caracteres de control en la descripción no rompen la descarga;
- el nombre del archivo es ASCII aunque el cliente se llame
  «Ñandú Café — … 🚢»;
- otro dueño recibe el mismo 404 que el catálogo de la pantalla, y en el
  cuerpo no aparece el producto;
- un cliente que no existe da 404;
- no se mezclan productos de otro cliente ni de otro dueño;
- sin sesión da 401.

**En el navegador** (`scripts/testing/pantalla_despacho1a.js`, API local y
datos inventados, 1280 y 390 px): carga dos productos, uno con `=1+1` en
la descripción, abre el catálogo, aprieta el botón, baja el archivo y lo
lee con openpyxl. Compara las descripciones con la pantalla y las
posiciones con la API, y exige que sean texto. Salida:
`OK 1280 px: «catalogo_cliente_inventado_d1a_1280.xlsx» trae ["=1+1 NOTEBOOK INVENTADA","CABALLO INVENTADO"], posiciones ["8471.30.12","0101.21.00"], todo como texto`,
y lo mismo a 390 px.

**Sabotajes** (`scripts/testing/sabotajes/despacho1a.sh 51890cd`): salida
0, `sabotajes sin rojo: 0`. Sin sabotaje, las pruebas y la pantalla dan
verde.

| Sabotaje | Rojo (copiado de la salida) |
|---|---|
| no se mira de quién es el cliente | `test_otro_dueno_recibe_el_mismo_404_que_en_el_catalogo`, «assert 200 == 404» |
| la consulta no filtra por dueño | `test_no_se_mezclan_…`, «trae productos de otro dueño» |
| la consulta no filtra por cliente | `test_no_se_mezclan_…`, «trae productos de otro cliente» |
| se puede bajar sin sesión | `test_sin_sesion_da_401`, «assert 404 == 401» |
| «=» queda como fórmula | `test_una_descripcion_con_formula_queda_como_texto[=HYPERLINK…]`, «assert 'f' == 's'» |
| sin el apóstrofo invisible | `…[+1+1]` y `…[@SUMA(A1)]`, «quotePrefix» |
| la posición sólo de dígitos sale como número | `test_la_posicion_sale_como_texto_con_ceros_y_letra`, «1012100» |
| la posición sin formato de texto | `test_la_posicion_…`, «number_format» |
| el orden no es el de la pantalla | `test_el_archivo_se_abre_y_trae_lo_guardado`, «TELEFONO INVENTADO» |
| cantidad y peso cruzados | `test_el_archivo_…`, «450.25» |
| el catálogo vacío sale sin encabezados | `test_un_catalogo_vacio_trae_solo_los_encabezados` |
| no se limpian los caracteres de control | `test_una_descripcion_con_caracteres_de_control_…`, «IllegalCharacterError» |
| el nombre del archivo va como viene | `test_el_nombre_del_archivo_es_ascii`, «UnicodeEncodeError» |
| el botón no está conectado | `FALLA: 1280 px: el botón no bajó nada` |

En la primera vuelta, el sabotaje «no filtra por cliente» dio rojo, pero
el mensaje de pytest cambiaba según las pruebas de antes en la misma base.
Le puse al caso un mensaje propio para cada fuga (`51890cd`). El rojo es
el mismo, ahora se lee.

**Puertas de DESPACHO-1a, sobre `51890cd`:**

| Puerta | Resultado |
|---|---|
| Las 12 de `tests/` que tocan clientes, catálogo o DESPACHO-1a | `249 passed, 3 warnings in 71.12s (0:01:11)` |
| `compileall -q proyecto_maria` | `compile-ok` (rc 0) |
| `node --check …/clientes.js` | `js-ok` |
| `pantalla_despacho1a.js` | `OK 1280 px …` y `OK 390 px …`, salida 0 |
| `sabotajes/despacho1a.sh 51890cd` | `sabotajes sin rojo: 0`, salida 0 |

**Sin correr todavía**, para el `/entregar` del 28/10 a las 18:00 UTC: la
suite completa sobre el SHA final, `smoke_friccion.sh`,
`ataque_aislamiento.sh` (no cubre esta ruta nueva: el aislamiento de esta
ruta lo cubren los casos y tres sabotajes), subagentes, `/code-review high`
y `/security-review`.

**Supuestos reversibles:**
- Se limpian los caracteres de control que Excel no acepta. Sin eso, la
  descarga da 500 con una descripción así.
- El nombre del archivo, en ASCII: `catalogo_<nombre>.xlsx`. El servidor
  y la pantalla lo arman cada uno, con el mismo criterio.
- El apóstrofo invisible (`quotePrefix`) en lo que empieza con
  `=`, `+`, `-` o `@`.
- La fecha como fecha de Excel, `dd/mm/yyyy`, y el día en UTC, igual que
  la pantalla (`slice(0, 10)`).
- El texto del botón, «Descargar en Excel», y el toast «Descarga iniciada.».

**Riesgos de DESPACHO-1a:**
- **Empates en «última vez».** En Postgres, los productos aprendidos en un
  mismo pedido llevan el mismo `now()`. El orden entre ellos no está fijado,
  ni en la pantalla ni en el Excel, y puede salir distinto entre una y
  otro. No lo arreglé: cambiaría también la consulta de la pantalla.
- **Un texto de más de 32767 caracteres** se escribe entero; Excel lo corta
  al abrirlo o se queja. No lo vi en el catálogo; no lo traté.
- **Un promedio NaN** se escribiría como NaN. El aprendizaje no debería
  dejarlo; no lo traté.
- **A 390 px el tablero ya se corre 133 px de costado**, con o sin el botón
  (lo medí también sacando el botón). El botón se ve entero. No es de esta
  pieza y no lo toqué.

## Puertas de ORG-1 y ORG-1b

| Puerta | Resultado |
|---|---|
| `tests/test_org1.py` sobre `ddfc798` | `46 passed, 3 warnings in 31.56s` |
| Los mismos casos contra `ea64a9c` | `36 failed, 10 passed, 39 warnings in 45.26s` |
| `org1_postgres.py`, Postgres 16 local, sobre `ddfc798` | `fallas: 0`, 3 de 3 corridas |
| Lo mismo contra `ea64a9c` | `fallas: 15` |
| `sabotaje_org1.sh 18f7f25` | `OK: los 9 sabotajes dan rojo por la razón esperada`, salida 0 |
| Suite completa, worktree limpio en `18f7f25` | `1 failed, 3323 passed, 302 skipped, 2 xfailed, 94 warnings in 505.43s (0:08:25)` |
| `compileall -q proyecto_maria` | rc 0 |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| `ataque_aislamiento.sh` | `Bloqueado: 22 · Fugas: 0`, «✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.» |
| ORG-1b: `sabotajes/org1b.sh 5d42909` | `sabotajes sin rojo: 0`, salida 0; los 7 dan su rojo, y sin sabotaje la prueba da verde |
| ORG-1b: `pantalla_org1b.js` contra `373ef55` | `FALLA: con invitación válida el email no viene completo`, salida 1 |
| ORG-1b: `test_pa1_textos`, `test_regression_phase0`, `test_static_endpoints` (las que leen la landing) y `test_org1`, sobre `5d42909` | `93 passed, 1 skipped, 3 warnings in 32.68s` |

Los casos corren cada uno dos veces, `sqlite_sin_zona` y
`postgres_con_zona`. El segundo inyecta un `expires_at` con zona al cargar
la fila, que es lo que hace asyncpg.

**El único rojo de la suite** es
`test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal`.
Es el de tiempo ya informado en SUFIJOS-1, 1c y 1d: «la subida normal dio
400 a los 30.0 s: … tardó demasiado». ORG-1 no toca la lectura de Excel.

**Sabotajes** (`sabotaje_org1.sh`). Cada uno vuelve a lo de antes o rompe
una guarda:

| Sabotaje | Qué hace | Rojos |
|---|---|---|
| `fecha_sin_zona` | vuelve a comparar con `datetime.utcnow()` | 14 failed |
| `sin_email` | cualquiera con el enlace entra | 10 failed |
| `invitar_sin_tope` | invitar sin tope | 13 failed |
| `tope_fijo` | tope 3 escrito a mano | 10 failed |
| `vencida_ocupa` | guarda: una pendiente vencida ocupa lugar | 2 failed |
| `reinvitar_ocupa` | guarda: reinvitar ocupa otro lugar | 1 failed |
| `registro_sin_tope` | registrarse sin tope | 3 failed |
| `gasto_sin_condicion` | gasta sin mirar si seguía pendiente | 2 failed |
| `contar_antes` | cuenta el tope antes de gastar (la carrera de SQLite) | 1 failed |

Dos sabotajes más se aplicaron a mano en Postgres, porque el candado sólo se
ve ahí:
- Sin `FOR UPDATE` al invitar: `FALLA | dos invitaciones a la vez por el
  último lugar: sale una ([(200, ''), (200, '')], pendientes 2)`, 3 de 3.
- Sin `FOR UPDATE` al registrarse: `FALLA | dos invitaciones por el último
  lugar: entra una ([(200, ''), (200, '')], miembros 3, ['accepted',
  'accepted'])`, 3 de 3.

**Lo que no corrí:**
- Subagentes adversariales, `/code-review` ni `/security-review`. No tengo
  cuota hasta el 28/10 a las 18:00 UTC. La autorrevisión del diff completo
  contra `ea64a9c` es sólo mía, sin independencia. Por eso todavía no
  entrego.
- ORG-1: la pantalla en un navegador. ORG-1 no toca pantallas.
- ORG-1b: la suite completa ni el smoke. ORG-1b cambia sólo la plantilla
  `landing.html`; corrí las pruebas que la leen, arriba.

## Comandos

Este muestra sólo lo de ORG-1:

```bash
git diff ea64a9c..ddfc798
```

Este tiene que dar `46 passed`:

```bash
python -m pytest -q --no-cov -p no:randomly tests/test_org1.py
```

Este tiene que dar «OK: los 9 sabotajes dan rojo por la razón esperada» y
salida 0:

```bash
scripts/testing/sabotaje_org1.sh 18f7f25 <venv>
```

Este tiene que dar `fallas: 0`. Usá un Postgres local y descartable; el
script rechaza cualquier host que no sea local:

```bash
python scripts/testing/org1_postgres.py postgresql://<usuario>@127.0.0.1:<puerto>/<base>
```

Este muestra sólo lo de ORG-1b:

```bash
git diff 373ef55..5d42909
```

Este tiene que terminar con `OK ORG-1b`. Va contra una API local
levantada con datos inventados:

```bash
BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_org1b.js
```

Este tiene que dar `sabotajes sin rojo: 0` y salida 0. Necesita `node` y
el Chromium de Playwright:

```bash
PY=<venv>/bin/python scripts/testing/sabotajes/org1b.sh 5d42909
```

Este muestra sólo lo de DESPACHO-1a:

```bash
git diff fe1571c..51890cd
```

Este tiene que dar `13 passed`:

```bash
python -m pytest -q --no-cov -p no:randomly tests/test_despacho1a.py
```

Este tiene que terminar con `OK 1280 px …` y `OK 390 px …`, y salida 0. Va
contra una API local levantada con datos inventados:

```bash
BASE_URL=http://127.0.0.1:<puerto> PY=<venv>/bin/python node scripts/testing/pantalla_despacho1a.js
```

Este tiene que dar `sabotajes sin rojo: 0` y salida 0. Arma su propio
worktree, su SQLite y su API en el puerto 8853:

```bash
PY=<venv>/bin/python scripts/testing/sabotajes/despacho1a.sh 51890cd
```

## Riesgos de ORG-1 y ORG-1b

- **ORG-1b: una invitación a un email que la pantalla no acepta queda sin
  salida.** Arreglado en `6b9762e` (ver la entrega de arriba): invitar
  valida con el mismo criterio que el registro.

- **La carrera de dos invitaciones a la vez no está protegida en SQLite.**
  `FOR UPDATE` no hace nada ahí, y la invitación no escribe antes de
  contar. Puede quedar un lugar de más pendiente. Al registrarse, el tope se
  vuelve a controlar, así que no entra un miembro de más. Producción es
  Postgres, y ahí está cubierta.
- **En Postgres puede faltar el índice único de `users.email`.** El modelo
  lo declara, pero no comprobé la base de producción, y no la toco. Ahora la
  carrera del mismo email la frena la invitación, no el índice.
- **El registro con un email de prueba reemplazable** confirma ese borrado
  antes de los controles de la invitación. Es de antes y ORG-1 no lo cambia.
- **El 400 «es para otro email»** dice que el email escrito no es el
  invitado. No dice cuál es. Hace falta el token para preguntar.

Última vuelta: Wed Oct 28 16:36:08 UTC 2026

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM, rutina horaria minuto 35. Desde las 16:20 UTC entrego las doce piezas en orden por orden de Emi (16:20:19 «Háganlo ahora que hay q gastar cupo», verificada en la sesión de la PM; mi canal todavía dice 18:00). ORG-1+ORG-1b+DESPACHO-1a ENTREGADA en 3aaa3c4 (pieza 4ce6d22 + arreglo 6b9762e email de invitación con la regex del registro y largo 100, pruebas 3aaa3c4: rojo 6 failed, verde 66 passed; suite sobre 3aaa3c4 no corrida); D40 abierta (invitaciones que ocupan lugar sin poder usarse, recomiendo (1)). Hallazgos de todas las piezas en el scratchpad adv/HALLAZGOS.md. DESTINO-1 ENTREGADA en f887b4a (16:41 UTC). SUFIJOS-2 ENTREGADA en bd76f9f (pieza 4ca6829 + arreglo: producto 91f0fb6, pruebas 15566a0, sabotajes 4821fff y bd76f9f; un número que cambiaría de valor en un sufijo no se genera; rojo 19 failed; sabotajes 17/17; suite 4821fff 4005 passed, 0 failed); D29 contestada (a). SEGURO-1 ENTREGADA en 5dfaf47 (pieza 371cde2 + arreglo: producto bf6e1d7, pruebas 5dfaf47; sin respuesta de los avisos no se ofrece «Dejar el seguro»; sabotajes 11/11; suite 5dfaf47 4007 passed, 0 failed). ORG-1 + D40 (PARA-DEV-2 17:05): pendiente, después de las piezas, en commits aparte encima de la cadena. SEGURO-1 hecha y subida SIN ENTREGAR: SHA probado 371cde2 (sabotajes seguro1.sh 10/10; suite a08de1f 3777 passed, 0 failed); D30 contestada (a), riesgo «seguro 0 en el TXT si nadie lo completa»; SEGURO-2 no se empieza hasta verla en PARA-DEV-2. DESPACHO-1b hecha y subida SIN ENTREGAR encima de SEGURO-1 y del merge 49f8e29: producto 0591722, pruebas e59e1a8, SHA probado e59e1a8 (50 casos; sabotajes despacho1b.sh 24/24; suite 3827 passed, 336 skipped, 2 xfailed, 0 failed; smoke y aislamiento 0); D31 contestada (a) en 3da0a8b, costos en riesgos. DATOS-1 (D5+D32 (a) borrar cliente borra sus presupuestos compartidos, D2 /health 503, D6 sin dev_detail) hecha y subida SIN ENTREGAR encima de d01f95c: producto 7d09c6f, casos 4416076, Postgres y sabotajes 162d277, arreglo de casos que gastaban el cupo de test_user c996ad4; SHA probado c996ad4 (test_datos1 9 passed; sabotajes datos1.sh 12/12; suite 3836 passed, 336 skipped, 2 xfailed, 0 failed; datos1_postgres.py fallas 0; smoke y aislamiento 0 sobre 162d277); su propio /entregar después del de DESPACHO-1b, con /security-review. Postgres 16 descartable en /tmp/cdi-pg55432, puerto 55432, base datos1a. DISCO-1 (historial de NCM de DATA_DIR a la tabla ncm_historial por dueño; carga única de archivos viejos a .migrado) hecha SIN ENTREGAR encima de c996ad4 y del merge cf84a76 (PM 1f6e0de): producto bd53fc4, casos y sabotajes 0f1161a, Postgres y textos de sabotajes 88b22c8; SHA probado 88b22c8 (test_disco1 11 passed; sabotajes disco1.sh 20/20; suite 3847 passed, 336 skipped, 2 xfailed, 0 failed; disco1_postgres.py fallas 0 y con sabotaje de carrera fallas 1; smoke y aislamiento 0); D33 contestada (a) en a3efc3a, riesgo anotado en DISCO-1; va en su propio /entregar, con subagentes, /code-review high y /security-review. OBSERVABILIDAD-1 (api_logs.owner_username nullable con su índice al arrancar, helper _migrate_add_api_logs_owner_column en main.py; si falla, log y la app sigue) hecha SIN ENTREGAR encima de 88b22c8: producto y CHANGELOG 8b1ce3b, casos, arnés y sabotajes 7ae35ab, merge de la PM 39be45e; SHA probado 39be45e (test_observabilidad1 8 passed; observabilidad1_arranque.py con Postgres 55432 38 OK fallas 0; sabotajes observabilidad1.sh con PG_URL 16/16 sobre 7ae35ab; suite 3855 passed, 336 skipped, 2 xfailed, 0 failed; smoke y aislamiento 0); D34 contestada (a) en 486e655 (sólo la columna; la métrica sigue sin dueño); va en su propio /entregar después del de DISCO-1, con subagentes, /code-review high y /security-review. SESION-1 (S3: revocar_sesiones nunca escribe NULL en active_jti; change-password cierra las otras y conserva la propia; reset cierra todas; /auth/logout y /logout revocan el token sólo si es el vigente; PUT /api/user/profile pide current_password si cambia el email, 400) hecha SIN ENTREGAR encima de 39be45e y del merge f5160d7 (PM 486e655): producto y CHANGELOG 7dfe144, casos, motores, pantalla y sabotajes 014a3e4, arreglo 4c1ae09 (jti_de_la_request en vez de request.state: la suite sobre 014a3e4 dio 1 failed en test_auth_invalid_plan), sabotajes ajustados 895ee73; SHA probado 895ee73 (test_sesion1 17 casos, rojo en base 11 failed; sesion1_motores.py sqlite y pg 26 OK, todo OK, rojo en base FALLAS 12; sabotajes sesion1.sh 19/19; pantalla 3/3; suite 3872 passed, 336 skipped, 2 xfailed, 0 failed; smoke y aislamiento 0); va en su propio /entregar después del de OBSERVABILIDAD-1, con subagentes, /code-review high y /security-review. ABUSO-1 (D35 (1) en las cinco, de f600ed4: IP desde XFF con TRUSTED_PROXY_HOPS, contadores de login y recuperación en la tabla limites_auth, registro 5/hora y 20/día, recuperar 5/15 min por IP y 3/hora por email, eventos 120/min, anónimos con lista explícita) hecha y subida SIN ENTREGAR encima de 895ee73: S5 584b8d1, 25158c6, 8c37653; IP ca7eee9; tabla 790dd8e; producto a3abd92; pruebas a2fc7f0; arreglo de concurrencia en reset 777ebc8 y sus pruebas 74ccb76; IP larga en la clave 44b43db y sus pruebas 43916a7; SHA probado 43916a7 (test_abuso1 58 passed, rojo en base 25 failed; abuso1_motores.py y sesion1_motores.py sqlite y pg todo OK; sabotajes abuso1.sh 27 ROJO, sin rojo 0; suite 3930 passed, 336 skipped, 2 xfailed, 0 failed); ver solo la pieza con git diff c702655..43916a7 -- . ':!docs'. D36 contestada (2) en eaee1b1: no se toca la comparación del email; en riesgos los dos lugares que comparan exacto y el PUT que deja crear pares. D37 contestada (2) en 20fb535: ABUSO-1 no cambia, el close cancelado de get_async_session va a riesgos, la advertencia queda a la vista, no se tocan middlewares; medirlo es pieza nueva que la PM propone a Emi. EMAIL-1 (D36 (1), Emi sí 12:15 UTC: _cuenta_por_email exacto primero y después lower; recuperar contraseña, recuperar usuario y login con @ lo usan; perfil, registro, alta de estudio e invitación comparan lower; con par sin exacta no elige ninguna) hecha SIN ENTREGAR encima de e22a5cf: producto y CHANGELOG 56ab458, pruebas 855e8ac y c2be841, caso de ABUSO-1 que sigue a EMAIL-1 2b93071 (la suite sobre c2be841 dio 1 failed en test_s6_recuperar_usuario_corta_en_silencio_por_email); SHA probado 2b93071 (test_email1 24 passed, rojo en base 12 failed; email1_motores.py sqlite y pg todo OK, rojo FALLAS 11; sabotajes email1.sh 13/13 y abuso1.sh 27/27 sobre 2b93071; suite 3954 passed, 336 skipped, 2 xfailed, 0 failed); D38 contestada (1) en 669e120; (3) espera el conteo de Emi; en riesgos quien tiene un par sin exacta no recupera hasta la (3). CONEXIONES-1 (D37 (1)) medida SIN ENTREGAR, sin cambio de producto: medidor, sonda y sabotajes 30c0e97; con el CMD del Dockerfile, uvloop y Postgres 16, 3544 cierres y 0 cancelados, el pool vuelve a 0 tomadas y 20 idle en todas las fases; sabotajes conexiones1.sh 3 OK FALLAS 0; D39 contestada (1) por ahora en 669e120: 50 de 50 con 40 logins malos va a riesgos; la medición chica es pieza nueva, no se empieza sin el sí de Emi. La próxima D es la D41. Entregas preparadas (sección arriba del informe): cada pieza con su SHA, su base para el diff y su suite sobre ese SHA en verde; la base de ORG-1 para el diff es fb11735 (ea64a9c arrastra EXCEL-3f de la Dev técnica); suite de SEGURO-1 sobre 371cde2: 3777 passed, 0 failed. Pendiente: el 28/10 después de las 18:00 UTC, en orden, /entregar de ORG-1+ORG-1b+DESPACHO-1a sobre 4ce6d22 (subagentes hasta alto, /code-review high, /security-review, Postgres 55432 para org1_postgres.py), DESTINO-1, SUFIJOS-2, SEGURO-1 (con /security-review), DESPACHO-1b, DATOS-1, DISCO-1, OBSERVABILIDAD-1, SESION-1, ABUSO-1 (revisión fuerte, /security-review, smoke y ataque_aislamiento), EMAIL-1 sobre 2b93071 (base e22a5cf, revisión fuerte, /security-review) y CONEXIONES-1 sobre 30c0e97 (base 2b93071, PG 55432); timbre «Dev MARIA: entregué <PIEZA> en <SHA>». PESO-NETO-1 y PRORRATEO-1 esperan al despachante. Nunca main, sin push --force, sin datos reales del 24/10 ni despachos del 28/10, nada se publica sin el «dale» de Emi para el SHA, sin Gemini en pruebas, subagentes hasta esfuerzo alto, sin advisor.
