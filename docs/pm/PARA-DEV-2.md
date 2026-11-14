# PM → Dev MARIA (Dev 2)

Este archivo es de la PM principal (en CDI no hay PM visual). Vos lo leés y
contestás en `PARA-PM-2.md`. La historia de este canal está en Git.

## Aviso: guarda de conexiones en `tests/conftest.py` (2026-11-13 16:06 UTC)

Llega con tu próximo merge de mi rama. Un error de teardown «… dejó N conexión(es) de aiosqlite abiertas…» es la guarda funcionando: un test o ayudante deja una conexión viva; se arregla cerrándola, no se saltea. Tu pytest entero sobre `ee2ee3c` corrió sin ella: el de SUFIJO-BORRADOR va después del merge. Desde hoy también corta al arrancar: un `rc=4` con «La guarda de conexiones no ve una conexión abierta de aiosqlite…» es un venv con aiosqlite viejo (antes de 0.22), no un rojo tuyo; instalá el de `requirements.txt` y volvé a correr.

## Vencidos `sabotaje_valor1b.sh` y `sabotaje_doc1.py`: aceptados sobre `70eb5dc` y `d4c6b73` (informes `a926930` y `f3a7d29`) e integrados (2026-11-14 09:56 UTC)

Actas `REPRODUCCION-SABOTAJE-VALOR1B-2026-11-14.md` y `REPRODUCCION-SABOTAJE-DOC1-2026-11-14.md`.
Los dos SHA finales pasaron por revisor: bien.

**valor1b:** con la copia de `70eb5dc` da 22 `ROJO`, 0 `FALLA`, `rc=0`; casos 8 y 10 con 1 y
2 failed; chequeo-6 igual al tuyo; anclas 2/0/0.
- Mis negativos: el guion viejo da `PATRON NO ENCONTRADO (2 veces)` en el 8; con el caso 8
  sacando `cuentasViejas();` de `borrarSeguroCalculado` da `FALLA … quedó verde`.
- **Supuesto (23→22):** aceptado; son 22 casos y 22 `ROJO`.
- **Riesgos 1 a 3:** aceptados. El 2 lo miré: el 9 y el 10 son mutaciones distintas que
  espera una sola prueba. El 1 y el `22` a mano van a la cola de limpieza.

**doc1.py:** con la copia de `d4c6b73`, en un worktree en ese SHA, da 3 `OK`, `rc=0`; a mano,
38 y 5 failed, cada uno sólo en su prueba; chequeo-6 igual al tuyo.
- Mis negativos: el guion viejo da `Patrón cambiado: servidor`; con «generador» neutro
  (`destinacion_del_txt(tipo_destinacion, False)`) el guion corta con `5 passed`.
- Miré por qué falla cada mutación: en las dos la EC pasa el control (el error siguiente o
  `DID NOT RAISE`), ningún 500.
- **Riesgos 1 a 4:** aceptados; tu línea va a la cola de limpieza.

**Cómo sigue:**
1. Los 2 vencidos que quedan, uno por pieza: vas por `sabotaje_maria7.sh`, después `guardar2.sh`.
2. D249 (a), con el criterio de la sección D247 de abajo.

D244 y D239 esperan a Emi:
- Si dice que sí a D244, te la escribo con su criterio.
- Si dice que sí a D239 (a), lleva adentro, como datos de un caso, un código sin sigla con
  el nombre de otro país («434 BELGICA» guarda `BE` sin avisar).
- Si Emi dice que «Holanda» también es 423, es una pieza chica aparte.

**Próxima D: D250.**

## Vencido `sabotaje_maria5.sh`: aceptado sobre `c0505cc` (informe `9153d23`) e integrado (2026-11-14 09:30 UTC)

Acta `REPRODUCCION-SABOTAJE-MARIA5-2026-11-14.md`. Regla nueva de la PM: en un vencido de sólo
arnés, un último commit que cambia únicamente comentarios no necesita revisor si el informe lo dice.

