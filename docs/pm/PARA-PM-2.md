# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## SEPARADORES-1d: entregada a revisión (2026-10-27)

**Resultado:** los dos puntos están hechos, con casos y sabotajes.
**Nada para decidir.** Abajo van los supuestos y una consecuencia de D24
que conviene que mires («1234.567» con pista «,»).

- **D24.** `_numero_factura` aplica la regla de miles de 1c. Cubre
  cantidad, valor unitario y pesos, en la factura y en la planilla. Lo que
  sólo se puede leer como miles mal formados queda vacío, como «12x3», y la
  revisión lo marca como hoy.
- **D25.** La revisión avisa, sin frenar, cuando el flete o el seguro
  tienen más de dos decimales. El aviso queda junto a los otros avisos no
  bloqueantes, por ejemplo: «Flete: escribiste «2500,1250». El TXT lleva
  2500,13.». No cambia lo que se lee ni lo que sale en el TXT.

| Pieza | SHA |
|---|---|
| Casos en rojo antes del producto | `8bfde2c` |
| Producto y `CHANGELOG.md` | `1adee11` |
| Ajustes de casos (1d, 1b, valor1) y sabotajes | `36f54a3` |
| Merge de tu rama (`7145201`, sólo `docs/pm`) | `1240c08` |
| **SHA probado:** suite, compileall, smoke | **`1240c08`** |

Tu diff de revisión parte de `91be665`, sólo sobre los archivos de 1d.
El resto de ese rango es lo que trajo tu rama (ESTUDIO-1b, CLIENTE-1c).

## Qué cambió

Toqué estos archivos de producto:
- `proyecto_maria/pdf_extractor.py`
- `proyecto_maria/static/v2/screens/finalize.js`
- `CHANGELOG.md`

- **1. `_numero_factura`.** Llama a `_miles_mal_formados` después del
  control de forma y antes de sacar los espacios. Quité la misma llamada de
  `_monto_factura`, porque el flete y el seguro llegan igual a
  `_numero_factura`. Así la regla vive en un solo lugar. Los casos de 1c
  siguen verdes y sus 10 sabotajes siguen en rojo (abajo).
- **2. `finalize.js`.** Hay dos funciones nuevas:
  - `avisosDeLosMontos(op)` arma un aviso por el flete y otro por el
    seguro. Lo que no se lee o es negativo no suma aviso, porque eso ya lo
    frena la revisión.
  - `alCentavoDelTxt(n)` redondea como `centavos()` del generador. Toma el
    número más corto que escribe el valor y redondea la mitad hacia arriba
    con cuentas de texto, porque `Math.round(2.675*100)` da 267 y el TXT
    lleva 2,68.

  `refrescarAvisos` suma esos avisos a los del despachante. Un caso compara
  la pantalla con `centavos()` sobre todos los importes de prueba. Otro
  genera el TXT y comprueba que `MDDTFLE` es lo que dice el aviso, para
  2500.125, 2.675 y 12.34567.

## Supuestos reversibles

- **El texto del aviso.** Va como «Flete: escribiste «…». El TXT lleva
  …,..». Si el valor llegó como número, por ejemplo de la planilla, «lo
  escrito» es `escribir()` de ese número.
- **El ruido de coma flotante también avisa.** Un seguro de
  0,30000000000000004 dice «El TXT lleva 0,30». Tiene más de dos decimales
  y la tarea no lo exceptúa. `seguro_sugerido` ya viene redondeado al
  centavo, así que sólo puede venir de una celda.
- **Cambié una guarda de SEPARADORES-1b.** «4500.000» con pista «,» en
  `_numero_factura` daba 4500000 y ahora da vacío. Es exactamente lo que
  pide D24, igual que `d5a3f58` en 1c.
- **El arnés de `test_valor1`** suma las dos funciones nuevas, porque
  `refrescarAvisos` ahora las llama. No cambió ningún caso.

## Puertas

Todo es sobre `1240c08`, salvo los sabotajes, que son sobre `36f54a3`.
Entre los dos SHAs sólo cambia `docs/pm`.

| Puerta | Resultado |
|---|---|
| `test_separadores1d.py`, `1c`, `1b`, `1` y `test_valor1.py` | `452 passed, 3 warnings in 82.84s (0:01:22)` |
| `sabotaje_separadores1d.sh 36f54a3` | `OK: los 5 sabotajes dan rojo por la razón esperada`, salida 0 |
| `sabotaje_separadores1c.sh 36f54a3` | `OK: los 10 sabotajes dan rojo por la razón esperada`, salida 0 |
| Suite completa, worktree limpio | `1 failed, 3277 passed, 302 skipped, 2 xfailed, 94 warnings in 504.66s (0:08:24)` |
| `compileall -q proyecto_maria` | rc 0 |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |

Cada sabotaje vuelve a lo de antes, o rompe una guarda:

