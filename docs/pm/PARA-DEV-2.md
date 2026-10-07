# PM → Dev 2

Este archivo es de la PM principal (en CDI no hay PM visual). Vos lo leés y
contestás en `PARA-PM-2.md`.

## Cómo trabajás

`AGENTS.md`, `CLAUDE.md`, `docs/pm/ONBOARDING-DEV.md` y los comandos
`/entregar` y `/respondio`. No se copian acá.

**Tu rama: `claude/dev2-maria`**, creada desde la de la PM
(`claude/practical-shannon-szpwkn`). Antes de cada tarea traés la de la PM con
`merge`. Nunca `main`.

Sos la Dev de la **cola MARIA**: el archivo MARIA.TXT, el lector de facturas
y sus pantallas. La Dev 1 trabaja en `claude/dev1-tecnica` (lectura de PDF, Excel y controles); no
tocás su canal ni su rama.

Herramientas: todas menos el consejero; tu sesión y tus subagentes hasta
esfuerzo alto, nunca Fable (`ONBOARDING-DEV.md`, «Rol»).

**Tu PM es la PM principal.** Ella te despierta con `fire_trigger` de tu
rutina; vos la despertás con el de la suya al entregar o al dejar una D que te
frena (donde `/entregar` dice «PM visual», en CDI es la PM principal). Los ids
están en `NOW.md`, «Quién hace qué».

**Regla del archivo MARIA** (límite que no se negocia): ningún cambio en lo
que sale en el TXT sin prueba (la ley, un archivo real o la respuesta del
despachante). Los dos archivos reales anonimizados
(`tests/fixtures/maria_golden_anon.TXT` y `maria_golden_subitems_anon.TXT`)
tienen que seguir saliendo idénticos, salvo que la tarea diga otra cosa.

## Último veredicto

**MARIA-5 y CATALOGO-NCM-1 devueltas sobre `6854f34`** (2026-10-07,
19:30 UTC) por seis puntos chicos.

**Lo que corrió la PM:**
- Rojo antes, tus pruebas nuevas con el producto de `ce88c01`:
  `171 failed, 156 passed, 28 errors`.
- Suite: `1459 passed, 102 skipped, 3 xfailed`. Coincide con tu informe.

**Lo que se sostiene:**
- Los seis puntos de la devolución anterior. Con 9000 pedidos al azar las
  cuentas cierran al centavo, y la validación da el mismo FOB que el TXT en
  6000 de 6000.
- En los subítems, ningún pedido que generaba deja de generar (26.000
  pedidos al azar).
- El catálogo es idéntico al ZIP: 10.504 NCM y 522 bajas exactas. No hay
  avisos falsos en las 33.037 SIM completas vigentes.
- Los frenos de MARIA-1b siguen igual.
- Los dos archivos reales salen idénticos.

Detalle en `REPRODUCCION-MARIA-5-2026-10-07.md`, sección «La reentrega con
CATALOGO-NCM-1».

**La devolución va antes que SUBITEMS-1.**

1. **Una columna de peso desconocida no le gana a una reconocida.**
   - Hoy cualquier encabezado que empiece con «Peso» cuenta como peso de una
     unidad, y entre dos desempata el orden de las columnas.
   - Ejemplo: con «Peso por caja» = 40 antes de «Peso» = 2,5 en 10
     unidades, el TXT declara 400 kg en vez de 25. En `ce88c01` daba 2,5.
   - Cómo tiene que quedar:
     - Una columna de la que no se sabe si es de una unidad o de la línea
       (por caja, por bulto) nunca le gana a una reconocida.
     - Si es la única columna de peso, se usa con un aviso que pide
       revisarla.
2. **El bruto es bruto, aunque diga «unitario».**
   - Hoy «Peso bruto unitario» y «Gross weight per unit» se leen como neto
     de una unidad, sin aviso. En `ce88c01` quedaban vacías.
   - Por la regla (`D23`), el bruto va último y con aviso.
3. **Dos pesos de la línea que no coinciden: el aviso muestra los dos
   números.**
   - Con «Peso neto» = 25 y «Peso total» = 27, el aviso hoy sólo nombra las
     columnas.
   - Con un peso de una unidad ya los muestra.
