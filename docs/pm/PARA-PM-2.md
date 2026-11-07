# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ENTORNO-1: **entregada**. Base `9f996a4`. SHA entregado `83085e4` más el informe (2026-11-07)

| Qué | SHAs |
|---|---|
| Producto | `118447a` (puertas), `dcc9bd5` (clave JWT) |
| Pruebas y negativos | `d74a5df`, `66df521`, `e358942`, `86b9240`, `a767154`, `8082c99`, `d985df1`, `b907e96`, `83085e4` |
| Suite completa | sobre `83085e4`: `5017 passed, 335 skipped, 3 xfailed` en 12:48, 0 failed |
| Informe | el commit `docs:` que sigue a `83085e4` |

**Resultado.** Hay un solo lugar que dice «esto es desarrollo»:
`_es_desarrollo()` en `proyecto_maria/main.py`, y es
`os.getenv("ENVIRONMENT") in ("development", "test", "testing")`. Exige el
valor tal cual: no recorta espacios, no ignora mayúsculas y no tiene un valor
por defecto. Reemplaza a `_demo_permitida`, que se borró. Seis puertas
dependen de él, y con `ENVIRONMENT` ausente, vacío, `production`, `prod`,
`staging`, `Development`, ` development` o `TESTING` ninguna abre:

1. el login con la contraseña guardada tal cual (el hash como contraseña);
2. los usuarios demo `demo`, `premium` y `basico`;
3. el webhook de MP sin `MP_WEBHOOK_SECRET`, que acepta cualquier firma;
4. el link de reset que se imprimía por consola sin SMTP;
5. `simulate-charge`, demo-checkout, demo-confirm y la demo de
   billing_checkout (supuesto S1);
6. la clave JWT por defecto o débil: fuera de desarrollo, la app no arranca
   (D97).

Las seis siguen abiertas con `development`, `test` y `testing`. Ese es el
contrapunto, y muestra que la prueba distingue.

**Prueba.** `tests/test_entorno1.py`, un caso por causa: puerta cerrada fuera
de desarrollo y puerta abierta en desarrollo, parametrizados por puerta. La
familia de valores de `ENVIRONMENT` va como datos en `CERRADOS` y `ABIERTOS`.

Cada valor corre en un proceso aparte (`tests/entorno_sonda.py`), porque las
banderas se leen al importar la app y un monkeypatch de `IS_PRODUCTION` no
prueba lo que pasa al arrancar sin la variable. La sonda sella `dotenv`: un
`.env` local con `ENVIRONMENT=development` no puede completar la variable que
la prueba deja afuera. La evidencia está más abajo.

## Decisiones

- **D97. Sin `ENVIRONMENT` y con la clave JWT por defecto o débil, ¿la app
  no arranca?** Hoy, en `dcc9bd5`, no arranca: levanta `ValueError`
  «insecure JWT_SECRET_KEY». Antes ese freno existía sólo con
  `ENVIRONMENT=production`.
  - (a) Dejarlo así. Es reversible y cierra que alguien firme sesiones con la
    clave que está en el repositorio.
  - (b) Ir más amplio: `IS_PRODUCTION = not _es_desarrollo()`. Eso afecta
    también el CSRF, las cookies Secure y /docs, que hoy miran
    `IS_PRODUCTION`. Es lo de D98.
  - (c) Volver al freno sólo con `production`.

  **Recomiendo (a).** Cierra la puerta sin cambiar otro comportamiento.
  **Antes de publicar**, mirá en Railway que `ENVIRONMENT=production` y que
  `JWT_SECRET_KEY` sea fuerte: si falta la variable y la clave es la de
  desarrollo, el deploy no levanta (riesgo R1).
- **D98. Otros controles siguen mirando `== "production"`.** Lo encontró
  `/code-review`.
  - `IS_PRODUCTION` decide el CSRF en report-only, las cookies sin `Secure`
    y si /docs queda expuesto.
  - `connection.py:26` cae a SQLite sin `ENVIRONMENT`.
  - `vuce_connector.py:67` aborta el modo fake sólo en `production`.
  - `gunicorn_conf.py:18,47` deja auto-reload si falta `ENVIRONMENT`.
    Railway usa el Dockerfile, así que es bajo.

  Ninguno es una puerta de desarrollo de las cuatro de la tarea. Opciones:
  (a) una pieza aparte que pase esos usos a `not _es_desarrollo()`, con su
  prueba; (b) dejarlo. **Recomiendo (a), después de D99.**
- **D99. Usuarios demo que ya existan en producción.** Severidad **alta**,
  decide Emi.
  - Si producción arrancó alguna vez sin `ENVIRONMENT`, el lifespan viejo creó
    `demo/demo123` con rol admin, más `premium` y `basico`.
  - Esta pieza impide que se creen de nuevo, pero no borra los que ya estén.
  - No lo puedo ver: no toco producción.
  - Opciones: (a) que la PM o Emi revise la tabla `users` de producción y
    desactive las cuentas si están; (b) una migración que las desactive por
    nombre y por hash conocido; (c) dejarlo.
  - **Recomiendo (a) ya**, y (b) sólo si aparecen.

