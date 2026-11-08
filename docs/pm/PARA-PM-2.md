# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## SEGURO-2: **entregada**, producto y pruebas en `d160738` (2026-11-08)

Base `3366ca5`. Lo que SEGURO-1 sólo avisaba ahora frena la generación hasta
que se corrige, en `/generate_maria` (400) y en `/generate_maria/avisos` (el
mismo texto). Hay dos frenos:

1. **El seguro para completar.** Si la factura traía seguro y no se pudo
   leer, no se genera mientras no se complete. El 400 dice: «Seguro: no
   pudimos leerlo de la factura. Completalo en la revisión; si la factura no
   trae seguro, escribí 0.» Cualquier valor escrito en la revisión lo
   completa, 0 incluido. En la revisión ese campo se ve vacío: un 0 a la
   vista parecía leído, y escribir el mismo 0 no disparaba el cambio. Si el
   servidor frena por esto, la pantalla vuelve a la revisión.
2. **El 1 % dejado con un incoterm que ya lleva el seguro en el precio**
   (D30 b). «Dejar el seguro como está» ahora lo marca como dejado. Con CIF
   (o cualquiera de los cinco), ese 1 % frena igual que el calculado. Con
   otro incoterm, dejarlo es elegirlo y genera, aunque las cuentas de ahora
   den otro número. Recalcularlo, escribirlo a mano o el borrado al pasar a
   CIF le sacan la marca.

No cambia lo que sale en el TXT: sólo cuándo no se genera. Un 0 escrito sale
`0.00` como antes, y el 1 % dejado con CFR sale igual que antes.

| SHA | qué |
|---|---|
| `2bfbee9` | fix: el seguro sin completar y el 1 % dejado con CIF frenan la generación + CHANGELOG |
| `e0aa49c` | test: casos del seguro para completar y del 1 % dejado; arnés `seguro2.sh`; anclas de `valor1c`, `separadores1b` y `seguro1` al nombre nuevo |
| `836f131` | merge de tu rama |
| `e464a6e` | fix: el seguro para completar se ve vacío y el 400 vuelve a la revisión |
| `e88435b` | test: esos dos |
| `9949e89` | fix: la revisión usa el mismo predicado de finalize y sólo vacía el seguro |
| `b5cc881` | test: el flete sin leer se ve como vino; las anclas siguen al predicado compartido |
| `6546870` | test: la revisión encuentra el predicado que exporta `finalize.js` |
| `332750c` | fix: el porqué del freno en dos líneas |
| `d160738` | merge de tu rama (sólo docs) |
| este commit | docs: este informe |

`producto +46/−20`. Suma 26 netas, y estas son las razones:

- el freno nuevo en el servidor: la constante del texto, los dos campos del
  pedido y las ramas de `_seguro_por_corregir`, que reemplaza a
  `_seguro_calculado_viejo`;
- las dos marcas en el pedido y la de dejado, que se pone y se saca en los
  cuatro lugares donde cambia el seguro;
- la vista vacía en la revisión (`valorEnLaRevision`) y la vuelta a la
  revisión ante el 400.

## Decisiones

**D125.** Un 1 % que llega sin marcas (ni `seguro_calculado` ni
`seguro_dejado`) genera 200 con CIF. Es el caso de un cliente viejo, de la
API sin la pantalla, o de alguien que lo escribió a mano. El servidor no
tiene cómo distinguirlo de una factura que trae exactamente el 1 %.

- (a) aceptarlo así: el freno mira cómo llegó el seguro, no cuánto vale;
- (b) que el servidor recalcule el 1 % y frene si coincide. Frenaría
  facturas reales que traen exactamente el 1 %, y la persona no tendría
  cómo pasar.

Recomiendo (a). Con (b), el falso rojo no tiene salida; con (a), el agujero
necesita saltear la pantalla.

**D126.** La nota «si la factura no trae seguro, escribí 0» del 400 sale
también con FOB o CFR. Ahí un 0 está bien, pero el sistema podría ofrecer
calcular el 1 %.

- (a) dejarla igual para los cinco incoterms;
- (b) con FOB y CFR, decir además que se puede calcular en «Ajustes y
  seguro».

Recomiendo (a): un texto para todos, y el botón de calcular ya está en esa
pantalla. (b) es un cambio de texto chico, si lo querés.

## Riesgos

- **La marca es la palabra del cliente.** `seguro_para_completar` y
  `seguro_dejado` los manda la pantalla. Un cliente que no los manda genera
  como antes de SEGURO-2: es D125 y lo mismo que ya pasaba con
  `seguro_calculado`.
