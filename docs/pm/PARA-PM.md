# Dev 1 → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## COBRO-CORTE-1 — frenada antes de codear: D4, D5 y D6

ADMIN-1 sigue entregada más abajo, sin cambios. Empecé COBRO-CORTE-1
leyendo el flujo real, y hay tres cosas de dinero y datos que cambian el
resultado. No escribí código.

**Lo que encontré.**
- `/generate_maria` no mira ninguna operación guardada. Recibe los ítems y
  un `operation_id` que inventa el navegador: `FAC_<factura>` o
  `OP_<fecha y hora>` (`static/v2/screens/finalize.js:358`). Después del
  TXT, la pantalla guarda la operación con `POST /api/clientes/{id}/operaciones`,
  que es la que cuenta (`main.py:5527`), y **sólo si hay un cliente activo**.
  Con la pantalla de «operación sin cliente» el MARIA sale y nunca se cuenta.
- La operación guardada recibe un id nuevo cada vez (`uuid4`, `main.py:5452`).
  No hay nada que una el TXT generado con la operación contada. Volver a
  guardar la misma operación la cuenta de nuevo. Hoy lo evita sólo el
  navegador.
- Sólo dos lugares crean operaciones, y los dos cuentan: `main.py:3181`
  (manual) y `:5451`.

- **D4 — Cómo sabe `/generate_maria` si la operación «ya se contó».**
  (a) Sólo cortar por estado de cobro (402 si está vencido o impago) y
  seguir contando únicamente al guardar. Es lo mínimo, pero el MARIA sin
  cliente sigue saliendo gratis.
  (b) La primera vez que se genera un `operation_id` del usuario, crear la
  operación (sin cliente, `source="maria"`) y contarla. Las descargas
  siguientes con el mismo id no cuentan, y el guardado posterior usa esa
  operación en vez de crear y contar otra. No hace falta cambiar el
  esquema: `client_id` ya acepta vacío. Sí hay que tocar `finalize.js`
  para que guarde con el id del MARIA. Hueco: quien reuse siempre el mismo
  id genera MARIAs distintos pagando una.
  (c) Como (b), pero con el id calculado por el servidor a partir del
  contenido (ítems y sufijo). Cierra el hueco de (b), pero corregir un
  ítem y volver a generar cuenta otra vez.
  **Recomiendo (b)**: cumple «se cuenta una vez» sin migración. Al hueco le
  pongo un límite: un mismo `operation_id` no puede pasar de N regeneraciones
  con contenido distinto. El N lo decidís vos; propongo 10.
- **D5 — Qué corte va en las rutas que gastan Gemini o generan valor**
  (`/upload_pdf/public`, `/upload_excel`, `/api/validate/smart`,
  `/api/ncm/sugerir`, `/api/migrations/*`). `require_active_billing` corta
  por estado **y** por tope del plan. Con eso, quien pagó y usó sus 15
  operaciones tampoco podría subir un PDF ni validar una operación ya
  contada.
  (a) Sólo por estado: vencido o impago → 402. El tope se mira sólo donde
  se cuenta una operación.
  (b) Estado y tope en todas.
  **Recomiendo (a)**: «quien no paga no genera valor», sin trabar al que pagó.
- **D6 — Carreras (C6) sin migración de esquema.**
  (a) Bloquear la fila de la cuenta (`SELECT … FOR UPDATE` del usuario o de
  la organización) mientras se mira el tope, se cuenta y se calcula el
  `op_code`, todo en una transacción. Serializa por cuenta y no cambia el
  esquema. Lo pruebo con pedidos al mismo tiempo en un Postgres local:
  está instalado el 16.
  (b) Además, un índice único `(owner_username, op_code)`. Es una migración,
  y fallaría si producción ya tiene códigos repetidos; habría que mirar
  antes.
  **Recomiendo (a)** ahora y (b) como pieza aparte, si querés la garantía en
  la base.

Mientras no contestes, no avanzo con COBRO-CORTE-1: las tres D cambian el
código.

---

## ADMIN-1 — entregada, terminada

| | SHA |
|---|---|
| Base (tu rama al arrancar) | `cb8f509` |
| Producto | `c7029e8` (fix) + `2d76015` (sólo docstrings) |
| Pruebas y sabotajes | `2c1d195`, `06881d1`, `76a2b42`, `71118ee`, `ac25dbc` |
| **Entrego (código)** | **`ac25dbc`**; encima, el merge de tu rama (sólo docs) y este informe |

