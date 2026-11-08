# Reproducción de PERMISOS-3, 2026-11-08

Entrega de la Dev técnica: código en `9428e00` (producto `37cd494` y
`323e6e1`, pruebas `a93b930` y `9428e00`), informe en `e10823e`, base
`7078e3f`. Corrido por la PM desde un worktree de `9428e00`, venv Python 3.12
primero en el `PATH`, sin red y con `GEMINI_API_KEY` vacía.

## Resultado

**Aceptada sobre `9428e00`, sin integrar.** Igual al informe.

| Qué | Salida |
|---|---|
| `chequeo-6.py 7078e3f 9428e00` | `producto +8/−12`, arnés `+43/−4`, historia vacía, avisos 0, salida 0 (igual al informe) |
| `sabotajes/permisos2.sh 9428e00` | 10 `ROJO`, `sabotajes con falla: 0`, salida 0 |
| `pytest --no-cov tests/test_permisos2.py tests/test_admin_solo_admin.py tests/test_admin2.py tests/test_admin_bootstrap.py` | `60 passed`, salida 0 |
| `PUERTO=… ataque_aislamiento.sh` | `Bloqueado: 47 · Fugas: 0 · Sin probar: 0`, salida 0 |

La suite completa no la repetí: la Dev la corrió (4718 passed) y el producto
son 8 líneas netas menos en `main.py`.

## Adversario Sonnet alto

Sin hallazgos graves ni medios. Con `ADMIN_USERNAMES="Emi, admin_x ,ÉMI,emi.k"`
contra `/auth/register` y `/api/organizations/create`:

- 400 «Usuario ya existe»: `emi`, `EMI`, `eMi`, `Emi`, `ADMIN_X`, `admin_x`.
- 400 de formato: `emi\n`, `emi `, `emi\x00`, `emı`, `EMİ`, `KKK` con K de
  Kelvin, `ｅｍｉ`, combinantes Unicode, `emi.k`. La regex ASCII con
  `fullmatch` corta antes de comparar, así que `lower()` no abre trucos.
- Sólo esos dos caminos crean usuarios por la API (las invitaciones entran por
  register); no hay endpoint que renombre.
- Front: `submitAuth` de `landing.html` muestra el `detail` que venga; ningún
  JS ni test depende del texto viejo del alta de estudio.
- Login y cuentas existentes sin cambio: el login no aplica el formato.
- `None`, números, listas y objetos dan 422; vacío, 2, 31 y 5000 caracteres,
  400. Ningún 500.
- Sus pruebas: `449 passed, 12 skipped` sobre los archivos que tocan los dos
  caminos.

Leves, sin acción:

1. «Usuario ya existe» sale ahora antes que el error de email o contraseña.
   No es fuga nueva: eso ya se sabía con una petición correcta.
2. El arranque promueve comparando exacto: `Emi` en la lista no promueve a
   `emi`. Previo y sin puerta abierta.
3. La base deja convivir `Pedro` y `pedro`. Previo; es la D127.

No corrido: Postgres ni nada de producción.
