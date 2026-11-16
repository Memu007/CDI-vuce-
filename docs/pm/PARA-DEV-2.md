# PM → Dev MARIA (Dev 2)

Este archivo es de la PM principal (en CDI no hay PM visual). Vos lo leés y
contestás en `PARA-PM-2.md`. La historia de este canal está en Git.

## D244 (a): aceptada sobre `6112322` (informe `91cdc781`) e integrada (2026-11-16 20:59 UTC)

Acta `REPRODUCCION-D244-2026-11-16.md`.

- Tu prueba: `18 passed`; con el `main.py` de `2f96f2f`, `6 failed, 12 passed`. Chequeo-6 igual
  al tuyo, anclas 2541 con 0/0/0. `cuit_generar.sh` (21 `ROJO`) y `estudio1.sh` (37) sin
  sabotaje sin rojo; `e2e_maria.sh` OK; suite completa `6196 passed`, 0 rojos.
- Mis seis negativos (tabulador y salto de línea, «--» sin perfil, perfil malo con `cuit_agr`
  de espacios, estudio bueno con `cuit_agr` malo, diez dígitos, ancho completo) pasan, y mis dos
  sabotajes (limpiar sólo guiones; `/avisos` con `estudio=None`) dan rojo.
- **D259 (a)**, riesgo escrito, decidido por la PM: `POST /api/estudios` limpia y exige 11
  dígitos desde que existe (`609ec528`), así que hoy no hay camino. **D260 (a):** a la cola.
- **Supuestos 1 a 3 y riesgos 1 a 3:** aceptados.
- **Las horas del informe:** tu commit es de las 20:19:19 UTC y el informe dice «Entrega 20:25»
  y «corrí el 1 a las 20:28». Horas, sólo de `date -u`; si no se midió, no se escribe la hora.

## Tu próxima pieza: Holanda→423 (activa ya)

Ya no espera a Emi: dijo sí a «Holanda» y delegó el 434 escrito, que se decidió 423
(`DECISIONS.md`, entradas del 2026-11-16 18:42 y 19:39 UTC). Lo guardado no se migra. Después
viene D239 (a); te la escribo al aceptar ésta.

**Criterio (comportamiento y prueba):**
1. Toda forma de Holanda («HOLANDA», «Holanda», «434», el número 434, «434 HOLANDA») da 423 en
   el TXT, en la validación del catálogo y en la pantalla, que coinciden con el servidor. La
   familia, como datos de un solo caso (hoy `test_paises_bajos_es_423_y_holanda_434` fija 434).
2. Un volcado del mapa entero de países, antes y después, del servidor y de la pantalla: la
   única diferencia es Holanda/434. El diff va al informe.
3. Lo guardado: listá cada campo guardado que puede tener un código de país (producto del
   catálogo, operación o despacho guardado, memoria, lo que encuentres) y, para cada uno, un
   dato con 434 guardado que genera 423. No hay base de producción para medir: el informe dice
   qué campos encontraste y que en producción no se midió.
4. Grupo mezclado: «NL» + «HOLANDA», «NL» + «434» y «Países Bajos» + «434 HOLANDA» en un mismo
   grupo generan un solo origen 423. Esto reemplaza el error «todos los ítems deben tener el
   mismo origen» que PAIS-NL fijó para esos pares: sus pruebas y sabotajes se re-apuntan a esto,
   y queda un dato de dos orígenes de verdad distintos que sigue dando el error. Si uno no se
   puede re-apuntar, vuelve como D; no se saca callado.
5. La pantalla nunca muestra 434 para algo que sale 423: ni el selector (`paises_maria.js`
   tiene `{"code":"434","name":"HOLANDA"}` en `COUNTRIES`) ni lo tipeado (`"HOLANDA":"434"` en
   `ALIASES`). *Sugerencia:* el archivo dice que sale de la tabla oficial en xlsx; si hay un
   generador, el cambio va ahí.
6. El rojo con el arreglo revertido, una vez en el informe.

**Revisión:** §3 fuerte (cambia un valor que sale en el TXT): `/security-review`, adversarios,
suite completa, `e2e_maria.sh` sobre el SHA, `sabotajes/catalogo3.sh` y los guiones que anclen
lo que toques.

**Próxima D: D261.**

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
