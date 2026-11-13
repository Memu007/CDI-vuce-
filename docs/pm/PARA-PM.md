# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## EXCEL2D-RELOJ: la subida cara vuelve a ver una espera sin CPU

| | SHA |
|---|---|
| base (merge de tu rama) | `ccd40350` |
| el testigo suma las esperas sin CPU; sabotaje de 4 s en `excel2d.sh` | `f75cb48c` |
| informe | el commit `docs:` que trae este archivo |

**Resultado.** Producto +0/−0. `test_la_subida_cara_no_frena_a_nadie` sigue
midiendo `frenado` y `gasto` en CPU, y suma `espera`: el reloj de los saltos
de 10 ms del hilo testigo en que el proceso gastó menos de reloj/20 de CPU
**y** ningún otro hilo del proceso estaba listo para correr (estado `R` en
`/proc/self/task/<tid>/stat`). Con carga, la subida queda en `R` y no cuenta;
esperando, ningún hilo está en `R`. Tope 0,5 s. Con el sabotaje
`await asyncio.sleep(4)` después de `validar_con_carril` en `upload_excel_v2`
el caso sale rojo: «la subida esperó 3.98 s sin gastar CPU». En las cuatro
escenas sin sabotaje la espera medida es 0,000.

**Por qué no un tope liso de reloj** (tu último punto): en hambre (`taskset
-c 0` con 8 ocupados) una subida normal de «9995 combinadas» llega a 7,481 s
de reloj; en máquina quieta, con `time.sleep(4)`, la de «2499 combinadas»
tarda 4,496 s. Un tope de reloj que no dé falso rojo en hambre (>7,5 s) no ve
una espera de 4 s. La medida nueva separa las dos: hambre 0,000; `sleep(4)`
3,986 quieta y 3,984 en hambre; `sleep(1)` 0,986 y 0,984.

Esto cierra D214 (la propuesta de tope de 10 s queda descartada por los
números de arriba).

## Decisiones

**D228. X-FORWARDED-STATUS ya está hecha.** La premisa no se sostiene sobre
`ccd40350`:
- Ocho de los nueve (`cliente1`, `despacho1a`, `destino1`, `estudio1` dos
  veces, `estudio1b`, `maria9`, `separadores1`, `validacion1`) registran con
  `scripts/testing/_registrar.js`, que corta con `registro: <status> <texto>`
  si no da 2xx. Es el «un solo lugar»; entró con REGISTRO-GUIONES (`b832fc22`),
  con su rojo de proxy 429 en ese informe.
- `org1b` registra por el formulario y mira el status: líneas 25 (alta del
  estudio), 107 (`!== 400`) y 128 (`!== 200`, con el texto).
- Los `.py` que mandan `X-Forwarded-For` (`abuso1_motores`, `abuso2_postgres`,
  `email1_motores`, `sesion1_motores`) miran `s == 200` en cada registro que
  prepara una cuenta. Los que no lo miran (S6, ráfaga y 20 simultáneos de
  `abuso1_motores`) son sondas que imprimen el código a propósito.
  `conexiones1_*` no registra.
- La entrada de `docs/pm/COLA-LIMPIEZA.md:153` («15 guiones») está vieja.

Opciones:
- (a) Cerrarla como hecha y sacar la entrada de la cola (la cola es tuya).
- (b) Que igual le sume algo: decime qué, porque no encuentro el hueco.

Recomiendo **(a)**. No toqué nada.

D205, D206 y D208 siguen con Emi. D215 sigue como la contestaste.
Próxima D: D229.

## Comandos

```bash
git fetch origin claude/dev-tecnica && git checkout origin/claude/dev-tecnica
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov tests/test_excel2d.py          # 26 passed
PY=python scripts/testing/sabotajes/excel2d.sh f75cb48c     # 21 ROJO, «sabotajes con falla: 0»
python docs/pm/herramientas/chequeo-6.py ccd40350 f75cb48c  # producto +0/−0, avisos: 0
```

## Puertas (4 núcleos)

| puerta | salida |
|---|---|
| `pytest tests/test_excel2d.py`, máquina quieta, sobre `f75cb48c` | «26 passed, 3 warnings in 4.16s» |
| caso, quieta, 3 corridas | «7 passed, 26 deselected» (2.93 s, 2.74 s, 2.84 s) |
| caso, 4 ocupados, 3 corridas | «7 passed, 26 deselected» (3.71 s, 3.10 s, 3.26 s) |
| caso, 8 ocupados, 3 corridas | «7 passed, 26 deselected» (5.54 s, 5.70 s, 6.29 s) |
| caso, hambre (`taskset -c 0`, 8 ocupados), 3 corridas | «7 passed, 26 deselected» (22.79 s, 22.84 s, 22.88 s) |
| rojo, `await asyncio.sleep(4)` tras `validar_con_carril` | «E   AssertionError: la subida esperó 3.98 s sin gastar CPU» y «… 3.99 s …»; «2 failed, 5 passed, 19 deselected, 5 warnings in 11.04s» |
| `excel2d.sh f75cb48c` | 21 ROJO, el último «la subida espera 4 s sin gastar CPU», «sabotajes con falla: 0» |

Las cuatro escenas corrieron antes del commit, en un worktree descartable con
el caso y un medidor aparte (`test_medir`, por eso «26 deselected»; no entró
al commit). La primera fila, el rojo y `excel2d.sh` corrieron sobre `f75cb48c`.

Medidas por escena, 14 subidas cada una (los 7 casos × 2 corridas):

| escena | espera máx. | frenado máx. (CPU) | reloj máx. | gasto máx. (CPU) |
|---|---|---|---|---|
| quieta | 0,000 | 0,319 | 0,974 | 0,989 |
| 4 ocupados | 0,000 | 0,210 | 1,117 | 0,944 |
| 8 ocupados | 0,000 | 0,129 | 1,854 | 0,780 |
| hambre | 0,000 | 0,105 | 7,481 | 0,857 |

El rojo de «9995 combinadas» con el sabotaje es esperable: también pasa por
`validar_con_carril` antes de rechazarse.

`chequeo-6`, entero:

```
chequeo-6 ccd40350..f75cb48ca3408c5bc9f7d8e24fc769a9e6e1728c: avisos para mirar, no un veredicto
producto +0/−0
arnés +28/−4
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos y lo que no corrí

- `espera` lee `/proc/self/task`: anda en Linux (la CI es ubuntu), en Mac el
  caso falla con `FileNotFoundError`. Si alguien lo corre en Mac, lo ve.
- Una espera más corta que 0,5 s no se ve. `sleep(1)` sí (0,986).
- Una espera con otro hilo del proceso en `R` todo el tiempo no se ve: con
  carga del proceso mismo no hay forma de separarla de la carga.
- No corrí la suite completa: sólo cambió este caso y el guion de sabotajes.
- Sin adversarios ni `/code-review`, como pediste.

Archivos de producto tocados: ninguno.

/compact conservar: Dev 1 técnica, rama claude/dev-tecnica; entregué EXCEL2D-RELOJ (f75cb48c + informe): el caso suma espera sin CPU (saltos sin CPU y sin hilo en R vía /proc), tope 0,5 s, sabotaje asyncio.sleep(4) en excel2d.sh; D214 cerrada; D228 (X-FORWARDED-STATUS ya hecha por _registrar.js, sacar la entrada de la cola) abierta; D205, D206, D208 con Emi; próxima D229; tests/test_conexiones1.py sin seguimiento; nunca main, nada se publica sin el «dale» de Emi para el SHA, sin secretos.
