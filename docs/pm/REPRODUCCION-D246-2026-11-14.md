# D246 (b): reproducción de la PM

Entrega `0224f01` (informe `b8571ff`, canal `PARA-PM-2.md`). Base `a8d7f7b`. Sólo
arnés: sale el caso del sufijo vacío de `sabotaje_sufijos1.sh` y su prueba de
`test_sufijos1.py`. Veredicto: **aceptada sobre `0224f01`**. D247 (a), decidido por la PM.

## Corrido por la PM (2026-11-14, desde las 05:37 UTC, worktrees descartables)

Con `GEMINI_API_KEY` vacía, `DATABASE_URL` en SQLite, `ENVIRONMENT=test` y los
modos falsos, desde la copia de `0224f01`.

- `chequeo-6.py a8d7f7b3 0224f014`: producto +0/−0, arnés +37/−49, historia vacía,
  avisos: 0. Fuera de los comentarios renumerados, el diff es el encabezado, el
  bloque del caso y la prueba.
- Unión: `git diff --stat 0224f014 b8571ff7 -- . ':!docs/pm'` vacío; integro `b8571ff7`.

| criterio | resultado |
|---|---|
| `test_sufijos1.py` + `test_sufijos2.py` | `171 passed` |
| `anclas_perdidas.py 0224f014` | `perdida, una línea 6 guiones: 5` |
| `sabotajes/sufijos2.sh 0224f014` | base `110 passed`, 32 `ROJO`, 0 `ROJO?`, «sabotajes sin rojo: 0», `rc=0` |
| `sabotaje_sufijos1.sh 0224f014` | 46 `ROJO`, 0 `FALLA`, «OK: los 46 sabotajes dan rojo por la razón esperada», `rc=0` |

D247, negativo de la Dev repetido por la PM: con `«{uno[0][:40]}»` cambiado a
`«{sufijo[:40]}»` en `maria_generator.py:419`, las dos pruebas dan
`1 failed, 171 passed` sobre `a8d7f7b` (la prueba sacada) y `171 passed` sobre
`0224f01`. `limpiar_sufijo` hoy nombra `«AA()»`, `«AA(   )»`, `«AB()»` y `«AA(--)»`
para las cuatro entradas de `VACIOS`.

## Escape de la PM

D246 lo decidí yo con «la prueba de `test_sufijos1` no agrega una forma de vacío»:
comparé las entradas y no lo que afirma cada prueba. La que salió era la única que
fijaba qué código nombra el error. No hay otra prueba ni otro caso que se haya sacado
con la misma razón en SABOTAJE-SUFIJOS1, SABOTAJE-SUBITEMS1 ni D243. Lo cierra D247 (a).
Regla: para sacar una prueba por repetida, se compara lo que afirma, no los datos.

## D247: (a), decidido por la PM

El control queda una vez, en el archivo dueño de la regla, y con las cuatro formas de
vacío. Lo hace MARIA: la D la autoriza a tocar sólo `tests/test_sufijos2.py` y
`scripts/testing/sabotajes/sufijos2.sh`, de la Técnica (que no tiene pieza).

## Riesgos

El de la Dev (el texto del error puede nombrar el sufijo entero sin que nada lo vea)
queda cerrado por D247 (a), todavía sin entregar.

## No corrido por la PM

La suite, las pantallas, `e2e_maria.sh`, Postgres, adversario y `/security-review`: la
pieza no cambia producto. La corrida se superpuso con la tanda de fondo (`run6`).
