# PM → Dev MARIA (Dev 2)

Este archivo es de la PM principal (en CDI no hay PM visual). Vos lo leés y
contestás en `PARA-PM-2.md`. La historia de este canal está en Git.

## D239 (a): aceptada sobre `01c28e83` (informe `42cad854`), integrada; D263 activa (2026-11-17 08:53 UTC)

Acta `REPRODUCCION-D239a-2026-11-17.md`, sección «Vuelta». Lo que corrí da igual que tu informe:
chequeo-6 (+57/−14, un AVISO), el rojo con el arreglo revertido («At index 7 diff: None !=
'RESTO (AFRICA)'»), suite completa (6199 passed), `sin_sigla` 16/16, `holanda423` 17/17,
`e2e_maria.sh` OK, volcado igual a `196ef370` y anclas como la base. `despacho1b.sh` con
Postgres sigue corriendo (11 ROJO y 0 sin rojo a las 08:51); si da un «sin rojo», la pieza se
reabre. Cada código de la tabla con cada nombre o alias del índice, en cuatro formas (unas
900 000), da 0 países equivocados (la base daba 434 918): eso vale para los nombres que el índice
conoce. El ejemplo que no te di, «212 ARUBA (TERRITORIO DE PAISES BAJOS)», da ningún origen.
El adversario (unas 2,5 millones de formas) no encontró país equivocado con texto ASCII.

**Respuestas (decidido por la PM):**
- **AVISO +43 líneas netas:** aceptado con tu motivo. La línea de los tres reconocedores de país
  entra a `COLA-LIMPIEZA.md` en este commit.
- **D266, ampliado:** no son sólo nombres en inglés: cualquier nombre que el índice no conoce deja
  ganar al código («435 República Dominicana» → 435, Chipre; ya pasaba en `196ef370`). Riesgo
  escrito, no pieza: `origen_iso2` sólo lee el despacho impreso por el sistema oficial, que trae
  el nombre de la tabla, y lo de pantalla pasa por `origen_para_catalogo`. Va a Emi como
  propuesta de alias.
- **Dígitos de ancho completo** («３１０ ＢＲ» → BR, nuevo de esta vuelta): el `\d` del patrón
  acepta dígitos Unicode y `codigo_de_pais` no. Riesgo escrito, junto a la propuesta de alias;
  no lo arregles ahora.
- **D267** («900 SD» da Sudán, y SN, NO, SI, ROU): riesgo escrito; ya estaba en la base.
- **Pérdidas con aviso de más** («310 12», «310 12,5 KG», «143 - REP. DE SUDAFRICA», «310 POR
  MAR», «309 COREA (SUR)», «341 HONG KONG (CHINA)»…): aceptadas. Son ruidosas.
- El tope de CPU de `test_despacho1b` queda como riesgo escrito; no es de esta pieza.

## D263: la validación y el TXT leen el mismo campo (pieza activa)

Hoy `validate_items_for_maria` (`maria_generator.py`) revisa `item["origen"]`, pero el generador
escribe `pais_origen` si viene y si no `origen`. Por la API (`MariaRequest.items` es una lista
libre), un ítem con `pais_origen="4340"` y `origen="CN"` valida y sale `CARTPAYORI=4340`. La
pantalla no manda `pais_origen`. Pieza de la PM (`DECISIONS.md`, 2026-11-16 23:30 UTC).

**Criterio (comportamiento y prueba):**
1. La validación y el TXT leen el mismo campo. La familia, como datos en un caso:
   - `pais_origen` no reconocido («4340») con `origen` válido: error que nombra el ítem, y
     nunca llega a `CARTPAYORI`;
   - `pais_origen` válido sin `origen`: hoy da «Falta origen»; tiene que comportarse según el
     mismo campo que usa el TXT;
   - ninguno de los dos: error, nunca el `'CN'` de respaldo;
   - `pais_origen` vacío con `origen` válido: como hoy.
2. Lo que manda la pantalla (sólo `origen`) sigue igual.
3. El rojo con el arreglo revertido, una vez en el informe.
4. Revisión §3 fuerte (cambia lo que sale en el TXT): suite completa, `e2e_maria.sh` sobre el SHA,
   adversarios y los guiones que anclen lo que toques.

Sugerencia, no criterio: un solo lugar que diga qué campo manda, y que lo usen la validación y el
generador.

**Próxima D: D268.**

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
