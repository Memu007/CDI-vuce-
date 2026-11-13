# AGENTS.md — la puerta de entrada de cualquier asistente

Vale para cualquier asistente que tome este repositorio: Claude Code, Cursor,
Antigravity, Cascade/Windsurf, Devin, Codex, Copilot o Aider. Las reglas viven
en los documentos enlazados y no se copian. Una regla escrita en dos lugares
envejece en uno.

**Reglas congeladas** desde el 2026-10-06 (`docs/pm/NOW.md`, «Reglas»). Sólo
cambian antes si algo se rompe, y siempre con una decisión anotada en
`docs/pm/DECISIONS.md`.

## Lo que vale para todos, siempre

1. **`main` es de Emi.** Railway publica cada push a `main` sin esperar los
   tests: empujar a `main` es publicar. Todo trabajo va a una rama. A `main`
   se llega sólo con el «dale» de Emi para ese SHA (`docs/pm/ONBOARDING-PM.md`,
   «Publicar»). Nunca `git push --force`.
2. **Nada sin plan aprobado.** Ninguna tarea nueva, arreglo «de paso» ni
   refactor sin que esté en `docs/pm/PARA-DEV.md` o lo pida Emi en ese
   momento. Si ves algo que conviene hacer, proponelo con su costo y su
   riesgo; no lo hagas.
3. **Los límites que no se negocian** tienen una sola copia:
   `docs/pm/ONBOARDING-PM.md`, «Límites que no se negocian». Incluyen: ningún
   secreto ni dato real de clientes en el repositorio, nada contra producción
   ni contra terceros desde una prueba y nada publicado sin «dale».
4. **El estado vigente** (qué está hecho, qué sigue, qué espera a Emi) está en
   `docs/pm/NOW.md`. Las decisiones tomadas, en `docs/pm/DECISIONS.md`.
   `HANDOFF.md` describe cómo funciona el producto, pero está desactualizado
   desde julio: ante una contradicción, mandan Git y `NOW.md`.

## Hablar con Emi

Emi es dueño del producto y no programa. Lo usa desde el teléfono.

- **La conclusión, arriba y en castellano llano.** Cada término técnico se
  traduce la primera vez que aparece. Después: qué cambió, qué probar y qué
  riesgo hay.
- **La versión chica, primero.** Si un plan tiene más de cinco o seis pasos,
  se propone primero el mínimo útil.
- **Las opciones, con lo que cuestan en el negocio** («más rápido pero…»), y
  con una recomendación.
- **Sin dar la razón para quedar bien.** Si un pedido choca con la seguridad,
  los datos de los clientes, el cobro o una decisión tomada, se dice antes de
  hacerlo, con una alternativa.
- **Lo que toca clientes, CUIT, el archivo MARIA, PDFs, pagos o publicación**
  lleva una recomendación clara y no se asume.
- Entre reglas, gana lo que Emi pida en el mensaje actual, salvo que choque con
  un límite que no se negocia: eso se le dice.

## Según tu rol

**PM principal.** Leé completo `docs/pm/ONBOARDING-PM.md`. Hay una sola PM
principal, la sesión anotada en `NOW.md`, «Quién hace qué».

**PM visual** (si se suma). Leé `docs/pm/ARRANQUE-PM-VISUAL.md` y hacé lo que
dice.

**Dev del canal.** Leé `CLAUDE.md` y, una vez, `docs/pm/ONBOARDING-DEV.md`.
Después, tu canal: la Dev 1 lee `docs/pm/PARA-DEV.md` y responde en
`docs/pm/PARA-PM.md`; la Dev N, `PARA-DEV-N.md` y `PARA-PM-N.md` («Estructura» en
`docs/pm/ONBOARDING-PM.md`).

**Otro asistente en un chat suelto con Emi** (Cursor, Copilot, etc., fuera
del canal):
- Antes de tocar código, leé `CLAUDE.md`. Sus reglas de trabajo valen para
  vos también.
- Trabajá en una rama. Al terminar, dejá una a tres líneas en `CHANGELOG.md` y
  avisale a Emi qué rama revisar.
- Si la tarea no es trivial, podés responder como un equipo de especialistas:
  PM, Tech Lead, Backend, Frontend, QA y Seguridad. Consultá sólo los roles
  que sirvan y nombralos entre corchetes al principio, por ejemplo
  `[PM + Backend + QA]`. Las sesiones PM y Dev no lo usan: tienen subagentes
  de verdad (`docs/pm/ONBOARDING-PM.md`, «Subagentes»).

**Auditoría externa.** Lee, cuestiona y propone. Su informe no cambia
prioridad, alcance ni aceptación por sí solo: la PM decide qué adopta.

## Lo único que este archivo afirma

- Si la entrega pendiente vive en una rama de Dev sin integrar, `PARA-PM.md` se
  lee **desde esa rama**.
- Si un documento y Git se contradicen sobre qué está implementado, manda Git y
  se corrige el documento.
- **No son reglas:** `.specify/`, `.windsurf/plans/`, `.devin/plans/`, `plans/`,
  `docs/archive/` y los informes viejos de `docs/`. Son notas o historia.
- Los archivos de cada herramienta (`.cursor/rules/`, `.github/`,
  `CONVENTIONS.md`, `.devin/rules/`, `.agent/rules/`, `.windsurf/rules/`) sólo
  apuntan acá. No llevan reglas propias.

## Eficiencia de chats

Vale para PMs y Devs; esta es su única copia.

- **Compactar sola:** cada sesión tiene `/autocompact 200k` (lo escribe
  Emi una vez en cada chat; vive en el contenedor) y se compacta sola
  alrededor de ~150k, también en medio de una corrida (lo que corre en
  segundo plano sigue). Con menos de ~180k se compacta sin parar y gasta
  más. Lo que conserva lo dice `# Compact instructions` en `CLAUDE.md`: por
  eso cada sesión deja **siempre al día** su `/compact conservar: …` (Dev 1,
  al final de `docs/pm/PARA-PM.md`; Dev N, al final de `docs/pm/PARA-PM-N.md`;
  PM principal, en `NOW.md`).
- **Control:** en cada vuelta la PM principal mira cada sesión con
  `get_session`. Sólo si una muestra un `max_tokens` distinto de 200000
  (contenedor nuevo) o `used_tokens` pasa ~170k, le pasa a Emi el
  `/compact conservar: …` de esa sesión y le pide `/autocompact 200k` en
  ese chat. `/compact` no viaja por mensaje entre sesiones. Emi puede
  compactar a mano cuando quiera.
- **Antes de compactar o cambiar de chat,** el estado vigente queda subido al
  repositorio.
