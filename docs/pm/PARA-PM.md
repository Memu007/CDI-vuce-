# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## EXCEL-3 — la proforma china tal como viene: entregada

**Resultado: terminada, para revisar.** El sintético con la forma de la
proforma del 24/10 (en `.xls` y en `.xlsx`) da 48 productos, la cantidad en
m², la unidad `m2`, y el flete y el descuento en la operación. En la base
daba «No se pudieron extraer items».

| Qué | SHA |
|---|---|
| Base (tu rama al empezar) | `3dbfb4e` |
| Producto | `f3f9eb8` + `b76be2f` (devolución de la autorrevisión) |
| Pruebas, sintético y sabotajes | `b7e93f2`, `5bbc48f`, `956a291`, `d1884db` |
| Merge de tu rama (sólo docs) | `15f5b2e` |
| Informe | este commit |

Archivo de producto tocado: `proyecto_maria/main.py` (lectura del Excel:
`try_extract_with_mapping`, `upload_excel_v2`, alias de columnas).

### Decisiones

- **D1. Nombre de los campos que lee VALOR-1.** Devuelvo
  `operacion.flete` (ya existía: la revisión lo muestra y va al TXT) y
  `operacion.descuento` (nuevo, **positivo**: lo que se deduce), más
  `operacion.filas_excel_flete` / `filas_excel_descuento` (filas de la
  planilla). (a) Quedan así y la Dev MARIA los toma en VALOR-1;
  (b) VALOR-1 pide otro nombre o signo y lo cambio. **Recomiendo (a)**: el
  descuento hoy sólo se informa, no resta del FOB, así que el nombre se puede
  ajustar sin romper nada. Pasásela a la Dev MARIA.

Lo demás son supuestos reversibles (abajo, «Supuestos»).

### Qué hace ahora la lectura de Excel

1. Encabezado fuera de la fila 1: ya lo buscaba EXCEL-2; ahora además la NCM
   **no es obligatoria** (una proforma no la trae: sin ella daba 400). Los
   productos entran sin NCM y la revisión la pide.
2. «Specification» es la descripción antes que «Item», salvo que «Item»
   traiga el nombre del producto en tantos renglones con cantidad como
   «Specification» (si no, se rompían facturas con `Item | Specification`).
   «Part No.» va a `codigo_parte`, no a la NCM.
3. Grupo: un renglón sin NCM ni descripción, con cantidad o precio **y con
   sus propias medidas** (Width/Length/Ancho/Largo), toma la descripción y el
   código del de arriba; si trae su propio código, lo conserva. Sin medidas
   no hereda nada (una fila así sigue como «sin leer», regla de EXCEL-1; un
   subtotal sin rótulo no pasa a producto). Con la especificación combinada
   hacia abajo (`.xlsx`) cada renglón conserva el código. Ancho y largo van
   en la descripción **sólo si la planilla agrupa**; en una factura común no
   se tocan.
4. Cantidad en la unidad del precio: con `Unit price (USD/sqm)` y
   `QTY (Rolls)`, la cantidad es la única columna de **la línea** («total»)
   en esa unidad, `SM.TOTAL (sqm)`. La de un rollo (`SQ.MT.`), un largo o
   piezas por caja nunca reemplaza la cantidad; un peso tampoco (G.W./N.W.
   incluidos). Si no hay una sola columna así y la cantidad dice otra unidad,
   aviso. Cada ítem lleva `unidad` (`m2`, `kg`, `m`, `u`); el TXT ya la usa
   (`m2` → `03`). «MT» no se adivina (es tonelada). También corrige el mapeo
   guardado de un cliente que aprendió `QTY (Rolls)`.
5. `Gross Weight(kgs)` = bruto de la línea, dividido por la cantidad (regla
   de pesos vigente, con su aviso).
6. Total, Discount y Freight no son productos, con el rótulo en cualquier
   columna (por ejemplo `Item`). Flete y descuento quedan en la operación con
   aviso que nombra la fila. No se leen como monto: un producto que empieza
   con «Discount …», un descuento en porcentaje (fila sin leer), un flete
   negativo (fila sin leer), ni una nota «Freight included» en otra columna
   de un renglón con medidas.
