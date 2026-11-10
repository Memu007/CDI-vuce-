---
name: revisar-entrega
description: PM. Revisar la entrega pendiente de la Dev en PARA-PM.md, reproducirla con las herramientas de PM y escribir el veredicto en PARA-DEV.md. Usalo cuando la rutina o un aviso muestren una entrega nueva.
---

# /revisar-entrega — revisar lo que entregó la Dev

Sólo PM. El método y sus porqués están en `docs/pm/ONBOARDING-PM.md`
(«Revisión y aceptación») y en `docs/pm/herramientas/LEEME.md`. Acá va sólo el orden.

## Canales

Con dos Devs hay dos canales, y cada Dev usa sólo el suyo. A la Dev 1 la
revisa la PM principal; a la Dev 2 también, mientras no haya PM visual (`NOW.md`, «Quién hace qué»). Si hay PM visual, revisa a la Dev 2 y devuelve el veredicto también en `ENTRE-PMS.md`:

| | PM escribe | la Dev contesta | rama de la Dev |
|---|---|---|---|
| Dev 1 | `PARA-DEV.md` | `PARA-PM.md` | la de `NOW.md`, «Quién hace qué» |
| Dev 2 | `PARA-DEV-2.md` | `PARA-PM-2.md` | la de `NOW.md`, «Quién hace qué» |
| Dev N | `PARA-DEV-N.md` | `PARA-PM-N.md` | la de `NOW.md`, «Quién hace qué» |

La PM escribe en su propia rama (`NOW.md`); cada Dev la trae con `merge`.
Nunca se toma una tarea ni se escribe en el canal de la otra Dev.

## 1. ¿Hay una entrega nueva?

```bash
git ls-remote origin refs/heads/<rama Dev>          # la rama está en NOW.md
git fetch -q origin +refs/heads/<rama Dev>:refs/remotes/origin/<rama Dev>
git log --oneline HEAD..origin/<rama Dev>
```

Mirá la rama de tu Dev y su canal (`PARA-PM.md` la Dev 1, `PARA-PM-N.md`
la Dev N). Si no cambió desde tu último veredicto, no hay entrega: decilo
en una línea y terminá. Revisá desde la rama de esa Dev sin integrarla: se
integra recién al aceptar (paso 4).

## 2. Leer el informe desde la rama

SHAs, lo que decidís (D1, D2…), supuestos de la Dev y los comandos copiables.
Mirá el diff fuera de `docs/pm` vos misma: `git diff <base> <SHA> --stat`.
Contra `CLAUDE.md` §6: `docs/pm/herramientas/chequeo-6.py <base> <SHA>` da
lo mismo que el informe, y cada `AVISO` está arreglado o explicado. Uno sin
explicar, o una explicación que no alcanza, es devolución; si lo dejaste
pasar al aceptar, va como escape («Revisión y aceptación»).

## 3. Reproducir

1. `docs/pm/herramientas/levantar.sh <SHA>`, separado del turno
   (`docs/pm/herramientas/LEEME.md`).
2. `chequeo-previo.sh <SHA>`: todo OK antes de correr nada. Los casos del
   informe; los negativos de la Dev; uno o dos negativos tuyos que ataquen
   otro borde.
3. `suite-y-puertas.sh <base> <SHA>` cuando corresponde.
4. Si la pieza toca dinero, sesión, permisos, datos o es transversal:
   subagentes adversariales con contexto nuevo, con el modelo y el esfuerzo
   de la tabla de `ONBOARDING-PM.md` («Subagentes»).
5. Lo que dé distinto del informe se reproduce y se clasifica antes de
   aceptar. Un rojo intermitente necesita causa, no una repetición verde.

## 4. Veredicto

- **Consejero antes de escribir el veredicto** (sólo la PM principal;
  cuándo, en `ONBOARDING-PM.md`, «Subagentes»).
- `docs/pm/REPRODUCCION-<PIEZA>-<fecha>.md` con la evidencia.
- Arriba del canal de esa Dev (`PARA-DEV.md` o `PARA-DEV-N.md`): aceptada,
  rechazada o con devolución, sobre qué SHA, y las respuestas a cada D con
  su número.
- Una devolución nombra la **causa** y pide un caso de la familia, no sólo el
  ejemplo; al aceptar la vuelta, probá un ejemplo distinto del que diste
  («Devolución por la causa» en `ONBOARDING-PM.md`). Si pide código, lleva
  su camino de hoy («Código de producto sólo con camino de hoy»); sin
  camino, es un riesgo y no una devolución.
- Lo que se le suma a la siguiente tarea queda escrito antes de activarla.
- `NOW.md` y `DECISIONS.md` si corresponde.
- Al aceptar la pieza entera (no una subpieza), su marca en `ROADMAP.md`
  pasa a ✅ en el mismo commit; `avance.py` cuenta desde ahí.
- Si la aceptás, integrá recién ahí la rama de esa Dev con `merge`.
- **Higiene** (`ONBOARDING-PM.md`, «Higiene de los documentos»): en el mismo
  commit, lo cerrado sale del canal y los topes se respetan.
- Commits propios sólo en `docs/pm/` y `.claude/`. Push a la rama de PM
  (`claude/practical-shannon-szpwkn`); cada Dev la trae. Si el push se
  rechaza porque la otra PM empujó, `fetch` + `merge` y de nuevo.
- **Despertá a la Dev ya:** `send_message` a su sesión (`priority` `next`) apenas está subido
  el veredicto, sin esperar su hora.

## 5. Emi

Sólo la PM principal le habla a Emi (la PM visual lo pasa por
`ENTRE-PMS.md`). Una línea sólo si tiene que decidir algo, siempre con una
recomendación.
En modo automático, sólo los casos de «Modo automático» en
`ONBOARDING-PM.md` (publicar, plata o producción, datos de producción
irreversibles, límites que no se negocian, contrato); lo demás lo decide
la PM y lo anota como «decidido por la PM». Nada se publica sin su
autorización explícita para ese SHA («Publicar» en `ONBOARDING-PM.md`).
