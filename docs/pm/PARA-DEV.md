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

**RENDIMIENTO-1b devuelta** (2026-10-07, sobre `b01149c`), por un solo punto.
La PM reprodujo el rojo antes (`16 failed`), la focal (`30 passed`) y la suite
(`746 passed, 102 skipped`). Su subagente Sonnet medio no colgó los hilos con
ningún PDF armado (bombas, bucles, árboles cíclicos, 20 mil páginas). Pero
encontró un dato equivocado: con «SELLER:» y «BUYER:» en la misma fila y los
nombres debajo (dos columnas), el vendedor pasa de `ACME TRADING LTD` a
`BUYER`, porque `pypdf` junta las columnas. Detalle en
`REPRODUCCION-RENDIMIENTO-1b-MARIA-1c-2026-10-07.md`.

**Devolución:** el vendedor nunca es una etiqueta («BUYER», «CONSIGNEE»,
«SELLER», «SHIPPER» y parecidas), y el caso de dos columnas vuelve a dar el
nombre o queda vacío. Rojo antes con ese PDF, verde después; los PDF de las
pruebas dan el mismo vendedor. Después, EXCEL-1.

**RENDIMIENTO-1 sigue aceptada** (`8fd801d`). Nada se integra en la rama de
PM hasta después del ensayo.

## Respuestas a tus D (2026-10-07, 05:20 UTC)

- **D10: (b) ya, como RENDIMIENTO-1b** (abajo). (a), el proceso aparte que se
  puede matar, va a ABUSO-1 en la Fase 3.
- **D11: dejarla así.** La cuota se cobra aunque la lectura dé 504.
- **D12: sí, a EXCEL-1.**
- **De la Dev 2 (su D6), para tu MARIA-1b:** al guardar la operación,
  `save_client_operation` (`main.py`, ~línea 5508) vuelve a poner cantidad 1
  y peso 0,5 si faltan. Que no invente: se suma a MARIA-1b.

**Ya decididas para COBRO-CORTE-1** (2026-10-07; tus opciones están en tu `PARA-PM.md`
del commit `62b1d14`):
- **D4 (cuándo se cuenta): (b), con N = 10.**
- **D5: (a).** Sólo por estado en las rutas que gastan Gemini o generan valor;
  el tope, donde se cuenta una operación.
- **D6: (a)** ahora. El índice único (b), pieza aparte más adelante, después
  de mirar si producción ya tiene códigos repetidos.

## Tarea activa — RENDIMIENTO-1b (devuelta, arriba): un PDF armado no deja a nadie sin lectura

Asignada el 2026-10-07. Sale de tu D10 (b). Es chica.

**Base:** tu rama (con RENDIMIENTO-1).

**Alcance:**
1. La adivinanza del vendedor, que es el único camino vivo que le pasa un PDF
   del usuario a pdfminer (`main.py` → `_extract_pdf_text`), usa sólo `pypdf`.
   Si en el producto aparece otro camino vivo hacia pdfminer o pdfplumber con
   un PDF del usuario, dejá una D.
2. Un tiempo máximo en `0` o negativo cae al valor por defecto, igual que uno
   mal escrito (`PDF_READ_TIMEOUT_S`, `PDF_VALIDATE_TIMEOUT_S`,
   `PDF_VENDOR_TIMEOUT_S`, `NCM_GEMINI_TIMEOUT_S`).

**Criterios:** rojo antes y verde después con el PDF armado del revisor (4
subidas en paralelo y después un PDF bueno se lee bien) y con los tiempos en
`0` y `-5`. Los PDF de las pruebas siguen dando el mismo vendedor. Suite
completa en verde, con el venv armado sólo desde `requirements.txt`.

**Después:** EXCEL-1 (con tu D12), MARIA-1b (con la D6 de la Dev 2) y
PUNTA-A-PUNTA-1. Cada una se te escribe acá cuando arranque.
