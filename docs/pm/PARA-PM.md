# Dev 1 → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## EXCEL-2 — entregada sobre `3e6e63e`

**Resultado:** están todos los puntos del canal, cada uno con rojo antes y
verde después:
- lo que el Excel no leía (D18);
- el CSV del historial de NCM;
- el aviso de mapeo;
- D26 (a), con sus dos criterios medidos;
- lo de paso.

Un subagente (Opus, esfuerzo alto) atacó la pieza y encontró tres defectos
graves en mi primera versión. Están arreglados:
- un FOB duplicado con celdas combinadas;
- los topes de D26 se salteaban renombrando partes del libro;
- la búsqueda del encabezado se trababa con un texto enorme.

No toqué los nombres de las columnas de peso (MARIA-5).

**Lo que decidís vos:** D27, el tope de los textos compartidos (abajo).

| | SHA |
|---|---|
| Base | `3b52bc9` (PUNTA-A-PUNTA-1 aceptada) |
| Producto | `e8f0891`, `0a39909`, `c6c1c23`, `c5ceae9`, `252a5c9`, `b17a59b`, `9314720` |
| Pruebas y sabotajes | `caefdb2`, `eaecaab`, `8cfdcdb`, `6c31dac`, `295c3b7`, `9a54355`, `48646ca`, `1a36a6d` |
| CHANGELOG | `3e6e63e` |

### Qué cambió

1. **D26 (a): abrir un libro armado.**
   - Validar un `.xlsx` ya no lo abre con openpyxl. Cuenta las hojas desde el
     índice del libro y lo rechaza antes de abrirlo si se pasa de alguno de
     estos topes:
     - textos compartidos: 10 MB (`EXCEL_MAX_TEXTOS_MB`);
     - estilos y propiedades: 10 MB;
     - primera hoja: 30 MB (`EXCEL_MAX_PRIMERA_HOJA_MB`).
   - Las partes del libro se buscan como las busca openpyxl, por
     `[Content_Types].xml`: renombrarlas o poner un índice señuelo no saltea
     los topes.
   - Al leer la factura se abre una copia del libro con sólo la primera hoja,
     así openpyxl no recorre las otras hojas que no declaran su medida. El
     historial de NCM también lee sólo la primera.
2. **D18: lo que el Excel no leía.**
   - El encabezado se busca en las primeras 30 filas: la primera fila con 3
     columnas reconocidas. Las columnas del mapeo guardado del cliente
     cuentan como reconocidas, así un pie de página no pasa a ser el
     encabezado.
   - Las filas sin leer siguen nombrándose con su número real en la
     planilla.
   - Sin columna de país de origen, los productos entran con el origen vacío
     y la subida lo avisa.
   - El texto de una celda combinada hacia abajo vale para todas sus filas,
     sólo en su columna y sólo debajo del encabezado. Los números no se
     copian, así que la cantidad y el precio no se duplican.
3. **El CSV del historial de NCM:**
   - Se leen UTF-8, con o sin BOM, y Windows-1252 (latin-1). Un UTF-8 con
     algún byte suelto sigue leyéndose como UTF-8.
   - El separador es el que más aparece en el encabezado, sin contar lo que
     va entre comillas.
4. **El aviso de mapeo nombra la columna.** Cuando el catálogo del cliente y
   el archivo no coinciden, dice: «Para «precio unitario» se usó la columna
   «Precio Unitario» del archivo, no «Valor»».
5. **De paso:**
   - Una lista o un entero enorme (`10**400`) como monto dan 400 y no 500,
     en los productos, los subítems y la exportación. También un producto
     mal formado.
   - El CUIT del despachante (también el del perfil) va con 11 dígitos 0-9,
     sin guiones ni espacios.
   - El identificador del vendedor no puede tener dígitos de otros
     alfabetos. Las letras siguen pasando, porque hay identificaciones
     extranjeras.

### Rojo antes y verde después

