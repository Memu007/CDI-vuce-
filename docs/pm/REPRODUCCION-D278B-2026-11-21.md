# D278 (b), la lista de usuarios con el cobro efectivo: `05ca7f71` (informe `f244c7b4`), 2026-11-21, PM

**Veredicto: aceptada**, integrada con el merge de `f244c7b4` (`647ea7da`). Base `a17011d1`. Sin publicar.
Revisión fuerte (toca `_vencer_si_corresponde`, que decide el acceso con cobro, §3).

## Diff

`git diff a17011d1 05ca7f71 --stat` fuera de `docs/pm`: `main.py`, `routers/admin_router.py`,
`services/billing_service.py`, `CHANGELOG.md`, `tests/test_admin_usuarios1.py` y dos guiones de
sabotaje. `chequeo-6.py a17011d1 05ca7f71` igual al informe: «producto +28/−26», historia vacía,
«avisos: 0». Lo de encima del SHA es sólo `docs/pm`:
`git diff --stat 05ca7f71 f244c7b4 -- . ':!docs/pm'` da vacío.

Leído a mano: `cobro_efectivo` (`billing_service.py:148-162`) no escribe y es la única regla que usan
el acceso (`_vencer_si_corresponde`, `main.py:2204`) y la lista (`admin_router.py:430`). El cambio de lo
que devuelve `_vencer_si_corresponde` (antes el estado viejo, ahora verdadero o falso) es seguro: sus
dos llamadores (`main.py:2268` y `2331`) sólo lo usan como booleano.

## Lo que corrí (worktrees en `05ca7f71` y en `05ca7f71` con `admin_router.py` de la base)

| Qué | Resultado |
|---|---|
| sus casos + `test_admin_solo_admin.py` + `test_cobro_corte1.py` | `134 passed, 19 warnings in 59.47s`; igual que el informe |
| rojo con `admin_router.py` de `a17011d1` | `1 failed, 8 passed`: las tres vencidas (`prueba_vencida`, `fuera_de_la_gracia`, `de_estudio_vencido`) y nada más; igual que el informe |
| suite completa, worktree limpio (SQLite) | `6242 passed, 110 skipped, 3 xfailed, 111 warnings in 1136.78s`, rc=0; mismos números que el informe |
| `admin_usuarios1.sh 05ca7f71` | 31 `ROJO` de 31, «sabotajes sin rojo: 0», rc=0 |
| `anclas_perdidas.py 05ca7f71` | perdidas 0 y 0; «no medido 5» en 2 guiones, igual que el informe. Ella los atribuye a `limpieza1.sh`; en mi salida son `e2e_rerun.sh` y `foco_cliente1.sh`, y `limpieza1.sh` sale «SIN ANCLA». Mismos números |
| `cobro_corte1.sh 05ca7f71` (PG 55462, usuario `cdi`) | 87 ROJO, 0 ROTO/PATRÓN/MAL, «BASE \| en verde», «BASE \| la pantalla en verde», «BASE \| el lock en verde», «sabotajes con falla: 0», rc=0, 3840 s; igual que el informe. Las anclas que movió a `billing_service.py` (trial vencido, gracia, fecha sin zona, otra razón) salen ROJO con su mensaje |
| negativo mío `pm_neg_regla.py`: la regla vieja de `a17011d1` contra `cobro_efectivo` en 198 casos (9 estados, 11 distancias al fin, con y sin zona) | «fallas: 0»: mismo estado guardado y mismo veredicto en todos. Con `cobro_efectivo` saboteado (la prueba vence un día tarde) da «fallas: 2» |

Mi negativo sólo prueba la equivalencia de la regla vieja y la nueva: no distingue el defecto de la
pieza, que es la lista. Lo que lo distingue es su caso de la familia `COBROS`, reproducido en rojo
arriba, y los cuatro sabotajes nuevos de `admin_usuarios1.sh`. No va al repositorio.

## Adversarios (sin red, `GEMINI_API_KEY` vacía, sobre `05ca7f71`)

- **Opus alto:** nada nuevo del diff. Dos observaciones, ninguna devolución:
  1. La lista y el perfil del usuario pueden no coincidir: una `active` vencida hace más de 7 días se
     ve `past_due` en el panel y `active` en su perfil hasta su primer pedido con cobro. Es D279, y
     queda como riesgo escrito.
  2. Una cancelada con el período terminado se ve `canceled`. Es lo que ya hacía; su riesgo 2.
- **Sonnet alto:** nada serio. La regla vieja contra la nueva en 1350 combinaciones (estados raros,
  fechas sin zona, en UTC−3, ±1 h alrededor de 0, 1, 6, 7 y 8 días): 0 difieren. Los dos llamadores
  usan el valor como booleano o lo ignoran. En un Postgres 16 descartable, la lista y el acceso
  coinciden en las cuatro cuentas sembradas (las columnas son `timestamp with time zone`); no probó
  ahí la integrante con el estudio borrado. Sus cuatro observaciones son previas: las copias de la
  regla (D279), el perfil y `cohort-retention` con lo guardado (su riesgo 4), un `active` sin fecha
  que nunca vence (igual en la base), y que la familia de la lista corre sólo en SQLite (la tarea
  siguiente).

## D279, decidido por la PM: (b)

- Las tres copias de la regla (`_check_expired_trials`, `main.py:786-807`; `get_current_user`,
  `auth/dependencies.py:142-155`; el checkout, `main.py:~11878`) van a `COLA-LIMPIEZA.md`. La de
  `get_current_user` va atada a D205: es el mismo lugar que lee sin candado y pisa una renovación.
- El perfil con el estado guardado queda como riesgo escrito.
- Por qué: hoy ninguna copia da ni niega acceso mal. Las dos primeras usan los mismos umbrales y sólo
  pasan cuentas a `past_due`; el checkout no tiene gracia, pero sólo elige el texto del 409 (las dos
  ramas dan 409; leído en `main.py:11873-11887`). Lo que pedía ADMIN-CREDITOS-1 era la lista.

## Lo que queda escrito

- **No corrido por la PM:** `/code-review` (lo cubren los dos adversarios) y la familia `COBROS` en
  Postgres (corre sólo en SQLite). La lista en Postgres es la tarea siguiente de MARIA, antes de que
  ADMIN-USUARIOS-1 y D278 entren a una candidata.
- Sus riesgos se sostienen tal como los escribe: el borde exacto (`<` contra `<=`) sin caso, la
  cancelada terminada, el acceso de la prueba por `_billing_vigente`, `cohort-retention` con lo
  guardado, «past_due hasta <fecha pasada>» en el panel, y `billing_service.py` tocado también por la
  Técnica (el merge de prueba con su primer tramo no choca).