## Vencido `sabotaje_maria1d.sh`: aceptado sobre `6e4e658` (informe `38a7ed2`) e integrado (2026-11-14 08:18 UTC)

Acta `REPRODUCCION-SABOTAJE-MARIA1D-2026-11-14.md`. Supuesto y riesgos aceptados.

## D248 (c): aceptada sobre `3fcc9c4` (informe `8f50af3`) e integrada (2026-11-14 07:57 UTC)

Acta `REPRODUCCION-D248-2026-11-14.md`. Supuestos 1 y 2 y riesgos aceptados; el `38`
escrito a mano quedó en `COLA-LIMPIEZA.md`.

## D247 (a): aceptada sobre `4a58c68` (informe `ee3ccfd`) e integrada (2026-11-14 07:03 UTC)

Acta `REPRODUCCION-D247-2026-11-14.md`. Con la copia de `4a58c68`: las dos pruebas
`171 passed`; tu cambio del criterio da `4 failed` en `4a58c68` y `171 passed` en
`0224f01`; `sufijos2.sh` 33 `ROJO`, 0 `FALLA`, `rc=0`; `sabotaje_sufijos1.sh` 46 `ROJO`,
`rc=0`; anclas en 5 y 1; chequeo-6 igual al tuyo. Gracias por medir D249 sin que te lo
pidiera.

- **D249: (a), decidido por la PM. Va después de D248 (c) y los 6 vencidos.** Te
  autorizo a tocar sólo `tests/test_sufijos2.py` y `scripts/testing/sabotajes/sufijos2.sh`
  (ya le avisé a la Técnica). Medí la familia entera de los fragmentos «…» de
  `limpiar_sufijo`: además de tus dos, hay siete más que nadie distingue (tabla en el
  acta). Se acepta así, con cada cambio solo:
  - da rojo en la entrega y queda verde en la base `4a58c68`:
    - «pide» con `«{sufijo[:40]}»`, en más de un dato (hoy lo sostiene uno solo);
    - «pide» con `«{sufijo[pos:pos + 40]}»`;
    - «cambiaría» con `en «{sufijo[:40]}»`;
    - `«{cambiaria[:20]}»` cambiado por `«{cambiaria}»` y por `«{sufijo[:20]}»`;
    - «está vacío» sin recorte (`«{uno[0]}»`);
    - «cerca de» con `sufijo[:20]` y con `sufijo[pos:]`;
    - «no se puede separar» con `sufijo[:10]` en lugar de `sufijo[:80]`;
    - el aviso con `limpio[:10]` en lugar de `limpio[:80]`;
  - `sufijos2.sh` entero en `ROJO`, con un sabotaje por cambio y la cuenta exacta en
    el informe;
  - `sabotaje_sufijos1.sh` sigue en 46, anclas en 5 y 1, las dos pruebas verdes.
  - **Sugerencia** (no es criterio): pares (sufijo, lo que nombra el error) y un
    código de más de 40 o de 80 letras, para que el recorte se vea.
- **Riesgos:** aceptados. `.upper()` y el texto de la instrucción, que tu adversario
  mostró verdes, son previos: no entran en D249.

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

## EMAIL-1 (D45 (1)): aceptada sobre `40423be`, sin cambio de producto ni integrar (2026-11-08 PM)

Emi dio 12 h más: corte el **2026-11-09 05:00 UTC**, como el de hoy.

Evidencia: `docs/pm/REPRODUCCION-EMAIL-1-D45-2026-11-08.md`. Igual al informe,
ahora también sobre `40423be`: chequeo-6 sin avisos; `email1.sh` 15 ROJO, sin
rojo 0; en PG 16 con `C.UTF-8`, la familia da 1 letra (U+0130), `und-x-icu` 0
y `ucs_basic` 1407; `abuso2_postgres.py` fallas 0; `abuso2.sh` 20 ROJO.
Aceptás bien la premisa caída y admitir que `email1.sh` estaba roto.

- **D131 → (a)**, va a Emi. Sumo una prueba a tu favor: con una base mía en
  `C`/`SQL_ASCII`, las variantes con İ mandan 1 mail en vez de 3. La base no
  las encuentra.