```
tests/test_excel2.py sobre 3b52bc9 (antes de EXCEL-2): 23 failed, 6 passed
  (las 6 que pasan ya andaban: CSV con coma y con BOM, libro normal, id extranjero con letras, combinada hacia el costado)
  la subida normal detrás de 8 libros armados sin <dimension>: «400 en 30.4 s» → ahora 200 en 13 s
lo que encontró el subagente, sobre 295c3b7: 19 failed → verde
  (FOB 10120 en vez de 5120; topes salteados con xl/strings.xml o un índice señuelo; 262 s con un texto
   enorme arriba; el pie tomado como encabezado; CSV con «CafÃ©»; CUIT del despachante; 500)
sharedStrings con 19 millones de entradas vacías: se rechaza en 0,0 s, sin memoria extra
  (antes: 93 s y 1,9 GB al abrirlo)
```

### Corrido, con su salida

```
suite como la CI (venv-limpio, ENVIRONMENT=testing, sus --deselect), worktree limpio en 1a36a6d:
  1267 passed, 102 skipped, 10 deselected, 3 xfailed · fin: 0
sabotajes (scripts/testing/sabotajes/excel2.sh 1a36a6d): base en verde y 27 en ROJO, «sabotajes con falla: 0»
```

`3e6e63e` sólo agrega el CHANGELOG sobre `1a36a6d`. Después traje tu rama:
son sólo documentos.

### Comandos para vos

```bash
git fetch origin claude/dev1-tecnica && git checkout 3e6e63e
<venv>/bin/python -m pytest -q --no-cov tests/test_excel2.py          # 51 passed
PY=<venv>/bin/python scripts/testing/sabotajes/excel2.sh 3e6e63e        # «sabotajes con falla: 0»
```

## Decisiones

- **D27 — El tope de 10 MB para los textos compartidos.**
  - Esos textos son comunes a todas las hojas. Un libro con la factura en la
    hoja 1 y un catálogo grande en la hoja 2 se rechaza aunque esa hoja no
    se lea: el tope se cruza con unas 57 mil filas de catálogo.
  - El subagente probó un catálogo de 120 mil filas guardado por
    LibreOffice: 4,4 MB comprimido y 20,5 MB de textos. Antes entraba en
    7,9 s; ahora da 400 con un mensaje claro.
  - El tope no puede ser mucho más alto: textos vacíos armados, cerca de
    10 MB, ya cuestan unos 330 MB de memoria al abrirlos, y el criterio era
    1 GB.
  - Opciones:
    - (a) dejar 10 MB (`EXCEL_MAX_TEXTOS_MB` se puede cambiar sin tocar
      código);
    - (b) subirlo a 20 MB;
    - (c) una pieza que lea la primera hoja sin openpyxl.

  **Recomiendo (a):** una factura real no tiene 57 mil filas, y el mensaje
  pide dejar sólo la hoja de la factura.

## Qué no corrí y riesgos

- **`.xls` (xlrd):** el encabezado se busca igual, pero las celdas
  combinadas no se rellenan, porque xlrd no las da sin el formato.
- **El aviso de mapeo se repite en cada subida** mientras el archivo traiga
  las dos columnas (la del catálogo y la reconocida). Es una sola línea en
  el aviso del final.
- **La migración (`migration_service.py`) sigue leyendo todas las hojas con
  pandas.** Es otra pantalla y tiene su propio tope; no la toqué.
- **Libros armados, ya existía antes:** con nombres de hoja repetidos, uno
  que antes daba 400 ahora da 200.

## COBRO-MP-1 — plan (todavía sin código)

Lo arranco porque Emi no contestó GUARDAR-1; si la aprueba, paso a esa.
Leí el webhook (`main.py:8444-8692`), `billing_service.process_payment` y las
pruebas que lo cubren. Esto es lo que hay hoy:

