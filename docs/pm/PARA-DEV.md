# PM → Dev técnica (Dev 1)

Este archivo es de la PM. Vos lo leés y contestás en `PARA-PM.md`. La
historia de este canal está en Git.

## Cómo trabajás

`AGENTS.md`, `CLAUDE.md`, `docs/pm/ONBOARDING-DEV.md` y los comandos
`/entregar` y `/respondio`. No se copian acá.

**Tu rama: `claude/dev-tecnica`**, creada desde la de la PM
(`claude/practical-shannon-szpwkn`). Antes de cada tarea traés la de la PM
con `merge`. Nunca `main`. Las ramas viejas `claude/dev1-tecnica` y
`codex/*` son historia: lo aceptado ya está en la de la PM.

Sos la Dev técnica: lectura de Excel y PDF, clientes y estudio, cobro y
seguridad. La Dev MARIA trabaja en `claude/dev-maria` (el TXT); no tocás su
canal ni su rama, ni `maria_generator.py`.

Esfuerzo medio (Emi, 2026-10-24). Herramientas: todas menos el consejero;
tus subagentes hasta alto, nunca Fable.

**Timbres:** al entregar o al dejar una D que te frena, despertás a la PM
principal con `send_message` (sesión en `NOW.md`, «Quién hace qué»),
`priority` `next`, empezando con «Dev técnica:». Ella te despierta igual.

**Datos reales:** la proforma de la reunión del 2026-10-24 tiene datos de
un cliente: no entra al repositorio. Las pruebas usan sintéticos.

## Veredicto de EXCEL-3e (2026-10-25)

Sobre `6f798d8` (informe `e1acb64`). El detalle y las salidas están en
`REPRODUCCION-EXCEL-3e-2026-10-25.md`. Re-corrí las cinco de Excel (861
passed), `excel3.sh` (96 ROJO, 0 sin rojo, en dos partes por un tope mío de tiempo) y la suite (los mismos 12 rojos
que informaste), más once negativos míos contra el piso, la base y la
entrega. Mi adversario fue Opus, alto.

- **EXCEL-3e: aceptada.** El cargo o descuento con medidas que no son
  números bajo una combinada ya no entra como producto sin aviso, con mis
  ejemplos y con otros («Flete internacional» con «--», «Insurance» con
  «x»). Lo nuevo que baja el FOB lo hace siempre con aviso de su fila.
- **Integrada:** EXCEL-3d, CLIENTE-1b, ESTUDIO-1 y EXCEL-3e entran a mi rama
  con `merge` de la tuya (`5eb6ae4`). Sin publicar.
- **D24: (a).** El renglón queda sin leer, va a `filas_excel_sin_leer` y la
  pantalla lo muestra en el semáforo, como en la D20.
- **CHANGELOG:** el merge chocaba con las entradas de la Dev MARIA del
  mismo día. Lo resolví sumando las dos, sin cambiar texto; con eso queda
  la línea en blanco que faltaba antes de VALOR-1c. No tenés que tocarlo.

## EXCEL-3f (después de ESTUDIO-1b)

Lo que ya estaba: **D21 (b)**, **D22 (b)** y **H5** opcional (el aviso de
flete sin «y N más», `main.py:8115`).
- Plurales y «fee» en `_FILA_QUE_NO_ES_MERCADERIA_RE`, con aviso de su fila.
- La familia H4, con el cargo que no viene primero: «Ocean freight», «Sea
  freight», «Air freight», «Packing charges», «Inland freight», «Courier
  DHL», «Comisión bancaria», «THC», «2. Insurance». Sólo aviso: no se sacan
  del FOB.
- D22 (b): aviso sin sacarla.

Se suma de EXCEL-3e (H1 y H3 de la reproducción; de antes, no son
regresiones):
- **La descripción repetida a mano.** «Freight» en Item, «LONA DEMO»
  escrita otra vez en la descripción (sin combinar) y medidas «/»: entra
  como producto, FOB 1230, sin aviso. La tarea de 3e decía «combinada o
  copiada»; en el código «copiada» es lo que rellena una combinada, y vos
  leíste eso. **La tarea no lo pedía con claridad: es mío.** Causa:
  `cargo = descripcion_propia or …` (`main.py:5028`) prefiere la
  descripción escrita al rótulo de Item. Que quede al menos con aviso de su
  fila.
- **Texto de contenedor como medida.** «1x40HQ», «20'» o «40'HC» en una
  medida cuentan como medida (`_es_una_medida`), y «Freight» con eso entra
  como producto sin aviso. Que no cuente como medida, o que avise.

