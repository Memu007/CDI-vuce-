# Dev 1 → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## PUNTA-A-PUNTA-1 — entregada sobre `3b52bc9`

**Resultado:** la prueba hace el recorrido de Emi por HTTP, como la pantalla
v2:
- login de verdad, con cookie y CSRF;
- la factura en PDF (Gemini simulado con los datos del archivo real) y en
  Excel;
- la NCM con el formato que guarda la pantalla;
- `/api/validate/smart`, la tarjeta del despachante, `/generate_maria` con
  el pedido de `buildMariaRequest`, y la descarga.

El archivo real de 2025 sale **igual byte a byte salvo el número de
operación** (D23). El de subítems sale igual línea por línea salvo D23, D24
y D25. Es una pieza de pruebas: no toqué el producto.

**Lo que decidís vos:** nada nuevo. D23, D24 y D25 quedaron como `xfail`
estrictos con la D en el motivo (`3b52bc9`).

| | SHA |
|---|---|
| Prueba y sabotajes | `9610f6d`, `a443cc2`, `1c2656e`, `3170aa7`, `dff7be1` (docstring), `3b52bc9` (xfail de D23 a D25) |

### Qué prueba (`tests/test_punta_a_punta1.py`, corre en la CI: no está entre los `--deselect`)

- **PDF y Excel → archivo real de 2025:** igual salvo las líneas de D23,
  nombradas una por una. El archivo sin cambios queda como `xfail`
  estricto: el día que la pantalla lo produzca, la prueba avisa.
- **Subítems, por PDF y por Excel** → el archivo real entero, línea por
  línea. Ese archivo se guardó con LF y sin completar los campos.
- **Factura con coma decimal** («5.000,00», peso «1.220») → el mismo
  archivo.
- **Dos productos:** el flete y el seguro se reparten por el FOB, y la base
  imponible cierra.
- **Sin el token CSRF da 403, y sin sesión 401:** el recorrido no usa
  atajos.

### Corrido, con su salida

```
pytest tests/test_punta_a_punta1.py: 7 passed, 3 xfailed (D23, D24, D25)
sabotajes (scripts/testing/sabotajes/punta_a_punta1.sh 3b52bc9): base en verde y 9 en ROJO, «sabotajes con falla: 0»
  lector (flete perdido; la coma decimal), mapeo del Excel (precio y peso cruzados), ruta (procedencia),
  generador (seguro fuera de la base, FOB del subítem, espacio de la NCM, flete sin repartir, FOB total = el mayor)
suite como la CI (venv-limpio, ENVIRONMENT=testing, sus --deselect), worktree limpio en 3b52bc9
(con tu integración 6ea8ca9): 1216 passed, 102 skipped, 10 deselected, 3 xfailed · fin: 0
```

### Lo que vale la pena saber

- Lo encontró su revisión (Opus, esfuerzo alto) y está corregido:
  - La NCM iba sin el formato de la pantalla, y un generador que dejara el
    espacio de «8479.89.99.900 H» pasaba en verde.
  - Con un solo producto no se veía el prorrateo.
  - Ninguna factura traía coma decimal.
  - El script de sabotajes no comprobaba que la base estuviera en verde.
- **El peso de un producto con más de una unidad no se mira.**
  - Hoy el generador toma `peso_unitario` como el peso de la línea:
    2 unidades de 260 kg salen `QARTKGRNET=260.000`.
  - La semántica del peso la está cambiando MARIA-5 (Dev 2). Cuando entre,
    hay que sumar ese caso.
- Copiar el pedido de la pantalla en Python tiene un riesgo: si
  `finalize.js` cambia y la copia no, la prueba no lo ve. Lo dice el
  docstring de `pedido()`.

## Decisiones

No hay D nuevas. D23 y D25 quedaron como `xfail` estrictos, con la D en el
motivo, como pediste, y D24 también, mientras lo decide Emi.

## Qué no corrí y riesgos

- El peso con más de una unidad (lo cambia MARIA-5).
- La prueba copia el pedido de la pantalla: si `finalize.js` cambia, hay
  que actualizarla.

## Sigo con

EXCEL-2, como está en el canal (con D26 (a) y lo de paso). Si
PUNTA-A-PUNTA-1 vuelve con devolución, eso va primero.

Última vuelta: 2026-10-07
Contexto: el que mide la PM con get_session (al entregar MARIA-1b eran 38 %).

`/compact conservar: Dev 1 de CDI, rama claude/dev1-tecnica. MARIA-1b y
EXCEL-1 aceptadas e integradas (6ea8ca9). PUNTA-A-PUNTA-1 entregada sobre
3b52bc9 (suite 1216, 3 xfail D23-D25). Sigue EXCEL-2 (canal: D18, CSV, aviso
de mapeo, D26 (a) con 8 libros sin <dimension> y sharedStrings de 19 M < 1 GB,
y de paso 10**400 → 400 y cuit_agr/vendedor_id sólo 0-9). Entorno:
PM_DIR=/tmp/cdi-dev1, levantar.sh <SHA> <puerto>, venv /tmp/cdi-dev1/venv y
venv-limpio; rutina de la PM trig_01TvMmGfSLDfbcJrf66ZZ7YK.`
