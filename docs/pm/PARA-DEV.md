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

## Mientras reviso (2026-10-25 00:30 UTC)

PRUEBAS-1 + PA-1b (`e924b29`) siguen en revisión. El veredicto va acá arriba.

- **D8: (b).** `landing.html:139` queda «NCM», igual que D6.
- **Orden:** EXCEL-3c (arriba). Después terminá **CLIENTE-1b** («Más
  adelante») y seguí con ESTUDIO-1. MARIA-7 ya está integrada en mi rama
  (`1fa0b6e`): traela con `merge` antes de empezar EXCEL-3c.

## Veredicto de PA-1 + D3 (2026-10-24): aceptada

Sobre `31719c3` (producto `489daf4`, `c7e4c3a`, `26797f8`, `d8e084c`),
incluido el supuesto de la fecha a medias. Integrada con `merge` a la rama de
la PM (`fe41228`); el producto es idéntico al revisado. Detalle en
`REPRODUCCION-PA-1-2026-10-24.md`: focales 65 passed, suite 1782 passed,
`pa1.sh` 27 ROJO y `cliente1.sh` 23 ROJO con 0 sin rojo (esperando el foco,
abajo). La e2e no la corrí.

- **D4: (b).** «Posición SIM» queda.
- **D5: (a)**, como pieza chica **PA-1b**: sólo la demo de la landing pasa a
  «3 PA SIM» (`proyecto_maria/templates/landing.html:130` y `:139`).
  `public_quote.html` no; el resto de la landing (textos de venta) tampoco.
- **D6: (a).** `enrich.js:207` queda «NCM».
- **D7: (a)**, dentro de **CLIENTE-1b** (abajo, ampliada).

Del adversario (sobre D3, en navegador): el núcleo de D3 aguanta. Salieron
tres cosas anteriores a D3; dos van a CLIENTE-1b y la tercera queda como
riesgo (un guardado en vuelo cierra el formulario de otro cliente abierto
después). No la arregles.

## Ahora (2026-10-24 21:05 UTC), en este orden

### 1. PRUEBAS-1: pruebas que quedaron mal (sólo pruebas, sin producto)

Salió al probar la publicación de `8b45207`. El producto está bien; las
pruebas no.

**a) `cliente1.sh` da un «sin rojo» que va y viene.** Lo vi 1 vez en una
corrida y lo reproduje 2 de 82 veces.
- **Causa:** `openForm()` (`clientes.js`) pone el foco en `#cfNombre` con
  `setTimeout(..., 80)`. `page.fill('#cfCuit', …)` enfoca y escribe en dos
  pasos; si el temporizador cae en el medio, el CUIT se escribe en el
  nombre («Nombre20-12345678-6») y el CUIT queda vacío. Entonces el aviso
  dice que falta el CUIT y la prueba lo toma como falla, aunque no haya
  sabotaje.
- **Qué:** antes de llenar el formulario recién abierto, esperar la
  condición observable `document.activeElement.id === 'cfNombre'`
  (`page.waitForFunction`), no una espera fija. **Por la familia:** toda
  prueba que llene `cxForm` justo después de abrirlo (alta, «Cliente Dos»,
  editar, y las de PA-1 si llenan el formulario).
- **Prueba de que distingue:** con la espera, 100 corridas seguidas sin
  que el CUIT caiga en el nombre; sin la espera, que se vea al menos una
  (podés acortar el `setTimeout` en un worktree descartable para forzarlo,
  nunca en el producto).

**b) `excel1.sh` tiene cuatro sabotajes viejos.** EXCEL-3 cambió el código
que atacan y el script no se actualizó (sobre `8b45207`: «sabotajes con
falla: 4»):
- «las filas de subtotal vuelven a entrar» y «el total en la columna de
  código vuelve a entrar»: el patrón ahora es `_es_fila_de_total(rotulo or
  pieza)`. Ojo: cambiarlo por `rotulo` solo **no** da rojo (rótulo ya toma
  «TOTAL AMOUNT» de la columna de código); con `descripcion` sí. Elegí el
  sabotaje que reproduce el defecto viejo.
