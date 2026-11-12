# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CONEXIONES-1 G: tres columnas. En «hoy» se pierde la recarga entera; (b) no pierde más que hoy

| SHA | Qué |
|---|---|
| `7ed91bac` | `test:` medidor de cuerpos grandes (`scripts/testing/conexiones1_cuerpo.py`) |
| `2b04a543` | `test:` medidor de créditos extra vencidos con recarga (`scripts/testing/conexiones1_creditos.py`) |
| `9a032f12` | `test:` el medidor de créditos no se cuelga si la carrera no se arma (sale 4) |
| este commit | `docs:` este informe |

Producto +0/−0: no commiteé producto. Columnas: **hoy** = mi cabeza sin diff
(producto igual a `21df2a39`: `git diff 21df2a39 HEAD -- proyecto_maria`
vacío); **revisado** = diff de F, (a); **alternativa** = diff de D186 (b).
Los dos diffs están abajo, enteros.

### Resultado

1. **Cuerpos grandes:** en hoy y en (b) la impaga recibe el 402 sin que se lea
   el cuerpo (0 retenidas, memoria +1 MB como mucho). Con el revisado el 402
   espera el cuerpo entero: 4×500 MB suben el pico a **4159.7 MB** y la otra
   cuenta espera **2041 ms** al soltar. Nadie recibió un error (`no_200` 0 en
   todas).
2. **Créditos vencidos + recarga a la vez:** en las **tres columnas** se
   pierde la recarga entera, en usuario y en organización: «quedan 0 de 10
   pagos (perdidos 10)». (b) no pierde más que hoy: pasa por tu regla. Que
   hoy pierda es un hallazgo de plata aparte, para Emi (D188).
3. Con un arreglo de prueba de una línea el mismo medidor da verde (rc=0):
   el medidor discrimina. Un arreglo más ingenuo da deadlock 500 en la
   organización (D189).

## Decisiones

- **D188 (para Emi, plata). En producción hoy, una recarga que entra mientras
  una cuenta con créditos extra vencidos crea una operación se pierde entera.**
  La cuenta pagó 10 y quedan 0, con el vencimiento en NULL. Medido sobre HEAD
  en Postgres 16 con MP simulado; la ventana real es lo que tarda el alta
  entre leer la cuenta y confirmar (no medida en producción).
  - (a) Arreglarlo dentro de la pieza de producto de CONEXIONES-1, con el caso
    de este medidor como puerta (recomendada): el arreglo es chico y toca la
    misma función que F.
  - (b) Pieza aparte de plata, después de CONEXIONES-1.
  - (c) Aceptar el riesgo.
  - Aparte, para Emi: ¿hubo recargas reclamadas como no acreditadas? Yo no
    tengo forma de verlo.
- **D189. Cómo se arregla.** Candidato probado: tomar la fila de la cuenta
  antes de vencerla, en `require_active_billing`
  (`await db.refresh(entidad, with_for_update=True)`, diff de 1 línea abajo).
  Con él los cuatro casos dan OK 10 de 10 y vencimiento futuro, rc=0, sin
  deadlocks.
  - (a) Ese, dentro de la pieza de producto, con revisión fuerte (recomendada).
  - (b) Otro arreglo que proponga la PM; el medidor lo juzga igual.
  - Riesgo medido: `refresh` **sin** `with_for_update` (después de
    `can_create_operation`) arregla el usuario pero en la organización da
    `DeadlockDetectedError` y el alta devuelve 500. Un arreglo así no puede
    entrar.
  - No sé todavía si los demás caminos que usan `require_active_billing` o
    `can_create_operation` (análisis de PDF, otros planes) tienen el mismo
    hueco: el medidor cubre sólo `/api/operations/manual` y plan premium. Va
    en el plan de la pieza.

Siguen abiertas de antes: D182, D183 y D184 (Emi).

## 1. Cuerpos grandes de una impaga en `/api/operations/manual`

Medidor `conexiones1_cuerpo.py`, gunicorn con 1 worker uvicorn, loopback. Una
«impaga» es una cuenta sin pago; la «otra cuenta» está al día y pide su lista
en paralelo. hoy: árbol `21df2a39` (rondas de tabla) y `7ed91bac` (4×500),
mismo producto que mi cabeza.

### Cuánto tarda el 402 (s, desde que la impaga empieza a mandar)

| Ronda | hoy | revisado | alternativa |
|---|---|---|---|
| 1×1 MB | 0.009 | 0.008 | 0.036 |
| 1×10 MB | 0.008 | 0.01 | 0.011 |
| 1×100 MB | 0.007 | 0.076 | 0.01 |
| 1×500 MB | 0.011 | 0.338 | 0.01 |
| 8×100 MB (1ª) | 0.129–0.155 | 0.621–0.658 | 0.109–0.153 |
| 8×100 MB (2ª) | 0.027–0.038 | 0.516–0.521 | 0.028–0.043 |
| 8×100 MB (3ª) | 0.028–0.044 | 0.518–0.524 | 0.033–0.037 |
| 4×500 MB | 0.087–0.097 | 2.037–2.09 | 0.119–0.131 |

En hoy y en (b) el 402 llega con 1 a 4 MB mandados (lo que el socket aceptó);
con el revisado, con el cuerpo entero (500.0 MB en 4×500). Con el revisado el
atacante decide cuánto dura: si retiene los últimos bytes, el 402 no llega
(uvicorn no tiene plazo para el cuerpo; leído, no medido).

### Cuánta memoria sube el proceso (RSS del worker, MB: antes → retenido · pico · después)

