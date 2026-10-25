# NOW — CDI

Actualizado: 2026-10-25. Estado vigente; la historia está en Git.

Método al día con CAMBIOS.md del secondbrain hasta 2026-10-21 (aplicado 2026-10-24).

**Publicado 2026-10-24 20:33 UTC:** `main` = `8b45207` (EXCEL-3 + CLIENTE-1),
con «dale 8b45207» de Emi; avance limpio sobre `dddcf6d`. Evidencia: CI
40128443771 verde (tests y e2e) sobre ese SHA; producto idéntico a `3fd8826`,
donde la suite local de la PM dio verde; sabotajes sobre `8b45207`: excel3
27/27 en rojo; cliente1 14 rojos y 1 «sin rojo» por una carrera de la prueba
(el foco a `#cfNombre` a los 80 ms parte el `fill` del CUIT; reproducida 2
de 82), sólo de prueba, va como PRUEBAS-1. La cadena de los scripts de piezas
viejas sigue corriendo y se anota al terminar. Falta: que Emi lo pruebe en el
sitio (proforma real y alta de cliente).

**EXCEL-3 aceptada 2026-10-24 19:30 UTC** (Dev técnica; producto `f3f9eb8` +
`b76be2f`): integrada por SHA (`a173af2`) a la rama de la PM, merge `a0c15ac`.
**Publicada** en `8b45207` (arriba); falta que Emi pruebe la proforma real en el sitio.
Detalle en `REPRODUCCION-EXCEL-3-2026-10-24.md`. D1 (descuento positivo,
sólo leído) y D2 (CLIENTE-1, a la vista con aviso) decididas por la PM;
Emi puede cambiarlas. Lo menor del adversario queda como EXCEL-3b, después
de PA-1.

**CLIENTE-1 aceptada 2026-10-24 19:41 UTC** (Dev técnica; producto `fbc006a` +
`12ff9b6`): el alta de cliente muestra CUIT, razón social, domicilio e inicio
de actividad y avisa cuáles faltan. Integrada por SHA (`c402bcb`) a la rama
de la PM, merge `23d7d5d`. **Publicada** en `8b45207`. Detalle en
`REPRODUCCION-CLIENTE-1-2026-10-24.md`. D3 (a) decidida por la PM: editar no
borra una fecha guardada en otro formato; va con PA-1. Hallazgo: la fecha de
inicio va al TXT como `AAAA-MM-DD` y el MARIA usa `DD/MM/AAAA`; sumado a
MARIA-7 como punto 9.

**PA-1 + D3 aceptada 2026-10-24 21:10 UTC** (Dev técnica; producto
`489daf4`, `c7e4c3a`, `26797f8`, `d8e084c`): «PA SIM» en las pantallas y
editar un cliente no borra una fecha de inicio que el campo no muestra.
Integrada con `merge` (`fe41228`), **sin publicar**. Detalle en
`REPRODUCCION-PA-1-2026-10-24.md`. D4–D7 decididas por la PM: la demo de la
landing va como PA-1b; la fecha validada en la API (con «None» y años de 5
cifras) va a CLIENTE-1b, y limpiar lo guardado en producción lo decide Emi.

**PRUEBAS-1 + PA-1b aceptadas con nota 2026-10-25 00:47 UTC** (Dev técnica,
sobre `e924b29`): sólo pruebas y la demo de la landing. Integrado `e924b29`
exactamente (merge `4f00636`), sin los commits de EXCEL-3b que vienen
después en su rama; **sin publicar**. `foco_cliente1.sh` dio rc=1 sobre
código sano: la nota va a CLIENTE-1b. Detalle en
`REPRODUCCION-PRUEBAS-1-2026-10-25.md`.
**Cola MARIA, aceptada e integrada, sin publicar:** MARIA-7/8
(`1fa0b6e`), VALOR-1b y MARIA-9 (`9f787f6`), y **SEPARADORES-1 y VALOR-1c
2026-10-25 07:05 UTC** sobre `a099655`: el flete «3.480» ya no sale 3,48, lo
ambiguo se pregunta, Generar frena un seguro calculado con otras cuentas.
D19 (b). Sigue SEPARADORES-1b. Detalle en
`REPRODUCCION-SEPARADORES-1-VALOR-1c-2026-10-25.md`.

