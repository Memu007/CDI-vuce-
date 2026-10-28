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
| Catálogo NCM | Ya tiene 10.226 posiciones (cargadas en julio de 2026 desde el nomenclador de ARCA del 19/12/2018: le falta la enmienda de 2022; D21 de la Dev 1). El «22 de 9.500» de septiembre quedó viejo | medido en el código | alta |

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
Modoc y 5 % con Lakaut. Agregado (22:15): **se elige en cada operación;
Lakaut = `PSAD01`, Modoc = `PSAD06`.** Coincide con los dos archivos reales
(`PSAD06` en 2025, `PSAD01` en 2026). CDI pone siempre `PSAD06` (Modoc): hoy
acierta en la mayoría de sus despachos, pero no se puede cambiar.

**Pregunta 6, FCA y FAS** (2026-10-06). FCA y EXW no son lo mismo, pero en
los dos casos se declara «gastos anteriores a FOB». Coincide con la regla que
ya tiene el generador (`maria_generator.py:413-426`: todo lo que no es grupo C
o D va a `GTOS-ANT-FOB`). FAS no lo nombró; por la misma regla de la nota del
SIM (la diferencia entre el FOB y la condición pactada) también es anterior al
FOB. Ojo: FAS no está en la lista de condiciones válidas del generador
(`maria_generator.py:777`).

**Reducción o exclusión del IVA adicional** (22:12). En el Kit hay un menú
«Ventajas» con decenas de opciones; una es `IVAADREDUCCION`, que el
despachante elige cuando sabe que el importador tiene una reducción. No es
automática: elegirla cuando no corresponde es una infracción grave. Ninguno
de los dos archivos reales trae ventajas, así que no hay prueba de cómo iría
en el TXT. **Lectura de la PM:** CDI no la pone en el archivo; avisa que, si
hay reducción o exclusión, se elige en «Ventajas» del Kit. La exclusión no la
nombró: es el mismo menú, con una ventaja que no se sabe.

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
>
> **22:12** — (a «¿cómo cargás una reducción o una exclusión del IVA
> adicional?») En el kit hay un menú que se llama «Ventajas». En ese menú hay
> decenas de opciones disponibles para elegir para que el sistema, por
> ejemplo, no liquide un impuesto o no pida la presentación de algún
> certificado, etc. Ahí hay una ventaja que se llama IVAADREDUCCION. El
> despachante la selecciona cuando sabe que el importador tiene una reducción
> del impuesto. Si bien el sistema tiene cargada la reducción del impuesto
> para cada CUIT puede pasar que haya un error sistémico y que el despachante
> esté dándole un beneficio al importador que no le corresponde (cometiendo
> una infracción grave); por eso no es algo automático sino que hay que saber
> cuándo seleccionarla y cuándo no.
>
> **22:15** — Selección de la empresa de digitalización: se selecciona en
> cada operación. Códigos: Lakaut = PSAD01; Modoc = PSAD06.

## Lo que falta pedirle (para que Emi lo mande)

Las dos preguntas cortas ya están respondidas (2026-10-06, 22:12 y 22:15).
Quedan los dos favores:

> 1. ¿Me pasás dos o tres despachos que hayas cargado, con nombres, CUIT y
>    montos tapados? Mejor si son distintos: uno EXW, uno CIF y uno con
>    varios productos.
> 2. ¿Podés probar en tu Kit María un archivo nuestro? Sólo cargarlo para ver
>    si lo acepta, sin oficializar nada. (Se manda al cerrar la Fase 1.)

## Preguntas nuevas (2026-10-25), para que Emi las mande

Salen de la carga del 2026-10-24 y de VALOR-1. Mientras no conteste, CDI
sigue como está.

> 1. El identificador de la operación (`IDSO`): ¿cuántos caracteres puede
>    tener como máximo? ¿El MARIA rechaza uno que ya se usó?
> 2. En los sufijos de valor (lo que va entre paréntesis, como `AI(...)`):
>    ¿cómo se escribe un número con decimales? ¿Acepta un sufijo vacío?
> 3. El seguro del 1 %: ¿se calcula sobre el FOB de la factura o sobre el
>    FOB con los ajustes (descuentos y gastos que se suman o se restan)?
> 4. ¿En qué condiciones de venta el seguro ya viene en el precio y no hay
>    que sumarlo (CIF, CIP, alguna otra)?

