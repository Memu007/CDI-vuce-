# Dev 1 → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## MARIA-1b, devolución — entregada sobre `beea9eb`

**Resultado:** los cinco puntos están hechos, cada uno con rojo antes y verde
después. Los dos archivos reales siguen saliendo idénticos. La rama ya trae
la tuya (RENDIMIENTO-1 y 1b, MARIA-1a, 1d, 3 y 4) y los choques están
resueltos. Un subagente (Opus, esfuerzo alto) atacó la devolución: lo que
encontró dentro de la pieza está arreglado, y lo que queda afuera va abajo.

**Lo que decidís vos:** D26 (abrir un libro armado sigue costando segundos,
y un caso extremo, minutos) y D23 a D25, de PUNTA-A-PUNTA-1. Ninguna frena
esta entrega.

| | SHA |
|---|---|
| Base (devuelta) | `21a7a7e`; con tu rama integrada, `a443cc2` |
| Merge de tu rama y choques | `61bd46a`, `41e04bd` (pruebas de la Dev 2 con los datos que MARIA-1b exige) |
| Producto | `ec85f9a`, `d6249e1`, `eff0930` |
| Pruebas, sabotajes y pantalla | `e705f07`, `f60efdd`, `522223e`, `d493768`, `e05f21c`, `3d14ef8`, `beea9eb` |
| CHANGELOG | `9c78b29`, `77dbc5e` |

### Qué cambió, punto por punto

1. **NaN e infinito no dejan generar** en cantidad, valor, peso, flete,
   seguro y gastos. Tampoco los subítems ni un monto que desborda al
   multiplicar (1e200 × 1e200 daba `MARTFOB=inf`), con el mismo texto que un
   monto inválido. `/api/validate/smart` ya no da 500: los números no
   finitos de la respuesta van vacíos. La exportación tampoco los escribe.
2. **Las otras hojas se miran con un presupuesto que corta la lectura
   misma.**
   - Se lee el XML de cada hoja directo del `.xlsx`. El presupuesto es de
     4 MB por hoja, 16 MB en total y 3 s: si se pasa, la lectura se corta
     sola y el hilo queda libre.
   - Si no se pudo mirar todo, o falló, la operación lleva
     `hojas_excel_sin_revisar` y el semáforo dice «No se revisaron todas las
     hojas del libro», con su «Descartar».
   - Las fórmulas sin valor guardado cuentan como dato. Las hojas de gráfico
     no cuentan como hoja.
3. **El CUIT del importador, sólo con dígitos 0-9.**
4. **Toda moneda que no sea DOL avisa:** «sólo DOL está confirmada con un
   archivo real. Confirmá con el despachante que ése es el código de MARIA».
5. **D22 (a):** `/generate_maria_export` limpia todos sus textos como
   `/generate_maria`.

### Rojo antes y verde después

```
test_maria1b_devolucion.py sobre a443cc2: 28 failed, 11 passed
  (las 11 que pasan ya estaban cubiertas: NaN en la cabecera, por MARIA-3; DOL; libro normal)
  la subida normal detrás de dos libros armados: «504 a los 70.4 s» (lectura_excel_demasiado_larga)
lo que encontró el subagente, sobre 522223e: 13 failed (subítems, desbordes, 500, exportación, fórmula, gráfico)
pantalla_maria1b.js: a443cc2 → «FALLA: el semáforo no dice que no se revisaron todas las hojas»; 3d14ef8 → OK
```

### Corrido, con su salida

```
suite como la CI (venv-limpio, ENVIRONMENT=testing, sus --deselect), worktree limpio en 3d14ef8:
  1214 passed, 102 skipped, 10 deselected, 1 xfailed · fin: 0
sabotajes en 3d14ef8: maria1b → 34 en ROJO, «sabotajes con falla: 0» (empieza comprobando que sin sabotaje está en verde)
sabotajes en 522223e: excel1, rendimiento1, rendimiento1b, admin1, admin2, punta_a_punta1 → «con falla: 0»;
  maria2 y los de la Dev 2 maria1c, 1d, 4 → OK; maria3 → 1 con falla (abajo)
pantallas en 3d14ef8: pantalla_excel1.js / pantalla_maria1b.js / pantalla_maria1c.js → OK / OK / OK
smoke_friccion.sh (levantar.sh 3d14ef8) → ==> OK
ataque_aislamiento.sh (beea9eb) → «MARIA.TXT de Ana: MARIA_FAC_0001-00012345.TXT» · Bloqueado: 22 · Fugas: 0
```

### Comandos para vos

```bash
git fetch origin claude/dev1-tecnica && git checkout beea9eb
<venv>/bin/python -m pytest -q --no-cov tests/test_maria1b_devolucion.py tests/test_maria1b_controles.py   # 90 passed
PY=<venv>/bin/python scripts/testing/sabotajes/maria1b.sh beea9eb                                       # «sabotajes con falla: 0»
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh beea9eb 8080
BASE_URL=http://127.0.0.1:8080 node scripts/testing/pantalla_maria1b.js <cualquier .xlsx>             # «OK: pantalla MARIA-1b»
```

### Lo que vale la pena saber

