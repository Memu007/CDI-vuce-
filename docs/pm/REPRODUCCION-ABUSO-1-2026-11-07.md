# Reproducción ABUSO-1 (Dev MARIA) — 2026-11-07

Entregado: `55bf408` (devolución sobre `43916a7`; informe `9f996a4` en
`PARA-PM-2.md`). Base de la vuelta: `1f48bb5`.
Entorno de la PM: worktree limpio, venv, sin red, `GEMINI_API_KEY` vacía,
`ENVIRONMENT=testing`, Postgres 16 local.

## Puertas

| Puerta | Informe | PM |
|---|---|---|
| chequeo-6 `1f48bb5 55bf408` | producto `+35/−20`, historia vacía, 0 avisos | igual |
| casos de la pieza | verdes | `72 passed` |
| `compileall` | OK | OK |
| motores (`abuso1_motores.py pg`) | todo OK | `pg: todo OK`, rc=0 |
| sabotajes (`abuso1.sh 55bf408`) | 35 en rojo | 35 `ROJO`, `sabotajes sin rojo: 0`, rc=0 |
| suite completa | `5005 passed, 335 skipped, 3 xfailed` | `1 failed, 5004 passed, 335 skipped, 3 xfailed`, rc=1 |

Los cuatro puntos de la devolución están: D44 (1) probado en PG con 120
logins malos y 120 buenos a la vez; duraciones de 14 y 16 min y de la
ventana; claves de 121 a 300; surrogate suelto en recuperar usuario.

## Adversarios (contexto nuevo, sin red)

Opus alto y Sonnet alto: **nada serio introducido por el diff.** Sin
colapso de usuarios, correos ni tokens; sin evasión del límite.

Introducido, menor (va a ENTRADAS-1):
- el 422 usa `json.dumps` con `allow_nan=True`: un `NaN` o `1e999` en el
  cuerpo da un JSON inválido (la base daba 500);
- `ensure_ascii` hace el eco del 422 unas 3 veces más grande.

De antes, no de la pieza (a piezas nuevas):
- reset con token válido y `new_password` con surrogate o de más de 72
  bytes: 500, y el token no se consume (D94, D96);
- registro con surrogate en nombre o clave: 500 (D96);
- el 422 con cuerpo no JSON de bytes no UTF-8: 500 (`jsonable_encoder`);
- el tope de recuperar usuario se esquiva con `U+0130` (Python `lower` ≠
  PG `lower`), y un tercero puede silenciar el recuperar de otro (3/h por
  correo);
- un login bueno en otra cuenta borra el contador `login:<ip>`: queda sólo
  el 5/min de slowapi, sin el bloqueo de 15 min.

## El rojo de la suite

`tests/test_despacho1b.py::test_las_hojas_leidas_antes_del_corte_dan_sus_productos`:
avisos `leí hasta la hoja 2` y `no pude leer sus productos`, renglones vacíos.
No es de la pieza: el diff sólo toca `main.py` (auth y el 422) y el caso
llama a `leer_despacho` directo. Solo: `1 passed` tres veces; el archivo
entero: `283 passed in 51.13s`; con un hilo girando a la par: `1 passed`
(la hipótesis de CPU de otros hilos no queda probada). Causa sin cerrar: a
la cola de MARIA, sin repetir la suite para tapar el rojo.
