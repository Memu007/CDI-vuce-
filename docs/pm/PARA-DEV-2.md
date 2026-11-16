# PM → Dev MARIA (Dev 2)

Este archivo es de la PM principal (en CDI no hay PM visual). Vos lo leés y
contestás en `PARA-PM-2.md`. La historia de este canal está en Git.

## D257 (b): aceptada sobre `3c7eb14` (informe `38cb92f`) e integrada (2026-11-15 05:57 UTC)

Acta `REPRODUCCION-D257-2026-11-15.md`.

- Con la copia de `3c7eb14`: 70 `ROJO`, 0 `FALLA`, `rc=0`; los siete nuevos, `1 failed, 84
  passed`. Chequeo-6 igual al tuyo, anclas 2541 con 0/0/0.
- Mis dos negativos (en los sufijos, `grupos.clear(); grupos.add(gid)`; en el arancel, el `elif`
  del grupo pidiendo además `item.get("sufijo")`) dan rojo con tu prueba, cada uno en su dato, y
  `83 passed` con la de `e1bd17a`.
- **La premisa del punto 2** estaba mal en mi criterio; tu corrección (un sufijo de operación sin
  AI en `un_grupo_sin_el_suyo`) es la correcta.
- **D258 (a)**, decidida por la PM: va a la cola de limpieza.
- **Supuestos 1 a 4 y riesgos 1, 3 y 4:** aceptados. **Riesgo 2:** riesgo escrito. Con tu
  sabotaje 67, `test_maria9_sufijo_operacion.py` da `27 passed`, pero el generador igual corta
  con «Falta el sufijo de valor SBT» sin pasar por `usa_el_sufijo_de_la_operacion`: se pierde
  un 400 claro, no sale un TXT sin sufijo. No abre pieza.

## Tu próxima pieza: D244 (a), con el sí de Emi (2026-11-16 18:42 UTC)

Emi contestó: D244 sí, «Holanda» sí y D239 sí. Tu cola: D244 → Holanda→423
(también el número 434 escrito: sale 423) → D239 (a). Las dos últimas te las
escribo al activarlas; no las toques antes.

**Criterio (comportamiento y prueba):**
1. Con un CUIT del despachante que no cierra con su dígito verificador,
   `/generate_maria/avisos` lo anuncia, venga del perfil, de `cuit_agr` o del
   estudio elegido, con el mismo texto que el 400 de `/generate_maria` (el que
   dice dónde corregirlo). Sin CUIT inválido, no aparece ningún aviso nuevo.
2. Un `cuit_agr` de puros espacios o puros guiones cuenta como que no vino, en
   los avisos y al generar: se usa el del perfil (o «Falta el CUIT…» si no
   hay). Decidido por la PM: es la mitad de tu (a). Tu caso de
   `tests/test_cuit_generar.py` que hoy fija el 400 que nombra «» pasa a fijar
   esto.
3. El orden estudio → `cuit_agr` → perfil queda en un solo lugar.
   *Sugerencia:* que `/avisos` use `_cuit_del_despachante`.
4. La familia (los tres orígenes inválidos, `cuit_agr` en blanco con y sin
   perfil, y uno válido sin aviso) como datos de un solo caso. El rojo con el
   arreglo revertido, una vez en el informe.

**Revisión:** la misma que CUIT-GENERAR (§3: toca el CUIT que sale en el TXT):
`/security-review`, adversarios, suite completa y `e2e_maria.sh` sobre el SHA.
Si tocás la pantalla, su guion (`pantalla_cuit_generar1.js`) corre también.

**`test_despacho1b`:** lo sigo midiendo yo.

**Próxima D: D259.**

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
