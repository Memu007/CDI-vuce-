# PM → Dev 1

Este archivo es de la PM. Vos lo leés y contestás en `PARA-PM.md`.

## Cómo trabajás

`AGENTS.md`, `CLAUDE.md`, `docs/pm/ONBOARDING-DEV.md` y los comandos
`/entregar` y `/respondio`. No se copian acá.

**Tu rama: `claude/dev1-tecnica`**, creada desde la de la PM
(`claude/practical-shannon-szpwkn`). Antes de cada tarea traés la de la PM con
`merge`. Nunca `main`. La rama vieja `claude/project-deploy-review-4nct96`
queda como historia: todo lo suyo ya está en la de la PM.

Sos la Dev de la **cola técnica** (permisos, cobro, sesión, datos). La Dev 2
hace la cola MARIA en `claude/dev2-maria`; no tocás su canal ni su rama.

Herramientas: todas menos el consejero; tu sesión y tus subagentes hasta
esfuerzo alto, nunca Fable (`ONBOARDING-DEV.md`, «Rol»).

Tu PM principal te despierta con `fire_trigger` de tu rutina; vos la
despertás a ella con el de la suya al entregar o al dejar una D que te frena
(`/entregar` §5). Los ids están en `NOW.md`, «Quién hace qué».

## Último veredicto

**VUCE-3 aceptada** (2026-09-18, sobre `e8344d0`).

**ADMIN-1 aceptada sobre `ac25dbc`** (2026-10-07). La PM reprodujo el rojo
antes, la focal (`14 passed`) y la suite (`694 passed, 102 skipped`). Su
subagente Opus alto no encontró ninguna ruta abierta; sí dos puntos ciegos de
la prueba de recorrido, que se suman a ADMIN-2 (abajo). Detalle en
`REPRODUCCION-ADMIN-1-2026-10-07.md`. Integrada en la rama de la PM.

## Respuestas a tus D (2026-10-07, 01:10 UTC)

- **D1 (ADMIN-1, `/api/system/connectors`): (b).** Al usuario común, sólo el
  `mode` de cada conector; el detalle, sólo al admin. Va en ADMIN-2.
- **D2 (`/api/payments/simulate-webhook`): (a), borrarla.** Activa cobro sin
  pagar. Va en ADMIN-2.
- **D3 (`cohort-retention` con `require_role`): (a).** Va en ADMIN-2.
- **D4 (COBRO-CORTE-1, cuándo se cuenta): (b), con N = 10.**
- **D5: (a).** Sólo por estado en las rutas que gastan Gemini o generan valor;
  el tope, donde se cuenta una operación.
- **D6: (a)** ahora. El índice único (b), pieza aparte más adelante, después
  de mirar si producción ya tiene códigos repetidos.

D4 a D6 quedan anotadas para cuando vuelva COBRO-CORTE-1 (ver abajo).

## Tarea activa — ADMIN-2: lo que encontraste en ADMIN-1

Asignada el 2026-10-07. Sale de tus D1 a D3. Es chica.

**Base:** tu rama, con la de la PM traída con `merge`.

**Alcance.**
1. `GET /api/system/connectors` (`main.py:6373`): el usuario común recibe sólo
   el `mode` de cada conector; `base_url`, claves, CUIT, certificado y
   user-agent, sólo el admin. El chip «Sistema/Demo» de la barra superior
   (`static/v2/topbar_financials.js:88`) sigue andando.
2. Borrar `POST /api/payments/simulate-webhook` (`main.py:7983`) y lo que sólo
   exista para ella. Si alguna prueba la usa para armar un estado, que lo arme
   de otra forma.
3. Sacar el `require_role('admin')` de `cohort-retention`
   (`routers/admin_router.py:343`) y sumarlo a tu prueba de rutas de admin.
4. **Sumado por la revisión de ADMIN-1:** que la prueba de recorrido también
   vea (a) apps montadas aparte con `app.mount` bajo `/api/admin/` o
   `/api/dev/`, y (b) rutas crudas de Starlette (`app.router.add_route`) con
   `include_in_schema=False`. Hoy no hay ninguna, pero una así pasaría verde.
   Con su sabotaje: una de cada una, abierta, y la prueba en rojo.

**Fuera de alcance:** cómo se decide quién es admin (tu riesgo 2 se lo paso a
Emi: que `ADMIN_USERNAMES` nombre sólo usuarios que ya existen).

**Criterios:** rojo antes y verde después en cada punto (usuario común ve el
detalle de los conectores; sin sesión y con el secreto, `simulate-webhook`
pasa una cuenta a `active`; el admin por variable recibe 403 en
`cohort-retention`). El chip anda en pantalla (captura). Suite completa en
verde. Autorrevisión con Opus alto y Sonnet alto (es cobro y permisos).

## Después — RENDIMIENTO-1 (apenas entregues ADMIN-2)

Leer un PDF no frena el sitio para todos (hallazgo D3). `upload_pdf_public`
(`main.py:3428`) llama a `process_pdf(contents)` (`:3450`) y a
`_extract_pdf_text(contents)` (`:3474`), que son sincrónicos, dentro de una
función `async`; lo mismo `_suggest_ncm_with_gemini` (`:6905`, usada en
`:7027`). Con un solo proceso, mientras se lee un PDF nadie más es atendido.

**Alcance:** que esas llamadas no bloqueen (por ejemplo, `asyncio.to_thread`)
y que la lectura tenga un tiempo máximo con un error claro. Ojo: la Dev 2 ya
cambió `upload_pdf_public` en MARIA-2; traé la rama de la PM antes de
arrancar (la integro cuando la acepte).

**Criterios:** una prueba con dos pedidos al mismo tiempo, uno con una lectura
lenta simulada, donde `/health` responde mientras tanto (rojo antes, verde
después); el tiempo máximo con su error. Suite completa en verde.

## En pausa — COBRO-CORTE-1

Emi está decidiendo si primero se termina todo el camino «PDF o Excel →
TXT MARIA» y el cobro se corre unas semanas. Hasta que decida, COBRO-CORTE-1
no arranca. Tus D4 a D6 ya están contestadas arriba, para cuando vuelva.
