# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## EXCEL-3e: entregada

**Resultado:** un flete, seguro o descuento bajo una especificación
combinada, con medidas «/», «-», 0 o vacías, ya no entra como producto.
Se lee como flete o descuento, o queda sin leer con aviso de su fila.

Arreglé la causa, no una lista: `_es_una_medida` decide qué es una medida.
Sirve un número mayor que 0, o un texto con una cifra que no empieza con
raya («48-50», «1,5m», «½», «2 m²»). «/», «-», «—», 0, «0.0», «-1 m»,
«–1», «N/A» o «一» no son medida: no abren el renglón del grupo y no se
escriben en la descripción («ancho - m»).

Un producto real con «-» sigue entrando, con o sin la descripción
combinada. Bajo la descripción combinada, un renglón sin rótulo propio con
«-» sigue siendo del grupo y conserva el código. Lo encontró el adversario
como regresión mía, y quedó arreglado en `f127546`.

**Lo que decidís:** D24, abajo. Las D20 a D23 ya las contestaste.

### Decisiones

**D24. Sin combinadas, el renglón sin descripción y con medidas «-» ya no
hereda.**

El caso es `[2, "DT-1", vacío, "-", "-", 1, 4, 2, 8]` debajo de un producto,
sin combinar.
- En la base heredaba la descripción de arriba, con el aviso «tomaron la
  del renglón de arriba».
- Ahora queda sin leer, con su aviso de fila, y el FOB no suma sus 8.

Lo encontró el adversario Opus alto y lo reproduje. Es a propósito: es la
regla de EXCEL-1, sin medidas no se hereda, y es la misma condición que
impide que un subtotal sin rótulo con «-» se vuelva producto.
- (a) Dejarlo así: la fila se ve como sin leer y la persona la carga.
- (b) Que herede con aviso cuando tiene código propio igual al del grupo.
  Un subtotal o un cargo con el código repetido entraría como producto: es
  la puerta de H1 por otro lado.
- **Recomiendo (a).** Perder una fila con aviso se ve. Sumar un cargo al
  FOB sin aviso no se ve.

### SHAs

Base: `1955cac` (lo que ya estaba en origin).

| Commit | Qué es |
|---|---|
| eeef144 | pruebas: el cargo con medidas «/», «-», 0 o vacías, toda la familia |
| c74741d | producto: «/», «-» o 0 no son una medida |
| c95ec27 | pruebas: una medida en texto sigue abriendo el renglón |
| c0ae47d | refactor: `_es_una_medida` sin una guarda que no cambiaba nada |
| 798d2b2 | pruebas: negativos, «N/A», «—», «0.0», «0 m», «½» y la descripción |
| 5c2b8cf | producto: un negativo o «-» no es medida ni va a la descripción, con el CHANGELOG |
| b6dd426 | sabotajes |
| afcb215 | pruebas: «-1 m», «–1», «一», «m²» y la unidad de «½» (del `/code-review`) |
| 4af14da | producto: lo de afcb215, con el CHANGELOG corregido |
| f2755e7 | sabotajes |
| e662ac7 | pruebas: el renglón con «-» bajo la combinada conserva el código (rojo del adversario) |
| f127546 | producto: ese arreglo, con el CHANGELOG |
| 2552158 | sabotajes |
| 14a19e8 | sabotajes: dos patrones viejos y uno que no compilaba; ahora un sabotaje que no compila es ROTO |
| 1d9ef2e | merge de tu rama (SEPARADORES-1 y VALOR-1c). La suite, compileall, smoke y ataque corrieron sobre él |
| 6f798d8 | pruebas: «(1)» como medida negativa, y tres sabotajes que ya no distinguían. **Es el SHA que entrego.** Las cinco de Excel y los sabotajes corrieron sobre él |
| 482ec98 | merge de tu rama (sólo `docs/pm`) |

**Archivos de producto:** `proyecto_maria/main.py` y `CHANGELOG.md`. No
toqué `maria_generator.py`, `controles_maria.py` ni `despachante.js`.

Los tres `.xls` nuevos (`tests/fixtures/h1_*.xls`) son sintéticos: «LONA
DEMO», «DT-1». La proforma del 24/10 no entró.

### Lo que barre la prueba

`test_un_cargo_con_medidas_que_no_son_no_entra_como_producto` cruza todo:
- las medidas «/», «-», 0, vacía y las variantes de raya y texto;
- flete, seguro y descuento;
- importe y precio, o sólo importe;
- el rótulo en Item o en la descripción;
- `.xlsx`.

El `.xls` va con los tres fixtures de `XLS_H1`, uno por cargo.

El producto real con «-» se prueba con y sin la descripción combinada, y el
renglón bajo la combinada en `.xlsx` y `.xls`.

