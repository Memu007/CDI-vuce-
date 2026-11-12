# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## IDS-PYTEST (agregado de BORRADOR-1): `estudio1.sh` da rc=0 con pytest 9.2.0 y con 9.1.1, y ningún otro guion mío depende de un id que pytest arma solo. Nada para decidir

| Qué | SHA |
|---|---|
| Arnés | `dd0eab7e` (id del caso y patrón de `estudio1`, padre `c57b645e`) |
| Merges de tu rama | `45309f10` y `2bf38f93` |
| Informe | el commit `docs:` encima de `2bf38f93` |
| Rojo de antes | `c57b645e`, con su propio `estudio1.sh` |
| Verde de después | `dd0eab7e`, con su propio `estudio1.sh` |

**Producto tocado: ninguno.** `chequeo-6` da `producto +0/−0` y `arnés +4/−2`.

**Versión de pytest**

| Entorno | Python | pytest | Qué corrió |
|---|---|---|---|
| El de siempre | 3.12.3 | **9.1.1** | BORRADOR-1 y todo lo anterior, incluidos los 37 ROJO de `estudio1` que te informé |
| Uno nuevo, armado con `requirements.txt` (`pytest>=9.1.0`) | 3.12.3 | **9.2.0** | el rojo de antes y el verde de después de esta pieza |

Tu resultado (36 ROJO, 1 ROJO? y rc=1) y el mío (37 ROJO y rc=0) difieren por la versión de pytest. El producto no tiene nada que ver.

**Resultado**
- **La causa.** pytest 9.2.0 le pone al texto largo del parámetro el id `nombre4`, que es el nombre del argumento más la posición. 9.1.1 usaba el texto mismo, `xxxx…`. El sabotaje buscaba `[xxxxx`.
- **El arreglo.** El caso le da un id propio, `pytest.param("x" * 201, id="largo")`, y el sabotaje busca `[largo]`. Con las dos versiones, el caso junta los mismos cinco ids: `[]`, `[   ]`, `[None]`, `[Estudio\nInventado]` y `[largo]`.
- **Antes y después no son el mismo SHA.** El caso y el patrón cambian juntos:
  - «antes» es `c57b645e` con su guion;
  - «después» es `dd0eab7e` con el suyo.

  Cada corrida usa una copia del guion de su SHA (`git show <SHA>:scripts/testing/sabotajes/estudio1.sh`), y no toqué nada mientras corrían.
- **Rojo de antes, `c57b645e` con 9.2.0: 36 ROJO, `sabotajes sin rojo: 1`, rc=1.**
  ```
  ROJO? | el nombre de más de 200 entra: rojo (salida 1), pero sin «FAILED tests/test_estudio1.py::test_el_alta_rechaza_un_nombre_vacio_o_que_no_sirve[xxxxx»
  FAILED tests/test_estudio1.py::test_el_alta_rechaza_un_nombre_vacio_o_que_no_sirve[nombre4]
  ```
  El sabotaje sí rompió el caso. Lo que no coincidía era el id.
- **Verde de después, `dd0eab7e` con 9.2.0: 37 ROJO, `sabotajes sin rojo: 0`, rc=0.**
  ```
  ROJO  | el nombre de más de 200 entra: dice «FAILED tests/test_estudio1.py::test_el_alta_rechaza_un_nombre_vacio_o_que_no_sirve[largo]»
  ```
- **Verde de después, `dd0eab7e` con 9.1.1: 37 ROJO, `sabotajes sin rojo: 0`, rc=0**, con la misma línea `[largo]`.
- **Mis otros guiones.**
  - Son 42 guiones, con 237 patrones con `[`. Comparé cada patrón con los ids que junta pytest 9.2.0 sobre `dd0eab7e`.
  - Todos coinciden salvo dos que no son texto fijo: `cobro_mp2.sh:250` y `:280` usan `[$fila]`.
  - Cada valor que toma `$fila` (por ejemplo `cancelar_cancela`, `checkout_crea` y `sacar_cancela`) existe como id explícito.
- **Los ids que cambian de 9.1.1 a 9.2.0 en todo `tests/`.** Junté los ids de todo `tests/` con las dos versiones sobre el mismo árbol (`c57b645e`), 6155 de cada lado. Cambian ocho:

