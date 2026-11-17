# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Entrega DESPACHO1B-CARGA: sobre `962bc88f` (2026-11-17 20:50 UTC)

**Resultado.** Sólo cambia `tests/test_despacho1b.py` (`producto +0/−0`). Base `50d32c26`.

- **Se reprodujo.** Con 7 corridas de pytest en paralelo en 4 núcleos (catalogo3 más despacho1b): 1 rojo
  en 21 corridas.
- **El caso:** `test_un_corte_por_cpu_en_la_primera_hoja_no_dice_que_es_escaneado`.
- **El error:** no falla ningún assert del caso. Da `RuntimeError: Failed to process unraisable
  exception` desde `collect_unraisable` de pytest.
- **La causa, medida:**
  1. El lector lee dentro del proceso de pytest, con la memoria de la suite.
  2. El recolector corre dentro del tope y ejecuta un finalizador ajeno (`_collection_gced` de
     sqlalchemy).
  3. Un tick del tope cae en ese finalizador. Python no lo propaga y se lo pasa a `sys.unraisablehook`.
  4. El gancho de pytest es Python y formatea el traceback con el temporizador andando.
  5. Medí el gancho en 52 avisos: 50 tardaron menos de 0,05 ms y 2, 3,6 y 4,0 ms. Leo los lentos como la
     primera lectura del archivo (`linecache.updatecache`, que es donde cae el tick del rojo); eso no lo
     medí aparte. Con la máquina cargada, la ventana crece.
  6. Un segundo tick cae dentro del gancho y pytest lo cuenta como error del caso.
- **Producción no:** el lector corre en un proceso aparte, con el gancho de C.
- **El arreglo (sólo prueba):** un ayudante, `_recolector_sin_la_suite`, rodea sólo la lectura. Hace
  `gc.collect()`, `gc.freeze()` y al salir `gc.unfreeze()`. Los seis casos que leen con el temporizador
  en el hilo principal lo usan. Es el `gc.freeze()` del acta del 07/11 (criterio 6), que tenía uno solo
  de los seis, ahora en un lugar.
- **Con la misma carga:** 21 de 21 verdes y 0 ticks tragados. Antes eran 18 ticks tragados en 21
  corridas.
- **Con el corte desarmado y la misma carga:** 7 de 7 en rojo, con dos sabotajes distintos.

**Criterio 7.** Lo leo como causa en la prueba, no en el entorno:
- La prueba lee en el proceso de pytest, cosa que el producto no hace. La carga sólo agranda la ventana.
- Con 8 procesos gastando CPU al lado y sólo este archivo, no salió (3 de 3 verdes).
- Salió con 7 suites en paralelo en 4 núcleos, sin otros procesos al lado. Si eso no te parece una carga
  razonable, el arreglo se retira: son tres commits de prueba.

**Lo que decidís vos:**
- **D271. El mismo caso en otro archivo.** `tests/test_rendimiento1d.py:97`
  `test_el_texto_tiene_tope_de_cpu` llama a `texto_plano_del_pdf(trabajo(hojas=2), limite_cpu_s=0.2)` en
  el proceso de la suite, con el temporizador y sin el ayudante.
  - Espera el corte con `pytest.raises`, así que gastar de más no lo pone rojo. Un tick en el gancho de
    pytest, sí. No lo medí: mis corridas cargadas eran catalogo3 más despacho1b.
  - El criterio 5 dice «del archivo», por eso no lo toqué.
  - Descartado: `tests/test_rendimiento1c.py:395`, que marcó el adversario, valida por
    `validate_file_upload` → `validar_pdf_aparte`, que lee en un proceso aparte (`create_subprocess_exec`).
    Las otras lecturas dentro del proceso de esos dos archivos (`1c:278`, `1d:90`) usan el tope por
    defecto de 10 s: el temporizador sólo dispara si una lectura gasta eso. No las medí.
  - (a) Pieza chica: el ayudante pasa a `tests/pdf_bombas.py` y lo usan los dos archivos. Recomendada:
    un chequeo en un solo lugar (§6).
  - (b) Queda como riesgo escrito.
