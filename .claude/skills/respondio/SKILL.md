---
name: respondio
description: Dev. Retomar el ciclo después de que la PM escribió en PARA-DEV.md - traer la rama Dev, integrar sus commits y hacer lo que dice. Usalo cuando te despierte tu rutina horaria o la PM principal.
---

# /respondio — retomar después de la PM

Las reglas están en `CLAUDE.md` y `docs/pm/ONBOARDING-DEV.md`. Acá va sólo el
orden. «Tu canal» es el de la tabla: `PARA-DEV.md` para la Dev 1,
`PARA-DEV-2.md` para la Dev 2.

## Canales

Con dos Devs hay dos canales, y cada Dev usa sólo el suyo:

| | PM escribe | la Dev contesta | rama de la Dev |
|---|---|---|---|
| Dev 1 | `PARA-DEV.md` | `PARA-PM.md` | la de `NOW.md`, «Quién hace qué» |
| Dev 2 | `PARA-DEV-2.md` | `PARA-PM-2.md` | la de `NOW.md`, «Quién hace qué» |

La PM escribe en su propia rama (`NOW.md`); cada Dev la trae con `merge`.
Nunca se toma una tarea ni se escribe en el canal de la otra Dev.

## 1. ¿Hay algo nuevo?

```bash
git fetch origin <rama de la PM>     # la que registra docs/pm/NOW.md
git log --oneline HEAD..origin/<rama de la PM>
```

- **Nada nuevo de la PM:** decilo en una línea y terminá. Si te disparó la
  rutina, no hagas nada más: vuelve a preguntar en una hora.
- **Hay commits:** seguí.

## 2. Integrar

- Con `merge`, nunca `rebase`.
- Los commits de la PM tocan sólo `docs/pm/` y `.claude/` (agentes y
  comandos), además de traer `main` y lo que ella aceptó de las Devs. Si un
  commit propio de la PM toca `src/`, `backend/` o `scripts/`, frená y
  avisá antes de seguir.

## 3. Leer qué cambió

```bash
git diff <SHA de antes>..HEAD -- docs/pm/<tu canal>
```

- **Tu canal no cambió** (la PM escribió en el de la otra Dev, o sólo
  actualizó `NOW.md` u otro documento): no hay respuesta para vos. Si tu
  última entrega está en revisión y tu canal tiene una pieza marcada
  «apenas entregues <esa>» o «mientras la PM revisa <esa>», arrancala (o
  seguí con ella). Si no, decilo en una línea («No hay nada nuevo
  para la Dev 1 en PARA-DEV.md») y no hagas nada más.
- **Cambió:** arriba de tu canal
  está la decisión sobre tu última entrega. Leé también la «Tarea activa»
  entera: la PM puede haberle sumado un agregado.
- Si tu informe tenía decisiones numeradas (D1, D2…), comprobá que la PM
  contestó cada una. Si falta alguna, preguntala en tu próximo informe; no la
  des por decidida.

## 4. Qué hacer según lo que dice

| La PM dice | Qué hacés |
|---|---|
| Devolución sobre tu entrega (rechazo, agregado, cambio) | Se atiende primero, en la misma pieza, y se vuelve a entregar con `/entregar` |
| Aceptada, con una «Tarea activa» nueva | Arrancala; si ya la habías arrancado al entregar, seguí |
| Aceptada, sin tarea nueva | Decilo en una línea y no arranques nada |
| Algo que decide Emi | Va como D en tu informe y la PM lo resuelve o se lo pregunta. No sigas en eso |

## 5. Trabajar

- Levantá el entorno local del proyecto (`ONBOARDING-DEV.md`, «Desarrollo local»); en contenedores remotos muere entre turnos.
- Rojo antes que verde: el caso nuevo tiene que fallar por el motivo de la
  tarea antes de tocar el producto.
- Cerrá con `/entregar`.

## 6. En el chat

Una línea con lo que hiciste; lo que haya que decidir, como D en tu
informe. Vos no le hablás a Emi: lo lee la PM principal. Si escribiste
una D sin la que no podés seguir, subila y avisale a tu PM con
`fire_trigger` de su rutina, como en `/entregar` §5.