| Ronda | hoy | revisado | alternativa |
|---|---|---|---|
| 1×1 | 158.4 → 158.5 · 158.5 · 158.5 | 158.2 → 159.6 · 160.2 · 160.2 | 157.9 → 158.3 · 158.3 · 158.3 |
| 1×10 | 158.5 → 158.6 · 158.6 · 158.6 | 160.2 → 168.8 · 178.5 · 159.1 | 158.3 → 158.3 · 158.3 · 158.3 |
| 1×100 | 158.6 → 158.6 · 158.6 · 158.6 | 159.1 → 258.8 · 358.5 · 158.7 | 158.3 → 158.3 · 158.4 · 158.4 |
| 1×500 | 158.6 → 158.8 · 158.9 · 158.9 | 158.7 → 659.0 · 1158.7 · 158.6 | 158.4 → 158.4 · 158.4 · 158.4 |
| 8×100 (1ª) | 158.9 → 160.6 · 160.6 · 160.6 | 158.6 → 1060.1 · 1859.8 · 183.1 | 158.4 → 160.0 · 160.0 · 160.0 |
| 8×100 (2ª) | 160.6 → 160.8 · 160.8 · 160.8 | 183.1 → 1060.7 · 1860.4 · 182.8 | 160.0 → 160.2 · 160.2 · 160.2 |
| 8×100 (3ª) | 160.8 → 160.8 · 160.8 · 160.8 | 182.8 → 1160.8 · 1960.6 · 173.8 | 160.2 → 160.3 · 160.3 · 160.3 |
| 4×500 | 158.3 → 159.4 · 159.4 · 159.4 | 158.2 → 2160.1 · 4159.7 · 160.3 | 158.3 → 159.5 · 159.5 · 159.5 |

Retenidas (impagas que el servidor dejó esperando el cuerpo): hoy 0, revisado
igual al número de impagas, alternativa 0. Con el revisado el pico es unas 2
veces los bytes en vuelo y se libera después del 402, con un remanente de
hasta ~25 MB.

### Si otra cuenta al día lo nota (ms; `no_200` fue 0 en todas: nunca un error)

| Ronda | hoy | revisado | alternativa |
|---|---|---|---|
| base sin carga (medianas) | 4.4–6.6 | 4.6–7.3 | 4.8–6.4 |
| subiendo, máximo en 8×100 | 85.0 · 19.3 · 22.3 | 70.1 · 98.0 · 34.6 | 109.4 · 22.7 · 19.7 |
| subiendo, máximo en 4×500 | 82.8 | 99.7 | 115.1 |
| retenido | 5.3–12.7 | 5.3–8.2 | 5.2–11.1 |
| soltado, 1×100 | 11.6 | 78.1 | sin muestra |
| soltado, 1×500 | 13.1 | 342.0 | 8.4 |
| soltado, 8×100 | 9.1 (1ª) | 639.1 · 543.1 · 538.9 | sin muestra |
| soltado, 4×500 | sin muestra | 2041.0 (n 2) | sin muestra |

- Con el revisado la otra cuenta **espera** al soltar: hasta 639 ms con 8×100
  y 2041 ms con 4×500, porque el worker es uno y el event loop junta y une los
  cuerpos. En hoy y en (b) no.
- «Subiendo» no discrimina: las tres columnas tienen máximos de 70 a 115 ms
  (carga del loopback).
- «soltado» es una sola muestra por ronda (dos en 4×500) y a veces ninguna:
  cuando la ronda termina rápido, el medidor no llega a tomarla.

**Keep-alive en hoy:** una copia del medidor que no corta al 402 y sigue
mandando los 100 MB enteros (`1x100,4x100,8x100`) deja la memoria plana
(RSS 158.4–161.1 MB); el costo es CPU y ancho de banda. No la corrí con el
revisado ni con (b).

## 2. Créditos extra vencidos y una recarga a la vez

Medidor nuevo `conexiones1_creditos.py`, Postgres 16, Mercado Pago simulado.
La recarga entra por el mismo camino que en producción: el aviso firmado de MP
a `/api/payments/webhook` (pago `approved`, `external_reference` `<cuenta>:topup`).
La cuenta tiene 5 créditos extra vencidos ayer, plan premium al día. Por
usuario y por organización corre dos fases:

- **control:** la recarga termina y después se crea la operación;
- **carrera:** el medidor toma la fila de la cuenta (`for update`), pide la
  recarga y espera a verla esperando en `pg_stat_activity`; pide el alta y
  espera a ver un segundo pedido esperando (cierre transitivo de
  `pg_blocking_pids`); recién ahí suelta. Ninguna espera fija.

Cada fase exige 200 en la recarga, el pago `aplicado` en
`mp_pagos_aplicados`, 200 en el alta y la operación guardada. Después tienen
que quedar 10 créditos (`TOPUP_OPS`) con vencimiento futuro. Sale 1 si se
pierde uno, 2 si la medición no vale (también si quedan más de 10), 4 si la
carrera no se arma.

| | hoy | revisado | alternativa |
|---|---|---|---|
| usuario, control | 10 de 10 · vence en el futuro | 10 de 10 · vence en el futuro | 10 de 10 · vence en el futuro |
| usuario, carrera | **0 de 10 · perdidos 10** · vencimiento no futuro | **0 de 10 · perdidos 10** | **0 de 10 · perdidos 10** |
| organización, control | 10 de 10 · vence en el futuro | 10 de 10 | 10 de 10 |
| organización, carrera | **0 de 10 · perdidos 10** · vencimiento no futuro | **0 de 10 · perdidos 10** | **0 de 10 · perdidos 10** |
| salida | rc=1 | rc=1 | rc=1 |

