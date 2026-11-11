# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## MEMORIA-E2E entregada en f186ecf (base 7d5c9e7)

| commit | qué |
|---|---|
| `d497551` | fix: la posición SIM con la letra separada por un espacio alimenta la memoria del cliente |
| `9be52ef` | test: la posición como la arma la pantalla aprende por guardar-uso, la operación, learn y el PUT |
| `195af11` | test: el caso junta las cuatro entradas antes de comparar |
| `f186ecf` | test: node en un fixture con tope; tab y NBSP antes de la letra siguen rechazados |
| `a471763` | merge de tu rama (`816038e`); sólo `docs/pm/` |
| (este) | docs: informe |

Las puertas corrieron sobre `f186ecf`. Lo que hay después es tu rama y este
informe: `git diff f186ecf..HEAD --stat` muestra sólo `docs/pm/`.

**Resultado:** «8471.30.00.900 R», como la manda la pantalla, aprende por las
cuatro entradas y el catálogo del cliente la muestra. `e2e_maria.sh` verde.
El cambio de producto es una regex en `client_memory.py`: acepta un espacio
(sólo el espacio común) entre la posición y la letra. `producto +2/−2`.

`ncm_para_historial` la usa sólo la memoria (`client_memory.py:152`,
`main.py:9002` y `:10504`, `despacho_lector.py:870`). Lo que sale en el TXT no
pasa por ahí.

## Decisiones

**D165. Tres lugares leen una posición SIM y no aceptan lo mismo.**
`client_memory.py:110` (`_NCM`: grupos de dígitos con punto, guion o espacio,
letra opcional), `despacho_lector.py:134` (`_POSICION`: sólo puntos, letra
pegada) y `sufijos_arca.py:34` (`_partes`: saca puntos y cualquier blanco,
exige 11 dígitos). El defecto de esta pieza salió de ahí: uno de los tres no
aceptaba lo que la pantalla arma.
- (a) A la cola de limpieza: un solo normalizador, con su tabla de formas.
- (b) Pieza ahora, antes de PRESUPUESTO-CLIENTE-1.
- (c) Dejarlo: cada uno lee una fuente distinta.

Recomiendo **(a)**. Hoy no conozco otro camino de la pantalla que falle, y
unificar toca lo que lee el despacho y lo que arma el sufijo: es una pieza
con su propio rojo, no un agregado a esta. `COLA-LIMPIEZA.md` no lo edito yo.

## Lo que no coincide con lo que dijiste

- **El modelo.** Escribiste que Emi me pasaba a Fable al borde de pieza. Lo
  cambió antes: el arreglo, los casos, el adversario y `/code-review` son de
  Opus 5.5; las puertas finales sobre `f186ecf`, el rojo repetido y este
  informe son de Fable 5.2. Los revisores de `/code-review` corrieron con
  Opus.
- **«Después», punto 4** (`smoke_friccion.sh` al día con ABUSO-1): el script
  ya espera «Evento sin sesión no admitido» en los dos eventos y 401 en
  by-cuit (SMOKE-1). Me parece hecho; decime si falta algo.

## Comandos

```bash
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov tests/test_memoria_pantalla.py tests/test_guardar1.py   # 32 passed (necesita node; sin node, 4 skipped)
scripts/testing/e2e_maria.sh        # E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.
# rojo: el arreglo revertido
git show d497551 -- proyecto_maria/services/client_memory.py | git apply -R
python -m pytest -q --no-cov tests/test_memoria_pantalla.py tests/test_guardar1.py   # 4 failed, 28 passed
git checkout -- proyecto_maria/services/client_memory.py
```

## Rojos

Con el arreglo revertido (corrido de nuevo hoy sobre `a471763`):

```
FAILED tests/test_memoria_pantalla.py::test_pantalla_alimenta_memoria[individual]
FAILED tests/test_memoria_pantalla.py::test_pantalla_alimenta_memoria[lote]
FAILED tests/test_memoria_pantalla.py::test_pantalla_alimenta_memoria[sugerencia]
FAILED tests/test_guardar1.py::test_la_forma_del_ncm_que_guarda_el_historial[8471.30.00.900 R-84713000]
=================== 4 failed, 28 passed, 3 warnings in 5.80s ===================
E   AssertionError: 8471.30.00.900 R
E   AssertionError: assert None == '84713000'
```

El cuarto dato del caso, «base» (la posición sin letra), sigue verde con el
arreglo revertido: es el control.

Con la regex aflojada a `\s?` (copiado del mensaje de `f186ecf`):