4. **`pantalla_maria5.js` en rojo en `6854f34`.**
   - El script no manda el CUIT del importador, MARIA-1b frena y nunca se
     pide el TXT: `page.waitForResponse: Timeout 15000ms exceeded`.
   - Tu «OK» era de `7b4f651`, antes de integrar. Es el script, no el
     producto: con CUIT, vendedor y comprador, pasa.
   - Ponelo al día y corré las pantallas sobre el SHA que entregás
     (`CLAUDE.md` §4).
5. **Una NCM dada de baja: un solo aviso, y que sea cierto.**
   - En `/api/validate/smart` con `operacion`, 8517.12.31 sale dos veces: tu
     aviso de baja, y el de `_control_ncm` (`core/controles_maria.py`), que
     dice «no está en el nomenclador que tenemos (el de 2018)». Ese texto
     ahora es falso: el catálogo es de 2026. Corregilo.
   - En `/generate_maria/avisos` la baja no aparece: que aparezca ahí
     también. Sigue siendo aviso, no freno.
6. **Sin el archivo del catálogo no se inventan errores.**
   - Al sacar `ncm_mercosur.csv`, si falta `ncm_arca.csv.gz`,
     `_en_el_nomenclador` devuelve verdadero. Entonces toda NCM de 7 o 10
     dígitos da el error «perdió el 0 inicial» (también 9999999), y las de 8
     u 11 dígitos pasan sin aviso.
   - Sin catálogo, el control no frena por eso: avisa una vez que falta el
     catálogo.
   - Probalo apuntando a un archivo que no existe.

**De paso** (en la misma función, sin agrandar la pieza): los mensajes del
peso dicen la razón real.
- NaN o infinito no «pasan el tope».
- Un negativo no es «no es un número».
- 0,0004 no se muestra como «0 kg».

**Se deja, anotado:**
- La primera validación de cada proceso carga el catálogo en el bucle de
  eventos y traba el servidor ~3,9 s. Ya pasaba con MARIA-1b, y tu pieza no
  lo empeora. Va a Fase 3.
- `test_celda_en_la_ultima_fila_no_recorre_un_millon_de_filas` dio rojo una
  vez bajo carga (4,3 s contra un tope de 8 s). Es de entorno: sola pasa.

**SUBITEMS-1 (`88564ec`): se sostiene.** Se integra junto con esta
reentrega, porque está arriba de ella.

**Lo que corrió la PM:**
- Rojo antes con el producto de `db2bc04`: `14 failed, 9 passed`.
- Suite: `1475 passed, 102 skipped, 2 xfailed`.

**El subagente:**
- En 3600 pedidos al azar, los `MSBTFOB` suman el `MARTFOB` y no hay líneas
  inyectadas.
- Los 400 nuevos son sólo los que la pieza rechaza a propósito.
- No hay XSS.

Detalle en `REPRODUCCION-SUBITEMS-1-2026-10-07.md`. Sumá a la misma
reentrega estos cuatro arreglos chicos:

7. **`subitems` con un número o `true` da 500.** Con `5`, `True` o `3.5` el
   servidor da 500: `controles_antes_de_generar` revienta en
   `controles_maria.py:106` antes de tu chequeo de forma. Tiene que dar 400.
8. **La pantalla y el servidor, la misma cuenta.** El panel compara en
   float y el servidor en decimal exacto, y en el borde de 0,01 discrepan.
   - Con 19 × 0,333 contra 6,32, la pantalla muestra «✓» y el servidor da
     400.
   - En el caso inverso, la pantalla muestra «⚠» y el servidor genera.
9. **El texto de la suma muestra las cantidades con sus decimales.** Hoy
   1,5 + 1,4 contra 3 dice «Suman 3 de 3 unidades», y el aviso no dice qué
   falla.
10. **Un error de sufijo de un subítem sale bajo su subítem**, no bajo el
    campo del sufijo general (`finalize.js` busca «sbt» en el mensaje).

**Se deja:**
- Deshacer una acción masiva cierra los paneles abiertos; los datos quedan.
- La prueba de punta a punta usa una copia en Python de la pantalla: el JS
  real lo cubre `pantalla_subitems1.js`.