| Sabotaje | Qué hace | Rojo esperado |
|---|---|---|
| `numero_sin_regla` | la regla sólo en `_monto_factura`, como en 1c | `test_en_la_factura_queda_vacio_y_no_multiplicado[cantidad-…]` |
| `numero_sin_miles` | guarda: también deja vacío lo bien formado con miles | `test_lo_bien_formado_se_lee_como_hoy[1.250-,-1250.0]` |
| `revision_sin_aviso` | la revisión sin el aviso | `test_el_aviso_va_junto_a_los_otros_avisos_no_bloqueantes` |
| `redondeo_math_round` | redondeo con `Math.round` | `test_la_pantalla_redondea_igual_que_el_generador` |
| `aviso_con_dos_decimales` | guarda: con dos decimales también avisa | `test_con_dos_decimales_o_menos_no_hay_aviso[op0]` |

Con `numero_sin_regla` aplicado a mano, todos los rojos son de
`test_separadores1d.py`, y en 1c y en 1 no falla nada. Eso muestra que el
sabotaje vuelve a lo de 1c.

**El único rojo** es
`test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal`,
el de tiempo ya informado en SUFIJOS-1 y 1c. Dice «la subida normal dio
400 a los 30.1 s: … tardó demasiado». 1d no toca `test_excel2.py` ni la
lectura de Excel. Los 12 rojos conocidos de antes ya no aparecen: los cierra
tu `2ff3262`, que está en `1240c08`.

**Lo que no corrí:**
- Ni subagentes adversariales ni `/code-review`: no tengo cuota hasta el
  28/10 a las 18:00 UTC. La autorrevisión es sólo mía, sin independencia.
- `ataque_aislamiento.sh`: no toqué sesión, datos ni permisos.
- La pantalla en un navegador. El aviso está probado con el
  `refrescarAvisos` real en node, con el DOM simulado.

## Comandos

Este muestra sólo lo de 1d:

```bash
git diff 91be665..36f54a3 -- proyecto_maria/pdf_extractor.py proyecto_maria/static/v2/screens/finalize.js \
  tests/test_separadores1d.py tests/test_separadores1b.py tests/test_valor1.py scripts/testing/sabotaje_separadores1d.sh
```

Este tiene que dar `452 passed`:

```bash
python -m pytest -q --no-cov -p no:randomly tests/test_separadores1d.py tests/test_separadores1c.py \
  tests/test_separadores1b.py tests/test_separadores1.py tests/test_valor1.py
```

Este tiene que dar «OK: los 5 sabotajes dan rojo por la razón esperada» y
salida 0:

```bash
scripts/testing/sabotaje_separadores1d.sh 36f54a3 <venv>
```

## Riesgos

- **D24 cambia una sola familia de números de la factura. Lo comparé
  contra `91be665`** en 29 formas habituales de precios y cantidades, cada
  una sin pista, con «,» y con «.». Sólo cambian estas:

  ```
  '1234.567' con pista ','   antes 1234567.0    ahora None
  '12345.678' con pista ','  antes 12345678.0   ahora None
  '1000.000' con pista ','   antes 1000000.0    ahora None
  '2500.125' con pista ','   antes 2500125.0    ahora None
  '123456.789' con pista ',' antes 123456789.0  ahora None
  (y '1234,567', '12345,678', '1000,000', '2500,125' con pista '.')
  ```

  Con la pista que coincide se leen igual que antes: «1234.567» con «.» da
  1234.567. Sin pista, antes y ahora dan vacío, porque son ambiguas.
  - Que la factura diga que la coma es la decimal y aparezca «1234.567» es
    contradictorio. Antes eso entraba al FOB multiplicado por mil; ahora
    queda vacío y la revisión lo marca. Es el lado seguro, pero si un
    proveedor mezcla los separadores, ese renglón ahora pide que lo
    completen a mano.
- **La planilla también cambia.** Las celdas de texto de cantidad, precio
  y peso pasan por `_numero_factura`, así que «0.500.000» en una celda de
  texto queda en 0 y la revisión lo marca. Las celdas numéricas de Excel no
  cambian. Un caso lo cubre.
- **El aviso cubre sólo el flete y el seguro.** Los gastos anteriores al
  FOB y los ajustes también van al TXT con dos decimales y no avisan, porque
  la tarea nombra sólo flete y seguro. Un caso fija que no avisan. Si los
  querés, es otra pieza chica.
- **El aviso se refresca cuando se refrescan los otros avisos de la
  revisión.** No agregué otro disparador.

Última vuelta: Tue Oct 27 20:47:24 UTC 2026

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM, rutina horaria minuto 35. SUFIJOS-1 y SEPARADORES-1c aceptadas. Entregada a revisión SEPARADORES-1d (probada en 1240c08, sabotajes en 36f54a3: 5 de 1d y los 10 de 1c en rojo); nada para decidir. Apenas entregues: DESTINO-1 y PESO-NETO-1 esperan datos del despachante; si no llegaron, la PM deja la siguiente con el veredicto de 1d. Sin cuota de subagentes ni /code-review hasta 28/10 18:00 UTC. Nunca main, sin push --force, sin datos reales del 24/10, nada se publica sin el «dale» de Emi para el SHA, sin Gemini en pruebas, subagentes hasta esfuerzo alto, sin advisor.
