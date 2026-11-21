# CONEXIONES-1-PRODUCTO (con NOKEY): `b4f7e590` (informe `924cb1ca`), 2026-11-21, PM

**Veredicto: PENDIENTE** (todas las puertas corridas; falta el consejero). Base `ac4993b7`.
Sin publicar. Revisión fuerte (plata, sesión, transversal, §3).

## Diff

`git diff b4f7e590 1c5924dc -- proyecto_maria scripts tests` vacío: lo de encima del SHA es sólo
`docs/pm`. `chequeo-6.py ac4993b7 b4f7e590` igual que el informe: «producto +218/−54», historia
vacía, dos AVISO (164 netas; `paises_maria.js` 286 → 293). Los dos vienen de ADMIN-USUARIOS-1 y
CATALOGO-PAIS-2, ya aceptadas; lo suyo contra `44e3b0ba` es `+47/−42`, avisos 0. Explicación
suficiente.

## Lo que corrí (worktrees en `b4f7e590`, 20/11 23:00 UTC en adelante, con la copia del SHA)

| Qué | Resultado |
|---|---|
| `anclas_perdidas`, `conexiones1_producto.sh`, `conexiones1_nokey.sh` | rc=0; 11 BIEN y 4 BIEN, iguales a su tabla |
| `conexiones1_creditos.py` SHA / base | «pierden: 0; no valen: 0; sin carrera: 0» / «perdidos 10», «pierden: 2», rc=1 |
| suite completa, worktree limpio + `conexiones1_tests.diff` (SQLite) | `6251 passed, 110 skipped, 3 xfailed, 108 warnings in 1147.65s`, rc=0; mismos números |
| `GEMINI_API_KEY= e2e_maria.sh` sobre el SHA y sobre la unión con la rama de PM | los dos «E2E MARIA OK: …», rc=0 |
| `conexiones1_medir.py` sin y con cuota (PG16 desechable) | rc=0 los dos, 504 s; abajo |
| `cobro_corte1.sh b4f7e590` (PG 55462, usuario `cdi`) | 87 ROJO, 0 ROTO/PATRÓN/MAL, «BASE \| en verde», «BASE \| la pantalla en verde», «BASE \| el lock en verde», «sabotajes con falla: 0», rc=0, 3887 s; igual que el informe |
| `cobro_mp1.sh b4f7e590` entero (ella corrió sólo D, sobre `709b3a3e`) | 145 ROJO; BASE en verde (servidor, carrera de D y pagos a la vez en Postgres, perfil, Listo); el VERDE de D31 sigue verde; «sabotajes con falla: 0», rc=0, 3561 s |
| negativo mío `test_pm_neg_soltar.py` (6 casos: soltar y después usar, con la base caída) | `6 passed` |
| negativo mío `pm_neg_tope.py` (PG, dos pedidos cruzados en el candado: a manual+manual, b manual+generar, c extra 1, d extras vencidos) | «fallas: 0», rc=0: pasa uno, el otro 402, un solo cobro |

Medición, otra cuenta con 60 pedidos lentos (sin / con cuota): bcrypt 3,77 / 4,09 s (D180, fuera de
la pieza), gemini 0,36 / 0,41, pdf 0,03 / 0,06, excel 0,14 / 0,12, cuerpo 0,04 / 0,04. `close`
empezados = terminados = 3898; QueuePool, Traceback, CancelledError y excepciones ASGI: 0; «sin
conexiones tomadas». Iguales a su informe.

La primera corrida mía de `cobro_corte1.sh` dio «el lock ya está en rojo sin sabotaje»: la lancé
con el usuario `postgres` y ese Postgres sólo tiene `cdi` («role "postgres" does not exist»).
Error mío de entorno; la segunda, entera, es la de la tabla.

Mis negativos no van al repositorio. A `pm_neg_tope.py` no le hice sabotaje propio: la familia la
cubre su «manual con el cupo sin candado (D188)», que reproduje en rojo.

## Adversarios (sin red, `GEMINI_API_KEY` vacía, PG16 desechable, sobre `b4f7e590`)

- **Opus alto:** nada nuevo del diff. Aguantan las carreras de cupo (1 operación = +1), soltar con
  falla ×5 sin perder conteo, el orden usuario → org sin ciclo, 8 rutas con la misma dependencia.
  Dos previos, que salen igual en la base (`run_base.log`):
  1. `_vencer_y_guardar` (`main.py:2285`) y `get_current_user` (`auth/dependencies.py:146-156`) leen
     sin candado; su `UPDATE billing_status='past_due'` espera el FOR UPDATE del webhook y después
     pisa una renovación pagada: pagó y queda con 402. Probabilidad baja, severidad media (plata).
  2. Si falla el commit de `_vencer_y_guardar`, el rollback vence la entidad y `tiene_acceso` da
     MissingGreenlet → 500. No pierde escrituras. Ya está en sus riesgos.
- **Sonnet alto:** nada serio. 9 rutas × 19 escenarios, base contra cabeza: 171/171 sin
  diferencias. Base caída al soltar en SQLite y con `pg_terminate_backend` en Postgres: 200 con
  conteo correcto o 500 sin cobro a medias. Sospecha sin reproducir (pool lleno entre la dependencia
  y la ruta): la medición dio 0 QueuePool.

## Lo que queda escrito

- El previo 1 de Opus no es de esta pieza: no es devolución. Va como candidata a pieza futura, para
  proponer a Emi.
- Sus riesgos se sostienen tal como los escribe (multipart antes de las dependencias, `_soltar_conexion`
  que se traga el error, `result` del lifespan, casos fuera de git y de la CI).
