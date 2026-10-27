# Reproducción de ESTUDIO-1b — 2026-10-27

Sobre `3aba9c2` (producto `e226ac3`, `975d627`; informe `807d562` en
`claude/dev-tecnica`; base `4452b22`). Entra con la vuelta de CLIENTE-1c
(ver `REPRODUCCION-CLIENTE-1c-2026-10-27.md`, «Vuelta»). Todo local, con
sintéticos.

**Veredicto:** aceptada.

## Lo que corrió la PM

| Qué | Resultado |
|---|---|
| Suite completa sobre `3aba9c2` | `3229 passed, 102 skipped, 2 xfailed`, rc=0 |
| `sabotajes/estudio1b.sh 3aba9c2` (incluye la pantalla en Chromium) | 20 de 20 en rojo («sabotajes sin rojo: 0») |
| `sabotajes/estudio1.sh 3aba9c2` | corriendo al subir este veredicto (9 de 37 en rojo hasta ahí, ninguno verde); el total va en la próxima vuelta |
| 32 negativos propios por API (archivo descartable, no entra al repo) | `32 passed` |

El revisor adversarial **no corrió** (presupuesto semanal).

## Los tres casos de D23 (b)

| Caso | Dónde se prueba |
|---|---|
| perfil usado después de un estudio: gana el perfil | pruebas de la Dev y negativos de la PM |
| perfil elegido a mano, la operación siguiente sin tocar el selector | `pantalla_estudio1b.js`, dentro de `estudio1b.sh` |
| un estudio único recién cargado, sin uso previo del perfil: gana el estudio | pruebas de la Dev |

## Negativos de la PM (todos pasan)

- Un TXT que falla con el perfil no cuenta como uso. `/generate_maria/avisos`
  tampoco.
- `estudio_id` raro da 400 en las dos rutas: `{}`, `true`, `false`, `0`,
  `"0"`, espacio de ancho cero, tab, `"NULL"`, `"undefined"`.
- El estudio de otra cuenta da 400 y no cuenta.
- El uso del perfil de la cuenta A no mueve la preselección de B.
- Un `cuit_agr` distinto del perfil no cuenta; el del perfil con guiones sí.
- Nombres con U+2060, BOM, U+2067 o ZWJ dan 400. «Muñoz & Cía.», cirílico
  y japonés pasan.
- Borrar el último estudio usado vuelve al perfil.

## La tabla nueva

`usos_cuit_perfil` se crea con `create_all` en `init_db()`, que corre
siempre al arrancar (`main.py`, `lifespan`), igual que `estudios`. No hay
migraciones aparte.

## Riesgos anotados (de la Dev, no se arreglan ahora)

- `cuit_valido` acepta `00000000000` (ya estaba).
- Dos TXT a la vez con el perfil pueden chocar al anotar el uso
  (IntegrityError): el TXT sale igual.
- U+3164 y U+2800 pasan en el nombre (no son de la categoría Cf).
