# Reproducción de MARIA-5 — 2026-10-07

**Último veredicto: devuelta otra vez sobre `6854f34`**, la reentrega con
CATALOGO-NCM-1, por seis puntos chicos (sección del final). Antes, **devuelta** sobre `6d59893` (informe en `87fad88`; base: la rama de
la PM integrada, `8e819dd`) por seis puntos. Tres son nuevos de la pieza, y
dos de ellos ponen un peso equivocado en el TXT sin aviso.

## Lo que corrió la PM

Worktrees limpios, venv armado sólo con el `requirements.txt` de la rama,
Gemini falso, terceros simulados.

| Qué | Salida |
|---|---|
| Rojo antes: `tests/test_maria5_*.py` (seis archivos) con el producto de `8e819dd` | `101 failed, 31 passed` |
| Focal (MARIA-5, archivos reales, subítems, MARIA-3, 1d, 4 y gastos) | `432 passed, 5 warnings in 11.94s` |
| Suite | `1199 passed, 102 skipped, 23 warnings in 98.03s` |
| Hallazgo 1, a mano: `_peso_del_producto({'peso_unitario':25,'peso_total_linea':25}, 10, '.')` | `(25.0, 250.0)`; con `2.5` y `26`, gana el unitario sin aviso: `(2.5, 25.0)` |

Coincide con el informe (1199).

## Subagente de la PM (Sonnet alto)

**Se sostiene:**
- **Peso:** por la pantalla v2, la v1, los dos juntos, cantidades decimales,
  grupos y subítems, sale siempre el peso neto de la línea. No hay
  cantidad × total.
- **Centavos:** unos 11.000 pedidos al azar (1 a 40 ítems, FOB de 0,0001 a
  10¹², flete y seguro con muchos decimales) cierran en `MDDTFOB`, `MDDTFLE`,
  `MDDTASS` y la base, siempre que el FOB total no redondee a 0.
- **Regresiones:** en 1500 pedidos normales sólo cambian `QARTKGRNET` y ±0,01
  en el reparto de flete y seguro.
- **Archivos reales y pantalla:** los dos archivos reales salen idénticos y
  `pantalla_maria5.js` da OK.

| # | Hallazgo | ¿Antes? | Cómo quedó |
|---|---|---|---|
| 1 | **Lector:** si Gemini copia el total en `peso_unitario` y en `peso_total_linea`, el TXT sale con cantidad × total (25 kg en 10 unidades → 250 kg). Sin cruce ni aviso | Nuevo | **Devolución 1** |
| 2 | **Excel:** con «Peso» y «Peso neto» a la vez gana «Peso» como unitario, sin aviso: 30 × 10 = 300 kg en el TXT. Igual con «Weight» y «Net Weight» | Nuevo (el TXT ahora multiplica) | **Devolución 1** |
| 3 | Excel: «Peso total» le gana a «Peso neto» | Nuevo | **Devolución 1** |
| 4 | Excel: un peso en texto («2,5») en una columna de una unidad hace desaparecer la fila sin aviso (sale del FOB). Con «Peso total» se conserva y avisa | Ya pasaba | **Devolución 2** (el informe dice «un peso que no es número se avisa») |
| 5 | Peso `NaN`, `inf`, `1e300` o `0,0004` (sale `0.000`) llega al TXT con 200 | Ya pasaba | **Devolución 3**, en el generador. El control del pedido de MARIA-1b (Dev 1) es otra capa |
| 6 | Si el FOB total redondea a 0,00, el flete y el seguro quedan en la carátula y no en los ítems | Ya pasaba | Se deja: hace falta un FOB menor que medio centavo |
| 7 | **Subítems:** la tolerancia compara la suma sin redondear contra el `MARTFOB` redondeado; pedidos que pasaban ahora dan 400 (5 de 3000 al azar) | Nuevo | **Devolución 4** |
| 8 | Grupo en la v2: bajar la cantidad deja un producto en 0 y «Generar» queda bloqueado | Nuevo | **Devolución 5** |
| 9 | Grupo: al cambiar la cantidad cambia el unitario promedio (declarado por la Dev; pantalla y TXT coinciden) | Nuevo | Se deja |
| 10 | La v1 manda el total en float y da un centavo distinto que la v2 | Parcial | `DECISIONS.md`: la v1 y la exportación divergen |
| 11 | La validación muestra 20,02 y el TXT 20,01 con grupos (el informe dice «la validación muestra el mismo FOB») | Nuevo | **Devolución 6** |
| 12 | El aviso «Gastos a FOB» calcula sin redondear (11,01) y el TXT con (11,02) | Nuevo | **Devolución 6** |
| 13 | Aduana o tipo de destinación «N/A» o «None» salen `001` e `IC04` sin aviso (vacíos ya era así; la pantalla manda el del perfil) | Parcial | Se deja, anotado |
| 14 | `/generate_maria_export` sigue con el reparto en float y el peso de una unidad | Ya pasaba | `DECISIONS.md` (junto con el 10) |

## No corrido por la PM

