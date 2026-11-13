# Reproducción de EXCEL2D-RELOJ (2026-11-13)

Entrega de la Técnica: prueba `f75cb48c`, informe `6dc29490`, base `ccd40350`.
Sólo pruebas (producto +0/−0): `test_la_subida_cara_no_frena_a_nadie` suma
la espera sin CPU (saltos sin CPU y sin otro hilo en estado `R` de
`/proc/self/task`), tope 0,5 s. Revisado por la PM principal en worktrees en
el SHA entregado y en la base. Veredicto: **aceptada e integrada**.

| qué | salida |
|---|---|
| `chequeo-6.py ccd40350 f75cb48c` | producto +0/−0, sólo pruebas, historia vacía, 0 AVISO: igual que el informe |
| `excel2d.sh f75cb48c` | 21 `ROJO`, `sabotajes con falla: 0`, rc=0; el nuevo: `la subida espera 4 s sin gastar CPU` |
| negativos de la PM, `-k 'no_frena and 2499'`, `--no-cov`, después de `validar_con_carril` en `upload_excel_v2` (07:0x–07:12 UTC) | ver abajo |
| 4 núcleos con 8 ocupados, `-k no_frena`, dos veces | `7 passed` las dos (6,8 y 6,1 s) |
| un núcleo (`taskset -c 0`) con 8 ocupados, dos veces | `7 passed` las dos (25,8 y 24,5 s) |

| negativo | `f75cb48c` | base `ccd40350` |
|---|---|---|
| sano | `1 passed` | `1 passed` |
| `threading.Event().wait(2)` | rojo, `esperó 1.99 s sin gastar CPU` | verde |
| 20 × `await asyncio.sleep(0.05)` | rojo, `esperó 0.99 s` | verde |
| `time.sleep(4)` | rojo, `esperó 3.98 s` | verde |
| GIL (`re.match(r"(a+)+$", "a"*26+"b")`) | rojo, `el otro hilo no avanzó mientras el proceso gastó 2.27 s de CPU` | rojo (2,04 s) |

Las tres esperas son distintas del `asyncio.sleep(4)` de la Dev y la base no
las ve; el GIL sigue rojo: no perdió lo que medía. Cierra D214.

**D228 (a), corrido.** Ocho de los nueve guiones registran con
`scripts/testing/_registrar.js` (corta con `registro: <status> <texto>`);
`org1b` mira el status en el formulario (líneas 107 y 128). Leídos los `.py`:
`abuso2_postgres`, `email1_motores` y `sesion1_motores` afirman 200; las
sondas de `abuso1_motores` imprimen el código a propósito. Puerta: commit
local sin subir con `raise HTTPException(503)` al entrar a `register`,
`SOLO="destino1 cliente1"`: `ROJA … FALLA: registro: 503 {"detail":"registro
saboteado"}` las dos, rc=1; `destino1` sobre `f75cb48c`: `verde`, rc=0. La
entrada de «15 guiones» sale de la cola.

**Riesgos, no devolución.**
- El testigo lee `/proc` y gasta CPU propia: si una espera coincide con él en
  `R`, deja de contarse. Daría un verde falso, no un rojo falso.
- Un hilo trabado en disco (`D`) no figura como `R` y cuenta como espera.
  Mis cargas fueron sólo de CPU. Si la CI da «esperó X s sin gastar CPU», es
  la primera hipótesis.
- Mis negativos y cargas corrieron con `--no-cov`, como la CI (`ci.yml:49`).

**La CI de la PR.** Un push no cancela la corrida anterior (`ci.yml` no
tiene `cancel-in-progress`); lo que corta es el tope `timeout-minutes: 20`
de `ci.yml:15`. La de `ccd40350` murió por tope al 88 %. La de `927d35fe`
(trae EXCEL2D-TIEMPO, no RELOJ) dio verde: «Suite completa» 18:01, a 1:22 del
tope; la verde de `205b7457` tardó 14:47. La de `5eb910fe`, con RELOJ, dio
verde (`tests` y `e2e-maria`): «Suite completa» 19:09, job 19:49, a 11 s del
tope. El margen del tope va a Emi
(punto 14) o como pieza de la Técnica; no frena subir docs.