| Pregunta | Qué decide | Mientras tanto |
|---|---|---|
| 1 | Largo y repetición de `IDSO` (D1 de MARIA-7) | no cambian `NDDTIMMTRN` ni `IEXT` |
| 2 | Decimales y vacío en los sufijos (D7 de MARIA-7) | como hoy |
| 3 | Base del seguro sugerido (D13 de VALOR-1) | FOB de la factura |
| 4 | Si el botón del seguro se esconde en algunas condiciones (D14) | se ofrece siempre |

Una más (2026-10-27), para PRORRATEO-1. Por ítem, el TXT sólo trae FOB,
flete y seguro (`MARTFOB`, `MARTFLE`, `MARTASS`); no hay campo de ajustes:

> 5. Los ajustes que se suman o se restan al valor (descuentos, gastos,
>    comisiones): ¿van en el archivo, y en qué campo, o los cargás vos a mano
>    en el MARIA? Si van repartidos por ítem, ¿cómo los repartís?

| Pregunta | Qué decide | Mientras tanto |
|---|---|---|
| 5 | Si PRORRATEO-1 escribe algo en el TXT o sólo muestra el reparto | no arranca; los ajustes no cambian el TXT (D12) |

Una más (2026-10-28), para DESPACHO-1 (armar el catálogo del cliente con
despachos ya oficializados):

> 6. Un despacho ya oficializado, ¿cómo lo bajás del sistema (PDF, otro
>    archivo)? ¿Me pasás uno o dos así, con nombres, CUIT y montos tapados?
>    Y para el catálogo de productos de un cliente: ¿los despachantes usan
>    algún formato o programa para guardarlo o pasárselo, o con un Excel
>    alcanza?

| Pregunta | Qué decide | Mientras tanto |
|---|---|---|
| 6 | Qué archivo lee DESPACHO-1 y en qué formato se baja el catálogo | DESPACHO-1 no arranca; el catálogo se bajaría en Excel |

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
| Pregunta 5 | `ARDIG-CUIT-PSAD` (hoy `PSAD06` fijo; Modoc = `PSAD06`, Lakaut = `PSAD01`) |
| Pregunta 6 | `GTOS-ANT-FOB` con FCA y FAS |
| Favor 1 (archivos reales) | identificadores (`IDSO`, `IEXT`, `NDDTIMMTRN`, `LDVDREFDOC`), sufijos de valor por producto, número de proveedor y formato del archivo |
| Favor 2 (probar en su Kit) | si acepta el número de proveedor, el redondeo y el formato; es la prueba de la puerta G4 |

## Qué cambia con cada respuesta

| Pregunta | Cambio en el producto |
|---|---|
| 1 | **Respondida.** `CARTUSO` deja de ser 3 fijo: se elige entre los seis estados, por ítem. Por defecto, «nuevo sin uso importado» (2) si el origen es extranjero; si es argentino, se pide elegir |
| 2 | **Respondida.** `IVAADICIONAL1` por operación, con cambio por ítem. Por defecto, reventa sin beneficio (`NO_VALIDA`). `IVAAD1` sólo si se marca uso particular. Reducción o exclusión: no va en el TXT; aviso de que se elige en «Ventajas» del Kit |
| 3 | **Respondida.** El peso del TXT pasa a ser el total de la línea (ítem o subítem), igual al que muestra la pantalla de validación |
| 4 | **Respondida.** `BANCOSARGENTINA`: lo elige el cliente en cada operación. Se carga en la operación (se puede proponer el último que usó ese cliente) y se emite en el archivo; si falta, aviso |
| 5 | **Respondida.** `ARDIG-CUIT-PSAD` se elige en cada operación, como el banco (CDI propone la última usada): Modoc = `PSAD06`, Lakaut = `PSAD01` |
| 6 | **Respondida.** La regla del FOB ya estaba bien. Falta cablear el campo de pantalla, que hoy no llega al TXT, y sumar FAS a las condiciones válidas (MARIA-3) |
| Favor 1 | Identificadores, sufijos por ítem y número de proveedor según los archivos reales |
| Favor 2 | Redondeo y formato según lo que acepte su Kit |
