# NOW — CDI

Actualizado: 2026-10-07. Estado vigente; la historia está en Git.

**Producto:** `Memu007/CDI-vuce-` (privado desde el 2026-10-06).
**Publicado:** `main` = `5cb03ab` (2026-10-07, publicación de ensayo) en Railway,
`cdi-production.up.railway.app`. Railway publica cada push a `main` sin
esperar los tests.
**En producción:** la usa sólo Emi, con facturas reales (Emi, 2026-10-07).
**Rama de PM:** `claude/practical-shannon-szpwkn`: lo aceptado y sin publicar
(incluye los 25 commits de `e8344d0`, ADMIN-1, ADMIN-2 y MARIA-2). **Ramas de las
Devs:** `claude/dev1-tecnica` y `claude/dev2-maria`.
**Plan:** `ROADMAP.md`, con el orden de Emi del 2026-10-07: primero el TXT,
después el cobro, la seguridad al final y exhaustiva. Ningún estudio entra
antes de cerrar la Fase 3.

## Para Emi

1. **Segunda publicación, candidato `6ea8ca9`** (atacado en
   `REPRODUCCION-PUBLICACION-2-2026-10-07.md`): arregla el país de origen,
   suma los controles antes de generar, el Excel y lo del despachante. Falta
   que Emi escriba «dale 6ea8ca9»: su «dale a todo» (~15:27 ARG) lo frenó el
   sistema de permisos de la sesión, que pide la autorización explícita.
   Reventa confirmada (el IVA adicional pasa a `NO_VALIDA`).
   Después de publicar: Emi genera un TXT con una factura real y lo revisa.
   La línea «Billing cron» no aparece si nadie pasa a impago.
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
6. **Límite de uso de la cuenta:** el 2026-10-07 entre las ~02:05 y las
   03:40 UTC las Devs quedaron paradas porque la cuenta llegó a su límite de
   5 horas («You've hit your session limit»). Lo más barato para que no se
   repita: pegar el `/compact` de cada Dev apenas se pueda (están en ~38 % y
   ~41 %; cada paso relee todo el contexto). Si vuelve a pasar, Emi decide
   entre aceptar las pausas o bajar el ritmo.
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

- **Dev 1:** EXCEL-2 entregada (`3e6e63e`, D27), en revisión: rojo antes
  (`43 failed, 8 passed`) y suite (`1277 passed, 102 skipped, 3 xfailed`)
  hechos; falta el subagente. Ahora GUARDAR-1 (Emi dijo que sí). COBRO-MP-1,
  en pausa en `83b4ec1` con D28 a D31 contestadas (`074a50b`).
- **Dev 2:** devolución de MARIA-5 (dos pesos para una línea, filas que desaparecen, guarda del peso, subítems, grupos, una sola cuenta). Sigue: CATALOGO-NCM-1, SUBITEMS-1 (Emi: sus facturas traen subítems) y MARIA-6 cuando lleguen los archivos reales del despachante.
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
| G5 · Pruebas | 🟢 | `1224 passed, 102 skipped, 1 xfailed, 0 failed` en la rama integrada (`6ea8ca9`, 2026-10-07) | — |
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

2026-10-07 18:45 UTC: Emi contestó «dale a todo» y que la suscripción está en
Railway. GUARDAR-1 entra (Dev 1, antes que COBRO-MP-1); reventa confirmada;
SUBITEMS-1 entra (Dev 2). El push de `6ea8ca9` a `main` lo frenó el sistema
de permisos: falta «dale 6ea8ca9» escrito. EXCEL-2: falta el subagente
(después de las 18:50 UTC, cuando se renueva el límite de 5 horas). Dev 1
compactada (11 %).

## Medición

`archivo/MEDICION-SUBAGENTES.md` y `archivo/MEDICION-CONSEJERO.md`.