- **D132 → (a)**, decidida por la PM: pieza **RESET-3**, después de AVISOS-2.
  Pedir el reset tiene tope por cuenta, como `recuperar:cuenta:`. El rojo es
  con IPs distintas y lleva sabotaje propio.
- Las cuatro líneas «EMAIL-1» de `main.py` van a la cola de limpieza.

**Tarea activa: AVISOS-2**, con lo de arriba (D129 (a), D130 (a) y las tres
bajas). Después, RESET-3. Próxima D libre: D133.

## AVISOS-1: aceptada sobre `0aed334`, sin integrar (2026-11-08 PM)

Evidencia: `docs/pm/REPRODUCCION-AVISOS-1-2026-11-08.md`. Igual al informe:
chequeo-6 con los tres avisos explicados; `avisos1.sh` 22 ROJO y `seguro2.sh`
19 ROJO, sin rojo 0. Las seis suites dan `256 passed`, no 199: el número del
informe quedó de una corrida anterior. Sonnet alto: ninguna importación
frenada por error y ninguna exportación que genere; sin 500.

- **D129 → (a)**, decidida por la PM: el predicado único antes de limpiar.
- **D130 → (a)**, decidida por la PM: pieza **AVISOS-2**, después de EMAIL-1.
  Suma tres bajas del adversario:
  1. `es_exportacion` normaliza el texto entero (2 millones de caracteres,
     unos 5 s con el proceso trabado): que un texto enorme no cueste;
  2. con el seguro borrado y de vuelta a FOB, el 400 dice «al pasar a un
     incoterm que ya lo lleva en el precio»: tiene que decir lo que pasó,
     como la nota;
  3. `/generate_maria_export` acepta `IC04` o `TRAN` en un TXT de exportación.
- Al dar números, el del SHA que entregás.

## SUFIJOS-2+SEGURO-1: aceptada sobre `ad2d0f8`, sin integrar (2026-11-08 PM)

Evidencia: `docs/pm/REPRODUCCION-SUFIJOS-2-SEGURO-1-2026-11-08.md`. Igual al
informe: chequeo-6 (`+86/−62`, el AVISO de 24 netas explicado), 224 passed,
`sufijos2.sh` y `seguro1.sh` con «sabotajes sin rojo: 0». Mío: el grupo
MARIA da 1549 passed, y mis negativos (`−5`, `１０`, `1⁄2`, `1.500,50`, `1·5`,
`1٫5`, `X1.500`) frenan.

- **D123 → (a)**, decidido por la PM, como pieza chica **AVISOS-1** después
  de SEGURO-2: el rechazo de exportación va después de limpiar los textos,
  en los dos endpoints, con su caso de la familia (cualquier invisible o
  espacio adelante del código).
- Supuesto (los avisos miran los textos limpios): de acuerdo, queda.
- Riesgos anotados, no se tocan: `31/02/2026` pasa como fecha; `٥` frena con
  el mensaje de «vacío».

Seguí con **SEGURO-2**. Próxima D libre: D124.

## ENTRADAS-4: aceptada sobre `6baddb5`, sin integrar (2026-11-08 PM)

Evidencia: `docs/pm/REPRODUCCION-ENTRADAS-4-2026-11-08.md`. Igual al
informe: chequeo-6 (`+1/−1`, avisos 0), sonda contra Postgres `fallas: 0`,
`entradas4.sh` 5 ROJO con «sabotajes con falla: 0». Mío: los tests que suben
Excel con un `cliente_id` real siguen verdes (`55 passed`).

- Supuesto (NUL → cliente inexistente, 200 sin mapeo): de acuerdo, queda.
- Riesgos anotados; el arnés y los helpers copiados de `*_postgres.py` van
  a la cola de limpieza.

Seguí con **SUFIJOS-2+SEGURO-1**. Próxima D libre: D118.

## ENTORNO-4: aceptada sobre `44b9759`, sin integrar (2026-11-08 PM)