## Supuestos (reversibles)

- **S1.** Sumé `simulate-charge` como puerta, aunque la tarea no la nombra. Ya
  tenía su propio freno, `ENABLE_SIMULATE_CHARGE`, pero abría con
  `ENVIRONMENT` ausente. El checkout demo usa el mismo `_es_desarrollo`.
- **S2.** `test` cuenta como desarrollo, igual que `testing` y `development`:
  la suite y los scripts usan `ENVIRONMENT=test`. D93 (a) se respeta: el script
  manual sigue con `testing` y no lo toqué.
- **S3.** Sin `ENVIRONMENT`, la app arranca igual, con las puertas cerradas,
  salvo que la clave JWT sea la por defecto o débil (D97).
- **S4.** `.env.example:9` sigue diciendo «Options: development, staging,
  production». No lo toqué: `staging` es válido, sólo que no es desarrollo.

## Rojo antes del arreglo

Sobre `d74a5df` (pruebas sin producto), `$S/entorno1_rojo.txt`:

```
E   AssertionError: demo abre con ENVIRONMENT en [None, '', 'prod', 'staging', 'Development', ' development', 'TESTING']
5 failed, 5 passed, 3 warnings in 34.97s
```

Dio el mismo texto para `login_con_lo_guardado`, `webhook_sin_secreto`,
`link_de_reset_en_stdout` y `cobro_simulado`. `production` no aparece en la
lista porque ya estaba cerrada.

El caso de la JWT, sobre `a767154`, `$S/entorno1_rojo_jwt.txt`:

```
AssertionError: clave_jwt_de_desarrollo no queda cerrada: {None: 'abierta', '': 'abierta', 'prod': 'abierta', 'staging': 'abierta', 'Development': 'abierta', ' development': 'abierta', 'TESTING': 'abierta'}
1 failed, 11 passed
```

El sello de `.env`, en `$S/entorno1_sello_env.txt`: con un `.env` que trae
`ENVIRONMENT=development`, la sonda sin sello da
`5 failed, 5 passed, 3 warnings in 8.87s` con `{None: 'abierta'}`, y con el
sello da `10 passed, 3 warnings in 7.73s`. Sin el sello, la prueba habría
quedado verde en una máquina con `.env` aunque el producto estuviera roto.

## Negativos

`scripts/testing/sabotajes/entorno1.sh` da **10 ROJO**, «sabotajes sin rojo:
0» (`$S/entorno1_sabotajes.txt`):

- Cada una de las seis puertas, vuelta a la condición vieja («abierta salvo
  con `production`»), da su propio FAILED con los siete valores abiertos.
- El lugar único, aflojado de tres formas:
  - sin mirar mayúsculas ni espacios:
    `cobro_simulado no queda cerrada: {'Development': 'abierta', ' development': 'abierta', 'TESTING': 'abierta'}`;
  - con `staging` como desarrollo:
    `webhook_sin_secreto no queda cerrada: {'staging': 'abierta'}`;
  - con la variable ausente como desarrollo:
    `login_con_lo_guardado no queda cerrada: {None: 'abierta'}`.
- El contrapunto: con `return False`, nada abre ni en desarrollo, y da
  `demo no queda abierta: {'development': 'cerrada', 'test': 'cerrada', 'testing': 'cerrada'}`.

Al sacar `_demo_permitida`, los patrones de `cobro_mp2.sh` quedaron rotos.
`83085e4` los apunta a `_es_desarrollo`. Resultado: BASE en verde, **23
ROJO**, «sabotajes con falla: 0» (`$S/cobro_mp2_sabotajes.txt`).

`email1.sh` da `ROTO  | la invitación busca al miembro tal cual: el sabotaje
no encontró su patrón` y «sabotajes sin rojo: 1». Da lo mismo sobre la base
`9f996a4` (`$S/email1_sabotajes_base.txt`), así que es anterior a esta pieza.
EMAIL-1 no se toca: queda como riesgo R3.

## Autorrevisión

| Revisor | Modelo y esfuerzo | Hallazgo | Qué hice |
|---|---|---|---|
| `/code-review high` | el de la sesión, alto | clave JWT por defecto aceptada sin `ENVIRONMENT` | arreglado, `a767154`→`dcc9bd5` (D97) |
| ídem | ídem | `.env` local se colaba en la sonda | arreglado: sello de `dotenv` |
| ídem | ídem | once arranques seguidos podían pasar el tope de tiempo | arreglado: sondas en paralelo, de a 4 |
| ídem | ídem | predicados flojos: una respuesta rara contaba como cerrada | arreglado: «sin medir» no cuenta como cerrada |
| ídem | ídem | `cd` sin control en el script | arreglado: `cd "$WT" \|\| exit 2` |
| ídem | ídem | CSRF report-only, cookies sin Secure, /docs sin `ENVIRONMENT` | D98 |
| ídem | ídem | usuarios demo ya creados en producción | D99, alta |
| ídem | ídem | rate limiter con bypass de localhost | no montado; riesgo bajo, R4 |
| ídem | ídem | pruebas que parchean `IS_PRODUCTION` dan falsa seguridad | riesgo R2 |
| adversario-sonnet-alto | Sonnet, alto | `connection.py:26` y `vuce_connector.py:67` | bajos, van en D98 |
| `/security-review` (adversario-sonnet-alto) | Sonnet, alto | ninguno por encima del 80% | — |