### Hallazgos de la autorrevisión

| Quién | Hallazgo | Qué hice |
|---|---|---|
| Opus alto | con la descripción combinada, el renglón con «-» perdía el código y el producto de arriba su ancho y largo (regresión mía) | arreglado en f127546, con rojo en e662ac7 y dos sabotajes |
| Opus alto | sin combinar, el renglón con código y «-» ya no hereda | **D24** |
| `/code-review high` | «-1 m», «–1» y «－1» contaban como medida | arreglado en 4af14da, con rojo y sabotaje |
| `/code-review high` | «一» (cifra CJK) y «m²» se tomaban mal | arreglado en 4af14da, con rojo y sabotaje |
| `/code-review high` | «½» sin unidad salía sin «m» | arreglado en 4af14da, con rojo y sabotaje |
| `/code-review high` y Opus alto | «Ocean freight» y «Mould fee» (la familia H4) | riesgo alto, abajo: es EXCEL-3f |
| Opus alto | «1x40HQ» y «20GP» cuentan como medida | riesgo, abajo |
| Opus alto | «STD», «FULL» y «A/R» ya no son medida | supuesto, abajo |
| Opus alto | «(5)» se lee como negativo | riesgo bajo |
| Opus alto | «2 PCS» o «USD 5» en una medida | riesgo que ya estaba en la base |
| `/code-review high` | `_es_una_medida` corre dos veces por celda | eficiencia, no lo toco |
| `/code-review high` | la CI saltea el `.xls` si no tiene xlwt | riesgo, abajo |
| yo, al correr los sabotajes | dos sabotajes de `trae_unidad` no encontraban su patrón desde 4af14da (ROTO), y el de «hereda aunque el renglón no tenga medidas» dejaba `main.py` sin compilar: su rojo era el SyntaxError | arreglado en 14a19e8; el script ahora da ROTO si un sabotaje no compila, probado volviendo a poner el paréntesis de más |
| yo, al correr los sabotajes sobre 1d9ef2e | «sin el signo» daba VERDE: era equivalente, porque «-1» y «-1 m» los rechaza igual la guarda de la raya. 3c B1 y 3d daban ROJO? porque esperaban casos que no pasan por la línea saboteada (en 3d, igual desde la base `1955cac`) | arreglado en 6f798d8: caso nuevo «(1)», en el que decide el signo, y 3c B1 y 3d esperan cada uno un caso distinto de la copia de un cargo con texto en Item |

### Puertas

La suite, compileall, smoke y ataque corrieron sobre `1d9ef2e`; de ahí a `6f798d8` cambian sólo `tests/test_excel3.py` y `excel3.sh`. Las cinco de Excel y los sabotajes corrieron sobre `6f798d8`.

| Puerta | Salida |
|---|---|
| Suite completa (worktree limpio, 1d9ef2e) | `12 failed, 2985 passed, 102 skipped, 2 xfailed, 29 warnings in 314.28s (0:05:14)`; las mismas 12 fallan en la base `1955cac` (`12 failed, 2491 passed, …`). Ver «Rojos» |
| Las cinco de Excel (6f798d8) | `861 passed, 5 warnings in 74.76s (0:01:14)`; los 24 nuevos son «(1)», y los 2 warnings de más son los `SyntaxWarning '\-'` de `pdf_extractor.py`, que salen sólo sin caché de compilación (en 1d9ef2e: `837 passed, 3 warnings`) |
| compileall | rc=0 |
| smoke | «==> OK · telemetría + alias session/state + by-cuit protegido», rc=0 |
| ataque | «✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.», rc=0 |
| `sabotajes/excel3.sh 6f798d8` | 96 ROJO, «sabotajes sin rojo: 0», exit 0 |

### Rojos de la suite (no son de EXCEL-3e)

Las mismas 12 fallan en la base `1955cac`, con la misma lista (`diff` vacío).
- **11 son del presupuesto compartido:** con la suite entera dan 402
  «Alcanzaste el límite de 15 operaciones del plan Premium». Corridas solas,
  con una base nueva, pasan. Son las que la CI deselecciona.
- **1 es mía, de CLIENTE-1c:** `test_guardar1::test_datos_largos_de_la_operacion_no_impiden_guardarla`
  falla también sola: `assert [('',)] == [('2020-01-15',)]`. La operación trae
  «2020-01-15T00:00:00» y desde CLIENTE-1c esa fecha no se copia a la ficha
  (antes se cortaba a diez caracteres). Es una regresión de CLIENTE-1c, que ya
  está en origin. La arreglo en CLIENTE-1c, que es lo que sigo ahora, con su
  rojo antes.

### Lo que no se corrió

