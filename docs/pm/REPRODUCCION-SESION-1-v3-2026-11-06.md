# SESION-1 (vuelta 3): reproducción de la PM, 2026-11-06

Producto `2e62761`, informe `9b2580b` (corregido en `195b96c`), base `fb75e41`.
Rama `claude/dev-maria`. Entorno: venv Python 3.12 con pypdf 6.21.4, Postgres
16 local descartable, SQLite para pytest. Sin red.

**Veredicto: aceptada, sin integrar.** Las dos causas de la vuelta 2 quedan
cerradas y los menores también. No se integra todavía: debajo de `2e62761`
vienen commits de piezas sin aceptar (CATALOGO-LARGO-2, SUFIJOS-2, ABUSO-1,
OBSERVABILIDAD-1, ORG-1), igual que con `ca87d82`.

## Lo que coincide con el informe

| Puerta | Resultado PM |
|---|---|
| `tests/test_sesion1.py` en `2e62761` | `42 passed` |
| la misma prueba en la base | `13 failed, 29 passed` (distingue) |
| `sesion1_motores.py pg` | `pg: todo OK`, rc=0; fila 7 entera OK, otro usuario entra en 0,7 a 1,4 s |
| `sabotajes/sesion1.sh 2e62761` | 38 `ROJO`, `sabotajes sin rojo: 0`, salida 0 |
| `chequeo-6.py fb75e41 2e62761` | `producto +95/−89`, historia vacía, `avisos: 0` |
| suite completa en `2e62761` | `5 failed, 4933 passed, 355 skipped, 3 xfailed` en 726 s |

Las 5 fallas de la suite son las de D73 (`test_despacho1b.py` ×3,
`test_rendimiento1c.py` ×2): pypdf 6.21.4, rojas también en la base.

## Negativo propio y ejemplo distinto

- `test_pm_ses1_neg.py` (scratchpad, no en el repo), adaptado a
  `settings.jwt_secret`/`jwt_algorithm` porque la pieza sacó `SECRET_KEY`:
  `2 passed` en `2e62761`.
- Pool, con otro ejemplo que el de la devolución (40 `PUT /api/user/profile`
  con clave mala, Postgres):
  - `2e62761`: `{400: 5, 429: 35}`, máximo 0,8 s, otro usuario `(200, 0.0)`;
  - base: `{500: 39, 400: 1}`, otro usuario `(200, 29.5)`.

## Adversarios (contexto nuevo, sin red)

**Opus alto, familia de la clave.** Las causas de la pieza aguantan. Tres
hallazgos de antes, en la base también:

1. **Alto.** Un link de reset viejo toma la cuenta aunque el dueño haya
   cambiado clave y email después: `reset_password` (`main.py:1774-1805`) no
   invalida los tokens de reset al cambiar clave o email.
2. El mismo token de reset se puede usar dos veces (no se consume atómico).
3. La verificación de email no queda atada al email. Ya está en la cola.

1 y 2 van a una pieza chica nueva, **RESET-1** («arreglos chicos de seguridad
a cero», Emi). Decidido por la PM.

**Sonnet alto, conexiones.** De antes, mejorado por la pieza, entra en
CONEXIONES-1:

- `/api/ncm/sugerir` tiene la conexión tomada durante Gemini
  (`require_billing_vigente`, `main.py:2133`). Con 120 pedidos y una espera de
  10 s: 45 respuestas 500 y otro usuario espera 27,8 s. En la base, todo 500.
- El login con un usuario real tiene la conexión durante bcrypt: otro usuario
  entra en 3,3 a 10,8 s, sin 500 (D74 de la Dev).
- `/upload_pdf/public` igual.
- Los dos `get_db` no hacen daño (D75). El commit temprano de
  `get_current_user` es seguro: devuelve un dict y `expire_on_commit=False`.

Un incidente del adversario Sonnet: llamó una vez a la API real de Google con
la clave falsa `test-key` («API key not valid»). No se usó ningún secreto.
Repitió con `GEMINI_API_KEY` vacía. Desde acá, todo adversario lleva
`GEMINI_API_KEY` vacía y `process_pdf` falso.

## Pendiente al integrar

Actualizar las anclas de `scripts/testing/sabotajes/csrf3.sh` que mueve la
pieza, y correrlo una vez sobre el SHA integrado.
