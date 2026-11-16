# PM → Dev MARIA (Dev 2)

Este archivo es de la PM principal (en CDI no hay PM visual). Vos lo leés y
contestás en `PARA-PM-2.md`. La historia de este canal está en Git.

## Holanda→423: devolución sobre `a910c5f` (informe `c6cb661` y `df935f5`) (2026-11-16 23:30 UTC)

Acta `REPRODUCCION-HOLANDA-423-2026-11-16.md`. No se integra.

- **Lo que está bien y no se toca:** chequeo-6 igual al tuyo; anclas 2553 con 0/0/0; tus tres
  archivos `247 passed` y `4 failed` con el producto de `8d2cacc`; `e2e_maria.sh` OK sobre el SHA y
  la unión; `sabotaje_maria3.sh` 32 OK, `sabotaje_maria1a.sh` 10 OK, `catalogo3.sh` `rc=0`, 65 `ROJO`, 0 «ROJO?» ni sin rojo, «fallas: 0» (23:30:31);
  suite completa `6197 passed`, 0 rojos. Mi mapa independiente de `codigo_de_pais` (4019 formas,
  `8d2cacc` contra `a910c5f`) cambia sólo las seis de Holanda. Mis siete negativos pasan.
- **La causa de la devolución: una forma que lleva el código reemplazado se muestra distinta de
  lo que sale.** En `8d2cacc`, 434 se mostraba 434 y salía 434; ahora, con la API del catálogo,
  escribir «434» u «0434» guarda y devuelve eso, la pantalla lo pone tal cual y el TXT dice 423.
  Tiene camino hoy (escribirlo, o un 434 ya guardado que el lookup lleva a la grilla) y tu informe
  dice que el criterio 5 no se cumple. Un nombre («HOLANDA», como «CHINA») que se muestra como se
  escribió no es parte de esto.

**Criterio de la vuelta (comportamiento y prueba):**
1. Ningún lugar de la pantalla que muestre un origen guardado o escrito, y cuyo valor pueda llegar
   a un TXT hoy, muestra una forma que lleve el código reemplazado: muestra lo que sale en el TXT.
   La lista de lugares sale del código y va al informe con, para cada uno, si llega a un TXT hoy.
   Los que vi en `a910c5f`: la fila del catálogo (`catalogo.js:270`), el catálogo del cliente
   (`clientes.js:1427`), el origen que el lookup trae a la grilla (`upload.js:586`, `:600-602`) y
   la grilla de ítems antes de generar (`finalize.js`); la procedencia de la revisión
   (`review.js:252-271`). Según tu tabla, `default_origin` («Origen habitual», `clientes.js:1071`,
   `:1232`, `:1955`) y el «Origen frecuente» (`clientes.js:1139`, `main.py:8466-8475`) no vuelven a
   la generación: si es así, van como riesgo escrito y sin código. Sumá los que encuentres.
2. La familia como datos de un caso: las formas con el código reemplazado (434, 0434, el número
   434, «434 · HOLANDA», «434 - Holanda», «434 · PAISES BAJOS»), guardadas y escritas. Los nombres
   («HOLANDA», «Holanda», «Países Bajos») y «NL» son control: se muestran como hoy.
3. Un volcado antes y después de lo que muestra cada lugar para todos los demás países: sin
   diferencias. El diff va al informe. Mostrar todos los países con su etiqueta no es parte de
   esta vuelta (D261, abajo).
4. Lo guardado sigue sin reescribirse (`DECISIONS.md`, 2026-11-16 19:39 UTC).
5. El rojo con el arreglo revertido, una vez.

**Revisión:** §3 fuerte, como la pieza. `e2e_maria.sh`, `catalogo3.sh` y los guiones que anclen lo
que toques, desde la copia del SHA que entregás.

**Las D:**
- **D261:** la parte de 434 es esta devolución. La (a), mostrar todos los países con `label`,
  cambia la pantalla para todos y no se pidió: se la llevo a Emi con tu recomendación, aparte.
  No la hagas en esta vuelta.
- **D262 (a)**, decidido por la PM: a la cola de limpieza.
- **D263**, de la PM: `validate_items_for_maria` mira `origen` y el generador usa `pais_origen`
  primero; `pais_origen="4340"` con `origen="CN"` valida y sale `CARTPAYORI=4340`. Sólo por la
  API, ya en la base. Pieza aparte, después de D239 (a); no la toques ahora.
- **Supuestos 1 a 3:** aceptados. **La premisa del criterio 4:** verificada, bien dicho.

Después de esta vuelta sigue D239 (a), que te escribo al aceptar ésta.

**Próxima D: D264.**

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
