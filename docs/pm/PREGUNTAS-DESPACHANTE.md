# Preguntas al despachante — 2026-10-06 (versión simple)

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
| Procedencia ≠ origen | Código Aduanero, art. 15: «la mercadería se considera procedente del lugar del cual hubiera sido expedida con destino final al lugar de importación». Sale del documento de transporte. El origen se acredita con el certificado de origen | leyes-ar.com/codigo_aduanero/15.htm (cita). Además, el archivo real anonimizado `tests/fixtures/maria_golden_anon.TXT` trae procedencia distinta del origen | alta |
| EXW y grupos C y D | Nota «Nueva pregunta del SIM en importación»: se declara a nivel carátula «el importe de la diferencia entre el valor FOB declarado y el valor en la condición de venta pactada». EXW va en `GTOS-ANT-FOB`; C y D en `GTOS-POS-FOB`. Es un dato informativo | pcram.net/post.php?mid=8451 (cita) | alta |
| Los 150 del archivo EXW | Son la diferencia entre EXW y FOB (gastos en origen). No tienen por qué coincidir con el flete y el seguro internacionales, que van por otra vía | inferencia de la cita anterior | media |
| `GANANCIASOP3` | Para reventa va `COMERC`, que es lo que el sistema declara hoy. Desde el 24/08/2026 el SIM suprimió `NO_VALIDA` en este campo | cda.org.ar, noticia 42706 (resumen) | media-alta |
| Banco 191 | Banco Credicoop Cooperativo Limitado | tabla de entidades del BCRA (sitio no oficial) | alta |
| Catálogo NCM | Ya tiene 10.226 posiciones de ARCA (julio de 2026). El «22 de 9.500» de septiembre quedó viejo | medido en el código | alta |

## Respuestas del despachante

**2026-10-06 (noche), por mensaje a Emi.**

**Pregunta 1, estado de la mercadería.** Se elige siempre entre seis, sea o no
para revender: nuevo sin uso argentino, nuevo sin uso importado, sin uso
argentino, sin uso importado, usado argentino (incluye reacondicionado) y
usado importado (incluye reacondicionado).

**Pregunta 2, percepción de IVA adicional.** Se paga cuando la mercadería es
para revender, y completa, salvo dos casos: una reducción de un porcentaje
por normativa, para cierta mercadería y por un plazo; o una exclusión de un
porcentaje que la DGI le dio al importador, por un plazo. El despachante lo
decide por operación y por mercadería.

**Lo que muestran juntas con los dos archivos reales anonimizados** (lectura
de la PM, 2026-10-07):

| Archivo real | Origen | `CARTUSO` | `IVAADICIONAL1` |
|---|---|---|---|
| `maria_golden_subitems_anon.TXT` (EXW 2026) | 310, China | 2 | `NO_VALIDA` |
| `maria_golden_anon.TXT` (DDP 2025) | 200, Argentina | 3 | `IVAAD1` |

- **Estado:** el orden de la lista coincide con los códigos de los dos
  archivos (2 = nuevo sin uso importado; 3 = sin uso argentino, para una
  mercadería de origen argentino). Confianza media-alta; lo confirma la
  prueba en su Kit (favor 2).
- **IVA adicional:** para reventa sin reducción ni exclusión, el archivo de
  2026 trae `NO_VALIDA` (ningún beneficio: percepción completa). `IVAAD1`
  (uso particular, que exceptúa la percepción) **no corresponde para
  reventa, y hoy CDI lo declara siempre.**
**Pregunta 3, peso** (2026-10-06, 21:35). Se declara por cada ítem o
subítem. Con el archivo real de 2026: el ítem tiene 6 unidades repartidas en
tres subítems de modelos distintos y un solo peso de ítem, 33 kg, sin peso por
subítem. Con modelos distintos, el peso del ítem sólo puede ser el total de la
línea, no el de una unidad. Confianza alta; lo termina de confirmar la prueba
en su Kit.

**Pregunta 4, banco** (2026-10-06, 21:35). Se declara el que decida el
cliente. El archivo real de 2026 lo trae (`BANCOSARGENTINA` = 191); el de 2025
no. Hoy CDI no lo emite. Agregado (21:40): **no siempre es el mismo; el
cliente elige el que quiera para cada operación.**

