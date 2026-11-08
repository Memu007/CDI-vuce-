# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ENTORNO-3 (D107 a): **entregada** en `fd545c1` (2026-11-08)

Base `a9c4f06`. Sin ENVIRONMENT o con un valor que no es `development`, `test` ni
`testing`, las cuatro puertas que faltaban van como en producción: sin
`FRONTEND_URL` el link de los emails no cae a localhost (la llamada falla), sin
`ALLOWED_ORIGINS` la app no arranca, toda respuesta lleva HSTS y el limitador por
ruta no deja pasar a 127.0.0.1. Las cuatro usan `es_desarrollo()` / `_es_desarrollo()`
de ENTORNO-1, sin regla nueva.

| SHA | qué |
|---|---|
| `c7ec382` | fix: las cuatro puertas + CHANGELOG |
| `63c072d` | fix: los avisos dicen la regla que aplican, no «en produccion» |
| `8c35989` | test: cuatro puertas más en la sonda de entorno |
| `6ddd38a` | test: sabotajes de las cuatro puertas (`entorno3.sh`) |
| `2b7f09a` | test: la sonda del límite con reloj quieto; FRONTEND_URL opcional en la sonda |
| `47e8ca7` | merge de tu `ba3289f` |
| `dbdad51` | test: el sabotaje de FRONTEND_URL anclado en código, no en un comentario |
| `fd545c1` | test: `_entorno_comun.sh` define ALLOWED_ORIGINS (arreglo de una regresión mía, abajo) |

`producto +11/−10`.

## Decisiones

- **D111 — `RateLimitByEndpointMiddleware` no está montado en la app.**
  (`security_middleware.py:165`; `main.py` no lo agrega.) El cambio de ENTORNO-3
  en ese limitador es correcto pero hoy no protege nada.
  (a) dejarlo así y anotarlo en la cola de limpieza; (b) montarlo, pieza aparte
  con sus pruebas (cambia respuestas 429 en rutas de clientes y cálculo);
  (c) borrarlo. **Recomiendo (a)**: montarlo cambia comportamiento visible y el
  login ya tiene sus límites propios (ABUSO-1/2); que la PM decida si vale (b).
- **D112 — sin FRONTEND_URL fuera de desarrollo, tres rutas guardan el token antes de fallar.**
  `request-password-reset` (`main.py` ~1828/1832), la invitación (~10814/10816)
  y verify-email (296, en tarea de fondo) hacen commit del token y después
  llaman a `get_frontend_url()`, que ahora levanta. Queda un token sin email y
  un 500 (o un error en la tarea). No abre nada: es una mala configuración que
  ya daba un link a localhost.
  (a) dejarlo: es una variable obligatoria de despliegue; (b) pieza chica: pedir la URL antes del commit en las tres rutas;
  (c) que la app no arranque sin FRONTEND_URL fuera de desarrollo, como
  ALLOWED_ORIGINS. **Recomiendo (c)**: un solo chequeo, en el arranque, y no hay
  que tocar las tres rutas; pero cambia el arranque, así que es tuya.
- **D113 — `billing_service.py:32-36` tiene su propio `get_frontend_url`.**
  Cae a `http://127.0.0.1:8000` sin mirar el entorno. No lo toqué: no está en
  D107. (a) cola de limpieza; (b) pieza chica: que use el de `main.py` (o uno
  común en `config.py`). **Recomiendo (b)** dentro de la pieza de D112 si sale
  (c), porque es el mismo chequeo.

## Lo que hay que saber

- **Rompí el arnés de ENTORNO-1 y lo arreglé en `fd545c1`.** En `2b7f09a`,
  `entorno1.sh` dio `ROJO?` en «ninguna puerta abre ni en desarrollo»: con
  ENVIRONMENT ausente la app ahora exige ALLOWED_ORIGINS y el arnés no la
  definía (`ValueError: CORS config error: ALLOWED_ORIGINS no puede ser vacio
  ni '*' si ENVIRONMENT no es development, test ni testing...`). `fd545c1` la
  define en `_entorno_comun.sh`; en `fd545c1` los tres arneses dan salida 0.
- **Orden de commits:** el rojo de las cuatro puertas lo corrí sobre la base
  antes de tocar el producto, pero el commit de producto (`c7ec382`) quedó antes
  que el de las pruebas (`8c35989`). La evidencia del rojo es el sabotaje:
  cada uno vuelve a la regla vieja y la prueba falla por esa puerta.
