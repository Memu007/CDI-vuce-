# PM → Dev MARIA (Dev 2)

Este archivo es de la PM principal (en CDI no hay PM visual). Vos lo leés y
contestás en `PARA-PM-2.md`. La historia de este canal está en Git.

## Tarea activa: CATALOGO-4; después CATALOGO-PAIS y ORIGEN-2, una a la vez (2026-11-19 14:45 UTC)

Emi dijo «sí a las dos y al país con nombre» (19/11, antes de las 14:45 UTC) a CATALOGO-4, a ORIGEN-2 y
a que los catálogos muestren el país con nombre. Es un sí a las piezas, no un «dale» para publicar.
Base: la cabeza de mi rama; traela con `merge`. Una pieza a la vez: la siguiente arranca recién con la
anterior aceptada. ORIGEN-ETIQUETA (D261) quedó aceptada sobre `5a28c13c`; su acta y Git la guardan.

### CATALOGO-4 (activa)

La causa: en el catálogo del proveedor (`match_items`), dos productos que se parecen igual a lo leído
se desempatan por el orden en que la base devuelve las filas, que no está fijado.

1. Lo idéntico sigue ganando primero, como hoy.
2. Ante un empate de parecido gana el último confirmado y, a la misma hora (o sin fecha), decide el
   contenido de la fila, no su orden. El ganador es el mismo con las filas cargadas en cualquier orden,
   en SQLite y en Postgres. La familia de empates va como datos de un solo caso.
3. Nada que hoy no empata cambia de ganador.
4. Negativo: con el arreglo revertido, al menos un orden de carga da rojo.

*Sugerencia:* la memoria del cliente ya desempata así (`desempate` en `client_memory.py`); si sirve,
un solo lugar para los dos.

### CATALOGO-PAIS, apenas te acepte CATALOGO-4

En los catálogos del proveedor (`catalogo.js`) y del cliente (`clientes.js`), el origen de cada producto
se ve con código y nombre («423 · PAISES BAJOS»), con la misma `etiqueta` de ORIGEN-ETIQUETA.

1. Guardar otro campo del producto deja el origen guardado igual, byte a byte.
2. Toda la tabla de países va y vuelve al mismo código al guardar sin tocar el origen y al escribirlo.
3. La persona puede corregir el origen escribiendo nombre o código (hoy el del cliente tiene
   `maxlength="3"`).
4. Un origen que no se reconoce se ve como se escribió, escapado.
5. El TXT sale igual antes y después.

### ORIGEN-2, apenas te acepte CATALOGO-PAIS

La causa: el origen habitual del cliente se recorta a 3 caracteres en el servidor (alta y edición) y en
la base (`VARCHAR(3)`), mientras el resto del producto acepta el nombre o el código del país. Es
migración: revisión más fuerte (§3) y sabotajes.

1. El origen habitual acepta el nombre o el código, validado igual que en el catálogo. Lo que no es un
   país de la tabla no se guarda recortado ni en silencio: la pantalla dice por qué.
2. La ficha del cliente (la etiqueta de arriba y «Origen habitual») lo muestra con código y nombre.
3. Migración probada en Postgres descartable: las filas que ya existen («CN» y vacías) quedan iguales.
   El caso del largo corre en Postgres, que hace cumplir el `VARCHAR`; SQLite no.
4. Negativo en el mismo SHA con el recorte de vuelta: rojo.
5. **Afuera, decidido por la PM:** la calculadora (`/api/ncm/calcular`) también recorta a 3, y ahí
   «BRASIL» dejaría de contar como Mercosur. Su pantalla sólo ofrece una lista de códigos de dos letras,
   así que hoy no hay camino que lo rompa: queda como riesgo escrito, sin código.

**Próxima D: D275.**

## Aviso: guarda de conexiones en `tests/conftest.py` (2026-11-13 16:06 UTC)

Llega con tu próximo merge de mi rama. Un error de teardown «… dejó N conexión(es) de aiosqlite abiertas…» es la guarda funcionando: un test o ayudante deja una conexión viva; se arregla cerrándola, no se saltea. Tu pytest entero sobre `ee2ee3c` corrió sin ella: el de SUFIJO-BORRADOR va después del merge. Desde hoy también corta al arrancar: un `rc=4` con «La guarda de conexiones no ve una conexión abierta de aiosqlite…» es un venv con aiosqlite viejo (antes de 0.22), no un rojo tuyo; instalá el de `requirements.txt` y volvé a correr.

## Vencido `sabotaje_maria5.sh`: aceptado sobre `c0505cc` (informe `9153d23`) e integrado (2026-11-14 09:30 UTC)

Acta `REPRODUCCION-SABOTAJE-MARIA5-2026-11-14.md`. Regla nueva de la PM: en un vencido de sólo
arnés, un último commit que cambia únicamente comentarios no necesita revisor si el informe lo dice.

## Ritmo y calidad (Emi, 2026-10-28)

Vamos tranquilas: no hay fecha de entrega y, si el plan se estira, no pasa
nada. Lo que no se negocia es la calidad: código que se lea como hecho por
una persona senior, no generado a las apuradas.

- No te adelantes: una pieza a la vez, cerrada entera antes de la siguiente.
- No te saltees ningún paso de `/entregar` (autorrevisión, `/code-review`,
  `/security-review` cuando toca dinero, sesión, permisos o datos, rojo antes
  del arreglo, sabotajes). Si algo no se corrió, se dice.
- Preferí el arreglo simple y legible al ingenioso; nombres claros, sin
  código muerto ni duplicado, y comentarios sólo donde explican un porqué.
- Mejor una entrega más tarde que una devolución.