- «vuelven las dos columnas con el mismo nombre (500)»: el `drop` ahora son
  dos líneas con `campos` y `pesos`.
- «el mapeo guardado vuelve a dejar afuera lo detectado» (`elegido = g`):
  da 35 rojos, pero ya no el de
  `test_mapeo_guardado_no_deja_afuera_encabezados_nuevos`. Decí por qué esa
  prueba ya no lo distingue y ajustá la expectativa o la prueba.
- **`excel2.sh`, lo mismo** (sobre `8b45207`, 20:20–20:50 UTC): tres
  sabotajes no encuentran su patrón: «leer la factura vuelve a abrir el
  libro entero» (la llamada ahora es `_xlsx_solo_primera_hoja(ruta,
  max_filas=_MAX_FILAS_EXCEL)`), «la columna de origen vuelve a ser
  obligatoria» (ahora `if not all([desc_col, cant_col, valor_col]):`) y «un
  producto mal formado vuelve a dar 500» (`if not isinstance(_it, dict) or
  (` ya no existe; está en `main.py` ~4238). Además el script no termina en
  30 minutos: corrieron 26 de 42 (23 ROJO). Medí cuánto tarda cada sabotaje
  y decí por qué; si es `test_excel2.py` entero por vez, corré sólo la
  prueba que cada sabotaje nombra.

- **`maria1b.sh`, lo mismo** (sobre `8b45207`, «sabotajes con falla: 2»):
  EXCEL-2 (`7e9c4e0`) movió el código. «NaN e inf vuelven a pasar en la
  cantidad» busca `if _fuera_de_rango(cantidad):` y ahora es
  `cantidad_mala = _fuera_de_rango(cantidad)` (`core/controles_maria.py:115`);
  «una hoja de gráfico vuelve a contar como hoja» busca la línea de
  `chartsheet` en `main.py` y ahora está en `security/file_security.py:162`.
  Sólo el script: no toques `controles_maria.py`.

**a), validado por la PM:** con `page.waitForFunction(() =>
document.activeElement && document.activeElement.id === 'cfNombre')` después
de cada una de las cinco esperas de `#cfNombre` en `pantalla_cliente1.js`,
`cliente1.sh 31719c3` dio 23 ROJO y 0 sin rojo. Ése es el camino; falta la
prueba de que distingue (arriba) y la familia.

**c) e2e: el rojo intermitente de `#validatingRerun`** que viste sobre
`d1f7833` (`Node is either not clickable or not an Element`,
`config/e2e_maria.js:202`). No es de PA-1, y una repetición verde no lo
cierra.
- **Diagnóstico:** en el momento de la falla, registrá si el botón está en el
  documento (`isConnected`), si se ve (`offsetParent`, caja) y si la
  validación anterior terminó. Decí la causa.
- **Qué:** esperar una condición observable (el botón visible y habilitado,
  la validación anterior terminada), no una espera fija.
- **Prueba de que distingue:** con una demora forzada en
  `/api/validate/smart` (`page.route`), sin la espera falla y con la espera
  pasa.

**Al terminar:** `excel1.sh`, `excel2.sh` y `cliente1.sh` con «sin rojo: 0» /
«con falla: 0» sobre tu SHA, y cuánto tardó cada uno; la e2e con la prueba
de la demora.

### 2. PA-1b: la demo de la landing (D5)

Las dos líneas de la demo (`landing.html:130` y `:139`): «NCM» pasa a
«PA SIM», como el progreso de la aplicación. Una prueba de texto como las de `test_pa1_textos.py` y su
sabotaje. Nada más.

### 4. ESTUDIO-1, con lo que pediste definido (decidido por la PM)

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

## Más adelante — GUARDAR-2

Ya hay un candidato aislado: `2d930c5` en la rama vieja
`claude/dev1-tecnica` (sobre `1cdfe49`). Partí de ahí, no lo rehagas;
faltaba lo de `CIERRE-RETOMA-2026-10-24.md` («Qué sigue», punto 2).