**Pregunta 5, empresa de digitalización (PSAD)** (21:42). Trabaja 95 % con
Modoc y 5 % con Lakaut. Los dos archivos reales traen `PSAD06` (2025) y
`PSAD01` (2026); CDI pone siempre `PSAD06`. **No se sabe qué código es cada
empresa:** una búsqueda en la web no lo encontró (los sitios oficiales están
bloqueados desde acá). Pregunta corta para la próxima: qué número o código
aparece en el Kit al lado de cada una.

**Pregunta 6, FCA y FAS** (2026-10-06). FCA y EXW no son lo mismo, pero en
los dos casos se declara «gastos anteriores a FOB». Coincide con la regla que
ya tiene el generador (`maria_generator.py:413-426`: todo lo que no es grupo C
o D va a `GTOS-ANT-FOB`). FAS no lo nombró; por la misma regla de la nota del
SIM (la diferencia entre el FOB y la condición pactada) también es anterior al
FOB. Ojo: FAS no está en la lista de condiciones válidas del generador
(`maria_generator.py:777`).

- **Falta saber:** cómo se carga en el Kit una reducción o una exclusión
  (¿una opción de una lista o un número de certificado?). Pregunta corta para
  la próxima.

## Sus respuestas, tal cual (2026-10-06, por mensaje a Emi)

Sin nombres: la fuente es «el despachante de Emi».

> **21:20** — Los estados que se pueden seleccionar, independientemente si es
> para revender o no son: Nuevo sin uso argentino; Nuevo sin uso importado;
> Sin uso argentino; Sin uso importado; Usado argentino, Incl. Reacond; Usado
> importado, Incl. Reacond.
>
> **21:34** — Percepción de IVA adicional: se paga cuando la mercadería es para
> revender. Se paga completo salvo que se den alguna de las siguientes
> situaciones: por normativa del estado, para determinada mercadería, el
> impuesto tiene una reducción de X porcentaje, por un plazo determinado; la
> DGI le otorgó al importador una exclusión del impuesto de X porcentaje, por
> un plazo determinado. Es decir que el despachante lo decide por operación y
> por mercadería.
>
> **21:35** — El peso se declara por cada ítem o subítem.
>
> **21:35** — Banco: se declara el que decida el cliente.
>
> **21:40** — No siempre es el mismo banco, el cliente puede elegir el que
> quiera para cada operación.
>
> **21:42** — PSAD: yo trabajo 95 % con Modoc y 5 % con Lakaut.
>
> **(después)** — FCA y EXW no son lo mismo, pero para hacer el despacho en
> ambos casos se declara el dato «gastos anteriores a FOB».

## Lo que falta pedirle (para que Emi lo mande)

Las preguntas 1 y 2 de abajo, Emi ya se las mandó (2026-10-07). Faltan sus
respuestas y los dos favores.

> 1. Cuando hay una reducción o una exclusión del IVA adicional, ¿cómo lo
>    cargás en el Kit? ¿Elegís una opción de una lista o cargás un número de
>    certificado?
> 2. En el Kit, cuando elegís Modoc o Lakaut como empresa de digitalización,
>    ¿qué número o código aparece al lado de cada una?
> 3. (Favor) ¿Me pasás dos o tres despachos que hayas cargado, con nombres,
>    CUIT y montos tapados? Mejor si son distintos: uno EXW, uno CIF y uno con
>    varios productos.
> 4. (Favor) ¿Podés probar en tu Kit María un archivo nuestro? Sólo cargarlo
>    para ver si lo acepta, sin oficializar nada. (Se manda cuando la cola
>    MARIA esté lista.)

## El mensaje que se mandó (2026-10-06)

Emi (2026-10-06): la versión anterior era demasiado técnica. Tenía los
nombres de los campos del archivo (`CARTUSO`, `NO_VALIDA`), que el
despachante no usa. Esta versión pregunta por su trabajo de todos los días. La
traducción a cada campo es tarea de la PM (tabla de abajo). Lo que se puede
ver en un archivo real no se pregunta: se pide el archivo.

