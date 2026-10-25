# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## EXCEL-3c y CLIENTE-1b: entregadas

**Resultado:** las dos piezas están hechas. Cada punto tiene su sintético y
su sabotaje en rojo. Los revisores encontraron dos problemas altos en
EXCEL-3c: una regresión de mi primera vuelta y uno que ya estaba en la base.
Los dos están arreglados. Todas las puertas dan verde sobre d527f33 salvo
una: `ataque_aislamiento.sh` da rc=1, pero no por esta pieza. Falla igual en
tu rama (13a0939) desde MARIA-7. Va como D17, con el arreglo listo.
`foco_cliente1.sh` ahora distingue siempre: elegí una tercera opción, que
explico abajo. Falta la prueba con la proforma real del 24/10, que no entra
al repositorio: la hace Emi.

## Decisiones

- **D15 (nueva). La fecha de inicio que se completa desde la operación.**
  `main.py:6934-6938` copia `comprador_fecha_inic_activ` de la operación al
  cliente (`fecha_op[:10]`) sin validar, cuando el cliente no tiene fecha.
  Por ahí todavía puede entrar una fecha que no sirve, por ejemplo
  «20150-01-0».
  - (a) Dejarlo así.
  - (b) Validarla con `_fecha_inic_activ_de_api` (`main.py:5102`). Si no
    sirve, no se copia, y la operación sigue como está.
  - **Recomiendo (b), como pieza chica aparte.** Es la misma regla de
    CLIENTE-1b en el tercer lugar donde se escribe la fecha. No la toqué
    porque la tarea nombraba sólo el alta y la edición.
- **D16 (nueva). La fecha en la importación masiva de clientes.**
  `main.py:6303` guarda `str(record.get("fecha_inic_activ") or "").strip()[:10]`
  sin validar.
  - (a) Dejarlo así.
  - (b) La misma función que en D15. Una fecha que no sirve queda vacía y el
    informe de la importación lo dice.
  - (c) Un `@validates` en el modelo, que cubre todos los lugares de una
    vez, incluido D15.
  - **Recomiendo (b), junto con D15.** (c) es más seguro a futuro, pero toca
    el modelo y cambia el error de los tres lugares a la vez.
- **D17 (nueva). `ataque_aislamiento.sh` no llega a probar G3.** Manda
  `"sbt_sufijo_valor":"01"`, y desde dfa636f (MARIA-7) la API lo rechaza.
  Dice «❌ PUERTA G3 SIN PROBAR: Ana no llegó a generar su MARIA.TXT.» y
  sale con rc=1. Falla igual en tu rama (13a0939).
  - (a) Lo arreglo yo: en la línea 146, el sufijo pasa a
    `AA(DEMO)-AB(DEMO)-CA00-` y se agrega `"cuit_agr":"20111111112"`. Con
    eso da «✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.»,
    `Bloqueado: 22 · Fugas: 0`. Sin el arreglo da `Bloqueado: 19 · Fugas: 0`.
  - (b) Se lo pedís a la Dev MARIA, porque el cambio lo trajo MARIA-7.
  - **Recomiendo (a).** Son dos campos de un script de prueba y la puerta
    hoy está ciega. No lo commiteé porque no es de esta pieza.
- **Para Emi (operación, no una D):** el script de las fechas toma la clave
  de la base con `--base`, y la clave queda en el historial y en la lista de
  procesos. Si lo corre en producción, conviene pasarla con una variable o
  borrar el historial después.

## SHAs (lo que revisaste: e08b4c4)

| Qué | SHAs |
|---|---|
| CLIENTE-1b, producto | be411a5, 780e13d, 1653449 |
| CLIENTE-1b, pruebas y sabotajes | 8029607, 51e013d, bcabb32, 7ad5c82, 9b1a10f, 23936d5, d527f33 (foco) |
| EXCEL-3c, producto (con su CHANGELOG) | 92badcf, e48ea90 |
| EXCEL-3c, pruebas y sabotajes | 5631297, b0f4508, 559dec4, 4ab5ba5 |
| Merges de tu rama | 566abbf, e5f81be, e3736ca (sólo `docs/pm`) |
| Informe | este commit |

