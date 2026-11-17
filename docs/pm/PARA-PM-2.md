# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Entrega DESPACHO1B-CARGA-2: sobre `fd4eb1dd` (2026-11-17 23:40 UTC)

**Resultado.** Sólo cambian pruebas (`producto +0/−0`). Base `8f3a9052`. Sin decisiones nuevas para vos.

- **D271, medido: aparece.** `test_el_texto_tiene_tope_de_cpu` se tragó un tick en 2 de 21 corridas
  cargadas. Con el archivo solo, 0 en 21. Entonces el ayudante pasó a `tests/pdf_bombas.py`
  (`recolector_sin_la_suite`), una sola copia, y lo usan `test_despacho1b.py` (los seis casos) y
  `test_rendimiento1d.py:97`. Con la misma carga sobre `fd4eb1dd`: 0 en 21.
- **D272, arreglado.** El `try` interno abarca el bucle entero, condición incluida. Fuera de pytest, 3
  tandas de 2000 del cuerpo del caso:
  - antes: `cortes == 1` 18 veces en 6000 (5, 3 y 10), todas con la pila `('<module>', 10), ('cortar',
    346)`: la línea 10 es la condición del `while`;
  - después: 0 en 6000, y ninguna pasó de 1 s.
  - Con el corte desarmado el caso sigue en rojo (`assert 0 == 2`), y con el temporizador que no se
    repite también (`assert 1 == 2`).
- **El tope del producto no se tocó.** Sin esperas fijas nuevas ni reintentos.
- **Puertas:** los tres archivos tocados o que usan el ayudante, la carga 7 × 3, `despacho1b.sh` con
  Postgres y chequeo-6, abajo con su salida.

## D271: la medición, sobre `8f3a9052`

`contar.py` cuenta, por caso, los avisos «Exception ignored» que pasan por `cortar` (ticks tragados) y
los `FAILED`. El archivo solo: `tests/test_rendimiento1d.py`, 21 veces seguidas. La carga: siete lazos en
paralelo, en 4 núcleos y sin otros procesos, cada uno con `tests/test_catalogo3.py
tests/test_despacho1b.py tests/test_rendimiento1d.py` tres veces.
```
solo 21:04:52
corridas: 21 {'12 passed': 21}
ticks tragados por caso: {}
fallas: {}
carga 21:11:31
corridas: 21 {'408 passed': 21}
ticks tragados por caso: {'test_el_texto_tiene_tope_de_cpu': 2}
fallas: {}
```
El tick tragado, en `carga_5_2` y `carga_6_2`:
```
tests/test_rendimiento1d.py::test_el_texto_tiene_tope_de_cpu
  PytestUnraisableExceptionWarning: Exception ignored in: <function WeakSet.__init__.<locals>._remove at 0x7f511649d800>
    File "/usr/lib/python3.12/_weakrefset.py", line 39, in _remove
    File ".../proyecto_maria/core/despacho_lector.py", line 346, in cortar
  proyecto_maria.core.despacho_lector._DemasiadoTrabajo
```
No salió ningún rojo: hace falta un segundo tick dentro del gancho de pytest, como en la pieza anterior.
Es la misma causa, y por eso va el mismo ayudante.

En `rendimiento1d:97`, el PDF se arma antes del bloque (`data = trabajo(hojas=2)`). Así el congelado
rodea sólo la lectura y el armado no gasta el tope.

## D272: antes y después, fuera de pytest, sobre `fd4eb1dd`

Los dos cuerpos, 2000 veces por tanda, tres tandas de cada uno en paralelo:
```
antes_1.txt: {2: 1995, 1: 5} {(('<module>', 10), ('cortar', 346)): 5}
antes_2.txt: {2: 1997, 1: 3} {(('<module>', 10), ('cortar', 346)): 3}
antes_3.txt: {2: 1990, 1: 10} {(('<module>', 10), ('cortar', 346)): 10}
despues_1.txt: {2: 2000} lentos 0
despues_2.txt: {2: 2000} lentos 0
despues_3.txt: {2: 2000} lentos 0
```
El informe anterior decía 17 en 6000; esta corrida, 18. «lentos» cuenta las vueltas de 1 s o más (el
segundo assert del caso).

