---
trigger: always_on
---

# Leé primero — CDI

Este repositorio tiene **una sola fuente de reglas** para cualquier asistente: **`AGENTS.md`**, en la raíz. Leelo antes de tocar nada. Si vas a tocar código, leé también `CLAUDE.md`: sus reglas valen para cualquier asistente.

Lo crítico, por si no seguís el enlace:

- **Nunca empujes ni fusiones a `main`.** Railway publica cada push a `main` sin esperar los tests. Trabajá en una rama; `main` sólo con el «dale» de Emi.
- **Nada sin plan aprobado:** ninguna tarea, arreglo «de paso» ni refactor que no haya pedido Emi o que no esté en `docs/pm/PARA-DEV.md`. Proponé; no hagas.
- Ningún secreto (`.env*`) ni dato real de clientes en el repositorio. Nada contra producción ni contra servicios de terceros desde una prueba.
- Emi no programa: conclusión arriba, castellano llano, versión chica primero, sin dar la razón para quedar bien.

Este archivo no lleva reglas propias: si querés cambiar una, se cambia en `AGENTS.md`.