- Los sabotajes de la Dev (`sabotaje_maria5.sh` y los demás), ni
  `pantalla_maria5.js`; esa pantalla la corrió el subagente.
- Gemini real y el Kit del despachante.

Contexto de la Dev 2 en la pieza: de ~97 mil a ~356 mil tokens (~26 puntos);
espera su `/compact`.

## La reentrega con CATALOGO-NCM-1 — devuelta sobre `6854f34`

Base: la rama de la PM hasta `ce88c01`, con EXCEL-1, MARIA-1b y
PUNTA-A-PUNTA-1. Informe en `cc6030b`. Venv armado sólo con el
`requirements.txt` de la rama.

| Qué | Salida |
|---|---|
| Rojo antes: `test_maria5_*.py`, `test_catalogo_ncm1.py`, `test_excel1_lectura.py`, `test_excel1_txt.py`, `test_punta_a_punta1.py` y `test_generar_maria_txt.py` con el producto de `ce88c01` | `171 failed, 156 passed, 3 xfailed, 28 errors` |
| Suite | `1459 passed, 102 skipped, 3 xfailed, 25 warnings in 202.74s` (coincide con el informe) |
| La PM, a mano, hallazgos 1, 2 y 5 (servidor en `6854f34`) | `Peso por caja`+`Peso`: `peso=[40.0]`; `Peso bruto unitario`: `peso=[3.0] avisos=[]`; validación de 8517.12.31: los dos avisos, uno con «(el de 2018)»; `/generate_maria/avisos`: `[]` |

**Subagente de la PM (Sonnet alto).** La pieza se sostiene:
- **Los seis puntos devueltos:**
  - Dos pesos: con el lector, (25,25) en 10 unidades da 25 kg con aviso; en
    el Excel gana el neto.
  - Seis pesos en texto en 10 variantes de columna: todas las filas se
    conservan.
  - NaN, inf, 1e300 y 0,0004 dan 400.
  - Subítems: en 26.000 pedidos al azar, 0 que antes generaban y ahora no.
  - Grupos con Playwright: ningún producto queda en 0.
  - Una sola cuenta.
- **Centavos:** en 9000 pedidos al azar, `MDDTFOB` = Σ `MARTFOB`; flete y
  seguro cierran; la validación da el mismo FOB que el TXT en 6000 de 6000;
  «Gastos a FOB» es igual al TXT en 3653 de 3653.
- **Catálogo:**
  - Idéntico al ZIP (10.504 NCM) y las 522 bajas son exactas.
  - Sin avisos falsos en las 33.037 SIM completas.
  - `/api/ncm/aviso` y `/api/ncm/sugerir` piden sesión.
  - No hay inyección en `ncm.js`.
- **Frenos de MARIA-1b:** 24 casos, iguales a `ce88c01`.
- **Archivos reales:** salen idénticos.

| # | Hallazgo | ¿Antes? | Cómo quedó |
|---|---|---|---|
| 1 | Excel: «Peso por caja» (40) antes de «Peso» (2,5) gana: 400 kg en 10 unidades en vez de 25. Cualquier «Peso…» cuenta, y desempata el orden | Nuevo (en `ce88c01`, 2,5) | **Devolución 1** |
| 2 | `pantalla_maria5.js` da rojo en `6854f34`: no manda el CUIT y MARIA-1b frena. El OK del informe era de `7b4f651`. Con CUIT, pasa | Nuevo (de la integración) | **Devolución 4** |
| 3 | «Peso bruto unitario» y «Gross weight per unit» se leen como neto de una unidad, sin aviso | Nuevo (antes, vacío) | **Devolución 2** |
| 4 | Sin `ncm_arca.csv.gz`: toda NCM de 7 o 10 dígitos da el error del 0 inicial, y las de 8 u 11 pasan sin aviso | Nuevo (se sacó el respaldo) | **Devolución 6** |
| 5 | Una baja sale dos veces en la validación, una con el texto falso «(el de 2018)» de `_control_ncm`; en `/generate_maria/avisos` no sale | Nuevo | **Devolución 5** |
| 6 | La primera validación carga el catálogo en el bucle de eventos: `/health` tarda 3,75 s | Ya pasaba (MARIA-1b) | Se deja, a Fase 3 |
| 7 | Dos pesos de la línea distintos (neto 25, total 27): el aviso no muestra los números | Nuevo | **Devolución 3** |
| 8 | Mensajes del peso: NaN «pasa el tope», un negativo «no es un número», 0,0004 se ve «0 kg» | Nuevo | De paso |
| 9 | `test_celda_en_la_ultima_fila…` rojo una vez bajo carga (4,3 s contra 8 s) | Mismo margen | Se deja (entorno) |

**No corrido por la PM:**
- Los sabotajes de la Dev (`sabotaje_maria5.sh`, `sabotaje_catalogo_ncm1.sh`
  y los demás).
- `/upload_pdf/public` con un PDF (el lector se probó a nivel función).
- El caso sin catálogo por HTTP (se probó en una copia).
- Gemini real y el Kit.

Contexto de la Dev 2: ~49 % al entregar (`get_session`, 18:56 UTC; su
informe dice ~21 %).
