# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ENTORNO-4 (D112 c, D113 b): **entregada** en `44b9759` (2026-11-08)

Base `4a6fdcd`. Fuera de `development`, `test` o `testing`, sin `FRONTEND_URL`
la app no arranca, igual que sin `ALLOWED_ORIGINS`. Una `FRONTEND_URL` con
sólo espacios cuenta como vacía. La vuelta de los dos cobros de Mercado Pago
(plan y recarga) usa la misma URL que los emails y ya no cae a localhost.

`get_frontend_url` vive ahora una sola vez, en `config.py`. Salieron las dos
copias: la de `main.py` y la de `billing_service.py`, que caía a
`127.0.0.1:8000` sin avisar. `main.py` la llama al arrancar, después del
bloque de CORS.

`docker-compose.yml` no levanta sin `FRONTEND_URL`, y `preflight_env.sh` avisa
si falta o si no es https.

| SHA | qué |
|---|---|
| `eefa383` | fix: sin `FRONTEND_URL` fuera de desarrollo no arranca; el cobro usa la misma URL + CHANGELOG |
| `07f3ab4` | test: la sonda mide el arranque sin `FRONTEND_URL` y la URL del cobro |
| `dfc1a13` | test: el arnés de ENTORNO exporta `FRONTEND_URL` |
| `7b64a54` | test: la sonda mide la vuelta de los dos cobros y la URL con sólo espacios |
| `a943321` | fix: URL con sólo espacios cuenta como vacía; compose y preflight la traen |
| `c127943` | test: sabotaje de la URL con sólo espacios |
| `907069a` | fix: el chequeo va después de CORS; compose la exige; preflight recorta sólo los bordes |
| `44b9759` | test: la sonda cuenta como rechazo sólo el error de `FRONTEND_URL` |

`producto +19/−26`: resta, porque unifiqué tres copias en una.

**Nada para decidir.** Supuestos reversibles, fuera de lo pedido al pie de la letra:

- `compose` y `preflight_env.sh`. La tarea nombra la app y `billing_service`;
  los toqué porque si no, `docker compose up` levantaba una app que aborta
  sola.
- La caída de desarrollo del cobro pasa de `:8000` a `:8010`, la misma que ya
  usaban los emails. Es consecuencia de usar una sola URL.

D115 (a) y D117 (a): las tomé como decididas (`194603c`). D117 (a) es
ENTRADAS-4, que sigue.

## Lo que hay que saber

- **Railway necesita `FRONTEND_URL` antes de publicar este SHA.** Si no la
  tiene, el deploy no arranca. Antes arrancaba y el link del reset salía
  roto al mandarlo.
- Con `FRONTEND_URL` y `ALLOWED_ORIGINS` faltando a la vez, el primer
  arranque fallido nombra `ALLOWED_ORIGINS`. Hacen falta dos intentos para
  ver las dos. `preflight_env.sh` nombra las dos de una vez.
- El chequeo no mira el esquema: `FRONTEND_URL=cdi.com` arranca. `preflight`
  avisa si no es https, pero no frena.

## Riesgos

- Sin validación de esquema en la app (arriba). Riesgo bajo: lo pone quien
  despliega.
- `docker-compose.yml:61` ya tenía, desde antes, el mismo error con
  `JWT_SECRET_KEY`. El mensaje de `:?` lleva «:» adentro y compose lo corta.
  En `FRONTEND_URL` lo evité con «p.ej.». El de `JWT_SECRET_KEY` no lo toqué:
  está fuera de la pieza.
- La ruta de suscripción (preapproval) no se mide por separado. Usa el mismo
  `base_url` que el plan, que sí se mide.

## Hallazgos de la autorrevisión

| quién | modelo y esfuerzo | hallazgo | qué hice |
|---|---|---|---|
| adversario | Sonnet alto | `FRONTEND_URL` con sólo espacios pasaba como URL | `a943321` + sabotaje `c127943` |
| adversario | Sonnet alto | compose y preflight no la traían | `a943321` |
| adversario | Sonnet alto | `planes_y_cobros.md` decía «No» obligatoria y `:8000` | `a943321` |
| adversario | Sonnet alto | un sabotaje dependía de una variable puesta en línea | `7b64a54` |
| `/code-review` | high | compose tenía localhost fijo | `907069a` |
| `/code-review` | high | la sonda tomaba cualquier `RuntimeError` como rechazo | `44b9759` |
| `/code-review` | high | preflight sacaba también los espacios de adentro | `907069a` |
| `/code-review` | high | el chequeo partía el bloque de CORS | `907069a` |
| `/code-review` | high | comentario viejo con `8000` | `44b9759` |
| `/code-review` | high | no valida esquema | riesgo, arriba |
| `/code-review` | high | la cabecera de preflight no nombraba `FRONTEND_URL` | `907069a` |
| `/code-review` | high | preapproval no se mide | no: comparte `base_url` con lo medido |
| `/code-review` | high | la sonda suma un subproceso | no: ~22 s en total |

