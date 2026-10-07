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

**MARIA-5 devuelta sobre `6d59893`** (2026-10-07) por seis puntos. La PM
reprodujo el rojo antes sobre `8e819dd` (`101 failed, 31 passed`), la focal
(`432 passed`) y la suite (`1199 passed, 102 skipped`): coincide con tu
informe. Lo central se sostiene. Por la v2, la v1, grupos y subítems el peso
sale siempre el de la línea. En ~11.000 pedidos al azar las cuentas cierran
al centavo. Los dos archivos reales salen idénticos. Detalle en
`REPRODUCCION-MARIA-5-2026-10-07.md`.

**La devolución va antes que CATALOGO-NCM-1.**

1. **Dos pesos para la misma línea: gana el total neto, con aviso.** Lector
   y Excel usan una sola regla. Si unitario × cantidad no da el total de la
   línea, gana el total neto, y un aviso muestra los dos números.
   - **Lector:** hoy `_peso_del_producto({'peso_unitario':25,
     'peso_total_linea':25}, 10, '.')` devuelve `(25.0, 250.0)`. Si Gemini
     copia el total en los dos campos, el TXT declara 250 kg. Con 2,5 y 26
     gana el unitario sin aviso.
   - **Excel:** hoy con «Peso»=30 y «Peso neto»=25 en 10 unidades gana
     «Peso» como unitario (300 kg, sin aviso), y «Peso total» le gana a
     «Peso neto». Con varias columnas, el orden es neto > total >
     peso/weight (de una unidad) > bruto. El aviso nombra la columna usada y
     las que se ignoraron.
2. **Un peso que no es número nunca hace desaparecer una fila,** en ninguna
   columna de peso: la fila se conserva con aviso. Hoy, en «Peso unitario»,
   «2,5» como texto saca la fila del FOB sin decir nada; con «Peso total» ya
   avisa.
3. **El peso, con la misma guarda que los importes en el generador:** no
   finito, por encima del tope o que redondea a `0.000` da 400. Hoy `NaN`,
   `inf` y `1e300` llegan al TXT, y `0,0004` sale `0.000`. El control del
   pedido de MARIA-1b (Dev 1) es otra capa: no se pisan.
4. **Subítems: la tolerancia compara lo mismo con lo mismo** (redondeado con
   redondeado, o exacto con exacto). Hoy un ítem de 7 × 2,675 con subítems
   (2 × 2,675), (2,5 × 2,6722) y (2,5 × 2,675) da 400 («suman 18.72 pero el
   ítem declara 18.73»), y antes generaba. Criterio: ningún pedido que
   generaba en `8e819dd` da 400 por esto (sirve un lote al azar, como el del
   subagente).
5. **Grupo en la v2: editar la cantidad nunca deja un producto en 0.** Si el
   total nuevo es menor que la cantidad de productos del grupo, se rechaza
   con el mensaje que ya existe. Hoy 1/1/1 bajado a 2 queda `[1,1,0]` y
   «Generar» se bloquea.
6. **Una sola cuenta.** La validación y el aviso «Gastos a FOB» redondean
   igual que el TXT. Hoy, con grupos, la validación muestra 20,02 y el TXT
   dice 20,01; y el aviso dice 11,01 cuando el TXT trae 11,02.

**Se deja, anotado:**
- El flete con un FOB total que redondea a 0,00 (hallazgo 6).
- El unitario promedio del grupo (hallazgo 9).
- Aduana o tipo de destinación «N/A» que salen por defecto (hallazgo 13).
- La v1 y `/generate_maria_export` divergen del TXT de la v2 en peso y
  centavos (hallazgos 10 y 14). Eso queda en `DECISIONS.md`, para que decida
  Emi.

**Criterios:** rojo antes y verde después en cada punto. El punto 1 se prueba
por `_leer`, con Gemini falso, hasta el TXT: (25, 25) con cantidad 10 da
`QARTKGRNET=25.000` y el aviso. Los dos archivos reales siguen idénticos.
Suite completa en verde.

## Respuestas a tus D (2026-10-07, 13:05 UTC)

- **D22 (peso del lector y del Excel): (a), con dos precisiones.** Decidido
  por la PM (está dentro de MARIA-5).
  - Lector: pide `peso_unitario` y `peso_total_linea`; si viene sólo el total,
    lo divide por la cantidad. La revisión muestra el unitario y el total de
    cada línea, para que Emi lo vea antes de generar.
  - Excel: «peso total» y «peso neto» se dividen por la cantidad; «peso» y
    «weight», de una unidad, como dice la plantilla. **«Peso bruto» no
    entra como neto en silencio:** si es la única columna de peso, se usa
    dividida por la cantidad y sale un aviso («el TXT pide peso neto; se usó
    el bruto»).
  - El Excel es terreno de la Dev 1 (`main.py`, las cargas): tocá sólo el
    mapeo del peso. MARIA-5 no se publica sin esta parte (si no, el «peso
    total» del Excel saldría multiplicado).
- **Lo encontrado de paso:**
  - El 0,5 inventado al guardar ya lo saca MARIA-1b (Dev 1). Al integrar
    vas a tener que resolver ese pedazo de `main.py`: la PM integra MARIA-1b
    y EXCEL-1 apenas cierre su revisión, y vos traés la rama antes de
    entregar.
  - `setGroupField` en `ncm.js` (el total del grupo copiado a cada
    producto, el TXT suma de más): **entra en MARIA-5**, punto 4.
- MARIA-1d no dejó D. Anteriores (D5 a D21): en Git.

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

**Después:** MARIA-6 cuando lleguen los archivos reales del despachante.

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

