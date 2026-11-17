# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Entrega D269: sobre `471db09a` (16:31 UTC)

**Resultado.** Los seis criterios se cumplen en `471db09a` (base `6649ff89`). Hoy, con un renglón «CN» y
otro igual con origen vacío, en blanco, «XX» o «ATLANTIDA» (por `origen` o por `pais_origen`),
`/generate_maria/avisos` no dice nada del origen, dice «los renglones 1 y 2 van en un solo ítem» y le
aplica al 2 el estado de importado (con «XX» o un nombre, también la procedencia); generar frena. Con el arreglo, ese renglón no se junta ni lleva procedencia o
estado por defecto, y los avisos traen el mismo «Item 2: Falta origen/país de origen» u «Origen no
reconocido '…'» con que frena generar. Con orígenes válidos no cambia nada. `producto +16/−16`.

**Lo que decidís vos:**
- **D270. Una procedencia no reconocida se sigue tomando como China.** Dos renglones de la misma
  posición con origen CN, el segundo con procedencia «XX» o «ATLANTIDA»: los avisos dicen «Procedencia no
  reconocida…» y también «los renglones 1 y 2 van en un solo ítem» y el sufijo de valor compartido;
  generar frena (400). Con procedencia «BR» no se juntan, como debe ser. Es D269 por la procedencia:
  la clave de posición la lee con `get_pais_codigo`. Propongo pieza chica: `renglones_por_posicion`
  saltea también un renglón con procedencia escrita no reconocida. No lo hice: fuera de la tarea.
- **Criterio 5, desvío.** Tus filas de «sin estado» y «sin procedencia», tal como están, ya no
  distinguen el sabotaje: con el arreglo, un origen que no se reconoce no lleva ni estado ni procedencia
  por defecto, así que `pais_origen` «  » leído crudo da lo mismo que leído con `strip`. A cada una le
  sumé un segundo renglón con `pais_origen` «  » y `origen` BR, sin procedencia ni estado: con
  `origen_de` es Brasil y lleva el aviso; leído crudo, no. Tus renglones quedan como primer renglón de
  la fila y siguen sin aviso. Si preferís otra forma, decime.

**El arreglo (`a9bdaa61`, `82a94faa`).** La causa es una: los avisos usaban `get_pais_codigo`, que con un
país que no reconoce da 310, y no avisaban del origen. Tres cambios, todos sobre `origen_de`:
- `errores_de_procedencia` pasa a `errores_de_pais`: suma el origen que falta o no se reconoce, con el
  texto de la validación, que ahora la usa en vez de repetirlo. Los avisos la llaman igual que antes.
- `renglones_por_posicion` saltea el renglón sin origen reconocido. **La usa también el generador**
  (`maria_generator.py:1452`): por eso §3 fuerte (criterio 6). Por HTTP no cambia nada, porque la
  validación frena antes; sí cambia llamando al generador directo (riesgos, D268).
- «sin procedencia» pide `pais_reconocido(origen_de(item))`; «sin estado», `codigo_de_pais(...)` fuera de
  `None` y 200 (`codigo_de_pais` da `None` si no lo reconoce; `get_pais_codigo` cae en 310).

### Criterios 1 a 3: el caso

`test_los_avisos_no_toman_un_origen_que_falta_como_china` (`tests/test_generar_maria_txt.py`). El primer
renglón es CN; el segundo, el mismo producto con `(pais_origen, origen)` como dato. Cada fila pide
`/generate_maria` y `/generate_maria/avisos` y compara lo que dice generar con los avisos del origen, de
los renglones juntos y de lo declarado por defecto:
- `(None,"CN")` → genera; «juntos 1 y 2», «procedencia 1, 2», «estado 1, 2» (criterio 3);
- `(None,"")`, `(None,"  ")`, `("",None)`, `("  ",None)` → generar y avisos: «Item 2: Falta origen/país
  de origen»; nada junto; procedencia y estado sólo del 1;
- `(None,"XX")`, `("XX","CN")`, `(None,"ATLANTIDA")`, `("ATLANTIDA",None)` → «Item 2: Origen no
  reconocido '…'», igual en los dos.