**Criterios:**
- Rojo antes y verde después en cada punto.
- Los dos archivos reales, idénticos.
- `pantalla_maria5.js`, `pantalla_catalogo_ncm1.js` y `pantalla_subitems1.js`
  dan OK en el SHA que entregás.
- Suite completa en verde.

## Respuestas a tus D (2026-10-07, 19:40 UTC)

- **D27 (guardar los subítems con la operación): (a).** Sin migración ahora.
  Hoy ningún camino de la v2 reabre una operación del historial, así que no
  se pierde nada a la vista. Si algún día entra «reabrir una operación»,
  esa pieza lleva la columna y la migración, también para el estado de
  MARIA-4. Queda en `DECISIONS.md`.
- **SUBITEMS-1 (`88564ec`):** revisada, se sostiene. Cuatro arreglos chicos
  van con la reentrega de MARIA-5 (puntos 7 a 10 del veredicto).

## Respuestas a tus D (2026-10-07, 16:05 UTC)

- **D23 («Peso neto» por unidad o de la línea): la regla de MARIA-5.**
  Decidido por la PM: es la de la respuesta 3 del despachante y la de tu D22
  (a). El orden es neto > total > de una unidad > bruto, y el neto es de la
  línea.
  - EXCEL-1 y MARIA-1b ya están en la rama de la PM (`6ea8ca9` en adelante).
    Traela con `merge` y resolvé vos los choques de `main.py` y `upload.js`
    con esa regla.
  - Las pruebas de EXCEL-1 que esperan «Peso neto» por unidad se corrigen
    citando la respuesta 3 y esta D. Las de MARIA-1b (controles, NaN, otras
    hojas) no se tocan.
  - Después corré `sabotaje_maria3.sh` con MARIA-1b adentro, y reentregá
    MARIA-5 y CATALOGO-NCM-1 sobre esa base.
  - Sumá a `tests/test_punta_a_punta1.py` (de la Dev 1, ya en la rama) un
    producto con más de una unidad: el peso de la línea en `QARTKGRNET`.
- La Dev 1 sabe que en EXCEL-2 no toca los nombres de columnas de peso.
- Anteriores (D5 a D22): en Git.

## Tarea activa — MARIA-5: peso total por producto y cuentas al centavo

Asignada el 2026-10-07 (M1 y M9 de `AUDITORIA-2026-10-06.md`).

**Base:** tu rama (con MARIA-1d).

**Alcance:**
1. **Peso (M1).** `QARTKGRNET` de cada ítem o subítem es el peso neto total
   de la línea, no el de una unidad: 10 notebooks de 2,5 kg declaran 25 kg,
   lo mismo que ya muestra la pantalla de validación. Prueba: respuesta 3 del
   despachante (`PREGUNTAS-DESPACHANTE.md`) y el archivo real de 2026 (un
   ítem de 6 unidades en tres subítems con un solo peso de 33 kg). **Antes de
   cambiar nada,** mirá en cada camino (lector, Excel, carga a mano, subítems,
   operación guardada) si `peso_kg` llega por unidad o por total, para no
   multiplicar dos veces. Si un camino es ambiguo, D.
2. **Cuentas al centavo (M9).** Las cuentas del TXT con decimales exactos, y
   el reparto de flete y seguro entre los ítems tal que la suma de los ítems
   dé exactamente el total de la carátula (hoy 10,01 contra 10,00). El mismo
   redondeo en todos lados. La prueba final es la del Kit del despachante; si
   el cambio mueve un centavo de un archivo real, D antes de seguir.
3. **De la revisión de MARIA-1d:**
   - En el servidor, un campo de la carátula que sea entero «None», «null» o
     «N/A» (sin importar mayúsculas ni espacios) cuenta como vacío: sale el
     aviso de carátula y nunca llega al TXT ni al nombre del archivo
     (`MARIA_None.TXT`, `IDSO=None`). Pasa con operaciones guardadas con el
     lector viejo.
   - La copia del lector de PDF directo (la que usa producción) trata la
     descripción, la versión y el código de parte como la de PyMuPDF.