## EXCEL-3c, punto por punto (`tests/test_excel3.py`)

| Punto | Qué hace ahora | Pruebas |
|---|---|---|
| R1 | Con el origen combinado, un producto con descripción propia que empieza con «Payment», «Handling» o «Seguro» entra | `test_un_producto_con_una_palabra_de_cargo_y_su_descripcion_se_lee`, `test_con_la_descripcion_combinada_una_palabra_de_cargo_en_otra_columna_no_saca_al_producto` |
| B1 y la familia | Seguro, pago, gastos y handling, con el rótulo en el código o en la descripción y con descripción u origen combinados, quedan sin leer, con aviso | `test_un_cargo_no_entra_como_producto_aunque_venga_una_combinada`, `test_un_cargo_dicho_con_mas_palabras_no_entra_aunque_venga_una_combinada`, `test_un_cargo_con_su_rotulo_combinado_no_suma_la_fila_de_abajo`, `test_la_copia_de_una_descripcion_combinada_se_decide_como_su_fila` |
| R2 | Una cabecera sin código («PVC BLUE») vuelve a darles la descripción a los renglones con código: 540 | `test_una_cabecera_sin_codigo_le_da_la_descripcion_a_los_renglones_con_codigo` |
| G3 | «DT-1-15» bajo «DT-1» no hereda: queda sin leer, con aviso | `test_un_codigo_que_empieza_con_el_del_grupo_no_hereda` |
| D12 (a) | Los renglones que entran sin precio se avisan al subir, desde su fila; no se inventa precio | `test_los_renglones_que_entran_sin_precio_se_avisan_al_subir`, `test_sin_la_especificacion_combinada_los_renglones_sin_precio_quedan_sin_leer`, `test_el_aviso_sin_precio_no_nombra_filas_que_quedaron_sin_leer` |
| Del adversario | «Freight elevator» con el origen combinado es un producto, no el flete | `test_un_producto_que_empieza_como_el_flete_con_el_origen_combinado_es_mercaderia` |
| CHANGELOG | Dice sólo lo probado | — |

**Cómo decide ahora (`main.py:4600-4637`):** sin nada copiado de una
combinada, como antes. Con el origen o la descripción copiados, la fila es
un cargo sólo si su rótulo empieza como un cargo y además dice nada más que
palabras de cargo, de monto o de moneda (`_es_solo_un_cargo`). «Seguro de
carga», «Insurance €40» y «Payment 30% T/T in advance» son cargos. «Payment
terminal POS» y «Seguro de puerta» son productos. La copia de una
descripción combinada se decide igual que su fila de arriba. La lista de
palabras es la parte frágil: si le falta una, un cargo entra como producto.
Por eso el comentario dice que se amplía y no se achica.

**Supuestos reversibles**

- **G3:** «DT-1-15» no hereda de «DT-1». En la proforma, DT-650-BL y
  DT-650-WH son colores distintos, así que un código que empieza con el del
  grupo no prueba que sea el mismo material. Si preferís que herede, es un
  cambio chico y el test lo dice.
- **CLIENTE-1b:** una fecha vacía o `null` se guarda `""` y no NULL, como
  pedía la tarea. Una fila que ya tenía NULL se queda con NULL. La pantalla
  y el TXT tratan igual a los dos.

## CLIENTE-1b

- **Qué hace:** el alta y la edición aceptan `AAAA-MM-DD` (año de 4 cifras,
  fecha que existe) y `DD/MM/AAAA`, y guardan `AAAA-MM-DD`. `null` y vacío
  guardan `""`. Cualquier otra cosa da un 400 que no guarda nada y que el
  formulario muestra. Una edición que no manda la fecha la conserva. El
  aviso de lo que falta para el MARIA pide también la fecha guardada que no
  sirve.
