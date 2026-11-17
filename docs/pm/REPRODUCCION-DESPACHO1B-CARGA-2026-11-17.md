# DESPACHO1B-CARGA: `962bc88f` (informe `ee4aa981`), 2026-11-17, PM

**Veredicto: aceptada, integrada.** Base `50d32c26`. Sólo cambia `tests/test_despacho1b.py`.

## Diff

`chequeo-6.py 50d32c26 962bc88f`:
```
producto +0/−0
arnés +40/−24
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```
El ayudante `_recolector_sin_la_suite` (`gc.collect()`, `gc.freeze()`, `gc.unfreeze()` al salir)
rodea sólo la lectura en los seis casos que leen con temporizador dentro del proceso de pytest.

## Lo que corrí (worktrees en el scratchpad de la PM, 20:50 a 21:02 UTC)

| Qué | SHA | Resultado |
|---|---|---|
| `tests/test_despacho1b.py` solo | `962bc88f` | «285 passed», 0 «Exception ignored» |
| corte desarmado (`yield; return` antes de `signal.signal(signal.SIGPROF, cortar)`) | `962bc88f` | «6 failed, 279 passed» |
| 7 corridas en paralelo de `test_catalogo3.py` + `test_despacho1b.py`, 4 núcleos | `50d32c26` | 7 × «396 passed»; 7 ticks tragados, todos en `test_un_corte_por_cpu_en_la_primera_hoja_no_dice_que_es_escaneado` |
| la misma carga | `962bc88f` | 7 × «396 passed»; 0 ticks tragados |
| `tests/test_despacho1b.py` solo, sin carga, 3 veces (negativo mío) | `50d32c26` | 3 × «285 passed»; 3 ticks tragados, en el mismo caso |

Los seis rojos del desarmado: `una_sola_hoja_cara_se_corta_en_el_tope_de_cpu`,
`el_lector_aparte_corta_una_sola_hoja_cara`, `el_tope_de_cpu_cubre_entender_el_texto`,
`las_hojas_leidas_antes_del_corte_dan_sus_productos`, `un_corte_por_cpu_en_la_primera_hoja_no_dice_que_es_escaneado`
y `un_corte_por_cpu_que_se_traga_un_finalizador_vuelve_a_cortar`. Dos no llevan el ayudante y está
bien: `leer_despacho_aparte` y `_medir_aparte` leen en un proceso aparte, donde no está la suite.

**No reproduje el rojo** (0 de 7 en la base; ella lo vio 1 en 21). Sí el paso de antes, el tick
tragado por un finalizador ajeno (`_collection_gced` de sqlalchemy): 7 de 7 cargado y 3 de 3 sin
carga en la base; 0 con el arreglo. Que aparezca sin carga cierra el criterio 7: la causa está en
la prueba (lee dentro del proceso de pytest) y la carga sólo agranda la ventana.

`962bc88f` es de las 18:35 UTC; su `despacho1b.sh` con Postgres (18:47 a 20:48) corrió sobre ese SHA.

## No corrido, y por qué

Suite completa, `e2e_maria.sh`, `despacho1b.sh` mío y adversarios: la pieza cambia sólo un archivo de
pruebas, con producto +0/−0; el archivo entero y el sabotaje alcanzan.

## Decisiones

- **D271** (`tests/test_rendimiento1d.py:97`, tope de 0,2 s dentro del proceso, sin el ayudante): no
  medido. Va a la pieza chica que sigue: primero se mide si ahí se traga un tick (solo y con la misma
  carga). Si aparece, el ayudante pasa a `tests/pdf_bombas.py` y lo usan los dos archivos; si no,
  riesgo escrito con lo medido.
- **D272** (el caso del finalizador da `cortes == 1` 17 en 6000 fuera de pytest: el primer tick cae
  en la condición del `while`, fuera del `try` interno): (a), en la misma pieza chica.

## Riesgos escritos

Un generador suspendido que quede vivo; hilos que comparten `ITIMER_PROF`; seis `gc.collect()`, cerca
de 1 s en un archivo de 50 s.
