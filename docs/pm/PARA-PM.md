# Dev 1 → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ADMIN-2 — entregada, terminada

| | SHA |
|---|---|
| Base (mi rama con la tuya traída, `efef997`) | `6c3ba09` |
| Producto | `8808ef8` (fix) + `c08ea3f` (refactor de los conectores) |
| Pruebas y sabotajes | `d74a74f`, `50d3a0b`; agregado 4: `f9f8393` |
| **Entrego (código)** | **`f9f8393`** (trae tu rama: ADMIN-1 aceptada y MARIA-2) |

ADMIN-1 aceptada: gracias. Su informe está en el commit `f413c45` de este
archivo.

**Agregado 4 (de tu revisión de ADMIN-1), hecho en `f9f8393`.** La prueba de
recorrido ahora (a) falla si hay una app montada con `app.mount` sobre
`/api/admin/`, `/api/dev/` o `/dev/` (o por encima de esas rutas, como
`/api`), porque una app montada no hereda `require_admin` y no se puede
recorrer desde afuera, y (b) suma las rutas crudas de Starlette bajo esos
prefijos (`app.router.add_route`, aunque tengan `include_in_schema=False`) a
las que el usuario común tiene que recibir 403. Sabotajes, en
`admin1.sh`:

```
ROJO  | ruta cruda de Starlette en /api/dev, fuera del esquema y abierta: dice «GET /api/dev/cruda → 200»
ROJO  | app montada aparte bajo /api/admin, abierta: dice «apps montadas sobre rutas de admin, sin require_admin: ['/api/admin/montada']»
```

Resultado, punto por punto:
1. `/api/system/connectors`: el usuario común recibe sólo
   `{"vuce":{"mode":…},"tarifar":{"mode":…},"afip":{"mode":…}}`. El admin
   (por rol o por `ADMIN_USERNAMES`) recibe el detalle de antes.
2. `POST /api/payments/simulate-webhook` está borrada (404). Sólo la usaba
   ella misma: ningún script, prueba ni pantalla la llamaba.
3. `cohort-retention` ya no pide el rol aparte. El admin por variable entra.
   La prueba de rutas de admin ahora recorre todas las de lectura también con
   un admin por `ADMIN_USERNAMES`.

## Decisiones

- **D7 — El chip «Sistema/Demo» no existe en pantalla, ni antes ni ahora.**
  `topbar_financials.js` pide los conectores y busca `#tfSystemChip`. Ninguna
  plantilla lo tiene (`git log -S tfSystemChip -- proyecto_maria/templates`
  está vacío), así que sale sin dibujar nada. Por eso no hay captura del chip.
  Mandé la captura de la barra con un usuario común: carga bien, y el pedido
  a los conectores da 200 con sólo los modos. El código del chip lee sólo el
  `mode`, así que si algún día se dibuja, anda.
  Opciones: (a) nada; (b) borrar ese código muerto en una pieza aparte.
  **Recomiendo (a)** por ahora: no molesta y no es de esta cola.
- **D8 — El webhook de MP se puede reenviar (alta, cobro).** Lo encontró el
  revisor Sonnet y lo reprodujo con el SDK de MP simulado. El webhook real
  acepta sin firma el aviso IPN (`?topic=payment&id=…`, `main.py:7810-7830`),
  le pregunta a MP por ese pago, y para no repetir sólo mira el **último**
  pago (`last_payment_id`). Con dos pagos reales viejos que se alternan,
  cualquiera, sin sesión, vuelve a dejar una cuenta vencida en `active` por
  30 días con el contador en 0, o suma `extra_ops` sin pagar.
  En su prueba: `past_due`, 999 operaciones usadas → `active`, 0 usadas, y
  `extra_ops_remaining` 40.
  Opciones: (a) pieza nueva antes de publicar el cobro: guardar todos los
  `payment_id` procesados y rechazar los repetidos; (b) sumarlo a COBRO-MP-1.
  **Recomiendo (a), y que vaya delante de COBRO-CORTE-1** cuando vuelva el
  cobro: es el único camino de esta lista que activa sin pagar en
  producción.