- **La familia** va por POST y por PUT: `null`, `""`, `"None"`,
  `20150-01-01`, `2015-02-30`, `15/03/2015` y `2015-03-15`
  (`tests/test_cliente1b.py`).
- **El script** `scripts/datos/clientes_fecha_inic_activ.py`:
  - sin opciones sólo informa, por id, las fechas que no sirven, sin
    mostrar nada más del cliente;
  - con `--arreglar-none` vacía sólo las «None», también las que tienen un
    tab o un salto, y sólo si la fila sigue igual que cuando la leyó;
  - `--base` es obligatoria, acepta `sqlite:///` y no crea una base que no
    existe.
  - Está probado en una base local (`tests/test_cliente1b_script.py`, 6
    pruebas). Correrlo en producción lo decide Emi.
- No toqué `maria_generator.py`.

### `foco_cliente1.sh`: ni informativa ni una M mayor

Elegí una tercera opción: un sabotaje determinista. Con el temporizador de
10 ms, la variante sin espera falla cuando el temporizador cae entre el foco
y la escritura, y eso depende de la suerte. Ninguna M lo vuelve seguro, y
hacerla informativa deja la puerta sin rojo.

Ahora, en un worktree descartable, el temporizador se cambia por uno que cae
siempre en el peor momento: apenas otro campo toma el foco, lo devuelve a la
razón social antes de que el fill escriba (o a los 3 s, si nadie lo toma).
Por eso:

- con la espera, no puede fallar;
- sin la espera, falla siempre, y con el síntoma: lo escrito en otro campo
  cae en la razón social.

Además corre N veces con el temporizador real de 80 ms. Sale con rc=1 si la
espera falla una sola vez, o si sin la espera alguna de las M corridas no
falla con el síntoma. M=5 por defecto. El producto no se toca.

## Hallazgos de la autorrevisión

**Adversario de CLIENTE-1b (Opus, alto):** 4 hallazgos.

| # | Hallazgo | Qué pasó |
|---|---|---|
| 1 | Media: el script comparaba con `TRIM` y el informe con `strip`, así que una `'None\t'` se informaba pero no se arreglaba | Arreglado en 780e13d |
| 2 | Baja: el año 0000 en la pantalla no tenía prueba | Arreglado en 7ad5c82 |
| 3 | Baja: una ruta sqlite que no existe creaba un archivo vacío y salía con traceback | Arreglado en 1653449 |
| 4 | Baja, operación: `--base` deja la clave en el historial | Nota para Emi, arriba |

Además comparó la API con el generador en 26 entradas raras, sin
diferencias.

**Seguridad de CLIENTE-1b (Sonnet, alto):** 0 hallazgos. Notó que el vacío
ahora se guarda `""` y no NULL (es el supuesto de arriba).

**`/security-review` de todo el rango (Opus, alto):** 0 hallazgos.

**Adversario de EXCEL-3c (Opus, alto, sobre 23936d5..b0f4508):** 6
confirmados y 2 especulativos.

| # | Hallazgo | Qué pasó |
|---|---|---|
| 1 | Alta, regresión mía: un cargo con su descripción combinada en dos filas sumaba la segunda fila al FOB («Payment 30% TT» en B3:B4: total 5950 en vez de 3500) | Arreglado en e48ea90 |
| 2 | Alta, ya estaba en la base: «Freight elevator DEMO» con el origen combinado se leía como flete (sale del FOB 9000) | Arreglado en e48ea90 |
| 3 | Baja: el aviso «sin precio» nombraba filas que no entraron | Arreglado en e48ea90 |
| 4 | Baja: sin columna de origen, entraba la mitad de un producto combinado | Arreglado en e48ea90 (la copia se decide como su fila) |
| 5 | Baja, efecto de R2: una nota sin código («Packing: rolls…») abre grupo, y «DT-9» sin especificación hereda la nota como descripción. El valor queda bien | Riesgo |
| 6 | Media, ya estaba en la base: un «-» en el origen vuelve producto a «Insurance» (+40 sin aviso) | Riesgo |
| — | Especulativos: una NCM con letras combinada hasta un seguro; un grupo abierto por «Insurance» con renglones con medidas debajo | Riesgo, no reproducidos |