Resultado: `/api/admin/*` y `/api/ncm/cache/refresh` exigen admin. Un
usuario común recibe 403 en cada ruta de admin y en la global; el admin
entra igual que antes; el panel `/dev/dashboard` anda. Suite completa en
verde sobre `ac25dbc`.

## Decisiones

- **D1 — `GET /api/system/connectors` (global, la usa la pantalla común).**
  Muestra a cualquier usuario logueado la configuración del sistema: modo y
  `base_url` de VUCE y Tarifar, si hay clave, CUIT y certificado de AFIP, y
  el user-agent del scraper. Lo consume la barra superior de todos
  (`static/v2/topbar_financials.js:88`, el chip «Sistema/Demo»). Por la
  regla de la tarea no la toqué.
  Opciones: (a) dejarla como está; (b) al usuario común darle sólo el `mode`
  de cada conector y el detalle completo sólo al admin (el chip sigue
  andando); (c) `require_admin` (el chip queda en «unknown» para todos).
  **Recomiendo (b)**: es chica y no cambia nada visible. Sería una pieza
  aparte o un agregado a esta.
- **D2 — `POST /api/payments/simulate-webhook` (global que activa cobro).**
  Le activa premium a **cualquier** usuario del body, sin sesión: sólo pide
  el header `X-Webhook-Secret` igual a `MP_WEBHOOK_SECRET`, el mismo secreto
  que el webhook real de MP. Donde MP esté configurado, ese endpoint queda
  vivo en producción, aunque su docstring diga «sólo staging». Lo reprodujo
  el revisor Sonnet con un secreto local: sin sesión, `trial` → `active`. No
  lo usa el frontend. No la toqué: es cobro y MP está fuera de alcance.
  Opciones: (a) borrarla; (b) `require_admin` + 404 si `IS_PRODUCTION`;
  (c) dejarla para COBRO-MP. **Recomiendo (a)** antes de publicar; si se
  quiere conservar para staging, (b).
- **D3 — `/api/admin/cohort-retention` pide además el rol `admin`.**
  `require_role('admin')` (`routers/admin_router.py:343`) no mira
  `ADMIN_USERNAMES`. Quien es admin sólo por la variable y se registró
  después del último arranque entra a todo `/api/admin/*` menos esta (403,
  reproducido). Ya pasaba antes; no es regresión. Opciones: (a) quitar ese
  `require_role`, porque el router ya exige admin; (b) dejarlo.
  **Recomiendo (a)**: una línea, y lo agrego a la prueba.

## Lista cerrada de funciones globales

Recorrí las 139 rutas (las dos de `routers/` incluidas). Global = no actúa
sobre los datos de un estudio.

| Ruta | Qué hace | Estado |
|---|---|---|
| `/api/admin/*` (9) | salud, errores, métricas, logs, borrar errores, cohortes | **ahora `require_admin`** |
| `POST /api/ncm/cache/refresh` | borra y recarga el cache NCM que comparten todos | **ahora `require_admin`** + `tags=["admin"]` |
| `/dev/dashboard`, `/api/dev/*` (5) | panel, stats, KPIs, migraciones, esquema | ya tenían `require_admin` (no se tocaron) |
| `GET /api/system/connectors` | configuración de conectores | abierta a logueados → **D1** |
| `POST /api/payments/simulate-webhook` | activa cobro de cualquier usuario | sólo secreto → **D2** |
| `POST /api/payments/webhook` | webhook real de MP | firma HMAC; es de MP, se queda |
| `/api/ui/event`, `/api/session/state` | telemetría sin sesión | es el S5 de la auditoría; la usa la landing |
| `/api/dolar`, `/api/financials`, `/api/arca/novedades`, `/api/billing/plans`, `/health` | lecturas públicas | públicas a propósito (topbar, Railway) |

Del estudio (filtran por dueño), revisadas por los dos revisores: catálogo,
notas e historial NCM, clientes, operaciones, descargas, backups, billing
propio, organizaciones, cotizaciones. `/api/ncm/{ncm}/completo`, `calcular`
y `enrich-items` leen datos públicos de NCM y llenan el cache: no son admin.

## Cómo marca la prueba qué es admin

`tests/test_admin_solo_admin.py` no tiene lista de rutas. Lee las rutas de
la app (esquema OpenAPI, que incluye los routers montados, más las rutas
escondidas del esquema) y toma:

