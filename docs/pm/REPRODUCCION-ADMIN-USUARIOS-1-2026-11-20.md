# ADMIN-USUARIOS-1: `b06b47fa` (informe `a8edd311`), 2026-11-20, PM

**Veredicto: aceptada, integrada** (merge de `a8edd311` en la rama de PM). Base `e5d943e4`.
Sin publicar. Fuera del candidato `0d7401ed`: entra en el siguiente.
Revisión fuerte (permisos y datos, §3).

## Diff

`chequeo-6.py e5d943e4 b06b47fa`: «producto +160/−12», «arnés +540/−6», historia vacía, un AVISO
(«suma 148 líneas netas»). Es función nueva, no un arreglo: ≈60 líneas de ruta en
`admin_router.py`, ≈80 de la sección en `dev_dashboard.html`, y `billing_service.py` +4 netas porque
`como_utc` reemplaza dos copias. Explicación suficiente. Igual que el informe.

## Lo que corrí (worktree en `b06b47fa`, 19:53 UTC en adelante, con la copia del SHA)

| Qué | Resultado |
|---|---|
| comando 1: `test_admin_usuarios1.py` + `test_admin_solo_admin.py` | `35 passed` |
| comando 2: `pantalla_panel_dev.js` | `fallas: 0` |
| comando 3: producto de `e5d943e4` sobre el SHA | `8 failed, 14 warnings, 27 errors` |
| comando 4: `sabotajes/admin_usuarios1.sh b06b47fa` | 27 ROJO, «sabotajes sin rojo: 0», rc=0 |
| negativo mío con sesiones reales (firma de token en la cookie, sin el atajo de pytest) | `7 passed` |
| el mismo, con la bandera admin de la fila como `"admin" in str(roles)` | `1 failed, 6 passed` |
| el mismo, con `_es_admin` como `"admin" in str(roles)` | `3 failed, 4 passed` |
| suite completa desde worktree limpio (SQLite, 19:54 a 20:13) | `6241 passed, 110 skipped, 3 xfailed … in 1151.25s`, rc=0; igual que el informe |

Mi negativo: roles `"administrador"`, `["Admin"]`, `["owner","operador"]`, `{"admin": true}`,
`None` y el texto `'["admin"]'` dan 403 sin datos; el admin da 200 y la bandera coincide con el
control; POST, PUT, PATCH y DELETE dan 405. No va al repositorio.

## Adversarios (sin red, `GEMINI_API_KEY` vacía, sobre `b06b47fa`)

- **Sonnet alto:** nada grave. Plan guardado contra cobrado (bajo-medio), estado guardado y no
  efectivo (bajo), un `creditos_extra` negativo se muestra tal cual. Sólo en SQLite, un `roles` con
  JSON roto da 500 en toda la lista. Según el adversario (no lo verifiqué), en Postgres la columna
  JSON no lo deja y ese usuario tampoco entraría.
- **Opus alto:** nada grave. Un plan `NULL` sale `None` con 200 (bajo). `billing_service` da lo mismo
  que antes en 33 fechas; 424 tests de cobro verdes; el arranque pasa los vencidos a `past_due`.
- Ninguno corrió en Postgres.

## Lo que leí

- **Riesgo 2 (plan «trial»).** `User.plan` vale «trial» por defecto (`models.py:38`), pero los tres
  caminos que crean cuentas guardan «premium»: el registro (`main.py:3489`), el alta de estudio
  (`main.py:10740`) y los usuarios demo (`main.py:1730`). No hay otro `User(` fuera de los tests. Lo
  que dice el informe se sostiene: riesgo escrito, no devolución.
- **D278 (estado efectivo).** `_check_expired_trials` (`main.py:792`) cubre `trial` vencido y
  `active` con 7 días de gracia, pero corre sólo al arrancar (`main.py:1683`). Al usar, lo vencen
  `_vencer_si_corresponde` y `get_current_user`. El hueco es real y más chico que lo que dice el
  informe: una cuenta que venció después del último arranque y no volvió a entrar se ve con su
  estado viejo y su «hasta» ya pasado.

## No corrido por la PM

- Postgres: no corrí los tests ni la ruta en PG16. Se apoya en la sonda de la Dev (las dos clases de
  columna de fecha, login real, base igual antes y después).
- `panel_dev.sh` (6 de 6 en el informe): no lo corrí.
- Puerta antes de que esta pieza entre en una candidata: la ruta de la lista sobre Postgres 16 con
  la candidata (`tests/conftest.py` fija SQLite, así que los tests no sirven para eso).
