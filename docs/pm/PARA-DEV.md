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

## Respuestas a tus D (2026-10-07, 10:15 UTC)

- **EXCEL-1:** en revisión de la PM. Mientras, arrancá MARIA-1b (abajo).
- **D17: (a), en MARIA-1b.**
- **D18:** el aviso de «otras hojas con datos», en MARIA-1b. Lo demás
  (encabezado fuera de la fila 1, sin columna de origen, celdas combinadas)
  queda anotado como EXCEL-2, después de PUNTA-A-PUNTA-1.
- **D19:** anotados. La NCM de 7 dígitos (el 0 inicial perdido) va en
  MARIA-1b: el control del catálogo la tiene que atajar.
- Anteriores: D13 (a), D14 (a), D15 a MARIA-3, D16 (b).

**Ya decididas para COBRO-CORTE-1** (2026-10-07; tus opciones están en tu `PARA-PM.md`
del commit `62b1d14`):
- **D4 (cuándo se cuenta): (b), con N = 10.**
- **D5: (a).** Sólo por estado en las rutas que gastan Gemini o generan valor;
  el tope, donde se cuenta una operación.
- **D6: (a)** ahora. El índice único (b), pieza aparte más adelante, después
  de mirar si producción ya tiene códigos repetidos.

## Tarea activa — MARIA-1b: controles antes de generar

Asignada el 2026-10-07. Fase 1 (`ROADMAP.md`). Cambia cuándo se puede
generar el TXT, no lo que sale en él.

**Base:** tu rama (con EXCEL-1).

**Alcance:**
1. Antes de generar, con un aviso claro por producto u operación: NCM que no
   está en el catálogo (si tiene 7 dígitos, proponer el 0 inicial), moneda,
   incoterm, CUIT del importador y montos (vacíos, negativos, en 0). Lo que
   impide un TXT válido no deja generar; lo dudoso avisa.
2. Ningún texto (descripción, nombres, domicilio) mete saltos de línea ni
   `=` que rompan el TXT (M10).
3. Al guardar la operación no se inventan cantidad 1 ni peso 0,5
   (`save_client_operation`, D6 de la Dev 2).
4. El aviso de filas del Excel sin leer queda en el semáforo hasta que la
   persona lo descarte (tu D17), y se avisa si el libro tiene otras hojas con
   datos (tu D18).

**Fuera de alcance:** lo que el generador decide (Dev 2) y el resto de D18
(EXCEL-2).

**Criterios:** rojo antes y verde después por cada control; los dos archivos
reales siguen saliendo idénticos; suite completa en verde.

**Después:** PUNTA-A-PUNTA-1 y EXCEL-2.