- **D9 — Otros caminos de cobro sin pago real** (Sonnet; ninguno es de
  ADMIN-2):
  - `/api/billing/cancel` y después `/reactivate` pasan una prueba
    gratuita a `active` y le dan 7 días de gracia extra, una sola vez
    (`main.py:2020-2057`).
  - `simulate-charge` y el usuario `demo/demo123` admin quedan abiertos si
    `ENVIRONMENT` no es exactamente `production` (`main.py:85`). Es lo que
    Emi tiene que confirmar en Railway.
  - Sin `MP_ACCESS_TOKEN`, `demo-confirm` y `/api/payments/success` le
    muestran a cualquiera «Tu cuenta Premium ha sido activada», pero en el
    servidor no cambia nada.
  **Recomiendo** sumar el primero y el tercero a COBRO-MP-2. El segundo
  queda como está: Emi ya lo tiene en la lista de Railway.

## Comandos copiables

```bash
git fetch origin claude/dev1-tecnica && git checkout f9f8393
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh f9f8393 8080
# desde el worktree:
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov tests/test_admin2.py tests/test_admin_solo_admin.py  # 27 passed
PY=$(which python) scripts/testing/sabotajes/admin2.sh f9f8393   # 5 «ROJO», «sabotajes con falla: 0»
PY=$(which python) scripts/testing/sabotajes/admin1.sh f9f8393   # 9 «ROJO», «sabotajes con falla: 0»
```

## Evidencia (salida exacta)

**Rojo antes:** las pruebas nuevas sobre el código de la base `6c3ba09`.

```
E   AssertionError: {'vuce': {'mode': 'fake', 'has_api_key': False, 'base_url': 'https://sandbox.vuce.gob.ar/api'}, 'tarifar': {'mode': 'f...0 (+https://cdi.local; contacto: soporte@cdi.local)', 'min_interval_ms': 1000, 'timeout_s': 8, 'cache_ttl_hours': 168}}
E   AssertionError: 200 {"success":true,"payment_id":"sim_69ec9f1c333247f1","billing_status":"active","trial_ends_at":"2026-11-06T00:58:34.011479","extra_ops_remaining":0}
E   AssertionError: /api/admin/cohort-retention: 403 {"detail":"Permisos insuficientes"}
FAILED tests/test_admin2.py::test_conectores_usuario_comun_sin_detalle - Asse...
FAILED tests/test_admin2.py::test_simulate_webhook_ya_no_existe_sin_sesion - ...
FAILED tests/test_admin_solo_admin.py::test_admin_por_admin_usernames_entra[/api/admin/cohort-retention]
=================== 3 failed, 23 passed, 7 warnings in 2.25s ===================
```

El segundo rojo es el de la tarea: sin sesión, con el secreto, una cuenta
`trial` pasó a `active`.

**Verde después**, con la app en :8811 sobre `d74a74f` y un usuario común
nuevo:

```
8811: {"vuce":{"mode":"fake"},"tarifar":{"mode":"fake"},"afip":{"mode":"fake"}}
```

El revisor Opus repitió en :8811: común → sólo modos, sin sesión → 401,
admin → detalle completo, `simulate-webhook` → `{"detail":"Not Found"} 404`,
`cohort-retention` → 403 común / 401 sin sesión / 200 admin. El detalle de
los conectores no aparece en ninguna otra ruta (`/health`,
`/api/financials`).

**Sabotajes** sobre `50d3a0b`:

```
ROJO  | conectores: el usuario común vuelve a ver el detalle: dice «FAILED tests/test_admin2.py::test_conectores_usuario_comun_sin_detalle»
ROJO  | conectores: el admin pierde el detalle: dice «FAILED tests/test_admin2.py::test_conectores_admin_con_detalle»
ROJO  | simulate-webhook vuelve a existir: dice «assert 200 in (404, 405)»
ROJO  | simulate-webhook vuelve: activa la cuenta y responde 404: dice «assert 'active' == 'trial'»
ROJO  | cohort-retention vuelve a pedir el rol: dice «FAILED tests/test_admin_solo_admin.py::test_admin_por_admin_usernames_entra[/api/admin/cohort-retention]»
sabotajes con falla: 0
```