Evidencia: `docs/pm/REPRODUCCION-ENTORNO-4-2026-11-08.md`. Igual al
informe: chequeo-6 (`+19/−26`, avisos 0), `36 passed`, `entorno4.sh` y
`entorno3.sh` 4 ROJO cada uno con «sabotajes sin rojo: 0». Mis negativos:
en producción, `FRONTEND_URL` vacía, con un espacio, un tab o sólo `/` no
arranca; `ENVIRONMENT=Production` también la exige.

- Compose y preflight: bien tomados; quedan.
- `docker-compose.yml:61`, el mensaje de `JWT_SECRET_KEY` cortado por «:»:
  a la cola de limpieza.
- Publicar este SHA pide `FRONTEND_URL` en Railway: lo paso a Emi.

Seguí con **ENTRADAS-4**. Próxima D libre: D118.

## ENTRADAS-3: aceptada sobre `cf5309a`, sin integrar (2026-11-08 PM)

Evidencia: `docs/pm/REPRODUCCION-ENTRADAS-3-2026-11-08.md`. Igual al
informe: chequeo-6 (`+48/−21`, el aviso explicado), `47 passed`, Postgres
`fallas: 0`, `entradas3.sh` 11 y `entradas2.sh` 24 ROJO con «sabotajes con
falla: 0». Mis negativos: NUL en el nombre del parámetro da 400; `%2500` y
un `€` escapado dan 200.

- **D115: (a), decidido por la PM.** Lo nuevo ya no entra; una fila vieja
  con un número enorme se limpia a mano sólo si aparece el 500, y eso pasa
  por Emi porque es dato de producción.
- **D117: (a), decidido por la PM.** Pieza chica **ENTRADAS-4**, después de
  ENTORNO-4: ningún campo `Form` que va a la base da 500 por un NUL. Caso con
  la familia de campos como datos y sabotaje propio (§3, datos).
- **Al informe:** el comando de `entradas3.sh` necesita `PG_URL`; sin ella
  sale al empezar. Ponelo en el próximo bloque de comandos.
- **A la cola de limpieza:** `_TEXTOS_DEL_CLIENTE` repite los nombres que
  leen el alta y la edición, y `DataStore.add_operation` parece muerto.
- **Riesgo anotado:** `client_ip` `String(45)` con una lista de IPs detrás de
  un proxy.

Tu orden: ENTORNO-4 (en curso) → ENTRADAS-4 → SUFIJOS-2+SEGURO-1 → SEGURO-2
→ EMAIL-1 → CONEXIONES-1 → OBSERVABILIDAD-1 → ORG-1+D40, y D102. Próxima D
libre: D118 (la técnica también toma de la misma secuencia).

## ENTORNO-3: aceptada sobre `fd545c1`, sin integrar (2026-11-08 PM)

Reproducido igual al informe: chequeo-6 (`+11/−10`, avisos 0), `30 passed`,
`entorno1.sh` 10, `entorno2.sh` 8 y `entorno3.sh` 4 ROJO, sin rojo 0. Mis
negativos (`prod`, `Production`, `staging`, vacío; `*` y blanco en
`ALLOWED_ORIGINS`) cierran, y `development` abre. Acta:
`REPRODUCCION-ENTORNO-3-2026-11-08.md`.

- **D111: (a), decidido por la PM.** A la cola de limpieza (ya anotado).
- **D112: (c), decidido por la PM**, con **D113 (b)**: pieza chica
  **ENTORNO-4**, después de ENTRADAS-3. Fuera de desarrollo, sin
  `FRONTEND_URL` la app no arranca (como `ALLOWED_ORIGINS`), y
  `billing_service.py` usa la misma URL, sin caer a localhost. Sabotajes en
  el arnés de ENTORNO.
- **Numeración:** la Dev técnica también usó D112 para otra cosa; la suya
  queda registrada como D114. Tu próxima D libre: **D115**. Desde ahora,
  antes de numerar, mirá la última D de `DECISIONS.md` y de los dos canales.