| Caso | id con 9.2.0 | Guion que lo nombra | ¿Se rompe? |
|---|---|---|---|
| `test_disco1.py::test_importar_con_una_fila_que_la_base_no_guarda_da_400_y_no_guarda_nada` | `desc0-8413.70.10-Fila…` | `disco1.sh:200` y `:227` buscan `[BBBB` | **Sí. Es de MARIA y no lo toqué: ¿se lo pasás?** |
| `test_disco1.py::test_confirmar_con_algo_que_la_base_no_guarda_da_400_y_no_guarda` | `desc0-8413.70.10-La…` | `disco1.sh:203` y `:220` buscan `[Bomba sintetica-888`, que es otro parámetro | No |
| `test_estudio1.py::test_el_alta_rechaza_un_nombre_vacio_o_que_no_sirve` | `nombre4`, ahora `largo` | `estudio1.sh:134` | Arreglado en `dd0eab7e` |
| `test_maria1a_lectura_factura.py::test_otros_numeros_sucios_quedan_vacios` | `texto3` | ninguno | No |
| `test_maria8_subitems_por_posicion.py::test_el_sufijo_de_un_renglon_se_valida_como_los_otros` | `largo-sufijo1-120…` | `sabotaje_maria8.sh:203` y `:207` buscan `[igual` y `[no_texto` | No |
| `test_org1.py::test_invitar_un_email_que_el_registro_rechaza_400_sin_ocupar_lugar` | `malo5` | `org1.sh:203`, sin `[` | No |
| `test_subitems1.py::test_el_error_del_sufijo_dice_que_subitem` | `sufijo2` | `sabotaje_subitems1.sh:81`, que corta en `[` | No |
| `test_valor1c.py::test_un_general_que_se_usa_sigue_controlado` | `general2-120…` | `sabotaje_valor1c.sh:155`, sin `[` | No |

No corrí `disco1.sh`. Lo de esa fila sale de leer sus patrones contra los ids.

## Decisiones

Nada para decidir. No usé ninguna D de mi rango.

**Supuesto reversible:** el id se llama `largo`. Cambiarlo es una palabra en el caso y otra en el guion.

## Comandos

```bash
# 1. Tu versión de pytest. Para ver el rojo de antes tiene que ser 9.2.0.
python -m pytest --version

# 2. Rojo de antes: termina con «sabotajes sin rojo: 1» y rc=1.
#    La línea ROJO? del nombre de más de 200 busca «[xxxxx» y muestra «[nombre4]».
git show c57b645e:scripts/testing/sabotajes/estudio1.sh > /tmp/e1_antes.sh && bash /tmp/e1_antes.sh c57b645e; echo rc=$?

# 3. Verde de después: termina con «sabotajes sin rojo: 0» y rc=0, con «[largo]» en esa línea.
git show dd0eab7e:scripts/testing/sabotajes/estudio1.sh > /tmp/e1_despues.sh && bash /tmp/e1_despues.sh dd0eab7e; echo rc=$?

# 4. Los cinco ids del caso, iguales con 9.1.1 y con 9.2.0. El último es [largo].
python -m pytest --collect-only -q --no-cov tests/test_estudio1.py 2>/dev/null | grep nombre_vacio
```

## Puertas

| Puerta | Salida |
|---|---|
| `estudio1.sh` sobre `c57b645e`, pytest 9.2.0 | 36 ROJO · `sabotajes sin rojo: 1` · rc=1 |
| `estudio1.sh` sobre `dd0eab7e`, pytest 9.2.0 | 37 ROJO · `sabotajes sin rojo: 0` · rc=0 |
| `estudio1.sh` sobre `dd0eab7e`, pytest 9.1.1 | 37 ROJO · `sabotajes sin rojo: 0` · rc=0 |
| ids del caso, `--collect-only` en `dd0eab7e`, 9.1.1 y 9.2.0 | `[]` · `[   ]` · `[None]` · `[Estudio\nInventado]` · `[largo]`, iguales |
| Patrones de mis 42 guiones contra los ids de 9.2.0 | 237 · 235 coinciden como texto · los 2 `[$fila]` coinciden con cada valor |
| `python -m compileall -q proyecto_maria` | rc=0 |
| `chequeo-6 c57b645e dd0eab7e` | avisos: 0 |

<details><summary>chequeo-6, salida entera</summary>

```
chequeo-6 c57b645e4321e1d41ef86f2b776dbce54b3ff6fc..dd0eab7e7989a1e6ff3c4b2c0d3b582e1ee47d1d: avisos para mirar, no un veredicto
producto +0/−0
arnés +4/−2
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

</details>

**Qué no corrí**
- La suite completa: el cambio es el id de un caso y un patrón.
- Mis otros 41 guiones: los revisé contra los ids que junta pytest, sin ejecutarlos.
- `disco1.sh`, que es de MARIA.
- Subagentes y `/code-review`: el diff son 6 líneas de arnés sin producto.

**Riesgos**
- Un guion nuevo que dependa de un id armado por pytest para un texto largo vuelve a depender de la versión, y hoy nada lo impide.
- `requirements.txt` acepta cualquier pytest desde 9.1.0. Un cambio futuro de ids puede volver a separar tu entorno del mío.

**Archivos de producto tocados:** ninguno.

**Sigue:** CONEXIONES-1 C, sólo arnés.
