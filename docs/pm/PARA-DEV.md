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

## Veredicto de CLIENTE-1c (2026-10-27): con devolución

Sobre `4452b22` (informe `dbe7c4a`). El detalle y las salidas están en
`REPRODUCCION-CLIENTE-1c-2026-10-27.md`. Re-corrí la suite desde base
limpia (3135 passed, **0 rojos**: los 12 quedaron cerrados) y
`cliente1c.sh` (25 ROJO, 0 sin rojo), más negativos míos contra el script.
Mi adversario fue Opus, alto.

- **Bien:** D15 (b), D16 (b), la regla única de la fecha con
  `fecha_inic_activ_sirve` y la causa de los 402 (`2ff3262`). La fecha con
  hora que ya no se copia es D15 (b): está decidido.
- **Devolución — la clave de `--base` en el error.** Causa: el dónde y los
  secretos salen de una segunda lectura del texto (`urlsplit` en
  `_donde_y_secretos`), no de lo mismo que conecta (`make_url`). Cuando las
  dos lecturas no coinciden, el error muestra la clave, o el script se cae
  con un traceback en vez del mensaje limpio. Ejemplo:
  `postgresql://u:pa/ss@127.0.0.1:1/db` → «No se pudo revisar la base
  u:pa/ss@127.0.0.1:1/db: …».
  - Arreglá la familia, no el «/»: cualquier `--base` que la conexión
    acepte tiene que dar el mensaje limpio, sin la clave, con rc 2.
  - De la misma causa: el enmascarado reemplaza el usuario en todo el
    texto («ConnectionRef***sedError» con usuario «u»). Lo que se tapa
    tiene que ser lo que leyó la conexión, sin romper el resto del mensaje.
  - Caso y sabotaje en `cliente1c.sh` para cada forma que encuentres.
- **D25: (b).** La importación sigue la regla del alta: la fecha que no
  sirve queda vacía, con aviso en su fila. Va en esta misma vuelta, con su
  caso y su sabotaje.
- **Se anota, no lo arregles:** el año `0001` pasa por los tres lugares.
- **No integro todavía** tu rama: entra con la vuelta. La CI de mi rama
  sigue roja hasta entonces.

Después, ESTUDIO-1b.

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

1. La vuelta de CLIENTE-1c (arriba), con D25 (b).
2. ESTUDIO-1b.
3. EXCEL-3f.
4. GUARDAR-2.

Puertas de la vuelta: la suite sigue en 0 rojos, `cliente1c.sh` sin
sabotaje en verde, y mi diff de revisión va desde `4452b22`.


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
