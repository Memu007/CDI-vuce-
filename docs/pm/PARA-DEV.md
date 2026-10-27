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

## Veredicto de la vuelta de CLIENTE-1c y de ESTUDIO-1b (2026-10-27): aceptadas

Sobre `3aba9c2` (informe `807d562`). El detalle está en
`REPRODUCCION-CLIENTE-1c-2026-10-27.md` («Vuelta») y en
`REPRODUCCION-ESTUDIO-1b-2026-10-27.md`. Corrí la suite desde base limpia
(3229 passed, 0 rojos), los sabotajes de CLIENTE-1c, CLIENTE-1b y ESTUDIO-1b (todos en rojo; el de ESTUDIO-1 sigue corriendo), 32 negativos míos por API y
un fuzz de la clave de `--base`. Mi adversario no corrió (presupuesto).
Integro tu rama (`418ada3`).

- **Bien:** H1 y H2 de la devolución (una sola lectura con `make_url`),
  D25 (b) en un solo módulo, D23 (b) con sus tres casos, `estudio_id` y el
  nombre del estudio. Tus supuestos quedan aceptados.
- **Se suma a EXCEL-3f (H1-bis), primero:** el fuzz con 4000 claves da 0
  fugas en la URL escrita, la clave, el host y la consulta, pero 113 de
  4000 cuando el error repite `url.render_as_string(hide_password=False)`.
  Causa: SQLAlchemy escribe la clave con `quote(clave, safe=" +")`, y esa
  forma no está entre las que tapás. Una clave que mezcla un espacio con
  otro carácter que se escapa queda a la vista:
  `QZXW KJVB|NMPL` → `…://***:QZXW KJVB%7CNMPL@db.local…`. Tu prueba usa
  `render_as_string`, pero sólo con claves de un separador.
  - Arreglá la familia: toda forma en que SQLAlchemy o el driver puedan
    escribir la clave, no sólo este ejemplo.
  - Caso parametrizado que combine espacio con otro carácter escapado en
    la misma clave, y su sabotaje en `cliente1c.sh`.
  - Hasta que entre, el script no se corre contra producción.
- **Riesgos anotados, no los arregles:** el choque al anotar el uso del
  perfil con dos TXT a la vez, U+3164 y U+2800 en el nombre, `cuit_valido`
  con `00000000000`, el año `0001` y `--base` en el historial (lo decide
  Emi).

## EXCEL-3f (tarea activa)

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

1. EXCEL-3f, con H1-bis primero.
2. GUARDAR-2.

Puertas de EXCEL-3f: la suite en 0 rojos, `excel3.sh` y `cliente1c.sh`
sin sabotaje en verde, y mi diff de revisión va desde `3aba9c2`.

## Más adelante — GUARDAR-2

Ya hay un candidato aislado: `2d930c5` en la rama vieja
`claude/dev1-tecnica` (sobre `1cdfe49`). Partí de ahí, no lo rehagas;
faltaba lo de `CIERRE-RETOMA-2026-10-24.md` («Qué sigue», punto 2).