- Quedan monkeypatch de `IS_PRODUCTION` en pruebas viejas (`test_cobro_mp1:38`,
  `test_cobro_mp2:106`, `test_email1:158,216`, `test_prelaunch_block2:242,375,590,635`,
  `test_prelaunch_block3:200–260`) y `main.py:105` sigue definiendo
  `IS_PRODUCTION`. No los toqué: van a la cola de limpieza (lo dice D107).

## Riesgos

- `ALLOWED_ORIGINS='*'` y valores con sólo espacios fuera de desarrollo: el
  código los rechaza, pero no hay caso nuevo para esos dos (la prueba cubre
  vacío).
- HSTS va en toda respuesta fuera de desarrollo, también en un staging por
  HTTP: el navegador lo ignora sin TLS, no rompe.
- D112: con FRONTEND_URL faltante, reset e invitación dan 500 después de
  guardar el token.

## Hallazgos de la autorrevisión

| quién | modelo y esfuerzo | hallazgo | qué hice |
|---|---|---|---|
| adversario | Sonnet alto | sin hallazgos dentro de la pieza | — |
| `/code-review` | high | sin hallazgos confirmados dentro de la pieza | — |
| yo, relectura contra §6 | — | el sabotaje de FRONTEND_URL se anclaba en un comentario | `dbdad51` |
| `/security-review` | — | sin hallazgos | — |
| yo | — | sonda del límite podía partir los 11 pedidos en dos minutos | `2b7f09a` (reloj quieto) |
| yo | — | `entorno1.sh` en `ROJO?` por ALLOWED_ORIGINS | `fd545c1` |
| yo | — | D111, D112, D113 | arriba |

## Puertas

| puerta | SHA | salida |
|---|---|---|
| suite (`pytest -q --no-cov --timeout=300`, entorno del proyecto) | `2b7f09a` | `5201 passed, 335 skipped, 3 xfailed, 97 warnings in 976.75s (0:16:16)`, salida 0 |
| suite como la CI (`env -u DATABASE_URL ENVIRONMENT=testing ...`) | `2b7f09a` | `5201 passed, 335 skipped, 3 xfailed, 97 warnings in 983.93s (0:16:23)`, salida 0 |
| `compileall -q proyecto_maria` | `2b7f09a` | 0 |
| `entorno1.sh` | `fd545c1` | 10 ROJO, salida 0 |
| `entorno2.sh` | `fd545c1` | 8 ROJO, salida 0 |
| `entorno3.sh` | `fd545c1` | 4 ROJO, «sabotajes sin rojo: 0», salida 0 |

`dbdad51` y `fd545c1` sólo cambian scripts de sabotaje: el producto y las
pruebas de pytest son los de `2b7f09a`, así que las suites valen para `fd545c1`.
No corrí smoke ni ataque de aislamiento: no hay cambio de datos ni de rutas.

chequeo-6, entero:

```
chequeo-6 a9c4f06..fd545c1: avisos para mirar, no un veredicto
producto +11/−10
arnés +72/−3
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12047 → 12048
  proyecto_maria/security/security_middleware.py: 238 → 238
avisos: 0
```

## Comandos

```bash
git fetch origin claude/dev-maria && git checkout fd545c1
PY=<venv>/bin/python scripts/testing/sabotajes/entorno3.sh fd545c1   # 4 ROJO, «sabotajes sin rojo: 0»
PY=<venv>/bin/python scripts/testing/sabotajes/entorno1.sh fd545c1   # 10 ROJO, ningún ROJO?, salida 0
PY=<venv>/bin/python -m pytest -q --no-cov tests/test_entorno1.py   # verde
```

## Archivos de producto tocados

`proyecto_maria/main.py`, `proyecto_maria/security/security_middleware.py`.

Sigo con ENTRADAS-3 (D109 a, D110 a).

/compact conservar: Dev MARIA (session_01C8gCBjvn36wnYC6qG2Sixi), rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM session_01B7FVQspcEHF7PqNv797wNM con send_message next. ENTORNO-3 (D107 a) entregada en fd545c1 (base a9c4f06), D111–D113 abiertas, próxima D libre D114. Sigue ENTRADAS-3 (D109 a, D110 a; trabajo sin commitear en el worktree wt_ent3 del scratchpad), después SUFIJOS-2+SEGURO-1 y D102 (fijar bcrypt). Corte de rutinas 2026-11-08 15:50 UTC. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; TXT y proforma reales nunca en el repo.
