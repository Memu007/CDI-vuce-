# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## EXCEL2D-TIEMPO: la subida cara mide CPU del proceso, no reloj

| | SHA |
|---|---|
| base | `205b7457` |
| el hilo testigo y el total miden CPU del proceso; tope del frenado 1 s | `6759d65d` |
| 2499 combinadas tolera 1,5 s de CPU, no 3 | `ba2d2693` |
| el hilo testigo deja siempre una muestra al terminar | `181e0dfc` |
| merge de tu rama (`72c297c1`, sólo `NOW.md` y la reproducción) | `c614c5e8` |
| informe | el commit `docs:` que trae este archivo |

**Resultado.** Producto +0/−0. `test_la_subida_cara_no_frena_a_nadie` ya no
mira el reloj: mide `time.process_time()` (CPU de todo el proceso). Otros
procesos de la máquina no la inflan. El defecto que cuida (openpyxl
reteniendo el GIL) sigue rojo: con el sabotaje de formatos el testigo ve
4,99 s de CPU sin poder correr (tope 1 s). Con 8 procesos ocupados en 4
núcleos el caso normal más caro gasta 0,50 s de CPU y frena 0,11 s.

De paso, el tope de 3 s de «2499 combinadas» no veía su propio sabotaje
(copiar `df.attrs` en cada fila): en la base `205b7457` sale VERDE. Lo bajé a
1,5 s y ahora sale ROJO. Ese cambio va solo en `ba2d2693` para poder
revertirlo (D215).

## Decisiones

**D214. Una espera sin CPU (cola, lock, timeout) ya no la ve nadie.**
El reloj la veía; la CPU no, porque esperar no gasta CPU. No hay sabotaje
hoy que la devuelva, pero es cobertura perdida.
- (a) Sumar un tope de reloj generoso al mismo caso, por ejemplo 10 s
  (5 veces lo más lento medido con 8 ocupados, 2,09 s). Separa una espera
  larga del ruido de la carga.
- (b) Dejarlo así y anotarlo como riesgo.

Recomiendo **(a)**: son dos líneas y un tope que la carga no alcanza. No lo
hice porque no lo pediste.

**D215. Con cobertura, «2499 combinadas» queda cerca del tope 1,5.**
La CI (`ci.yml:49`) y las puertas corren `--no-cov`: ahí gasta ≤0,50 s, un
tercio del tope. Pero `pytest.ini` prende cobertura por defecto, y así gasta
1,16–1,22 s.
- (a) Quedarse con 1,5. El sabotaje de `attrs` (2,25–2,39 s) sale rojo,
  pero quien corra `pytest` sin `--no-cov` en una máquina lenta puede ver
  un rojo falso.
- (b) Volver a 3 (revertir `ba2d2693`). Nunca da falso rojo, pero el
  sabotaje de `attrs` vuelve a pasar verde, como en la base.

Recomiendo **(a)**: un falso rojo local se ve y se explica; un sabotaje
verde no se ve.

D205, D206 y D208 siguen con Emi.

## Comandos

```bash
git fetch origin claude/dev-tecnica && git checkout origin/claude/dev-tecnica
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov tests/test_excel2d.py                       # 26 passed
PY=python scripts/testing/sabotajes/excel2d.sh 181e0dfc                  # 20 ROJO, «sabotajes con falla: 0»
PY=python scripts/testing/sabotajes/excel2d.sh 205b7457                  # en la base: «VERDE | las celdas rellenadas vuelven a copiarse en cada fila», falla: 1
# máquina cargada: un proceso ocupado por núcleo, y después matarlos
for i in $(seq $(nproc)); do python -c "while True: pass" & done
python -m pytest -q --no-cov tests/test_excel2d.py                       # 26 passed
kill $(jobs -p)
python docs/pm/herramientas/chequeo-6.py 205b7457 181e0dfc              # producto +0/−0, avisos: 0
```

## Puertas sobre `181e0dfc`

| Puerta | Salida exacta |
|---|---|
| sabotajes `excel2d.sh` | 20 ROJO, «sabotajes con falla: 0», «salida 0» |
| sabotaje que cuida el GIL (formatos xlsx) | «ROJO  \| los formatos vuelven a no mirarse antes de abrir: dice «FAILED tests/test_excel2d.py::test_la_subida_cara_no_frena_a_nadie[120 000 corchetes en un formato]» (9 s)»; aparte, con el mismo sabotaje a mano sobre `181e0dfc`: «E   AssertionError: el otro hilo no avanzó mientras el proceso gastó 5.13 s de CPU» |
| sabotaje de `attrs` en la base `205b7457` | «VERDE \| las celdas rellenadas vuelven a copiarse en cada fila: la prueba no lo vio», «sabotajes con falla: 1» |
| `test_excel2d.py`, 4 ocupados (= núcleos), 5 vueltas | 26 passed, 3 warnings in 4.90s / 5.48s / 5.28s / 5.87s / 5.46s |
| `test_excel2d.py`, 8 ocupados, 5 vueltas | 26 passed, 3 warnings in 9.24s / 9.53s / 9.94s / 9.95s / 10.03s |
| los 8 `tests/test_excel*.py` juntos en orden, quieta, 3 vueltas | 1327 passed, 3 warnings in 80.73s / 81.06s / 81.82s |
| los mismos con 4 ocupados, 2 vueltas | 1327 passed, 3 warnings in 123.92s / 123.50s |
| `chequeo-6.py 205b7457 181e0dfc` | ver abajo |