## Se retoma el 04/11, con el método nuevo (PM)

Emi levantó la pausa por 3 días, hasta el sábado 07/11 a la tarde. Traé mi
rama con `merge` y leé lo que cambió: `CLAUDE.md` §6 (código como lo dejaría
una senior), «Código de producto sólo con camino de hoy» en
`ONBOARDING-PM.md`, `COLA-LIMPIEZA.md` y `/entregar`. Desde ahora cada
entrega lleva la salida entera de `docs/pm/herramientas/chequeo-6.py <base>
<SHA>`, con cada `AVISO` arreglado o explicado en una línea. Lo que ya
estaba escrito antes del 04/11 no se reescribe: su aviso se explica como
«ya escrito, va a la cola de limpieza» y tu informe propone la línea; la
PM la pasa a `COLA-LIMPIEZA.md`. Lo nuevo de la vuelta sí cumple §6.

## Piezas nuevas que aprobó Emi el 04/11 (PM)

Tu cola queda: CATALOGO-LARGO-2 → RESET-1 → PYPDF-1 → ABUSO-1 → SUFIJOS-2+SEGURO-1 → **SEGURO-2** → EMAIL-1 →
CONEXIONES-1 → OBSERVABILIDAD-1 → ORG-1+D40. El detalle, al activarlas:

- **CATALOGO-LARGO-1 (datos):** con cliente y proveedor, una descripción de
  301 a 2000 caracteres no se pierde en silencio en la memoria del cliente
  ni en el catálogo (`product_key` de 300, `descripcion` de 500): se guarda
  o da un error a la vista, nunca 200 sin guardar. Migración, si hace
  falta, probada en Postgres descartable.
- **SEGURO-2 (TXT):** lo que SEGURO-1 sólo avisa frena la generación hasta
  que se corrija, también el 1 % mandado sin calcular (D30 b).

## Cómo trabajás

`AGENTS.md`, `CLAUDE.md`, `docs/pm/ONBOARDING-DEV.md` y los comandos
`/entregar` y `/respondio`. No se copian acá.

**Tu rama: `claude/dev-maria`**, creada desde la de la PM
(`claude/practical-shannon-szpwkn`). Antes de cada tarea traés la de la PM
con `merge`. Nunca `main`. Las ramas viejas `claude/dev2-maria` y
`codex/*` son historia: lo aceptado ya está en la de la PM.

Sos la Dev de la **cola MARIA**: el MARIA.TXT, el lector de facturas y sus
pantallas. La Dev técnica trabaja en `claude/dev-tecnica`; no tocás su
canal ni su rama.

Esfuerzo alto (Emi, 2026-10-24). Herramientas: todas menos el consejero;
tus subagentes hasta alto. Desde que Emi te pase a Fable (2026-11-11, al
borde de pieza): los revisores de `/code-review` heredan Fable y está
permitido; los `adversario-*` y `mecanico-haiku` siguen con su modelo fijo;
ningún otro subagente en Fable.

**Timbres:** al entregar o al dejar una D que te frena, despertás a la PM
principal con `send_message` (sesión en `NOW.md`, «Quién hace qué»),
`priority` `next`, empezando con «Dev MARIA:». Ella te despierta igual.

**Regla del archivo MARIA** (límite que no se negocia): ningún cambio en lo
que sale en el TXT sin prueba (la ley, un archivo real, la respuesta del
despachante o lo que el MARIA aceptó o rechazó). **Los TXT y la proforma de
la reunión del 2026-10-24 tienen datos reales de un cliente: no entran al
repositorio.** Las pruebas usan sintéticos con la misma forma.

## Qué pasó el 2026-10-24

Emi y el despachante cargaron en el MARIA un TXT de CDI de una factura real
(decenas de renglones de un mismo producto en varios colores y medidas,
una sola posición SIM, origen China, CFR). Entró después de doce correcciones a mano. Cada una es
un defecto del generador. La versión que cargó tiene esta forma (valores
inventados acá):

```
[DDT]
ISTA=IC05
IDSO=AB1234CD                ← corto: con 19 caracteres el MARIA lo rechaza
CDDTEXE=01
CDDTBUR=001
CDDTTYPDEC=IC05
CDDTAGR=20111111112          ← CUIT del despachante: sin esta línea, «No existe el campo CDDTAGR»
CDDTIMPEXP=I
...
MDDTFLE=3480.00              ← CDI escribió 3.48: tomó «3.480» como decimal
...
[DVD]
LDVDREFDOC=<número real de la factura>   ← CDI escribió un pedazo («E7L1-1»)
...
[ART]
NART=0001
CARTSBITEM=S                 ← un ítem por posición, con subítems
CARTUNTDCL=03                ← m² (CDI puso 07 = unidad)
QARTUNTDCL=<suma de m²>
CARTUNTEST=01                ← kilogramo, la unidad estadística de VUCE
QARTUNTEST=<igual a QARTKGRNET, al centésimo>   ← si no, error 2122
QARTKGRNET=<kilo neto>
...
[SBT]
NART=0001
ISBT=0001
MSBTFOB=...
QSBTUNTDCL=...
MSBTUNITAR=...
IEXT=1-1
CSBTSVL=AA(MARCA)-AI(500G AZUL001 120CMX40M)-   ← AI distinto por renglón; sólo letras, números y espacios
QSBTUNTEST=<kilos del renglón>
```

Todas las líneas terminan en CRLF (una línea sin CR: «falta carácter de fin
(crlf) en línea 15»). El MARIA no acepta guiones, puntos ni caracteres raros
dentro de los valores de los sufijos: van espacios. El guión que separa un
sufijo del otro (`)-`) sí.
