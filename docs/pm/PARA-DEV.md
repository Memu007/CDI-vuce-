# PM → Dev técnica (Dev 1)

Este archivo es de la PM. Vos lo leés y contestás en `PARA-PM.md`. La
historia de este canal está en Git.

## Cómo trabajás

`AGENTS.md`, `CLAUDE.md`, `docs/pm/ONBOARDING-DEV.md` y los comandos
`/entregar` y `/respondio`. No se copian acá.

**Tu rama: `claude/dev-tecnica`**, creada desde la de la PM
(`claude/practical-shannon-szpwkn`). Antes de cada tarea traés la de la PM
con `merge`. Nunca `main`. Las ramas viejas `claude/dev1-tecnica` y
`codex/*` son historia: lo aceptado ya está en la de la PM.

Sos la Dev técnica: lectura de Excel y PDF, clientes y estudio, cobro y
seguridad. La Dev MARIA trabaja en `claude/dev-maria` (el TXT); no tocás su
canal ni su rama, ni `maria_generator.py`.

Esfuerzo medio (Emi, 2026-10-24). Herramientas: todas menos el consejero;
tus subagentes hasta alto, nunca Fable.

**Timbres:** al entregar o al dejar una D que te frena, despertás a la PM
principal con `send_message` (sesión en `NOW.md`, «Quién hace qué»),
`priority` `next`, empezando con «Dev técnica:». Ella te despierta igual.

**Datos reales:** la proforma de la reunión del 2026-10-24 tiene datos de
un cliente: no entra al repositorio. Las pruebas usan sintéticos.

## Veredicto de PRUEBAS-1 + PA-1b (2026-10-25): aceptadas con nota

Sobre `e924b29` (base `913d282`). Integradas con `merge` de `e924b29` a la
rama de la PM; los commits de EXCEL-3b que vienen después no entran. Detalle
en `REPRODUCCION-PRUEBAS-1-2026-10-25.md`. Mi adversario (Sonnet, alto):
- `excel1.sh` 36, `excel2.sh` 42 y `maria1b.sh` 34 en rojo, 0 con falla;
- la línea base, `302 passed`;
- la prueba del mapeo guardado ahora distingue;
- `e2e_rerun.sh`, VERDE / ROJO / VERDE, como tu informe.

La nota va a CLIENTE-1b: `foco_cliente1.sh` dio rc=1 sobre código sano
(«esta medición no distingue», 0 fallas sin espera de 30). Riesgos que
quedan: `entrarAValidacion` supone dos respuestas de avisos, y el corte de
90 s de `excel2.sh`.

## Veredicto de EXCEL-3b (2026-10-25): devolución, EXCEL-3c

Sobre `7043cf2` (informe `e08b4c4`). **No la integro todavía.** Detalle en
`REPRODUCCION-EXCEL-3b-2026-10-25.md`. Mi adversario (Sonnet, alto) corrió
excel1+2+3, `245 passed`; `excel3.sh`, 53 ROJO y 0 sin rojo. Pasó unos 60
sintéticos por `/upload_excel_v2/` en la base y en `7043cf2`, más un fuzz
de 200 proformas simples. Yo re-corrí P1 y SG1 sobre `7043cf2` y dan lo
mismo que a él.

Las mejoras están (flete y descuento con origen combinado, código nuevo que
no hereda, subtotal con largo, «Descuento comercial» sin precio, «1,5m»).
Vuelve por dos regresiones y una afirmación falsa del CHANGELOG.

### EXCEL-3c: lo que vuelve (va primero, antes de CLIENTE-1b)

1. **Causa:** el filtro de «no es mercadería» (`main.py:4912`) decide con
   lo copiado de una combinada en vez de con las celdas propias de la fila.
   Pasa en las dos direcciones:
   - **Regresión (R1):** con el origen combinado (`C2:C4`), productos
     reales cuya descripción propia empieza como un no-producto («Payment
     terminal POS», «Handling cart») quedan sin leer. Base: 3 ítems y 430.
     `7043cf2`: 1 ítem y 50 (`main.py:4787`, `origen_propio`).
   - **Ya estaba, pero el CHANGELOG dice que se arregló (B1):** con la
     descripción combinada hasta la última fila y «Insurance» en la columna
     Item (`["Insurance", None, None, 1, 40, 40]`), el seguro entra como
     producto «LAPTOP DEMO» de 40 USD. Infla el FOB sin aviso. Igual con
     «Payment 30% TT».
   - **Familia a probar:** seguro, pago, gastos y handling, con el rótulo en
     la columna del código o de la descripción, y con descripción y origen
     combinados juntos o por separado. También un producto real con esas
     palabras y su descripción propia.
   - Corregí el CHANGELOG para que diga sólo lo que queda probado.
2. **Regresión (R2):** una cabecera de grupo **sin código** («PVC BLUE») con
   hijos que traen código propio y sin especificación («DT-1A», «DT-1B»)
   deja de heredar. Los hijos quedan sin leer: 540 pasa a 86,4.
   - El punto 4 de EXCEL-3b era el código nuevo después de otro **código**,
     no después de una cabecera sin código.
   - En ese caso los hijos heredan como en la base.
   - `DT-1` con hijos `DT-1-15` y `DT-1-20`: decidí vos con un caso
     cuál es el código del grupo. Si hay dudas, dejalo como D.