Por qué ahora no queda una ventana: en CPython 3.12 la señal se atiende en un punto de corte del
intérprete (llamada, salto hacia atrás, entrada a función). Entre el `except` y el `cortes += 1` no hay
ninguno (lo miré con `dis`). Todo lo demás del primer tramo está dentro del `try` interno.

## Sabotajes de los dos casos tocados, sobre `fd4eb1dd`

```
desarmado: E   Failed: DID NOT RAISE _DemasiadoTrabajo|E   AssertionError: 0|E   assert 0 == 2|FAILED tests/test_rendimiento1d.py::test_el_texto_tiene_tope_de_cpu - Failed:...|FAILED tests/test_despacho1b.py::test_un_corte_por_cpu_que_se_traga_un_finalizador_vuelve_a_cortar| ======================== 2 failed, 5 warnings in 3.30s =========================
norepite: E   AssertionError: 1|E   assert 1 == 2|FAILED tests/test_despacho1b.py::test_un_corte_por_cpu_que_se_traga_un_finalizador_vuelve_a_cortar| =================== 1 failed, 1 passed, 5 warnings in 2.87s ====================
sin sabotaje: ======================== 2 passed, 5 warnings in 0.89s =========================
```
- **desarmado:** `_tope_de_cpu` sale sin armar el temporizador.
- **norepite:** `setitimer(..., 0)` en vez de `0.05`: el temporizador no se repite.

## Commits

| commit | qué |
|---|---|
| `bca3fff6` test | D272: el `try` interno abarca el bucle, condición incluida |
| `fd4eb1dd` test | D271: el ayudante pasa a `tests/pdf_bombas.py` y lo usan los dos archivos. **Lo que se entrega** |
| informe | el commit siguiente |

## Pruebas

| qué | SHA | resultado |
|---|---|---|
| carga 7 × 3 (catalogo3, despacho1b, rendimiento1d) | `fd4eb1dd` | 21 × «408 passed»; 0 ticks tragados; 0 fallas |
| despacho1b, rendimiento1d y rendimiento1c | `fd4eb1dd` | «312 passed, 3 warnings in 110.20s» |
| `despacho1b.sh` con Postgres | `fd4eb1dd` | «BASE \| verde sin sabotaje», 136 ROJO, «sin Postgres, no corridos: 0», «sabotajes sin rojo: 0» (21:36 a 23:35) |
| chequeo-6 | `8f3a9052..fd4eb1dd` | abajo, entero |

`rendimiento1c` entra porque importa de `pdf_bombas.py`.

Los sabotajes de `despacho1b.sh` que anclan en los casos que usan el ayudante:
```
ROJO  | el temporizador de CPU no se repite: «FAILED tests/test_despacho1b.py::test_un_corte_por_cpu_que_se_traga_un_finalizador_vuelve_a_cortar»
ROJO  | un corte por CPU parece escaneado: «FAILED tests/test_despacho1b.py::test_un_corte_por_cpu_en_la_primera_hoja_no_dice_que_es_escaneado»
ROJO  | extraer se lleva el tope entero: «FAILED tests/test_despacho1b.py::test_las_hojas_leidas_antes_del_corte_dan_sus_productos»
ROJO  | la señal queda puesta: «FAILED tests/test_despacho1b.py::test_el_tope_de_cpu_deja_la_senal_como_estaba»
```
`despacho1b.sh` no tiene sabotajes que anclen en `rendimiento1d`; ese caso lo cubre el «desarmado» de arriba.

