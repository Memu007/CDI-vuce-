# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## EXCEL-3b: entregada

**Resultado:** los cinco puntos de EXCEL-3b están hechos, cada uno con su
sintético y su sabotaje. Los revisores encontraron dos regresiones y yo una
de EXCEL-2; las tres están arregladas. Sobre 1a5053a: 53 sabotajes en rojo,
ninguno sin rojo; la suite completa, 1816 passed, sin rojos. Lo que se
entrega es 7043cf2 (sólo cambia el CHANGELOG respecto de 1a5053a). Falta la
prueba con la proforma real del 24/10, que no entra al repositorio: la hace
Emi.

## Decisiones

- **D12 (nueva). Precio sólo en el primer renglón del grupo (o sólo el
  precio combinado).** Los renglones de abajo traen cantidad, medidas e
  importe, pero no precio. Hoy quedan **sin leer, con aviso** de fila sin
  leer. En la base entraban como productos con precio 0, sin aviso.
  - (a) Dejarlo así: sin leer, con aviso.
  - (b) Si el precio está combinado (`celdas_rellenadas`), el renglón lo
    hereda.
  - (c) Además de (b), sacar el precio de importe ÷ cantidad cuando falta.
  - **Recomiendo (b), como pieza chica aparte.** Sale de la celda combinada,
    que es un dato del archivo. (c) adivina, y un importe redondeado cambia
    el valor en aduana.
- **D8 sigue abierta** (`landing:139`). Recomiendo (b): dejar «NCM».

## SHAs (base 53a441d)

| Qué | SHAs |
|---|---|
| Producto | 14eb492 (con su CHANGELOG), 21567fe, 522e082 |
| Pruebas y sabotajes | fa51544, 5521920, 6922481, 104768e, 1a5053a |
| CHANGELOG | 15309df, 7043cf2 |
| Merge de tu rama | 7cacb05 (sólo `docs/pm`) |
| Informe | este commit |

## Cada punto, con su prueba (`tests/test_excel3.py`)

| # | Punto | Pruebas |
|---|---|---|
| 1 | Sin rótulo ni precio, con largo o total de grupo: no es producto | `test_un_subtotal_sin_rotulo_ni_precio_con_medidas_no_es_un_producto`, `test_una_especificacion_combinada_que_alcanza_al_subtotal_no_lo_vuelve_producto` |
| 2 | Un texto en otra columna no vuelve flete o descuento a un renglón | `test_un_texto_en_otra_columna_no_vuelve_flete_o_descuento_a_un_renglon`, `test_una_nota_de_flete_en_otra_columna_de_un_renglon_no_lo_saca`, `test_el_flete_y_el_descuento_con_el_rotulo_a_la_izquierda_se_leen` |
| 3 | La unidad que sale del encabezado del precio se avisa | `test_la_unidad_que_sale_del_encabezado_del_precio_se_avisa`, `test_la_unidad_de_la_cantidad_y_el_precio_se_avisa_con_las_dos_columnas`, `test_una_unidad_que_sale_solo_de_la_cantidad_no_avisa_del_precio` |
| 4 | El grupo se corta en flete o descuento, y en un código nuevo sin especificación | `test_un_flete_sin_monto_corta_el_grupo`, `test_un_descuento_leido_corta_el_grupo`, `test_un_descuento_con_texto_que_queda_sin_leer_corta_el_grupo`, `test_un_codigo_nuevo_sin_especificacion_no_hereda_la_del_grupo_anterior` |
| 5 | «Descuento …» negativo se avisa y no es producto; «1,5m» no repite la unidad | `test_un_descuento_con_texto_y_monto_negativo_se_avisa_y_no_es_producto`, `test_un_largo_escrito_con_su_unidad_no_la_repite`, `test_un_largo_con_rango_conserva_su_unidad` |

Las demás pruebas nuevas cubren lo que encontraron los revisores: las
combinadas, el `.xls`, «Discount tag labels» y la nota de descuento.

**Supuestos reversibles**

- Punto 3: la unidad del precio sólo se toma si hay una columna total en esa
  unidad. Con «Qty» sin unidad y «Unit price (USD/M)» no queda unidad ni
  aviso; así ya era en EXCEL-3.
- Punto 4: «se avisa» quiere decir que DT-2 sin especificación queda sin
  leer, con el aviso genérico de filas sin leer del semáforo y su número de
  fila. No tiene un motivo propio.

## Hallazgos de la autorrevisión

**Adversario 1 (Opus, esfuerzo alto)**, sobre 14eb492/fa51544:

| # | Hallazgo | Qué pasó |
|---|---|---|
| 1 | Alta, regresión: se perdían flete y descuento con el rótulo en «No.», «S/N» o «Item No.» | Arreglado en 21567fe |
| 2 | Regresión: no se leían las combinadas del `.xls` | Arreglado en 21567fe (fixture `combinada_con_codigo.xls`, sintético) |
| 3 | Media, regresión: con el precio sólo en el primer renglón, los de abajo quedan sin leer | **D12** |
| 4 | Con la especificación y el precio combinados se perdían código y medidas | Arreglado |
| 5 | «Discount tag labels» no abría su grupo | Arreglado en 21567fe |
| 6 | «Ocean freight» entra como producto | Ya pasaba en la base: riesgo |
| 7 | «Descuento comercial» +500 entra como producto; «Special discount» -500 entra como producto de 0 | Ya pasaba en la base: riesgo |
| 8 | Un subtotal con precio y largo se cuenta dos veces | Ya pasaba en la base: riesgo |
| 9 | El aviso de la unidad confundía | Arreglado: nombra las dos columnas |
| 10 | El rango «48-50» perdía la unidad | Arreglado |
| 11 | Un código nuevo sin especificación sólo tiene el aviso genérico | Supuesto del punto 4 |

