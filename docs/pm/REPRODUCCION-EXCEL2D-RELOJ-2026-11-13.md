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
