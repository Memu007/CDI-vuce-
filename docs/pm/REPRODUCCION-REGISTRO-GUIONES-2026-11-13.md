# Reproducción de REGISTRO-GUIONES (2026-11-13)

Entrega de la Técnica: arnés `b832fc2`, informe `19f890a5`, base `08ae9654`.
Sólo arnés (producto +0/−0). Revisado por la PM principal en worktrees
aparte en `b832fc2` (`/tmp/cdi-pm/wt-tec`) y en `08ae9654`
(`/tmp/cdi-pm/wt-tec-base`). Cada pantalla, con su servidor uvicorn y una
base sqlite nueva (el registro tiene tope de 5 por hora por IP).

## Lo medido

| qué | salida |
|---|---|
| `chequeo-6.py 08ae9654 b832fc2` | producto +0/−0, 0 avisos (igual al informe) |
| su medición con `git grep … \| awk` | 13 en la base, 0 en `b832fc2` (igual) |
| `grep "/auth/register"` en `pantalla_*.js` de `b832fc2` | sólo `_registrar.js:4` y `pantalla_org1b.js:72` (que espera el 400 a propósito) |
| `git diff --stat b832fc2 19f890a5` | sólo `docs/pm/PARA-PM.md` |

**Negativo mío** (otro borde que el suyo, que fue un 429 por proxy): registro
repetido del mismo usuario con `_registrar.js` contra un servidor de la
entrega. El primero da 200; el segundo corta con
`registro: 400 {"detail":"Usuario ya existe"}`. El chequeo dice status y
cuerpo, como pide la tarea.

## Las pantallas, de a una

| SHA | pantalla | salida |
|---|---|---|
| `b832fc2` | `borrador1`, `destino1`, `maria9`, `sesion1`, `validacion1`, `despacho1a`, `estudio1` | rc=0 |
| `b832fc2` | `orden1` | rc=0, 71 `OK` (ver abajo) |
| `b832fc2` | `maria5`, `subitems1` | rc=1, «Falta el CUIT del despachante (CDDTAGR)…» |
| `b832fc2` | `maria3` | rc=1, `TimeoutError` |
| `b832fc2` | `maria4` | rc=1, el click en «Generar» reintenta sobre un botón deshabilitado |
| `08ae9654` | `maria5`, `subitems1`, `maria3`, `maria4` | los mismos cuatro rojos |

Los cuatro rojos son de la base, como dice el informe.

**`orden1` y mi límite de tiempo.** La primera corrida dio rc=124: lo cortó
el `timeout 300` de mi propio corredor mientras un caso esperaba los
reintentos («12 pedidos en 200 s»). No fue la entrega. La repetí con 900 s:
rc=0, 71 `OK`, ninguna `FALLA`.

## Guiones de sabotaje

| guion sobre `b832fc2` | salida |
|---|---|
| `sabotajes/estudio1.sh` | 37 `ROJO`, «sabotajes sin rojo: 0», rc=0 (igual que sobre `dc4cf077`) |
| `sabotaje_maria9.sh` | «VERDE pantalla sin sabotaje», 29 `ROJO`, «OK: los 29 sabotajes dan rojo por la razón esperada», rc=0 |
| `sabotaje_separadores1.sh` | «VERDE pantalla sin sabotaje», 17 `ROJO`, «OK: los 17 sabotajes…», rc=0 |
| `sabotajes/destino1.sh` (`PUERTO=8857`) | 19 `ROJO`, «sabotajes sin rojo: 0», rc=0 |

En los cuatro: ningún `ROTO` y ningún «registro: 4xx/5xx». La tarea de fondo
terminó con 1 por un `tail -2` mío con varios archivos al final del comando,
no por un guion: cada guion dejó su `rc=0` en su registro.

`estudio1` no alcanza solo: su pantalla ya miraba el registro antes de la
pieza. Lo que podría romperse ahora es una pantalla que **antes no lo miraba**
y que un guion llama varias veces contra el mismo servidor: si repite una
cuenta, antes seguía de largo y ahora corta en el registro. Medido sobre
`b832fc2`: de las 13 de la base (su comando de `git grep … | awk` sobre
`08ae9654`), busqué quién las llama en `*.sh`, `herramientas/` y `tests/`,
fuera de comentarios, y también llamadas armadas con variables
(`pantalla_$…`). Sólo `sabotajes/destino1.sh:49`, `sabotaje_maria9.sh:130` y
`sabotaje_separadores1.sh:153`; los dos tests que nombran `pantalla_maria5`
lo hacen en el docstring. Son los tres que corrí enteros.

## No corrido por la PM

- Las otras 16 pantallas tocadas: `catalogo_ncm1`, `cliente1`,
  `cobro_corte1`, `cobro_mp1`, `cobro_mp1_v2`, `csrf1`, `csrf2`, `csrf3`,
  `despacho1b`, `estudio1b`, `excel1`, `maria1b`, `maria1c`, `maria7`,
  `separadores1` (sólo dentro de su guion) y `sufijos1`.
- Su `csrf1` con `CSRF_ENFORCE=true` y su negativo del 429 con proxy.

## Escape de la PM

La puerta de la tarea decía que `sabotaje_maria1c`, `maria4`, `maria7` y
`maria9` corren sus pantallas, «medido con grep». No es así: sólo `maria9`
corre la suya; en los otros tres el nombre aparece en un comentario. Mi grep
contó menciones, no llamadas. Por eso la puerta «base verde de `maria4`» que
el informe da por no cumplida no correspondía. Además, una búsqueda mía de
«pantallas que no corre ningún guion» marcó por error `cobro_mp1`, que
`cobro_mp1.sh:695–699` corre por `$JS`: esa cuenta no se usa.

## Decisiones

**D209: (a), MARIA.** Ningún guion corre esas cuatro pantallas, por eso nadie
vio el rojo en tres semanas. La exigencia del CUIT es de su pieza, y la causa
de `maria3` y `maria4` no está confirmada: su pieza empieza por ahí
(`PARA-DEV-2.md`, paso 2).

## Veredicto

Aceptada sobre `b832fc2`. Integro el informe `19f890a5` (sobre `b832fc2`
sólo cambia `PARA-PM.md`).
