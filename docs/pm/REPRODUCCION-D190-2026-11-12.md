# D190 (Técnica): las seis pantallas usan `_ip_nueva`, aceptada sobre `0b92e6d8`

2026-11-12, PM principal. Corrido en un worktree aparte sobre `0b92e6d8`, con
la venv `/tmp/cdi-pm/venv`, de 16:50 a 17:41 UTC. Informe de la Dev: `5a1a5a8b`.

## Lo reproducido

- **`grep`** de la Dev: sólo `_ip_nueva.js:3` y `pantalla_orden1.js:1343`.
- **`node --check`** de las seis: OK.
- **`_ip_nueva`:** 1000 llamadas, 1000 valores distintos.
- **`chequeo-6 c8247e95 0b92e6d8`:** producto +0/−0, arnés +272/−12, 0
  avisos. Igual al informe.
- **Parche `conexiones1_tests.diff`:** `git apply --check` da 0 y crea
  `tests/test_conexiones1.py`. Corrido sin el arreglo de producto, como se
  espera: 7 rojos y 1 verde
  (`test_ncm_con_la_base_caida_al_soltarla_sigue_sugiriendo`). El primer
  rojo dice `conexiones tomadas en _suggest_ncm_with_gemini: [1]`, que es lo
  que el arreglo tiene que bajar a 0.
- **`anclas_perdidas.py` sobre `0b92e6d8`:** 28 perdidas en 9 guiones,
  ninguna de un guion de D190 (son los vencidos ya anotados y `finalize.js`).

## Mi rojo (otro borde que el de la Dev)

La Dev lo mostró con `pantalla_estudio1b.js` (corridas 6 y 7). Yo corrí
`pantalla_estudio1.js`, que registra dos cuentas por corrida, cuatro veces
contra una sola base (puerto 8793, `ENVIRONMENT=development`):

| IP | corrida 1 | 2 | 3 | 4 | 429 de `/auth/register` |
|---|---|---|---|---|---|
| `_ip_nueva` | OK | OK | OK | OK | 0 |
| fija `10.0.0.1` | OK | OK | rc=1 `registro sin perfil: 429` | rc=1 `registro: 429 … Demasiados registros desde esta conexión` | 2 |

Falla en la corrida 3, como da la cuenta: 5 registros por hora y por IP, 2
por corrida. En las dos fases hay además 429 en `POST /api/session/state`
(68 con `_ip_nueva`, 12 con la IP fija): es la telemetría de la página, no
el registro, y la pantalla pasa igual.

## Las pantallas sin los sabotajes

Cada pantalla tocada, sin sabotajes, sobre una base nueva:

| pantalla | corridas | resultado | 429 fuera de la telemetría |
|---|---|---|---|
| `orden1` | 4 seguidas, una base | las 4 rc=0 | 0 (106 de `/api/session/state`) |
| `cliente1` | 1 (con `CDI_DB`) | rc=0, `PANTALLA CLIENTE-1 OK (con CLIENTE-1b y 1c)` | 0 |
| `despacho1a` | 1 | rc=0 | 0 |
| `destino1` | 1 | rc=0 | 0 |
| `estudio1b` | 1 | rc=0, `PANTALLA ESTUDIO-1b OK` | 0 |

El `192.0.2.` que queda no llega al límite de `/auth/login` por la cuenta,
no por la corrida: el límite es 5 por minuto y por IP, cada IP se usa una vez
por corrida y una corrida de `orden1` tarda ~9 min. Las cuatro corridas son
una observación; no podían fallar por eso. La primera corrida de `cliente1` dio rc=1 porque
mi guion no le pasaba `CDI_DB`; error mío, no de la entrega.

## No corrido

- Los 9 guiones de sabotaje: los corrió la Dev (todos rc=0, sabotajes sin
  rojo 0); yo corrí las pantallas solas.
- El `cmp` del parche contra el archivo de la Dev: el original está sólo en
  su contenedor.
- La suite: producto +0/−0 y nada en `tests/`.

## Escape

Ninguno.