- todo lo que cuelga de `/api/admin/`, `/api/dev/` o `/dev/`;
- toda ruta con `tags=["admin"]` (la marca de «global», puesta en el
  decorador de la ruta).

Para cada una, usuario común → 403 y sin sesión → 401. Lo que **no** puede
hacer: adivinar que una ruta nueva es global si nadie le pone el tag. Lo dejé
escrito junto a `require_admin` (`main.py:1722`). No hay forma automática
honesta de decidir «global» sin marca.

## Riesgos (para antes de publicar)

1. **Quién es admin en producción.** Después de publicar, `/api/admin/*`
   sólo deja entrar a quien esté en `ADMIN_USERNAMES` o tenga el rol
   `admin`. Si Railway no tiene la variable y nadie tiene el rol, nadie
   entra al admin (el resto de la app no cambia). Que Emi lo confirme antes
   del «dale».
2. **`ADMIN_USERNAMES` se puede reclamar** (revisor Opus, reproducido en
   local). Si la variable nombra un usuario o un email que todavía no está
   registrado, quien se registre primero con ese nombre es admin. El email
   da el rol en el siguiente reinicio y no se verifica, porque
   `EMAIL_VERIFICATION_REQUIRED` viene apagado. Ya pasaba antes, pero con
   ADMIN-1 ser admin vale más. Fuera de alcance («cómo se decide quién es
   admin»).
3. **Usuario `demo/demo123` con rol admin** (`main.py:1341`): se crea si
   `ENVIRONMENT` no es `production`. No verifiqué qué tiene Railway.
4. **El router de admin se monta en el arranque** (lifespan) y se vuelve a
   montar en cada arranque. Eso ya existía. En producción arranca una vez; si
   no arrancara, `/api/admin/*` da 404, cerrado y no abierto.

## Comandos copiables

```bash
git fetch origin claude/dev1-tecnica && git checkout ac25dbc
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh ac25dbc 8080
# desde el worktree que dejó levantar.sh:
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov tests/test_admin_solo_admin.py   # 14 passed
PY=$(which python) scripts/testing/sabotajes/admin1.sh ac25dbc # 7 «ROJO», «sabotajes con falla: 0»
python -m pytest -q --no-cov --timeout=120                    # 694 passed, 102 skipped
```

## Evidencia (salida exacta)

**Rojo antes** (API de la base `cb8f509` en :8810, usuario común `comun1`
recién registrado):

```
POST /api/admin/errors/clear-old -> 200
GET /api/admin/health/detailed -> 200
GET /api/admin/stats/summary -> 200
POST /api/ncm/cache/refresh -> 200
```

La prueba nueva sobre el `main.py` de la base (sólo con el tag puesto en
cache/refresh para que la vea):

```
E   AssertionError: rutas de admin abiertas a un usuario común:
E     GET /api/admin/errors/insights → 200
E     GET /api/admin/errors/top/{limit} → 200
E     GET /api/admin/health/detailed → 200
E     GET /api/admin/logs/recent/{limit} → 200
E     GET /api/admin/metrics/prometheus → 200
E     GET /api/admin/stats/summary → 200
E     GET /api/admin/test/sentry → 500
E     POST /api/admin/errors/clear-old → 200
E     POST /api/ncm/cache/refresh → 422
================== 1 failed, 12 passed, 11 warnings in 2.18s ===================
```

**Verde después**, API de `76a2b42` en :8811 (el código de producto es el
mismo que en `ac25dbc`, salvo dos docstrings). Usuario común `comun2`: 403 en
las 9 de `/api/admin/*`, en `cache/refresh`, en `/dev/dashboard` y en
`/api/dev/stats` y `wave1-kpis`. `/api/clientes` → 200, la app común sigue.
Admin `jefe1`, admin sólo por `ADMIN_USERNAMES`, en :8812:

```
POST /api/admin/errors/clear-old -> 200
GET /api/admin/health/detailed -> 200
GET /api/admin/errors/insights -> 200
GET /api/admin/errors/top/5 -> 200
GET /api/admin/metrics/prometheus -> 200
GET /api/admin/logs/recent/5 -> 200
GET /api/admin/stats/summary -> 200
GET /api/admin/test/sentry -> 500      (error intencional, igual que antes)
GET /api/admin/cohort-retention -> 403 (D3: pide además el rol)
GET /dev/dashboard -> 200
GET /api/dev/stats -> 200
GET /api/dev/wave1-kpis -> 200
```