## Puertas

Todas sobre `44b9759`, desde worktree limpio, una a la vez; logs en el scratchpad.

| puerta | salida exacta |
|---|---|
| `compileall -q proyecto_maria` | `compileall 0` |
| suite, SQLite (`ENVIRONMENT=test`, `--timeout=300`) | `5214 passed, 335 skipped, 3 xfailed, 96 warnings in 1004.96s (0:16:44)`, `SALIDA suite_mia 0` |
| suite como la CI (`ENVIRONMENT=testing`, sin `DATABASE_URL`) | `5214 passed, 335 skipped, 3 xfailed, 93 warnings in 981.84s (0:16:21)`, `SALIDA suite_ci 0` |
| `test_entorno1.py` + `test_billing_checkout.py` | `36 passed, 3 warnings in 22.15s` |
| sabotajes `entorno1.sh` · `entorno2.sh` · `entorno3.sh` · `entorno4.sh` | 10 · 8 · 4 · 4 `ROJO`; cada uno `sabotajes sin rojo: 0`, `salida 0` |
| grep de historia de §6 | vacío |

Rojo del caso nuevo con el producto sin el arreglo. Son las pruebas de
`44b9759` con `proyecto_maria/` de `4a6fdcd`, copiado del log:

```
FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[frontend_en_localhost]
FAILED tests/test_entorno1.py::test_puerta_cerrada_fuera_de_desarrollo[arranca_sin_frontend_url]
FAILED tests/test_entorno1.py::test_puerta_abierta_en_desarrollo[frontend_en_localhost]
================== 3 failed, 33 passed, 5 warnings in 21.39s ===================
```

`arranca_sin_frontend_url` daba `'abierta'` en los ocho valores de
`ENVIRONMENT` de fuera de desarrollo. `frontend_en_localhost` daba
`'sin medir'`: el cobro no pasaba por `get_frontend_url`.

No corrí `smoke_friccion.sh` ni `ataque_aislamiento.sh`. La pieza no toca
rutas, sesión ni permisos: toca el arranque, y eso lo mide la sonda en un
proceso aparte.

chequeo-6, entero:

```
chequeo-6 4a6fdcd..44b9759: avisos para mirar, no un veredicto
producto +19/−26
arnés +76/−10
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/config.py: 51 → 64
  proyecto_maria/main.py: 12075 → 12060
  proyecto_maria/services/billing_service.py: 412 → 407
avisos: 0
```

## Comandos

```bash
git fetch origin claude/dev-maria && git checkout 44b9759
PY=<venv>/bin/python scripts/testing/sabotajes/entorno4.sh 44b9759   # 4 ROJO, «sabotajes sin rojo: 0»
PY=<venv>/bin/python scripts/testing/sabotajes/entorno3.sh 44b9759   # 4 ROJO, «sabotajes sin rojo: 0»
<venv>/bin/python -m pytest -q --no-cov tests/test_entorno1.py tests/test_billing_checkout.py   # 36 passed
# ENTRADAS-3 necesita un Postgres local; sin PG_URL sale al empezar:
PY=<venv>/bin/python PG_URL=postgresql://cdi@127.0.0.1:55432/postgres scripts/testing/sabotajes/entradas3.sh
```

## Archivos de producto tocados

`proyecto_maria/config.py`, `proyecto_maria/main.py`,
`proyecto_maria/services/billing_service.py`, `docker-compose.yml`,
`scripts/deployment/preflight_env.sh`, `docs/billing/planes_y_cobros.md`,
`CHANGELOG.md`.

Sigo con ENTRADAS-4 (D117 a).

/compact conservar: Dev MARIA (session_01C8gCBjvn36wnYC6qG2Sixi), rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM session_01B7FVQspcEHF7PqNv797wNM con send_message next. ENTORNO-4 entregada en 44b9759 (base 4a6fdcd). D115 a y D117 a decididas; próxima D libre D118. Sigue ENTRADAS-4 (producto en main.py:9068 TextoCodificable en cliente_id; arnés entradas4_postgres.py + sabotajes/entradas4.sh, verdes en el commit temporal 8d2e45e), después SUFIJOS-2+SEGURO-1, SEGURO-2, EMAIL-1, CONEXIONES-1, OBSERVABILIDAD-1, ORG-1+D40 y D102. Corte de rutinas 2026-11-08 15:50 UTC. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; TXT y proforma reales nunca en el repo.
