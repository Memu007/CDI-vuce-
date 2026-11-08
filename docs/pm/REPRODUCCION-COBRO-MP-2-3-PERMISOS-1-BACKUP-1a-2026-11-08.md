# Reproducción de COBRO-MP-2+3 vuelta 3, PERMISOS-1 y BACKUP-1a (Dev técnica), 2026-11-08

Entrega `ca84c5f`, informe `285d224` en `PARA-PM.md`. Bases: `ac52d6f`
(cobro y permisos) y `b831905` (backup). Corrido por la PM principal en un
worktree limpio de `ca84c5f`, venv `/tmp/cdi-pm/venv`. Log:
`/tmp/cdi-pm/cobro3.out` (09:55 a 12:25 UTC).

## Resultado: aceptadas, sin integrar

| Qué | Informe | PM |
|---|---|---|
| `chequeo-6.py ac52d6f ca84c5f` | +19/−15, 0 avisos | igual |
| `permisos1.sh ca84c5f` | falla 0 | 4 ROJO, falla 0 |
| `cobro_mp3.sh ca84c5f` | falla 0 | 22 ROJO, falla 0 |
| `backup1a.sh ca84c5f` | falla 0 | 48 ROJO, falla 0 (base `47 passed`; su propio Postgres) |
| `cobro_mp2.sh ca84c5f` | falla 0 (43 sobre `8174f01`, el resto sobre `ca84c5f`) | 87 ROJO, falla 0, **todo sobre `ca84c5f`** |

La Dev corrió parte de `cobro_mp2.sh` sobre `8174f01` con una copia del
guion que no está en el repo. Yo corrí el guion del repo entero sobre
`ca84c5f`: cubre ese hueco.

## Adversarios (contexto nuevo, sin red, GEMINI_API_KEY vacía)

- **Opus alto (cobro).** Sin nada grave nuevo. Baja: un sid que da 404 en
  MP cuenta como «cancelled», y así un miembro cancela un estudio sin
  suscripción que pague. Ya está en D119 y lo cierra COBRO-MP-4. Plazo y
  reactivar no cambian el producto en este rango: sólo suman pruebas. La
  firma se sostiene.
- **Sonnet alto (permisos y backup).** Sin camino nuevo a admin. Bajas que
  ya conocíamos: `re.match` con `$` acepta un `\n` final en el username (a
  la cola); con `IS_PRODUCTION` exacto se crea el admin demo (D99). Backup,
  media: la verificación no compara PK, índices, FK, objetos grandes ni
  secuencias (declarado en el informe y en el CHANGELOG). Otras bajas: otros
  parámetros de la URL pasan a los argumentos de `pg_dump`; los hijos
  heredan el entorno; `?dbname=` en la URL de prueba; TOCTOU del sha256;
  `os.link`. No borra nunca una base ajena.

## Riesgos que quedan

- El 404 de MP como cancelado: COBRO-MP-4 (D119 b).
- El backup no compara índices, FK, objetos grandes ni secuencias: una
  restauración «verificada» puede salir sin índices. Hay que decirlo antes
  de confiar la copia de producción.
- `\n` en el username, y los argumentos y el entorno de `pg_dump`: a la cola
  de limpieza.
