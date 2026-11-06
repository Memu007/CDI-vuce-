# Herramientas de PM

Vienen listos; lo que se completa, si algo, es el bloque de configuración
de arriba:

| Archivo | Qué hace | Qué se completa |
|---|---|---|
| `medir.py DESDE HASTA` | cuánto rinde el equipo, sacado de Git | zona horaria y ramas |
| `chequeo-6.py <base> <SHA>` | pone `CLAUDE.md` §6 en números: avisos para mirar, no un veredicto (`/entregar` §1, `/revisar-entrega` §2) | carpetas de producto y de arnés, archivo y función de los casos |
| `chequeo-6-js.mjs` | lo llama `chequeo-6.py` para leer JS/TS; necesita `typescript`: el del proyecto, o uno global por `NODE_PATH` | nada |
| `sabotajes-conocidos.txt` | los sabotajes vencidos, uno por línea («Publicar» en `ONBOARDING-PM.md`) | nada: arranca vacío |

El resto depende del stack de cada proyecto, así que cada proyecto escribe los
suyos. Lo que importa es el contrato: qué hace cada uno y qué tiene que
mostrar. Usan valores inventados (nunca secretos) y trabajan fuera del
repositorio.

| Script | Qué hace | Qué tiene que mostrar |
|---|---|---|
| `levantar.sh <SHA>` | worktree en ese SHA, `.env` inventados, dependencias, base nueva, API y frontend | las URLs locales arriba |
| `base-nueva.sh` | base recién creada, migraciones y datos de prueba | «base lista» |
| `reiniciar-api.sh` | reinicia la API por su línea de comando | cuántos procesos quedaron (tiene que ser 1) |
| `chequeo-previo.sh [SHA]` | antes de una corrida larga: worktree en el SHA, base con tablas, un solo proceso de API, API y frontend responden, carga de la máquina | una línea OK, FALLA o AVISO por punto; sale con 1 si algo falla |
| `suite-y-puertas.sh <base> <SHA>` | corre el chequeo previo, la suite completa, repite sólo los rojos y las demás puertas | termina con una línea `fin: …` para poder esperarla |

Lo largo se corre con `run_in_background` del arnés (hasta 2 h), con la
salida redirigida a un registro, y se espera mirando el registro. Lo lanzado
con `setsid nohup` muere cuando el contenedor se reinicia por turno quieto;
lo de `run_in_background` sobrevive (`LECCIONES.md` del Second Brain,
«Entorno»):

```bash
docs/pm/herramientas/suite-y-puertas.sh <base> <SHA> > "$PM_DIR/suite.out" 2>&1 < /dev/null
```

**Si un reinicio corta una corrida** (mata la corrida, la espera en
segundo plano y los subagentes, sin avisar), lo ve la vuelta siguiente y
se relanza.

Cuidados que costaron caro (ver `LECCIONES.md` del Second Brain):

- el proceso en segundo plano no hereda la salida de quien lo llama:
  redirigila entera;
- nunca `pkill -f` con un patrón que coincida con tu propia terminal;
- para traer una rama, refspec explícito:
  `git fetch -q origin +refs/heads/<rama>:refs/remotes/origin/<rama>`.

## En CDI

Escritos el 2026-10-06 y probados sobre `e8344d0`: `levantar.sh <SHA> [puerto]`
y `chequeo-previo.sh [SHA] [puerto]`. El `.env` que arman deja VUCE, Tarifar y
AFIP simulados, el dólar contra un puerto local cerrado y sin Mercado Pago,
SMTP ni Sentry. El chequeo lo verifica; con la API apagada da FALLA y sale
con 1. Trabajan en `$PM_DIR` (por defecto `/tmp/cdi-pm`). Cada sesión usa su
propio `PM_DIR` y su puerto. Faltan `suite-y-puertas.sh` y
`reiniciar-api.sh`: se escriben con la primera corrida larga.