7. «1st container» en `Item` no es un código ni una descripción.

### Puertas

| Puerta | Resultado |
|---|---|
| Rojo antes (base `3dbfb4e`, primeros 10 casos) | `8 failed, 2 passed` (los 2 verdes son guardas de lo que no cambia) |
| Rojo antes de la devolución (16 casos nuevos sobre `5bbc48f`) | `16 failed, 10 passed` |
| `tests/test_excel3.py` (26 casos) | `26 passed` |
| Focales de Excel, pesos, MARIA-1b, clientes, punta a punta (15 archivos) | `464 passed, 2 xfailed` |
| Sabotajes `scripts/testing/sabotajes/excel3.sh` sobre `d1884db` | `27` rojos por el motivo esperado, `sabotajes sin rojo: 0`, exit 0 |
| Suite completa, worktree limpio en `d1884db`, `--no-cov --timeout=120` | `1757 passed, 102 skipped, 2 xfailed, 25 warnings in 164.14s`, exit 0 |
| `compileall` | exit 0 |
| e2e de la CI (`scripts/testing/e2e_maria.sh`) sobre `d1884db` | «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.», exit 0 |
| `/code-review high` | 10 hallazgos: 7 arreglados con su rojo antes, 3 quedan como riesgo (abajo) |
| Subagente adversario Sonnet alto | 10 reproducidos: 7 arreglados; 3 quedan (abajo) |
| `/security-review` (subagente Sonnet medio) | nada que califique; los avisos van con `textContent` |

**Rojo de entorno conocido:** en una primera suite **con cobertura** sobre
`5bbc48f`, `1 failed, 1741 passed, 102 skipped, 2 xfailed`:
`test_ocho_libros_con_la_primera_hoja_al_borde_del_tope…`, «la subida normal
dio 504 a los 81.8 s». Lo corrí solo en la base `3dbfb4e` y en mi cambio:
con cobertura, **504 a los 79.2 s en la base** y 79.3 s en el mío; sin
cobertura, `1 passed` en 13.78 s y 13.79 s. Es el rojo bajo instrumentación
que ya está en `DECISIONS.md`, no de esta pieza. No subí timeouts ni lo
excluí.

### Hallazgos de la autorrevisión

| Hallazgo | Quién (modelo, esfuerzo) | Qué pasó |
|---|---|---|
| «Cantidad» con mayúscula tapaba la de m²: FOB 6,75 en vez de 216, con aviso que decía lo contrario | Sonnet alto | reproducido; arreglado (`b76be2f`) |
| La única columna en la unidad del precio era la cantidad aunque fuera la de un rollo o caja (FOB dividido por los rollos) | Sonnet alto y `/code-review` | reproducido; sólo «total» |
| G.W./N.W. podían ser la cantidad con precio por kg | `/code-review` | reproducido; arreglado |
| «MT» se leía como metro | Sonnet alto | reproducido; ya no se adivina |
| `Item | Specification` con el nombre en Item perdía el nombre | los dos | reproducido; decide el contenido |
| Ancho y largo se pegaban a cualquier factura; `:g` daba notación científica | los dos | reproducido; sólo si agrupa, sin notación científica |
| «Discount tag labels» (producto) se leía como descuento; «Discount 5%» como USD 5 | Sonnet alto | reproducido; arreglado |
| Flete negativo se sumaba como flete | Sonnet alto | reproducido; fila sin leer |
| «USD -850» no se leía | `/code-review` | reproducido; arreglado |
| Nota «Freight included» en otra columna sacaba el renglón | `/code-review` | reproducido; un renglón con medidas es mercadería |
| Código propio en cada renglón y especificación sólo arriba: se descartaban | `/code-review` | reproducido; heredan la descripción |
| Aviso viejo del catálogo («se usó QTY (Rolls)») quedaba al lado del nuevo | `/code-review` | reproducido; se saca |