- **Con CIF y el 1 % dejado, el 400 dice «lo calculó el sistema»** y lleva a
  `validating`, que es el mismo texto y el mismo camino que el calculado. Es
  cierto (el número lo calculó el sistema), pero no menciona que se dejó.
- **`borrarSeguroCalculado`**, al pasar a CIF, agrega el seguro a
  `campos_sin_leer`. Desde ahí cuenta como «no se pudo leer», aunque la
  factura no lo trajera, y para generar hace falta escribir un valor (0
  sirve). Es la dirección segura: pide un dato en vez de dejar pasar el 1 %.
- **El `startsWith('Seguro: no pudimos leerlo')` de `finalize.js`** repite
  el comienzo de la constante del servidor. Si alguien cambia ese texto, el
  400 se queda en la pantalla de generar en vez de volver a la revisión. Lo
  cubre `test_si_el_servidor_pide_completarlo_se_vuelve_a_la_revision`, que
  usa el texto del servidor copiado: falla si cambia la pantalla, no si
  cambia el servidor.
- **La revisión depende de `finalize.js`**: llama a `CDI.seguroSinLeer`. Si
  la exportación se pierde, la revisión tira un error al abrirse. Lo cubre
  `test_la_revision_tiene_el_predicado_de_finalize`; sin ese caso, quitar la
  exportación daba todo verde (lo encontré yo, abajo).
- **La firma del pedido incluye los campos nuevos.** Un cambio de marca
  vuelve a pedir las cuentas, como cualquier otro cambio del pedido.
- **«abc no es un importe» con el seguro para completar** frena por el
  importe primero (400 de SEPARADORES-1b) y se queda en la pantalla de
  generar, como antes.
- **Con CIF y el seguro sin leer, la pantalla de valor muestra tres
  instrucciones** (la nota, el aviso y el 400), que dicen lo mismo con otras
  palabras. Es un riesgo de UX y no lo toqué.
- **Sólo API:** dejado + seguro 0 + CIF da 400 «lo calculó el sistema». La
  pantalla no puede armar ese pedido: escribir el 0 saca la marca.

## Hallazgos de la autorrevisión

| quién | modelo y esfuerzo | hallazgo | qué hice |
|---|---|---|---|
| adversario | Sonnet alto | MEDIA: escribir el seguro sin leer no tenía prueba de que lo completa | `e88435b`: `test_escribir_el_seguro_sin_leer_lo_completa` + sabotaje |
| adversario | Sonnet alto | BAJA: el seguro sin leer se veía 0 en la revisión | `e464a6e` + caso + sabotaje |
| adversario | Sonnet alto | BAJA: `borrarSeguroCalculado` lo marca «sin leer» | riesgo, arriba |
| adversario | Sonnet alto | INFORMATIVA: el freno depende de lo que manda el cliente | riesgo, arriba (D125) |
| adversario | Opus alto | MEDIA: el 1 % sin marcas genera 200 con CIF | D125 |
| adversario | Opus alto | MEDIA: el 0 a la vista | `e464a6e` (el mismo de arriba) |
| adversario | Opus alto | BAJA: el 400 del seguro para completar terminaba en la pantalla de generar | `e464a6e`: vuelve a la revisión + caso + sabotaje |
| adversario | Opus alto | BAJA: «escribí 0» también con FOB o CFR | D126 |
| adversario | Opus alto | BAJA, sólo API: dejado + 0 + CIF da 400 | riesgo, arriba |
| adversario | Opus alto | INFORMATIVO: con un importe roto frena primero por SEPARADORES-1b | riesgo, arriba |
| `/code-review` | high | `borrarSeguroCalculado` marca el seguro como sin leer | riesgo, arriba |
| `/code-review` | high | el freno depende del booleano del cliente | riesgo, arriba (D125) |
| `/code-review` | high | el `startsWith` repite la constante | riesgo, arriba |
| `/code-review` | high | dejado + CIF dice «lo calculó el sistema» y lleva a `validating` | riesgo, arriba |
| `/code-review` | high | el predicado del seguro sin leer, repetido en la revisión | `9949e89`: la revisión usa el de `finalize.js` |
| `/code-review` | high | la vista vacía alcanzaba también al flete y los gastos sin leer | `9949e89`: sólo el seguro; caso `[flete_sin_leer]` |
| `/code-review` | high | dos `if` iguales en `onFieldChange` | `9949e89`: uno solo |
| `/code-review` | high | instrucción triple con CIF | riesgo de UX, arriba |
| `/security-review` | — | 0 hallazgos con confianza ≥ 8 | — |
| yo | — | sin la exportación de `CDI.seguroSinLeer` todo quedaba verde (`429 passed`); en el navegador, la revisión tiraba un error | `6546870`: `test_la_revision_tiene_el_predicado_de_finalize`; su rojo: `TypeError: undefined is not a function` |

