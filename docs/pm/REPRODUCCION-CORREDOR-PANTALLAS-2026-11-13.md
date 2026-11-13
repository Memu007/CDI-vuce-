# Reproducción de CORREDOR-PANTALLAS (2026-11-13)

Entrega de la Técnica: arnés `868c0355`, `bfde5a5a`, `907e1edb`; informe
`4e98c865`; base `67c8ff0d`. Sólo arnés (producto +0/−0). Revisado por la PM
principal con el `correr_pantallas.sh` del SHA entregado.

## Lo medido

| qué | salida |
|---|---|
| pantallas que no llama ningún guion (`.sh`/`.py`, fuera de comentarios), medido por mí | las mismas 11 del informe |
| cabeceras `// corredor:` | el `awk` del corredor y un `grep` aparte encuentran las mismas 8; ninguna se ignora |
| `chequeo-6.py 67c8ff0d 907e1edb` | producto +0/−0, arnés +92/−0, 0 avisos |
| `git diff --stat 67c8ff0d 907e1edb` | `correr_pantallas.sh` +84 y una línea de cabecera en 8 pantallas |
| `git diff --stat 907e1edb 4e98c865` | sólo `docs/pm/PARA-PM.md` |
| `kill -TERM` al PID del corredor mientras corre `borrador1` | el corredor sale y su worktree se borra (trap), pero **queda un uvicorn huérfano** (PPID 1, mismo grupo de procesos), sobre el worktree ya borrado. Lo maté por PID. Con Ctrl-C no pasaría: la señal va a todo el grupo |
| entorno de cada guion que levanta uvicorn para una pantalla, contra el del corredor más la cabecera | única diferencia: `sabotajes/sesion1.sh` con `ENVIRONMENT=testing` (la que dio el informe). `CSRF_ENFORCE` está en `_csrf_comun.sh`, `orden1.sh` y `orden1b.sh`, y en las cuatro cabeceras |

## La puerta del sabotaje

Corrida en commits locales recortados a 6 pantallas (`/tmp/cdi-pm/wt-tec-neg`),
con el `correr_pantallas.sh` idéntico al de `907e1edb`:

| commit local | qué tiene | resumen |
|---|---|---|
| A `90335b33` | cabecera de `csrf3` cambiada a `csrf_enforce=true` | 5 verdes, 1 roja: `csrf3` con «FALLA: cabecera: «csrf_enforce=true» no es VAR=valor», salida 2 |
| B `64e53c55` | A más un sabotaje a mano en `pantalla_cliente1.js:51` | 4 verdes, 2 rojas: `cliente1` («FALLA: el rótulo de CUIT no dice…») y `csrf3` |

El sabotaje suma exactamente una roja. La puerta que el informe dio por no
cumplida al pie de la letra (4→6 por `maria7`) queda cerrada así.

## El corredor entero sobre `907e1edb`

Desde `/home/user/cdi-vuce-`, `scripts/testing/correr_pantallas.sh 907e1edb`,
02:18:34 → 02:33:12:

```
resumen: 26 verdes, 4 rojas: maria3 maria4 maria5 subitems1
rc=1
```

Igual al informe. Las cuatro rojas, con las causas ya conocidas: `maria3`
`TimeoutError`; `maria4` click sobre `#validatingGenerate` deshabilitado;
`maria5` y `subitems1` «Falta el CUIT del despachante (CDDTAGR)…». Ninguna
otra roja. Al terminar: sin uvicorn, chromium ni worktree del corredor.

**`maria7` y `maria1c` salieron verdes:** no vi el intermitente. La premisa
de D210 es sólo de la Técnica.

## No corrido por la PM

- Cada pantalla sola contra su línea del corredor (sólo las tres del informe
  y las de mis corridas recortadas).
- `orden1` con más de un servidor en paralelo.
- El rojo intermitente de `maria7` y `maria1c`: en mi corrida, verdes.

## Escape de la PM

En la vuelta anterior di por bueno «matar el corredor no deja huérfanos»
porque maté la subshell que lo envolvía, no el corredor. Matado el corredor
por su PID, deja el uvicorn de la pantalla en curso. Va como arreglo chico en
su tarea siguiente; no cambia ningún resultado.

## Decisiones

**D210: (b), ya.** `maria7` y `maria1c` son del arnés; la Técnica no tenía
tarea y la cola de MARIA es larga. Va con una puerta determinista
(`page.route` demora el script y fuerza la carrera), no por repeticiones.

## Veredicto

Aceptada sobre `907e1edb`. Integro el informe `4e98c865`.