Tu orden: **ENTRADAS-3** (D109, D110) → ENTORNO-4 → SUFIJOS-2+SEGURO-1 → el
resto.

## ENTRADAS-2: aceptada sobre `b8aa9bd`, sin integrar (2026-11-08 PM)

Reproducido igual al informe: chequeo-6 (`+115/−49`, el aviso de 66 netas
alcanza), `36 passed`, PG 33 OK con `fallas: 0`, `entradas2.sh` 24 ROJO con
falla 0. Mis 21 negativos (NaN e infinito como texto, números fuera de
int32, cuerpo vacío o lista, claves de estudio sin número, NUL en `/static`)
dan lo esperado. Sonnet alto: nada nuevo de la pieza. Acta:
`REPRODUCCION-ENTRADAS-2-2026-11-08.md`.

**D109: (a), decidido por la PM.** Pieza ENTRADAS-3, después de ENTORNO-3.
Lleva: `tiene_medio_par` fuera del try (~8734 y ~8889), el NUL en el query
string, el log de `api_logs` con NUL o ruta de más de 200 caracteres, y
además:
- **D110 (a):** un campo del cliente que no es texto da 400;
- un número finito enorme (`1e308`) que hoy se guarda y después tira 500 en
  `GET /api/clientes` y en las métricas del cliente (Postgres, suma de
  `total_value`): que no se guarde o que la suma no reviente. Caso de la
  familia, no sólo el ejemplo.

Riesgos que quedan: el texto nuevo de change-password; la clave de estudio
de 8 letras ahora rechazada (va a la mirada en navegador antes de
publicar); 40000 ítems lentos al guardar al cliente.

## FRONT-422: aceptada sobre `4dbdb0b`, sin integrar (2026-11-08 PM)

Reproducido igual al informe: chequeo-6 (`+73/−31`, el aviso de +42 alcanza),
`33 passed`, `front422.sh` 17 ROJO, con falla 0. Mis negativos en node
(lista vacía, texto en blanco, `string_too_short`, `loc` anidado y de query,
`value_error`) dan lo esperado. Acta: `REPRODUCCION-FRONT-422-2026-11-08.md`.

**D108: (a), decidido por la PM.** Queda en el front. El script de sabotajes
se queda. R1 a R5 quedan como riesgos; R1 va a la mirada en el navegador
antes de publicar.

## ENTORNO-2: aceptada sobre `bf92bf9`, sin integrar (2026-11-08 PM)

Reproducido igual al informe: chequeo-6 (`+24/−26`, avisos 0), `22 passed`,
`entorno1.sh` 10 ROJO y `entorno2.sh` 8 ROJO, sin rojo 0. Mis negativos
(`"development\n"`, `"test "`, `dev`, `local`) dan las 11 puertas cerradas. Opus
alto: nada abierto, sin ciclos de importación, suite `5124 passed`. Acta:
`REPRODUCCION-ENTORNO-2-2026-11-08.md`.

**D107: (a), decidido por la PM.** ENTORNO-3 es pieza tuya después de
ENTRADAS-2: FRONTEND_URL (main.py:223), ALLOWED_ORIGINS (:406), HSTS
(security_middleware.py:62) y el pase de rate limit para 127.0.0.1 (:211)
con la misma regla: sin `ENVIRONMENT` de desarrollo, como en producción. Lo
mismo que ENTORNO-2: sabotajes en el arnés de `test_entorno1`. Los
monkeypatches de `main_mod.IS_PRODUCTION` que quedaron en tests viejos van a
la cola de limpieza, no a esta pieza.


## Rojo de `despacho1b`: aceptado sobre `d69233c`, sin integrar (2026-11-07 PM)

`283 passed`, chequeo-6 `+0/−0` sin avisos; la causa la medí aparte (una
pasada del recolector con 3 M objetos gasta 0,53 s; con `gc.freeze`, 0).
Acta: `REPRODUCCION-DESPACHO1B-ROJO-2026-11-07.md`. **D106: (a), decidido
por la PM**, queda como riesgo. Tu orden no cambia: la devolución de ABUSO-2
primero, después ENTORNO-2. Próxima D: D107.

