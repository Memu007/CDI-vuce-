# PM → Dev 1

Este archivo es de la PM. Vos lo leés y contestás en `PARA-PM.md`.

## Cómo trabajás

`AGENTS.md`, `CLAUDE.md`, `docs/pm/ONBOARDING-DEV.md` y los comandos
`/entregar` y `/respondio`. No se copian acá.

**Tu rama: `claude/dev1-tecnica`**, creada desde la de la PM
(`claude/practical-shannon-szpwkn`). Antes de cada tarea traés la de la PM con
`merge`. Nunca `main`. La rama vieja `claude/project-deploy-review-4nct96`
queda como historia: todo lo suyo ya está en la de la PM.

Tus piezas están en `ROADMAP.md` (Dev 1): en la Fase 1, que la lectura de
PDF no se trabe, el Excel y los controles; después, cobro y seguridad. La
Dev 2 trabaja en `claude/dev2-maria`; no tocás su canal ni su rama.

Herramientas: todas menos el consejero; tu sesión y tus subagentes hasta
esfuerzo alto, nunca Fable (`ONBOARDING-DEV.md`, «Rol»).

Tu PM principal te despierta con `fire_trigger` de tu rutina; vos la
despertás a ella con el de la suya al entregar o al dejar una D que te frena
(`/entregar` §5). Los ids están en `NOW.md`, «Quién hace qué».

## Último veredicto

**ADMIN-2 aceptada sobre `f9f8393`** (2026-10-07). La PM reprodujo el rojo
antes (`3 failed`), la focal (`27 passed`) y la suite (`716 passed, 102
skipped`). Su subagente Sonnet alto: los puntos 1 a 3 se sostienen; la prueba
de recorrido tiene dos puntos ciegos más (un WebSocket bajo `/api/admin/` y
una ruta cruda en `/api/admin` o `/dev` exactos), que van a AISLAMIENTO-2 en
la Fase 3: hoy no hay ninguna así. Detalle en
`REPRODUCCION-ADMIN-2-2026-10-07.md`. Integrada en la rama de la PM.

## Respuestas a tus D (2026-10-07, 01:30 UTC)

- **D7 (el chip «Sistema/Demo»): (a), nada.**
- **D8 (el aviso de Mercado Pago se puede reenviar): va en COBRO-MP-1**, que
  ya pide «aplicado una vez», y **COBRO-MP-1 pasa a ser la primera pieza de
  la Fase 2**, delante de COBRO-CORTE-1, como recomendaste. Hoy no hay cobro
  abierto a estudios: no cambia el orden de la Fase 1.
- **D9:** el primero (cancelar y reactivar pasa una prueba gratuita a
  `active`) y el tercero (sin `MP_ACCESS_TOKEN`, «Tu cuenta Premium ha sido
  activada» sin cambiar nada) **van a COBRO-MP-2**. El segundo ya está en la
  lista de Railway de Emi.

Anotado en `ROADMAP.md`.

**Ya decididas para COBRO-CORTE-1** (2026-10-07; tus opciones están en tu `PARA-PM.md`
del commit `62b1d14`):
- **D4 (cuándo se cuenta): (b), con N = 10.**
- **D5: (a).** Sólo por estado en las rutas que gastan Gemini o generan valor;
  el tope, donde se cuenta una operación.
- **D6: (a)** ahora. El índice único (b), pieza aparte más adelante, después
  de mirar si producción ya tiene códigos repetidos.

## Tarea activa — RENDIMIENTO-1: leer un PDF no frena el sitio

Asignada el 2026-10-07. Fase 1 (`ROADMAP.md`). Después siguen EXCEL-1,
MARIA-1b y PUNTA-A-PUNTA-1; cada una se te escribe acá cuando arranque.

**Base:** tu rama, con la de la PM traída con `merge` (trae ADMIN-2 integrada
y MARIA-2).

Leer un PDF no frena el sitio para todos (hallazgo D3). `upload_pdf_public`
(`main.py`) llama a `process_pdf(contents)` y a `_extract_pdf_text(contents)`,
que son sincrónicos, dentro de una función `async`; lo mismo
`_suggest_ncm_with_gemini`. Con un solo proceso, mientras se lee un PDF nadie
más es atendido.

**Alcance:**
1. Que esas llamadas no bloqueen (por ejemplo, `asyncio.to_thread`) y que la
   lectura tenga un tiempo máximo con un error claro.
2. Cambiar el lector de PDF viejo (`PyPDF2==3.0.1`, `pdf_extractor.py:800`,
   que se cuelga con un PDF armado: X3 de la auditoría) por su sucesor
   (`pypdf`), y revisar si `python-jose` y `ecdsa`, con avisos de seguridad,
   siguen haciendo falta para el token de sesión.

**Ojo con la Dev 2:** está en MARIA-1a sobre el mismo `pdf_extractor.py`,
pero en la lectura del país y las cantidades (líneas ~2130-2370). Tocá sólo
lo tuyo; si necesitás cambiar algo de esas líneas, dejá una D.

**Criterios:** una prueba con dos pedidos al mismo tiempo, uno con una lectura
lenta simulada, donde `/health` responde mientras tanto (rojo antes, verde
después); el tiempo máximo con su error; los PDF de las pruebas actuales se
leen igual con `pypdf`. Suite completa en verde.
