# Preguntas al despachante — versión final 2026-10-06

Revisión de la consulta de julio (`docs/features/CONSULTA_AL_DESPACHANTE.md`
de `CDI-vuce-`). Se sumaron dos investigaciones en la web, hechas por
subagentes con esfuerzo alto, y la auditoría del archivo MARIA. Las preguntas
quedaron como confirmaciones.

**Límite de la investigación.** Desde este entorno, la red bloquea los sitios
oficiales y casi todos los de despachantes. Todo sale de resúmenes de
buscador, salvo las citas textuales marcadas. Nada se cambia en el TXT sin la
respuesta del despachante.

## Lo que ya no hace falta preguntar

| Tema | Respuesta | Fuente | Confianza |
|---|---|---|---|
| Procedencia ≠ origen | Código Aduanero, art. 15: «la mercadería se considera procedente del lugar del cual hubiera sido expedida con destino final al lugar de importación». Sale del documento de transporte. El origen se acredita con el certificado de origen | leyes-ar.com/codigo_aduanero/15.htm (cita) | alta |
| EXW y grupos C y D | Nota «Nueva pregunta del SIM en importación»: se declara a nivel carátula «el importe de la diferencia entre el valor FOB declarado y el valor en la condición de venta pactada». EXW va en `GTOS-ANT-FOB`; C y D en `GTOS-POS-FOB`. Es un dato informativo | pcram.net/post.php?mid=8451 (cita) | alta |
| Los 150 del archivo EXW | Son la diferencia entre EXW y FOB (gastos en origen). No tienen por qué coincidir con el flete y el seguro internacionales, que van por otra vía | inferencia de la cita anterior | media |
| `GANANCIASOP3` | Para reventa va `COMERC`, que es lo que el sistema declara hoy. Desde el 24/08/2026 el SIM suprimió `NO_VALIDA` en este campo | cda.org.ar, noticia 42706 (resumen) | media-alta |
| Banco 191 | Banco Credicoop Cooperativo Limitado | tabla de entidades del BCRA (sitio no oficial) | alta |
| Catálogo NCM | Ya tiene 10.226 posiciones de ARCA (julio de 2026). El «22 de 9.500» de septiembre quedó viejo | medido en el código | alta |

## El mensaje para mandar

> Hola. Estoy terminando un sistema que arma el TXT para la Lectura de
> Archivos del Kit María. Me quedan diez confirmaciones cortas. Casi todas son
> de sí o no:
>
> 1. **`CARTUSO`**: ¿es el estado de la mercadería? Para mercadería nueva de
>    origen extranjero, ¿va `2` («nuevo sin uso importado»)? ¿Cuándo va `3`?
> 2. **`IVAADICIONAL1`**: para mercadería que el importador va a revender,
>    ¿va `NO_VALIDA`? ¿`IVAAD1` es sólo para uso o consumo particular del
>    importador y `IVAAD2` para bienes de uso? ¿Se decide ítem por ítem?
> 3. **Peso (`QARTKGRNET`)**: ¿es el peso neto **total** del ítem (cantidad
>    por peso unitario), no el de una unidad?
> 4. **`BANCOSARGENTINA`**: ¿es el banco que el importador designó para el
>    seguimiento del pago de la importación? ¿Se completa sólo cuando hay
>    pago por el mercado de cambios?
> 5. **Código de proveedor** (`(00272) NOMBRE`): ¿la Lectura de Archivos lo
>    controla contra tu tabla del Kit María, o sólo usa el nombre y el ID
>    tributario?
> 6. **FCA y FAS**: ¿la diferencia con el FOB va en `GTOS-ANT-FOB`, igual que
>    con EXW?
> 7. **Identificadores** (`IDSO`, `NDDTIMMTRN`, `IEXT`, la referencia
>    `LDVDREFDOC` del tipo `E001-1`): ¿qué ponés vos en cada uno, o el Kit los
>    reemplaza al leer el archivo?
> 8. **`ARDIG-CUIT-PSAD`**: en un archivo vino `PSAD06` y en otro `PSAD01`.
>    ¿De qué depende?
> 9. **Sufijos de valor (SBT)**: ¿van uno por modelo o ítem, o puede ir el
>    mismo para toda la operación?
> 10. **Redondeo**: si la suma de los ítems difiere del total por un centavo,
>     ¿el Kit lo rechaza?
>
> Y dos pedidos, si se puede:
> - **Dos o tres TXT reales**, con nombres, CUIT y montos tapados, de casos
>   distintos (EXW, CIF, varios ítems).
> - **Probar en tu Kit María un TXT que te mandemos**, sólo leerlo y sin
>   oficializar, para ver si lo acepta.
>
> Gracias.

## Qué cambia con cada respuesta

| Pregunta | Cambio en el producto |
|---|---|
| 1 | `CARTUSO` deja de ser 3 fijo. Por defecto «nuevo importado», con aviso, editable por ítem |
| 2 | `IVAADICIONAL1` según el destino del ítem; por defecto reventa |
| 3 | El peso del TXT pasa a ser el total de la línea, igual al que muestra la pantalla de validación |
| 4 | `BANCOSARGENTINA` en la ficha del cliente y en la operación |
| 5 | Campo «código en tu Kit María» en la ficha del proveedor |
| 6 | Se completa la regla del FOB y se cablea el campo de pantalla, que hoy no llega al TXT |
| 7 y 8 | Identificadores y `PSAD` según lo que diga; hoy se arman con el número de factura y un valor fijo |
| 9 | Sufijos por ítem (hoy: uno para toda la operación) |
| 10 | Aritmética con redondeo controlado (hoy usa decimales binarios y a veces no cierra) |