**`/code-review high`** sobre 53a441d..5521920, 10 hallazgos:

| Hallazgo | Qué pasó |
|---|---|
| El CHANGELOG describía mal el aviso de la unidad y no nombraba el `.xls` | Arreglado en 15309df |
| Con sólo el precio combinado se pierden renglones (`main.py` ~4845) | **D12** |
| Subtotal con la especificación combinada | Arreglado en 522e082 |
| «Descuento comercial» +500 entra como producto | Riesgo (de la base) |
| Un grupo sin código con hijos que traen código se pierde (~4842) | Riesgo, baja |
| Un `cargo` con «-» o «USD -850» tapa el rótulo (~4802) | Riesgo, baja |
| El `.xls` se lee dos veces (~3591) | Riesgo, rendimiento |
| «10m2 m» repite la unidad (~4874) | Riesgo, baja |
| La lógica de la unidad está duplicada en el endpoint (~7623) | Riesgo, mantenimiento |
| De estilo | No lo toco |
| Sabotaje repetido | Lo dejo: comprueba que un segundo test también da rojo |

**Adversario 2 (Opus, esfuerzo alto)**, sobre fa51544..21567fe:

| # | Hallazgo | Qué pasó |
|---|---|---|
| 1 | Alta, `.xls`: un origen combinado hasta «Freight charges» lo volvía producto; con «Freight» en Item se perdía el flete | Arreglado en 522e082 |
| 2 | Media: una nota «Discount applies…» sin precio abría un grupo | Arreglado en 522e082 |
| 3 | Media-baja, `.xls`: una especificación combinada hasta el «Subtotal» lo volvía producto | Arreglado en 522e082 |
| 4 | Con descripción, se ignora el rótulo de la izquierda («Freight» en No.): el flete entra como producto y se pierde un -175 | Ya pasaba en la base: riesgo |
| 5 | «Discount 5%» con -175 legible se descarta; un producto con «100%» queda sin leer | Ya pasaba en la base: riesgo |

**Mía:** una regresión de EXCEL-2, el producto perdía el origen combinado.
Arreglada en 522e082 y cubierta por un sabotaje.

## Riesgos

- Los que vienen de la base y siguen igual: «Ocean freight» y «Descuento
  comercial» positivo entran como productos; un subtotal con precio se suma
  dos veces; con descripción, el rótulo de la izquierda no cuenta.
  **Pueden inflar el valor declarado si nadie lo mira en la revisión.** Si
  querés, son una pieza aparte.
- D12: en la base esos renglones entraban con precio 0; ahora quedan sin
  leer, con aviso. No se pierden sin avisar.
- Se depende de `df.attrs`, que pandas marca como experimental. Lo cubren las
  pruebas del `.xls` y del `.xlsx`.

## Puertas, sobre 1a5053a (el producto es igual en 7043cf2)

| Puerta | Salida |
|---|---|
| `excel3.sh 1a5053a` | 53 ROJO, «sabotajes sin rojo: 0», EXIT 0 |
| Suite completa | `1816 passed, 102 skipped, 2 xfailed, 23 warnings in 166.92s (0:02:46)` |
| `compileall -q proyecto_maria` | ok |
| `test_excel3.py` | 59 passed |
| excel1 + excel2 + excel3 | 234 passed |

**No corrí:** un adversario sobre la tercera vuelta (522e082..1a5053a), la
e2e y `/security-review`. Es lectura de Excel, sin plata cobrada, sesión ni
permisos, pero sí cambia lo que se declara.

## Comandos

```bash
git checkout 7043cf2
PY=<venv>/bin/python bash scripts/testing/sabotajes/excel3.sh 1a5053a   # «sabotajes sin rojo: 0»
python -m pytest -q --no-cov tests/test_excel3.py                        # 59 passed
python -m pytest -q --no-cov --timeout=120                               # 1816 passed, 102 skipped, 2 xfailed
```

(con las variables de entorno de `/entregar` §3)

## Archivos de producto tocados

- `proyecto_maria/main.py`
- `CHANGELOG.md`

Las pruebas son `tests/test_excel3.py`, `tests/fixtures/combinada_con_codigo.xls`
y `scripts/testing/sabotajes/excel3.sh`.

## Sigo con

ESTUDIO-1 cuando integres MARIA-7. Hasta entonces no arranco nada nuevo.

/compact conservar: Soy la Dev técnica (Dev 1) de CDI, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica (nunca main), rutina trig_011UpBfwEu9TUzoNUrviqoP5 min 15; aviso a la PM principal session_01B7FVQspcEHF7PqNv797wNM con send_message priority next empezando «Dev técnica:». EXCEL-3b entregada (base 53a441d; puertas sobre 1a5053a, entrega 7043cf2 + informe). Abiertas para la PM: D12 (precio sólo en el primer renglón, recomiendo (b) heredar si está combinado) y D8 (landing:139, recomiendo (b) dejar NCM). Próxima D: D13. Sigo con ESTUDIO-1 cuando la PM integre MARIA-7. Reglas de Emi: sólo me piden la PM o Emi; nada se publica sin su «dale» para el SHA; nunca main; sin secretos ni datos reales (la proforma del 24/10 no entra); no tocar maria_generator.py, controles_maria.py ni el canal/rama de la Dev MARIA; subagentes hasta alto, sin Fable.
