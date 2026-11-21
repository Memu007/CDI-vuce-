# La lista de usuarios en Postgres 16: `3abb203d` (informe `d451a007`), 2026-11-21, PM

**Veredicto: aceptada**, integrada con el merge de `d451a007` (`9c5fbfc4`). Base `840cd8f5`. Sólo
pruebas (`producto +0/−0`). Sin publicar y fuera de la candidata `0d7401ed`: con esto,
ADMIN-USUARIOS-1 y D278 (b) pueden entrar a la próxima.

## Diff

`git diff 3abb203d d451a007 -- . ':!docs/pm'` y `git diff 3abb203d 9c5fbfc4 -- . ':!docs/pm'` vacíos.
`chequeo-6.py 840cd8f5 3abb203d` igual al informe: «producto +0/−0», «arnés +192/−20», historia
vacía, «avisos: 0». Archivos: `scripts/testing/admin_usuarios1_postgres.py` (nuevo) y
`tests/test_admin_usuarios1.py`.

## Lo que corrí (worktrees en `3abb203d`, PG16 descartable con `con_pg16.sh`)

| Qué | Resultado |
|---|---|
| `admin_usuarios1_postgres.py` sobre el SHA | 9 casos, «el guion corrió 9 casos y pytest junta 9», «fallas: 0», rc=0 |
| el mismo con `admin_router.py` de `a17011d1` | «fallas: 1» (las 4 cuentas de la familia `COBROS`), rc=1 |
| casos de admin en SQLite | `134 passed, 18 warnings`, rc=0 (ella: 19; todos de deprecación y de usuario: utcnow, crypt, httpx, Operation ID repetido, SECRET_KEY débil) |
| pruebas que recorren el repositorio | `90 passed` |
| `anclas_perdidas.py` | 0 perdidas, 5 no medido, 6 «SIN ANCLA» (`limpieza1.sh`), igual al informe |
| `sabotajes/admin_usuarios1.sh` con la copia del SHA | 31 ROJO, «sabotajes sin rojo: 0», rc=0, 157 s |

## Mis negativos (no van al repositorio)

1. **Mirar escribe.** Un `UPDATE` a `past_due` dentro de la lista: rojo sólo en
   `test_mirar_no_cambia_la_base` (leída por otra conexión de Postgres); la familia `COBROS` sigue
   verde. Es de la misma clase que el «mirar guarda» de su Sonnet, con otra escritura.
2. **Un caso dentro de una clase.** `TestDeLaPM::test_falla_en_clase`: el guion lo saltea y la
   comparación con `pytest --collect-only` lo marca («sólo pytest: [...]», «FALLA»), rc=1.

## No corrido por la PM

Adversario y `/code-review`: sólo pruebas, `producto +0/−0`, y ella ya pasó Sonnet alto dos veces,
Sonnet medio una y seis `/code-review`. La suite completa tampoco: no tocó `tests/conftest.py` ni
ayudantes compartidos.

## Lo que queda escrito

- Riesgo 1 (el guion corre como superusuario; el estado colgado sólo se alcanza donde falta la
  FK): riesgo escrito, bajo, no D.
- El guion no va a la CI: se corre a mano en cada pieza que toque la lista o la regla de cobro.