Criterio 3 para el TXT: suite completa y `e2e_maria.sh` sobre el SHA (abajo).

### Criterio 4: el rojo con el arreglo revertido

Producto de `6649ff89`, pruebas de `471db09a` (los otros dos casos del origen, verdes: ya pasaban en la base):
```
E   AssertionError: (None, '')
E   assert (['Item 2: Fa...estado 1, 2']) == (['Item 2: Fa..., 'estado 1'])
E     
E     At index 1 diff: ['juntos 1 y 2', 'procedencia 1', 'estado 1, 2'] != ['Item 2: Falta origen/país de origen', 'procedencia 1', 'estado 1']
E     Use -v to get more diff
FAILED tests/test_generar_maria_txt.py::test_los_avisos_no_toman_un_origen_que_falta_como_china
============ 1 failed, 4 passed, 58 deselected, 8 warnings in 4.25s ============
```

### Criterio 5: cada lugar de `origen_de`

`test_cada_lugar_lee_el_origen_que_sale_en_el_txt`, cuatro filas (con el desvío de arriba):
- «clave de posición»: CN, (`pais_origen` «  », `origen` BR) ×2, BR ×4 → `[("310","1.00"),("203","6.00")]`;
- «defensa del grupo»: el par BR con `grupo_id` "1" → `[("203","6.00")]`;
- «sin estado»: (`pais_origen` «  », AR, procedencia AR) y (`pais_origen` «  », BR) → estado sólo del 2;
- «sin procedencia»: (`pais_origen` «  », sin `origen`) y (`pais_origen` «  », BR) → procedencia sólo del 2.

Lo que vas a hacer al aceptar, ya hecho: cada uno de los siete lugares (los seis y el nuevo de
`renglones_por_posicion`) con `(item.get('pais_origen') or item.get('origen') or '')`, de a uno. Todos
rojos; el primer rojo nombra la fila:

| lugar | rojo |
|---|---|
| validación (`errores_de_pais`) | `('  ', '  ')`, `(None, '  ')`, `'clave de posición'` |
| generador | `('  ', 'BR')`, `'clave de posición'` |
| clave de posición | `'clave de posición'` |
| lo que se junta | `'clave de posición'` |
| defensa del grupo | `'defensa del grupo'` |
| supuesto de procedencia | `'sin procedencia'` |
| supuesto de estado | `'sin estado'` |

Los cinco últimos están en `origen_txt.sh`; los dos primeros los corrí a mano; el guion ya los
cubre con los sabotajes de D263 (sólo `origen`, el blanco que tapa, el TXT con su propio origen).

## Sabotajes (§3)

`origen_txt.sh` pasa de 4 a 13: los cinco lugares de arriba y cuatro del origen tomado como China (se
junta, lleva procedencia, lleva estado, los avisos no dicen el origen). Los casos ahora se detienen en la
primera fila distinta, en el orden de la familia, y la nombran (`_fila_por_fila`): antes la diferencia
de un dict con claves `None` y texto salía cortada y en un orden que dependía de la memoria, y la frase
de un sabotaje aparecía en 7 de 20 semillas. Con 10 y 13: «sabotajes sin rojo: 0».

Anclas que se movieron y seguí: `sabotaje_maria1d.sh:118` (los avisos llaman a `errores_de_pais`; el
sabotaje saca sólo la procedencia), `sabotaje_maria4.sh:98` (el supuesto de estado) y
`sabotaje_maria8.sh:113` (lo que se junta).

`catalogo3.sh` perdió un rojo: «get_pais_codigo vuelve a hacer int() de cualquier tira de cifras»
esperaba `test_un_origen_de_miles_de_cifras_no_rompe_los_avisos_ni_el_txt`, y con el arreglo los avisos
ya no llegan a `get_pais_codigo` con ese origen (lo que se junta lo saltea; la validación frena antes de
generar). El sabotaje sigue dando rojo, en `test_cada_forma_del_pais…[1111…]`: ahí lo apunté
(`471db09a`). Ese caso de las cifras queda como guarda de comportamiento, sin sabotaje propio.