### Riesgos que quedan (no arreglados)

- **El descuento no resta del FOB todavía** (lo decide VALOR-1): en la
  proforma real el FOB de la revisión queda inflado en el descuento hasta
  VALOR-1. Hay aviso.
- La NCM no se hereda en el grupo: si una factura agrupada trae la NCM sólo
  en el primer renglón, los de abajo la piden en la revisión. A propósito
  (no se inventa); se puede proponer.
- «Freight cost» en `Item` con texto en `Specification` («CNF Buenos
  Aires») entra como producto: se mira el rótulo de otra columna sólo si la
  descripción está vacía (mirar todas sacaría productos con notas). Media.
- Dos filas «Discount» (un parcial y su total) se suman. Baja.
- Un «Discount» con origen completo en la fila sigue como producto en 0 (como
  antes). Baja.
- Las filas de texto de pago y banco de abajo siguen como «filas sin leer»
  (regla de EXCEL-1): en la proforma, 3 filas en el semáforo.
- El origen no se deduce de «Ningbo, China» del encabezado: entra vacío,
  con el aviso de siempre.
- La lectura del sintético no mide la proforma real: Emi tiene que subir la
  del 24/10 y mirar 48 productos, m², flete y descuento.

### Supuestos reversibles

- Dos pruebas viejas cambian a propósito porque el flete deja de ser «fila
  sin leer» (punto 5 de la tarea): `test_excel1_lectura.py::test_total_flete_y_condiciones_no_son_productos`
  (ahora espera `[5]` sin leer y `flete == 500`) y
  `test_maria1b_controles.py::test_el_excel_deja_en_la_operacion_lo_que_no_se_leyo`
  (su fila «Freight» pasa a «Insurance», que sigue sin leer).
- El `.xls` del sintético va hecho en `tests/fixtures/` (xlwt no está en
  `requirements.txt`); una prueba comprueba que coincide con
  `tests/proforma_china_sintetica.py`.
- La descripción de un renglón queda «PVC TARPAULIN 650GSM BLUE, ancho 3,2 m
  x largo 10 m».

### Comandos para reproducir

```sh
# desde un worktree en d1884db, con un venv de requirements.txt
export ENVIRONMENT=testing GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov -p no:cacheprovider tests/test_excel3.py   # 26 passed
PY=$(which python) scripts/testing/sabotajes/excel3.sh                  # 27 «ROJO», sabotajes sin rojo: 0
# rojo antes: los casos sobre el producto de la base
git worktree add /tmp/excel3-base 3dbfb4e
cp tests/test_excel3.py tests/proforma_china_sintetica.py /tmp/excel3-base/tests/
cp tests/fixtures/proforma_china_sintetica.xls /tmp/excel3-base/tests/fixtures/
(cd /tmp/excel3-base && python -m pytest -q --no-cov tests/test_excel3.py)  # la proforma da 400 «No se pudieron extraer items»
```

Datos reales: nada de la proforma ni de la reunión del 24/10 entró al
repositorio; todo es inventado («DEMO TEXTILE», CUIT 30-00000000-1).

Última vuelta: 2026-10-24 19:12 UTC

/compact conservar: Soy la Dev técnica (Dev 1) de CDI, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica (nunca main), rutina trig_011UpBfwEu9TUzoNUrviqoP5 min 15; aviso a la PM principal session_01B7FVQspcEHF7PqNv797wNM con send_message priority next empezando «Dev técnica:». EXCEL-3 entregada: producto f3f9eb8+b76be2f, pruebas hasta d1884db, merge PM 15f5b2e; D1 (nombre/signo de operacion.descuento para VALOR-1) abierta. Sigue CLIENTE-1, después ESTUDIO-1 y PA-1 (ROADMAP Fase 1b); GUARDAR-2 más adelante desde 2d930c5. Reglas de Emi: sólo me piden la PM o Emi; nada se publica sin su «dale» para el SHA; nunca main; sin secretos ni datos reales (proforma del 24/10 fuera del repo); subagentes hasta alto, sin Fable.