Las tres columnas dan lo mismo. Salida de hoy (revisado y alternativa son
idénticas salvo la primera línea; la ruta del archivo, recortada):

```
…/proyecto_maria/main.py; db.commit() escrito en require_active_billing: False; _leer_cuerpo: False
OK     | usuario, control: quedan 10 de 10 pagos (perdidos 0), vencimiento futuro sí
PIERDE | usuario, carrera: quedan 0 de 10 pagos (perdidos 10), vencimiento futuro no
        esperaba: SELECT users.username, users.email, users.password, users.name, users.cuit, users.default_
        esperaba: UPDATE users SET extra_ops_remaining=$1::INTEGER, extra_ops_expires_at=$2::TIMESTAMP WITH 
OK     | organización, control: quedan 10 de 10 pagos (perdidos 0), vencimiento futuro sí
PIERDE | organización, carrera: quedan 0 de 10 pagos (perdidos 10), vencimiento futuro no
        esperaba: UPDATE organizations SET extra_ops_remaining=$1::INTEGER, extra_ops_expires_at=$2::TIMESTA
        esperaba: SELECT organizations.id, organizations.name, organizations.owner_username, organizations.p
pierden: 2; no valen: 0; sin carrera: 0
```

Primera línea en las otras dos columnas:

- revisado: `db.commit() escrito en require_active_billing: False; _leer_cuerpo: True`
- alternativa: `db.commit() escrito en require_active_billing: True; _leer_cuerpo: False`

**Por qué se pierde (del código, y coincide con lo que espera en la carrera):**
`can_create_operation` (`billing_service.py:155`) llama a `_expire_extra_ops`
(`:109`), que pone los créditos vencidos en 0 y el vencimiento en NULL **en
memoria**. Al crear la operación, SQLAlchemy manda ese cambio como un
`UPDATE … SET extra_ops_remaining=0, extra_ops_expires_at=NULL` sin mirar lo
que hay en la fila. Si la recarga confirmó sus +10 en el medio, ese UPDATE los
pisa. En la carrera se ve: la recarga espera con su `SELECT … FOR UPDATE` y el
alta con ese UPDATE.

### Rojo y verde del medidor

El rojo pedido es el producto de hoy: pierde sin que yo toque nada. Para ver
que el medidor también puede dar verde, apliqué el arreglo de prueba de D189
(sin commitear) y corrió así:

```
…/proyecto_maria/main.py; db.commit() escrito en require_active_billing: False; _leer_cuerpo: False
OK     | usuario, control: quedan 10 de 10 pagos (perdidos 0), vencimiento futuro sí
OK     | usuario, carrera: quedan 10 de 10 pagos (perdidos 0), vencimiento futuro sí
        esperaba: SELECT users.username, users.email, users.password, users.name, users.cuit, users.default_
        esperaba: SELECT users.username, users.email, users.password, users.name, users.cuit, users.default_
OK     | organización, control: quedan 10 de 10 pagos (perdidos 0), vencimiento futuro sí
OK     | organización, carrera: quedan 10 de 10 pagos (perdidos 0), vencimiento futuro sí
        esperaba: SELECT organizations.id, organizations.name, organizations.owner_username, organizations.p
        esperaba: SELECT organizations.id, organizations.name, organizations.owner_username, organizations.p
pierden: 0; no valen: 0; sin carrera: 0
```

rc=0, y cero `DeadlockDetectedError` en el log.

Con el arreglo ingenuo (`await db.refresh(entidad)` después de
`can_create_operation`, sin bloquear) el usuario da OK, pero la organización no:

```
NO VALE | organización, carrera: Invalida: alta 500 {"detail":"No pudimos procesar tu solicitud. Probá de nuevo en unos segundos. …
ERROR:root:Excepcion no manejada en POST /api/operations/manual: DBAPIError: (sqlalchemy.dialects.postgresql.asyncpg.Error) <class 'asyncpg.exceptions.DeadlockDetectedError'>: deadlock detected
pierden: 0; no valen: 1; sin carrera: 0
```

rc=2: el medidor no lo cuenta como verde.

**Si la carrera no se arma, el medidor no se cuelga.** Con una copia que exige
tres pedidos esperando (imposible), termina sin cuelgue: cada espera corta a los 15 s.

```
NO VALE | usuario, carrera: Invalida: carrera: el alta no llegó a esperar (terminó: False)
NO VALE | organización, carrera: Invalida: carrera: el alta no llegó a esperar (terminó: False)
pierden: 0; no valen: 0; sin carrera: 2
```

rc=4. Antes de `9a032f12` ese caso se colgaba hasta que lo cortaba el `timeout`.

## 3. Los diffs, con `git apply --check` limpio sobre mi cabeza

Los tres dan limpio en un worktree limpio de `9a032f12`. En mi árbol de
trabajo el de F choca sólo porque ahí tengo `tests/test_conexiones1.py` sin
seguimiento (lo crea ese diff y no lo commiteo: D184 es de Emi); con
`--cached` también da limpio.

```
$ git apply --check f.diff && echo f limpio            # worktree de 9a032f12
f limpio
$ git apply --check d186b.diff && echo d186b limpio
d186b limpio
$ git apply --check verde.diff && echo verde limpio
verde limpio
```

Están al final de este informe, en este orden: revisado (F, 365 líneas),
alternativa (D186 b, 79 líneas) y el arreglo de prueba de D189 (11 líneas).

## Declarado y no medido

