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

## Retoma 2026-10-19 — devolución MARIA-5d

Emi pidió continuar el plan con PM y subagentes. Se retoma en
`codex/pm-retoma-txt`, desde `99f3625`; no se publica ni se reactivan desde
Codex las rutinas de las sesiones anteriores. La rama de Dev conservada es
`origin/claude/dev2-maria`, `d22ff1a`.

**Problema reproducido en `d22ff1a`:** con 10 unidades y una columna de
peso bruto de una unidad de 3 kg, los encabezados `Peso bruto unit (kg)`,
`Gross weight unit (kg)` y `Unit gross weight` devuelven `peso_unitario=0.3`,
en vez de 3. El aviso afirma que se dividió el peso de toda la línea.
Los 65 focales existentes pasan: no cubren este borde.

**Tarea cerrada:** completar MARIA-5d sobre `d22ff1a` en una rama nueva.
Reconocer esas variantes inequívocas de una unidad, también con mapeo
guardado. Mantener la precedencia de neto sobre bruto y las guardas de total,
línea y plurales. No ampliar a otro lector ni al generador de exportación.

**Segunda revisión:** `b3fd518` resuelve las tres variantes, pero introduce
una regresión con `Unit gross weight per line` y `Unit gross weight line`:
antes eran totales y pasan a unitarios. PM reprodujo por AST ambos cambios.
Se adopta como bloqueo: una columna que dice por línea no se multiplica
por la cantidad. Corregir en la misma función y conservar 30 kg de línea
con 10 unidades, en vez de producir 300 kg. Sin cambiar otros clasificadores.

**Aceptación:** rojo antes y verde después por la ruta de subida Excel;
con 10 unidades se conservan 3 kg por unidad y 30 kg por línea, con aviso de
bruto y sin afirmar que se dividió. Un bruto de toda la línea con `total`,
`unidades` o `units` sigue dividiéndose. Añadir al menos un negativo que
falle si se convierte todo bruto en unitario. Focales MARIA-5d, peso Excel,
devolución y archivos de referencia; suite completa y puertas de pantalla
sólo cuentan si se ejecutaron sobre el SHA entregado. El fallo de sabotaje
`excel1.sh` conservado al pausar se debe clasificar, no ocultar.

**Entrega:** código, pruebas e informe por separado, SHA exacto, resultados
y limitaciones del entorno. Cero documentos reales en pruebas o informes.
Si el arreglo requiere cambiar el significado del peso o un archivo de
referencia, devolver D a la PM antes de hacerlo. Después de entregar,
esperar revisión independiente; ORG-1 conserva su orden posterior.

## Siguiente autorizada por Emi — DOC-1 (2026-10-19)

Emi eligió primero bloquear el TXT incorrecto, sin sumar exportación
completa. Base: rama de retoma PM después de la consigna, en una rama
aislada de MARIA-5d. El cierre de pesos sigue primero y no se mezclan las
entregas. Esta pieza es Fase 1, antes de ORG-1.

**Problema demostrado:** el lector descarta tipo documental y destinación;
la v2 siempre usa `/generate_maria`, y una EC02 puede salir con indicador
de importación. No está demostrada una mezcla entre dos PDFs.

**Alcance mínimo:**
1. Pedir clasificación documental en la misma lectura (sin otra llamada
   ni coste adicional), conservarla y distinguir una factura comercial
   admitida de declaración/despacho, exportación u otro documento. Una
   lectura ambigua no se presenta como factura válida. No inferir por
   nombre de archivo ni inventar número/fecha.
2. Rechazar documentos no admitidos con respuesta y mensaje claros antes
   de ofrecer ítems para generar. No reintentar ni caer en un fallback
   que elimine el rechazo. No tocar rutas de exportación.
3. Guarda de servidor: una destinación EC* explícita nunca pasa por el
   generador de importación, incluidos avisos y llamadas directas. No
   cambiar el formato de TXT de una importación válida.
4. Al fallar o rechazarse una nueva subida B, la pantalla no muestra la
   operación A como resultado de B ni permite generarla por ese recorrido.
   Una respuesta antigua de A no puede pisar la más nueva B. Dar un camino
   claro para empezar de nuevo; no borrar operaciones guardadas del usuario.

**Aceptación sintética:** factura de importación válida sigue funcionando;
despacho EC02 rechazado sin TXT; clase desconocida/ausente no se acepta
como factura; EC* enviada directamente al servidor rechazada; dos subidas
A→B no arrastran operación/ítems/NCM y B rechazada no revive A. Rojo antes,
verde después y negativo que detecte desactivar las guardas. Los mocks de
lectura de facturas anteriores se actualizan sólo para incluir la nueva
clasificación válida, sin debilitar sus aserciones.

