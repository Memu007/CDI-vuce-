# La forma de un despacho oficializado — 2026-10-28

Para DESPACHO-1. Sale de tres despachos reales que mandó el despachante el
28/10 (uno EXW, uno CIF y uno FCA con varios productos). Vinieron **sin
tapar**: no entran al repo ni a ninguna prueba. Acá van sólo los rótulos, el
orden y las reglas que se repiten; ningún nombre, CUIT, monto, fecha, marca
ni número de los originales. Las pruebas usan un sintético con esta forma y
valores inventados.

## Qué es

- PDF del sistema, con texto seleccionable (no escaneado). Cada hoja dice
  «Generado por DUX» y lleva «Firma y Sello Despachante de Aduana»: es la
  impresión de un programa de despachantes, no la pantalla del SIM. Otro
  despachante puede usar otro programa: **se lee por rótulo, no por
  posición en la hoja.**
- Encabezado de cada hoja: «SUBREGIMEN: IMPORTACION A CONSUMO CON DOCUMENTO
  DE TRANSPORTE», aduana, «Oficialización» y «Año / Ad. / Tipo / NºReg. /
  DC».
- El texto extraído tiene los rótulos en una línea y los valores en la de
  abajo, en columnas separadas por varios espacios. Los números van con
  punto de miles y coma decimal (`1.234,56`). Algún carácter con tilde puede
  salir roto en la descripción («Las dem?s»).

## Carátula

Rótulos, en este orden:

| Renglón | Rótulos |
|---|---|
| 1 | Aduana · Oficialización · Año / Ad. / Tipo / NºReg. / DC · Fojas |
| 2 | Importador / Exportador · CUIT Nº · Despachante de Aduana · CUIT Nº |
| 3 | Agente de Transporte Aduanero · CUIT Nº · Vendedor |
| 4 | Vía · Documento de Transporte · Identificador Manifiesto · Nombre del Transporte |
| 5 | Bandera · Puerto de Embarque · Fecha Arribo · Marcas y Números |
| 6 | Embalaje · Total Bultos · Peso Bruto · Depósito · Vto. Embarque · Plazo · Motivo / Nº Autorización |
| 7 | Aduana Destino / Salida · Cond. Venta · FOB Total · Divisa · Flete Total · Divisa |
| 8 | Seguro Total · Divisa (aparece cuando hay seguro, como en el CIF) |

La divisa del FOB y la del flete pueden ser distintas (en uno, FOB en euros
y flete en dólares).

**Opciones de carátula** («c) Opciones a nivel general» y, al final,
«Información Adicional» con `Nro.Item` = `0000`, `Código`, `Valor`):
`ARDIG-CUIT-PSAD`, `ARDIG-SETI-OPC`, `BANCOSARGENTINA`, `BLCONSIGREC`,
`DECVALORADUOPC`, `DOMICIL.ESTABLEC`, `FECHA INIC.ACTIV`,
`FECHAEMISIONFACT`, `FEMB-ORIGEN`, `GTOS-ANT-FOB` (EXW y FCA),
`GTOS-POS-FOB` (CIF), `IDTRIB-PROVEEDOR`, `IMPOGIRO-DIV-OPC`,
`NOTACREDITO-TXT`, `NOTADEBITO-TXT`, `NRO.REF.INTERNA`, `SENASA19/02OPC`,
`TRANSFERTEX`, `TRANSF-NO-ONEROS`, `VARIOSVENDEDORES`, `ZONAFRANCATEX1`,
y en alguno `ADUACOMPROBADEST`, `COMPRDESADUATXT`, `DJ-GARANTIAS-TXT`.
«b) Ventajas» puede traer una ventaja con su código.

## Por ítem («DECLARACION DE LA MERCADERIA»)

| Bloque | Rótulos |
|---|---|
| Ítem | Nº Item · Tipo · Posición SIM / Código AFIP · NALADISA / GATT · Lista · Estado |
| | Total Kg. Neto · Origen Pais / Provincia · Pais de Procedencia / Destino · Unidad / Estado · Cantidad Unidades Estadísticas · Información Adicional |
| Descripción | Texto libre de varias líneas (puede mezclar el texto del arancel con el de la mercadería) |
| VALOR MERCADERIA | Unitario en Divisa · Unidad · Cantidad Unidades · Ajuste a Incluir en Divisa · Ajuste a Deducir en Divisa |
| VALOR EN ADUANA | FOB Total en Divisa · FOB Total en Dólar · Valor en Aduana en Divisa · Valor en Aduana en Dólar |
| | Base IVA / Ganancias en Dólar y otros (no hacen falta para el catálogo) |
| Conceptos y LIQUIDACION | Tributos; no hacen falta para el catálogo |

- Con subítems, la unidad del renglón dice `SUBITEM` y cada subítem trae su
  propio valor y sufijos.
- El estado se escribe con palabras (por ejemplo «NUEVO SIN USO
  IMPORTADO»), no con el código de `CARTUSO`.
- En los tres despachos los ajustes por ítem están en cero.

**Opciones por ítem** (en «Información Adicional», con el número de ítem):
`GANANCIASOP3`, `IVAADICIONAL1`, `PAISEMIT-FACTCOM`, `DSE.PAIS.OPC`,
`DNRT-OPC`, `DNRT-EXC-OPC`, `TERRITORIOTEX-1`, `EXPLOARMASQUIMTX`,
`IMPOGIRO-DIV-OPC`, `PRECURSORMIXOPC`, `RES451-19ANEXOI`, `LEY26184ART6`,
y otras que dependen de la mercadería (SENASA, ANMAT, número de serie). El
catálogo no las necesita.

**Sufijos de valor** («Sufijos de valor:», uno por renglón, `CÓDIGO = qué
es`):

```
AA(ACME) = MARCA
AI(XZ 400 B) = CODIGO
AJ(CAJA X 12) = PRESENTACION
PB00 = Ninguno
PC01 = AUTOADHESIVO EN UNA CARA
```

(Valores inventados.) Los de valor libre llevan paréntesis; los de lista,
dos dígitos. El código de artículo (`AI`) puede tener espacios. En los tres
despachos aparecen `AA`, `AI`, `AJ` y de lista `PA`, `PB`, `PC`, `PE`,
`SA`, `NA`, `BM`, `CA`, `CB`, `GN`, `GP`, `SZ`.

## Cuentas que cierran

- Valor en aduana = FOB + flete + seguro.
- En el CIF, `GTOS-POS-FOB` = flete + seguro, y el seguro es el real, no el
  1 %.
- En EXW y FCA, la diferencia con el FOB va en `GTOS-ANT-FOB`, no como
  ajuste del ítem.

## Lo que DESPACHO-1 lee para el catálogo

Por renglón (ítem o subítem): posición SIM, descripción, sufijos de valor,
origen, unidad, cantidad, valor unitario y kilo neto. Lo que no encuentra
queda marcado; nada se rellena. El resto del despacho no se guarda.
