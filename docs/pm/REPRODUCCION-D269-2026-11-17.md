# D269: reproducción de la PM

Entrega `471db09a` (informe `b0dd5079`, canal `PARA-PM-2.md`). Base `6649ff89`. Producto:
`maria_generator.py` y `main.py`. `errores_de_procedencia` pasa a `errores_de_pais`, que suma el origen
que falta o no se reconoce, con el mismo texto con que frena generar. La clave de posición saltea el
renglón cuyo origen no se reconoce, y los supuestos «sin procedencia» y «sin estado» leen el país con
`origen_de`. Con un origen vacío o «XX», ningún aviso lo trata como China.
Veredicto: **aceptada sobre `471db09a`**, integrada con `9ec581db`.

## Corrido por la PM (2026-11-17, hasta las 17:38 UTC)

| Qué | Resultado |
|---|---|
| `chequeo-6.py 6649ff89 471db09a` | producto +16/−16, arnés +146/−18, historia vacía, `avisos: 0`, como en el informe |
| rojo con el arreglo revertido (producto de `6649ff89`, pruebas de `471db09a`, `-k origen`) | `1 failed, 4 passed`: `test_los_avisos_no_toman_un_origen_que_falta_como_china`, «['juntos 1 y 2', 'procedencia 1', 'estado 1, 2'] != ['Item 2: Falta origen/país de origen', 'procedencia 1', 'estado 1']» |
| suite completa sobre `471db09a` | `6202 passed, 110 skipped, 3 xfailed` en 18:39, salida 0 |
| `e2e_maria.sh` sobre el SHA, primera corrida | no corrió: «fatal: cannot change to '/tmp/cdi-pm/wt-e2e'» (faltaba el worktree de la PM, no es de la pieza) |
| `e2e_maria.sh` sobre el SHA, 17:38, con el worktree rehecho | «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.» |
| unión con la rama de PM | `git diff --stat b0dd5079 9ec581db` fuera de `docs/pm`, `.claude` y `AGENTS.md`: vacío. El e2e del SHA vale para la unión |
| `sabotajes/origen_txt.sh` (copia del SHA) | base 63 passed, 13 `ROJO`, «sabotajes sin rojo: 0», salida 0 |
| `sabotaje_maria1d.sh` | «OK: los 8 sabotajes dan rojo por la razón esperada» |
| `sabotaje_maria3.sh` / `maria4` / `maria8` | «OK: los 32…», «OK: los 8…», «OK: los 70…» |
| `catalogo3.sh` | «fallas: 0», salida 0 |
| `anclas_perdidas.py` base y SHA | iguales: la única PERDIDA es `limpieza1.sh:135` (`ci.yml`), como en la base |
| diff fuera de `docs/pm` | `CHANGELOG.md` (+4), `maria_generator.py`, `main.py`, sabotajes `maria1d/4/8`, `catalogo3.sh`, `origen_txt.sh`, `tests/test_generar_maria_txt.py`. Nada fuera de la tarea |

Las anclas que movió son los mismos sabotajes, no más flojos: el de avisos en `maria1d` filtra los
errores de procedencia de `errores_de_pais`; el de «sin estado» en `maria4` va a `codigo_de_pais`; el de
grupos en `maria8` mantiene el chequeo de origen; en `catalogo3` la falla esperada de
«`get_pais_codigo` int() de cualquier tira» pasa al caso de cada forma del país, porque los avisos ya no
llegan a `get_pais_codigo` con un origen no reconocido.

## Cada lugar de `origen_de`, revertido de a uno

Cambié `origen_de(item)` por la lectura cruda (`pais_origen or origen`, sin `strip`) en cada uno de los
siete lugares, de a uno (`-k origen`, 5 casos). Los siete dan rojo:

