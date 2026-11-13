# ENTORNO-1: reproducción de la PM (2026-11-07)

Dev MARIA, producto `83085e4`, informe `b1e2daf`, base `9f996a4`. Revisión
más fuerte (autenticación y plata). **Veredicto: aceptada, sin integrar**
(la rama lleva lo de `e0b8626` sin aceptar).

| Qué | Resultado |
|---|---|
| `chequeo-6.py 9f996a4 83085e4` | producto +23/−24, arnés +291/−7, historia vacío, 0 avisos: igual al informe |
| `test_entorno1`, `test_mp_webhook_signature`, `test_prelaunch_block3` | `82 passed` |
| `sabotajes/entorno1.sh 83085e4` | 10 ROJO, `sabotajes sin rojo: 0` |
| `sabotajes/cobro_mp2.sh 83085e4`, 1.ª | 2 «ROJO?» con salida 137 (proceso matado por memoria: un script del adversario Opus se llamaba `jwt.py` y se lanzaba a sí mismo; OOM del cgroup a las 18:5x) |
| `sabotajes/cobro_mp2.sh 83085e4`, 2.ª, sola | 23 ROJO, `sabotajes con falla: 0` |
| `git status --short` después de los sabotajes | vacío |
| suite entera (`ENVIRONMENT=testing`, SQLite) | `5017 passed, 335 skipped, 3 xfailed`, rc=0: igual al informe |

La 1.ª corrida de `cobro_mp2.sh` no es un rojo intermitente del producto:
la salida 137 es SIGKILL, coincide con el OOM que el adversario Opus informó
con pids, y la 2.ª corrida, sin otra carga, da los 23 rojos esperados.

## Adversarios (contexto nuevo, sin red, `GEMINI_API_KEY` vacía)

- **Opus alto:** uvicorn real, un proceso por valor. Ausente, `""`,
  `staging`, `prod`, `Production`, `" production"`, `Development`: demo
  401, login con el hash 401, simulate 404, checkout 503, demo-checkout y
  demo-confirm 404, webhook sin firma y con firma falsa 401, sin link de
  reset en el log. `development`/`test`/`testing`: todo abierto. Producción
  con clave fuerte y secreto: arranca, firma buena pasa, falsa 401. Las
  pruebas de la Dev sobre la base: `6 failed, 6 passed` (distinguen).
- **Sonnet alto:** lo mismo por otro camino; ninguna puerta de plata ni de
  sesión abierta con `ENVIRONMENT` ausente o desconocido.

Hallazgos, ninguno introducido por el diff como defecto:

1. Usuarios demo que ya estén en una base siguen entrando (el diff sólo deja
   de crearlos). Repro de Opus: arrancar en `development`, después en
   `production` sobre la misma base: `demo` 200 y `/api/dev/stats` 200. → D99, Emi.
2. Si Railway no tiene `production` exacto: con clave JWT débil no arranca, y
   sin `MP_WEBHOOK_SECRET` el webhook JSON da 401. Buscado (D97); confirmar
   antes de publicar.
3. Con `ENVIRONMENT` ausente siguen como en desarrollo los controles de
   configuración: CSRF sólo reporta, cookies sin `Secure`, `/docs` abierto
   (visto 200), sin exigir `ALLOWED_ORIGINS`/`FRONTEND_URL`, caída a SQLite
   sin `DATABASE_URL`, VUCE simulado permitido. Anterior. → D98, pieza ENTORNO-2.
4. `ENABLE_SIMULATE_CHARGE=true` abre simulate-charge en cualquier entorno:
   bandera explícita, anterior. Va en ENTORNO-2.
5. `test_email1.py:158` y `:216` parchean `IS_PRODUCTION`, que ya no decide
   el correo; `test_prelaunch_block3.py:205-235` es tautológica. Ninguno deja
   verde una regresión (la cubre `test_entorno1`). A la cola de limpieza.

## No corrido

`smoke_friccion`, `ataque_aislamiento`, Postgres (el de 55462 quedó caído
por el reinicio del contenedor; la pieza no toca consultas), arranque con
gunicorn.
