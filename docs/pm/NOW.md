# NOW — CDI

Actualizado: 2026-10-06. Estado vigente; la historia está en Git.

**Producto:** `Memu007/CDI-vuce-` (privado desde el 2026-10-06).
**Publicado:** `main` = `a771693` (2026-07-18) en Railway, `cdi-production.up.railway.app`.
Railway publica cada push a `main` sin esperar los tests.
**Rama de trabajo:** `claude/project-deploy-review-4nct96` = `e8344d0`, con 25
commits sin publicar. **Rama de PM:** `claude/practical-shannon-szpwkn`.
**Usuarios reales en producción:** ninguno; la usa sólo Emi.

## Para Emi

1. **URGENTE: rotar las claves de Gemini.** Una estuvo escrita en este
   repositorio cuando era público. Pasarlo a privado no la invalida. En Google
   AI Studio: borrar las dos claves que aparecieron, crear una nueva y ponerla
   sólo en las variables de Railway. Mirar la facturación de Google. (G0)
2. **Aprobar, corregir o rechazar el roadmap** (`ROADMAP.md`). Sin eso, la Dev
   no arranca.
3. **Mandar las preguntas al despachante** (`PREGUNTAS-DESPACHANTE.md`).
4. **Antes de la primera publicación:** confirmar en Railway que estén
   `DATABASE_URL` y `ENVIRONMENT=production`, y que el Postgres tenga backup.
   Recomendación: apagar la red pública de la base, porque la app usa la
   interna.
5. **Decidido por la PM, se puede revertir:** los límites del proyecto
   (`ONBOARDING-PM.md`) y que las reglas nuevas lleguen a `main` con la
   primera publicación. Hasta entonces, en `main` sigue la regla vieja que
   manda «push a `main`» a Cursor y compañía: **no le pidas a ningún asistente
   cambios sobre `main`.**

## Quién hace qué

| Rol | Sesión | Rutina | Rama |
|---|---|---|---|
| PM principal | session_01B7FVQspcEHF7PqNv797wNM | trig_01TvMmGfSLDfbcJrf66ZZ7YK (min 55) | claude/practical-shannon-szpwkn |
| Dev 1 | PENDIENTE: se abre en este repositorio cuando Emi apruebe el roadmap | PENDIENTE | claude/project-deploy-review-4nct96 |

La sesión «CDI — Dev 1» (session_01F66wsdGqhMMEiCLTopVVXe) se abrió sobre la
copia vieja (`Memu007/CDI`): su rutina está pausada y no trabaja acá.

Esfuerzo: PM principal extra; Dev 1 alto (sus tareas tocan cobro, sesión y
datos).

Archivos abiertos por Dev: (ninguno).

## En curso

- PM: roadmap propuesto, esperando a Emi.
- Dev 1: sin tarea (en espera).

## Cola

Cola, en orden: la de `ROADMAP.md` cuando Emi la apruebe. Hasta entonces,
vacía.

## Puertas para cobrarle a un estudio

Estado medido el 2026-10-06 (`AUDITORIA-2026-10-06.md`). Las de septiembre
(G0 a G7) siguen, con lo nuevo.

| Puerta | Estado | Qué falta |
|---|---|---|
| G0 · Secretos | 🔴 | Rotar las claves de Gemini (Emi) |
| G1 · Configuración | 🟢 | G1.1 a G1.5 cortan (re-verificado). G1.6 y G1.7 sin medir |
| G2 · Imagen real | 🟢 | Cerrada el 2026-09-17. El código no cambió desde entonces |
| G3 · Aislamiento | 🟡 | En la rama, 22/0 y sin fugas en lo atacado. **En producción sigue la fuga de MARIA.TXT** (se arregla al publicar). Abiertos: admin para cualquiera, sesiones que reviven al cambiar la contraseña, límite de intentos burlable |
| G4 · Producto (MARIA) | 🔴 | Peso por unidad en vez de total, `CARTUSO` e `IVAADICIONAL1` fijos, identificadores, ítems de demostración sin clave, avisos después de generar, redondeos |
| G5 · Pruebas | 🟢 | 680 passed, 102 skipped, 0 failed (re-verificado) |
| G6 · Volver atrás | 🟡 | El esquema aguanta ir y volver (probado en local). Falta: backup de la base y contar los `active` vencidos antes de publicar |
| G7 · Cobro | 🔴 | El corte por impago cubre 2 de 73 funciones; cancelar no cancela en Mercado Pago; aviso de pago sin firma y repetible; doble suscripción; invitaciones con error en Postgres |
| G8 · Piloto | ⚪ | Tres estudios presentan de verdad un MARIA de CDI (`ROADMAP.md`, bloque 4) |

## Publicado

- `a771693` (2026-07-18), anterior a este método. Cada publicación nueva: una
  línea con fecha, SHA y qué verificó Emi.

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

2026-10-06: mudanza del método a este repositorio y auditoría.

## Medición

`archivo/MEDICION-SUBAGENTES.md` y `archivo/MEDICION-CONSEJERO.md`.