**`/code-review high` (sobre b0f4508):** 10 hallazgos.

| # | Hallazgo | Qué pasó |
|---|---|---|
| 1 | La lista de cargos aceptados era corta: «Seguro de carga» o «Insurance fee» entraban como producto | Arreglado en e48ea90 (por palabras de cargo, monto o moneda) |
| 2 | «Freight prepaid» o «Payment … in advance» sin monto entraban | Arreglado en e48ea90 |
| 3 | Una columna Category «Handling equipment» sacaba al producto | Arreglado en e48ea90 |
| 4 | «Payment terminal POS» con el origen vacío, sin combinar, sigue afuera | Riesgo: es la regla de la base, sin combinada |
| 5 | Las monedas «€» y «U$S» no contaban como monto | Arreglado en e48ea90 |
| 6 | `sin_precio` se anotaba antes de saber si la fila entraba | Arreglado en e48ea90 (es el #3 del adversario) |
| 7 | La lista de cargos estaba repetida en dos expresiones | Arreglado: `_CARGOS` es una sola (`main.py:4603`) |
| 8 | Un término muerto en `origen_copiado` | Ya no existe: el código se rehízo en e48ea90 |
| 9 | La tupla de 6 campos y el nombre `es_cargo` reusado | Estilo, no lo toco |
| 10 | Una cabecera sin código hereda a cualquier código siguiente, hasta un total | Riesgo (es lo que pide R2; va con el #5 del adversario) |

## Riesgos

- **Pueden inflar el valor declarado sin aviso:**
  - un «-» en el origen de un seguro (#6 del adversario);
  - «Insurance policy XYZ» con origen combinado entra como producto (3590),
    porque «XYZ» no es palabra de cargo.

  Los dos se ven en la revisión de los ítems. Si querés, van en la pieza
  de D12 (b).
- **Descripción equivocada, con el valor bien:** una nota sin código le da
  su texto a un código sin especificación (#5 del adversario).
- **El aviso «sin precio» dice «lo trae sólo arriba o combinado»** aunque
  el de arriba tampoco lo traiga. El texto es inexacto, pero el número de
  fila es correcto.
- **Los que pediste no tocar siguen igual:** «Ocean freight», el subtotal
  con precio y largo, «10m2 m», el aviso de unidad y R3.
- **CLIENTE-1b:** la fecha todavía entra sin validar por la operación (D15)
  y por la importación masiva (D16).

## Archivos de producto

- `proyecto_maria/main.py`
- `proyecto_maria/static/v2/screens/clientes.js`
- `scripts/datos/clientes_fecha_inic_activ.py`
- `CHANGELOG.md`

## Puertas, sobre d527f33

| Puerta | Salida |
|---|---|
| `compileall -q proyecto_maria` | rc=0 |
| Suite completa | `2181 passed, 102 skipped, 2 xfailed, 26 warnings in 250.68s (0:04:10)` |
| excel1 + excel2 + excel3 + cliente1b + script | `346 passed, 3 warnings in 68.78s (0:01:08)` |
| `test_excel3.py` | `120 passed, 3 warnings in 3.74s` |
| `excel3.sh 4ab5ba5` (difiere de d527f33 sólo en el script del foco) | 69 ROJO, «sabotajes sin rojo: 0», rc=0 |
| `cliente1b.sh d527f33` | 16 ROJO, «sabotajes sin rojo: 0», rc=0 |
| `cliente1.sh d527f33` | 29 ROJO, «sabotajes sin rojo: 0», rc=0 |
| `smoke_friccion.sh` | «==> OK · telemetría + alias session/state + by-cuit protegido», rc=0 |
| `ataque_aislamiento.sh` | «❌ PUERTA G3 SIN PROBAR: Ana no llegó a generar su MARIA.TXT.», `Bloqueado: 19 · Fugas: 0`, rc=1 (D17) |
| Lo mismo, con el arreglo de D17 | «✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.», `Bloqueado: 22 · Fugas: 0`, rc=0 |
| `foco_cliente1.sh`, N=2 M=2 | «con espera, 80 ms: 2 bien, 0 fallas de 2»; «con espera, en el peor momento: 2 bien, 0 fallas de 2»; «sin espera, en el peor momento: 0 bien, 2 fallas de 2 (2 con lo de otro campo en la razón social)»; «tardó 156 s», rc=0 |
| `foco_cliente1.sh`, N=100 M=5 | «con espera, 80 ms: 100 bien, 0 fallas de 100»; «con espera, en el peor momento: 5 bien, 0 fallas de 5»; «sin espera, en el peor momento: 0 bien, 5 fallas de 5 (5 con lo de otro campo en la razón social)»; «tardó 1696 s»; «mediciones con falla: 0»; `rc=0` |

**No corrí:** la e2e completa ni los sabotajes de piezas anteriores (te
tocan antes de publicar). No hubo un segundo adversario sobre e48ea90: lo
cubren el code-review y los 69 sabotajes, pero no es una revisión
independiente.

## Comandos

```bash
git checkout d527f33
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov tests/test_excel3.py tests/test_cliente1b.py tests/test_cliente1b_script.py   # todo passed
PY=<venv>/bin/python bash scripts/testing/sabotajes/excel3.sh d527f33          # «sabotajes sin rojo: 0»
PY=<venv>/bin/python bash scripts/testing/sabotajes/cliente1b.sh d527f33       # «sabotajes sin rojo: 0»
PY=<venv>/bin/python PUERTO=8846 bash scripts/testing/sabotajes/cliente1.sh d527f33   # «sabotajes sin rojo: 0»
PY=<venv>/bin/python N=10 M=5 bash scripts/testing/sabotajes/foco_cliente1.sh d527f33 # «sin espera … 5 fallas de 5 (5 con …)», rc=0
```

## Sigo con

ESTUDIO-1, que ya arranco: MARIA-7 está integrada en tu rama (1fa0b6e).

/compact conservar: Soy la Dev técnica (Dev 1) de CDI, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica (nunca main), rutina trig_011UpBfwEu9TUzoNUrviqoP5 min 15; aviso a la PM principal session_01B7FVQspcEHF7PqNv797wNM con send_message priority next empezando «Dev técnica:». EXCEL-3c y CLIENTE-1b entregadas (lo revisado antes: e08b4c4; puertas sobre d527f33 + este informe). Abiertas para la PM: D15 (fecha desde la operación, recomiendo b), D16 (importación masiva, recomiendo b con D15), D17 (ataque_aislamiento.sh ciego desde MARIA-7, recomiendo a, parche en el scratchpad ataque_parche.diff). Ya decidido: D12 (a) hecho, (b) aparte después de ESTUDIO-1; R3 queda; D8 (b). Próxima D: D18. Sigo con ESTUDIO-1 (estudios de la cuenta aislados por dueño; se eligen donde hoy va cuit_agr, último o único preseleccionado; sin migración, users.cuit de respaldo). Reglas de Emi: sólo me piden la PM o Emi; nada se publica sin su «dale» para el SHA; nunca main; sin secretos ni datos reales (la proforma del 24/10 no entra); no tocar maria_generator.py, controles_maria.py ni el canal/rama de la Dev MARIA; subagentes hasta alto, sin Fable.