No corrido: pytest entero, adversarios (sólo pruebas) y el corredor entero
para D228 (sólo `destino1` y `cliente1`).

## Escape (2026-11-13 09:25 UTC)

Lo encontró MARIA (D234, informe `fdaa2da5`): `pytest` entero da rojo en
`test_la_subida_cara_no_frena_a_nadie[9995 combinadas en 19 990 filas]`, 2 de
2 en su contenedor (1,01 y 1,26 s contra el tope de 1 s). Acepté sin `pytest`
entero y la CI de la PR, que sí lo corre, dio verde.

Causa, reproducida por mí: `_otro_hilo_listo()` recorre `/proc/self/task` en
cada marca. La suite llega a esta prueba con ~1080 hilos dormidos; el testigo
casi no marca y `frenado` mide al testigo. La prueba sola con 1075 hilos
dormidos puestos por un plugin: `1 failed` 2 de 2 (1,47 y 1,13 s); sin el
plugin, `7 passed`. Vuelve a la Técnica (`PARA-DEV.md`).

## Vuelta 2: entregada en `25e13c44` (test `c4a30b5a`), con devolución (2026-11-13 11:39 UTC)

El testigo ahora mide el tiempo de reloj y de CPU en cada marca, y saca la
espera de los saltos sin CPU. Diff fuera de `docs/pm`: sólo
`tests/test_excel2d.py`. Corrido por la PM en un worktree en `c4a30b5a`, con
el plugin de hilos del informe de MARIA (`HILOS=n`).

| qué | salida |
|---|---|
| puerta 1, el caso con 0, 1000 y 3000 hilos | verde en los tres |
| puerta 2, `sabotajes/excel2d.sh` con 1000 hilos | 6 `ROJO`, `sabotajes con falla: 0` |
| puerta 3, `pytest` entero | `6112 passed, 110 skipped, 3 xfailed, 104 warnings in 1111.63s`, 0 FAILED (el caso de más: `test_valor1.py` +7 en `git diff --stat caad310a c4a30b5a -- tests/`) |
| negativo mío `246d80c0` (nunca recorre `/proc`), 1000 hilos | «la subida espera 4 s sin gastar CPU» da `VERDE`: el recorrido hace falta |
| espera real de 4 s (`asyncio.sleep(4)` después de `validar_con_carril` en `main.py`) | medida: 3,91 s con 0 hilos, 1,95 s con 1000 y 0,87 s con 3000 |
| espera real de 0,8 s, apenas sobre el tope de 0,5 s, con `-k "no_frena and 2499"` | `HILOS=0`: `E   assert 0.7789743069993165 < 0.5`, `1 failed, 25 deselected, 3 warnings in 1.50s`; `HILOS=1000`: `1 passed, 25 deselected, 3 warnings in 1.61s`; `HILOS=3000`: `1 passed, 25 deselected, 3 warnings in 1.48s` |

**Causa.** El salto en el que el testigo recorre `/proc/self/task` se marca
como «otro hilo listo» y no suma a la espera. Con muchos hilos, ese recorrido
dura más que el tic de 10 ms del testigo, y de cada vuelta sólo cuenta como
espera el tic. El frenado ya no depende de los hilos;
la espera sí.

**No corrido por la PM:** que el producto no pierde hilos en un uvicorn que
vive mucho (va a la pieza de D229), y adversarios (la pieza es del arnés).

**Riesgos, no devolución.** El webhook de Mercado Pago (`main.py:11688`)
cierra la sesión por el finalizador: la pieza de D229 lo informa como
riesgo, y arreglarlo sería una pieza de producto aparte. Queda un residuo: un recorrido justo antes de CPU fuerte puede
quedar contado como salto con CPU.

**Integrada sin aceptar.** `c4a30b5a` entra a la rama de PM con NAVEGADOR
(merge `5c0faf45`): la unión es idéntica a `9059c696` fuera de `docs/pm`, y
con ese test `pytest` entero da verde, mientras que el de antes daba el rojo
de D234.
