# D244 (a): reproducción de la PM

Entrega `6112322` (informe `91cdc781`, canal `PARA-PM-2.md`). Base `2f96f2f`. Producto:
`proyecto_maria/main.py` (`_cuit_del_despachante` limpia `cuit_agr` de espacios y guiones;
`/generate_maria/avisos` la usa). Arnés: `tests/test_cuit_generar.py` y los guiones
`cuit_generar.sh`, `estudio1.sh`, `excel2.sh`. Veredicto: **aceptada sobre `6112322`**.

## Corrido por la PM (2026-11-16, entre 20:00 y 20:54 UTC)

| Qué | Resultado |
|---|---|
| `git diff --stat 6112322 origin/claude/dev-maria -- . ':!docs/pm'` | vacío |
| `chequeo-6.py 2f96f2f 6112322` | producto +16/−8, arnés +94/−50, historia vacía, `avisos: 0`, como en el informe |
| grep de historia de §6 sobre `proyecto_maria/` | vacío |
| `anclas_perdidas.py 6112322` | 103 guiones, 2541 anclas, 11 sin medir; perdidas 0, 0 y 0 |
| `tests/test_cuit_generar.py` sobre `6112322` | `18 passed` |
| la misma prueba con el `main.py` de `2f96f2f` | `6 failed, 12 passed` |
| `cuit_generar.sh` (corre también el guion de pantalla) | `rc=0`, 21 `ROJO`, 0 sin rojo (20:26) |
| `estudio1.sh` | `rc=0`, 37 `ROJO`, 0 sin rojo (20:35) |
| `scripts/testing/e2e_maria.sh` | «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.» (20:35) |
| suite completa (sqlite, `ENVIRONMENT=test`, sin red) | `6196 passed, 110 skipped, 3 xfailed` en 17:43 (20:53); 0 líneas `FAILED` |

Negativos míos, en un archivo descartable con seis datos que no le di a la Dev. Cada uno pide
que avisos y generar digan lo mismo y el resultado esperado: tabulador y salto de línea en
`cuit_agr` con perfil bueno (sale el del perfil); «--» sin perfil («Falta…» en los dos); perfil
`20-99999999-8` con `cuit_agr` de espacios (el texto del perfil malo); estudio bueno con
`cuit_agr` malo (sale el del estudio, sin aviso); diez dígitos (el texto de la operación);
dígitos de ancho completo (400 en los dos, mismo texto). `6 passed`; el archivo se borró.

Sabotajes míos, fuera del guion, con `test_cuit_generar`, `test_estudio1` y `test_estudio1b`:

| Cambio | Resultado |
|---|---|
| `cuit_agr` limpio sólo de guiones (quedan los espacios) | `4 failed, 87 passed` |
| `/avisos` llama con `estudio=None` | `2 failed` (`[malo en el estudio elegido]` y `test_con_estudio_los_avisos_no_piden_el_cuit`) |

Adversario (Opus, esfuerzo alto, contexto nuevo, sin red, `GEMINI_API_KEY` vacía): 28 casos
comparando avisos con generar coinciden sobre `6112322`; corrió además 21 archivos que usan
`/generate_maria/avisos` (`1191 passed`). Único hallazgo nuevo: D259. Ya en la base: U+FEFF,
guiones unicode y dígitos de ancho completo dan un 400 con texto confuso. Sin problema: tipos
raros (422 en los dos), NBSP y U+3000 (ahora caen al perfil; antes, 400 con «»), `estudio_id`
ajeno o inválido (el mismo 400, sin mostrar un CUIT ajeno).

**No corrido por la PM:** `estudio1b.sh` y `excel2.sh` (los corrió la Dev, verdes);
`/security-review` (lo corrió la Dev hasta `c824b0d`); el aviso nuevo mirado en el navegador.

## Las horas del informe

El commit del informe es de las 20:19:19 UTC (`git log -1 --format=%cI 91cdc781`), y el
informe dice «Entrega 20:25» y que corrió el 1 a las 20:28. Como el commit sale del mismo
contenedor, no es diferencia de relojes: las horas se escribieron, no se midieron. No cambia el
veredicto porque la PM reprodujo todo; desde ahora, horas sólo de `date -u`.

## Las D

- **D259 (a)**, riesgo escrito, decidido por la PM: un estudio elegido cuyo CUIT fuera sólo
  espacios o guiones cae al CUIT del perfil en lugar de dar 400. Hoy no hay camino: el único que
  escribe `estudios.cuit` es `POST /api/estudios`, que desde que existe (`609ec528`) limpia
  espacios y guiones y exige 11 dígitos (después, `cuit_valido`). Lo nuevo es sólo eso; un `""`
  ya caía al perfil en `fc5944fc`. La (b) sería producto sin camino de hoy.
- **D260 (a)**, decidido por la PM: la limpieza del CUIT está escrita tres veces en `main.py`
  (`:4747`, `:4965`, `:7723`): a la cola de limpieza.

## Supuestos y riesgos

- **Supuestos 1 a 3** (el aviso va primero en `supuestos`; `=` cuenta como en blanco; el commit
  de arreglo `f165e9d` no es observable): aceptados.
- **Riesgos 1 a 3** (D259; U+200B, ya en la base; el aviso ahora sale también con estudio
  elegido): aceptados.
