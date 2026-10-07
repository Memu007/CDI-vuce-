# NOW — CDI

Actualizado: 2026-10-07. Estado vigente; la historia está en Git.

**Producto:** `Memu007/CDI-vuce-` (privado desde el 2026-10-06).
**Publicado:** `main` = `a771693` (2026-07-18) en Railway, `cdi-production.up.railway.app`.
Railway publica cada push a `main` sin esperar los tests.
**Rama de PM:** `claude/practical-shannon-szpwkn`: contiene `e8344d0` (25
commits sin publicar, antes en `claude/project-deploy-review-4nct96`, que
queda como historia) más las reglas y documentos. **Ramas de las Devs:**
`claude/dev1-tecnica` y `claude/dev2-maria`.
**Usuarios reales en producción:** ninguno; la usa sólo Emi.

## Para Emi

1. **URGENTE: rotar las claves de Gemini.** Una estuvo escrita en este
   repositorio cuando era público. Pasarlo a privado no la invalida. En Google
   AI Studio: borrar las dos claves que aparecieron, crear una nueva y ponerla
   sólo en las variables de Railway. Mirar la facturación de Google. (G0)
2. **Publicación de ensayo (aprobada el 2026-10-07; falta el «dale» para el
   SHA).** De día, antes del «dale», en Railway:
   - en las variables del servicio: `ENVIRONMENT` = `production` y que exista
     `DATABASE_URL` (la de la base de Railway). La versión nueva no arranca
     sin `DATABASE_URL`; si faltara, Railway deja andando la vieja;
   - en la base: hacer una copia (pestaña de copias de seguridad) si el plan
     lo permite;
   - mirar qué cuentas hay: toda cuenta activa con el período vencido hace
     más de 7 días pasa a impaga al arrancar;
   - recomendado: prender «Wait for CI» y apagar la red pública de la base.
   La PM le pasa el SHA exacto con la suite corrida sobre él.
3. **Mandar las preguntas al despachante** (`PREGUNTAS-DESPACHANTE.md`).
4. **Decir si CDI usa Google Cloud** (hay un segundo camino de publicación en
   el repositorio; si no, se borra en LIMPIEZA-1) y **si alguna vez subió
   datos reales** al sitio publicado.
5. **Decidido por la PM, se puede revertir:** los límites del proyecto
   (`ONBOARDING-PM.md`) y que las reglas nuevas lleguen a `main` con la
   primera publicación. Hasta entonces, en `main` sigue la regla vieja que
   manda «push a `main`» a Cursor y compañía: **no le pidas a ningún asistente
   cambios sobre `main`.**

## Quién hace qué

| Rol | Sesión | Rutina | Rama |
|---|---|---|---|
| PM principal | session_01B7FVQspcEHF7PqNv797wNM | trig_01TvMmGfSLDfbcJrf66ZZ7YK (min 55) | claude/practical-shannon-szpwkn |
| Dev 1 (técnica) | session_01VV5RVDA64AuzLaPBDnwH39 | trig_016zR6giZB8Mq9ZdfaerVh2D (min 15) | claude/dev1-tecnica |
| Dev 2 (MARIA) | session_01JssJQ6CQvEBZ7yjJp3hHQx | trig_019ehV8P48FzbNwYQGZjgYcW (min 35) | claude/dev2-maria |

**Sin PM visual:** la PM principal revisa a las dos Devs, y las dos la
despiertan con su rutina (donde los comandos dicen «PM visual», acá es la
principal).

La sesión vieja «CDI — Dev 1» (session_01F66wsdGqhMMEiCLTopVVXe, rutina
trig_01XijDAiEX4aBm8dfv9ZD6C1) se abrió sobre la copia vieja (`Memu007/CDI`):
pausada, no trabaja acá.

Esfuerzo (Emi, 2026-10-07): PM principal extra; las Devs, como máximo alto,
también sus subagentes. Ningún subagente usa Fable. El consejero es sólo de
la PM principal.

Archivos abiertos por Dev:
- Dev 1 (ADMIN-1): `proyecto_maria/main.py` (montaje del admin, cerca de la
  línea 1312, y las rutas globales), `proyecto_maria/routers/admin_router.py`.
- Dev 2 (MARIA-2): `proyecto_maria/pdf_extractor.py` (modo demostración),
  `main.py` `upload_pdf_public` (cerca de la 3446) y su pantalla en
  `static/v2`.

## En curso

- Dev 1: ADMIN-1 (`PARA-DEV.md`). Después, COBRO-CORTE-1.
- Dev 2: MARIA-2 (`PARA-DEV-2.md`). Después, MARIA-1a.
- PM: publicación de ensayo (espera el «dale» de Emi para el SHA, de día).
- Emi le manda al despachante la versión simple de `PREGUNTAS-DESPACHANTE.md`.

## Cola

La de `ROADMAP.md`, aprobado el 2026-10-07: cola técnica para la Dev 1 y cola
MARIA para la Dev 2, en ese orden. Semana 1 desde el 2026-10-07.

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

2026-10-07 (madrugada, vuelta horaria): roadmap nuevo con dos auditores
(tamaño y choque de piezas; lo que la auditoría no había mirado: seis
hallazgos X1 a X6 en `AUDITORIA-2026-10-06.md`). Dev sin cambios en su rama
(`e8344d0`). PM al 10 % de contexto.

## Medición

`archivo/MEDICION-SUBAGENTES.md` y `archivo/MEDICION-CONSEJERO.md`.