chequeo-6, entero:
```
chequeo-6 8f3a9052..fd4eb1dd: avisos para mirar, no un veredicto
producto +0/−0
arnés +32/−29
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Revisiones

| quién | sobre | hallazgos | qué hice |
|---|---|---|---|
| `/code-review high` | `8f3a9052..fd4eb1dd` | 7 | ninguno pide cambio dentro de la tarea; abajo |
| `adversario-sonnet-medio` | `fd4eb1dd` | 0 | sus sabotajes dan rojo; `rendimiento1c` y `rendimiento1d`: «27 passed» |

Los siete del `/code-review`:
1. **Carrera en el `finally` del producto** (un tick entre el `setitimer(0)` y la vuelta del manejador):
   el producto queda fuera de la tarea. Medido antes, 0 en 10 000. Riesgo.
2. **Un tick entre el `except` y el `cortes += 1`:** refutado con `dis` y con el 0 en 6000.
3. **Los finalizadores por conteo de referencias no los frena el congelado:** cierto; dentro del bloque
   sólo muere lo que crea la lectura. Riesgo.
4. **El ayudante es voluntario:** un caso nuevo que lea con tope dentro de pytest puede olvidarlo. Riesgo.
5. **`gc.unfreeze` no se anida:** no hay otro `gc.freeze` en el repositorio. Riesgo bajo.
6. **El import a nivel de módulo en `test_despacho1b.py`:** lo dejé, es una línea para seis usos.
7. **El costo de `gc.collect()`:** medido en la pieza anterior, entre 97 y 202 ms cada uno. Ahora suma
   uno más, en `rendimiento1d`.

El adversario corrió sus pruebas mientras corría mi carga. Por eso esa carga no es «sin otros procesos»;
igual dio 0.

## Comandos

```bash
VENV=/ruta/al/venv
PT="env -u DATABASE_URL -u ENVIRONMENT GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=. $VENV/bin/python -B -m pytest -q --no-cov -p no:cacheprovider --timeout=300"
CASOS="tests/test_rendimiento1d.py::test_el_texto_tiene_tope_de_cpu tests/test_despacho1b.py::test_un_corte_por_cpu_que_se_traga_un_finalizador_vuelve_a_cortar"
# 1. los dos casos, en fd4eb1dd                                  → «2 passed»
$PT $CASOS | tail -1
# 2. el temporizador que no se repite                  → «1 failed, 1 passed», con «assert 1 == 2»
R=/tmp/d1bc2; git worktree add -f -q --detach $R fd4eb1dd && cd $R
sed -i 's/max(segundos, 0.001), 0.05)/max(segundos, 0.001), 0)/' proyecto_maria/core/despacho_lector.py
git diff --stat; $PT $CASOS | grep -E "^E  |passed|failed"
cd - >/dev/null; git worktree remove -f $R
# 3. §6                                                          → «producto +0/−0», «avisos: 0»
python3 docs/pm/herramientas/chequeo-6.py 8f3a9052 fd4eb1dd
```
La carga de 7 × 3 tardó 8 minutos (21:27 a 21:36), y las 6000 vueltas con los sabotajes, 4 (21:23 a
21:27). No te las pido: están arriba.

## Riesgos

- **Carrera en el `finally` del producto** (punto 1 de arriba). No la toqué: el criterio 3 deja el tope
  como está.
- **Finalizadores por conteo de referencias** (punto 3): si una lectura suelta el último puntero a un
  objeto ajeno con `__del__`, ese finalizador corre dentro del tope. No lo vi.
- **El ayudante es voluntario** (punto 4). Hoy lo usan los siete casos que leen con temporizador dentro
  del proceso de pytest con un tope chico.
- **`gc.unfreeze` no se anida** (punto 5).
- **Lo que no corrí:** la suite completa (sólo cambian pruebas de tres archivos, y el criterio 4 no la
  pide); `e2e_maria.sh`.

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5, rama `claude/dev-maria`; rutina trig_01Ukttby1fc4sGVQfSn1jC9U apagada por la PM: me despierta por send_message. PM principal session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `09ac6e29`. Aceptadas: las de antes (CUIT-GENERAR `29327d2` … D269 `471db09a`), DESPACHO1B-CARGA sobre `962bc88f`, DESPACHO1B-CARGA-2 sobre `fd4eb1dd` (informe `b0c0b0db`). Sin pieza: mi cola espera a Emi (D266, D261) o a alguien de afuera (PESO-NETO-1, MARIA-6, PRORRATEO-1, LEGAL-1); quieta hasta que la PM escriba. Próxima D: D273. Lecciones (además de las del historial de este archivo): el negativo de un arreglo va en el mismo SHA con el arreglo vaciado; una tasa «después» sin ese negativo no distingue; cada número del informe sale de un log, y el que no está, se mide o se saca; lo que marca un adversario se reproduce antes de proponerlo; un congelado del recolector sin `gc.collect()` antes mueve los finalizadores al caso siguiente; una tarea en segundo plano muere a las 2 h: puertas con `setsid nohup` y un vigía de timeout largo; horas, sólo de `date -u` en el momento de escribirlas, también la del encabezado; los comandos para la PM se prueban antes de escribirlos. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica; subagentes hasta esfuerzo alto, sin consejero, nunca Fable; detener los subagentes después de su informe.
