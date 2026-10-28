# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## EXCEL-2b, vuelta de tu revisión sobre `b3ac325` (más el agregado de GUARDAR-2)

| Qué | SHA |
|---|---|
| Pruebas: en qué hilo leen las otras hojas y los ítems, índice ilegible, umbral enorme (rojo: `EXCEL_LIVIANO_MB=1e308` da 500) | `271c0db` |
| Pruebas: la aserción del umbral enorme ya no desborda ella misma | `f5f8f75` |
| **Producto:** un tope en MB que no entra en bytes vale el de defecto; CHANGELOG con lo medido | `ce3ac05` |
| Pruebas: GUARDAR-2, dos clientes del mismo despachante no comparten historial | `f567adb` |
| Sabotajes de los puntos 2 y 4 | `83871a5` |
| Pruebas: hallazgos del adversario Sonnet (rojo: `EXCEL_MAX_DESCOMPRIMIDO_MB=1e308` da 400) | `43fd20d` |
| **Producto:** el cuarto tope pasa por la misma lectura | `cedb3ff` |
| Sabotajes de esos hallazgos | `606dda5` |
| Informe | este commit |

Entre `606dda5` y este informe van `0fa30bf`, `36aba87` y `6da850e` (la vuelta
de ORDEN-1), `836da59` (patrones de `cobro_mp1.sh` que perdió MP-2, sólo
sabotajes) y `630652d` (merge de tu rama hasta `47e7110`, sin `PARA-DEV.md`).
No son de esta pieza: los informo en la entrega siguiente. Las puertas de esta
tabla corrieron sobre `606dda5`, sin ellos.

Archivo de producto tocado en esta vuelta: `proyecto_maria/security/file_security.py`
(y `CHANGELOG.md`).

**Resultado.** Cerré los puntos 2 a 5 y el agregado de GUARDAR-2, cada uno con
su prueba y su sabotaje. **El punto 1 no está cerrado:** los libros chicos pero
caros de leer siguen entrando al carril liviano. Lo decidís vos en la **D32**.

## Decisiones

**D32. Libros chicos en bytes pero caros de leer (tu punto 1).** No lo arreglé
en esta pieza. Los números:

| Forma | Quién | Tamaño | Lectura |
|---|---|---|---|
| Celda en la fila 1.048.576, columna G | PM | 1496 bytes | 5,2 s, 400 MB |
| Lo mismo con `<dimension>` hasta la columna IV | adversario de la PM | — | 179 s, 6,4 GB |
| `styles.xml` repetido | adversario de la PM | 4,6 KB comprimido | 19,9 s |
| Celda en la fila 1.048.576, columna AZ | yo, sobre `bdc902d` | 1578 bytes | 10,25 s, 1476 MB |
| Dos de esas trampas delante de una subida normal | yo | — | la normal tarda 5,5 s (más que el tope de D5) |

Lo lento ya estaba en la base. Lo nuevo es que ahora ocupa el carril de las
subidas normales.

- **(a)** Riesgo aceptado: se entrega así y el CHANGELOG dice que el carril
  liviano protege del tamaño, no de la densidad.
- **(b)** En el hilo liviano, antes de leer, se recorre la primera hoja (2 MiB
  como mucho, porque entró al carril) buscando la fila y la columna más altas
  en `r="…"` y en `<dimension>`. También se cuentan los `<xf` de `styles.xml`
  y las entradas del `sst`. Si alguno pasa su tope, la lectura va al carril
  pesado. El `.xls` lee siempre en el pesado.
- **(c)** Sólo el `.xls` va siempre al pesado.

**Recomiendo (b).** Es la única que devuelve la garantía de D5 frente a las
formas medidas, y cuesta milisegundos. Su límite: es una heurística, cierra
las formas conocidas y no las que falten descubrir. Si elegís (b), va como
pieza propia, con rojo primero: un caso por forma (celda lejana, `<dimension>`,
estilos, `sst`, `.xls`) y un sabotaje por tope. No la metí acá porque cambia
el producto en un lugar que no estaba en tu devolución, y prefiero que lo
decidas con los números a la vista.

## Tus puntos

1. **Densidad:** la D32, arriba.
2. **En qué carril leen las otras hojas y los ítems:** casos en `271c0db`.
   Sabotajes en `83871a5`: `_otras_hojas_con_datos` con
   `pool=_pool_lectura_excel()` y `extract_items_from_excel` en el pool
   pesado. Los dos dan rojo.
3. **`excel2b.sh` salía con 1:** arreglado en `bdc902d`, que ya iba en la entrega de `d2de9fb`, posterior a `b3ac325`. La
   prueba de D5 afirma el tiempo antes que los carriles, así que el sabotaje
   dice «esperó detrás de las pesadas». Corrida de hoy, más abajo.
4. **`1e308` y los dos mutantes:**
   - `EXCEL_LIVIANO_MB=1e308`: arreglado en `ce3ac05`. El control se hace
     sobre los bytes (`math.isfinite`); si no entra, vale el de defecto.
   - El adversario Sonnet encontró el mismo error en el cuarto tope:
     `EXCEL_MAX_DESCOMPRIMIDO_MB=1e308` daba 400 «cannot convert float
     infinity to integer» en toda subida de Excel. Tenía su propia lectura.
     Arreglado en `cedb3ff`: los cuatro topes pasan por `_mb_de_entorno`.
     Prueba parametrizada con las cuatro variables.
   - `except Exception: return True`: lo mata el caso del índice ilegible
     (`271c0db`), con su sabotaje.
   - `_LIVIANO_IMAGENES_LECTURAS` de 20 a 100000: sabotaje en `83871a5`. En
     `606dda5` sumé 19 y 21, con una prueba que cuenta exactamente 20
     lecturas.