Sobre `f9f8393`, los de ADMIN-2 siguen igual y los 9 de ADMIN-1 (7 + los 2
del agregado) dan ROJO: `sabotajes con falla: 0`.

## Puertas

| Puerta | Resultado |
|---|---|
| Suite completa sobre `f9f8393` (con MARIA-2), worktree limpio | `716 passed, 102 skipped, 25 warnings in 59.15s` |
| Suite completa sobre `50d3a0b` (sin MARIA-2) | `706 passed, 102 skipped, 25 warnings in 58.25s` (694 + 12 nuevas) |
| `compileall` sobre `50d3a0b` | sin errores |
| `smoke_friccion.sh` (`d74a74f`) | `OK · telemetría + alias session/state + by-cuit protegido` |
| `ataque_aislamiento.sh` (`d74a74f`) | 22 BLOQUEADO, 0 FUGA |

## Autorrevisión

| Revisor | Hallazgo | Qué hice |
|---|---|---|
| Opus alto | nada dentro del alcance; la respuesta de conectores cambia según quién pide y no lleva `Cache-Control: private` (hoy no hay cache delante) | informativo, no lo agregué |
| Sonnet alto | reenvío de pagos al webhook (alta) | D8 |
| Sonnet alto | cancel/reactivate, `ENVIRONMENT`, cartel demo | D9 |
| `/code-review high` | la vista común y la del admin eran dos listas a mano | ahora la común sale del detalle (`c08ea3f`) |
| `/code-review high` | el chequeo del estado de la cuenta en la prueba de `simulate-webhook` nunca se vio rojo | sabotaje nuevo que activa y devuelve 404 (`50d3a0b`) |
| `/code-review high` | `cohort-retention` queda sin control propio: depende de cómo se monta el router | lo cubre la prueba que recorre rutas; ponerle `require_admin` en el router trae un import circular con `main.py`, no lo hice |
| `/code-review high` | `cohort-retention` hace 2 consultas por usuario; `admin2.sh` copia a `admin1.sh`; un ayudante de pruebas repetido | fuera de alcance, sin cambio |

## Qué no corrí

- Nada contra producción ni terceros.
- Humo y aislamiento corrieron sobre `d74a74f`; `50d3a0b` sólo cambia cómo se
  arma la respuesta de conectores (misma salida, la cubre la prueba) y un
  sabotaje.
- `/security-review`: no lo corrí en esta pieza. El revisor Sonnet tuvo el
  foco de cobro y seguridad.

## Archivos de producto que toqué

`proyecto_maria/main.py` (`_es_admin`, `/api/system/connectors`, borrado de
`simulate-webhook`), `proyecto_maria/routers/admin_router.py`
(`cohort-retention` y un import), `CHANGELOG.md`.

## Sigo con

RENDIMIENTO-1, como dice tu canal. Antes traigo tu rama por MARIA-2.

Última vuelta: 2026-10-07 01:25 UTC
Contexto: ~32 %

`/compact conservar: Dev 1 de CDI en la rama claude/dev1-tecnica. ADMIN-1
aceptada (ac25dbc). ADMIN-2 entregada con el agregado 4 (código f9f8393), informe en PARA-PM.md con D7–D9. Sigue
RENDIMIENTO-1 (PARA-DEV.md; después DEPENDENCIAS-1, EXCEL-1, MARIA-1b,
PUNTA-A-PUNTA-1): asyncio.to_thread para process_pdf,
_extract_pdf_text y _suggest_ncm_with_gemini, con tiempo máximo; MARIA-2 ya
está integrada en mi rama. COBRO-CORTE-1 en pausa, con
D4=(b) N=10, D5=(a), D6=(a). Entorno: PM_DIR=/tmp/cdi-dev1, levantar.sh
<SHA> 8811; venv /tmp/cdi-dev1/venv; sabotajes en
scripts/testing/sabotajes/admin1.sh y admin2.sh. Rutina de la PM:
trig_01TvMmGfSLDfbcJrf66ZZ7YK.`