- La suite completa sobre 6f798d8: corrió sobre 1d9ef2e, y lo que cambia después son sólo pruebas de Excel y el script de sabotajes.
- Postgres: no hay cambios de base.
- Una proforma real: las pruebas usan sintéticos.

### El merge de tu rama

- **Conflicto en `main.py`:** en `generate_maria_endpoint` quedaron las dos
  líneas, primero el estudio de ESTUDIO-1 y después «sin productos» de
  VALOR-1c. `test_estudio1`, `test_valor1c` y `test_valor1`: `131 passed`.
- **Conflicto en `CHANGELOG.md`:** quedaron las entradas de las dos ramas.
- **compileall:** muestra dos `SyntaxWarning: invalid escape sequence '\-'`
  en `pdf_extractor.py` (927 y 936). Vienen con tu rama, de la Dev MARIA: no
  es un error, y no lo toqué.

### Riesgos (sin arreglar, como pediste)

- **H2, H3 y H6:** siguen como en tu devolución.
- **«Seguro de carga» con «/» combinada:** sigue igual.
- **Alto. H4:** «Ocean freight» y «Mould fee» entran como producto. Va en
  EXCEL-3f, con aviso.
- **Medio.** «1x40HQ» o «20GP» en una medida cuentan como medida: un flete
  con eso pasa por renglón del grupo.
- **Supuesto reversible.** «STD», «FULL» y «A/R» ya no son medida: un
  renglón con eso y sin cifra no hereda, y queda sin leer con aviso.
- **Bajo.** «(5)» se lee como negativo y no es medida.
- **Bajo.** «2 PCS» o «USD 5» en una medida cuentan como medida: ya era así
  en la base.
- **CI.** Sin xlwt, la CI saltea los casos `.xls`. Acá corrieron con xlwt.

### Comandos

```bash
git fetch origin claude/dev-tecnica && git checkout 6f798d8
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov -p no:randomly tests/test_excel1_lectura.py tests/test_excel1_txt.py tests/test_excel2.py tests/test_excel3.py tests/test_maria5_peso_excel.py   # 861 passed
PY=$(command -v python) bash scripts/testing/sabotajes/excel3.sh 6f798d8   # 96 ROJO, «sabotajes sin rojo: 0»
python -m pytest -q --no-cov tests/test_excel3.py -k conserva_el_codigo   # 6 passed (en f2755e7 dan 6 failed)
```

## Lo que sigue abierto de antes

- **ESTUDIO-1:** aceptada. ESTUDIO-1b va con D23 (b), en una tabla aparte,
  con los 400 del `estudio_id` y del nombre, y con los dos riesgos que
  pediste anotar.
- **EXCEL-3f:** D21 (b) y D22 (b), con la familia H4 sólo con aviso.
- **D20:** (a), queda así.

## Sigo con

CLIENTE-1c, que ya está empezada (`d2df3c4` y `8b65b6b`). Después vienen
ESTUDIO-1b, EXCEL-3f y GUARDAR-2.

/compact conservar: Soy la Dev técnica (Dev 1) de CDI, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica (nunca main), rutina trig_011UpBfwEu9TUzoNUrviqoP5 min 15; aviso a la PM principal session_01B7FVQspcEHF7PqNv797wNM con send_message priority next empezando «Dev técnica:». EXCEL-3e entregada en 6f798d8 (base 1955cac; puertas: suite en 1d9ef2e, Excel y sabotajes en 6f798d8; producto main.py y CHANGELOG; arreglo final f127546), abierta D24 (renglón con código y «-» sin combinar no hereda; recomiendo a). Próxima D: D25. Sigo con CLIENTE-1c (ya hay d2df3c4 y 8b65b6b en origin; tests/test_cliente1c.py; falta test_guardar1::test_datos_largos_de_la_operacion_no_impiden_guardarla: la fecha con hora queda vacía, D15 b, supuesto reversible; y las notas de CLIENTE-1b: --base sin la clave en el error, dígito de ancho completo), después ESTUDIO-1b (D23 b tabla aparte, 400 para estudio_id "null"/"None"/"N/A"/espacios, nombre sin U+200B–200F/202A–202E/2066–2069 ni vacío; riesgos cuit_valido 00000000000 y estudio borrado durante la generación), EXCEL-3f (D21 b, H4 con aviso, D22 b, H5 opcional) y GUARDAR-2 (desde 2d930c5 en claude/dev1-tecnica + punto 2 de «Qué sigue» de CIERRE-RETOMA-2026-10-24.md). Reglas de Emi: sólo me piden la PM o Emi; nada se publica sin su «dale» para el SHA; nunca main; sin secretos ni datos reales (la proforma del 24/10 no entra); no tocar maria_generator.py, controles_maria.py, despachante.js ni el canal/rama de la Dev MARIA; subagentes hasta alto, sin Fable.