| Lugar revertido | Rojo |
|---|---|
| validación | `test_generate_maria_valida_el_origen_que_sale_en_el_txt`, `test_los_avisos_no_toman…` y la fila «clave de posición» |
| clave de posición | fila «clave de posición» de `test_cada_lugar_lee_el_origen_que_sale_en_el_txt` |
| lo que se junta en los avisos | fila «clave de posición» |
| defensa del grupo | fila «defensa del grupo» |
| generador | `test_generate_maria_valida…` y la fila «clave de posición» |
| «sin procedencia» | fila «sin procedencia» |
| «sin estado» | fila «sin estado» |

Sin revertir nada: `5 passed`. `test_cada_lugar…` pasa sobre la base: es guarda, y lo prueba esta tabla.

## Mis negativos (avisos y generar, por el endpoint)

| Entrada | generar | avisos |
|---|---|---|
| `pais_origen` «  cn  » y `origen` BR | 200, 310, 2.00 | «juntos 1 y 2» |
| `pais_origen` tabulador / espacio duro y `origen` BR | 310 y 203 | no los junta |
| `origen` «200» o «AR» sin estado | 400 «el origen es argentino; elegí el estado» | estado sólo del ítem 1 |
| `origen` «999» | 200, 999 (OTROS PAISES, código válido de la tabla) | — |
| `pais_origen` «Brasil» y `origen` CN | 203 (gana `pais_origen`) | no los junta |

Ningún aviso contradice a generar. Origen AR sin estado: los avisos no lo anticipan (riesgo abajo).

## Adversario (Sonnet, alto, sin red)

~3700 entradas, base contra nueva. Ningún hallazgo de la pieza. Los ~1000 casos válidos con 200 dan el
TXT igual byte a byte; avisos y TXT no se contradicen en ninguno con el código nuevo (la base tenía ~120).
Lo que encontró ya estaba en `main` (`1cc0a500`):

1. `grupo_id=[1]` da 500 «unhashable type: 'list'» al generar. Sólo por API.
2. Una procedencia de renglón no reconocida con origen CN se sigue juntando en los avisos (D270).
3. Origen AR sin estado, o con estado 4: los avisos no anticipan el 400 de generar.

## Decidido por la PM y riesgos escritos

- **D270** (procedencia de renglón no reconocida, juntada en los avisos): riesgo escrito, no pieza. No hay
  camino de hoy: una procedencia de la operación que no está en la tabla da 400 en
  `_items_con_procedencia` (`main.py`) antes de avisos y de generar, y la pantalla no manda procedencia
  por renglón. Generar frena igual. Si una pieza manda procedencia por renglón, lleva este caso.
- **Desvío del criterio 5** (segundo renglón `pais_origen` «  » con `origen` BR en las filas de los
  supuestos): aceptado. Con el arreglo, un origen no reconocido ya no lleva supuestos, y sin ese renglón
  la fila no distingue el sabotaje.
- **D268** cambia de forma: `generate_maria_txt` llamado sin validar, con un origen inválido, ya no junta
  ese renglón (2 ART en vez de 1) y sigue escribiendo 310. Sigue sin camino: el único llamador valida.
- **Origen AR sin estado** (3 del adversario): generar frena con un 400 claro y la pantalla tampoco deja
  seguir (`finalize.js`, `CDI.despachante.leer()` antes de ir a Listo). Los avisos no lo anticipan por API.
- **`despachante.js:362`** propone estado 2 con un origen no reconocido: es pantalla; generar frena por el
  origen antes de usar el estado.
- **Grupo con orígenes válidos distintos**: generar frena y los avisos no lo dicen; ya era así.
- **`grupo_id` como lista** (1 del adversario): 500 sólo por API, ya en `main`.
- **Rojo intermitente de `test_despacho1b.py`** con la máquina cargada: sin nombre ni assert en el informe,
  no lo puedo atar a una causa. No es de esta pieza: va como DESPACHO1B-CARGA, la pieza siguiente.

No corrido por la PM: nada contra producción; la CI no se mira (deselecciona y Railway no la espera).