## Rojos antes del arreglo

Producto de `3366ca5` con los casos de `d160738` (`test_seguro2`,
`test_seguro1` y `test_valor1c`), en un worktree aparte:
`22 failed, 85 passed, 5 warnings in 32.21s`, salida 1.

| caso | por qué falla en la base |
|---|---|
| `test_un_seguro_sin_leer_no_genera_y_los_avisos_lo_dicen` `[CIF-]`, `[CIF-0]`, `[FOB-]`, `[CFR-14.88]` | `assert 200 == 400`: genera el TXT |
| `test_el_uno_por_ciento_dejado_no_genera_con_cif` | `assert 200 == 400` |
| `test_el_pedido_dice_si_el_seguro_sigue_para_completar`, los 4 | `JSONDecodeError`: el campo no existe y no sale JSON |
| `test_si_el_servidor_pide_completarlo_se_vuelve_a_la_revision` | `assert None == 'review'` |
| `test_la_revision_tiene_el_predicado_de_finalize` | error de node: `window.CDI.seguroSinLeer` no existe |
| `test_un_campo_sin_leer_se_ve_vacio_en_la_revision`, los 4 | `no está valorEnLaRevision en review.js` |
| `test_la_revision_muestra_vacio_el_seguro_sin_leer_y_lo_deja_en_0` | `no está valorEnLaRevision en review.js` |
| `test_el_pedido_dice_si_el_seguro_se_dejo` | `assert [None] == [True]` |
| `test_el_dejado_se_borra_al_pasar_a_cif_y_queda_para_completar` | `assert (14.88 == '')` |
| `test_recalcularlo_ya_no_es_el_dejado` | `'seguro_dejado' not in {'seguro': 93.13, 'seguro_dejado': True, 'seguro_calculado': True}` |
| `test_escribirlo_a_mano_ya_no_es_el_dejado` | `{'seguro': 15...dejado': True} == {'seguro': 15}` |
| `test_seguro1::test_con_cif_y_un_seguro_sin_leer_la_nota_lo_pide` | `'Con CIF el s... la revisión.' == 'Con CIF el s...o, escribí 0.'` |
| `test_valor1c::test_dejarlo_lo_marca_como_dejado_y_pide_las_cuentas_de_nuevo` | `{'seguro': 14.88} == {'seguro': 14...dejado': True}` |

Pasan en la base, y tienen que pasar: `test_el_cero_escrito_a_proposito_genera`,
`test_el_uno_por_ciento_dejado_genera_con_cfr` y
`test_escribir_el_seguro_sin_leer_lo_completa` (la revisión ya marcaba un campo
escrito como completado). Son los que vigilan que el freno no alcance de más;
sus rojos salen en los sabotajes «un 0 también frena», «el dejado se compara
con las cuentas de ahora» y «escribirlo no lo completa».

## Puertas

Todas sobre `d160738`, el último commit de producto y pruebas (este informe
sólo agrega docs). Corrieron desde un worktree limpio y de a una, y los logs
están en el scratchpad.

| puerta | salida exacta |
|---|---|
| `compileall -q proyecto_maria` | `compileall 0` |
| suite, SQLite (`ENVIRONMENT=test`, `--timeout=300`) | `5294 passed, 335 skipped, 3 xfailed, 98 warnings in 1030.50s (0:17:10)`, salida 0 |
| suite como la CI (`ENVIRONMENT=testing`, sin `DATABASE_URL`) | `5294 passed, 335 skipped, 3 xfailed, 92 warnings in 1038.71s (0:17:18)`, salida 0 |
| `test_seguro2` + `test_seguro1` + `test_valor1` + `test_valor1c` + `test_maria7_rechazos_24_10` | `194 passed, 3 warnings in 49.42s` |
| sabotajes `seguro2.sh` | `BASE \| 78 passed, 5 warnings in 20.65s`, 19 `ROJO`, `sabotajes sin rojo: 0` |
| sabotajes `seguro1.sh` | `BASE \| 52 passed, 5 warnings in 15.55s`, 12 `ROJO`, `sabotajes sin rojo: 0` |
| sabotajes `sabotaje_valor1c.sh` | `OK: los 25 sabotajes dan rojo por la razón esperada`, salida 0 |
| sabotajes `sabotaje_separadores1b.sh` | salida 1, idéntica a la de la base `3366ca5`: las dos fallas previas (`factura_multiplica` y el patrón 3 de `montos_ar.js`, roto desde `4f2045f`), y el corte por el patrón roto deja sin correr el 3b y del 4 al 10. Abajo, la corrida sin el 3 |
| grep de historia de §6 | vacío |

