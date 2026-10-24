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

## Veredicto de CLIENTE-1 (2026-10-24): aceptada

Sobre `c402bcb` (producto `fbc006a` + `12ff9b6`), integrada por SHA a la rama
de la PM. Detalle en `REPRODUCCION-CLIENTE-1-2026-10-24.md`. Reproducido en
`b0c920b`: tus 14 sabotajes en rojo, tu prueba de pantalla OK y cuatro
negativos míos (domicilio de espacios, editar y borrar el CUIT, fecha que no
es ISO, CUIT corto), todos como decís salvo un matiz de D3 (abajo).

**Se cruzaron los mensajes:** EXCEL-3 y D1 ya estaban respondidas en
`5237aa2` (abajo). No las reabras en `PARA-PM.md`.

## Veredicto de EXCEL-3 (2026-10-24): aceptada

Integrada por SHA (`a173af2`) a la rama de la PM; el producto es idéntico al
revisado. Detalle en `REPRODUCCION-EXCEL-3-2026-10-24.md`. Reproducido:
focales 120 passed; 27 sabotajes, 0 sin rojo; sintético sin datos reales; la
proforma real, en local, da 48 productos en m² y su mercadería, descuento y
flete cierran con el total de la hoja. Suite completa: un rojo, el de los
ocho libros de `test_excel2.py`, que falla igual en la base (es de EXCEL-2;
no lo toques ahora, lo decide Emi).

**D1: (a).** `operacion.flete`, `operacion.descuento` (positivo: lo que se
deduce) y `filas_excel_flete` / `filas_excel_descuento` quedan así. Coincide
con la decisión del 24/10: el sistema ofrece el descuento leído y el usuario
decide qué se deduce. Se lo paso a la Dev MARIA para VALOR-1.

## Ahora (2026-10-24 20:35 UTC): mientras reviso PA-1

PA-1 + D3 (`31719c3`) está en revisión; el veredicto y D4–D7 van acá
cuando termine. No esperes: seguí en este orden.

### 1. PRUEBAS-1: dos pruebas que quedaron mal (sólo pruebas, sin producto)

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
- Al terminar: `excel1.sh`, `excel2.sh` y `cliente1.sh` con «sin rojo: 0» /
  «con falla: 0» sobre tu SHA, y cuánto tardó cada uno.

### 2. EXCEL-3b (abajo, «Más adelante»)

### 3. ESTUDIO-1, con lo que pediste definido (decidido por la PM)

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
CUIT y el texto de «dónde cargarlo». Si llegás antes, seguí con EXCEL-3b.

## Tarea 1 — PA-1, con D3 al lado; después ESTUDIO-1

PA-1 como está en `ROADMAP.md`, Fase 1b. D3 (abajo) va en commits propios y
se entrega junto con PA-1, en el mismo informe. ESTUDIO-1 toca qué va al
`CDDTAGR`: coordiná por la PM con la Dev MARIA (MARIA-7 punto 3), no por su
canal.

## Más adelante — EXCEL-3b (lo que dejó el adversario)

Después de PA-1, en una sola pieza chica. Cada punto con su sintético y su
sabotaje; numeración de la tabla de `REPRODUCCION-EXCEL-3-2026-10-24.md`:

1. (#2) Una fila sin rótulo y sin precio con largo o total de grupo no es
   producto: queda sin leer, como en la base.
2. (#5) Un renglón sin descripción no pasa a ser flete o descuento por un
   texto en otra columna que no sea la de la descripción.
3. (#7) Cuando la unidad sale del encabezado del precio («USD/M», «USD/sqm»),
   se avisa cuál se tomó.
4. (#4, #3) El grupo se corta en una fila de flete o descuento (con o sin
   monto) y en un renglón con código nuevo y sin especificación (ese no
   hereda; se avisa).
5. (#1, #9) «Descuento …» con importe negativo y sin NCM se avisa (no entra
   como producto de valor 0); «1,5m» en el largo no repite la unidad.

## Más adelante — CLIENTE-1b: validar la fecha de inicio en el alta

Salió de MARIA-7 (D5 de la Dev MARIA). `POST /api/clientes` guarda la fecha
de inicio de actividad con `[:10]` sin validar; un valor que no es
`AAAA-MM-DD` ni `DD/MM/AAAA` recién frena al generar el TXT. Al guardar, esas
dos formas pasan y lo demás da error claro en el formulario. Sin migrar lo
ya guardado (tu D3 de CLIENTE-1 lo conserva). Después de EXCEL-3b.

## Más adelante — GUARDAR-2

Ya hay un candidato aislado: `2d930c5` en la rama vieja
`claude/dev1-tecnica` (sobre `1cdfe49`). Partí de ahí, no lo rehagas;
faltaba lo de `CIERRE-RETOMA-2026-10-24.md` («Qué sigue», punto 2).

## Respuestas a tus D

- **D3 (CLIENTE-1), 2026-10-24: (a).** Un matiz: la fecha no se borra «sin
  aviso». Al guardar sale «Faltan para el MARIA: inicio de actividad»; lo
  que no dice es que había una fecha y se perdió. Igual se arregla:
  - **Causa:** el campo de fecha sólo muestra AAAA-MM-DD; si lo guardado
    está en otro formato, el campo queda vacío y el guardado lo manda vacío.
  - **Qué:** si lo guardado no es AAAA-MM-DD y el campo quedó vacío, la
    fecha no se manda y se conserva. Si el usuario carga una fecha, la
    nueva reemplaza a la vieja.
  - **Prueba, por la familia:** fecha guardada `null`, `""`, `"01/03/2015"`,
    otro texto no ISO y una ISO; editar sin tocar la fecha y guardar. Las
    no ISO se conservan; `null` y `""` siguen vacías; la ISO se conserva.
    Un sabotaje que vuelva a mandar el campo vacío tiene que dar rojo.
  - **Lo que deja:** una fecha no ISO ya no se puede borrar desde el
    formulario (sólo reemplazar). Aceptado; anotalo como riesgo.
  - **Al aviso**, si la fecha vieja se conserva, que no diga que falta.
  - No toques la API ni el TXT: la conversión al formato del TXT la hace la
    Dev MARIA (MARIA-7, punto 9).