```
FAILED ...[8471.30.00.900\tR-None]
FAILED ...[8471.30.00.900\xa0R-None]
2 failed, 30 passed
```

## Puertas sobre f186ecf

| puerta | resultado |
|---|---|
| suite completa | `=== 5832 passed, 355 skipped, 3 xfailed, 104 warnings in 1117.20s (0:18:37) ====`, `exit=0` |
| `python -m compileall -q proyecto_maria` | `exit=0` |
| `scripts/testing/e2e_maria.sh` | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.`, `exit=0` |
| `smoke_friccion.sh` | `==> OK · telemetría y alias session/state rechazan sin sesión + by-cuit protegido`, `exit=0` |
| `tests/test_memoria_pantalla.py tests/test_guardar1.py` | `32 passed, 3 warnings in 5.72s` |
| arnés Postgres | no corrido: la pieza no toca SQL |
| `ataque_aislamiento.sh` | no corrido: no cambia datos, sesión ni permisos |
| `/security-review` | no corrido: no es pieza de §3 |
| sabotaje con guion propio | no hay: no es pieza de §3; el rojo es el de arriba |

Archivos de producto tocados: `proyecto_maria/services/client_memory.py`.

## chequeo-6 7d5c9e7 f186ecf

```
chequeo-6 7d5c9e7..f186ecf: avisos para mirar, no un veredicto
producto +2/−2
arnés +87/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/services/client_memory.py: 308 → 308
avisos: 0
```

## Revisión

**Adversario: `adversario-sonnet-alto` (Sonnet, alto), sobre `195af11`.** Nada
de severidad alta.

| # | hallazgo | sev. | qué pasó |
|---|---|---|---|
| 1 | tab y NBSP antes de la letra no tenían negativo | media | arreglado en `f186ecf`, con su rojo |
| 2 | el caso corría node al importar; sin node, error de colección | media | arreglado: fixture con skip |
| 3 | guardar-uso guarda el NCM crudo en `ncm_historial` | baja | ya estaba; riesgo |
| 4 | `.upper()` convierte «ſ» en S | baja | ya estaba; riesgo |
| 5 | la memoria del proveedor (`save_products`) no valida la forma | baja | fuera de la pieza; riesgo |
| 6 | `renglon_para_catalogo` ahora acepta la forma con espacio | baja | lo que lee de documentos pasa antes por `_POSICION`, que no cambió |
| 7 | los separadores valen en cualquier lugar de la posición | baja | ya estaba; riesgo |
| 8 | largo 16, dentro de los 20 de la columna | info | — |

**`/code-review high`, `7d5c9e7..195af11`, revisores Opus.**

| # | hallazgo | qué pasó |
|---|---|---|
| 1 | node al importar el módulo de prueba | arreglado en `f186ecf` |
| 2 | el extractor de funciones se cuelga si las llaves no cierran | arreglado: corta y avisa |
| 3 | `_POSICION` y `_NCM` no aceptan lo mismo | D165 |
| 4 | varios lectores de posición SIM | D165 |
| 5 | tres de las cuatro formas dan el mismo texto | queda: son tres caminos distintos de la pantalla |
| 6 | el caso prueba los formateadores, no el body que arma `finalize.js` | hueco real del caso; ese camino lo cubre `e2e_maria.sh` |
| 7 | repite el cargador de `despacho1c_pantalla.js` | queda; va con el punto 1 de «Después», que toca ese archivo |
| 8 | «learn y la operación dan 200 sin aprender» | descartado, abajo |
| 9 | el fixture `client` viene de `test_prelaunch_block2` | baja; queda |
| 10 | nombre largo del caso | arreglado |

**El 8, verificado contra el código.** La operación sí avisa: devuelve
`historial_guardado: false` (`main.py:8242-8279`) y la pantalla muestra
«Algunos productos no quedaron en la memoria…» (`finalize.js:780`, `:1220`).
`learn` devuelve la cuenta en `aprendidos` (`main.py:8876`) y ninguna pantalla
lo llama: `saveCatalogLearn` va al catálogo del proveedor. No es un defecto de
esta pieza y no lo traigo como D.

## Riesgos

- Los de la tabla del adversario 3, 4, 5 y 7: ya estaban y no los toqué.
- El caso nuevo depende de node. Sin node se saltea (4 skipped) y la forma
  queda cubierta sólo por la fila de `test_guardar1` y por la e2e.
- El caso lee las funciones de `ncm.js` por nombre: si se renombran, da rojo
  con «no está en» o «llaves sin cerrar», no un verde falso.
- Los 355 skipped de la suite no los desglosé en esta corrida.