| guion | SHA | resultado |
|---|---|---|
| `origen_txt.sh` | `5de87f20` | 13 ROJO, «sabotajes sin rojo: 0» (también con semillas 10 y 13) |
| `sabotaje_maria1d.sh` | `5de87f20` | «OK: los 8 sabotajes dan rojo por la razón esperada» |
| `sabotaje_maria4.sh` | `5de87f20` | «OK: los 8 sabotajes dan rojo por la razón esperada» |
| `sabotaje_maria8.sh` | `5de87f20` | «OK: los 70 sabotajes dan rojo por la razón esperada» |
| `sabotaje_maria3.sh` | `5de87f20` | «OK: los 32 sabotajes dan rojo por la razón esperada» |
| `catalogo3.sh` | `471db09a` | 65 ROJO, «fallas: 0» |

De `5de87f20` a `471db09a` sólo cambia `catalogo3.sh` (una línea): los otros cinco no se repiten.
`anclas_perdidas.py 5de87f20`: igual que la base (2590 → 2599 medidas; sólo la de siempre,
`limpieza1.sh:135`). No corrí `despacho1b.sh` ni `catalogo_largo2.sh` (Postgres): no anclan nada de lo tocado.

## Revisión

- `/code-review high` y dos adversarios de modelos distintos (esfuerzo alto), sin mi conclusión. Ninguno
  encontró un origen inválido tratado como China ni un cambio con orígenes válidos (uno probó 2000 entradas).
- Atendido: el comentario y el docstring viejos (`82a94faa`); el sabotaje 8 de `maria1d` sacaba también
  el aviso del origen (`d9e50a0a`); ayudantes repetidos entre los casos (`d9e50a0a`); el rojo que
  dependía del azar (`3a1a797b`, `5de87f20`).
- No atendido, con razón: arreglarlo en `clave_de_posicion` (cambia la clave del generador para todos;
  más riesgo que saltear en el que junta); `pais_reconocido` y `codigo_de_pais` repiten la búsqueda
  (cola de limpieza); se calcula `origen_de` dos veces por renglón (despreciable); las anclas de
  otros guiones van en un commit de pruebas antes del guion propio (no reescribo lo subido).

## Puertas

Sobre `471db09a`, en un worktree limpio (`/tmp/cdi-dev2/wt-d269`, sólo el enlace a `config/node_modules`):
```
=== 6202 passed, 110 skipped, 3 xfailed, 109 warnings in 1164.89s (0:19:24) ====
E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.
```
Los sabotajes, arriba.

## Comandos

```bash
VENV=/ruta/al/venv   # el tuyo
PT="env -u DATABASE_URL -u ENVIRONMENT GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=. $VENV/bin/python -B -m pytest -q --no-cov -p no:cacheprovider -W ignore"
# 1. el rojo: producto de 6649ff89, pruebas de 471db09a
R=/tmp/rojo269; git worktree add -f -q --detach $R 471db09a && cd $R && git checkout 6649ff89 -- proyecto_maria
$PT tests/test_generar_maria_txt.py -k origen | grep -E "^E   AssertionError|failed"   # «(None, '')» y «1 failed, 4 passed»
cd - >/dev/null; git worktree remove -f $R
# 2. los casos, verdes en 471db09a
$PT tests/test_generar_maria_txt.py -k origen | tail -1                                 # «5 passed»
# 3. sabotajes (incluye los cinco lugares) y §6
PATH=$VENV/bin:$PATH PY=$VENV/bin/python bash scripts/testing/sabotajes/origen_txt.sh 471db09a | tail -1   # «sabotajes sin rojo: 0»
python3.12 docs/pm/herramientas/chequeo-6.py 6649ff89 471db09a                         # «producto +16/−16», «avisos: 0»
```

chequeo-6, entero:
```
chequeo-6 6649ff89..471db09a: avisos para mirar, no un veredicto
producto +16/−16
arnés +146/−18
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/maria_generator.py: 2400 → 2400
  proyecto_maria/main.py: 12280 → 12280
avisos: 0
```

