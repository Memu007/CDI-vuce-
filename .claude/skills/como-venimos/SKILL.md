---
name: como-venimos
description: Para Emi, en cualquier sesión (PM principal, PM visual o Dev). Contesta en cuatro líneas quién tiene la pelota, qué sigue, qué tiene que decidir Emi y el avance, leyendo la rama y no la memoria del chat. No cambia nada.
---

# /como-venimos — el estado en cuatro líneas, para Emi

Sólo lee. No integra, no commitea, no arranca nada.

## Canales

Con dos Devs hay dos canales, y cada Dev usa sólo el suyo:

| | PM escribe | la Dev contesta | rama de la Dev |
|---|---|---|---|
| Dev 1 | `PARA-DEV.md` | `PARA-PM.md` | la de `NOW.md`, «Quién hace qué» |
| Dev 2 | `PARA-DEV-2.md` | `PARA-PM-2.md` | la de `NOW.md`, «Quién hace qué» |

La PM escribe en su propia rama (`NOW.md`); cada Dev la trae con `merge`.
Nunca se toma una tarea ni se escribe en el canal de la otra Dev.

## 1. Leer, desde las ramas

Las ramas son las que registra `docs/pm/NOW.md`. Lo de abajo es para la Dev
1; con dos Devs, se repite para la Dev 2 con su rama y su canal
(`PARA-DEV-2.md` y `PARA-PM-2.md`), y se contesta una línea de pelota por
Dev.

```bash
git fetch origin <rama Dev>
git log -1 --format='%h %cr' origin/<rama Dev> -- docs/pm/PARA-DEV.md   # lo último de la PM
git log -1 --format='%h %cr' origin/<rama Dev> -- docs/pm/PARA-PM.md    # lo último de la Dev
git show origin/<rama Dev>:docs/pm/PARA-DEV.md | head -40
git show origin/<rama Dev>:docs/pm/PARA-PM.md | head -30
git show origin/<rama Dev>:docs/pm/NOW.md | head -25
```

- Si lo último es de la Dev, la pelota la tiene la PM: revisar esa entrega.
- Si lo último es de la PM, la tiene la Dev: la «Tarea activa» o la
  devolución.
- La tiene Emi si `PARA-DEV.md` o `NOW.md` dicen que algo espera su decisión
  o su autorización para publicar.

Además, desde la rama de PM: `docs/pm/VISUAL.md` (estado de lo visual y
«Última vuelta» de la PM visual) y `docs/pm/ENTRE-PMS.md` (lo que se piden
las PMs). Una sesión con «última vuelta» de hace más de 3 h está parada:
decilo. Si alguna avisó que necesita compactar, decilo con su `/compact`.

## 2. Contestar así, y nada más

- **La pelota la tiene:** PM (revisando …) / Dev (haciendo …) / Emi (decidir …).
- **Sigue:** la próxima pieza de la cola.
- **Vos decidís:** lo pendiente de Emi, o «nada por ahora».
- **Avance:** la primera línea de `python3 docs/pm/herramientas/avance.py`
  (piezas aceptadas sobre el total del roadmap; aceptada no es publicada).

Si dos fuentes no coinciden (por ejemplo, `NOW.md` dice una tarea activa y
`PARA-DEV.md` otra), agregá una línea más que lo diga.