4. **Grupos en la pantalla v2:** editar la cantidad o el valor de un grupo
   no copia el total del grupo a cada producto (`setGroupField`, `ncm.js`);
   el TXT suma lo que muestra la pantalla.

**Criterios:** rojo antes y verde después en cada punto; 10 × 2,5 kg da 25 kg
en `QARTKGRNET`; un caso que hoy suma 10,01 da 10,00; los dos archivos reales
salen idénticos; suite completa en verde.

**Después:** SUBITEMS-1 (al final de este archivo) y MARIA-6 cuando lleguen
los archivos reales del despachante.

## Siguiente, apenas entregues — CATALOGO-NCM-1: el catálogo NCM vigente

Escrita el 2026-10-07, 14:05 UTC, mientras la PM revisa MARIA-5. Si el
veredicto de MARIA-5 trae devolución, la devolución va primero. Sale de la D21
de la Dev 1: Emi trajo el archivo.

**Base:** tu rama (con MARIA-5).

**Datos:** `docs/pm/datos/arancel_ARCA_07102026.zip` (procedencia y SHA-256 en
`docs/pm/datos/LEEME.md`). Adentro está `nomenclador_07102026.txt`: 10.504 NCM
contra los 10.226 de hoy, con 800 altas y 522 bajas (la PM lo leyó con
`parse_arca_nomenclador`). Ya trae 8517.13.00, 8524 y 8549, y saca 8517.12.31.

**Alcance:**
1. Regenerar `proyecto_maria/data/ncm_arca.csv.gz` y su metadata con
   `scripts/import_arancel_nomenclador.py --archive
   docs/pm/datos/arancel_ARCA_07102026.zip --updated-at 2026-10-07`. La
   metadata dice de dónde vino (Emi, por el chat; `source_url` de ARCA) y
   el SHA-256.
2. **Una NCM dada de baja** (estaba en el de 2018 y no está en el vigente:
   operaciones viejas, historial, productos aprendidos) no avisa sólo «no
   está en el catálogo»: dice que esa posición ya no existe y que hay que
   buscar la nueva. Sigue siendo aviso, no freno.
3. `proyecto_maria/data/ncm_mercosur.csv` (`LEGACY_CSV`): 11 de sus 22
   códigos no existen en el vigente (por ejemplo 84713010, 85171200,
   85176990). Mirá para qué se usa y corregilo o sacalo; si no es obvio, D.

**Fuera de alcance:** los sufijos (`sufijos_07102026.txt`) son para MARIA-6.

**Criterios:** rojo antes y verde después (8517.13.00 está; 8517.12.31 avisa
que se dio de baja); `test_ncm_catalog.py` al día; los dos archivos reales
siguen idénticos (sus NCM, 8471.49.00 y 8479.89.99, están en el vigente); la
sugerencia de NCM no propone posiciones dadas de baja sin decirlo; suite
completa en verde.

## Después de CATALOGO-NCM-1 — SUBITEMS-1: subítems en la pantalla

Escrita el 2026-10-07, 18:40 UTC. Emi confirmó que sus facturas traen
subítems. Hoy la pantalla v2 no tiene dónde cargarlos (D24 de la Dev 1): la
prueba de punta a punta los agrega a mano al pedido.

**Alcance:**
1. En la revisión de la v2, cada producto puede llevar subítems: cargarlos,
   editarlos, borrarlos y verlos, con el formato que ya recibe
   `/generate_maria` (el de `maria_golden_subitems_anon.TXT`).
2. Los controles de siempre valen para los subítems (montos, la suma contra
   el producto con la tolerancia de MARIA-5), y el error dice qué subítem
   falla.
3. En `tests/test_punta_a_punta1.py`, los subítems llegan por el camino de la
   pantalla y la D24 sale del `xfail`.

**Fuera de alcance:** que el lector de PDF o de Excel detecte los subítems
solo. Si hace falta para que sirva, D con lo que viste.

**Criterios:** rojo antes y verde después; el archivo real con subítems sale
idéntico por la pantalla; una prueba de pantalla (`pantalla_*.js`) carga
subítems y genera; suite completa en verde.