- **El aviso IPN se acepta sin firma**, aunque esté el secreto y también en
  producción (`?topic=payment&id=…`). Lo único que lo frena es que después
  se le pregunta el pago a Mercado Pago con nuestro token.
- **Para no repetir, sólo se mira el último pago** (`last_payment_id`).
  Cualquiera, sin sesión, alterna dos pagos viejos reales y cada vez deja la
  cuenta `active` 30 días con el contador en 0 (C3, tu D8).
- **El monto no se mira:** ni `transaction_amount` ni `currency_id`. Las
  pruebas pagan 30 000 un plan de 45 000 y pasan.
- **Cada pago fija 30 días desde hoy:** no extiende desde el fin del período
  actual.
- **Lo que no es `type=payment` se saltea**, también las renovaciones de una
  suscripción (preapproval).
- **Las altas de tablas no usan alembic:** las hace `create_all` al arrancar,
  y los cambios de columnas, funciones `_migrate_*` a mano.

**Plan, en este orden, cada paso con rojo antes y verde después:**

1. **Cada pago se aplica una sola vez.** Una tabla nueva,
   `mp_pagos_aplicados`, guarda el `payment_id` (único), la cuenta, el tipo,
   el monto, la moneda, la fecha de aprobación y cuándo se aplicó. El registro
   y el cambio de la cuenta van en la misma transacción; si el id ya está, se
   responde `skipped` y no se toca nada. Prueba: el ataque de D8, alternar A
   y B, no renueva nada.
2. **El monto se controla:**
   - un plan exige moneda `ARS` y un monto igual o mayor al precio de
     `PLANS`;
   - una recarga, igual o mayor a `TOPUP_PRICE_ARS`;
   - un pago que no alcanza no se aplica: queda registrado como rechazado,
     con su motivo, y se loguea.
3. **El período se extiende:** el nuevo fin es el mayor entre hoy y el fin
   actual (si la cuenta está activa), más 30 días. Una renovación pagada
   antes de tiempo no pierde días.
4. **Renovaciones de la suscripción:** procesar
   `subscription_authorized_payment`. Se busca el cobro autorizado, de ahí el
   pago, y se aplica como un pago del `external_reference` de la suscripción,
   con la misma tabla y el mismo control de monto.
5. **Las pruebas viejas que dan por bueno el comportamiento de antes se
   ajustan, y cada cambio va en su commit:**
   - `test_webhook_ipn.py` y `test_g7_cobro.py` pagan 30 000;
   - las que asignan `main.MP_WEBHOOK_SECRET` directo, sin monkeypatch, y lo
     dejan puesto para las demás pruebas.
6. **Todo con el SDK de Mercado Pago simulado**, como `test_prelaunch_block2`.
   Nada contra Mercado Pago real. Revisión con Opus y con Sonnet, en esfuerzo
   alto.

**Lo que tenés que decidir antes del paso que toca:**

- **D28 — El aviso IPN sin firma (paso 1).**
  - Opciones:
    - (a) seguir aceptándolo: con la tabla, reenviar un pago ya aplicado no
      hace nada, y el pago se le pregunta igual a Mercado Pago con nuestro
      token;
    - (b) rechazarlo cuando hay secreto.
  - Mercado Pago no firma el IPN. Si la cuenta tiene el IPN configurado en
    el panel y no los webhooks firmados, con (b) dejan de llegar los pagos.
  - **Recomiendo (a):** la tabla cierra el ataque, y (b) puede cortar cobros
    reales por una configuración que desde acá no puedo ver.
- **D29 — Cuánto tiene que valer un pago (paso 2).**
  - Opciones:
    - (a) igual o más que el precio de hoy;
    - (b) igual o más que el precio que tenía el plan cuando se armó el link
      de pago, guardándolo en `metadata`.
  - Con (a), si Emi sube el precio, un link viejo que se pague tarde se
    rechaza y hay que devolverlo a mano.
  - **Recomiendo (b):** es más trabajo, pero no rechaza pagos legítimos.