## ABUSO-2: aceptada sobre `1f79a8e`, sin integrar (2026-11-07 PM)

Producto `8ad47ee`, pruebas `22a2c4b`, `b6ad266` y `1f79a8e`. Reproducido
igual al informe: chequeo-6 (`+0/−0` de producto, avisos 0), `90 passed` y
`abuso2.sh` 20 ROJO (también el de Postgres), `fallas: 0`. Mi ejemplo distinto (`descontar` resta `n − 1`)
cae en 7 casos. Acta: `REPRODUCCION-ABUSO-2-2026-11-07.md`.

Riesgo, no devolución: un `delete` de lo propio por prefijo pasa en verde
(hoy no hay camino; una clave ajena que empiece igual lo cerraría si algún
día tocás ese caso). Siguen los riesgos de D105 y de Opus.


## ENTRADAS-1: aceptada sobre `c839197`, sin integrar (2026-11-07 PM)

Los cuatro puntos de la devolución dan rojo: `entradas1.sh` 32 `ROJO` sin
fallas. Mi ejemplo distinto (email con tope 101) cae en registro, estudio y
perfil. Acta: `REPRODUCCION-ENTRADAS-1-2026-11-07.md`. Lo que sigue de acá ya
está en tu orden: FRONT-422 (D100) y ENTRADAS-2 (D101, D104); D102 chore y
D103 en la cola.

## ENTORNO-1: aceptada sobre `83085e4`, sin integrar (2026-11-07 PM)

Reproducido: chequeo-6 igual al informe, `82 passed`, `entorno1.sh` 10 en
rojo, `cobro_mp2.sh` 23 en rojo, suite `5017 passed` igual a la tuya. Opus y
Sonnet alto con uvicorn real: con `ENVIRONMENT` ausente o desconocido no
abre ninguna puerta; nada serio introducido. Acta:
`REPRODUCCION-ENTORNO-1-2026-11-07.md`. **Supuestos S1 a S4: aceptados.**

- **D97: (a), decidido por la PM.** Que no arranque sin `production` y con
  clave débil es lo buscado; antes de publicar se confirma Railway con Emi.
- **D98: (a), pieza nueva ENTORNO-2**, después de ABUSO-2 (seguridad chica,
  Emi: «a cero»). Comportamiento pedido: con `ENVIRONMENT` ausente o
  desconocido, los controles de configuración se portan como en producción:
  CSRF bloquea, cookies `Secure`, `/docs` y `/openapi.json` cerrados, sin
  `DATABASE_URL` no cae a SQLite, VUCE simulado no permitido, y
  `ENABLE_SIMULATE_CHARGE` no abre el cobro simulado fuera de desarrollo.
  Un caso por causa con los valores como datos, como en `test_entorno1`.
  Sugerencia (no es criterio): que todos pregunten a `_es_desarrollo`.
- **D99: a Emi** (usuarios demo que ya estén en producción); no bloquea.
- A la cola de limpieza: los parches de `IS_PRODUCTION` en `test_email1` y
  la clase tautológica de `test_prelaunch_block3`.

El rojo de `despacho1b`: falló una vez en la suite entera y pasa solo;
diagnosticar la causa (el diff no toca el lector).

## CATALOGO-LARGO-2: aceptada sobre `d5bc7c1` (pruebas `b0bbd8c`), sin integrar (2026-11-06 PM)

Acta: `REPRODUCCION-CATALOGO-LARGO-2-v2-2026-11-06.md`. Coincide con tu
informe: `test_catalogo_largo2.py` 40 passed, Postgres 21 OK y `fallas: 0`,
37 sabotajes en rojo sin falla, chequeo-6 `+153/−75` con el aviso de 78 netas que explicaste.
La suite da `5 failed, 4984 passed`: los 5 de D73. Probé ejemplos distintos de
los de la devolución (medio par bajo dentro del texto, objeto y decimal en
origen, entero en NCM y en proveedor, NCM entero por `guardar-uso`): los siete
dan 400 sin guardar nada; en la base, cuatro daban 500. Opus y Sonnet alto,
en PG 16, no encontraron 500 nuevos, escrituras a medias ni filas perdidas.
Sin integrar, por lo mismo que `ca87d82`.

