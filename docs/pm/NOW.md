# NOW — CDI

Actualizado: 2026-10-20. Estado vigente; la historia está en Git.

**Producto:** `Memu007/CDI-vuce-` (privado desde el 2026-10-06).
**Publicado:** `main` = `a9b03cf` (2026-10-07 21:35 UTC, tercera publicación: GUARDAR-1) en Railway,
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
1a. **Tercera publicación, hecha:** `a9b03cf`, 2026-10-07 21:35 UTC («dale
   a9b03cf» de Emi). Emi espera unos minutos y guarda una operación con un
   producto con la SIM completa: tiene que guardar sin error.
1b. **Sin volumen** (Emi, 2026-10-07): cada publicación o reinicio borra los
   TXT generados y el historial de NCM aprendido; las operaciones quedan en
   la base. Descargar el TXT apenas se genera. Lo arregla DISCO-1 (Fase 3).
2. **Rotar las claves de Gemini** (G0). En Google AI Studio: borrar las que
   aparecieron, crear una nueva y ponerla sólo en Railway. Mirar la
   facturación de Google.
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

| Rol | Sesión | Rutina | Rama |
|---|---|---|---|
| PM principal | session_01B7FVQspcEHF7PqNv797wNM | trig_01TvMmGfSLDfbcJrf66ZZ7YK (min 55) | claude/practical-shannon-szpwkn |
| Dev 1 | session_01VV5RVDA64AuzLaPBDnwH39 | trig_016zR6giZB8Mq9ZdfaerVh2D (min 15) | claude/dev1-tecnica |
| Dev 2 | session_01JssJQ6CQvEBZ7yjJp3hHQx | trig_019ehV8P48FzbNwYQGZjgYcW (min 35) | claude/dev2-maria |

**Sin PM visual:** la PM principal revisa a las dos Devs, y las dos la
despiertan con su rutina (donde los comandos dicen «PM visual», acá es la
principal).

La sesión vieja «CDI — Dev 1» (session_01F66wsdGqhMMEiCLTopVVXe, rutina
trig_01XijDAiEX4aBm8dfv9ZD6C1) se abrió sobre la copia vieja (`Memu007/CDI`):
pausada, no trabaja acá.

Esfuerzo (Emi, 2026-10-07): PM principal extra; las Devs, como máximo alto,
también sus subagentes (Emi confirmó las dos sesiones en alto). Ningún subagente usa Fable. El consejero es sólo de
la PM principal.

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

- `a771693` (2026-07-18), anterior a este método. Cada publicación nueva: una
  línea con fecha, SHA y qué verificó Emi.
- `5cb03ab` (2026-10-07 12:53 UTC), publicación de ensayo: el producto atacado
  en `REPRODUCCION-ENSAYO-2026-10-07.md` (ADMIN-1, ADMIN-2, MARIA-2 y los 25
  commits de `e8344d0`). Suite sobre el mismo producto (`1ad3226`):
  `716 passed, 102 skipped`. Avance directo de `a771693`, sin merge. Emi:
  hizo la lista de Railway antes del «dale»; después verificó «Billing cron» con 0
  y guardó una operación (2026-10-07, ~10:20 ARG). CI de GitHub en verde.
- `6ea8ca9` (2026-10-07 19:58 UTC), segunda publicación: MARIA-1a, 2b, 1c, 4,
  3 y 1d, RENDIMIENTO-1 y 1b, EXCEL-1 y MARIA-1b, atacado en
  `REPRODUCCION-PUBLICACION-2-2026-10-07.md`. Suite sobre el mismo SHA:
  `1224 passed, 102 skipped, 1 xfailed`. Avance directo de `5cb03ab`, sin
  merge. «dale 6ea8ca9» de Emi a las ~16:58 ARG (antes, «dale a todo», que el
  sistema de permisos no tomó). CI: pruebas en verde y `e2e-maria` en rojo. La e2e no completa la fecha de emisión que pide MARIA-3; la PM lo reprodujo y, con esa línea, pasa entero («E2E MARIA OK»). El producto está bien, la prueba quedó vieja; la arregla la Dev 1 con GUARDAR-1. Emi generó un TXT con una factura real y «se ve bien» (19:59 UTC, un minuto después del push: falta confirmar que ya corría la versión nueva; con ella el TXT dice `IVAADICIONAL1=NO_VALIDA` y `CARTUSO=2`).
- `a9b03cf` (2026-10-07 21:35 UTC), tercera publicación: GUARDAR-1, aislada
  con `cherry-pick` (`REPRODUCCION-GUARDAR-1-2026-10-07.md`), y la línea de la
  e2e de la CI. Suite sobre el mismo producto (`2621c3b`): `1247 passed, 102
  skipped, 3 xfailed`; e2e «E2E MARIA OK»; Postgres 16 `fallas: 0`. Avance
  directo de `6ea8ca9`, sin merge. CI: en curso. Falta lo que verifica Emi.

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

2026-10-19: retoma en Codex autorizada por Emi. Reconciliadas ramas y
entregas conservadas; MARIA-5d devuelta con tres rojos reproducidos por PM;
revisión de GUARDAR-2 en curso. Sin aceptación nueva ni publicación.

2026-10-19, continuación: MARIA-5d candidata `eff9dea`, 148 focales PM
verdes y 11 sabotajes Dev; suite general en curso. Borradores de revisión:
PM #1 y pesos #2, sin fusionar. Emi autorizó DOC-1; backend y UI trabajan
en una entrega separada. Las rutinas históricas de Claude siguen sin tocarse.