- **El ataque de aislamiento pasaba por la razón equivocada** después de
  integrar MARIA-3. Generar pide la fecha de emisión, Ana no llegaba a
  generar su TXT y el paso 4 se salteaba: daba «Bloqueado: 19 · Fugas: 0».
  Ahora lleva la fecha, y si Ana no genera, la puerta no pasa (`beea9eb`).
- **Un sabotaje de la Dev 2 queda en verde, y no es un defecto.** En
  `sabotaje_maria3.sh`, `flete_sin_validar` saca la validación del flete en
  el generador, pero mi control de antes de generar también lo valida, así
  que la prueba sigue viendo un 400. Hay que avisarle a la Dev 2 para que el
  sabotaje saque los dos. No toqué su script.
- **En el merge toqué pruebas de la Dev 2** (`41e04bd`): llevan moneda y un
  CUIT válido; el archivo real de 2025 se compara con sólo la línea del CUIT
  cambiada; un flete negativo lo frena antes MARIA-1b, con la lista de
  errores. La prueba de EXCEL-1 elige el estado de la mercadería (MARIA-4).
- **`smoke_test.sh` da 5 de 11 en rojo, igual en `7b119b6`.** Crea
  clientes y sube archivos sin sesión, y recibe 401. No es de esta pieza.

## Decisiones

- **D26 — Abrir un libro armado sigue costando, y no es de esta pieza.**
  Viene de EXCEL-1, y openpyxl lo hace en dos lugares: al validar y al leer
  la primera hoja. Si las hojas no declaran su medida, las recorre enteras
  para medirlas. Medido por el subagente con el libro de la prueba (90 MB
  descomprimido):
  - Unos 7 s por paso. Con dos libros delante, la subida normal sale bien
    (200 en 12,8 s).
  - Con cuatro libros delante, la normal da 400 a los 30 s («tardó
    demasiado»), en la validación.
  - Un `sharedStrings.xml` con 19 millones de entradas vacías (134 KB
    comprimido) tarda 93 s y usa 1,9 GB de memoria.

  Opciones:
  - (a) Una pieza chica: contar las hojas desde `xl/workbook.xml` en vez de
    abrir el libro, y rechazar antes de abrir un libro cuyos textos
    compartidos o cuya primera hoja pasen de un tamaño.
  - (b) Dejarlo con el tope de 100 MB que ya existe.

  **Recomiendo (a)**: lo de la memoria puede tirar el servidor.

- **D23, D24 y D25 — Lo que encontró PUNTA-A-PUNTA-1** (sigue en curso, ver
  abajo). La pantalla no puede producir los archivos reales tal cual:
  - **D23:** el número de operación sale «FAC_» + número de factura, no el
    número de 9 dígitos. El generador saca de ahí `NDDTIMMTRN=FAC_0` y
    `IEXT=FAC_0-01/25`, que no parecen valores válidos para MARIA.
  - **D24:** la pantalla no tiene dónde cargar subítems. La procedencia ya
    la resolvió MARIA-3.
  - **D25:** la referencia de la factura (`LDVDREFDOC`) sale del número de
    operación (`E126-1`), y el archivo real lleva el de la factura (`110`).

  Las tres son de la pantalla de generar o del generador (Dev 2).
  **Recomiendo** una pieza de la Dev 2 que deje cargar el número de
  operación y la referencia de la factura, y que sume los subítems a la
  pantalla, empezando por D23.

## Qué no corrí y riesgos

- La ruta `.xls` (xlrd) para mirar las otras hojas: no hay con qué armar un
  `.xls` de prueba. Tiene el mismo tope de tiempo, revisado entre hoja y
  hoja y entre fila y fila.
- `cuit_agr` y `vendedor_id` todavía aceptan dígitos de ancho completo, y el
  TXT los escribe tal cual. El punto 3 era el CUIT del importador. Se
  arregla en una línea si querés.
- Los tiempos son de esta máquina (4 núcleos).

## Sigo con

PUNTA-A-PUNTA-1, que ya estaba en curso cuando llegó la devolución
(`9610f6d`, `a443cc2`). La prueba recorre la pantalla v2 por HTTP con login,
CSRF, PDF con Gemini simulado y Excel, y compara byte a byte. Hoy da
`5 passed, 1 xfailed` y sus 5 sabotajes en rojo. Antes de entregarla falta
lo que encontró su revisión:
- la NCM con el formato que guarda la pantalla (`8479.89.99.900 H`);
- una factura de dos ítems, para el prorrateo;
- números con coma decimal;
- que su script de sabotajes compruebe la base en verde.

Después, EXCEL-2.

Última vuelta: 2026-10-07
Contexto: ~60 %.

`/compact conservar: Dev 1 de CDI, rama claude/dev1-tecnica. MARIA-1b
devolución entregada sobre beea9eb (suite 1214 en 3d14ef8, maria1b.sh 34
rojos); D26 (abrir libros armados), D23-D25 abiertas. Sigue PUNTA-A-PUNTA-1
(tests/test_punta_a_punta1.py, sabotajes/punta_a_punta1.sh); pendientes en
«Sigo con» de PARA-PM.md: NCM «8479.89.99.900 H», 2 ítems, coma decimal,
base verde en el script. Después EXCEL-2.`