Una corrección al informe: en D84 decís que el usuario ve qué fila corregir.
No es así: el 400 no nombra el ítem, `saveCatalogLearn` sólo mira `res.ok`, y
la pantalla dice «Algunos productos no quedaron» cuando no quedó ninguno
(`finalize.js:764-768`). No empeora la base, pero una premisa así tiene que
estar probada antes de ofrecerla para decidir.

- **D84: (a)**, el lote entero se rechaza. Que el 400 nombre el ítem y que la
  pantalla diga la verdad va a CATALOGO-3. Decidido por la PM.
- **D85: (a)**, a CATALOGO-3 con D76; suma el proveedor `"\x00"`, que hoy
  guarda bajo `vendor_id ""`.
- **D86: (a)**, a CATALOGO-3 con D78.
- **D87: (a)**, el patrón de `despacho1b.sh:325` en un commit de pruebas
  aparte, con su rojo, en tu próxima entrega (PYPDF-1).
- **A la cola de limpieza** (decidido por la PM): la fila que choca en
  `_migrate_catalogo_claves` (sin `ORDER BY`, log repetido en cada
  arranque); el índice de `_migrate_product_history_clave` sin
  `lock_timeout` (`main.py:1464`); lotes o `PUT` a la vez dan 500;
  `/api/catalog/lookup` con 500 y sin limpiar el NUL; precios raros; los
  mensajes del NCM («pasa de 2000» con tope 20, «La NCM» y «El NCM»).

CATALOGO-3 sigue esperando el sí de Emi.

## SESION-1: aceptada sobre `2e62761`, sin integrar (2026-11-06 PM)

Acta: `REPRODUCCION-SESION-1-v3-2026-11-06.md`. Coincide con tu informe:
`test_sesion1.py` 42 passed (13 rojos en la base), motores pg OK, 38 sabotajes
en rojo, chequeo-6 `+95/−89` sin avisos, suite `4933 passed` con sólo las 5 de
D73. Probé otro ejemplo del pool (40 `PUT` del perfil): ningún 500 y otro
usuario entra al instante; en la base, 39 respuestas 500 y 29,5 s. Las dos
causas quedan cerradas.

- Se integra junto con `ca87d82`, por lo mismo: debajo vienen piezas sin
  aceptar (ahora también CATALOGO-LARGO-2).
- **D73:** no se fija una versión vieja a ciegas. Primero hay que ver qué
  cambió en 6.21.4, que puede ser un arreglo de seguridad. Va como pieza chica
  **PYPDF-1**, después de RESET-1. Decidido por la PM.
- **D74: (a)**, se acepta así. Lo que queda (la conexión tomada durante
  bcrypt, Gemini en `/api/ncm/sugerir` y la subida pública de PDF) entra en
  CONEXIONES-1 con los números del acta. Decidido por la PM.
- **D75: (a)**, a `COLA-LIMPIEZA.md`. Decidido por la PM.
- **Pieza nueva RESET-1** (seguridad, chica; Emi: «arreglos chicos de
  seguridad a cero»). Va después de CATALOGO-LARGO-2, antes de ABUSO-1. El
  problema viene de antes: `reset_password` no invalida nada.
  - Un link de reset pedido antes de que el dueño cambie la clave o el email
    ya no sirve después de ese cambio.
  - Un link usado una vez no sirve una segunda vez, tampoco con dos usos a la
    vez (se consume atómico, probado en Postgres).
  - El caso lleva los cambios como datos: cambio de clave, cambio de email,
    otro reset y el mismo link dos veces.
- Las anclas de `csrf3.sh` las actualizo yo al integrar.
- **Sigue CATALOGO-LARGO-2**, como ya venías. Tus próximas D empiezan en D76.

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
