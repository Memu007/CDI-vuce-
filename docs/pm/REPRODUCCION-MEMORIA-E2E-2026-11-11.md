# Reproducción de MEMORIA-E2E (MARIA), 2026-11-11

Entrega `f186ecf` (base `7d5c9e7`), informe `40fc745`. Worktree de la PM en
`/tmp/cdi-pm/wt-f186ecf0`, `GEMINI_API_KEY` vacía.

## Lo que corrí

| qué | resultado |
|---|---|
| `tests/test_memoria_pantalla.py tests/test_guardar1.py` | `32 passed, 3 warnings in 5.67s` |
| lo mismo con `d497551` revertido | `4 failed, 28 passed`: los tres `test_pantalla_alimenta_memoria[individual/lote/sugerencia]` y `test_la_forma_del_ncm_que_guarda_el_historial[8471.30.00.900 R-84713000]`, igual que el informe |
| `scripts/testing/e2e_maria.sh` | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.`, `exit=0` |
| `chequeo-6.py 7d5c9e7 f186ecf` | `producto +2/−2`, `arnés +87/−0`, historia vacío, `avisos: 0`: igual que el informe |
| `git diff f186ecf 40fc745` fuera de `docs/pm` | vacío |

## Negativos míos (`ncm_para_historial`, sobre `f186ecf`)

| entrada | da |
|---|---|
| `8471.30.00.900 r` | `84713000` (se pasa a mayúscula antes, como ya hacía) |
| `84713000900 R` | `84713000` |
| `8471.30.00 900 R` | `84713000` |
| `8471.30.00.900 R5` | `None` |
| ` R` | `None` |
| `8471.30.00.900-R` | `None` |
| `8471.30.00.90 R` | `None` (10 dígitos con letra) |
| `84713000 R` | `None` (8 dígitos con letra) |
| `8471.30.00.900 ʀ` | `None` |

## Quién usa la función

`git grep` sobre `f186ecf`: `ncm_para_historial` la llaman
`client_memory.py:152` (`identidad_del_producto`), `main.py:9002` (PUT del
producto del cliente), `main.py:10504` (guardar-uso) y
`despacho_lector.py:870` (`renglon_para_catalogo`). `identidad_del_producto`
la usan la memoria y su migración de claves (`main.py:1497`). Ninguno arma
el TXT. `_POSICION` (`despacho_lector.py:134`) sólo lee texto de documentos
y no cambió.

## Lo que no corrí

- Suite completa: la corrió la Dev sobre `f186ecf` (5832 passed). Para un
  +2/−2 en una regex, no la repetí.
- Adversarios: no es pieza de §3.
- Sobre el árbol de la PR: `f186ecf` está sobre trabajo de MARIA que mi
  rama no tiene. La prueba en ese árbol es la del armado con sólo los
  cuatro commits (veredicto en `PARA-DEV-2.md`) y el check `e2e-maria` en
  la cabeza nueva de la PR.

## El armado para la PR: `d2f7f9c` (base `db8f607`, D166 a)

Worktree de la PM en `/tmp/cdi-pm/wt-armado`, `GEMINI_API_KEY` vacía.

| qué | resultado |
|---|---|
| `git log db8f607..d2f7f9c` | cuatro commits: `faf2b5f` (fix), `c6a8de6`, `df3e26f`, `d2f7f9c` (pruebas) |
| `git diff --stat db8f607 d2f7f9c` | `CHANGELOG.md` +4, `client_memory.py` +2/−2, tres archivos de prueba; nada más |
| `proyecto_maria/` | sólo la regex y su comentario, igual a `d497551` |
| `CHANGELOG.md` | las mismas 4 líneas `+` que `d497551` (`diff` vacío) |
| árbol de `fcee205` (merge en su rama) y de `5067149` | iguales, `eb441dcc…` |
| `tests/test_memoria_pantalla.py tests/test_guardar1.py` | `32 passed` |
| lo mismo con `faf2b5f` revertido en `proyecto_maria/` | `4 failed, 28 passed`, los mismos cuatro casos |
| mis nueve negativos | iguales a la tabla de arriba; `8471.30.00.900 R` da `84713000` |
| `scripts/testing/e2e_maria.sh` | `E2E MARIA OK: …`, `exit=0` |

`git diff d2f7f9c f186ecf -- client_memory.py` tiene tres bloques: la
importación (línea 32) y `lookup_client_memory` (272 y 280), que son de
CATALOGO-3. Ninguno cae en `_NCM` ni en `ncm_para_historial` (108-125).
`git grep` sobre `d2f7f9c`: `_NCM` sólo lo usa `ncm_para_historial`; la
llaman los mismos cuatro lugares (`client_memory.py:152`, `main.py:8950`,
`main.py:10452`, `despacho_lector.py:872`). Ninguno arma el TXT.

Integrado en mi rama con `merge` (`3c1b11fd`); fuera de `docs/pm` y
`.claude`, el árbol es igual al de `d2f7f9c`.

No corrí la suite completa ni los adversarios: es la misma regex ya
aceptada. El job `tests` de la CI no instala node: si el runner no lo trae,
`test_pantalla_alimenta_memoria` se salta ahí (lo cubre `e2e-maria`).