- **D30 — Las renovaciones no se pueden verificar desde acá (paso 4).**
  - El SDK (`mercadopago` 2.2.0) no tiene una función para los cobros
    autorizados. Habría que llamar a mano a `/authorized_payments/{id}`, y
    no tengo cómo confirmar el formato real sin Mercado Pago.
  - Opciones:
    - (a) implementarlo según la documentación pública, con el formato
      simulado, y que Emi lo pruebe en el sandbox antes de publicar;
    - (b) dejar el paso 4 hasta tener un aviso real anonimizado de una
      renovación.
  - **Recomiendo (a), con el paso 4 aparte:** no frena los pasos 1 a 3, y
    queda la prueba en el sandbox como condición para publicar.
- **D31 — La tabla nueva (paso 1).** No cambia ninguna tabla que ya existe:
  la crea `create_all` al arrancar, en Postgres y en SQLite. Para volver
  atrás alcanza con publicar el código anterior: la tabla sobra, no estorba,
  y se puede borrar con `DROP TABLE mp_pagos_aplicados`.
  - **Pido el visto bueno** antes de publicar, como pide «sin migraciones a
    ciegas».

**Mientras tanto:** arranco por los pasos 1 y 3, que no dependen de ninguna D.

## COBRO-MP-1 — en pausa en `37d0efe` (sin entregar)

Pausada por GUARDAR-1. Los cuatro pasos tienen código y pruebas; falta
cerrarla:

- **Hecho:** pasos 1 y 3 (`3d3f712`), paso 2 con D29 b y sus tres
  condiciones (`2d51448`: suscripción contra el monto leído en Mercado Pago,
  links viejos contra el precio de hoy, rechazados visibles en
  `/dev/dashboard` → «Pagos de Mercado Pago no aplicados»), paso 4 con D30 a
  (`f5f06ee`: si el cobro o la suscripción no tienen la forma esperada, no se
  aplica nada y se loguea). Pruebas viejas que pagaban 30 000, en su commit
  (`90eff1f`).
- **D31:** la prueba con nombre de dos avisos a la vez está
  (`test_dos_avisos_del_mismo_pago_a_la_vez_se_aplican_una_sola_vez`), y
  `scripts/testing/cobro_mp1_postgres.py` lo mismo contra un Postgres 16
  local: 8 de 8 OK en `18a1850`; con el `IntegrityError` saboteado, FALLA.
- **Pruebas:** `tests/test_cobro_mp1.py`, 36 en verde en `37d0efe`.
- **Falta para entregar:** sabotajes de los pasos 2 y 4 en
  `scripts/testing/sabotajes/cobro_mp1.sh`, suite completa, revisión Opus y
  Sonnet (alto), CHANGELOG, el script de Postgres sobre el SHA final, e
  informe con los riesgos (D28: consultas a Mercado Pago con ids al azar;
  formato del cobro autorizado sin confirmar contra un aviso real).

## Sigo con

GUARDAR-1. Si EXCEL-2 vuelve con devolución, eso va primero.

Última vuelta: 2026-10-07
Contexto: el que mide la PM con get_session.

`/compact conservar: Dev 1 de CDI, rama claude/dev1-tecnica. Aceptadas e
integradas: MARIA-1b, EXCEL-1, PUNTA-A-PUNTA-1. EXCEL-2 entregada sobre
3e6e63e; D27 abierta. Ahora GUARDAR-1 (ncm String(10) en
client_product_history, 500 en Postgres). COBRO-MP-1 en pausa en 37d0efe (ver
PARA-PM.md). Postgres local: /usr/lib/postgresql/16/bin, datos en
/tmp/cdi-dev1/pg, puerto 55432, usuario cdi. Entorno: PM_DIR=/tmp/cdi-dev1,
venv /tmp/cdi-dev1/venv y venv-limpio; rutina de la PM
trig_01TvMmGfSLDfbcJrf66ZZ7YK. Compactar desde el 30 %.`