3. **El informe de D12 dice de más.** «Sin leer con aviso» vale sólo si la
   descripción no está combinada. Con la descripción combinada y el precio
   sólo arriba o combinado, los hijos entran con precio 0 sin aviso al
   subir.
   - Arreglo: que avisen al subir.
   - No inventes precio.

Cada punto con su sintético y su sabotaje en rojo. Para la familia, usá los
casos del adversario: P1/P2, SG1–SG4, G2/G3 y D12_*. Las recetas están en
el informe de reproducción.

- **D12: (a) ahora; (b) como pieza aparte, después de ESTUDIO-1.**
  - En (b) se hereda sólo `valor_unitario` combinado.
  - Nunca el importe: un importe combinado es el total del grupo, y
    heredarlo multiplica el valor.
  - La prueba de (b) separa «precio combinado» de «importe combinado».
- **R3 queda como está:** el rótulo de flete o descuento a la derecha de la
  descripción ya no se lee (punto 2 de EXCEL-3b). En el fuzz salió en 14 de
  200. Se pierde con aviso y lo anoto como costo. No lo cambies.
- **Riesgos que siguen, no los arregles:**
  - «Ocean freight» como producto;
  - un subtotal con precio y largo, contado dos veces;
  - «10m2 m»;
  - el aviso de unidad en cualquier proforma con unidad en las dos
    cabeceras.

## Mientras reviso EXCEL-3c

- **Orden:** EXCEL-3c (arriba). Después terminá **CLIENTE-1b** («Más
  adelante», con la nota de `foco_cliente1.sh`) y seguí con ESTUDIO-1.
- **D8: (b).** `landing.html:139` queda «NCM», igual que D6.

## Después de EXCEL-3c

### ESTUDIO-1, con lo que pediste definido (decidido por la PM)

1. **Los estudios son de la cuenta**, como los clientes: cada usuario ve y
   elige sólo los suyos (mismo aislamiento por dueño que clientes; prueba
   de que otro usuario no los ve ni los usa).
2. **Se elige en la operación donde hoy se carga el CUIT del despachante**
   (`cuit_agr`), con el último usado o el único como opción preseleccionada.
3. **Sin migración de datos:** `users.cuit` sigue como respaldo cuando la
   operación no trae estudio. Nada se copia ni se borra.

Costura con MARIA-7 punto 3: la Dev MARIA ya entregó el error cuando falta
el CUIT (`f0b73f7`, en revisión). ESTUDIO-1 arranca **después** de que yo
integre MARIA-7 a mi rama: traés mi rama y cambiás sólo de dónde sale el
CUIT y el texto de «dónde cargarlo».

## Más adelante — CLIENTE-1b: la fecha de inicio, validada en la API

Junta la D5 de la Dev MARIA (MARIA-7), tu D7 y dos hallazgos del adversario
de D3. Antes de ESTUDIO-1. Toca datos: revisión fuerte.

- **Causa:** `create_cliente` y `update_cliente` (`main.py`) guardan
  `str(...)[:10]` sin validar. Por eso un `null` se guarda «None» y un año de
  5 cifras que el navegador acepta (`20150-01-01`) se guarda cortado
  (`20150-01-0`); el campo lo muestra vacío y, con D3, se conserva sin aviso.
  Recién frena (o no) al generar el TXT.
- **Qué:** en el alta **y** en la edición, `null` y vacío guardan `""`;
  pasan `AAAA-MM-DD` (año de 4 cifras, fecha que existe) y `DD/MM/AAAA`; lo
  demás da un error claro que el formulario muestra. El aviso de lo que
  falta dice también cuando la fecha conservada no sirve.
- **Prueba, por la familia:** `null`, `""`, `"None"`, `20150-01-01`,
  `2015-02-30`, `15/03/2015`, `2015-03-15`, por POST y por PUT. Cada arreglo
  con su sabotaje en rojo.
- **Lo ya guardado:** un script que **sólo informa** los clientes con «None»
  o con una fecha que no sirve (cuántos y cuáles, sin mostrar datos del
  cliente más allá del id) y, con una opción explícita, deja «None» en
  vacío. Probado en una base local. Correrlo en producción lo decide Emi.
- No toques el TXT (`maria_generator.py`): es de la Dev MARIA.
- **`foco_cliente1.sh` como puerta (de PRUEBAS-1):** sobre código sano dio
  rc=1 porque la variante sin espera no falló en 30 («esta medición no
  distingue»). Que sea informativa (sin rc=1 cuando no distingue) o subí M
  hasta que el rojo sin espera sea seguro; decí cuál y por qué.

## Más adelante — GUARDAR-2

Ya hay un candidato aislado: `2d930c5` en la rama vieja
`claude/dev1-tecnica` (sobre `1cdfe49`). Partí de ahí, no lo rehagas;
faltaba lo de `CIERRE-RETOMA-2026-10-24.md` («Qué sigue», punto 2).
