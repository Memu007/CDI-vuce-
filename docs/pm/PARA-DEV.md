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

## Veredicto de ESTUDIO-1 (2026-10-25)

Sobre `5468581` (código `c992715`, informe `c820c74`). El detalle está en
`REPRODUCCION-ESTUDIO-1-2026-10-25.md`. Re-corrí `test_estudio1.py` (26
passed) y `estudio1.sh` (37 ROJO, 0 sin rojo), más 8 negativos míos. Mi adversario fue
Opus, alto: no encontró cómo entrar a lo ajeno ni cómo perder datos.

- **ESTUDIO-1: aceptada.** Se suma **ESTUDIO-1b**, que va antes de publicar.
- **No integro todavía.** `5468581` trae EXCEL-3d, y su H1 sigue abierta.
  Integro todo junto cuando acepte EXCEL-3e.
- **D23: (b)**, en ESTUDIO-1b.

### ESTUDIO-1b (después de CLIENTE-1c; antes de publicar ESTUDIO-1)

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

## Veredicto de EXCEL-3d (2026-10-25)

Sobre `5468581` (informe `470fc48`). El detalle y las salidas están en
`REPRODUCCION-EXCEL-3d-2026-10-25.md`. Mi adversario fue Opus, alto. Yo
re-corrí sus casos de plata contra `e08b4c4`, `273c153`, `31c9b5a` y la
entrega.

- **EXCEL-3d: devolución, EXCEL-3e.** Los tres puntos que devolví están
  arreglados, con mis ejemplos y con otros distintos. `test_excel3.py` da
  264 passed y los sabotajes, 0 sin rojo. Pero la vuelta trae una regresión
  de plata sin aviso, H1, abajo.
- **E1 del adversario no es un hallazgo.** Contra `e08b4c4`, la base de mi
  veredicto anterior, la cabecera y su hijo quedan los dos sin leer, igual
  que en 3d. Lo que dejó entrar al hijo fue 3c. Las filas sin leer se ven en
  el semáforo. Sólo pido que la docstring de `test_excel3.py:1046` diga a qué
  SHA llama «la base». Va en el próximo commit de código.
- **No integro todavía.** EXCEL-3d, CLIENTE-1b y ESTUDIO-1 entran juntas
  cuando acepte EXCEL-3e.

### EXCEL-3e: lo que vuelve (va primero, antes que CLIENTE-1c)

**H1. Un cargo con medidas que no son números entra como producto.**

El caso: la especificación está combinada (`C2:C3`) y la fila 3 es
`Freight, -, -, "/", "/", -, 1, 1200, 1200`.
- `e08b4c4`, `273c153` y `31c9b5a` leen un flete de 1200 con aviso de la
  fila 3. El FOB queda en 30.
- `5468581` da FOB 1230, un producto «LONA DEMO, ancho / m x largo / m» y
  avisos `[]`.
- Con medidas «-» o 0 pasa lo mismo.
- Con «Discount» y -10, se pierde el descuento de 10 y entra un producto
  fantasma. El único aviso es «sin precio», que confunde.

La causa:
- `con_medidas` (`main.py:4973`) mira si la celda tiene texto, no si es un
  número.
- Con la descripción copiada, `descripcion_propia` (`main.py:4945`) queda
  vacía.
- Con las dos, la fila no pasa por la lectura de flete y descuento
  (`main.py:4984`). Entra como hijo y hereda la decisión del producto de
  arriba (`main.py:5071`).

**Lo que tiene que quedar:**
- Una fila con rótulo de cargo o descuento, bajo una descripción combinada o
  copiada y con medidas que no son números, nunca entra como producto sin un
  aviso que nombre su fila.
- Se lee como la leía la base, o queda afuera con ese aviso.
- **Piso:** lo que hace `31c9b5a`.
- **No** se arregla agregando palabras a la lista: se arregla la causa.

**La prueba barre la familia:**
- medidas «/», «-», 0 y vacías;
- flete, seguro y descuento;
- con importe y precio, y con sólo el importe;
- `.xlsx` y `.xls`;
- el rótulo en Item y en la columna de la descripción;
- un producto real con medidas «-», que tiene que seguir entrando.

Cada caso con su sabotaje en rojo. Corregí el CHANGELOG si dice algo que la
vuelta cambia.

### Tus D de EXCEL-3d (decidido por la PM)

- **D20: (a).** Se queda así: las filas se ven como sin leer.
- **D21: (b)**, en una pieza aparte, **EXCEL-3f**, después de ESTUDIO-1:
  - plurales y «fee» en `_FILA_QUE_NO_ES_MERCADERIA_RE`, con aviso de su
    fila;
  - la familia H4, con el cargo que no viene primero: «Ocean freight», «Sea
    freight», «Air freight», «Packing charges», «Inland freight», «Courier
    DHL», «Comisión bancaria», «THC», «2. Insurance». Para estas, sólo
    aviso: no se sacan del FOB.
  - Ésta sí es una pieza de lista, decidida aparte. La regla de «no por
    lista» vale para EXCEL-3e.
- **D22: (b)**, en EXCEL-3f: aviso sin sacarla.
- **H5** (el aviso de flete sin «y N más», `main.py:8115`): opcional, en
  EXCEL-3f.
- **D8 (b) y D12 (b)**, como estaban: D12 (b) va aparte, después de
  ESTUDIO-1. R3 se queda como está.

**Riesgos que anoto, no los arregles:** H2, H3 y H6 de la reproducción, y
«Seguro de carga» con medidas «/» combinada. Están igual en los cuatro SHAs.

### Orden

1. EXCEL-3e.
2. CLIENTE-1c, que ya empezaste.
3. ESTUDIO-1b.
4. EXCEL-3f.
5. GUARDAR-2.

## Después — CLIENTE-1c

D15 (b) y D16 (b) en una pieza chica. (c) no: toca el modelo y cambia el
error de tres lugares a la vez. Van con estas notas de CLIENTE-1b:
- Con un `--base` mal escrito, el script muestra la clave en el error de
  Python. Que el error no la muestre.
- Un dígito de ancho completo se lee distinto en la pantalla y en el
  generador.

Toca datos: revisión fuerte. Cada lugar con su sabotaje en rojo.

## Más adelante — GUARDAR-2

Ya hay un candidato aislado: `2d930c5` en la rama vieja
`claude/dev1-tecnica` (sobre `1cdfe49`). Partí de ahí, no lo rehagas;
faltaba lo de `CIERRE-RETOMA-2026-10-24.md` («Qué sigue», punto 2).
