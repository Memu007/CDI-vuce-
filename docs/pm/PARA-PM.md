# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## EXCEL-3f, con H1-bis: entregada en `8c63c37`

| Qué | SHA |
|---|---|
| H1-bis, producto | `6be261c` |
| H1-bis, pruebas y sabotajes | `b24daa0` |
| EXCEL-3f, producto | `e330340`, `42f4e42`, `d9e728d` (refactor, abajo) |
| EXCEL-3f, pruebas y sabotajes | `d513219`, `41011f2`, `d5da28c`, `2fdd4e1`, `b3e4bcb` |
| Merges de tu rama (`7145201`, `ea64a9c`, `89a0fde`) | `c59a873`, `b2eadb8`, `8c63c37` (lo que se entrega) |
| Merges posteriores, sólo `NOW.md` (`5a5052d`, `f5953eb`) | `847d7b9`, `06c4461` |
| Informe | este commit |

Tu diff de revisión desde `3aba9c2` trae también lo de la Dev MARIA que vos
integraste (`e9981e5` y SEPARADORES-1d). Lo mío solo, sin eso:
`git diff 89a0fde..8c63c37` (7 archivos, +539 −39; `89a0fde` es la punta de
tu rama, integrada entera).

**Suite en `8c63c37`: 0 rojos.** Un caso de `test_excel2` está al borde de
su corte de 30 s en esta máquina: en una corrida anterior (`2fdd4e1`) salió
rojo, y en la base `7145201`, sin lo mío, sale igual (1 de 5). Va en
«Riesgos» con la serie. No lo toqué: no es de esta pieza.

**Nada para decidir.** Lo que elegí sin que se pidiera va en «Supuestos».

## 1. H1-bis: la clave de `--base` como la escriba quien sea

- **La familia, no el ejemplo.** Antes se tapaban la clave y tres formas
  fijas (`quote` sin lista segura y `quote_plus`). Ahora cada secreto se
  busca con un patrón que, carácter por carácter, acepta: el carácter tal
  cual, su `%XX` (mayúscula o minúscula, UTF-8), «+» por el espacio, y cómo
  lo escriben Python (`repr`/`ascii`: `\t`, `\xf1`, `\'`) y JSON
  (`\u00f1`, `\"`). No depende de qué lista de «no escapar» use SQLAlchemy o
  el driver: `quote(clave, safe=" +")` de SQLAlchemy cae adentro, y también
  cualquier otra lista.
- Un pedazo del host que resulta ser la clave escrita de otra forma ya no
  queda «visible»: se tapa.