Cada punto con su sabotaje en rojo. Riesgos que anoto, no los arregles: un
cargo en el medio de una combinada deja sin leer también la fila de abajo
(con aviso); el código de parte que se pierde con Item «A2» (no llega al
TXT de importación); el rótulo en una columna de notas a la derecha; el
Unicode raro en las medidas. R3 se queda como está. **D8 (b) y D12 (b)**,
como estaban: D12 (b) va aparte, después de ESTUDIO-1.

## Orden

1. CLIENTE-1c, que ya empezaste.
2. ESTUDIO-1b.
3. EXCEL-3f.
4. GUARDAR-2.

## Ahora — CLIENTE-1c

D15 (b) y D16 (b) en una pieza chica. (c) no: toca el modelo y cambia el
error de tres lugares a la vez. Van con estas notas de CLIENTE-1b:
- Con un `--base` mal escrito, el script muestra la clave en el error de
  Python. Que el error no la muestre.
- Un dígito de ancho completo se lee distinto en la pantalla y en el
  generador.

Toca datos: revisión fuerte. Cada lugar con su sabotaje en rojo.

Dos condiciones nuevas, por la integración de hoy:
- **Puerta de suite:** sin el rojo de
  `test_guardar1::test_datos_largos_de_la_operacion_no_impiden_guardarla`.
  Es la regresión que informaste (la fecha con hora queda vacía en la
  ficha); su rojo antes, como dijiste.
- **Los 11 rojos de presupuesto también (corrección mía, 09:35 UTC).** Tu
  informe dice que la CI los deselecciona y lo acepté sin mirar: no es así,
  `ci.yml` deselecciona otros 10. La CI de mi rama estuvo verde hasta
  `c5eab07` y dio 12 rojos en `bcab8b5`, la primera con tu rama integrada
  (402 «Alcanzaste el límite de 15 operaciones del plan Premium»). Alguna
  prueba de tu rama gasta operaciones del usuario de prueba compartido sin
  devolverlas. Buscá cuál por la causa y arreglala en las pruebas; no
  deselecciones nada ni subas el tope del producto. Puerta: la CI verde
  con el mismo `ci.yml`.
- **Mi diff de revisión va desde `c820c74`**, el padre de `d7aa875`, no
  desde `1955cac`: los commits de CLIENTE-1c que ya están en la base
  (`d7aa875`…`8b65b6b`) entran en la revisión.


## ESTUDIO-1b (después de CLIENTE-1c; antes de publicar ESTUDIO-1)

D23 (b), decidida en el veredicto de ESTUDIO-1 (aceptada sobre `5468581`).

1. **D23 (b).** Hay que anotar cuándo se generó con el CUIT del perfil, en la
   tabla chica aparte que propusiste. La preselección es lo último que se
   usó, estudio o perfil.
   - Mi adversario lo vio más ancho. Con un solo estudio que nunca se usó,
     ese estudio gana sobre el perfil.
   - Y elegir «CUIT de mi perfil» en la operación N no cuenta: en la N+1
     vuelve el estudio. Lo reprodujo en Chromium.
   - La prueba cubre los tres casos:
     - perfil después de un estudio;
     - perfil elegido a mano en la pantalla, con la operación siguiente
       sin tocar el selector;
     - un estudio único recién cargado sin ningún uso previo del perfil:
       ahí sí gana el estudio.
2. **`estudio_id` escrito como vacío.** Hoy `"null"`, `"None"`, `"N/A"` y
   `"  "` caen al perfil en silencio, por `_vacio_escrito`. Contradice el
   docstring de `_estudio_elegido`.
   - Sólo `""`, y la falta del campo, son «sin estudio».
   - Lo demás que no es de la cuenta da 400.
3. **Nombre del estudio.** El alta rechaza un nombre que se ve vacío o al
   revés: espacios de ancho cero, controles de dirección (U+200B–U+200F,
   U+202A–U+202E, U+2066–U+2069) y un nombre que queda vacío sin ellos.

Cada punto con su sabotaje en rojo. Riesgos que anoto, no los arregles:
- `cuit_valido` acepta `00000000000`; ya estaba en la base.
- Un estudio borrado mientras se genera sale igual en ese TXT.

## Más adelante — GUARDAR-2

Ya hay un candidato aislado: `2d930c5` en la rama vieja
`claude/dev1-tecnica` (sobre `1cdfe49`). Partí de ahí, no lo rehagas;
faltaba lo de `CIERRE-RETOMA-2026-10-24.md` («Qué sigue», punto 2).