- **D272. Otro intermitente, con otra causa, en la familia.** Es
  `test_un_corte_por_cpu_que_se_traga_un_finalizador_vuelve_a_cortar`:
  - Su cuerpo, fuera de pytest, da `cortes == 1` 17 veces en 6000 (5, 4 y 8 en tres tandas de 2000).
  - La pila de las 8 de la última tanda: `('<module>', 10), ('cortar', 346)`. La línea 10 es la condición
    del `while`.
  - El primer tick se atiende fuera del `try` interno, así que el caso cree que no se tragó ninguno.
  - Ya estaba antes de esta pieza, y el ayudante no lo cambia.
  - En las 63 corridas cargadas sin sabotaje (21 en la base, 21 en `45e4ac61`, 21 en `962bc88f`) no salió.
  - (a) Pieza chica de prueba: la condición del bucle entra al `try` interno. Recomendada.
  - (b) Riesgo escrito.

## El rojo, antes del arreglo

Base `50d32c26`. Un lazo corre `tests/test_catalogo3.py tests/test_despacho1b.py` tres veces; siete
lazos en paralelo, en 4 núcleos y sin otros procesos. `contar.py` cuenta, por caso, los avisos «Exception
ignored» que pasan por `cortar` (ticks tragados) y los `FAILED`:
```
corridas: 21 {'396 passed': 20, '1 failed, 395 passed, 6 warnings': 1}
ticks tragados por caso: {'test_un_corte_por_cpu_en_la_primera_hoja_no_dice_que_es_escaneado': 18}
fallas: {'test_un_corte_por_cpu_en_la_primera_hoja_no_dice_que_es_escaneado': 1}
```
El rojo (recortado):
```
______ test_un_corte_por_cpu_en_la_primera_hoja_no_dice_que_es_escaneado _______
/usr/lib/python3.12/traceback.py:139: in format_exception
...
/usr/lib/python3.12/linecache.py:137: in updatecache
    lines = fp.readlines()
proyecto_maria/core/despacho_lector.py:346: in cortar
    raise _DemasiadoTrabajo
E   proyecto_maria.core.despacho_lector._DemasiadoTrabajo
The above exception was the direct cause of the following exception:
...
/tmp/cdi-dev2/venv/lib/python3.12/site-packages/_pytest/unraisableexception.py:75: in collect_unraisable
    raise errors[0]
E   RuntimeError: Failed to process unraisable exception
```
En una corrida verde, el tick tragado se ve como aviso:
```
tests/test_despacho1b.py::test_un_corte_por_cpu_en_la_primera_hoja_no_dice_que_es_escaneado
  PytestUnraisableExceptionWarning: Exception ignored in: <function _collection_gced at 0x7f21b1c807c0>
    File ".../sqlalchemy/event/registry.py", line 103, in _collection_gced
    File "/home/user/CDI-vuce-/proyecto_maria/core/despacho_lector.py", line 346, in cortar
  proyecto_maria.core.despacho_lector._DemasiadoTrabajo
```

**Lo que descarté midiendo:** que el temporizador quede armado después de leer, o que la excepción
escape del lector. Fueron 300 lecturas cortadas, con 0, 2 y 4 hilos gastando al lado: 0 y 0
(`temporizador_armado_despues=0 excepcion_afuera=0`, las 100 de cada tanda con el aviso del corte).

## El arreglo

| commit | qué |
|---|---|
| `45e4ac61` test | el `gc.freeze()` del caso de las hojas leídas pasa a una fixture para cinco casos más |
| `27c7e314` merge | tu rama hasta `da1a6bc8` (criterios 6 y 7) |
| `161952ba` test | de `/code-review`: el congelado rodea sólo la lectura y antes hace `gc.collect()` |
| `962bc88f` test | de `/code-review`: también el caso del finalizador tragado y el de las 60 hojas. **Lo que se entrega** |
| informe | el commit siguiente |

Por qué cambió la primera forma:
- Como fixture, congelaba desde el arranque del caso, así que lo que arma el PDF quedaba dentro del tope.
- Sin `gc.collect()` antes, la basura de la suite quedaba congelada. Al descongelarla, sus finalizadores
  corrían en un caso posterior: la misma falla, en otro lado.
- En el caso del finalizador tragado, la medición de tiempo ahora arranca después del `gc.collect()`.

Los seis casos:
- `test_un_pdf_que_da_mucho_trabajo_deja_de_leerse_por_tiempo_de_cpu` (0,5 s);
- `test_una_sola_hoja_cara_se_corta_en_el_tope_de_cpu` (0,5 s);
- `test_el_tope_de_cpu_deja_la_senal_como_estaba` (0,5 s);
- `test_las_hojas_leidas_antes_del_corte_dan_sus_productos` (1,0 s; ya tenía `gc.freeze()`);
- `test_un_corte_por_cpu_en_la_primera_hoja_no_dice_que_es_escaneado` (0,05 s);
- `test_un_corte_por_cpu_que_se_traga_un_finalizador_vuelve_a_cortar` (0,02 s).