`seguro2.sh`, entero:

```
Preparing worktree (detached HEAD d160738)
BASE  | ======================= 78 passed, 5 warnings in 20.65s ========================
ROJO  | el servidor no mira si sigue para completar: «FAILED tests/test_seguro2.py::test_un_seguro_sin_leer_no_genera_y_los_avisos_lo_dicen[CIF-]» «FAILED tests/test_seguro2.py::test_un_seguro_sin_leer_no_genera_y_los_avisos_lo_dicen[FOB-]» 
ROJO  | un 0 también frena: «FAILED tests/test_seguro2.py::test_el_cero_escrito_a_proposito_genera» 
ROJO  | generar sólo avisa: «FAILED tests/test_seguro2.py::test_un_seguro_sin_leer_no_genera_y_los_avisos_lo_dicen[CIF-]» «FAILED tests/test_seguro2.py::test_el_uno_por_ciento_dejado_no_genera_con_cif» 
ROJO  | el pedido no dice que sigue para completar: «FAILED tests/test_seguro2.py::test_el_pedido_dice_si_el_seguro_sigue_para_completar[sin_leer]» 
ROJO  | escribirlo no lo completa: «FAILED tests/test_seguro2.py::test_escribir_el_seguro_sin_leer_lo_completa[0-True]» «FAILED tests/test_seguro2.py::test_escribir_el_seguro_sin_leer_lo_completa[15-True]» 
ROJO  | el seguro sin leer se ve en 0: «FAILED tests/test_seguro2.py::test_un_campo_sin_leer_se_ve_vacio_en_la_revision[sin_leer]» 
ROJO  | finalize no exporta el predicado: «FAILED tests/test_seguro2.py::test_la_revision_tiene_el_predicado_de_finalize» 
ROJO  | la revisión no lo usa: «FAILED tests/test_seguro2.py::test_la_revision_muestra_vacio_el_seguro_sin_leer_y_lo_deja_en_0» 
ROJO  | otro monto sin leer también se vacía: «FAILED tests/test_seguro2.py::test_un_campo_sin_leer_se_ve_vacio_en_la_revision[flete_sin_leer]» 
ROJO  | el 400 se queda en la pantalla de generar: «FAILED tests/test_seguro2.py::test_si_el_servidor_pide_completarlo_se_vuelve_a_la_revision» 
ROJO  | el dejado no frena con CIF: «FAILED tests/test_seguro2.py::test_el_uno_por_ciento_dejado_no_genera_con_cif» 
ROJO  | el dejado se compara con las cuentas de ahora: «FAILED tests/test_seguro2.py::test_el_uno_por_ciento_dejado_genera_con_cfr» 
ROJO  | el pedido no dice que se dejó: «FAILED tests/test_seguro2.py::test_el_pedido_dice_si_el_seguro_se_dejo» 
ROJO  | dejarlo no lo marca: «FAILED tests/test_valor1c.py::test_dejarlo_lo_marca_como_dejado_y_pide_las_cuentas_de_nuevo» 
ROJO  | el dejado no se borra al pasar a CIF: «FAILED tests/test_seguro2.py::test_el_dejado_se_borra_al_pasar_a_cif_y_queda_para_completar» 
ROJO  | el borrado deja la marca: «FAILED tests/test_seguro2.py::test_el_dejado_se_borra_al_pasar_a_cif_y_queda_para_completar» 
ROJO  | recalcularlo deja la marca: «FAILED tests/test_seguro2.py::test_recalcularlo_ya_no_es_el_dejado» 
ROJO  | escribirlo a mano deja la marca: «FAILED tests/test_seguro2.py::test_escribirlo_a_mano_ya_no_es_el_dejado» 
ROJO  | la nota no pide el 0: «FAILED tests/test_seguro1.py::test_con_cif_y_un_seguro_sin_leer_la_nota_lo_pide» 
sabotajes sin rojo: 0
rc=0
```

`sabotaje_separadores1b.sh` corta en el primer patrón que no encuentra. Su
sabotaje 3 (`montos_ar.js`) no encuentra el suyo desde `4f2045f`, así que en
la base y acá no corrían ni el 3b ni del 4 al 10, y ahí está el ancla 8 que
`e0aa49c` movió. Para verla corrí una copia del arnés sin los sabotajes 3 y 3b
(borrados con `sed`, en el scratchpad, sin subirla), sobre `d160738`:

