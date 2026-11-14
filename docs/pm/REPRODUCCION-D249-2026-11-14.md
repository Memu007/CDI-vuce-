# D249 (a): reproducción de la PM

Entrega `50dabfa` (pruebas `de69dc4` y `50dabfa`, informe `5682f6e`, canal `PARA-PM-2.md`).
Base `279a685` (producto y las dos pruebas iguales a `4a58c68`, según la Dev). Sólo arnés:
`tests/test_sufijos2.py` +31 (de 110 a 117 pruebas) y `scripts/testing/sabotajes/sufijos2.sh`
+52 (de 33 a 49 sabotajes). Veredicto: **aceptada sobre `50dabfa`**.

## Corrido por la PM (2026-11-14, entre 11:20 y 11:40 UTC)

Superpuesto con `run6` de fondo. Al terminar no quedó ningún worktree en `50dabfa`.

| Qué | Resultado |
|---|---|
| `chequeo-6.py 279a685 50dabfac` | producto +0/−0, arnés +83/−0, historia vacía, `avisos: 0` |
| unión `50dabfac..5682f6e3` fuera de `docs/pm` | vacía |
| copia del guion de `50dabfac` sobre `50dabfac` | `rc=0`, 49 `ROJO`, `BASE \| 117 passed`, `sabotajes sin rojo: 0` |
| el mismo guion sobre la base `279a685` | `rc=1`, `BASE \| 110 passed`, 33 `ROJO`, `sabotajes sin rojo: 16` |
| copia con un sabotaje mío: «cerca de» corrido en uno (`sufijo[pos + 1:pos + 21]`) | `ROJO \| … «…[no_se_separa_largo]»`, 50 `ROJO`, `rc=0` |
| `sabotaje_sufijos1.sh 50dabfac` | `rc=0`, «OK: los 46 sabotajes dan rojo por la razón esperada» |
| `anclas_perdidas.py 50dabfac` | 103 guiones, 2509 anclas, 11 sin medir; 0, 0 y 0 |

Sobre la base, los 16 nuevos no dan rojo: 15 `VERDE | … la prueba no lo vio` y uno `ROJO?`,
«pide» con `«{sufijo[:40]}»`, que en la base lo ve sólo
`test_un_sufijo_que_pide_numero_no_acepta_decimales[AA(X)-ZB(16.384)-CA00-]` (el `FAILED` de mi
`base.log`): es el «hoy lo sostiene uno solo» del criterio.

Los 10 cambios del criterio tienen cada uno su sabotaje, con el título de la tabla del informe;
los 6 de más son el supuesto 1. El hallazgo del adversario (`valor[:20]`) da `VERDE` en la base
y `ROJO` en `50dabfac` («en lugar del número que cambiaría sale el principio del valor»).

Dicho por la Dev, no lo corrí: con los 8 archivos que miran estos textos, «cerca» `[:20]`,
«separar» `[:10]` y el aviso `[:10]` ya los veía otro archivo; la segunda pasada del adversario
fue sobre `50dabfa`, con 13 cambios de la parte «cambiaría» y 0 en verde.

## Decisiones

- Supuestos 1 (seis sabotajes de más) y 2 (el dato `pide` repite un sufijo): aceptados.
- Riesgo 1 (`.strip()` en los bordes): aceptado; no cambia qué código nombra el error.
- Riesgo 2 (`AF(-2.5)` sin texto exacto, sólo con comodín): a `COLA-LIMPIEZA.md` como
  «un dato más en el mismo caso».
- Riesgo 3 (`.upper()`): previo, fuera de D249.
- Sin `/code-review`: pasa esta vez, decidido por la PM (producto +0/−0 y el SHA entregado pasó
  por el adversario). `/entregar` no lo exceptúa: en las próximas, se corre o se dice por qué no.
- Sin D nueva: la próxima sigue siendo D251.

## No corrido

- Suite entera y `e2e_maria.sh`: sin cambio de producto.
- Subagentes adversariales de la PM: arnés sin dinero, sesión ni datos.
- El riesgo 1 medido por la PM.
- La medición de la Dev con los 8 archivos.