| commit | qué |
|---|---|
| `a9bdaa61` fix | `errores_de_pais`; lo que se junta y los dos supuestos piden un origen reconocido; CHANGELOG |
| `41160302` test | el caso de los avisos y el de cada lugar; anclas de maria1d, maria4 y maria8 |
| `6fc0b947` test | `origen_txt.sh` suma nueve |
| `82a94faa` fix | el comentario y el docstring |
| `d9e50a0a` test | ayudantes compartidos; el sabotaje 8 de maria1d saca sólo la procedencia |
| `628f34b0` test | los casos muestran sólo las filas distintas |
| `3a1a797b` test | los casos se detienen en la primera fila distinta |
| `5de87f20` test | la frase del sabotaje del blanco |
| `471db09a` test | `catalogo3.sh`: el sabotaje del `int()` espera el caso de las cifras. **Lo que se entrega** |
| `83aecf45` merge | tu rama hasta `46842b02` (sólo `NOW.md`) |
| informe | el commit siguiente |

## Riesgos

- **D268 cambia de forma**: `generate_maria_txt` llamado sin validar, con un origen inválido, ahora no
  junta ese renglón (2 ART en vez de 1); sigue escribiendo 310. Por HTTP no se llega.
- **La pantalla manda «XX» por un origen en blanco**, así que el aviso dice «Origen no reconocido 'XX'»,
  no «Falta origen». Es lo mismo que dice generar, y ya era así.
- **Grupos**: un grupo con orígenes válidos distintos frena al generar y los avisos no lo dicen (ya era
  así; no es un origen tomado como China).
- **Pantalla**: `despachante.js:362` propone el estado 2 por defecto con un origen no reconocido («XX»). Es
  pantalla, no aviso del servidor; no lo toqué.
- **Intermitente**: un test de `test_despacho1b.py` falló una vez con la máquina cargada; solo, verde.
  No es de esta pieza.
- Lo de producción no se midió; la CI deselecciona y Railway no la espera.

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5, rama `claude/dev-maria`, rutina trig_01Ukttby1fc4sGVQfSn1jC9U; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `46842b02` con el merge `83aecf45`). Aceptadas: las de antes (CUIT-GENERAR `29327d2` … D257 (b) `3c7eb14`), D244 (a) y Holanda→423 sobre `b3a3bf69`, D239 (a) sobre `01c28e83`, D263 sobre `9e5960d2`. Entregada, en revisión: D269 sobre `471db09a` (informe: el commit siguiente): los avisos no toman como China un origen que falta o no se reconoce (`errores_de_pais`; lo que se junta y los supuestos piden `pais_reconocido(origen_de(item))`); casos `test_los_avisos_no_toman_un_origen_que_falta_como_china` y `test_cada_lugar_lee_el_origen_que_sale_en_el_txt`; `origen_txt.sh` 13; suite 6202 passed y e2e OK sobre `471db09a`. Abierto para la PM: D270 (procedencia no reconocida se junta como China) y el desvío del criterio 5 (filas de los supuestos con un renglón `blanco_br`). Sin pieza «apenas entregues» en mi canal: al volver, `/respondio`. D268 y la unidad: riesgo escrito (decidido por la PM). Próxima D: D271. Lecciones (además de las del historial de este archivo): la diferencia de un dict con claves `None` y texto sale cortada y en orden de memoria: un caso de familia se detiene en la primera fila distinta y la nombra; un arreglo que corta un camino puede dejar sin rojo el sabotaje de otro guion: correr todos los que anclan lo tocado; una tarea en segundo plano muere a las 2 h: puertas con `setsid nohup` y un vigía; no editar un guion de sabotaje mientras corre; un python que reescribe un archivo antes de correr deja el worktree sucio si falla: worktree nuevo; horas, sólo de `date -u`. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica; subagentes hasta esfuerzo alto, sin consejero, nunca Fable; detener los subagentes después de su informe.