2026-10-07 22:45 UTC: pausa pedida por Emi hasta mañana; rutinas de CDI
apagadas y Devs avisadas (ver «Para Emi» 0).

2026-10-07 22:08 UTC: MARIA-5, CATALOGO-NCM-1 y SUBITEMS-1 aceptadas e
integradas (`0e57f70`). Antes de la próxima publicación falta MARIA-5d (el
bruto «unitario» se divide). Dev 2: MARIA-5d y después ORG-1. Dev 1:
despertada para entregar la devolución de EXCEL-2. CI de `a9b03cf`: trabada
en el apt del runner de GitHub.

## Medición

`archivo/MEDICION-SUBAGENTES.md` y `archivo/MEDICION-CONSEJERO.md`.

## Continuación 2026-10-20

- **MARIA-5d:** informe Dev `254531b` (sólo documentos) sobre el producto
  de `eff9dea`: suite completa `1570 passed, 102 skipped, 2 xfailed`,
  cobertura 50,47 %, salida 0; 148 focales PM y 11 sabotajes. No se repite.
  Falta cerrar las puertas de navegador/Kit antes de autorizar publicación.
- **DOC-1:** producto `b5b6dec`, pruebas finales `378288e`, negativos
  actualizados `10bbe35`; mismo producto Python. Suite con chequeo previo,
  `1564 passed, 102 skipped, 2 xfailed`, cobertura 50,53 %, salida 0.
  PM reprodujo 38 focales y 11 escenarios JS. CUA local, con lector y
  usuario simulados: factura A válida → revisión; despacho B → rechazo
  claro; recarga → operación vacía, sin A. No mide precisión de Gemini.
- **Devolución DOC-1, resuelta en `c2d41b4`:** el botón Deshacer de NCM conservaba un snapshot fuera
  de `CDI.state` durante diez segundos. Tras una nueva operación puede
  restaurar ítems anteriores al volver a NCM. Se requiere atarlo a la
  referencia del estado de su operación y conservar undo en la misma
  operación. Corrección integrada en `fe0a101`, con 4 escenarios undo y 11 de subida verdes; publicación pendiente.
- Ningún cambio en producción. Las ramas de revisión siguen separadas;
  datos privados y harness local de lectura no se versionan.

### Cierre de esta vuelta (2026-10-20)

DOC-1 entregada en `fe0a101`, rama local `codex/doc1-block-invalid-pdf`.
El snapshot NCM fue corregido en `c2d41b4` y probado en `637758c`:
PM repitió 4 escenarios undo y 11 de subida sobre el candidato aislado;
Dev repitió 38 focales y los 15 escenarios después de integrar. Diff Python
vacío desde `378288e`: se conserva la evidencia de suite anterior, no se
repite por JS ni se afirma que la suite Python prueba navegador.

Revisión técnica local satisfactoria; **sin publicación ni aceptación de
precisión del lector real**. Pendientes: puerta oficial completa de
navegador, instalación limpia y prueba permitida de Emi con el lector real.

El rechazo automático anterior de push quedó resuelto por autorización
explícita de Emi el 2026-10-20: «dale. y. anotalo asi. la prox. pm sabe».
Se autoriza guardar las tres ramas detalladas en `DECISIONS.md` y preparar
sus borradores de revisión. **No es autorización para publicar**: no tocar
`main` ni Railway. No pedir de nuevo permiso para este mismo guardado.

## Traspaso a la próxima PM — 2026-10-20

Leer primero este NOW, `DECISIONS.md` y
`REPRODUCCION-RETOMA-2026-10-19.md`; leer cada informe desde su propia rama.

| Rama de revisión | Entrega | Estado técnico |
|---|---|---|
| `codex/pm-retoma-txt` | Documentación de PM y autorización de guardado | Sin código de producto; retoma de `99f3625` |
| `codex/maria5d-unit-kg` | `254531b`, informe sobre producto `eff9dea` | 1570 passed, 102 skipped, 2 xfailed; 148 focales PM y 11 negativos |
| `codex/doc1-block-invalid-pdf` | `fe0a101` | 1564 passed, 102 skipped, 2 xfailed sobre el mismo Python; 38 focales y 15 escenarios JS tras integración |

**Siguiente:** verificar las cabezas remotas y los borradores, completar la
puerta oficial de navegador y el entorno limpio, integrar sólo en una rama
candidata y verificar esa combinación. La prueba CUA local tuvo lector
simulado: falta una prueba permitida con lector real; no afirmar precisión
Gemini ni aceptación en Kit. Publicar requiere el «dale» de Emi para un
SHA final probado, conforme a las reglas vigentes.

**Después:** recibir EXCEL-2 `c2f8063` y GUARDAR-2 `2d930c5` por separado
(no la punta completa de Dev 1), con sus pruebas pendientes. D32 ya es (b),
sin migración. No reabrirla ni adelantar cobro. No reactivar rutinas antiguas
ni asumir que hay sesiones de Claude trabajando.

**Alcance DOC-1:** bloquear el TXT incorrecto, no generar exportaciones
completas. No se demostró mezcla de dos PDFs: se confirmó clasificación
perdida y ruta de importación aplicada a un despacho. No usar los TXT
manuales de este chat como archivos de referencia aceptados por el Kit.
