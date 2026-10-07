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

**EXCEL-1 devuelta** (2026-10-07, sobre `9cc321e`). La PM reprodujo el rojo
antes (`46 failed, 8 errors` sobre `ec3d793`), la focal con los archivos
reales (`116 passed`) y la suite (`897 passed, 102 skipped`). Su subagente
Sonnet alto: el aislamiento entre cuentas y los números se sostienen. Detalle
en `REPRODUCCION-EXCEL-1-2026-10-07.md`.

**Devolución** (cada punto con rojo antes y verde después; la devolución va
antes que MARIA-1b):
1. **El mapeo aprendido no pisa una columna reconocida.** Con `cliente_id`
   (la pantalla lo manda siempre), «Valor» aprendido como precio unitario hace
   que «Precio Unitario» 350 salga 3500; igual «Peso» contra «Peso Neto». Las
   pruebas tienen que mandar `cliente_id`, como la pantalla.
2. **Validar un Excel no usa los hilos compartidos:** 12 subidas de un
   `.xlsx` de 8 MB llevaron una consulta de NCM de 0,4 s a 49 y 62 s. Grupo
   propio también para validar, y el tamaño descomprimido se mira antes de
   abrirlo.
3. **La fila de ejemplo de la plantilla** («Laptop 14 pulgadas modelo X») no
   entra como producto.
4. **Un mapeo con dos columnas para el mismo campo** no da 500: se rechaza al
   guardarlo, o se avisa al subir.
5. **Lo que llamaba a las rutas borradas:** la pantalla vieja
   (`static/app.js:939`) dice claro que el Excel se sube en la pantalla nueva;
   `scripts/testing/smoke_test.sh:269` espera lo que corresponde.

Las filas de total que entran sin NCM ni origen las frena el control antes de
generar: quedan para MARIA-1b. El CSV con `;` de `/api/ncm/import-historial`
va a EXCEL-2.

**Tu contexto está en ~80 %:** si no compactaste, pedile a Emi el `/compact`
antes de seguir.

## Respuestas a tus D (2026-10-07, 11:10 UTC)

- **EXCEL-1 (devolución):** en revisión de la PM. Seguí con MARIA-1b.
- **D20: (a).** El CUIT del importador vacío frena, y la pantalla deja de
  decir «opcional»: el TXT sin él no sirve para presentar. En MARIA-1b.
- **D21:** pendiente de Emi (`DECISIONS.md`): hace falta el nomenclador
  vigente de ARCA, que desde acá no se puede bajar. Mientras, «no está en el
  catálogo» sigue como aviso.
- Anteriores (D13 a D19): en Git.

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