```
chequeo-6 205b7457..181e0dfc0b757c02231fe12bd49a0d28b226ca98: avisos para mirar, no un veredicto
producto +0/−0
arnés +11/−8
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Mediciones (máximo de 3 vueltas, en segundos)

Sin cobertura, como la CI. «Frenado» es el salto más grande de CPU entre
dos muestras del hilo testigo.

| Caso | Quieta: reloj / CPU / frenado | 4 ocupados | 8 ocupados |
|---|---|---|---|
| 2499 combinadas (tope 1,5) | 0,535 / 0,493 / 0,075 | 0,66 / 0,471 / 0,09 | 1,174 / 0,502 / 0,079 |
| 9995 combinadas (tope 3) | 0,946 / 0,963 / 0,31 | 1,187 / 1,004 / 0,33 | 2,091 / 0,883 / 0,112 |
| los otros 5 casos | 0,214 / 0,206 / 0,097 | 0,356 / 0,198 / 0,095 | 0,493 / 0,201 / 0,1 |

Con 8 ocupados el reloj se duplica y la CPU no se mueve: eso es lo que
pediste separar.

Con cobertura (como `pytest` sin `--no-cov`):

| Caso | Quieta | 4 ocupados | sólo `-k 2499`, proceso nuevo |
|---|---|---|---|
| 2499 combinadas | CPU 1,193, frenado 0,131 | CPU 1,128 | CPU 1,224 |
| 9995 combinadas | CPU 1,929, frenado 0,438 | CPU 1,735 | — |

Sabotajes, una medición cada uno (`attrs`, 3):

| Sabotaje | Caso | CPU | Frenado | Por qué sale rojo |
|---|---|---|---|---|
| formatos xlsx sin mirar antes de abrir | 120 000 corchetes | 5,016 | 4,99 | frenado (tope 1) |
| muchos rangos | 640 000 rangos | 3,908 | 0,268 | total |
| formatos .xls | tres de 60 000 corchetes | 14,7 | 1,279 | frenado y total |
| `attrs` en cada fila | 2499 combinadas | 2,25–2,387 | 0,091 | total (tope 1,5) |
| `attrs` en cada fila | 9995 combinadas | 0,89 | 0,273 | no le cambia: rechaza con 400 antes del bucle |

El frenado normal más alto es 0,438 (9995, con cobertura). El sabotaje con
frenado más bajo es el de .xls, 1,279. El tope 1 queda entre los dos.

## Revisión (`/code-review high`) y qué hice con cada hallazgo

| # | Hallazgo | Qué hice |
|---|---|---|
| 1 | La CPU no ve una espera sin CPU (cola, lock, timeout) que el reloj veía | D214 |
| 2 | El tope del frenado pasó de 0,5 s de reloj a 1 s de CPU: un freno de 0,6–0,99 s pasa | Riesgo, queda en 1: el normal llega a 0,438 y el sabotaje más bajo a 1,279 |
| 3 | `process_time` suma hilos que dejaron tests anteriores | Corrí los 8 `test_excel*.py` juntos en orden, quieta y cargada: todo verde. La suite completa no la corrí |
| 4 | Con cobertura, 2499 queda a 1,22 de 1,5 | D215 |
| 5 | Igual que 4, con `-k 2499` solo | Medido: 1,164–1,224. Va en D215 |
| 6 | 9995 con tope 3 no vería una regresión lineal más suave | Queda: el sabotaje de `attrs` no lo toca (400 antes del bucle) y el suyo sale rojo en 16 s. Con cobertura gasta 1,93 de 3 |
| 7 | Si la subida termina antes de la primera vuelta del testigo, `max()` de una lista vacía tapa el status | Arreglado en `181e0dfc`. Con `listo` puesto antes de arrancar el hilo: el bucle viejo da «ValueError: max() iterable argument is empty» y el nuevo, 2 muestras |
| 8 | Hay otros topes de reloj: `tests/test_excel2.py:141,434,555` y `tests/test_excel1_lectura.py:285` | Fuera de alcance. Te propongo una pieza igual para ellos |

## Lo que no corrí

- La suite completa: sólo los 8 archivos `test_excel*.py`.
- Subagentes adversarios: no corrí ninguno en esta pieza.
- El runner real de la CI: todo es de esta máquina (4 núcleos).
- La línea E de cada sabotaje en `excel2d.sh`: mira sólo el id del `FAILED`.
  La del sabotaje de formatos la saqué aparte (tabla de puertas).

## Riesgos

- D214: una espera sin CPU pasa verde.
- D215 (a): un rojo falso local con cobertura en una máquina lenta.
- Hallazgo 2: un freno de 0,6–0,99 s de CPU pasa verde.
- El runner de la CI puede tener otra CPU; la medición de CPU depende de la
  velocidad del núcleo, no de la carga. El margen sin cobertura es 3 veces.

Archivos de producto tocados: ninguno. `tests/test_excel2d.py` es el único
archivo cambiado.

/compact conservar: Dev 1 técnica, rama claude/dev-tecnica; entregué EXCEL2D-TIEMPO (6759d65d, ba2d2693, 181e0dfc + informe): test_la_subida_cara_no_frena_a_nadie mide CPU del proceso, frenado < 1 s, 2499 combinadas tope 1,5; D214 (tope de reloj para esperas sin CPU) y D215 (1,5 vs 3 con cobertura) abiertas; D205, D206, D208 con Emi; próxima D216; tests/test_conexiones1.py sin seguimiento; nunca main, nada se publica sin el «dale» de Emi para el SHA, sin secretos.