**Rojo conocido de EXCEL-2, ya publicado:** `test_excel2.py::test_ocho_libros…`
falla siempre en la máquina de la PM (4 núcleos), también en la base: una
subida normal detrás de ocho libros de ~10 MiB espera en la fila de 2 hilos y
pasa el tope de 30 s. Pendiente de Emi: si se prioriza.

**Desde el 2026-10-24, tarde:** Codex deja CDI (Emi). Dos Devs nuevas en
Claude («Quién hace qué»). Ese día Emi y el despachante cargaron en el MARIA
el TXT de una factura real después de doce correcciones a mano: son la
Fase 1b del roadmap nuevo a tres meses (`ROADMAP.md`, aprobado por Emi el 2026-10-24). Pendiente de Emi: el esfuerzo en los dos chats
nuevos (el `/autocompact 200k` ya está: los dos marcan 200k), el packing list y los códigos de destino que manda el despachante.

**Publicación del 2026-10-24 10:00 ARG (`648cd2f`):** completada; cierre en `CIERRE-RETOMA-2026-10-24.md`.

**EXCEL-2 revisada y aceptada en su alcance funcional sobre `dddcf6d`**
(producto `be17e1b`), PR #5 lista para revisión (ya no borrador), SIN fusionar ni publicar. Suite local
completa: **1731 passed, 102 skipped, 2 xfailed**, 250.01 s, exit0; CI final
40017165638 tests y e2e-maria success. PM y QA independientes verificaron
origen combinado, límites, concurrencia real y nueve sintéticos iguales a
base648. 38 mutaciones históricas detectadas por motivo correcto; 2 sin evaluar
por timeout y 2 recetas obsoletas, NO 42/42. Nuevos negativos XML/subítems
se registran aparte. Cerca del tope de estilos: 499900 xf añadidos, 200,
9.18 s, RSS familiar 460140544 bytes. No es garantía universal de recursos.
Margen de concurrencia limitado (23.29 s frente a timeout30 s). Diferencia
con instrumentación de cobertura diagnosticada y anotada en DECISIONS;
no se omitieron tests ni se cambió timeout. No repetir puertas verdes sin
cambio nuevo. Informe `QA-EXCEL2-REENTREGA-2026-10-23.md` y cierre24.

La autorización anterior cubría producto166/main648. Para publicar EXCEL-2
nuevo hace falta autorización específica de Emi para HEADdddcf6d; no reutilizar
el permiso anterior. GUARDAR-2 sigue separado/D32(b), sin cobro ni migración.
Su preparación requiere Postgres local descartable y negativos de dueño;
Docker no estaba iniciado y no había binarios Postgres al revisar. No se
instaló ni arrancó ningún servicio. Fase1 no se cierra sin prueba real de
Emi/despachante en Kit.

Observación de arranque: log de métricas informa falta api_logs.owner_username;
el modelo ya estaba igual en a9b03cf. Queda por clasificar con fuentes locales,
sin leer ni migrar DB de producción. No se arregló de paso ni se incorporaron
registros, clientes o credenciales. Detalle en cierre24.

**Historial de retoma, superado por el estado de arriba:** Emi autorizó publicar la candidata. PR #4 fusionado
tras CI tests y e2e-maria verdes; main ahora `648cd2f` y su producto es
idéntico a `166395f` (diff comprobado). **Railway todavía no confirmado:**
su UI conserva ACTIVE `a9b03cf`, la salud pública responde ok y el JS servido
aún era anterior a las 09:00 ARG. Fuente main/autodeploy correctos, pero
Railway informa incidente y colas de despliegue. No repetir deploys ni
afirmar que el sitio ya se actualizó. La autorización sigue vigente para
terminar esta misma publicación, sin pedir otro «dale».
Detalle: `PUBLICACION-FASE1-2026-10-21.md`.

**Continuación activa:** EXCEL-2 `c2f8063` devuelta aunque 93 focales verdes:
una referencia XML de celda con comillas simples evade el tope de 256
columnas. PM reprodujo con una celda; devolución corregida localmente en
`04e1d0`, rama `codex/excel2-xml-quotes`, preservada en el repo de trabajo.
PM repitió reproducción verde y QA independiente aprobó 32 focales y checks
propios. Guarda XML satisfactoria; **EXCEL-2 completa sigue sin aceptar**:
falta integrar aisladamente con main y verificar suite/CI, memoria/concurrencia
y criterios históricos. `QA-EXCEL2-XML-2026-10-22.md` conserva los límites
de lo medido. No entró en PR #4. GUARDAR-2 sigue separado; no adelantar cobro.