Quedan sin el ayudante, y por qué:
- los de `leer_despacho_aparte` y `_medir_aparte`: corren en un proceso aparte;
- `test_fuera_del_hilo_principal_el_tope_se_mira_entre_hojas`: sin señal, el control es entre hojas y su
  assert es `< 60`;
- `test_sin_memoria_al_abrir_el_pdf_no_se_disfraza_de_pdf_roto`: el lector está reemplazado y termina al
  instante.

Dentro del bloque, sólo muere lo que crea la lectura. pypdf no tiene `__del__` ni callbacks de weakref,
y los `WeakKeyDictionary` del lector son del camino aparte.

## Pruebas

| qué | SHA | resultado |
|---|---|---|
| carga, antes | `50d32c26` | 21 corridas: 20 × «396 passed», 1 × «1 failed, 395 passed»; 18 ticks tragados |
| carga, con el arreglo | `45e4ac61` | 21 × «396 passed»; 0 ticks tragados |
| carga, con el arreglo | `962bc88f` | 21 × «396 passed»; 0 ticks tragados |
| corte desarmado (`_tope_de_cpu` sin temporizador), carga | `962bc88f` | 7 × «6 failed, 390 passed»; el caso, en las 7 |
| corte por CPU que dice escaneado (sin `salteadas = True`), carga | `962bc88f` | 7 × «3 failed, 393 passed»; el caso, en las 7 |
| las dos de arriba | `45e4ac61` | iguales: 7 × 6 y 7 × 3 |
| `tests/test_despacho1b.py` solo | `962bc88f` | «285 passed» |
| `despacho1b.sh` con Postgres | `962bc88f` | «BASE \| verde sin sabotaje», 136 ROJO, «sin Postgres, no corridos: 0», «sabotajes sin rojo: 0» (18:47 a 20:48) |
| chequeo-6 | `50d32c26..962bc88f` | abajo, entero |

Los tres sabotajes de `despacho1b.sh` que anclan en los casos tocados:
```
ROJO  | el temporizador de CPU no se repite: «FAILED tests/test_despacho1b.py::test_un_corte_por_cpu_que_se_traga_un_finalizador_vuelve_a_cortar»
ROJO  | un corte por CPU parece escaneado: «FAILED tests/test_despacho1b.py::test_un_corte_por_cpu_en_la_primera_hoja_no_dice_que_es_escaneado»
ROJO  | extraer se lleva el tope entero: «FAILED tests/test_despacho1b.py::test_las_hojas_leidas_antes_del_corte_dan_sus_productos»
```

Los rojos del caso con el corte desarmado:
```
E   AssertionError: {'renglones': [], 'divisa': None, 'avisos': ['Una línea pasa de 2000 caracteres: no parece un despacho.'], 'sin_texto': False}
```
y sin `salteadas = True`:
```
E   assert True is False
```