```
FALLA  factura_multiplica (la misma falla previa: 5 failed, todos de test_en_la_factura_con_grupos_de_espacio_tambien)
ROJO   factura_ignora_la_pista: 3 failed, 262 passed, 5 warnings in 48.96s
ROJO   factura_grupo_con_espacio: 5 failed, 260 passed, 6 warnings in 49.55s
ROJO   pedido_monto_cero: 5 failed, 260 passed, 5 warnings in 49.41s
ROJO   pedido_ajuste_nada: 7 failed, 258 passed, 3 warnings in 49.16s
ROJO   servidor_lee_como_python: 25 failed, 240 passed, 3 warnings in 49.74s
ROJO   flete_solo_numero: 13 failed, 252 passed, 4 warnings in 50.21s
ROJO   generar_sin_normalizar: 1 failed, 264 passed, 3 warnings in 51.60s
ROJO   avisos_sin_mirar: 4 failed, 261 passed, 3 warnings in 51.72s
ROJO   blanco_no_es_cero: 1 failed, 264 passed, 3 warnings in 51.46s
FALLAN 1 sabotajes
rc=1
```

El ancla 8 nueva (`generar_sin_normalizar`) da rojo. La única falla es la
previa. El 3b no lo corrí: no sé si su patrón sigue vivo. Arreglar el arnés
de SEPARADORES-1b no es de esta pieza.

No corrí `smoke_friccion.sh` ni `ataque_aislamiento.sh`. La pieza agrega un
400 a la generación y cambia dos pantallas, y eso lo miden los casos y los
sabotajes. No toca sesión, permisos ni datos de otro usuario.

chequeo-6, entero:

```
chequeo-6 3366ca5..d160738: avisos para mirar, no un veredicto
producto +46/−20
  AVISO producto suma 26 líneas netas: el informe dice por qué (§6: más de 20)
arnés +343/−9
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12063 → 12072
  proyecto_maria/static/v2/screens/finalize.js: 1425 → 1436
  AVISO creció una función de más de 150: proyecto_maria/static/v2/screens/finalize.js:9 <anónima> 1417 → 1428, 2 en su propio cuerpo (§6: lo nuevo va aparte)
  proyecto_maria/static/v2/screens/review.js: 1175 → 1181
  AVISO creció una función de más de 150: proyecto_maria/static/v2/screens/review.js:7 <anónima> 1169 → 1175, 3 en su propio cuerpo (§6: lo nuevo va aparte)
avisos: 3
```

Los tres `AVISO`:

- **26 netas:** explicado arriba, junto a la tabla de SHAs.
- **Las dos funciones de más de 150 líneas** son la IIFE que envuelve cada
  archivo entero (`finalize.js:9` y `review.js:7`). Lo nuevo va en
  funciones aparte (`valorEnLaRevision`) o en líneas dentro de las que ya
  cambian el seguro (`dejarSeguro`, `calcularSeguro`,
  `borrarSeguroCalculado`, `buildMariaRequest`, `onFieldChange`). Partir la
  IIFE no es de esta pieza.

## Comandos

```bash
git fetch origin claude/dev-maria && git checkout d160738
<venv>/bin/python -m pytest -q --no-cov -p no:randomly tests/test_seguro2.py tests/test_seguro1.py tests/test_valor1c.py   # todo passed
PY=<venv>/bin/python bash scripts/testing/sabotajes/seguro2.sh d160738   # 19 ROJO, «sabotajes sin rojo: 0»
PY=<venv>/bin/python bash scripts/testing/sabotajes/seguro1.sh d160738   # 12 ROJO, «sabotajes sin rojo: 0»
bash scripts/testing/sabotaje_valor1c.sh d160738 <venv>                  # «OK: los 25 sabotajes dan rojo por la razón esperada»
```

## Archivos de producto tocados

- `proyecto_maria/main.py`
- `proyecto_maria/static/v2/screens/finalize.js`
- `proyecto_maria/static/v2/screens/review.js`
- `CHANGELOG.md`

Sigo con AVISOS-1.

/compact conservar: Dev MARIA (session_01C8gCBjvn36wnYC6qG2Sixi), rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM session_01B7FVQspcEHF7PqNv797wNM con send_message next. SEGURO-2 entregada, producto y pruebas en d160738 (base 3366ca5), D125 y D126 abiertas. Próxima D libre D127. Sigue AVISOS-1 (D123 a: el rechazo de exportación después de `_textos_como_van_al_txt` en los dos endpoints, con su caso), después EMAIL-1, CONEXIONES-1, OBSERVABILIDAD-1, ORG-1+D40 y D102. Corte de rutinas 2026-11-08 15:50 UTC. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; TXT y proforma reales nunca en el repo.