**Último veredicto de EXCEL-2, manda sobre el párrafo anterior:** integración
local `d448033` sobre main648cd2f, rama `codex/excel2-integration-648`,
**devuelta**. Dev informó 356 focales y 15 JS verdes, pero PM reprodujo:
normal 400 a los 30.26 s detrás de ocho libros con XML de 10282491 bytes
(dentro de 10 MiB); y una combinada de origen con comillas simples pierde
el país en el segundo producto. La prueba existente de ocho libros usaba
una estimación incorrecta de tamaño y podía pasar por rechazo temprano.
Nueve libros sintéticos normales sí devuelven los mismos datos JSON que
la base, y 2000 combinadas dieron 200 en 0.166 s. No correr suite
larga hasta corregir los dos rojos. Consigna en PARA-DEV e informe completo
`REVISION-EXCEL2-INTEGRADA-2026-10-22.md`. Subagentes de implementación
interrumpidos por límite de uso; PM completó QA y dejó devolución. No
afirmar implementación ni negativos terminados; rama local preservada.

**Verificación previa al merge (histórica):** candidato `166395f` (pesos + DOC-1 +
compatibilidad Excel), rama `codex/phase1-form-default-compat`, preservada en
el repo de trabajo. Suite completa en entorno limpio: **1612 passed, 102
skipped, 2 xfailed**, cobertura 50.75 %, salida 0; chequeo previo aprobado.
PM revisó el cambio y reprodujo el rojo previo y ocho focales verdes. La
primera combinación `8b19662` había fallado cuatro casos: FastAPI nuevo
interpretaba `use_mapping` omitido como False. Se corrigió sin cambiar requisitos.
CUA sobre esa combinación llegó a descarga, controles y persistencia con datos
sintéticos. **No publicado ni listo para declarar MVP terminado**: falta la
puerta oficial de CI sobre el SHA final y la prueba real de Emi/despachante.
Evidencia completa en `VERIFICACION-CANDIDATO-2026-10-21.md`.
Siguiente cola: revisión separada EXCEL-2 y GUARDAR-2; no adelantar cobro.
Los párrafos históricos de devolución anteriores no reabren los defectos
de peso/DOC-1 ya corregidos. El candidato nuevo sigue local; el permiso
anterior cubrió las tres ramas/PR existentes, no publicar a main.