chequeo-6, entero:
```
chequeo-6 50d32c26..962bc88f: avisos para mirar, no un veredicto
producto +0/−0
arnés +40/−24
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

Subagentes y revisiones:

| quién | sobre | hallazgos | qué hice |
|---|---|---|---|
| `/code-review high` | `45e4ac61` | 6 | la fixture amplía el congelado y no hace `gc.collect()`: arreglado (`161952ba`); otros archivos: D271; caso del finalizador: D272; el gancho de C en vez del congelado: abajo |
| `adversario-sonnet-medio` | `45e4ac61` | 0 graves; dos de otros archivos | `rendimiento1d:97`, D271; `rendimiento1c:395` lee aparte: descartado |
| `/code-review high` | `161952ba` | 7 | el caso de las 60 hojas y el del finalizador: arreglado (`962bc88f`); los demás: abajo |
| `/code-review high` | `962bc88f` | 6 | ninguno nuevo dentro de la tarea: abajo |
| `adversario-sonnet-medio` | `962bc88f` | 0 reproducidos; 1 residuo teórico | riesgos |

- **Lo propuesto y no hecho: cambiar el gancho de pytest por el de C** durante la lectura. Lo descarté
  por dos razones:
  - no cubre la otra mitad del acta del 07/11 (el recolector gasta el tope);
  - escondería las excepciones ignoradas del propio lector.
- **Del `/code-review` sobre `161952ba`, sobre `NOW.md`:** las horas corregidas ponen la integración de
  D269 (17:45) antes de la aceptación (17:47). Es tu archivo; te lo paso.

## Comandos

```bash
VENV=/ruta/al/venv
PT="env -u DATABASE_URL -u ENVIRONMENT GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=. $VENV/bin/python -B -m pytest -q --no-cov -p no:cacheprovider --timeout=300"
# 1. el archivo, en 962bc88f                                   → «285 passed»
$PT tests/test_despacho1b.py | tail -1
# 2. el corte desarmado                → «6 failed», entre ellos ..._no_dice_que_es_escaneado
R=/tmp/d1bc; git worktree add -f -q --detach $R 962bc88f && cd $R
python3 - <<'EOF'
p = "proyecto_maria/core/despacho_lector.py"; s = open(p, encoding="utf-8").read()
a = "    anterior = signal.signal(signal.SIGPROF, cortar)"
assert s.count(a) == 1; open(p, "w", encoding="utf-8").write(s.replace(a, "    yield\n    return\n" + a))
EOF
$PT tests/test_despacho1b.py | grep -E "^FAILED|passed"
cd - >/dev/null; git worktree remove -f $R
# 3. §6                                                          → «producto +0/−0», «avisos: 0»
python3 docs/pm/herramientas/chequeo-6.py 50d32c26 962bc88f
```
La carga de 7 × 3 tarda unos 7 minutos y no te la pido; está en el informe.

## Riesgos

- **Residuo teórico, no reproducido** (lo marcó el adversario): un generador suspendido que muera dentro
  de la lectura cerraría en un marco de Python. Un tick ahí iría al gancho de pytest. En pypdf no
  encontré ninguno que quede suspendido: el lector consume las hojas con `list(reader.pages)`.
- **Hilos:** `ITIMER_PROF` y `process_time` cuentan la CPU de todos los hilos del proceso. Un hilo de
  otro caso que siga gastando se come el tope. Ya era así y no lo vi pasar.
- **Costo:** seis `gc.collect()` completos más por corrida del archivo, fuera del tope. Medí uno después
  del archivo, con 241 024 objetos vivos y el guion de sabotajes corriendo al lado: entre 97 y 202 ms de
  CPU cada uno (`GC_CPU 96.6ms 116.3ms 160.4ms 190.1ms 201.6ms 152.4ms`). Son cerca de 1 s en un archivo
  de unos 50 s.
- **D271 y D272**, arriba.
- **Lo que no corrí:** la suite completa (sólo cambia este archivo, y el criterio 4 no la pide);
  `e2e_maria.sh`; la carga con quemadores sobre el SHA final (la de 7 suites, sí).

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5, rama `claude/dev-maria`, rutina trig_01Ukttby1fc4sGVQfSn1jC9U; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `da1a6bc8` con el merge `27c7e314`). Aceptadas: las de antes (CUIT-GENERAR `29327d2` … D263 `9e5960d2`), D269 sobre `471db09a` (D270: riesgo escrito; desvío del criterio 5: aceptado). Entregada, en revisión: DESPACHO1B-CARGA sobre `962bc88f` (informe: el commit siguiente): sólo `tests/test_despacho1b.py`; el ayudante `_recolector_sin_la_suite` (`gc.collect`, `gc.freeze`, `gc.unfreeze`) rodea la lectura en los seis casos con temporizador en el hilo principal; causa: un tick tragado por un finalizador ajeno va al gancho de pytest y otro tick lo rompe (`RuntimeError: Failed to process unraisable exception`); carga 7 × 3 en 4 núcleos: base 1 rojo y 18 ticks tragados en 21, arreglo 21 de 21 y 0; desarmado 7 × «6 failed», escaneado 7 × «3 failed». Abierto para la PM: D271 (`rendimiento1d:97` sin el ayudante; recomiendo (a), el ayudante a `pdf_bombas.py`) y D272 (el caso del finalizador da `cortes == 1` 17 en 6000 fuera de pytest: el tick cae en la condición del `while`; recomiendo (a)). Sin pieza «apenas entregues» en mi canal: al volver, `/respondio`. Próxima D: D273. Lecciones (además de las del historial de este archivo): cada número del informe sale de un log, y el que no está, se mide o se saca; lo que marca un adversario se reproduce antes de proponerlo (`rendimiento1c:395` leía aparte); un congelado del recolector sin `gc.collect()` antes mueve los finalizadores al caso siguiente; una tarea en segundo plano muere a las 2 h: puertas con `setsid nohup` y un vigía de timeout largo; horas, sólo de `date -u`. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica; subagentes hasta esfuerzo alto, sin consejero, nunca Fable; detener los subagentes después de su informe.