- Tu ejemplo `QZXW KJVB|NMPL` y ocho claves más (espacio con `|`, `%`, `"`,
  `/`, `+`, `\`, `ñ`, tab, las dos comillas) × ocho formas de escribirla
  (la de SQLAlchemy, `quote`, `quote` sin lista, `quote_plus`, `%xx` en
  minúscula, `repr`, `ascii`, JSON): 72 casos. Más un fuzz de 400 claves al
  azar con separadores, blancos y otros alfabetos, con el error repitiendo
  `render_as_string(hide_password=False)` y las otras formas. Fuera de la
  suite corrí el mismo fuzz con dos semillas más, 5000 claves cada una: 0
  fugas.
- **Sabotajes en `cliente1c.sh`:** sin «+» por el espacio, sin `%xx` en
  minúscula, sin las formas de Python y de JSON, sin tapar el pedazo del
  host. Todos en rojo (abajo).

## 2. EXCEL-3f

Todo lo nuevo **sólo suma un aviso que nombra la fila**: no saca nada del
FOB que antes entraba. Lo único que cambia el FOB es el plural (punto 1).

1. **Plurales y «fee».** «Fletes», «Freights», «Seguros», «Insurances»,
   «Bank fees», «Fee», «Payments», «Shipping costs»… se leen como el cargo
   en singular: el flete va a la operación y lo demás a filas sin leer,
   como «Freight» o «Insurance».
2. **D22 (b).** Un cargo con su propio origen («Insurance», «China») o
   «Gastos administrativos» con su origen entra como producto, con el aviso
   «N renglón(es) parecen un cargo y entraron como producto: …».
3. **Familia H4, el cargo que no viene primero.** Los nueve de la tarea
   («Ocean freight», «Sea freight», «Air freight», «Packing charges»,
   «Inland freight», «Courier DHL», «Comisión bancaria», «THC»,
   «2. Insurance») entran con ese aviso, en las cuatro formas (origen
   combinado o no, rótulo en descripción o en Item) y en xls. La regla: todo
   lo que dice el rótulo es de cargo y al menos una palabra lo es por sí
   sola. Un producto que comparte una palabra no se avisa: «Power bank»,
   «Air fryer», «Packing tape», «Courier bag», «Sea salt», «Bank card
   reader», «Feeder», «Container».
4. **Una fila con su propia NCM no lleva el aviso**: es mercadería, como
   antes.
5. **H1, la descripción escrita otra vez.** «Freight» en Item con «LONA
   DEMO» escrita en la descripción y medidas: entra como antes, con el aviso
   de su fila. La fila de abajo que copia la descripción no hereda el aviso.
   «Freight included», «Handling equipment», «A2» o «#3» en Item son una
   nota: sin aviso.
6. **H3, texto de contenedor como medida.** Elegí avisar, no cambiar
   `_es_una_medida`: «Freight» o «Freight 1x40HQ» con «1x40HQ», «20'» o
   «40'HC» en las medidas entra con el aviso de su fila. «Freight» en la
   descripción con eso sigue siendo flete, como antes.
7. **H5.** El aviso del flete nombra las filas como los demás: «de la fila
   3» con una, «de las filas 3, 4, 5, 6, 7 y N más» con más de cinco.
8. El texto del aviso pasó de «empiezan como un cargo» a «parecen un cargo»:
   ahora incluye cargos que no empiezan así.

**Hallazgo propio de `/code-review` (`42f4e42`):** con las palabras nuevas
(«container», «express», «packing») en la lista de siempre, «Insurance
container» con el origen combinado salía del FOB y «Freight express»
perdía el aviso de flete dudoso. Ahora esas palabras viven en otra lista
que sólo suma el aviso; casos y sabotaje en `d5da28c` y `2fdd4e1`.

**Refactor después de la corrida de sabotajes (`d9e728d`).** Tres sabotajes
viejos de `excel3.sh` (3b, 3c y 3d) dejaron de servir con 3f: dos no
encontraban su patrón y el de 3d («el rótulo dudoso entra como producto
común») quedaba verde. El verde era real: la rama `copiada` ponía el mismo
aviso que el bloque nuevo de D22, y cada copia tapaba el sabotaje de la
otra. Saqué la de `copiada` (dos líneas): el aviso queda en un solo lugar y
el comportamiento no cambia (`test_excel3`: 958 passed antes y después).
Los tres sabotajes apuntan ahora al código de 3f (`b3e4bcb`); el de 3d da
rojo en
`test_un_cargo_con_palabras_de_mas_no_cambia_el_fob_sin_un_aviso_con_su_fila[Gastos administrativos-origen_rotulo_en_descripcion]`.

## Supuestos (los podés rechazar)

- H3 con aviso, sin tocar `_es_una_medida`: cambiarla movía la lectura de
  todas las medidas de la planilla.
- El aviso nuevo exige que la fila no tenga NCM propia (`not pieza`).
- «parecen un cargo» en vez de «empiezan como un cargo».
- Los plurales también entran a la lista que reconoce un rótulo de cargo en
  el resto del lector (por ejemplo «Seguros» como rótulo de columna).

## Riesgos

| Riesgo | Severidad | Detalle |
|---|---|---|
| El rótulo de Item puede venir de Part No. o Transporte | baja | `rotulo_aparte` lee las columnas a la izquierda de la descripción. «Courier» en una columna de transporte, sin NCM, daría el aviso de más. Sólo aviso, no cambia el FOB. |
| «Shipping container 20GP» como producto | baja | Todo lo que dice es de cargo y «shipping» lo es por sí sola: aviso de más. Con su NCM no se avisa. |
| Los plurales amplían el descarte | baja | Una fila «Fees» o «Seguros» sin NCM ni origen sale del FOB como su singular. Es lo pedido; lo anoto porque también toca dónde se reconoce un rótulo. |
| Un código como «THC-200» | baja | Sin NCM ni más texto, se avisa como cargo. Sólo aviso. |
| Sabotaje M de H1-bis queda verde | baja, sin fuga | Sacar `unquote(s)` de `_tapar` (línea de antes de H1-bis) no da rojo: `url.password` ya trae la clave decodificada. No la saqué: el caso de un pedazo escapado fuera de la clave no lo pude armar, y sacarla es ampliar. |
| `test_excel2::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope…` | media, no es de 3f | Rojo en la suite sobre `2fdd4e1` (verde sobre `8c63c37`): «la subida normal dio 400 a los 30.0 s». En esta máquina (4 núcleos) la subida normal tarda ~30 s y el corte de la validación es 30 s: está al borde. Serie alternada, sola, 5 por SHA: base `7145201` (sin lo mío) 200/400/200/200/200 en 32.0/30.0/32.4/30.7/29.6 s; `2fdd4e1` 200/400/200/200/200 en 31.1/30.0/31.4/30.6/31.1 s. Mismo reparto: el corte está en `file_security.py`, que no toqué. Cualquier máquina más lenta lo pone rojo; queda para quien tenga EXCEL-2. |
| Lo de tu lista | — | Cargo en el medio de una combinada, Item «A2», rótulo en columna de notas, Unicode raro en medidas; de H1-bis, lo del veredicto. No los toqué. |

## Hallazgos de la revisión

| Hallazgo | Quién | Qué pasó |
|---|---|---|
| Palabras nuevas sacaban «Insurance container» del FOB y el aviso de flete dudoso a «Freight express» | `/code-review high` | Arreglado en `42f4e42`, casos y sabotaje |
| Fila con su NCM llevaba el aviso | `/code-review high` | Arreglado en `42f4e42`, casos y dos sabotajes |
| `rotulo_aparte` lee Part No. y Transporte | `/code-review high` | Riesgo, arriba |
| «Shipping container 20GP» | `/code-review high` | Riesgo, arriba |
| Plurales amplían el descarte | `/code-review high` | Riesgo, arriba |
| Recorrido duplicado de las palabras | `/code-review high` | No lo cambié: no cambia resultado |
| Sabotajes de `excel3.sh` que perdieron su patrón con 3f | corrida de sabotajes | Arreglados en `2fdd4e1` |
| 3b-3#1 y 3c R1 sin patrón; 3d verde porque el aviso estaba dos veces | corrida de sabotajes sobre `2fdd4e1` | Saqué la copia de `copiada` (`d9e728d`) y reapunté los tres (`b3e4bcb`) |

**No corrí los subagentes adversariales:** sin presupuesto hasta el
2026-10-28 18:00 UTC. La revisión independiente queda para vos.

## Puertas, sobre `8c63c37`

| Puerta | Salida |
|---|---|
| Suite completa, worktree limpio | `3845 passed, 102 skipped, 2 xfailed, 92 warnings in 470.50s (0:07:50)`, 0 rojos |
| `compileall -q proyecto_maria` | salida 0 (dos `SyntaxWarning` de `pdf_extractor.py:927` y `:936`, de `a77e6ad`, 7 de octubre: no son míos) |
| `smoke_friccion.sh` | `OK · telemetría + alias session/state + by-cuit protegido`, salida 0 |
| `cliente1c.sh 8c63c37` | 44 ROJO, `sabotajes sin rojo: 0`, salida 0 |
| `excel3.sh 8c63c37` | 112 de 112 en ROJO; ningún VERDE, ROTO ni ROJO?. En dos tramos (abajo). |
| `test_excel3.py` antes y después del refactor | `2fdd4e1`: `958 passed`; `d9e728d`: `958 passed` |

**`excel3.sh` en dos tramos.** El contenedor se reinició dos veces y mató la
corrida (unos 70 min). El segundo intento llegó a 92 sabotajes, todos en
ROJO, y se cortó sin la línea final. Los 20 que faltaban los corrí con una
copia del script de `8c63c37`, igual byte a byte salvo una línea que saltea
los nombres que ya habían dado ROJO. El chequeo de base en verde corrió
igual, y cada sabotaje es independiente: arranca de `git checkout` del
producto. El segundo tramo dio 20 ROJO, `sabotajes sin rojo: 0`, salida 0.
Entre los dos tramos están los 112 sabotajes del script: 110 llamadas, más
2 del bucle de 3b#5. La corrida de un tirón está en «Para reproducir».

El rojo de borde de `test_excel2` no salió en esta corrida: sigue en
«Riesgos», porque en `2fdd4e1` y en la base `7145201` salió 1 de 5.

**No corrí:** los adversarios (sin presupuesto), `ataque_aislamiento.sh`
(no toqué datos, sesión ni permisos) y la CI de `ci.yml` (corre cuando
suba).

## Para reproducir

```bash
git fetch origin claude/dev-tecnica && git checkout 8c63c37
git diff 89a0fde..8c63c37 --stat                       # 7 archivos, +539 −39: sólo lo mío
bash scripts/testing/sabotajes/cliente1c.sh 8c63c37    # «sabotajes sin rojo: 0», salida 0
bash scripts/testing/sabotajes/excel3.sh 8c63c37       # «sabotajes sin rojo: 0», salida 0 (~70 min)
python -m pytest -q --no-cov tests/test_excel3.py tests/test_cliente1b_script.py
# el rojo de borde de test_excel2, en la base y en lo mío (cada uno ~31 s; alguno da 400 en ~1 de 5):
python -m pytest -q -s --no-cov tests/test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal
```

## Archivos de producto que toqué

`proyecto_maria/main.py` (también el refactor `d9e728d`),
`scripts/datos/clientes_fecha_inic_activ.py`, `CHANGELOG.md`.

## Sigo con

GUARDAR-2, desde `2d930c5`. Si tu veredicto trae una devolución, va
primero.

/compact conservar: Soy la Dev técnica (Dev 1) de CDI, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica (nunca main), rutina trig_011UpBfwEu9TUzoNUrviqoP5 min 15; aviso a la PM principal session_01B7FVQspcEHF7PqNv797wNM con send_message priority next empezando «Dev técnica:». Entregué EXCEL-3f con H1-bis en 8c63c37 (base 3aba9c2; lo mío solo: 89a0fde..8c63c37), sin D abiertas. Sigo con GUARDAR-2 desde 2d930c5 (rama vieja claude/dev1-tecnica, sobre 1cdfe49), lo que falta está en CIERRE-RETOMA-2026-10-24.md, «Qué sigue», punto 2. Reglas de Emi: sólo me piden la PM o Emi; nada se publica sin su «dale» para el SHA; nunca main; sin secretos ni datos reales (la proforma del 24/10 no entra); no tocar maria_generator.py, controles_maria.py, despachante.js ni el canal/rama de la Dev MARIA; subagentes hasta alto, sin Fable; sin presupuesto para subagentes hasta 2026-10-28 18:00 UTC.