La revisión de seguridad comprobó tres cosas:

- `_es_desarrollo` se define antes del chequeo de la JWT al importar; los
  demás usos son en tiempo de llamada.
- Las lecturas `== "testing"` que quedan son un subconjunto de desarrollo.
- El camino IPN del webhook no cambió: vuelve a consultar el pago a MP y exige
  `approved`.

**Flake propio, ya diagnosticado.** Una corrida dio rojo intermitente:
`tmp_path_factory.mktemp` llamado desde los hilos del pool chocaba al crear la
carpeta. `b907e96` crea las carpetas antes del pool. No es de entorno, era de
mi prueba.

## Puertas

| Puerta | Sobre | Resultado |
|---|---|---|
| `pytest` completo | `83085e4`, worktree limpio | `5017 passed, 335 skipped, 3 xfailed, 99 warnings in 768.46s (0:12:48)` |
| `tests/test_entorno1.py` | `83085e4` | `12 passed, 3 warnings in 11.90s` |
| `compileall -q proyecto_maria` | `83085e4` | salida 0 |
| sabotajes `entorno1.sh` | `83085e4` | 10 ROJO, 0 sin rojo |
| sabotajes `cobro_mp2.sh` | `83085e4` | 23 ROJO, 0 con falla |
| `smoke_friccion.sh`, `ataque_aislamiento.sh` | — | **no corridos** |

Los dos últimos no los corrí. Esta pieza no toca rutas ni aislamiento de
datos; cambia la condición de seis puertas, y la sonda las ejercita con la app
arrancada de verdad en cada valor.

## chequeo-6

```
chequeo-6 9f996a4..HEAD: avisos para mirar, no un veredicto
producto +23/−24
arnés +291/−7
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11965 → 11964
avisos: 0
```

## Riesgos

- **R1 (alto si se cumple).** Si Railway corre sin `ENVIRONMENT=production` y
  con la clave JWT por defecto o débil, la app ahora no arranca. Hay que
  verificarlo antes de publicar (D97).
- **R2.** `test_email1.py:158`, de EMAIL-1 y fuera de alcance, y
  `TestProduccionDemoUsers` de block3 parchean `IS_PRODUCTION`: no prueban el
  arranque real. La de block3 es tautológica. La prueba que vale para esto es
  `test_entorno1.py`.
- **R3.** El sabotaje de la invitación en `email1.sh` está roto desde antes de
  esta pieza.
- **R4 (bajo).** El rate limiter tiene bypass de localhost, pero el middleware
  no está montado.
- **R5 (funcional).** Sin `ENVIRONMENT` ni `FRONTEND_URL`, el link de reset
  apunta a `127.0.0.1:8010`. No es de seguridad.

## Comandos copiables

```bash
cd <worktree en 83085e4 o el SHA del informe>
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov tests/test_entorno1.py          # 12 passed (6 puertas × cerrada y abierta)
PY=$(which python) scripts/testing/sabotajes/entorno1.sh      # 10 «ROJO  |», última línea «sabotajes sin rojo: 0»
PY=$(which python) scripts/testing/sabotajes/cobro_mp2.sh     # «BASE  | en verde», 23 «ROJO  |», «sabotajes con falla: 0»
git diff 9f996a4 83085e4 -- proyecto_maria/ | grep '^+' | grep -E '[A-Z]{4,}(-[A-Z]{2,})*-[0-9]|caso [0-9]'   # vacío
```

## Archivos de producto tocados

- `proyecto_maria/main.py`

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP, aviso a la PM session_01B7FVQspcEHF7PqNv797WNM priority next. ENTORNO-1 ENTREGADA sobre 83085e4 (producto 118447a/dcc9bd5: _es_desarrollo() único en main.py, seis puertas cerradas sin ENVIRONMENT explícito, JWT débil frena el arranque fuera de desarrollo). D abiertas: D97 (freno JWT sin ENVIRONMENT, recomiendo a; verificar Railway), D98 (IS_PRODUCTION en CSRF/cookies/docs/connection/vuce), D99 (usuarios demo ya creados en producción, alta, decide Emi). Próxima D libre D100. Sigue: ENTRADAS-1 → ABUSO-2 → rojo de despacho1b. ABUSO-1 aceptada sobre 55bf408 (D94 a, D95 a, D96 a). Reglas de Emi: nada se publica sin su «dale» para el SHA (no propongo SHA), nunca main, nunca force/amend de lo pusheado, sin secretos ni datos reales, subagentes hasta alto sin Fable, no uso advisor, Postgres local 55432.
