# CUIT-GENERAR (D235 a): reproducción de la PM

Entrega `29327d2` (informe `47b8481`, canal `PARA-PM-2.md`). Base `3dc9908`.
Veredicto: **aceptada sobre `29327d2`**. D243 (b), decidida por la PM. D244 va a Emi
(recomiendo a).
Revisión fuerte (§3: datos que van al TXT).

## Corrido por la PM (2026-11-14, ~01:50–02:44 UTC, worktrees descartables)

- Leí el diff entero fuera de `docs/pm`. Producto: `_cuit_del_despachante`
  (`main.py:4740-4760`), un solo llamador (`main.py:5173`); valida con `cuit_valido`
  (`controles_maria.py:52`), el mismo que usa el alta de estudios (`main.py:7714`).
  Sale el `[0-9]{11}` y el `try/except` que tapaba errores.
- `chequeo-6.py 3dc9908 29327d2`: igual al informe (producto +25/−24, arnés +386/−93,
  historia vacía, avisos: 0).
- Unión: `git diff --stat 29327d2 origin/claude/dev-maria -- . ':!docs/pm'` vacío, y mi
  rama (`40de7018`) no cambia nada fuera de `docs/pm`, `.claude` y `AGENTS.md` desde la
  base común. Lo de abajo sobre `29327d2` vale para la unión.

| corrida | resultado |
|---|---|
| `tests/test_cuit_generar.py`, `29327d2` | `12 passed` |
| lo mismo con `main.py` de `3dc9908` | `7 failed, 5 passed` (los 7 que rechazan) |
| `sabotajes/cuit_generar.sh`, `29327d2` | `rc=0` en 222 s, 21 `ROJO`, `sabotajes sin rojo: 0` |
| `sabotajes/cuit_perfil.sh` (arnés compartido nuevo) | `rc=0`, 11 `ROJO`, `sabotajes sin rojo: 0` |
| pantalla `cuit_generar1` | `PANTALLA CUIT-GENERAR-1 OK` |
| `e2e_maria.sh`, `29327d2` | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.` |
| `anclas_perdidas.py`, «perdida, una línea» | 10 en `29327d2`, 6 en `3dc9908`: las 4 nuevas son las de D243 |
| suite entera, sqlite, `ENVIRONMENT=test`, dólar local, `GEMINI_API_KEY` vacía | `6143 passed, 110 skipped, 3 xfailed` (02:24–02:44 UTC), igual a la de la Dev |

El primer `e2e_maria.sh` dio `rc=1` con `ModuleNotFoundError: fastapi`: tomó el
`python3` del sistema. Repetido con el venv en el `PATH`: el OK de la tabla. Es
entorno, no producto.

## Negativos de la PM

Seis ejemplos no dados a la Dev, en un archivo descartable: CUIT de ancho completo en
`cuit_agr`, guion largo, 12 dígitos, perfil con espacio duro, perfil con el
verificador cambiado y `cuit_agr` con guiones igual a un perfil malo: `6 passed`
(todos rechazan con el texto que corresponde).

Sabotajes sobre `es_el_del_perfil`, con `test_estudio1`, `test_estudio1b` y
`test_cuit_generar` (sin tocar: `85 passed`):

| sabotaje | resultado |
|---|---|
| `es_el_del_perfil = False` | `9 failed`, entre ellos `test_el_cuit_del_perfil_en_cuit_agr_cuenta_como_uso_del_perfil` |
| sin `estudio is None` | `85 passed`: no distingue |

El segundo no es un hueco de casos: es un cambio sin efecto. Los dos usos de la marca
miran antes si hay estudio (`if estudio is not None:` en el texto de «dónde» y en
`main.py:5234`, con el uso del perfil en el `elif`), así que ninguna entrada da otro
resultado. Lo mismo pasa en la base (`73 passed` con el sabotaje equivalente).

## Adversario (Sonnet alto, contexto nuevo, sin red)

Corrió con `GEMINI_API_KEY=test-key`, no vacía como pide la regla; el guion no
llama a Gemini, pero queda declarado. Unos 130 mil valores por fuzz, tipos JSON raros
(422), `\r\n` (400). No encontró un `CDDTAGR` inválido que llegue al TXT, un rechazo
falso ni un 400 que guarde la operación. Dos hallazgos, ninguno alcanzable por la API
(sólo con un estudio escrito a mano en la base, porque el alta valida):

1. Nuevo: un estudio con `cuit=""` y un perfil malo da «Es el del estudio elegido…»
   cuando el malo es el del perfil. Antes generaba con el `CDDTAGR` inválido.
2. Ya estaba: un estudio con `cuit` de espacios da 400 con «».

Son riesgo, no pedido (no tienen camino de hoy): van como dato para Emi con D244; no
son devolución.

## Lo que sale de la revisión

- **D243 (b), decidido por la PM:** la pieza chica de las cuatro anclas va primera
  en la cola de MARIA. Criterio: `estudio1.sh`, `estudio1b.sh` y `excel2.sh`
  corridos enteros sobre el SHA nuevo, cada sabotaje en `ROJO`, y
  `anclas_perdidas.py` de vuelta a las 6 de la base. La rama de la Técnica no
  tocó esos guiones desde `3dc9908`.
- **D244 va a Emi, recomiendo (a):** que los avisos de antes de generar anuncien el
  CUIT que no cierra (hoy no lo dicen; el 400 al generar sí). No tiene fila en
  `ROADMAP.md` (AVISOS-1 es de exportaciones). Si dice que sí, entra cuarta en la
  cola de MARIA, después de D243 (b), `subitems1` y `sufijos1`.
- No se propone `29327d2` para publicar hasta que D243 (b) esté aceptada o esos
  tres guiones se corran a mano en `ROJO`.
- `40de7018` es la última cabeza de mi rama sin CUIT-GENERAR: si Emi da el «dale» a
  PAIS-NL antes de cerrar D243 (b), se publica desde ahí.
- Publicar frena a quien tenga guardado un CUIT que no cierra, en el perfil o en un
  estudio viejo: va a Emi con el «dale».
- CUIT-GENERAR no tiene fila en `ROADMAP.md` (es D235, sobre MARIA-7).
- `CLAUDE.md` §5 dice que la CI deselecciona tests; `ci.yml:40-49` corre la suite
  entera: a `COLA-LIMPIEZA.md`.

## Puertas de la Dev (medidas por ella sobre `29327d2`, no repetidas)

`compileall` sin salida; 35 pantallas verdes; `smoke_friccion.sh` OK;
`ataque_aislamiento.sh` con Postgres 16 local, `Bloqueado: 47 · Fugas: 0`;
`/security-review` (Opus alto, sólo lectura): ningún hallazgo.

## No corrido por la PM

Las otras 34 pantallas, `smoke_friccion.sh`, `ataque_aislamiento.sh`, `compileall`,
un adversario Opus (la tabla pide Sonnet alto para datos) y los guiones de D243
enteros. La reproducción se superpuso con la tanda de sabotajes de fondo
(`run6`, sobre `7436c6e5`), que no dice nada de este SHA.