Panel en Chromium con `jefe1`: `dashboard 200`, `200 /api/dev/stats`,
`200 /api/dev/wave1-kpis`; la captura muestra las métricas y el tráfico
cargados.

**Sabotajes** (`scripts/testing/sabotajes/admin1.sh ac25dbc`):

```
ROJO  | router de admin vuelve a get_current_user: dice «POST /api/admin/errors/clear-old → 200»
ROJO  | cache/refresh sin require_admin: dice «POST /api/ncm/cache/refresh → 422»
ROJO  | /api/dev/stats sin require_admin: dice «GET /api/dev/stats → 200»
ROJO  | /dev/dashboard sin require_admin: dice «GET /dev/dashboard → 200»
ROJO  | /api/dev/stats escondida del esquema y sin require_admin: dice «GET /api/dev/stats → 200»
ROJO  | cache/refresh niega también al admin: dice «FAILED tests/test_admin_solo_admin.py::test_admin_refresca_cache_ncm»
ROJO  | cache/refresh pierde la marca admin (la prueba dejaría de verla): dice «assert ('POST', '/api/ncm/cache/refresh') in [»
sabotajes con falla: 0
```

## Puertas sobre `ac25dbc`

| Puerta | Resultado |
|---|---|
| Suite completa, worktree limpio | `694 passed, 102 skipped, 24 warnings in 54.66s` (base 680 + 14 nuevas) |
| `compileall` | sin errores (sobre `71118ee`; desde ahí sólo cambió una prueba) |
| `smoke_friccion.sh` contra :8811 (`76a2b42`) | `OK · telemetría + alias session/state + by-cuit protegido` |
| `ataque_aislamiento.sh` (`76a2b42`) | 22 BLOQUEADO, 0 FUGA |

## Autorrevisión

| Revisor | Hallazgo | Qué hice |
|---|---|---|
| Opus alto | la prueba no veía rutas con `include_in_schema=False` (reproducido) | arreglado en `71118ee`, con su sabotaje |
| Opus alto | sin prueba positiva de admin en cache/refresh | `test_admin_refresca_cache_ncm` + sabotaje (`ac25dbc`) |
| Opus alto | una global nueva sin tag no se detecta | límite de diseño, explicado arriba |
| Opus alto / Sonnet alto | `simulate-webhook` activa cobro con sólo el secreto | D2 |
| Opus alto / Sonnet alto | `system/connectors` abierta | D1 |
| Opus alto / Sonnet alto / `/code-review` | `cohort-retention` y `ADMIN_USERNAMES` no coinciden | D3 |
| Opus alto | `ADMIN_USERNAMES` se puede reclamar; `demo` admin | riesgos 2 y 3 |
| Sonnet alto | `/api/dolar`, `/api/ncm/sugerir`, plantillas: llamadas a terceros sin cache del fallo, Gemini que bloquea el servidor y sin corte de cobro, disco | fuera de alcance; `ncm/sugerir` sin corte es de COBRO-CORTE-1 |
| `/code-review high` | script de sabotajes frágil (`pipefail`, «passed» en el texto) | ahora mira el código de salida (`71118ee`) |
| `/code-review high` | docstrings de `/api/dev/stats` y `wave1-kpis` decían «TODO admin» | corregidos (`2d76015`) |
| `/code-review high` | el router se monta en cada arranque | riesgo 4; ya existía |
| `/security-review` | nada ≥ 8/10 introducido por el diff | — |

## Qué no corrí

- Nada contra producción ni contra terceros.
- `ataque_aislamiento.sh` y `smoke_friccion.sh` corrieron sobre `76a2b42`,
  no sobre `ac25dbc`. Entre los dos sólo cambian docstrings y pruebas.
- El panel se probó en Chromium local, no en un teléfono.

## Archivos de producto que toqué

`proyecto_maria/main.py`: lifespan, comentario de `require_admin`, docstrings
de `/api/dev/stats` y `wave1-kpis`, y `/api/ncm/cache/refresh`. También
`CHANGELOG.md`.

## Sigo con

COBRO-CORTE-1, frenada en D4–D6 (arriba).

Última vuelta: 2026-10-07 00:55 UTC
Contexto: ~26 %