- Créditos: sólo plan premium y sólo `/api/operations/manual`. No medí el
  análisis de PDF ni otros planes, ni la ventana real en Railway.
- Créditos: no medí qué pasa si la recarga llega **después** del UPDATE ciego
  del alta (ahí la recarga parte de 0 y suma 10, que es lo correcto).
- Cuerpos: el proxy de Railway, el límite de memoria del contenedor y el ancho
  de banda real. Más de 4×500 o más de 8 a la vez.
- Cuerpos: keep-alive sólo en hoy.
- La suite completa: G no toca producto ni `tests/`.

## Hallazgos de la autorrevisión

| Revisor | Modelo y esfuerzo | Hallazgo | Qué hice |
|---|---|---|---|
| Adversario | Sonnet alto | (Alta) Si la carrera no se arma, el medidor se cuelga | sale con 4, cada espera corta a los 15 s; corrido con una copia imposible (arriba) |
| Adversario | Sonnet alto | (Alta) Un arreglo con `refresh` puede dar deadlock en la organización | confirmado y medido; va como riesgo en D189 |
| Adversario | Sonnet alto | (Media) «quedan 10» no alcanza: el vencimiento puede quedar en el pasado o NULL | el medidor exige vencimiento futuro |
| Adversario | Sonnet alto | (Media) El segundo pedido esperando podía no ser el alta | cierre transitivo de `pg_blocking_pids` y las consultas que esperan, impresas |
| Adversario | Sonnet alto | (Media) Sólo premium y sólo la ruta manual | declarado arriba |
| Adversario | Sonnet alto | (Baja) Una conexión por llamada sin cerrar en `sql` | `closing` |
| `/code-review` | high | Una excepción de la fase salía con 1, como si perdiera | cuenta como «no vale» (2) |
| `/code-review` | high | Salir con 3 chocaba con `con_pg16.sh` (Postgres no arranca) | «sin carrera» sale con 4 |
| `/code-review` | high | Quedar más de 10 contaba como OK | «SOBRA», no vale (2) |
| `/code-review` | high | La etiqueta «con commit» del árbol era ambigua | «db.commit() escrito en require_active_billing» |
| `/code-review` | high | `esperando_un_lock` de `cobro_mp2_postgres.py` y `_SDK` de `tests/test_cobro_mp2.py` quedan repetidos en el medidor | queda: son arneses; unificarlos va a la cola de limpieza |
| `/code-review` | high | `conexiones1_cuerpo.py:240`, `gather` sin `return_exceptions` | queda, riesgo bajo: no pasó en ninguna corrida |
| `/code-review` | high | `conexiones1_cuerpo.py:205`, «retenido» puede declararse antes de que el servidor tenga el último buffer | queda, riesgo bajo: la memoria retenida coincide con los bytes mandados |

`/security-review`: no corrido. G no tiene producto (+0/−0); va en la pieza
de producto, que toca plata.

Limpieza de los `conftest.py` sueltos (acta de F): retirados los tres
(`/tmp/adv-mp2/`, `/tmp/rv-corte1-o/probe/`, `/tmp/rv-corte1-o/probe_base/`).
`ls` de cada uno da «No such file or directory» y
`find /tmp -maxdepth 3 -name conftest.py -not -path "*/tests/*"` da vacío.

## Riesgos

- D188 es plata real en producción hoy, no un riesgo del diff.
- El medidor de créditos toma una fila con `for update` y abre hilos; si
  Postgres no responde, cada fase corta a los 15 s.
- Medí en loopback con 1 worker.

## Comandos copiables

Desde la raíz de un worktree limpio de `claude/dev-tecnica`, con el entorno
virtual del proyecto en el `PATH` y Postgres 16 para `con_pg16.sh`. Cada
corrida de créditos tarda menos de un minuto.

```bash
git fetch origin claude/dev-tecnica
git worktree add --detach /tmp/g origin/claude/dev-tecnica && cd /tmp/g
scripts/testing/con_pg16.sh python scripts/testing/conexiones1_creditos.py; echo rc=$?
#   → dos «PIERDE | … quedan 0 de 10 pagos (perdidos 10)», «pierden: 2; no valen: 0; sin carrera: 0», rc=1
awk '/^```diff/{n++;f=1;next} /^```$/{f=0} f&&n==3' docs/pm/PARA-PM.md > /tmp/verde.diff
git apply /tmp/verde.diff
scripts/testing/con_pg16.sh python scripts/testing/conexiones1_creditos.py; echo rc=$?
#   → cuatro «OK … quedan 10 de 10 pagos», «pierden: 0; no valen: 0; sin carrera: 0», rc=0
git checkout -- proyecto_maria/main.py
for n in 1 2; do awk -v n=$n '/^```diff/{k++;f=1;next} /^```$/{f=0} f&&k==n' docs/pm/PARA-PM.md > /tmp/d$n.diff; git apply --check /tmp/d$n.diff && echo "diff $n limpio"; done
#   → «diff 1 limpio» (revisado) y «diff 2 limpio» (alternativa)
```

Para la columna «revisado» o «alternativa» del punto 2: `git apply /tmp/d1.diff`
(o `d2`) y la misma corrida → rc=1, «pierden: 2».

## Puertas