**Devolución de revisión, 2026-10-20 (resuelta en `c2d41b4`):** además del borrador, invalidar el
snapshot de Deshacer NCM al cambiar de operación. Se demostró con el JS
real: batch A → nueva operación → NCM → Ctrl+Z restaura A, mientras
`lastSnapshot` siga vivo (10 s). La ruta sin ítems está bloqueada en Review,
pero una nueva factura válida C puede alcanzar NCM y recibir A. Elección
PM: atar los cuatro snapshots y su restauración a la referencia de
`CDI.state`; mantener Deshacer al volver Revisar/NCM en la misma operación.
Prueba discriminante antes/después, incluyendo C con sus propios ítems.
No reescribir el mecanismo de Deshacer ni ampliar funcionalidades.

**Entrega:** SHA y diff separados de MARIA-5d, pruebas y reporte propios;
suite proporcional y pantallas por herramientas permitidas. Declarar lo
no ejecutado. Cero PDFs/TXTs/datos reales o llamadas a Gemini/terceros.
Frenar con D si requiere cambiar contrato del Kit, formatos de archivo,
clasificar con otra llamada pagada o implementar exportación completa.

## Último veredicto

**MARIA-5, CATALOGO-NCM-1 y SUBITEMS-1 aceptadas sobre `df4de22`**
(2026-10-07, 22:05 UTC). Integradas en `0e57f70`.

**Lo que corrió la PM:**
- Rojo antes: `test_devolucion2_maria5_ncm.py` y `test_subitems1.py` con el
  producto de `88564ec`: `21 failed, 24 passed`.
- Suite: `1526 passed, 102 skipped, 2 xfailed`.
- e2e: «E2E MARIA OK».

**El subagente (Sonnet medio)** repitió los scripts que habían reproducido
cada hallazgo:
- Los diez puntos están arreglados.
- En 5000 pedidos al azar contra el generador y 1100 contra
  `/generate_maria`, ningún TXT cambia, salvo el número de «Item» en los
  errores de subítems con grupos (a propósito).
- Los archivos reales salen idénticos.

**Antes de publicar falta un punto: MARIA-5d.** La próxima publicación espera
este punto; va antes que la pieza siguiente.

1. **«Peso bruto unitario» se divide por la cantidad.**
   - `_clase_de_peso` devuelve «bruto» antes de mirar «unit» o «unidad», y el
     bruto siempre se divide. «Peso bruto unitario» = 3 en 10 unidades
     declara 0,3 kg por unidad: el TXT dice 3 kg la línea, en vez de 30.
   - Además el aviso dice «es de toda la línea; se dividió», y el encabezado
     dice lo contrario.
   - Pasa igual con «Gross weight per unit» y con un mapeo guardado.
   - Cómo tiene que quedar: un bruto que dice «unitario», «unit», «per
     unit» o «por unidad» es bruto **de una unidad**. No se divide, va
     último y lleva el aviso de bruto.
2. **De paso, menos ruido:** «Peso kg/u», «Peso c/u» y «Peso U.» dicen que
   son por unidad. Que no salgan como dudosas.

**Criterios:**
- Rojo antes y verde después.
- Los dos archivos reales, idénticos.
- La e2e y las tres pantallas dan OK.
- Suite completa.

**Se deja, anotado:**
- Con un grupo antes, los errores de peso y estado siguen con el número de
  línea del TXT, y los de subítems con el de la pantalla. Va a MARIA-6, que
  es de identificadores.
- Los errores de subítems de MARIA-1b (por ejemplo, NaN) salen en la
  pantalla final. El panel ya los marca antes.
- La baja no avisa con formas raras (`8517-12-31-000-X`, `851712310`), pero
  generar las frena igual.
- «Kg», «Net Wt» y «Unit Wt» sin mapeo guardado no se detectan. Ya pasaba.
- Dos columnas dudosas distintas no avisan que no coinciden.

Contexto: entregaste en ~65 % y compactaste (23 %).

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

## Después de MARIA-5d — ORG-1: invitaciones de un estudio (Fase 2)

Escrita el 2026-10-07, 22:05 UTC. MARIA-6 espera los archivos reales del
despachante, así que tu siguiente pieza es de la Fase 2 (`ROADMAP.md`).

**Qué arregla (C7 de `AUDITORIA-2026-10-06.md`):**
- Las invitaciones a un estudio funcionan.
- Respetan el tope de usuarios del plan.
- Quedan atadas al email invitado: otra persona no puede usar el link.

**Primero:** leé el código de invitaciones y organizaciones, y escribí en tu
`PARA-PM-2.md` qué hay hoy y qué falla, con un plan corto y las D que haga
falta. Es permisos: revisión fuerte (Sonnet y Opus, alto). Nada contra
producción ni correo real.

**Criterios:**
- Rojo antes y verde después en cada falla.
- Una prueba de aislamiento: un miembro de un estudio no ve nada de otro.
- La e2e da OK.
- Suite completa.