> Hola. Estoy armando un sistema que prepara el archivo para cargar las
> importaciones en el Kit María. Para no equivocarme te pido dos favores y
> seis preguntas cortas, de cómo lo hacés vos normalmente.
>
> **Los dos favores:**
> 1. ¿Me pasás dos o tres despachos que hayas cargado, con nombres, CUIT y
>    montos tapados? Mejor si son distintos: uno EXW, uno CIF y uno con
>    varios productos.
> 2. ¿Podés probar en tu Kit María un archivo nuestro? Sólo cargarlo para ver
>    si lo acepta, sin oficializar nada.
>
> **Las preguntas:**
> 1. En una importación común de mercadería nueva para revender, ¿qué estado
>    de la mercadería marcás? ¿Alguna vez marcás otro?
> 2. La percepción de IVA adicional, ¿cuándo se cobra completa y cuándo no
>    (por ejemplo, si es para uso propio o un bien de uso)? ¿Lo decidís por
>    despacho o por producto?
> 3. El peso de cada producto, ¿lo cargás por el total de unidades, no por
>    una sola?
> 4. ¿Qué banco ponés en el despacho? ¿Es el banco por el que el importador
>    le paga al exterior? ¿Es siempre el mismo para cada cliente?
> 5. ¿Con qué empresa de digitalización de documentación (PSAD) trabajás?
>    ¿Es siempre la misma?
> 6. Cuando la compra es FCA o FAS, ¿declarás los gastos hasta poner la
>    mercadería a bordo, igual que con EXW?
>
> ¡Gracias!

## Qué campo resuelve cada respuesta (para la PM)

| Pregunta o favor | Campo del archivo |
|---|---|
| Pregunta 1 | `CARTUSO` (hoy 3 fijo; la investigación dice que 2 es «nuevo sin uso importado»; los dos archivos reales anonimizados del proyecto traen 3 y 2, así que no es un valor fijo) |
| Pregunta 2 | `IVAADICIONAL1` (hoy `IVAAD1` fijo, que sería «uso particular») |
| Pregunta 3 | `QARTKGRNET` (hoy sale el peso de una unidad) |
| Pregunta 4 | `BANCOSARGENTINA` (hoy no se emite; 191 = Credicoop) |
| Pregunta 5 | `ARDIG-CUIT-PSAD` (hoy `PSAD06` fijo; un archivo real tenía `PSAD01`) |
| Pregunta 6 | `GTOS-ANT-FOB` con FCA y FAS |
| Favor 1 (archivos reales) | identificadores (`IDSO`, `IEXT`, `NDDTIMMTRN`, `LDVDREFDOC`), sufijos de valor por producto, número de proveedor y formato del archivo |
| Favor 2 (probar en su Kit) | si acepta el número de proveedor, el redondeo y el formato; es la prueba de la puerta G4 |

## Qué cambia con cada respuesta

| Pregunta | Cambio en el producto |
|---|---|
| 1 | **Respondida.** `CARTUSO` deja de ser 3 fijo: se elige entre los seis estados, por ítem. Por defecto, «nuevo sin uso importado» (2) si el origen es extranjero; si es argentino, se pide elegir |
| 2 | **Respondida.** `IVAADICIONAL1` por operación, con cambio por ítem. Por defecto, reventa sin beneficio (`NO_VALIDA`). `IVAAD1` sólo si se marca uso particular. Reducción o exclusión: aviso para cargarla en el Kit hasta saber cómo va en el archivo |
| 3 | **Respondida.** El peso del TXT pasa a ser el total de la línea (ítem o subítem), igual al que muestra la pantalla de validación |
| 4 | **Respondida.** `BANCOSARGENTINA`: lo elige el cliente en cada operación. Se carga en la operación (se puede proponer el último que usó ese cliente) y se emite en el archivo; si falta, aviso |
| 5 | **Respondida en parte.** `PSAD` en la configuración del estudio (cada despachante usa la suya, con cambio por operación). Falta qué código es Modoc y cuál Lakaut |
| 6 | **Respondida.** La regla del FOB ya estaba bien. Falta cablear el campo de pantalla, que hoy no llega al TXT, y sumar FAS a las condiciones válidas (MARIA-3) |
| Favor 1 | Identificadores, sufijos por ítem y número de proveedor según los archivos reales |
| Favor 2 | Redondeo y formato según lo que acepte su Kit |
