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

**VUCE-3 aceptada** (2026-09-18, sobre `e8344d0`). Re-verificada el
2026-10-06: `680 passed, 102 skipped, 0 failed`.

## Tarea activa — ADMIN-1: lo de administración, sólo para el admin

Asignada el 2026-10-07. Roadmap aprobado por Emi (`ROADMAP.md`, cola técnica,
pieza 1). Hallazgo S2 de `AUDITORIA-2026-10-06.md`.

**Base:** la cabeza de `claude/practical-shannon-szpwkn` al arrancar. Su
código es idéntico a `e8344d0`.

**Problema.** Cualquier usuario logueado entra a `/api/admin/*`: ve la salud
del servidor, los errores y las métricas, y puede **borrar el registro de
errores** (la PM lo reprodujo: usuario común, `clear-old` → 200). El router se
monta con `Depends(get_current_user)` (`proyecto_maria/main.py:1312`) en vez de
`require_admin` (`main.py:1727`). Además hay funciones que actúan sobre todo el
sistema y no sobre un estudio, como `/api/ncm/cache/refresh` (`main.py:6412`).

**Alcance.**
1. Todo `/api/admin/*` exige admin (`require_admin`).
2. Una **lista cerrada** de las funciones globales (las que no actúan sobre los
   datos de un estudio): recorré todas las rutas, decí cuáles son globales y
   protegé las que no lo estén. La lista va en tu informe.
3. Una prueba que **recorra las rutas de la app** y falle si aparece una ruta
   de admin o global sin `require_admin`. Que no sea una lista escrita a mano
   que envejece (`CLAUDE.md` §2).

**Fuera de alcance:** VUCE-4 (el listado de cobro), roles nuevos, cambiar cómo
se decide quién es admin, tocar `/api/dev/*` si ya usa `require_admin`.

**Criterios de aceptación** (todos con la salida pegada):
- Rojo antes: con la base de la tarea, un usuario común recibe 200 en
  `clear-old`. Verde después: 403 en **cada** ruta de `/api/admin/*` y de la
  lista global; un admin recibe lo de antes.
- La prueba que recorre rutas falla si se le saca `require_admin` a cualquiera
  de ellas (mostralo una vez).
- Suite completa en verde sobre el SHA que entregás, desde base limpia.
- `scripts/testing/ataque_aislamiento.sh` y `smoke_friccion.sh` como dice
  `/entregar`.
- La pantalla de admin (`dev_dashboard`) sigue andando para un admin.

**Leé:** `AUDITORIA-2026-10-06.md` (S2) y `ROADMAP.md` (cola técnica).

**Cuándo frenar y consultar (D):**
- Quién es admin sale de la variable `ADMIN_USERNAMES` o del rol `admin`
  (`main.py:1720`). Si en producción no estuviera configurada, nadie podría
  entrar al admin después de publicar. No lo resuelvas vos: anotalo como
  riesgo en el informe y la PM se lo pide a Emi antes de publicar.
- Si una función «global» es usada por la pantalla común de los estudios.

**Entrega:** con `/entregar`. Producto, pruebas e informe en commits
separados. Autorrevisión con un subagente Opus alto y uno Sonnet alto (es
permisos).

## Después — COBRO-CORTE-1 (apenas entregues ADMIN-1)

Quien no paga no genera valor ni gasta Gemini (hallazgos C1, C5 y C6). Hoy el
corte por falta de pago (402, `require_active_billing`, `main.py:1749`) está
sólo en `main.py:3139` y `main.py:5434`.

**Alcance.**
1. Llevar el corte a todo lo que genera valor o gasta Gemini:
   `/generate_maria` (`main.py:3542`), `/upload_pdf/public` (`:3422`),
   `/upload_excel` (`:3290`), `/api/validate/smart` (`:3372`),
   `/api/ncm/sugerir` (`:6930`) y `/api/migrations/*` (`:4708`, `:4793`).
   Revisá si hay más y listalos.
2. **Contar una vez por operación.** La operación ya se cuenta al crearse
   (`main.py:3208`, `:5523`). Generar el MARIA no se cobra de nuevo por cada
   descarga: si una operación todavía no se contó, se cuenta una vez
   (decidido por la PM).
3. Carreras (C6): con pedidos al mismo tiempo no se pasa del tope del plan
   ni se repite el `op_code` (`_next_op_code`, `main.py:4193`;
   `can_create_operation` y `record_operation_created` en
   `services/billing_service.py:108` y `:138`). Probalo en Postgres local.

**Fuera de alcance:** Mercado Pago (COBRO-MP-1 y 2), el estado `canceled`
(COBRO-MP-2).

**Ojo con la Dev 2:** ella cambia el manejo de errores de `/upload_pdf/public`
(`main.py:3446`, MARIA-2). Vos tocás la firma de esa función. Si su pieza se
aceptó antes, traé la rama de la PM con `merge` antes de empezar.

**Criterios:** rojo antes y verde después, por ruta, con una cuenta impaga
(402). Una prueba de concurrencia que muestre el tope y el `op_code` sin
repetirse. Suite completa en verde. Autorrevisión con Opus alto y Sonnet alto
(es plata).