**Producto:** `Memu007/CDI-vuce-` (privado desde el 2026-10-06).
**En GitHub:** `main` = `648cd2f` (PR #4, 2026-10-22). **Último activo confirmado
en Railway:** `a9b03cf` (2026-10-07, GUARDAR-1); despliegue nuevo pendiente,
`cdi-production.up.railway.app`. Railway publica cada push a `main` sin
esperar los tests.
**En producción:** la usa sólo Emi, con facturas reales (Emi, 2026-10-07).
**Rama PM histórica:** `claude/practical-shannon-szpwkn` (`99f3625`); retoma
en `codex/pm-retoma-txt`. La rama histórica contiene lo aceptado y sin publicar
(incluye los 25 commits de `e8344d0`, ADMIN-1, ADMIN-2 y MARIA-2). **Ramas de las
Devs:** `claude/dev1-tecnica` y `claude/dev2-maria`.
**Plan:** `ROADMAP.md`, con el orden de Emi del 2026-10-07: primero el TXT,
después el cobro, la seguridad al final y exhaustiva. Ningún estudio entra
antes de cerrar la Fase 3.

## Para Emi

0. **Retoma autorizada por Emi, 2026-10-19:** pidió actuar como PM con
   subagentes y continuar el plan. Trabajo actual en `codex/pm-retoma-txt`
   desde `99f3625`; `main` sigue en `a9b03cf`. Las sesiones y rutinas de
   Claude de la tabla siguiente son históricas: Codex no tiene las
   herramientas `update_trigger`, `get_session` ni el consejero Fable; no
   se afirma que se reactivaron. Se trabaja con subagentes locales por esta
   solicitud, sin nuevas automatizaciones ni publicación.
   - **MARIA-5d:** revisión independiente sobre `d22ff1a`: 65 focales y 68
     de generador/subítems verdes; tres variantes inequívocas de peso bruto
     unitario fallan por HTTP local (3 kg / 10 unidades devuelve 0,3 kg por
     unidad). PM reprodujo los tres rojos. Devolución y tarea cerrada en
     `PARA-DEV-2.md`, antes de aceptar o publicar.
   - **Dev 1:** Git conserva dos candidatos hermanos sobre `1cdfe49`:
     EXCEL-2 en `c2f8063` y GUARDAR-2 en `2d930c5`. `dfb6d24` preserva
     trabajo, no es una entrega única. El informe de su rama sigue viejo;
     no se aceptan piezas por los verdes de GUARDAR-1. D32 ya es (b).
   - **DOC-1 autorizada por Emi el 2026-10-19:** eligió bloquear el TXT
     incorrecto antes que sumar exportación completa. Consigna en
     `PARA-DEV-2.md`; implementación aislada en `codex/doc1-block-invalid-pdf`
     desde `1469102`, con subagentes backend y UI. Clasificación documental,
     rechazo EC* por importación y prevención de arrastre A→B. Va antes de
     ORG-1. La publicación sigue esperando revisión y autorización por SHA.
   - **Incidente PDF/TXT:** la mezcla entre documentos sigue sin demostrar.
     Se confirmó con datos sintéticos que la lectura pierde la
     clasificación de despacho/EC02 y que la v2 usa la ruta de importación.
     La generación de exportación sigue fuera del alcance vigente
     (`DECISIONS.md`, pendiente v1/export). DOC-1 bloquea la salida errónea;
     no amplía a exportación completa. Ningún PDF/TXT privado se
     incorpora al repositorio.
   - **Entorno:** focales en Python 3.12 con paquetes instalados y SQLite
     temporal, no un entorno limpio desde `requirements.txt`. Son revisión
     parcial, no sustituyen suite, pantallas, Postgres ni prueba en el Kit.

1. **Segunda publicación, hecha:** `6ea8ca9`, 2026-10-07 19:58 UTC («dale
   6ea8ca9» de Emi). Emi genera un TXT con una factura real, lo descarga
   enseguida y mira: fecha DD/MM/AAAA, CUIT sin guiones, IVA adicional
   `NO_VALIDA`, `CARTUSO` 2, banco y empresa de digitalización. Ahora pide
   fecha de emisión, moneda, incoterm, CUIT válido y estado si el origen es
   argentino: un error que pide eso no es una falla. Guardar con la SIM
   completa sigue dando error hasta GUARDAR-1.
1a. **Sin volumen** (Emi, 2026-10-07): cada publicación o reinicio borra los
   TXT generados y el historial de NCM aprendido; las operaciones quedan en
   la base. Descargar el TXT apenas se genera. Lo arregla DISCO-1 (Fase 3).
2. **Rotar las claves de Gemini y revocar la de Anthropic** (G0). Gemini: en
   Google AI Studio borrar las que aparecieron, crear una nueva y ponerla sólo
   en Railway; mirar la facturación. Anthropic (2026-10-24): hay una clave
   real en `scripts/utils/cambiar_ai.sh:62` de `main` y en el historial desde
   `32e4282`; revocarla en la consola de Anthropic. Después, pieza chica para
   sacar el archivo (el historial queda; lo que protege es revocar).
3. **Despachante:** recordarle los archivos reales (favor 1). Ya respondió
   todas las preguntas.
4. **Catálogo NCM:** Emi trajo el nomenclador vigente (2026-10-07). Lo
   carga la Dev 2 en CATALOGO-NCM-1. Una línea de Emi: ¿lo bajó de
   `arca.gob.ar`?
5. **Hasta publicar MARIA-1a: revisar el país de origen de cada TXT** antes
   de mandárselo al despachante. El código publicado corta el país a dos
   letras: si la lectura devuelve «CHN» o «China», sale Suiza.
6. **Límite de uso de la cuenta:** lo tocó dos veces el 2026-10-07: entre
   las ~02:05 y las 03:40 UTC, y entre las ~18:34 y las 18:50 UTC (las dos
   Devs quedaron paradas; la PM las despertó a las 18:56). Por la regla de
   Emi (`DECISIONS.md`), **hoy se compacta desde el 30 % las Devs y el 40 %
   las PMs**; mañana vuelve a 60 y 50.
7. **No pedirle a ningún asistente cambios sobre `main`:** desde el
   2026-10-07 `main` tiene las reglas nuevas, pero cada push publica.

## Quién hace qué

Desde el 2026-10-24 (Emi: Codex deja CDI; dos Devs nuevas en Claude).

| Rol | Sesión | Rutina | Rama | Esfuerzo |
|---|---|---|---|---|
| PM principal | session_01B7FVQspcEHF7PqNv797wNM | trig_01TvMmGfSLDfbcJrf66ZZ7YK (min 55) | claude/practical-shannon-szpwkn | — |
| Dev MARIA (Dev 2) | session_01C8gCBjvn36wnYC6qG2Sixi | trig_01WmrC3ALqBXkD9UBv6dFGbP (min 35) | claude/dev-maria | alto |
| Dev técnica (Dev 1) | session_018yxeKHYQKFA3qJ2WJmQru7 | trig_011UpBfwEu9TUzoNUrviqoP5 (min 15) | claude/dev-tecnica | medio |

Canales: Dev MARIA lee `PARA-DEV-2.md` y contesta en `PARA-PM-2.md`; Dev
técnica lee `PARA-DEV.md` y contesta en `PARA-PM.md`. **Sin PM visual:** la
PM principal revisa a las dos. Timbres por `send_message`, `priority` `next`.

Sesiones viejas, apagadas (historia): Dev 1 session_01VV5RVDA64AuzLaPBDnwH39
(trig_016zR6giZB8Mq9ZdfaerVh2D) y Dev 2 session_01JssJQ6CQvEBZ7yjJp3hHQx
(trig_019ehV8P48FzbNwYQGZjgYcW), con ramas `claude/dev1-tecnica` y
`claude/dev2-maria`; las ramas `codex/*`.

Archivos abiertos por Dev:
- Dev 1 (EXCEL-1): `proyecto_maria/main.py` (las cargas por Excel).
- Dev 2 (MARIA-3): `proyecto_maria/core/maria_generator.py` y las pantallas
  v2 de revisión.

## En curso

- **Dev 1:** GUARDAR-1 (Emi dijo que sí; está en producción). Después, la
  devolución de EXCEL-2 (devuelta sobre `3e6e63e` a las 19:45 UTC por seis
  puntos; tres rompen: una combinada gigante traba la lectura, una
  combinada con texto duplica el FOB, el tope de estilos no protege la
  memoria; D27 (a)). Después, COBRO-MP-1, en pausa en `18a1850`.
- **Dev 2:** MARIA-5, CATALOGO-NCM-1 y SUBITEMS-1 aceptadas sobre `df4de22` e integradas (`0e57f70`). Ahora MARIA-5d: devolución del 2026-10-19 por variantes «unit (kg)»; va antes de la próxima publicación. Después ORG-1 (Fase 2); MARIA-6 espera los archivos del despachante.
- **Aceptadas e integradas el 2026-10-07 después del ensayo** (sin publicar):
  RENDIMIENTO-1 y 1b (`ec3d793`), MARIA-1a, 2b, 1c, 4, 3 y 1d (`9679e21`).
  Suite sobre la rama integrada (`7b42556`, venv armado sólo con el
  `requirements.txt` nuevo): `1067 passed, 102 skipped, 0 failed`. Al
  integrar, dos pruebas de MARIA armaban su PDF con PyPDF2, que salió en
  RENDIMIENTO-1: pasan a `pypdf` (`7b42556`).
- **Integradas a las 15:20 UTC:** EXCEL-1 y MARIA-1b con su devolución (`beea9eb`). Suite sobre `6ea8ca9`: `1224 passed, 102 skipped, 1 xfailed`.
- **Aceptadas el 2026-10-07 e integradas:** ADMIN-1 (`ac25dbc`), MARIA-2
  (`65ea6f3`) y ADMIN-2 (`f9f8393`). Suite sobre `f9f8393`, que tiene el
  mismo producto y las mismas pruebas que la rama de PM:
  `716 passed, 102 skipped`.
- **Publicación de ensayo:** dos candidatos. (a) `cb8f509`, el código de
  `e8344d0` tal cual; (b) la cabeza de la rama de PM, que además cierra el
  admin, borra el atajo que activaba una suscripción sin pagar y saca los
  productos inventados, pero pide `ADMIN_USERNAMES`. La PM
  recomienda (b) si la variable está; si no, (a). Un subagente Opus alto
  atacó `81bcaba` y repitió sobre `7f1dd2c` (con ADMIN-2): se puede publicar
  si Emi hace antes la lista de arriba. Suite sobre `321f34b` (04:05 UTC):
  `716 passed, 102 skipped`; de ahí a la cabeza sólo cambian documentos. Si
  entra producto antes del «dale», se corre otra vez sobre el SHA exacto.
- **Despachante:** respondió las seis preguntas y las dos cortas el
  2026-10-06 (`PREGUNTAS-DESPACHANTE.md`): la empresa de digitalización se
  elige por operación (Modoc = `PSAD06`, Lakaut = `PSAD01`) y la reducción del
  IVA adicional es una «ventaja» que elige él en el Kit, no va en el TXT.
  Faltan los archivos reales y, al cerrar la Fase 1, la prueba en su Kit.

## Puertas para cobrarle a un estudio

| Puerta | Estado | Qué falta | Se cierra en |
|---|---|---|---|
| G0 · Secretos | 🔴 | Rotar las claves de Gemini | Emi, esta semana |
| G1 · Configuración | 🟢 | G1.1 a G1.5 cortan. G1.6 y G1.7 sin medir | — |
| G2 · Imagen real | 🟢 | Cerrada el 2026-09-17 | — |
| G3 · Aislamiento | 🟡 | La fuga de MARIA.TXT, cerrada en producción con el ensayo (sin cuentas ajenas: nadie vio facturas de Emi). Admin cerrado en la rama (ADMIN-1 y ADMIN-2). Abiertos: sesiones que reviven, límite de intentos burlable, prueba de aislamiento parcial | Fase 3 |
| G4 · Producto (MARIA) | 🔴 | Origen mal leído, estado e IVA adicional fijos, peso por unidad, avisos tarde, gastos FOB sin cablear, banco, identificadores. Sin productos inventados (MARIA-2) | Fase 1 y la prueba en el Kit |
| G5 · Pruebas | 🟢 | `1526 passed, 102 skipped, 2 xfailed, 0 failed` y e2e OK en la rama integrada (`df4de22` = `0e57f70` sin documentos, 2026-10-07) | — |
| G6 · Volver atrás | 🟡 | Esquema probado en local; falta la copia de la base | Fase 3 (y el ensayo lo ensaya) |
| G7 · Cobro | 🔴 | El corte por impago cubre 2 funciones; cancelar no cancela en Mercado Pago; aviso de pago sin firma; doble suscripción; invitaciones | Fase 2 |
| G8 · Piloto | ⚪ | Tres estudios presentan de verdad un MARIA de CDI | Fase 4 |

## Publicado

Una línea por publicación: fecha, SHA y qué verificó Emi. Las anteriores al
2026-10-24 (`a771693`, `5cb03ab`, `6ea8ca9`, `a9b03cf`) están en la historia
de Git de este archivo y en sus `REPRODUCCION-*`.

- `dddcf6d` (2026-10-24 18:40 UTC): EXCEL-2, «dale dddcf6d». CI verde. Emi
  probó el Excel en el sitio y anda.
- `8b45207` (2026-10-24 20:33 UTC): EXCEL-3 + CLIENTE-1, «dale 8b45207».
  Avance directo de `dddcf6d`. Falta lo que verifica Emi.

## Reglas

Congeladas desde el 2026-10-06 hasta el **2026-10-27** (`DECISIONS.md`,
«Reglas en un solo lugar»), salvo que algo se rompa. Ese día la PM revisa con
`medir.py` y las mediciones si alguna regla molesta.

## Método

Al día con `CAMBIOS.md` del Second Brain (`Memu007/ynerasecondbrain`) hasta
**2026-10-06 (noche)**, commit `faa8a3a`.

## Sumar una Dev

Cuando haya dos colas que no toquen los mismos archivos (por ejemplo, cobro y
sesión por un lado; pantallas y archivo MARIA por el otro):

1. Medir antes con `medir.py`: una sesión más agrega traspasos.
2. Copiar del Second Brain `plantilla/docs/pm/PARA-DEV-2.md` y `PARA-PM-2.md`.
   Si hay mucha cola visual, también `ARRANQUE-PM-VISUAL.md`, `VISUAL.md` y
   `ENTRE-PMS.md`, con su PM visual.
3. En `medir.py`, agregar `"dev2": "<su rama>"` a `RAMAS`.
4. Abrir la sesión, crearle su rutina, anotar todo en «Quién hace qué» y
   pasarle los ids de la rutina de su PM.

## Última vuelta

2026-10-25 07:56 UTC: sin entregas nuevas. MARIA en SEPARADORES-1b (`db39de0`, sin informe; contexto 142k); la técnica en CLIENTE-1c (`1955cac`, corriendo sabotajes, sin informe; 115k). CI verde sobre `a2fdabd`.

2026-10-25 07:05 UTC: SEPARADORES-1 y VALOR-1c (`a099655`, informe `4548644`) **aceptadas** e integradas con `merge`, sin publicar: suite `2280 passed, 102 skipped, 2 xfailed`, sabotajes 26 y 17 en rojo, 301 focales, 200.000 montos sin error y un adversario Opus alto (TXT igual byte a byte en 56 pedidos, ningún 500 nuevo). D19 (b). Sigue **SEPARADORES-1b** (D19 b y «separador y tres dígitos» mal agrupados, en la factura y en la pantalla), después SUFIJOS-1. Contexto de las tres sesiones bajo 120k; la técnica, en CLIENTE-1c sin informe.

## Medición

`archivo/MEDICION-SUBAGENTES.md` y `archivo/MEDICION-CONSEJERO.md`.

## /compact conservar de la PM principal

/compact conservar: Soy la PM principal de CDI (session_01B7FVQspcEHF7PqNv797wNM, rutina trig_01TvMmGfSLDfbcJrf66ZZ7YK min 55). Producto Memu007/CDI-vuce-, clon /home/user/cdi-vuce-, mi rama claude/practical-shannon-szpwkn (nunca main; cada push a main publica). main = 8b45207 (EXCEL-3 + CLIENTE-1, publicada 24/10 con «dale 8b45207»; falta que Emi la pruebe; volver a dddcf6d sólo con su ok). Dev MARIA (session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, alto): MARIA-7/8, VALOR-1b, MARIA-9, SEPARADORES-1 y VALOR-1c aceptadas e integradas (las dos últimas sobre a099655, sin publicar; D18 b, D19 b); ahora SEPARADORES-1b (D19 b: montoDelPedido manda el texto y el servidor lo rechaza; familia «separador + tres dígitos sin miles bien formados» ambigua en _monto_factura y montos_ar.js, no en _numero_factura), después SUFIJOS-1 (Fase 1c, VUCE_MODE=fake en pruebas). Dev técnica (session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica): EXCEL-3d 5468581 con devolución EXCEL-3e (H1: flete/descuento con medidas «/», «-», 0 bajo especificación combinada entra como producto sin aviso, causa con_medidas por texto + descripcion_propia vacía, main.py:4973/4945/4984/5071; piso 31c9b5a; no por lista); D20 a, D21 b y D22 b van en EXCEL-3f (lista + familia H4 sólo aviso); E1 descartado contra e08b4c4. ESTUDIO-1 aceptada sobre 5468581 (código c992715) con ESTUDIO-1b obligatoria antes de publicarla (D23 b: el perfil cuenta como último usado; estudio_id «null» no cae al perfil; nombres invisibles). No integré: 5468581 trae EXCEL-3d con H1; EXCEL-3d, CLIENTE-1b y ESTUDIO-1 se integran juntas al aceptar EXCEL-3e. Orden: EXCEL-3e, CLIENTE-1c (D15 b, D16 b), ESTUDIO-1b, EXCEL-3f, GUARDAR-2. PRUEBAS-1 + PA-1b integradas (merge 4f00636). Pendiente de la PM: revisar SEPARADORES-1b y EXCEL-3e cuando lleguen; al aceptar EXCEL-3e, merge --no-ff de claude/dev-tecnica. Para Emi: el límite de gasto mensual de la cuenta frenó a las tres sesiones el 25/10 de ~03:30 a 04:50 UTC (si se repite, decide él si lo sube); orden de prioridad de Argon (REPRODUCCION-ARGON-2026-10-24.md; nada al roadmap sin su «dale»); probar 8b45207; preguntas al despachante (las cuatro nuevas de PREGUNTAS-DESPACHANTE.md); packing list; revocar la clave de Anthropic de cambiar_ai.sh y rotar Gemini; 4.1 y 6.1 de producción; el script de fechas de CLIENTE-1b con --base deja la clave de la base en el historial (pasarla por variable). Roadmap en ROADMAP.md; TXT y proforma reales sólo en el scratchpad. Reglas de Emi: nada fuera del roadmap; Devs hasta alto, sin Fable; consejero sólo mío; castellano llano; consultas de 9 a 21 ARG; publicar sólo con «dale <SHA>» de día; usar date -u.