| Puerta | Resultado |
|---|---|
| Créditos, hoy (`9a032f12`) | pierden 2 · rc=1 |
| Créditos, revisado | pierden 2 · rc=1 |
| Créditos, alternativa | pierden 2 · rc=1 |
| Créditos, arreglo de prueba de D189 | pierden 0 · rc=0 · 0 deadlocks |
| Créditos, arreglo ingenuo | no valen 1 (alta 500 por deadlock) · rc=2 |
| Créditos, carrera imposible | sin carrera 2 · rc=4, sin cuelgue |
| Cuerpos, tabla y 4×500 en las tres columnas | medición válida · rc=0 en las seis |
| `git apply --check` de los tres diffs sobre `9a032f12` | limpio |
| chequeo-6 | 0 avisos |

**No corrido:** suite completa, smoke, ataques y `/security-review` (no hay
producto ni casos nuevos en `tests/`).

<details><summary>chequeo-6 21df2a39..HEAD (HEAD = 9a032f12)</summary>

```
chequeo-6 21df2a39..HEAD: avisos para mirar, no un veredicto
producto +0/−0
arnés +592/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

</details>

## Diffs

### Revisado: diff de F, (a)

```diff
diff --git a/proyecto_maria/main.py b/proyecto_maria/main.py
index 52fe473f..f5967be0 100644
--- a/proyecto_maria/main.py
+++ b/proyecto_maria/main.py
@@ -386,6 +386,7 @@ app = FastAPI(
 # Configurar CORS (OWASP A5 - Broken Access Control)
 from starlette.middleware.cors import CORSMiddleware
 from starlette.exceptions import HTTPException as StarletteHTTPException
+from starlette.requests import ClientDisconnect
 
 # CORS + cookies: la especificacion prohibe combinar allow_origins=["*"]
 # con allow_credentials=True (los browsers rechazan la cookie). Como la
@@ -2303,6 +2304,9 @@ async def require_billing_vigente(
     await _vencer_y_guardar(db, entidad)
     if not billing_service.tiene_acceso(entidad):
         raise HTTPException(status_code=402, detail=_detalle_402(entidad))
+    # Termina la transacción de lectura: si no, la conexión queda tomada
+    # mientras el endpoint espera a la IA o a la lectura del PDF.
+    await db.commit()
     return db_user
 
 
@@ -3746,11 +3750,21 @@ async def simulate_charge(user=Depends(get_current_user), db: AsyncSession = Dep
     }
 
 
+async def _leer_cuerpo(request: Request):
+    # Con el cuerpo ya leído, un cliente lento no retiene la conexión de las
+    # dependencias que vienen después.
+    try:
+        await request.body()
+    except ClientDisconnect:
+        raise HTTPException(status_code=400, detail="Body JSON inválido")
+
+
 @app.post("/api/operations/manual")
 @limiter.limit(get_dynamic_rate_limit)
 async def create_manual_operation(
     request: Request,
     user=Depends(get_current_user),
+    _cuerpo=Depends(_leer_cuerpo),
     db: AsyncSession = Depends(get_db),
     db_user: User = Depends(require_active_billing),
 ):
@@ -7172,6 +7186,8 @@ async def analyze_client_migration(
         )
     )
     existing_clients = existing_result.scalars().all()
+    # Suelta la conexión mientras se lee el archivo; los clientes quedan cargados.
+    await db.commit()
     mapper = GeminiMigrationHeaderMapper(username=user["username"])
     try:
         # Con tiempo máximo, como leer un PDF (EXCEL-1).
@@ -7211,7 +7227,6 @@ async def analyze_client_migration(
     db.add(batch)
     try:
         await db.commit()
-        await db.refresh(batch)
     except Exception as exc:
         await db.rollback()
         logging.exception("analyze_client_migration staging failed")
@@ -10328,6 +10343,15 @@ async def propuesta_de_sufijos(data: dict, user=Depends(get_current_user)):
     return {"fuente": sufijos_arca.fuente(tabla), "sin_tabla": not tabla, "items": salida}
 
 
+async def _soltar_conexion(db: AsyncSession) -> None:
+    # Suelta la conexión antes de esperar a un servicio lento. Si la base se
+    # cayó, lo ya leído alcanza: la ruta sigue sin cortar.
+    try:
+        await db.commit()
+    except Exception as err:
+        logging.warning("db release before slow call failed: %s", err)
+
+
 @app.post("/api/ncm/sugerir")
 async def sugerir_ncm(
     data: dict,
@@ -10448,6 +10472,7 @@ async def sugerir_ncm(
         # (RENDIMIENTO-1). Si no contesta a tiempo, se sigue sin sus sugerencias.
         import asyncio
         limite = _segundos_de_entorno("NCM_GEMINI_TIMEOUT_S", 30.0)
+        await _soltar_conexion(db)
         try:
             de_gemini = await asyncio.wait_for(
                 asyncio.to_thread(_suggest_ncm_with_gemini, descripcion, 5 - len(sugerencias)),
diff --git a/tests/test_cobro_corte1.py b/tests/test_cobro_corte1.py
index cfb81a79..8f35b604 100644
--- a/tests/test_cobro_corte1.py
+++ b/tests/test_cobro_corte1.py
@@ -828,7 +828,8 @@ _confirmar = main.AsyncSession.commit
 
 async def _commit_que_falla(self):
     # La autenticación confirma antes de la ruta: falla sólo el de main.py.
-    if sys._getframe(1).f_code.co_filename != main.__file__:
+    quien = sys._getframe(1).f_code
+    if quien.co_filename != main.__file__ or quien is main.require_billing_vigente.__code__:
         return await _confirmar(self)
     raise RuntimeError("la base se cayó al confirmar")
 
diff --git a/tests/test_conexiones1.py b/tests/test_conexiones1.py
new file mode 100644
index 00000000..99caa2d3
--- /dev/null
+++ b/tests/test_conexiones1.py
@@ -0,0 +1,260 @@
+"""Las rutas lentas de RUTAS no retienen una conexión a la base mientras esperan.
+
+Cada ruta se frena en su punto lento (la IA, el lector de PDF, la lectura del
+Excel, el cuerpo del pedido) y ahí se cuentan las conexiones que tiene tomadas
+el pedido. Con el pool de producción, cada una tomada ahí es un lugar menos
+para las otras cuentas mientras dura la espera.
+"""
+import asyncio
+import io
+import uuid
+
+import aiosqlite
+import pytest
+from fastapi.testclient import TestClient
+from pypdf import PdfWriter
+from sqlalchemy import event, func, select, update
+from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
+from sqlalchemy.pool import AsyncAdaptedQueuePool
+from starlette.requests import Request
+
+from proyecto_maria import main
+from proyecto_maria.core import rate_limit
+from proyecto_maria.database import connection as _conn
+from proyecto_maria.database.models import SystemBackup, User
+from proyecto_maria.services import migration_service
+
+CLAVE = "Clave-Segura-123"
+
+
+def _pdf():
+    escritor, salida = PdfWriter(), io.BytesIO()
+    escritor.add_blank_page(100, 100)
+    escritor.write(salida)
+    return salida.getvalue()
+
+
+@pytest.fixture
+def tomadas():
+    """Cuántas conexiones hay tomadas ahora, sin las del registro de métricas,
+    que corre en su propia tarea."""
+    duenas = {}
+
+    def al_tomar(_dbapi, registro, _proxy):
+        try:
+            duenas[id(registro)] = asyncio.current_task()
+        except RuntimeError:
+            duenas[id(registro)] = None
+
+    def al_devolver(_dbapi, registro):
+        duenas.pop(id(registro), None)
+
+    motor = _conn.engine.sync_engine
+    event.listen(motor, "checkout", al_tomar)
+    event.listen(motor, "checkin", al_devolver)
+    yield lambda: sum(1 for t in duenas.values()
+                      if t is None or "log_request_background" not in t.get_coro().__qualname__)
+    event.remove(motor, "checkout", al_tomar)
+    event.remove(motor, "checkin", al_devolver)
+
+
+def _sesion(monkeypatch):
+    monkeypatch.setattr(rate_limit.limiter, "enabled", False)
+    # Un 500 vuelve como respuesta y no como excepción del cliente de prueba.
+    c = TestClient(main.app, raise_server_exceptions=False)
+    nombre = f"conex1_{uuid.uuid4().hex[:10]}"
+    r = c.post("/auth/register", json={"username": nombre, "password": CLAVE, "name": nombre,
+                                       "email": f"{nombre}@cdi.test"})
+    assert r.status_code in (200, 201), r.text
+    r = c.post("/auth/login", json={"username": nombre, "password": CLAVE})
+    assert r.status_code == 200, r.text
+    return c, nombre
+
+
+def _lector_falso(*_a, **_k):
+    raise main.DocumentoNoAdmitido("lector falso")
+
+
+def _cortar_a_mitad(pedido):
+    """El cliente manda parte del cuerpo y se desconecta."""
+    mensajes = iter([{"type": "http.request", "body": b'{"client_id": "9', "more_body": True},
+                     {"type": "http.disconnect"}])
+
+    async def recibir():
+        return next(mensajes)
+    pedido._receive = recibir
+
+
+# (punto lento, dónde está, qué hace en lugar de esperar, pedido, código esperado)
+RUTAS = [
+    ("_suggest_ncm_with_gemini", main, lambda *_a, **_k: [],
+     ("/api/ncm/sugerir", {"json": {"descripcion": "notebook de 14 pulgadas"}}), 200),
+    ("process_pdf", main, _lector_falso,
+     ("/upload_pdf/public", {"files": {"file": ("a.pdf", _pdf(), "application/pdf")}}), 422),
+    ("_read_sheets", migration_service, None,
+     ("/api/migrations/analyze",
+      {"files": {"file": ("clientes.csv", b"cuit,nombre\n20123456786,Cliente Uno\n", "text/csv")}}), 200),
+    ("body", Request, None,
+     ("/api/operations/manual", {"json": {"client_id": "999999999", "items": [
+         {"descripcion": "notebook", "cantidad": 1, "valor_unitario": 10}]}}), 404),
+    ("body", Request, _cortar_a_mitad,
+     ("/api/operations/manual", {"json": {"client_id": "999999999", "items": []}}), 400),
+]
+
+
+@pytest.mark.parametrize("punto, modulo, reemplazo, pedido, codigo", RUTAS,
+                         ids=[f"{r[0]}-{r[4]}" for r in RUTAS])
+def test_la_espera_no_retiene_conexiones(monkeypatch, tomadas, punto, modulo, reemplazo, pedido, codigo):
+    c, _ = _sesion(monkeypatch)
+    vistas = []
+    original = getattr(modulo, punto)
+    if modulo is Request:
+        async def frenar(self):
+            if not hasattr(self, "_body"):
+                vistas.append(tomadas())
+                if reemplazo:
+                    reemplazo(self)
+            return await original(self)
+    else:
+        def frenar(*a, **k):
+            vistas.append(tomadas())
+            return (reemplazo or original)(*a, **k)
+    monkeypatch.setattr(modulo, punto, frenar)
+    monkeypatch.setattr(main, "lectura_automatica_disponible", lambda: True)
+    ruta, datos = pedido
+    with c:
+        r = c.post(ruta, **datos)
+    assert r.status_code == codigo, r.text
+    assert vistas and max(vistas) == 0, f"conexiones tomadas en {punto}: {vistas}"
+
+
+def _impaga(nombre):
+    async def guardar():
+        async with _conn.AsyncSessionLocal() as db:
+            await db.execute(update(User).where(User.username == nombre).values(billing_status="past_due"))
+            await db.commit()
+    asyncio.run(guardar())
+
+
+def _sin_cuota(monkeypatch):
+    def gastar(c):
+        assert c.post("/api/operations/manual", json=MANUAL).status_code == 404
+    monkeypatch.setattr(rate_limit.settings, "rate_limit_basic", "1/minute")
+    monkeypatch.setattr(rate_limit.limiter, "enabled", True)
+    return gastar
+
+
+MANUAL = {"client_id": "999999999", "items": [{"descripcion": "notebook", "cantidad": 1, "valor_unitario": 10}]}
+# (cuenta, cómo queda sin poder cargar, código con el cuerpo completo)
+CUENTAS = [
+    ("impaga", lambda nombre, _mp: _impaga(nombre), 402),
+    ("sin cuota", lambda _nombre, mp: _sin_cuota(mp), 429),
+]
+
+
+def test_cuenta_que_no_puede_cargar_y_corta_el_cuerpo(monkeypatch, tomadas):
+    """El corte se contesta antes que el plan o la cuota, sin tomar conexión."""
+    leer, vieron = Request.body, []
+    for cuenta, preparar, codigo in CUENTAS:
+        with monkeypatch.context() as mp:
+            c, nombre = _sesion(mp)
+            gastar = preparar(nombre, mp)
+            vistas = []
+            # Un corte por pedido, en orden: gastar la cuota, el cortado, el completo.
+            cortes = ([False] if gastar else []) + [True, False]
+
+            async def frenar(self):
+                if not hasattr(self, "_body"):
+                    vistas.append(tomadas())
+                    if cortes.pop(0):
+                        _cortar_a_mitad(self)
+                return await leer(self)
+            mp.setattr(Request, "body", frenar)
+            try:
+                with c:
+                    if gastar:
+                        gastar(c)
+                    cortado = c.post("/api/operations/manual", json=MANUAL)
+                    completo = c.post("/api/operations/manual", json=MANUAL)
+            finally:
+                rate_limit.limiter.reset()
+        vieron.append((cuenta, cortado.status_code, completo.status_code, max(vistas, default="sin leer")))
+    assert vieron == [(cuenta, 400, codigo, 0) for cuenta, _p, codigo in CUENTAS]
+
+
+def _respaldos(nombre):
+    async def contar():
+        async with AsyncSession(_conn.engine) as db:
+            return await db.scalar(select(func.count()).select_from(SystemBackup)
+                                   .where(SystemBackup.owner_username == nombre))
+    return asyncio.run(contar())
+
+
+def test_analyze_con_el_pool_lleno_no_deja_nada_a_medias(monkeypatch):
+    """Si otra cuenta toma todas las conexiones mientras se lee el Excel, el
+    respaldo no se guarda y contesta 500; si las toma recién después de
+    guardarlo, contesta 200. Nunca un 500 con el respaldo guardado."""
+    c, nombre = _sesion(monkeypatch)
+    leer, guardar = migration_service.analyze_migration_file_async, AsyncSession.commit
+    archivo = {"file": ("clientes.csv", b"cuit,nombre\n20123456786,Cliente Uno\n", "text/csv")}
+    estado = {}
+
+    async def llenar(momento):
+        if estado["momento"] == momento and not estado["otras"]:
+            motor = estado["motor"]
+            while motor.pool.checkedout() < motor.pool.size():
+                estado["otras"].append(await motor.connect())
+
+    async def leer_y_llenar(*a, **k):
+        estado["leido"] = True
+        await llenar("al leer")
+        return await leer(*a, **k)
+
+    async def guardar_y_llenar(self, *a, **k):
+        await guardar(self, *a, **k)
+        if estado["leido"]:
+            await llenar("al guardar")
+
+    monkeypatch.setattr(migration_service, "analyze_migration_file_async", leer_y_llenar)
+    monkeypatch.setattr(AsyncSession, "commit", guardar_y_llenar)
+    vieron = []
+    for momento in ("al leer", "al guardar"):
+        # pool_timeout=0 no sirve: wait_for(…, 0) corta aunque haya una conexión libre.
+        motor = create_async_engine(_conn.DATABASE_URL, poolclass=AsyncAdaptedQueuePool,
+                                    pool_size=5, max_overflow=0, pool_timeout=0.05)
+        estado.update(momento=momento, motor=motor, otras=[], leido=False)
+        antes = _respaldos(nombre)
+        _conn.AsyncSessionLocal.configure(bind=motor)
+        try:
+            with c:
+                lleno = c.post("/api/migrations/analyze", files=archivo)
+                quedaron = _respaldos(nombre) - antes
+                for otra in estado["otras"]:
+                    c.portal.call(otra.close)
+                libre = c.post("/api/migrations/analyze", files=archivo)
+                c.portal.call(motor.dispose)
+        finally:
+            _conn.AsyncSessionLocal.configure(bind=_conn.engine)
+        vieron.append((momento, lleno.status_code, lleno.json().get("detail", "").split(".")[0],
+                       quedaron, libre.status_code, _respaldos(nombre) - antes))
+    assert vieron == [("al leer", 500, "No pudimos procesar tu solicitud", 0, 200, 1),
+                      ("al guardar", 200, "", 1, 200, 2)]
+
+
+def test_ncm_con_la_base_caida_al_soltarla_sigue_sugiriendo(monkeypatch):
+    """Si la conexión se cae después de la última lectura, soltarla antes de
+    la IA no corta el pedido: se sugiere con lo que ya se leyó."""
+    c, _ = _sesion(monkeypatch)
+    mirar = main._looks_like_ncm_code_query
+
+    def caer_y_mirar(descripcion):
+        async def caida(*a, **k):
+            raise RuntimeError("conexión caída")
+        monkeypatch.setattr(aiosqlite.Connection, "commit", caida)
+        monkeypatch.setattr(aiosqlite.Connection, "rollback", caida)
+        return mirar(descripcion)
+    monkeypatch.setattr(main, "_looks_like_ncm_code_query", caer_y_mirar)
+    monkeypatch.setattr(main, "_suggest_ncm_with_gemini",
+                        lambda *a, **k: [{"ncm": "8471.30.12", "desc": "notebook", "source": "ia"}])
+    r = c.post("/api/ncm/sugerir", json={"descripcion": "notebook de 14 pulgadas"})
+    assert (r.status_code, [s["ncm"] for s in r.json().get("sugerencias", [])]) == (200, ["8471.30.12"])
```

### Alternativa: diff de D186 (b)

```diff
diff --git a/proyecto_maria/main.py b/proyecto_maria/main.py
index 52fe473f..50b4bb6e 100644
--- a/proyecto_maria/main.py
+++ b/proyecto_maria/main.py
@@ -2303,6 +2303,9 @@ async def require_billing_vigente(
     await _vencer_y_guardar(db, entidad)
     if not billing_service.tiene_acceso(entidad):
         raise HTTPException(status_code=402, detail=_detalle_402(entidad))
+    # Termina la transacción de lectura: si no, la conexión queda tomada
+    # mientras el endpoint espera a la IA o a la lectura del PDF.
+    await db.commit()
     return db_user
 
 
@@ -2325,6 +2328,9 @@ async def require_active_billing(
     ok, reason = billing_service.can_create_operation(entidad)
     if not ok:
         raise HTTPException(status_code=402, detail=_detalle_402(entidad, reason))
+    # Termina la transacción de lectura: si no, la conexión queda tomada
+    # mientras la ruta lee el cuerpo.
+    await db.commit()
     return db_user
 
 
@@ -7172,6 +7178,8 @@ async def analyze_client_migration(
         )
     )
     existing_clients = existing_result.scalars().all()
+    # Suelta la conexión mientras se lee el archivo; los clientes quedan cargados.
+    await db.commit()
     mapper = GeminiMigrationHeaderMapper(username=user["username"])
     try:
         # Con tiempo máximo, como leer un PDF (EXCEL-1).
@@ -7211,7 +7219,6 @@ async def analyze_client_migration(
     db.add(batch)
     try:
         await db.commit()
-        await db.refresh(batch)
     except Exception as exc:
         await db.rollback()
         logging.exception("analyze_client_migration staging failed")
@@ -10328,6 +10335,15 @@ async def propuesta_de_sufijos(data: dict, user=Depends(get_current_user)):
     return {"fuente": sufijos_arca.fuente(tabla), "sin_tabla": not tabla, "items": salida}
 
 
+async def _soltar_conexion(db: AsyncSession) -> None:
+    # Suelta la conexión antes de esperar a un servicio lento. Si la base se
+    # cayó, lo ya leído alcanza: la ruta sigue sin cortar.
+    try:
+        await db.commit()
+    except Exception as err:
+        logging.warning("db release before slow call failed: %s", err)
+
+
 @app.post("/api/ncm/sugerir")
 async def sugerir_ncm(
     data: dict,
@@ -10448,6 +10464,7 @@ async def sugerir_ncm(
         # (RENDIMIENTO-1). Si no contesta a tiempo, se sigue sin sus sugerencias.
         import asyncio
         limite = _segundos_de_entorno("NCM_GEMINI_TIMEOUT_S", 30.0)
+        await _soltar_conexion(db)
         try:
             de_gemini = await asyncio.wait_for(
                 asyncio.to_thread(_suggest_ncm_with_gemini, descripcion, 5 - len(sugerencias)),
diff --git a/tests/test_cobro_corte1.py b/tests/test_cobro_corte1.py
index cfb81a79..8f35b604 100644
--- a/tests/test_cobro_corte1.py
+++ b/tests/test_cobro_corte1.py
@@ -828,7 +828,8 @@ _confirmar = main.AsyncSession.commit
 
 async def _commit_que_falla(self):
     # La autenticación confirma antes de la ruta: falla sólo el de main.py.
-    if sys._getframe(1).f_code.co_filename != main.__file__:
+    quien = sys._getframe(1).f_code
+    if quien.co_filename != main.__file__ or quien is main.require_billing_vigente.__code__:
         return await _confirmar(self)
     raise RuntimeError("la base se cayó al confirmar")
 
```

### Arreglo de prueba de D189

```diff
diff --git a/proyecto_maria/main.py b/proyecto_maria/main.py
index 52fe473f..b6ad78b2 100644
--- a/proyecto_maria/main.py
+++ b/proyecto_maria/main.py
@@ -2321,6 +2321,7 @@ async def require_active_billing(
         raise HTTPException(status_code=401, detail="Usuario no encontrado")
 
     entidad, _ = await _get_billing_entity(db, db_user)
+    await db.refresh(entidad, with_for_update=True)
     await _vencer_y_guardar(db, entidad)
     ok, reason = billing_service.can_create_operation(entidad)
     if not ok:
```
