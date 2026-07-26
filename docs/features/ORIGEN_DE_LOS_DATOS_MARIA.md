# De dónde sale cada dato del MARIA.TXT

> Para el dueño del producto. Responde: **¿qué le podemos sacar a la factura,
> qué es siempre igual, y qué tiene que decidir el despachante?**
>
> Base: los **71 campos distintos** de los dos archivos reales de referencia
> (`tests/fixtures/maria_golden_anon.TXT`, DDP 2025, y
> `maria_golden_subitems_anon.TXT`, EXW 2026), cruzados con el manual de
> PreDespacho y con lo que hoy extrae `pdf_extractor.py`.

---

## Resumen en una tabla

| De dónde viene | Cuántos campos | ¿Lo tenemos? |
|---|---|---|
| **1. De la factura** (se puede leer del PDF) | ~18 | ✅ casi todo |
| **2. Fijos del formato** (siempre el mismo valor) | ~13 | ✅ todo |
| **3. Del despachante o del cliente** (se cargan una vez y se recuerdan) | ~8 | 🟡 parcial |
| **4. Decisión del despachante** (por operación) | ~10 | 🟡 parcial |
| **5. Calculados por el sistema** | ~12 | ✅ todo |

**La conclusión de producto:** la factura da la mayor parte de los números, pero
**ninguna factura trae la clasificación**. Lo que falta es casi todo del grupo 4
— y ahí es donde el despachante no se puede reemplazar.

---

## 1. Lo que sale de la factura

Esto es lo que el PDF puede dar, y lo que ya le pedimos a Gemini hoy.

| Dato de la factura | Campos del TXT | ¿Lo extraemos hoy? |
|---|---|---|
| Número de factura | `IDSO`, `IDDT`, `NRO.REF.INTERNA`, `IARTESPAPU`, `IEXT`, `NDDTIMMTRN` | ✅ `numero_factura` |
| Fecha de emisión | `FECHAEMISIONFACT`, y el **año del `IEXT`** | ✅ `fecha_emision` |
| Nombre del proveedor | `LDDTNOMFOD` | ✅ `vendedor_nombre` |
| ID tributario del proveedor | `IDTRIB-PROVEEDOR` | ✅ `vendedor_id` |
| Nombre y CUIT del importador | `LDDTNOMIOE`, `NDDTIMMIOE` | ✅ `comprador_nombre`, `comprador_cuit` |
| Moneda | `CDDTDEVFOB`, `CDDTDEVFLE`, `CDDTDEVASS` | ✅ `moneda` |
| Condición de venta (incoterm) | `CDDTINCOTE`, y **de qué campo de gastos se usa** | ✅ `incoterm` |
| Valor FOB total | `MDDTFOB` | ✅ (suma de ítems) |
| Flete | `MDDTFLE`, `MARTFLE` | ✅ `flete` |
| Seguro | `MDDTASS`, `MARTASS` | ✅ `seguro` |
| Descripción de cada ítem | (no va al TXT, se usa para clasificar) | ✅ `descripcion` |
| Cantidad por ítem | `QARTUNTDCL`, `QARTUNTEST` | ✅ `cantidad` |
| Valor unitario | `MARTUNITAR`, `MARTFOB` | ✅ `valor_unitario` |
| Peso neto | `QARTKGRNET` | ⚠️ ver abajo |
| Origen de la mercadería | `CARTPAYORI` | ✅ `origen` (cuando figura) |
| Domicilio del importador | `DOMICIL.ESTABLEC` | ✅ `comprador_domicilio` |
| Referencia del documento | `LDVDREFDOC` | ❌ no se extrae |
| Fecha de vencimiento de embarque | `DDDTVENEMB` | ❌ no se extrae |

> ⚠️ **El peso es el caso especial.** Se puede leer del PDF, pero por decisión
> de producto (2026-07-18) **no se autocompleta de una factura anterior** y
> validación lo bloquea si viene en cero o negativo. El despachante lo
> confirma siempre. Está bien así: un peso mal declarado lo rebota aduana.

---

## 2. Los fijos del formato

Siempre el mismo valor. No hay que preguntarlos nunca.

| Campo | Valor | Qué significa |
|---|---|---|
| `ISTA`, `CDDTTYPDEC` | `IC04` | Tipo de destinación (importación a consumo) |
| `CDDTEXE` | `01` | Ejercicio |
| `CDDTIMPEXP` | `I` | Importación (vs exportación) |
| `CDDTIVA` | `S` | |
| `ARDIG-SETI-OPC` | `PSAD` | |
| `CDVDDOC` | `FACTURACOMERCIAL` | Tipo de documento respaldatorio |
| `CDVDPRSDOC` | `S` | |
| `CARTTYP` | `N` | |
| `CARTPAGREG` | `N` | |
| `CARTCALDST` | `N` | |
| `GANANCIASOP3` | `COMERC` | |
| `NART` (en cabecera) | `0000` | |

Los dos archivos reales coinciden en todos estos. Ya los emitimos fijos.

---

## 3. Del despachante o del cliente — se cargan una vez

No están en la factura, pero **tampoco cambian en cada operación**. Van una
vez a la ficha y se recuerdan.