5. **CHANGELOG:** dice 1,5 y 1,7 s, lo medido (`ce3ac05`).

**GUARDAR-2 (tu agregado).** `f567adb`: dos clientes del mismo despachante, con
igual nombre y CUIT, no comparten historial ni en `/api/catalog/lookup` ni en
`/api/ncm/sugerir`. El adversario Sonnet vio que faltaba el otro sentido, el
guardado: en `43fd20d`, guardar el mismo NCM en el otro cliente le crea su
propio historial, y guardar otro NCM con la misma descripción no pisa al
primero. Sin cambio de producto: los filtros ya estaban. Dos sabotajes en
`606dda5`, uno por filtro.

## Hallazgos de la revisión

Adversario Sonnet, esfuerzo alto, sobre `83871a5`:

| Sev. | Hallazgo | Qué hice |
|---|---|---|
| MEDIA | `EXCEL_MAX_DESCOMPRIMIDO_MB=1e308` da 400 en toda subida de Excel | Rojo en `43fd20d`, arreglo en `cedb3ff`, sabotaje en `606dda5` |
| MEDIA | GUARDAR-2 no probaba el guardado cruzado entre clientes | Dos casos en `43fd20d`, dos sabotajes en `606dda5` |
| MEDIA, preexistente | `MAX_UPLOAD_MB` (`main.py:4084-4089`): con `inf` o `1e308` da 500; con `nan`, ValueError; con `-0`, tope 0 | A riesgos. Fuera de la pieza |
| BAJA | Nada distinguía 19 o 21 lecturas de cabezas de imagen | Prueba que cuenta exactamente 20 (`43fd20d`) y sabotajes con 19 y 21 |
| BAJA | Nada distinguía si el `except` de la cabeza de imagen cortaba la medida | Prueba con una entrada DEFLATE rota (`43fd20d`) y sabotaje que lo cambia a `ZeroDivisionError` |
| BAJA | Los topes absurdos se aceptan: `1e300` es un número de 307 cifras; `1e-9` da 0 bytes | A riesgos |

El adversario no verificó el sabotaje de D5 ni los tiempos del CHANGELOG.

**No corridos en esta vuelta:** el adversario Opus, `/code-review` y
`/security-review`. Es una devolución sin dinero, sesión ni permisos, y por
eso alcanza un Sonnet alto. Los cuatro sí corrieron en la entrega de `d2de9fb`.

## Puertas (sobre `606dda5`)

| Puerta | Salida |
|---|---|
| Rojo antes del arreglo de `cedb3ff` | «FAILED tests/test_excel2b.py::test_ningun_tope_de_excel_enorme_rompe_la_subida[EXCEL_MAX_DESCOMPRIMIDO_MB]», «400 {"detail":"Invalid Excel file: cannot convert float infinity to integer"}», «1 failed, 48 passed» |
| `pytest tests/test_excel*.py tests/test_guardar2.py` después | «1193 passed, 3 warnings in 138.19s», salida 0 |
| `excel2b.sh 606dda5` | 25 «ROJO», «sabotajes sin rojo: 0», salida 0 |
| `guardar2.sh 606dda5` | 12 ROJO, «sabotajes con falla: 0», salida 0 |
| Suite completa, worktree limpio en `606dda5` | `4178 passed, 121 skipped, 3 xfailed in 586.81s (0:09:46)`, salida 0 |
| `compileall -q proyecto_maria` | salida 0 |
| `smoke_friccion.sh` contra la API levantada en `606dda5` | «==> OK · telemetría + alias session/state + by-cuit protegido», salida 0 |

## Comandos

```bash
git fetch origin claude/dev-tecnica && git checkout 606dda5
export GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
PY=$PM_DIR/venv/bin/python scripts/testing/sabotajes/excel2b.sh    # 25 «ROJO», «sabotajes sin rojo: 0»
PY=$PM_DIR/venv/bin/python scripts/testing/sabotajes/guardar2.sh   # 12 «ROJO», «sabotajes con falla: 0»
EXCEL_MAX_DESCOMPRIMIDO_MB=1e308 $PM_DIR/venv/bin/python -m pytest -q --no-cov tests/test_excel2b.py -k enorme   # passed
```

## Riesgos y lo no corrido

- **D32**, arriba: hasta que la decidas, un libro chico armado para ser lento
  le hace esperar a la subida normal.
- `MAX_UPLOAD_MB` con `inf`, `nan` o `-0` (preexistente, `main.py:4084-4089`).
- Los topes de Excel aceptan valores absurdos pero finitos: `1e-9` da un tope
  de 0 bytes y toda subida de Excel va al pesado o se rechaza.
- `ataque_aislamiento.sh`: no corrido. Esta vuelta no toca sesión ni permisos;
  GUARDAR-2 sólo suma pruebas sobre filtros que ya existían.
- Sigue sin commitear en mi árbol la vuelta de ORDEN-1 (`app_v2.js`,
  `pantalla_orden1.js`). No está en este SHA. Va en su propia entrega,
  después de esta.

/compact conservar: Dev 1 (técnica), rama claude/dev-tecnica. EXCEL-2b entregada en este commit (D32 abierta). Sigue, en orden: devolución de ORDEN-1 (cambios sin commitear en app_v2.js y pantalla_orden1.js), COBRO-MP-1 (A–E), COBRO-CORTE-1, COBRO-MP-2, AISLAMIENTO-2, LIMPIEZA-1, BACKUP-1a (7 puntos). Informes en el scratchpad (informe_*.md); push y aviso a la PM principal por cada uno.
