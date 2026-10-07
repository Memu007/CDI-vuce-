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

**RENDIMIENTO-1b aceptada sobre `ec3d793`** (2026-10-07, con la devolución).
La PM reprodujo el rojo antes de la devolución sobre `b01149c` (`6 failed`:
`BUYER`, `CONSIGNEE`, `NOTIFY PARTY`, el nombre sin cortar), la focal con
RENDIMIENTO-1 (`38 passed`) y la suite con el venv armado sólo desde
`requirements.txt` (`754 passed, 102 skipped`). La primera revisión ya había
atacado los PDF armados (`REPRODUCCION-RENDIMIENTO-1b-MARIA-1c-2026-10-07.md`).
Con dos columnas el vendedor queda vacío: es una de las dos salidas aceptadas.

RENDIMIENTO-1 y 1b se integran en la rama de PM después del ensayo, juntas.

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

## Tarea activa — EXCEL-1: la carga por Excel, de punta a punta

Asignada el 2026-10-07. Fase 1 (`ROADMAP.md`). La carga por Excel nunca se
auditó.

**Base:** tu rama (con RENDIMIENTO-1 y 1b).

**Alcance:**
1. Recorré cada camino vivo que lee un Excel y llega al TXT: `/upload_excel/`,
   `/upload_excel/public`, `/upload_excel_v2/` y los que lean con
   `pd.read_excel` (hoy cerca de las líneas 3401, 4663, 6314 y 7257 de
   `main.py`), con la plantilla que ofrece la pantalla y con Excel reales de
   distinto formato (columnas en otro orden, números con coma, celdas vacías,
   filas de totales, `.xls` y `.xlsx`). Lo que inventa, pierde o lee mal un
   dato se arregla con el mismo criterio que MARIA-1a: un dato que falta
   queda vacío y con aviso, nunca inventado.
2. Leer un Excel no frena el sitio (tu D12): aparte, con tiempo máximo, como
   el PDF.
3. Si un camino no tiene llamador vivo desde las pantallas, decilo en una D
   antes de arreglarlo.

**Prueba para el TXT:** un Excel armado con los datos de los dos archivos
reales tiene que dar el mismo TXT que la carga por PDF con esos datos.

**Criterios:** rojo antes y verde después por cada defecto; una prueba con
`/health` respondiendo mientras se lee un Excel pesado; la suite completa en
verde. Lo que encuentres fuera de esto, en una D.

**Después:** MARIA-1b (con la D6 de la Dev 2) y PUNTA-A-PUNTA-1.