| Campo | Qué es | ¿De quién depende? | ¿Lo tenemos? |
|---|---|---|---|
| `CDDTAGR` | CUIT del despachante | Del estudio | 🟡 hay `cuit_agr`, sin pantalla clara |
| `NDDTIMMIOE`, `LDDTNOMIOE` | CUIT y nombre del importador | Del cliente | ✅ ficha de cliente |
| `DOMICIL.ESTABLEC` | Domicilio del establecimiento | Del cliente | ✅ |
| `FECHA INIC.ACTIV` | Fecha de inicio de actividades | Del cliente | ✅ (la trae la migración) |
| `ARDIG-CUIT-PSAD` | `PSAD06` / `PSAD01` | Varía entre los dos archivos | ❌ hoy va fijo |
| `CDDTBUR` | Aduana (`001` / `073`) | Por operación o por cliente | ✅ `aduana_codigo` |
| Código de proveedor | El `(00272)` de `LDDTNOMFOD` | Lo asigna el despachante por proveedor | ❌ no se pide |
| `IDTRIB-PROVEEDOR` | ID tributario extranjero | Del proveedor | ✅ |

> **Este grupo es la mejor oportunidad de producto.** Son datos que el
> despachante escribe una vez por cliente o proveedor y después no vuelve a
> tocar. Cada uno que falte es una corrección a mano en cada operación.

---

## 4. Lo que decide el despachante — y no se puede adivinar

Acá está el corazón del producto: **ninguna factura trae esto**.

| Campo | Qué decide | ¿Lo tenemos? |
|---|---|---|
| `IESPNCE` | La **posición SIM** (NCM 8 + SIM 3 + letra DC) | ✅ el asistente propone, el humano confirma |
| `CSBTSVL` | Los **sufijos de valor** (marca, modelo, medidas) | ✅ se carga a mano |
| `CARTSBITEM` + sub-ítems | Si el ítem se declara entero o **partido por modelo** | ✅ el motor ya lo hace, ❌ falta la pantalla |
| `CARTUSO` | `2` / `3` — uso o estado de la mercadería | ❌ **fijo en 3**, sin preguntar |
| `CARTPAYPRC` | **Procedencia** (de dónde viene el embarque) | ⚠️ ver abajo |
| `CARTUNTDCL`, `CARTUNTEST` | Unidad declarada y estadística | ✅ con fallback a `07` |
| `IVAADICIONAL1` | `IVAAD1` / `NO_VALIDA` | ❌ **fijo en `IVAAD1`** |
| `BANCOSARGENTINA` | Código de banco (`191`) | ❌ no se emite |
| Importe de gastos a FOB | El monto de `GTOS-ANT-FOB` / `GTOS-POS-FOB` | ✅ el motor lo acepta, ❌ falta la pantalla |
| `DDDTVENEMB` | Fecha de vencimiento de embarque | 🟡 parámetro sin pantalla |

### ⚠️ Origen ≠ procedencia

`CARTPAYORI` (origen) y `CARTPAYPRC` (procedencia) **son cosas distintas**, y
en el archivo de referencia viejo **difieren**: origen `200`, procedencia
`222`. Es normal — la mercadería puede ser de un país y embarcarse desde otro.

**Hoy los igualamos por defecto** (`CARTPAYPRC = CARTPAYORI`). En la mayoría de
las operaciones coincide, pero cuando no, el TXT sale con la procedencia
equivocada **y ninguna validación se queja**. Mismo patrón que el año del
`IEXT`: silencioso hasta la aduana.

Es el candidato más fuerte a próximo arreglo.

---

## 5. Los que calcula el sistema

Nadie los carga: salen de los otros.

| Campo | Cómo se calcula |
|---|---|
| `MARTBASIMP` | FOB + seguro + flete |
| `MARTASS`, `MARTFLE` por ítem | Prorrateo del total sobre cada ítem |
| `MARTUNITAR` | FOB del ítem ÷ cantidad |
| `MSBTFOB` | cantidad del sub-ítem × su valor unitario |
| `IARTESPAPU` | Número de factura + número de ítem |
| `NART`, `NARTEXT`, `ISBT` | Numeración correlativa |
| `IEXT` | Primeros 5 del número de factura + ítem + **año de la factura** |
| `NDDTIMMTRN` | Primeros 5 del número de factura |
| `MDDTFOB` | Suma de los ítems |

Todos verificados contra los dos archivos reales: **las cuentas cierran**.

---

## Qué haría yo con esto, por orden

1. **Arreglar procedencia ≠ origen.** Es un error silencioso, igual al del año.
2. **Pantalla para el grupo 3** (datos que se cargan una vez): código de
   proveedor, `ARDIG-CUIT-PSAD`, CUIT del despachante. Cada uno ahorra una
   corrección por operación, para siempre.
3. **Pantalla para partir un ítem en sub-ítems** — el motor ya lo soporta.
4. **Preguntar `CARTUSO` en vez de fijarlo en 3.** Hoy declaramos siempre lo
   mismo sin avisar.
5. Extraer del PDF `LDVDREFDOC` y `DDDTVENEMB`, que son fáciles y hoy faltan.

Los puntos 4 y 5, y todo lo que quedó marcado ❌ en el grupo 4, **necesitan que
el despachante defina el criterio primero**. No son decisiones de programación.
