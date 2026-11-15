# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Entrega D252 (a) sobre `bd009cc` (2026-11-15 04:35 UTC)

**Resultado.** Tu criterio de D252, puntos 1 a 4, se cumple en `bd009cc`. Base: `993825b`.
Toca dos archivos: `tests/test_maria8_subitems_por_posicion.py` (de 77 a 83 pruebas) y
`scripts/testing/sabotaje_maria8.sh` (de 43 a 63 sabotajes). `producto +0/−0`.
Lo medí todo otra vez en esta sesión, sobre `bd009cc`:
- los 115 cambios, contra la base y contra el archivo;
- los 41 verdes, contra el conjunto ancho;
- los 32 que quedan verdes, contra «el resto» y contra `test_excel3.py` con `xlwt`;
- el guion entero, las anclas, `chequeo-6` y un `/code-review high 993825b..bd009cc`.

De la sesión anterior quedan sin salida (no conservada) los nueve adversarios y las ocho
primeras `/code-review`.

**Lo que decidís vos:**

1. **D255** (`en_renglones` del arancel no decide nada). Recomiendo (a), una línea para la
   cola de limpieza.
2. **D256** (el lugar del aviso de cada renglón frente a «Sub-ítems:»). Recomiendo (a), límite
   escrito.
3. **D257** (27 verdes). Recomiendo **(b)**: una pieza chica sólo para los grupos. Ya está
   medido: «el resto» no atrapa ninguno de los 11 de grupos.
4. **Supuesto 1.** Doce de los 20 sabotajes nuevos no los pediste. `/code-review` los marca
   contra §6 («Guion de sabotaje propio sólo en lo que pide revisión más fuerte»). Si sobran,
   se sacan; los 8 que pediste quedan.

**El rojo de `test_despacho1b` (riesgo 2): no lo reproduje y no tengo su causa.**

| corrida | resultado |
|---|---|
| la prueba sola, sin carga | 60 de 60 verdes |
| la prueba sola, con carga 5,8 en 4 núcleos | 200 de 200 verdes |
| `leer_despacho(una_hoja_cara(), limite_cpu_s=0.05)` 10 000 veces, en un proceso con unos 3 millones de objetos vivos | ninguna `_DemasiadoTrabajo` escapada, el temporizador y el manejador de `SIGPROF` siempre devueltos, ningún resultado distinto |
| `sufijo_sin_strip` contra «el resto», solo | `1264 passed, 2 xfailed` |
| «el resto» con otros cambios | 32 corridas más, todas verdes |

En la sesión anterior la expliqué «por carga», y eso no se sostiene. El tope usa
`ITIMER_PROF`, que cuenta la CPU del proceso, no el reloj: siete pytest en cuatro núcleos no
le cambian la cuenta. La salida de ese rojo no se conservó, así que no hay traza que mirar.
Queda como **no reproducido, causa desconocida**. No es de D252: `despacho_lector.py` no
llama a nada de lo que se cambia. Si vuelve a aparecer, la salida se guarda entera.

| qué | SHA |
|---|---|
| base (tu rama hasta `952ef22`, mi merge) | `993825b` |
| pruebas: el aviso de cada renglón pasa a datos (salteados, uno solo en el medio, tres ítems); sabotajes 44 a 52 | `a29acdd` |
| pruebas: ítem de seis renglones y un renglón que no trae sufijo, por el adversario 1 | `9dbcd87` |
| pruebas: dos renglones solos en el medio, un grupo de dos y el aviso de la operación, por el adversario 2 | `c0a05f8` |
| pruebas: el aviso de la operación sale antes que el de un ítem solo, por el adversario 3 | `cb4076e` |
| pruebas: los datos son pedidos que generan, por `/code-review` | `11d0a6a` |
| pruebas: el orden entre dos ítems solos, por el adversario 5 | `04ee626` |
| pruebas: el último renglón del pedido cuenta para el aviso de la operación, por el adversario 6 | `9176837` |
| pruebas: un renglón solo que es el último del pedido, por el adversario 7 | `44d6856` |
| pruebas: uno solo antes del ítem y el pedido donde nadie va junto, por el adversario 8. **Lo que se entrega** | `bd009cc` |
| tus merges (`7f85fa9`, `b6ec77d`, `7dcf62c`; sólo `docs/pm/`) y mis notas de pausa y retomada | `dd3730d` a `7ce8a99` |
| informe | el commit siguiente |

`arnés +157/−8`: el archivo de pruebas suma +63/−6 y el guion +94/−2. Ningún otro archivo
cambia entre `993825b` y `bd009cc`. Son nueve commits, y cuatro arreglan algo que rompí yo en
uno anterior de esta misma entrega (abajo, «Cuatro cosas que hice mal»). Ninguna de las
cuatro llega a `bd009cc`: lo mide la tabla del apéndice.

## Comandos

`<venv>` es un entorno con `requirements.txt`. Cada línea dice lo que tiene que mostrar.

```bash
# 1. el guion entero, unos 9 minutos
env -u DATABASE_URL -u ENVIRONMENT scripts/testing/sabotaje_maria8.sh bd009cc <venv> > m8.log 2>&1; echo rc=$?   # rc=0
sed -n 2p m8.log          # VERDE  sin sabotaje: … 83 passed …
grep -c '^ROJO' m8.log    # 63
grep -c FALLA m8.log      # 0
grep -E '^ROJO +(aviso_renglon_por_puesto|aviso_renglon_tope_4|aviso_renglon_tope_2|aviso_renglon_solo_el_segundo|aviso_renglon_de_corrido|aviso_renglon_seguidos|en_renglones_de_corrido|arancel_en_renglones_de_corrido):' m8.log
#    tus ocho filas: 4, 2, 2, 5, 3, 3, 2 y 1 failed
tail -1 m8.log            # OK: los 63 sabotajes dan rojo por la razón esperada

# 2. anclas y §6
<venv>/bin/python scripts/testing/anclas_perdidas.py bd009cc | head -4   # 2534 anclas; las tres «perdida» en 0
python3 docs/pm/herramientas/chequeo-6.py 993825b bd009cc               # producto +0/−0, arnés +157/−8, avisos: 0

# 3. un verde de D255 y uno de D257 B, contra el archivo y contra «el resto» (unos 6 minutos cada uno)
git worktree add -q --detach /tmp/d252 bd009cc && cd /tmp/d252
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
ancho=$(ls tests/test_maria*.py tests/test_sufijo*.py tests/test_avisos*.py tests/test_excel3.py tests/test_orden1.py tests/test_valor1c.py)
resto=$(grep -lE 'maria_generator|supuestos|sufijo' tests/test_*.py | grep -vxF "$ancho")   # 21 archivos
for cambio in ' and n not in en_renglones:|:' 'if item["grupo_id"] not in grupos:|if not grupos:'; do
  git checkout -q -- proyecto_maria/
  <venv>/bin/python - "$cambio" <<'EOF'
import pathlib, sys
viejo, nuevo = sys.argv[1].split("|")
p = pathlib.Path("proyecto_maria/core/maria_generator.py"); s = p.read_text()
assert s.count(viejo) == 1; p.write_text(s.replace(viejo, nuevo))
EOF
  for pruebas in tests/test_maria8_subitems_por_posicion.py "$resto"; do
    env -u DATABASE_URL -u ENVIRONMENT <venv>/bin/python -B -m pytest -q --no-cov -p no:cacheprovider \
      --timeout=120 $pruebas | tail -1   # 83 passed; después 1264 passed, 2 xfailed (las dos veces)
  done
done
git checkout -q -- proyecto_maria/ && cd - && git worktree remove --force /tmp/d252
```

Los dos cambios del bloque 3 son las filas 16 y 88 del apéndice. Corrí el bloque tal como está
escrito, con mi venv, a las 04:33 UTC: `83 passed`, `1264 passed, 2 xfailed`, `83 passed`,
`1264 passed, 2 xfailed` y `rc=0`. Al final, `/tmp/d252` ya no está.

## Decisiones

Sobre `bd009cc` medí 115 cambios de las líneas de estos avisos. Uno está repetido, así que son
114 distintos.

| | cuántos |
|---|---|
| rojo en este archivo | 74 |
| verde en este archivo y rojo en otra prueba del conjunto ancho | 8 |
| verde en todo (D255: 3; D256: 2; D257: 27) | 32 |
| repetido (la fila 89 es el mismo cambio que la 53) | 1 |

Los 32 verdes dan verde en las cuatro mediciones: este archivo (`83 passed`), el conjunto
ancho (`2092 passed, 234 skipped, 1 xfailed`), `tests/test_excel3.py` con `xlwt`
(`958 passed`) y «el resto» (`1264 passed, 2 xfailed`). Ninguno cae dentro de tu criterio.
Lo que vería el despachante lo medí sobre la lista de avisos que devuelve
`supuestos_declarados`, sin abrir el navegador, salvo donde dice «no medido».

**D255. En los avisos del arancel, `en_renglones` (`maria_generator.py:1953`) y su condición
(`:1964`) no deciden nada.** Tu punto 2 pide: «Si ninguna entrada distingue `:1953`, lo decís
con la medición y va como D». La medición:

| cambio | resultado |
|---|---|
| `:1964` sin `and n not in en_renglones` (fila 16) | `83 passed`; verde en ancho, `excel3` y «el resto» |
| `:1953` `juntos[:1]` (fila 22) | ídem |
| `:1953` `en_renglones = set()` (fila 24) | ídem |
| `:1953` de corrido, `range(ns[0], ns[-1] + 1)` (tu fila 37, sabotaje 52) | `1 failed, 82 passed` `[un_grupo_en_el_medio]` |

Un renglón con grupo nunca entra en la lista de renglones juntos (`:972`). Por eso
`n not in en_renglones` siempre es verdad para él: sacar la condición o vaciar el conjunto no
cambia ningún aviso, con ninguna entrada. El sabotaje 52 da rojo porque **agranda** el
conjunto hasta meter al grupo adentro, y el producto hoy no llega a ese estado. Sirve de
guarda (si alguien toca `:972` y los grupos empiezan a juntarse, avisa), pero no demuestra que
`:1953` haga falta. Con ninguno de los tres cambios el despachante ve algo distinto.
`/code-review` también lo marcó: el conjunto se calcula dos veces, en `:2187` y en `:1953`.

- **(a)** Una línea para la cola de limpieza: sacar `en_renglones` y el parámetro `juntos` de
  `_avisos_del_arancel`, unas tres líneas menos de producto. Con eso se va también el sabotaje
  52, que deja de tener dónde anclar.
- **(b)** La misma limpieza, como pieza ahora.
- **(c)** Queda como está, como límite escrito.

Recomiendo **(a)**. Es producto y es restar, así que no entra en una pieza de sólo arnés, y no
hay apuro: hoy nada sale mal.

**D256. El lugar del aviso de cada renglón frente a «Sub-ítems: …» no está fijado.** La
prueba compara en orden sólo los avisos que empiezan con «Sufijo de valor».

| cambio | qué vería el despachante |
|---|---|
| el bucle de `:2230` pasa antes del aviso «Sub-ítems» de su ítem (fila 51) | «Sufijo de valor del renglón N…» sale antes que «Sub-ítems: los renglones…» de ese ítem: los mismos avisos, en otro orden |
| un bucle propio antes de todos los ítems (fila 107) | lo mismo, pero todos los de renglones salen antes del primer «Sub-ítems» |

- **(a)** Límite escrito: no se pierde ni cambia ningún aviso.
- **(b)** Pieza chica: la prueba compara la lista entera de avisos de cada dato. Eso arrastra
  «Código de artículo (AI) … se repite» y los avisos de unidad, que hoy este caso no mira.

Recomiendo **(a)**.

**D257. Los otros 27 verdes: topes por encima de los datos (11), grupos (11) y otros (5).**

*A. Topes y cola (11).* Es la familia de D253: por más largo que sea el dato, el tope
siguiente queda verde.

| cambio | qué vería el despachante |
|---|---|
| `:2230` `ns[:6]` (fila 41) | en un ítem de siete renglones con el sufijo del 7 mal escrito, se pierde «del renglón 7» |
| `:2193` `(items or [])[:6]` (fila 82) | en un pedido de siete, con el 7 solo y mal escrito, se pierde «del ítem 7» |
| `:2190` `items[:6]` (fila 105); `:2190` y `:478` con `items[-4:]`, `[-5:]` y `[-6:]` (seis filas) | en un pedido de seis o siete renglones donde sólo el primero (o sólo el último) usa el sufijo de la operación, se pierde el aviso de que ese sufijo se limpió |
| `:1958` `items[:2]` e `items[:3]` (filas 84 y 85) | en un grupo que empieza en el renglón 3 o 4, se pierde su aviso de arancel |

*B. Grupos (11).* Los datos tienen un solo grupo (`ga`): empieza en el renglón 1 o 2, lleva el
mismo sufijo en todos sus renglones y nunca es lo último del pedido.

| cambio | qué vería el despachante |
|---|---|
| `:1965` `if not grupos:` (fila 88) | con dos grupos sin el código AI, se pierde el aviso de arancel del segundo |
| `:2210` `if nuevo and idx < 3:` (fila 106) | en un grupo que empieza en el renglón 3, se pierde su «se limpió» |
| `:2212` sólo `if idx < len(items):` (fila 104) | lo mismo, en un grupo de un renglón que es el último del pedido |
| `:484` el grupo no cuenta para el sufijo de la operación (fila 72) | con un grupo sin sufijo propio y el de la operación mal escrito, se pierde el aviso de la operación |
| `:1968` sin `or general` (fila 55) | en un grupo sin sufijo propio, se pierde su aviso de arancel |
| `:2212` `sufijos.insert(…)` (fila 64); `:2213` `sorted(sufijos, …)` (filas 90 y 91) | con dos grupos, o un grupo y un ítem solo: los mismos avisos, en otro orden |
| `:2212` el sufijo del último renglón del grupo (fila 60) | nada: sólo cambia en un pedido que no genera («todos los ítems deben llevar el mismo sufijo») |
| `:972` y `:2203` con un `grupo_id` vacío (filas 39 y 54) | nada: ese pedido hoy se rechaza |

*C. Otros (5).*

| cambio | qué vería el despachante |
|---|---|
| `:453` sin `.strip()` (fila 38) | con un espacio al borde del sufijo, aparece un aviso de limpieza de más |
| `:2230` sólo si hay sufijo de la operación (fila 43) | nada por la API: `main.py:4815` nunca manda `None` |
| `:2231` un aviso de más si el renglón trae su sufijo ya limpio (fila 52; `/code-review` también lo marcó) | no medido en pantalla; leyendo el código, sobra un aviso |
| `:2200` sin `not subs` (fila 74) | no medido en pantalla |
| `limpiar_sufijo` compara sólo 24 caracteres de punta (fila 114) | con un sufijo de 40 y el error después del carácter 24, se pierde el aviso (el TXT sale limpio igual) |

- **(a)** Todo como límite escrito.
- **(b)** Una pieza chica sólo para B: el caso suma cuatro o cinco datos (dos grupos, uno que
  empieza después del renglón 2, uno al final, uno sin sufijo propio). A y C quedan como límite
  escrito.
- **(c)** Una pieza para las tres familias.

Recomiendo **(b)**. Ya está medido que ninguna otra prueba del repositorio atrapa los 11 de
grupos, y en tres de ellos (filas 88, 106 y 104) el despachante pierde un aviso. Con A pasa lo
mismo que con D253: cada tope que se fije deja verde el siguiente. C es chico o no se ve.

**Supuestos reversibles** (los agregué sin que los pidieras; si sobran, se sacan):

1. Son 20 sabotajes nuevos, no 8. Los 8 que pediste son el 44, 45, 46, 48, 49, 50, 51 y 52.
   Los otros doce salieron de las revisiones:
   - 47: tope de cinco;
   - 53: `en_renglones` sólo del primer ítem;
   - 54: un renglón sin sufijo propio no recibe aviso por el de la operación;
   - 55: el grupo se avisa una vez;
   - 56: el orden de los avisos;
   - 57: el de la operación sólo si alguien lo usa;
   - 58: el orden entre dos ítems solos;
   - 59 a 63: lo que rompí y volví a fijar.

   `/code-review` los marca contra §6: son avisos, no dinero ni datos, y el guion tarda 9
   minutos.
2. El caso tiene siete datos, no los tres que alcanzan para tus puntos 1 y 2 (`salteados` y
   `un_grupo_en_el_medio`, más `seguidos`, que es el de la base). `tres_items` está por el
   sabotaje 53. `el_ultimo_usa_el_de_la_operacion`, `uno_solo_antes_del_item` y
   `ninguno_va_junto` están por los sabotajes 59 a 63.
3. Cada renglón lleva un sufijo mal escrito distinto, con el número del renglón adentro. Así un
   aviso con el sufijo de otro renglón da rojo.
4. El sufijo de la operación va mal escrito y con el código AI (`AA(X.0)-AI(Y)-`). Así su aviso
   sale, y queda fijado dónde sale y cuántas veces.
5. La prueba compara en orden todos los avisos que empiezan con «Sufijo de valor», no sólo los
   «del renglón N». Por eso fija también los de ítem solo, grupo, operación y arancel.
6. La línea `_gen(renglones, …)` antes de pedir los avisos obliga a que cada dato sea un pedido
   que genera. El resultado no se mira (riesgo 4). Medí que `_gen` no cambia los renglones que
   recibe: los siete datos quedan iguales.
7. `caso` nombra un subconjunto de los datos que quedan en rojo, no todos. El 31, el 44, el 54
   y el 59 ponen en rojo datos que el guion no nombra. El 31 nombra cuatro y da `5 failed`: el
   quinto es `uno_solo_antes_del_item` (lo vio `/code-review` y lo medí acá).
8. El sabotaje 31, que ya existía, ahora nombra datos, porque la prueba sin dato dejó de
   existir.

## Qué hay ahora

El archivo pasa de 77 a 83 pruebas y `sabotaje_maria8.sh`, de 43 a 63 sabotajes. No hay caso
nuevo: `test_los_avisos_dicen_si_se_limpio_el_sufijo_de_un_renglon` ya existía con una sola
entrada (dos renglones seguidos) y ahora recorre los datos de `SE_LIMPIO`. Cada letra es la
posición de un renglón; en minúscula, el renglón va en un grupo hecho a mano.

| dato | renglones | lo que dicen los avisos, en orden |
|---|---|---|
| `seguidos` | `AAAABC` | operación, ítem 5, ítem 6, renglón 1, renglón 2 (el 3 y el 4 usan el de la operación) |
| `el_ultimo_usa_el_de_la_operacion` | `aC` | operación, grupo ga; arancel del grupo ga |
| `salteados` | `AABAACAA` | operación, ítem 3, renglones 1, 2, 4, 5, 7 y 8 (el 6 usa el de la operación) |
| `un_grupo_en_el_medio` | `AaaA` | grupo ga (una vez), renglón 1, renglón 4; arancel del grupo ga |
| `tres_items` | `ABCCAB` | renglones 1, 5, 2, 6, 3 y 4 |
| `uno_solo_antes_del_item` | `BAAAAA` | operación, ítem 1, renglones 2, 4, 5 y 6 (el 3 usa el de la operación) |
| `ninguno_va_junto` | `BC` | operación, ítem 1 |

Tu criterio:

1. **El aviso de cada renglón, con su texto entero, en un ítem salteado y largo.** Es
   `salteados`: el ítem tiene seis renglones (1, 2, 4, 5, 7 y 8), el 3 va solo en el medio con
   su aviso propio, y el 6 va solo y usa el de la operación. El texto entero lo arma
   `_aviso_de_que_se_limpio`, no el producto. Seis renglones es «más largo que cualquier tope»
   sólo hasta el tope de cinco: el tope de seis queda verde (D257 A).
2. **Un renglón solo entre dos que van juntos conserva sus avisos.** Sin grupo: el 3 de
   `salteados`, «del ítem 3». Con grupo: `un_grupo_en_el_medio`, «del grupo ga» en la limpieza
   y en el arancel. `:2187` lo distingue el sabotaje 51 (`2 failed`, los dos datos). `:1953` va
   en D255.
3. **Datos de los casos que ya existen.** Un caso, siete datos.
4. **Tus filas, en el guion, en `ROJO` con un dato nombrado** (salida de esta sesión):

| tu fila | sabotaje | cambio | resultado | dato nombrado |
|---|---|---|---|---|
| 22 | 44 | `{n + 1}` → `{ns.index(n) + 1}` | `4 failed, 79 passed` | `salteados`, `un_grupo_en_el_medio`, `tres_items` |
| 34 | 45 | `ns[:4]` | `2 failed, 81 passed` | `salteados` |
| 35 | 49 | `range(ns[0], ns[-1] + 1)` | `3 failed, 80 passed` | `salteados`, `un_grupo_en_el_medio`, `tres_items` |
| 36 | 51 | `:2187` de corrido | `2 failed, 81 passed` | `salteados`, `un_grupo_en_el_medio` |
| 37 | 52 | `:1953` de corrido | `1 failed, 82 passed` | `un_grupo_en_el_medio` |
| 52 | 46 | `ns[:2]` | `2 failed, 81 passed` | `salteados` |
| 53 | 48 | `ns[1:2]` | `5 failed, 78 passed` | `seguidos`, `salteados`, `un_grupo_en_el_medio`, `tres_items` |
| 54 | 50 | `range(ns[0], ns[0] + len(ns))` | `3 failed, 80 passed` | `salteados`, `un_grupo_en_el_medio`, `tres_items` |

En `993825b` las ocho daban `77 passed` (medido acá, columna base del apéndice). El guion
entero da 63 `ROJO`, 0 `FALLA`, «OK: los 63 sabotajes dan rojo por la razón esperada» y
`rc=0`. Las anclas no empeoran: 0, 0 y 0 perdidas, y «está» pasa de 2514 a 2534.

## La base, medida

Los 115 cambios, uno por uno, están en el apéndice. Contra `993825b` (sus 77 pruebas), 108 dan
`77 passed`; uno de ellos es el repetido. Los otros 7 ya daban rojo: filas 9, 11, 12, 13, 31,
33 y 48.

Revisé cada salida roja de esta sesión: todos los rojos son por aserción, salvo tres que son
un `TypeError` (filas 53, 73 y 89). Esos tres caen en
`test_un_grupo_que_no_se_puede_comparar_no_rompe_los_avisos`, la prueba que justamente pide
que ese `TypeError` no salga.

Los 8 que atrapa otra prueba del conjunto ancho:

| fila | nombre | dónde | resultado |
|---|---|---|---|
| 47 | `avisa_aunque_no_cambie` | `:456` | `2 failed` |
| 53 | `dos_grupos_el_segundo_sin_aviso` | `:2207` | `1 failed` |
| 67 | `usa_op_sin_el_primero` | `:2190` `items[1:]` | `7 failed` |
| 73 | `gid_sin_try` | `:2206` | `1 failed` |
| 75 | `sin_aviso_de_subitem_a_mano` | `:2196` | `1 failed` |
| 76 | `corta_a_60` | `:460` | `1 failed` |
| 86 | `arancel_items_sin_el_ultimo` | `:1958` | `3 failed` |
| 115 | `sin_propio_cuenta_el_limpio` | | `9 failed` |

«El resto» no atrapa ningún cambio más: los 32 verdes del conjunto ancho dan
`1264 passed, 2 xfailed`.

**Cuatro cosas que hice mal y corregí antes de entregar.** Las cuatro son la misma: para tapar
un agujero moví un dato en vez de agregar otro, y lo que el dato viejo fijaba quedó sin fijar.

1. `11d0a6a` dejó `salteados` con un solo renglón suelto con aviso propio, y el orden entre
   dos ítems solos quedó sin fijar. Lo encontró el adversario 5; lo arregla `04ee626`,
   sabotaje 58.
2. `04ee626` sacó de los datos el pedido donde el último renglón es el que usa el sufijo de la
   operación, y `items[:-1]` quedó verde. Lo encontró el adversario 6; lo arregla `9176837`,
   sabotaje 59.
3. `9176837` dejó sin dato al renglón solo, con sufijo propio, que es el último del pedido. Lo
   encontró el adversario 7; lo arregla `44d6856`, sabotaje 60.
4. `44d6856` perdió tres cosas que fijaban la prueba de la base o un commit anterior: el solo
   que va antes del ítem, el único usuario de la operación a cuatro del final y el pedido donde
   nadie va junto. Lo encontró el adversario 8; lo arregla `bd009cc`, sabotajes 61 a 63.

En `bd009cc` ningún cambio de la tabla que diera rojo en la base da verde (lo comparó esta
sesión, columnas base y `bd009cc`). Los commits del medio no los comparó nadie uno por uno.

**Cuándo paré.** Dije el criterio antes de la última vuelta. Se arregla:
1. todo agujero dentro de tu criterio;
2. lo que un commit de esta entrega fijaba y otro destapó, si ninguna otra prueba lo atrapa;
3. lo perdido contra la base.

Lo demás va como D. La última vuelta (adversario 9 y `/code-review` sobre `bd009cc`) no
encontró nada de esos tres tipos.

## Revisión

Los adversarios son todos `adversario-sonnet-alto` (Sonnet, esfuerzo alto), cada uno en su
propia copia del repositorio. Corrieron en la sesión anterior, y sus salidas no se conservaron.
Cada cambio que propusieron está en el apéndice, medido otra vez acá.

| quién | sobre | qué encontró | qué pasó |
|---|---|---|---|
| adversario 1 | `a29acdd` | verdes en arancel, grupo y `strip`; el ítem de cinco estaba justo en el tope; el sabotaje de `:1953` no demuestra que la línea haga falta | `9dbcd87`; lo último, D255 |
| adversario 2 | `9dbcd87` | 3 bajos | `c0a05f8` |
| adversario 3 | `c0a05f8` | 4 bajos | `cb4076e`; el resto, D257 |
| adversario 4 | `cb4076e` | 1 bajo: saltear el cuarto renglón de seis quedaba verde | `11d0a6a` |
| adversario 5 | `11d0a6a` | 1 medio y 1 bajo (lo mío, 1) | `04ee626` |
| adversario 6 | `04ee626` | 1 medio (lo mío, 2) | `9176837` |
| adversario 7 | `9176837` | lo mío, 3 | `44d6856` |
| adversario 8 | `44d6856` | lo mío, 4 | `bd009cc` |
| adversario 9 | `bd009cc` | ninguna regresión ni agujero en tus puntos 1 y 2; un límite nuevo, la cola del pedido (`items[-4:]`) | ningún commit; D257 A |
| `/code-review high`, ocho veces | `993825b..a29acdd` a `..44d6856` | 8, 9, 7, 6, 4, 4, 8 y 8 | un commit cada una, de `9dbcd87` a `bd009cc` |
| `/code-review high`, en esta sesión | `993825b..bd009cc` | 10, ningún error de corrección | ningún commit |

Los 10 de esta sesión:

| # | hallazgo | dónde va |
|---|---|---|
| 1 | ningún dato tiene dos grupos, ni un grupo con renglones de sufijos distintos | D257 B |
| 2 | ningún renglón con grupo trae el sufijo ya limpio | D257 C, fila 52 |
| 3 | el `63` del último `echo` va a mano | cola de limpieza; la línea ya existe |
| 4 | 20 sabotajes contra §6 | supuesto 1 |
| 5 | 45, 46 y 47 son una causa (también 49 y 50, 59 y 62) | riesgo 6 |
| 6 | la fecha del arancel va a mano en `_aviso_de_que_falta_el_codigo` | cola de limpieza |
| 7 | `en_renglones` se calcula dos veces | D255 |
| 8 | `_gen` recibe los mismos renglones que después se miran | medido: no los cambia (supuesto 6) |
| 9 | `LIMPIO` en el guion nombra a `SE_LIMPIO`, no a la constante | cola de limpieza |
| 10 | el 31 no nombra `uno_solo_antes_del_item` | supuesto 7 |

## Puertas

Todo sobre `bd009cc` y corrido en esta sesión.

| puerta | resultado |
|---|---|
| `tests/test_maria8_subitems_por_posicion.py` | `83 passed` |
| `sabotaje_maria8.sh bd009cc <venv>` | `VERDE  sin sabotaje: … 83 passed`; 63 `ROJO`, 0 `FALLA`; «OK: los 63 sabotajes dan rojo por la razón esperada»; `rc=0`; unos 9 minutos |
| sabotajes 40 a 43 (los de D251) | `3`, `3`, `2` y `14 failed` |
| sabotajes 44 a 63 | las ocho de la tabla de arriba; el 47, `1 failed`; del 53 al 63: 1, 2, 1, 5, 2, 1, 2, 1, 1, 1 y 1 `failed` |
| `anclas_perdidas.py bd009cc` | «revisión bd009cc: 103 guiones, 2534 anclas medidas y 11 llamadas sin medir»; perdidas de una línea, 0; de varias líneas, 0; otra cantidad, 0; no medido, 5 (2 guiones); sin ancla, 6 (1 guion); está, 2534 (101 guiones) |
| `bash -n scripts/testing/sabotaje_maria8.sh` | sin salida |
| conjunto ancho, sin cambio | `2092 passed, 234 skipped, 1 xfailed` |
| `tests/test_excel3.py` con `xlwt`, sin cambio | `958 passed` |
| «el resto», sin cambio | `1264 passed, 2 xfailed` |

- **El conjunto ancho** son los 38 archivos de la primera línea `ancho=` del bloque 3.
- **«El resto»** son los otros 21 que nombran el generador, los avisos o el sufijo. Los elige
  el `grep`, no una lista a mano.
- **Los 234 `skipped`** son todos de `test_excel3.py:1150`: `pytest.importorskip("xlwt")`.
  `xlwt` no está en `requirements.txt` (la prueba lo dice). Lo instalé sólo en mi venv temporal
  y corrí `test_excel3.py` aparte, contra los 32 verdes y sin cambio: 33 veces `958 passed`. La
  sesión anterior contaba `2326 passed` en el conjunto ancho porque su venv tenía `xlwt`.

**No corrido:** la suite entera, `compileall` (no hay producto), pantallas, e2e, smoke, el
ataque de aislamiento, Postgres, los otros guiones de sabotaje y `/security-review` (no hay
producto).

## `chequeo-6`

```
chequeo-6 993825b..bd009cc: avisos para mirar, no un veredicto
producto +0/−0
arnés +157/−8
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

1. Las mediciones corrieron de a cuatro o cinco pytest en cuatro núcleos. Ninguna dio un rojo
   que no fuera por aserción del cambio, y los tres `TypeError` son los que la prueba busca.
2. `test_despacho1b`: no reproducido, causa desconocida (arriba).
3. Un renglón que va junto con otros y no trae el código AI se nombra «renglón N» en el aviso
   de limpieza e «ítem N» en el del arancel. No es de esta pieza, y está fijado así en
   `tests/test_sufijos1.py` (`test_el_codigo_ai_repetido_entre_productos_se_avisa`). Si eso es
   lo que querés que lea el despachante, lo decidís vos.
4. `_gen(…)` sólo comprueba que el pedido genera. Si un dato dejara de generar, la prueba cae
   con el error del generador, no con una aserción.
5. Seis sabotajes (45 a 50) usan la misma ancla, `        for n in ns:`. Hoy aparece una vez;
   si el generador suma otro bucle igual, los seis pasan juntos a «otra cantidad».
6. El 49 y el 50 dan el mismo conjunto de rojos, y el 45, el 46 y el 47 son el mismo cambio con
   otro número. Ninguno de los que pediste sobra.
7. La suciedad del sufijo de cada renglón empieza en el carácter 17 de 40. Un cambio que
   compare sólo 18 caracteres de punta o más queda verde (fila 114, D257 C).
8. La prueba no compara lo que el aviso promete («sale «…»») con el TXT de estos datos. Eso lo
   hacen otros casos del archivo, para un ítem.
9. Los guiones de medición (`mut.py`, `cola.sh`, `tabla.py`) están en mi carpeta temporal, no
   en el repositorio. La tabla del apéndice tiene el texto exacto de cada cambio para rehacerlos.

**Líneas que propongo para la cola de limpieza:**

- `COLA-LIMPIEZA.md:273` dice «hoy `43`», y son 63. Mejor que `caso` cuente y que el último
  `echo` no lleve el número a mano.
- En `_aviso_de_que_falta_el_codigo`, el texto del arancel sale de `sufijos_arca` (la fuente y
  la posición) en vez de ir a mano, como `FUENTE` en `tests/test_sufijos1.py:27`.
- Los sabotajes 44 a 63 corren sólo su caso (`-k`), no el archivo entero.
- En `sabotaje_maria8.sh`, `LIMPIO` pasa a llamarse `SE_LIMPIO`, como el diccionario de la
  prueba.
- Si D255 es (a): sacar `en_renglones` y `juntos` de `_avisos_del_arancel`, y el sabotaje 52.

## Archivos de producto que toqué

Ninguno.

## Apéndice: los 115 cambios

Todo medido en esta sesión.
- **«base»:** el archivo de pruebas en `993825b`, con 77 pruebas.
- **`bd009cc`:** el mismo archivo, con 83.
- **«conjunto ancho» y «el resto»:** las otras pruebas, sobre `bd009cc`. En el conjunto ancho,
  `test_excel3.py` sin `xlwt`: `234 skipped`. Esos 32 verdes también dan `958 passed` con
  `xlwt`.
- **«—»:** no hizo falta medirlo, porque ya da rojo en el archivo.

| # | nombre | cambio en `maria_generator.py` | de dónde sale | base `993825b` | `bd009cc` | conjunto ancho | el resto |
|---|---|---|---|---|---|---|---|
| 1 | `renglon_del_aviso_por_puesto` | `:2231` `avisos.extend(_aviso_de_sufijo(f" del renglón {n + 1}", items[n].get("sufijo")))` → `avisos.extend(_aviso_de_sufijo(f" del renglón {ns.index(n) + 1}", items[n].get("sufijo")))` | PM, fila 22 | `77 passed` | `4 failed, 79 passed` | — | — |
| 2 | `del_renglon_tope_4` | `:2230` `for n in ns:` → `for n in ns[:4]:` | PM, fila 34 | `77 passed` | `2 failed, 81 passed` | — | — |
| 3 | `del_renglon_de_corrido` | `:2230` `for n in ns:` → `for n in range(ns[0], ns[-1] + 1):` | PM, fila 35 | `77 passed` | `3 failed, 80 passed` | — | — |
| 4 | `en_renglones_de_corrido_avisos` | `:2187` `en_renglones = {n for ns in juntos for n in ns}` → `en_renglones = {n for ns in juntos for n in range(ns[0], ns[-1] + 1)}` | PM, fila 36 | `77 passed` | `2 failed, 81 passed` | — | — |
| 5 | `en_renglones_de_corrido_arancel` | `:1953` `en_renglones = {n for ns in juntos for n in ns}` → `en_renglones = {n for ns in juntos for n in range(ns[0], ns[-1] + 1)}` | PM, fila 37 | `77 passed` | `1 failed, 82 passed` | — | — |
| 6 | `del_renglon_tope_2` | `:2230` `for n in ns:` → `for n in ns[:2]:` | PM, fila 52 | `77 passed` | `2 failed, 81 passed` | — | — |
| 7 | `del_renglon_solo_el_segundo` | `:2230` `for n in ns:` → `for n in ns[1:2]:` | PM, fila 53 | `77 passed` | `5 failed, 78 passed` | — | — |
| 8 | `del_renglon_seguidos_desde_el_primero` | `:2230` `for n in ns:` → `for n in range(ns[0], ns[0] + len(ns)):` | PM, fila 54 | `77 passed` | `3 failed, 80 passed` | — | — |
| 9 | `sufijo_del_primero_del_item` | `:2231` `avisos.extend(_aviso_de_sufijo(f" del renglón {n + 1}", items[n].get("sufijo")))` → `avisos.extend(_aviso_de_sufijo(f" del renglón {n + 1}", items[ns[0]].get("sufijo")))` | mía, antes de `a29acdd` | `1 failed, 76 passed` | `5 failed, 78 passed` | — | — |
| 10 | `sufijo_del_ultimo_del_item` | `:2231` `avisos.extend(_aviso_de_sufijo(f" del renglón {n + 1}", items[n].get("sufijo")))` → `avisos.extend(_aviso_de_sufijo(f" del renglón {n + 1}", items[ns[-1]].get("sufijo")))` | mía, antes de `a29acdd` | `77 passed` | `5 failed, 78 passed` | — | — |
| 11 | `sufijo_del_renglon_anterior` | `:2231` `avisos.extend(_aviso_de_sufijo(f" del renglón {n + 1}", items[n].get("sufijo")))` → `avisos.extend(_aviso_de_sufijo(f" del renglón {n + 1}", items[n - 1].get("sufijo")))` | mía, antes de `a29acdd` | `1 failed, 76 passed` | `5 failed, 78 passed` | — | — |
| 12 | `renglon_dicho_item` | `:2231` `avisos.extend(_aviso_de_sufijo(f" del renglón {n + 1}", items[n].get("sufijo")))` → `avisos.extend(_aviso_de_sufijo(f" del ítem {n + 1}", items[n].get("sufijo")))` | mía, antes de `a29acdd` | `1 failed, 76 passed` | `5 failed, 78 passed` | — | — |
| 13 | `renglon_desde_cero` | `:2231` `avisos.extend(_aviso_de_sufijo(f" del renglón {n + 1}", items[n].get("sufijo")))` → `avisos.extend(_aviso_de_sufijo(f" del renglón {n}", items[n].get("sufijo")))` | mía, antes de `a29acdd` | `1 failed, 76 passed` | `5 failed, 78 passed` | — | — |
| 14 | `renglones_al_reves` | `:2230` `for n in ns:` → `for n in reversed(ns):` | mía, antes de `a29acdd` | `77 passed` | `5 failed, 78 passed` | — | — |
| 15 | `sin_mirar_en_renglones_avisos` | `:2200` `if (isinstance(item, dict) and not subs and idx - 1 not in en_renglones` → `if (isinstance(item, dict) and not subs` | mía, antes de `a29acdd` | `77 passed` | `5 failed, 78 passed` | — | — |
| 16 | `sin_mirar_en_renglones_arancel` | `:1964` `elif item.get("grupo_id") is not None and n not in en_renglones:` → `elif item.get("grupo_id") is not None:` | mía, antes de `a29acdd` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 17 | `grupo_dicho_item` | `:2203` `if gid is None:` → `if True:` | mía, antes de `a29acdd` | `77 passed` | `2 failed, 81 passed` | — | — |
| 18 | `grupo_dicho_item_arancel` | `:1967` `sbts.append((f"grupo {item['grupo_id']}", posicion_de(item),` → `sbts.append((n + 1, posicion_de(item),` | mía, antes de `a29acdd` | `77 passed` | `2 failed, 81 passed` | — | — |
| 19 | `en_renglones_primer_item_avisos` | `:2187` `en_renglones = {n for ns in juntos for n in ns}` → `en_renglones = {n for ns in juntos[:1] for n in ns}` | mía, antes de `a29acdd` | `77 passed` | `1 failed, 82 passed` | — | — |
| 20 | `en_renglones_dos_items_avisos` | `:2187` `en_renglones = {n for ns in juntos for n in ns}` → `en_renglones = {n for ns in juntos[:2] for n in ns}` | mía, antes de `a29acdd` | `77 passed` | `1 failed, 82 passed` | — | — |
| 21 | `en_renglones_ultimo_item_avisos` | `:2187` `en_renglones = {n for ns in juntos for n in ns}` → `en_renglones = {n for ns in juntos[-1:] for n in ns}` | mía, antes de `a29acdd` | `77 passed` | `1 failed, 82 passed` | — | — |
| 22 | `en_renglones_primer_item_arancel` | `:1953` `en_renglones = {n for ns in juntos for n in ns}` → `en_renglones = {n for ns in juntos[:1] for n in ns}` | mía, antes de `a29acdd` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 23 | `en_renglones_vacio_avisos` | `:2187` `en_renglones = {n for ns in juntos for n in ns}` → `en_renglones = set()` | mía, antes de `a29acdd` | `77 passed` | `5 failed, 78 passed` | — | — |
| 24 | `en_renglones_vacio_arancel` | `:1953` `en_renglones = {n for ns in juntos for n in ns}` → `en_renglones = set()` | mía, antes de `a29acdd` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 25 | `en_renglones_todos_avisos` | `:2187` `en_renglones = {n for ns in juntos for n in ns}` → `en_renglones = set(range(len(items or []))) if juntos else set()` | mía, antes de `a29acdd` | `77 passed` | `4 failed, 79 passed` | — | — |
| 26 | `en_renglones_todos_arancel` | `:1953` `en_renglones = {n for ns in juntos for n in ns}` → `en_renglones = set(range(len(items))) if juntos else set()` | mía, antes de `a29acdd` | `77 passed` | `1 failed, 82 passed` | — | — |
| 27 | `en_renglones_sin_extremos_avisos` | `:2187` `en_renglones = {n for ns in juntos for n in ns}` → `en_renglones = {n for ns in juntos for n in ns[1:-1]}` | mía, antes de `a29acdd` | `77 passed` | `5 failed, 78 passed` | — | — |
| 28 | `en_renglones_primero_y_ultimo_avisos` | `:2187` `en_renglones = {n for ns in juntos for n in ns}` → `en_renglones = {n for ns in juntos for n in (ns[0], ns[-1])}` | mía, antes de `a29acdd` | `77 passed` | `3 failed, 80 passed` | — | — |
| 29 | `aviso_aunque_no_cambie` | `:455` sale `return [] ⏎ if not cambio:` | mía, antes de `a29acdd` | `77 passed` | `2 failed, 81 passed` | — | — |
| 30 | `del_renglon_tope_5` | `:2230` `for n in ns:` → `for n in ns[:5]:` | mía, antes de `a29acdd` | `77 passed` | `1 failed, 82 passed` | — | — |
| 31 | `del_renglon_sin_el_ultimo` | `:2230` `for n in ns:` → `for n in ns[:-1]:` | mía, antes de `a29acdd` | `1 failed, 76 passed` | `4 failed, 79 passed` | — | — |
| 32 | `del_renglon_sin_el_primero` | `:2230` `for n in ns:` → `for n in ns[1:]:` | mía, antes de `a29acdd` | `77 passed` | `5 failed, 78 passed` | — | — |
| 33 | `del_renglon_uno_si_uno_no` | `:2230` `for n in ns:` → `for n in ns[::2]:` | mía, antes de `a29acdd` | `1 failed, 76 passed` | `5 failed, 78 passed` | — | — |
| 34 | `grupo_avisa_cada_renglon` | `:2210` `if nuevo:` → `if True:` | mía, antes de `a29acdd` | `77 passed` | `1 failed, 82 passed` | — | — |
| 35 | `renglon_hereda_el_de_la_operacion` | `:2231` `avisos.extend(_aviso_de_sufijo(f" del renglón {n + 1}", items[n].get("sufijo")))` → `avisos.extend(_aviso_de_sufijo(f" del renglón {n + 1}", items[n].get("sufijo") or sbt_sufijo_valor))` | antes de `9dbcd87` | `77 passed` | `2 failed, 81 passed` | — | — |
| 36 | `grupo_con_el_sufijo_general_arancel` | `:1968` `limpio(item.get("sufijo")) or general))` → `general))` | antes de `9dbcd87` | `77 passed` | `2 failed, 81 passed` | — | — |
| 37 | `grupo_cada_renglon_arancel` | `:1965` `if item["grupo_id"] not in grupos:` → `if True:` | antes de `9dbcd87` | `77 passed` | `1 failed, 82 passed` | — | — |
| 38 | `sufijo_sin_strip` | `:453` `limpio, cambio = limpiar_sufijo(str(sufijo or "").strip())` → `limpio, cambio = limpiar_sufijo(str(sufijo or ""))` | antes de `9dbcd87` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 39 | `grupo_falso_se_junta` | `:972` `if item.get('grupo_id') is not None or item.get('subitems'):` → `if item.get('grupo_id') or item.get('subitems'):` | antes de `9dbcd87` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 40 | `del_renglon_ultimos_5` | `:2230` `for n in ns:` → `for n in ns[-5:]:` | antes de `9dbcd87` | `77 passed` | `1 failed, 82 passed` | — | — |
| 41 | `del_renglon_tope_6` | `:2230` `for n in ns:` → `for n in ns[:6]:` | antes de `9dbcd87` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 42 | `en_renglones_tope_5_avisos` | `:2187` `en_renglones = {n for ns in juntos for n in ns}` → `en_renglones = {n for ns in juntos for n in ns[:5]}` | antes de `9dbcd87` | `77 passed` | `1 failed, 82 passed` | — | — |
| 43 | `del_renglon_solo_con_operacion` | `:2230` `for n in ns:` → `for n in (ns if sbt_sufijo_valor is not None else []):` | antes de `9dbcd87` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 44 | `item_por_su_numero_en_el_txt` | `:2204` `sufijos.append((f" del ítem {idx}", item["sufijo"]))` → `sufijos.append((f" del ítem {len({str(i.get('pieza')) for i in items[:idx]})}", item["sufijo"]))` | antes de `c0a05f8` | `77 passed` | `2 failed, 81 passed` | — | — |
| 45 | `operacion_otra_vez_por_renglon_sin_sufijo` | `:2232` entra `if not items[n].get("sufijo"): ⏎ avisos.extend(_aviso_de_sufijo("", sbt_sufijo_valor))` | antes de `c0a05f8` | `77 passed` | `2 failed, 81 passed` | — | — |
| 46 | `sufijos_al_reves` | `:2213` `for donde, sufijo in sufijos:` → `for donde, sufijo in reversed(sufijos):` | antes de `c0a05f8` | `77 passed` | `5 failed, 78 passed` | — | — |
| 47 | `avisa_aunque_no_cambie` | `:456` `if not cambio:` → `if not limpio:` | antes de `c0a05f8` | `77 passed` | `83 passed` | `2 failed, 2090 passed, 234 skipped, 1 xfailed` | — |
| 48 | `corta_a_15` | `:460` `f"sale «{limpio[:80]}»."]` → `f"sale «{limpio[:15]}»."]` | antes de `c0a05f8` | `1 failed, 76 passed` | `6 failed, 77 passed` | — | — |
| 49 | `sin_aviso_de_la_operacion` | `:2191` `sufijos = [("", sbt_sufijo_valor)] if usa_el_general else []` → `sufijos = []` | antes de `c0a05f8` | `77 passed` | `5 failed, 78 passed` | — | — |
| 50 | `operacion_al_final` | `:2213` `for donde, sufijo in sufijos:` → `for donde, sufijo in sorted(sufijos, key=lambda par: par[0] == ""):` | antes de `cb4076e` | `77 passed` | `5 failed, 78 passed` | — | — |
| 51 | `renglones_antes_del_subitems` | `:2226` entra `for n in ns: ⏎ avisos.extend(_aviso_de_sufijo(f" del renglón {n + 1}", items[n].get("sufijo")))`; `:2230` sale `for n in ns: ⏎ avisos.extend(_aviso_de_sufijo(f" del renglón {n + 1}", items[n].get("sufijo")))` | antes de `cb4076e` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 52 | `renglon_avisa_aunque_este_limpio` | `:2231` `avisos.extend(_aviso_de_sufijo(f" del renglón {n + 1}", items[n].get("sufijo")))` → `avisos.extend(_aviso_de_sufijo(f" del renglón {n + 1}", items[n].get("sufijo")) or ([f"Sufijo de valor del renglón {n + 1}: x"] if items[n].get("sufijo") else []))` | antes de `cb4076e` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 53 | `dos_grupos_el_segundo_sin_aviso` | `:2207` `nuevo = gid not in grupos` → `nuevo = not grupos` | antes de `cb4076e` | `77 passed` | `83 passed` | `1 failed, 2091 passed, 234 skipped, 1 xfailed` | — |
| 54 | `grupo_falso_dicho_item` | `:2203` `if gid is None:` → `if not gid:` | antes de `cb4076e` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 55 | `grupo_sin_el_de_la_operacion_arancel` | `:1968` `limpio(item.get("sufijo")) or general))` → `limpio(item.get("sufijo"))))` | antes de `cb4076e` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 56 | `recorrido_sin_el_cuarto` | `:2230` `for n in ns:` → `for n in ns[:3] + ns[4:]:` | antes de `11d0a6a` | `77 passed` | `2 failed, 81 passed` | — | — |
| 57 | `en_renglones_sin_el_cuarto` | `:2187` `en_renglones = {n for ns in juntos for n in ns}` → `en_renglones = {n for ns in juntos for n in ns[:3] + ns[4:]}` | antes de `11d0a6a` | `77 passed` | `2 failed, 81 passed` | — | — |
| 58 | `recorrido_sin_el_tercero` | `:2230` `for n in ns:` → `for n in ns[:2] + ns[3:]:` | antes de `11d0a6a` | `77 passed` | `2 failed, 81 passed` | — | — |
| 59 | `recorrido_sin_el_quinto` | `:2230` `for n in ns:` → `for n in ns[:4] + ns[5:]:` | antes de `11d0a6a` | `77 passed` | `2 failed, 81 passed` | — | — |
| 60 | `grupo_con_el_sufijo_del_ultimo` | `:2212` `sufijos.append((f" del grupo {gid}", item["sufijo"]))` → `sufijos.append((f" del grupo {gid}", [i for i in items if i.get("grupo_id") == gid][-1]["sufijo"]))` | antes de `11d0a6a` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 61 | `usa_el_general_mira_cinco` | `:2190` `usa_el_general = usa_el_sufijo_de_la_operacion(items)` → `usa_el_general = usa_el_sufijo_de_la_operacion(items[:5])` | antes de `11d0a6a` | `77 passed` | `1 failed, 82 passed` | — | — |
| 62 | `item_solo_sin_aviso_propio` | `:2204` `sufijos.append((f" del ítem {idx}", item["sufijo"]))` → `pass` | antes de `11d0a6a` | `77 passed` | `4 failed, 79 passed` | — | — |
| 63 | `solos_del_ultimo_al_primero` | `:2204` `sufijos.append((f" del ítem {idx}", item["sufijo"]))` → `sufijos.insert(1 if usa_el_general else 0, (f" del ítem {idx}", item["sufijo"]))` | antes de `04ee626` | `77 passed` | `1 failed, 82 passed` | — | — |
| 64 | `grupos_del_ultimo_al_primero` | `:2212` `sufijos.append((f" del grupo {gid}", item["sufijo"]))` → `sufijos.insert(1 if usa_el_general else 0, (f" del grupo {gid}", item["sufijo"]))` | antes de `04ee626` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 65 | `solos_antes_que_la_operacion` | `:2204` `sufijos.append((f" del ítem {idx}", item["sufijo"]))` → `sufijos.insert(0, (f" del ítem {idx}", item["sufijo"]))` | antes de `04ee626` | `77 passed` | `4 failed, 79 passed` | — | — |
| 66 | `usa_op_sin_el_ultimo` | `:2190` `usa_el_general = usa_el_sufijo_de_la_operacion(items)` → `usa_el_general = usa_el_sufijo_de_la_operacion(items[:-1])` | antes de `9176837` | `77 passed` | `2 failed, 81 passed` | — | — |
| 67 | `usa_op_sin_el_primero` | `:2190` `usa_el_general = usa_el_sufijo_de_la_operacion(items)` → `usa_el_general = usa_el_sufijo_de_la_operacion(items[1:])` | antes de `9176837` | `77 passed` | `83 passed` | `7 failed, 2085 passed, 234 skipped, 1 xfailed` | — |
| 68 | `bucle_usa_op_sin_el_ultimo` | `:478` `for item in items:` → `for item in items[:-1]:` | antes de `9176837` | `77 passed` | `2 failed, 81 passed` | — | — |
| 69 | `operacion_una_vez_por_uso` | `:2191` `sufijos = [("", sbt_sufijo_valor)] if usa_el_general else []` → `sufijos = [("", sbt_sufijo_valor)] * sum(1 for i in items if not i.get("sufijo")) if usa_el_general else []` | antes de `9176837` | `77 passed` | `1 failed, 82 passed` | — | — |
| 70 | `solo_el_primer_item_solo` | `:2203` `if gid is None:` → `if gid is None and None not in grupos: ⏎ grupos.add(None)`; `:2205` entra `elif gid is None: ⏎ pass` | antes de `9176837` | `77 passed` | `1 failed, 82 passed` | — | — |
| 71 | `solo_el_ultimo_item_solo` | `:2204` entra `sufijos[:] = [s for s in sufijos if not s[0].startswith(" del ítem") or "sub-ítem" in s[0]]` | antes de `9176837` | `77 passed` | `1 failed, 82 passed` | — | — |
| 72 | `grupo_no_cuenta_para_la_operacion` | `:484` `elif sin_propio(item.get("sufijo")):` → `elif item.get("grupo_id") is None and sin_propio(item.get("sufijo")):` | antes de `9176837` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 73 | `gid_sin_try` | `:2206` `try: ⏎ nuevo = gid not in grupos ⏎ except TypeError: ⏎ continue  # lo dice el generador` → `nuevo = gid not in grupos` | antes de `9176837` | `77 passed` | `83 passed` | `1 failed, 2091 passed, 234 skipped, 1 xfailed` | — |
| 74 | `entero_aunque_tenga_subitems` | `:2200` `if (isinstance(item, dict) and not subs and idx - 1 not in en_renglones` → `if (isinstance(item, dict) and idx - 1 not in en_renglones` | antes de `9176837` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 75 | `sin_aviso_de_subitem_a_mano` | `:2196` `if isinstance(sub, dict) and isinstance(sub.get("sufijo"), str):` → `if False:` | antes de `9176837` | `77 passed` | `83 passed` | `1 failed, 2091 passed, 234 skipped, 1 xfailed` | — |
| 76 | `corta_a_60` | `:460` `f"sale «{limpio[:80]}»."]` → `f"sale «{limpio[:60]}»."]` | antes de `9176837` | `77 passed` | `83 passed` | `1 failed, 2091 passed, 234 skipped, 1 xfailed` | — |
| 77 | `items_sin_el_ultimo` | `:2193` `for idx, item in enumerate(items or [], start=1):` → `for idx, item in enumerate((items or [])[:-1], start=1):` | antes de `44d6856` | `77 passed` | `1 failed, 82 passed` | — | — |
| 78 | `items_hasta_2` | `:2193` `for idx, item in enumerate(items or [], start=1):` → `for idx, item in enumerate((items or [])[:2], start=1):` | antes de `44d6856` | `77 passed` | `2 failed, 81 passed` | — | — |
| 79 | `items_hasta_3` | `:2193` `for idx, item in enumerate(items or [], start=1):` → `for idx, item in enumerate((items or [])[:3], start=1):` | antes de `44d6856` | `77 passed` | `1 failed, 82 passed` | — | — |
| 80 | `items_hasta_4` | `:2193` `for idx, item in enumerate(items or [], start=1):` → `for idx, item in enumerate((items or [])[:4], start=1):` | antes de `44d6856` | `77 passed` | `1 failed, 82 passed` | — | — |
| 81 | `items_hasta_5` | `:2193` `for idx, item in enumerate(items or [], start=1):` → `for idx, item in enumerate((items or [])[:5], start=1):` | antes de `44d6856` | `77 passed` | `1 failed, 82 passed` | — | — |
| 82 | `items_hasta_6` | `:2193` `for idx, item in enumerate(items or [], start=1):` → `for idx, item in enumerate((items or [])[:6], start=1):` | antes de `44d6856` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 83 | `usa_op_no_del_item_del_primero` | `:484` `elif sin_propio(item.get("sufijo")):` → `elif sin_propio(item.get("sufijo")) and not any(it is not item and it.get("pieza") == item.get("pieza") for it in items[:1]):` | antes de `44d6856` | `77 passed` | `1 failed, 82 passed` | — | — |
| 84 | `arancel_items_hasta_2` | `:1958` `for n, item in enumerate(items):` → `for n, item in enumerate(items[:2]):` | antes de `44d6856` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 85 | `arancel_items_hasta_3` | `:1958` `for n, item in enumerate(items):` → `for n, item in enumerate(items[:3]):` | antes de `44d6856` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 86 | `arancel_items_sin_el_ultimo` | `:1958` `for n, item in enumerate(items):` → `for n, item in enumerate(items[:-1]):` | antes de `44d6856` | `77 passed` | `83 passed` | `3 failed, 2089 passed, 234 skipped, 1 xfailed` | — |
| 87 | `grupo_antes_que_todos` | `:2212` `sufijos.append((f" del grupo {gid}", item["sufijo"]))` → `sufijos.insert(0, (f" del grupo {gid}", item["sufijo"]))` | antes de `44d6856` | `77 passed` | `1 failed, 82 passed` | — | — |
| 88 | `arancel_solo_el_primer_grupo` | `:1965` `if item["grupo_id"] not in grupos:` → `if not grupos:` | antes de `44d6856` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 89 | `solo_el_primer_grupo` (el mismo cambio que `dos_grupos_el_segundo_sin_aviso`) | `:2207` `nuevo = gid not in grupos` → `nuevo = not grupos` | antes de `44d6856` | `77 passed` | `83 passed` | `1 failed, 2091 passed, 234 skipped, 1 xfailed` | — |
| 90 | `grupos_despues_de_los_items` | `:2213` `for donde, sufijo in sufijos:` → `for donde, sufijo in sorted(sufijos, key=lambda par: par[0].startswith(" del grupo")):` | después de `44d6856` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 91 | `grupos_antes_de_los_items` | `:2213` `for donde, sufijo in sufijos:` → `for donde, sufijo in sorted(sufijos, key=lambda par: (par[0] != "", not par[0].startswith(" del grupo"))):` | después de `44d6856` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 92 | `solo_no_si_es_el_primero` | `:2204` `sufijos.append((f" del ítem {idx}", item["sufijo"]))` → `if idx > 1: ⏎ sufijos.append((f" del ítem {idx}", item["sufijo"]))` | adversario sobre `44d6856` | `77 passed` | `2 failed, 81 passed` | — | — |
| 93 | `solo_no_antes_del_tercero` | `:2204` `sufijos.append((f" del ítem {idx}", item["sufijo"]))` → `if idx > 2: ⏎ sufijos.append((f" del ítem {idx}", item["sufijo"]))` | adversario sobre `44d6856` | `77 passed` | `2 failed, 81 passed` | — | — |
| 94 | `solo_si_hay_renglones_juntos` | `:2204` `sufijos.append((f" del ítem {idx}", item["sufijo"]))` → `if en_renglones: ⏎ sufijos.append((f" del ítem {idx}", item["sufijo"]))` | adversario sobre `44d6856` | `77 passed` | `1 failed, 82 passed` | — | — |
| 95 | `solo_si_hay_juntos` | `:2204` `sufijos.append((f" del ítem {idx}", item["sufijo"]))` → `if juntos: ⏎ sufijos.append((f" del ítem {idx}", item["sufijo"]))` | adversario sobre `44d6856` | `77 passed` | `1 failed, 82 passed` | — | — |
| 96 | `solo_si_mas_de_3_renglones` | `:2204` `sufijos.append((f" del ítem {idx}", item["sufijo"]))` → `if len(items) > 3: ⏎ sufijos.append((f" del ítem {idx}", item["sufijo"]))` | adversario sobre `44d6856` | `77 passed` | `1 failed, 82 passed` | — | — |
| 97 | `solo_si_mas_de_5_renglones` | `:2204` `sufijos.append((f" del ítem {idx}", item["sufijo"]))` → `if len(items) > 5: ⏎ sufijos.append((f" del ítem {idx}", item["sufijo"]))` | adversario sobre `44d6856` | `77 passed` | `1 failed, 82 passed` | — | — |
| 98 | `solo_no_antes_del_primer_junto` | `:2200` `if (isinstance(item, dict) and not subs and idx - 1 not in en_renglones` → `if (isinstance(item, dict) and not subs and idx - 1 not in en_renglones and idx - 1 > min(en_renglones, default=-1)` | adversario sobre `44d6856` | `77 passed` | `1 failed, 82 passed` | — | — |
| 99 | `en_renglones_con_los_de_antes` | `:2187` `en_renglones = {n for ns in juntos for n in ns}` → `en_renglones = {n for ns in juntos for n in ns} \| set(range(juntos[0][0] if juntos else 0))` | adversario sobre `44d6856` | `77 passed` | `1 failed, 82 passed` | — | — |
| 100 | `usa_op_uno_si_uno_no` | `:2190` `usa_el_general = usa_el_sufijo_de_la_operacion(items)` → `usa_el_general = usa_el_sufijo_de_la_operacion(items[1::2])` | adversario sobre `44d6856` | `77 passed` | `1 failed, 82 passed` | — | — |
| 101 | `bucle_usa_op_uno_si_uno_no` | `:478` `for item in items:` → `for item in items[1::2]:` | adversario sobre `44d6856` | `77 passed` | `1 failed, 82 passed` | — | — |
| 102 | `usa_op_ultimos_3` | `:2190` `usa_el_general = usa_el_sufijo_de_la_operacion(items)` → `usa_el_general = usa_el_sufijo_de_la_operacion(items[-3:])` | adversario sobre `44d6856` | `77 passed` | `1 failed, 82 passed` | — | — |
| 103 | `bucle_usa_op_ultimos_3` | `:478` `for item in items:` → `for item in items[-3:]:` | adversario sobre `44d6856` | `77 passed` | `1 failed, 82 passed` | — | — |
| 104 | `grupo_no_si_es_el_ultimo` | `:2212` `sufijos.append((f" del grupo {gid}", item["sufijo"]))` → `if idx < len(items): ⏎ sufijos.append((f" del grupo {gid}", item["sufijo"]))` | adversario sobre `44d6856` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 105 | `usa_op_hasta_6` | `:2190` `usa_el_general = usa_el_sufijo_de_la_operacion(items)` → `usa_el_general = usa_el_sufijo_de_la_operacion(items[:6])` | adversario sobre `44d6856` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 106 | `grupo_solo_antes_del_tercero` | `:2210` `if nuevo:` → `if nuevo and idx < 3:` | `/code-review` sobre `bd009cc` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 107 | `renglones_antes_de_todos_los_items` | `:2225` entra `for n in ns: ⏎ avisos.extend(_aviso_de_sufijo(f" del renglón {n + 1}", items[n].get("sufijo"))) ⏎ for ns in juntos:`; `:2230` sale `for n in ns: ⏎ avisos.extend(_aviso_de_sufijo(f" del renglón {n + 1}", items[n].get("sufijo")))` | `/code-review` sobre `bd009cc` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 108 | `usa_op_cola_4` | `:478` `for item in items:` → `for item in items[-4:]:` | adversario sobre `bd009cc` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 109 | `usa_general_cola_4` | `:2190` `usa_el_general = usa_el_sufijo_de_la_operacion(items)` → `usa_el_general = usa_el_sufijo_de_la_operacion(items[-4:])` | adversario sobre `bd009cc` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 110 | `usa_op_cola_5` | `:478` `for item in items:` → `for item in items[-5:]:` | adversario sobre `bd009cc` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 111 | `usa_general_cola_5` | `:2190` `usa_el_general = usa_el_sufijo_de_la_operacion(items)` → `usa_el_general = usa_el_sufijo_de_la_operacion(items[-5:])` | adversario sobre `bd009cc` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 112 | `usa_op_cola_6` | `:478` `for item in items:` → `for item in items[-6:]:` | adversario sobre `bd009cc` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 113 | `usa_general_cola_6` | `:2190` `usa_el_general = usa_el_sufijo_de_la_operacion(items)` → `usa_el_general = usa_el_sufijo_de_la_operacion(items[-6:])` | adversario sobre `bd009cc` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 114 | `cambio_solo_24` | `:446` `return limpio, limpio != sufijo` → `return limpio, limpio[:24] != sufijo[:24]` | adversario sobre `bd009cc` | `77 passed` | `83 passed` | `2092 passed, 234 skipped, 1 xfailed` | `1264 passed, 2 xfailed` |
| 115 | `sin_propio_cuenta_el_limpio` | `:474` `return not limpiar_sufijo(str(sufijo or "").strip())[0]` → `return not limpiar_sufijo(str(sufijo or "").strip())[1]` | adversario sobre `bd009cc` | `77 passed` | `83 passed` | `9 failed, 2083 passed, 234 skipped, 1 xfailed` | — |

## Sigo con

Nada: D252 (a) queda en tu revisión. Mi canal no tiene ninguna pieza marcada «apenas entregues». D255, D256, D257 y el supuesto 1 esperan tu respuesta; D244, D239 y «Holanda» esperan a Emi.

Última vuelta: 2026-11-15 04:44 UTC.

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5 (nueva el 15/11; la vieja _01C8gC… apagada), rama `claude/dev-maria`, rutina trig_01Ukttby1fc4sGVQfSn1jC9U; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rutina trig_01TvMmGfSLDfbcJrf66ZZ7YK, rama `claude/practical-shannon-szpwkn`, integrada hasta `7dcf62c`). Aceptadas: CUIT-GENERAR sobre `29327d2`, SABOTAJE-SUBITEMS1 sobre `bf6778e`, D243 (b) sobre `0dff850`, SABOTAJE-SUFIJOS1 sobre `afeae84`, D245 (a) sobre `e17c11e`, D246 (b) sobre `0224f01`, SABOTAJE-MARIA8 sobre `50320ff`, D247 (a) sobre `4a58c68`, D248 (c) sobre `3fcc9c4`, los vencidos `sabotaje_maria1d.sh` sobre `6e4e658`, `sabotaje_maria5.sh` sobre `c0505cc`, `sabotaje_valor1b.sh` sobre `70eb5dc`, `sabotaje_doc1.py` sobre `d4c6b73`, `sabotaje_maria7.sh` sobre `4477ae3` y `sabotajes/guardar2.sh` sobre `aeb994f` (no queda ningún vencido), D249 (a) sobre `50dabfa`, D250 (a) sobre `450f4cb` y D251 (a) sobre `9d580db`. D253 (a) y D254 (a) decididas: límite escrito. **D252 (a) ENTREGADA sobre `bd009cc`** (base `993825b`; sólo `tests/test_maria8_subitems_por_posicion.py`, de 77 a 83 pruebas, y `scripts/testing/sabotaje_maria8.sh`, de 43 a 63 sabotajes; arnés +157/−8, producto +0/−0), informe en este archivo, timbre mandado. En revisión de la PM: no arranco nada hasta su veredicto; si trae devolución, va primero. D255 (recomiendo (a), línea para la cola), D256 (recomiendo (a), límite), D257 (recomiendo (b), pieza chica sólo para los 11 de grupos, medido que «el resto» no los atrapa) y el supuesto 1 (12 sabotajes de más contra §6) esperan a la PM. `test_despacho1b`: no reproducido, causa desconocida. D244, D239 y «Holanda» esperan a Emi: no se tocan. Próxima D: D258. Lecciones: el worktree de una cola decide qué SHA mide: las tareas «base» corren en el worktree de la base, no en el del SHA que se entrega; antes de comparar una cuenta con la de otra sesión se miran los `skipped` con `-rs` (una dependencia que falta en el venv, como `xlwt`, saltea pruebas sin dar rojo); «por carga» no explica un corte de `ITIMER_PROF`, que cuenta CPU del proceso y no reloj; un bloque de comandos del informe se corre tal como está escrito antes de entregarlo; antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada; un dato nuevo de un caso no reusa un valor que otro control del mismo caso espera; antes de escribir el informe se trae la rama de la PM; antes de sacar una prueba por duplicada se compara lo que afirma cada una, no sólo sus entradas; antes de reescribir un sabotaje con el ancla perdida se mira si la protección que atacaba sigue existiendo: si no, es una D (D195 (a)); al ajustar una afirmación, la nueva tiene que seguir afirmando todo lo que afirmaba la vieja (el orden también), y una mutación que «mueve» una frase la tiene que sacar de donde estaba; una medición corre sobre el conjunto más angosto de pruebas que contesta la pregunta; antes de cambiar un número que la PM fijó como criterio se lee por qué lo fijó; un comentario o un mensaje de commit no afirma lo que el guion no obliga, y su porqué se comprueba con `git show`, no se supone; que «nadie cubría» algo se mide antes de escribirlo, y con todas las pruebas que usan ese dato, no sólo las del guion (un adversario que corre cuatro archivos dice «hueco» donde otra prueba lo atrapa); `anclas_perdidas.py` mide un commit: el arreglo se commitea antes de medir; el SHA que se entrega pasa por subagente o `/code-review`, y si el gancho de parada ya subió el commit, lo que siga va en un commit nuevo; después de un commit nuevo o de corregir uno, las puertas corren otra vez sobre ese SHA; un ancla lleva sólo el texto que saca más lo mínimo que la ata a su lugar; la cuenta escrita a mano en el último `echo` de un guion se compara con sus líneas `ROJO`; una mutación se mide a mano con el archivo de pruebas entero, para ver que pone en rojo sólo lo suyo y por aserción; `anclas_perdidas.py` sólo lee los `.sh`; un worktree que aparece en `git worktree list` mientras corre un guion mío es de ese guion, no un resto; una espera de 110 vueltas de 5 s no alcanza para tres corridas de 4 minutos: se vuelve a esperar la marca de fin, no se relanza; mientras haya una D mía sin contestar, el informe siguiente la repite arriba; el dato que fija «qué pedazo se muestra» no tiene ese pedazo al principio de donde sale, o cortar el todo da lo mismo; `sabotaje_sufijos1.sh` recibe el venv como segundo argumento, no por `PY`; un riesgo que diría «cubierto» se mide antes de escribirlo; mover un dato para tapar un agujero se mide de los dos lados, con todos los cambios anotados otra vez; un ítem vecino en un caso de avisos lleva su propio aviso, o el recorrido de ítems queda sin mirar; el criterio para dejar de iterar se dice y se sostiene, y lo que queda va como D; dos cambios del mismo tamaño aplicados en el mismo segundo comparten el `.pyc`: una medición rápida corre con `python -B` y sin `.pyc`; lo que vería el despachante con un cambio se mide en pantalla antes de escribirlo en una D; un dato de un caso se agrega, no se mueve: mover un dato destapa lo que el dato viejo fijaba; al reemplazar una prueba de la base, la nueva conserva la forma del dato viejo (largo, caracteres) o se mide qué deja de atrapar; al clasificar salidas de pytest por texto, «xfailed» contiene «failed»: se busca `\d+ failed`; el «conjunto ancho» se arma con `grep` de todos los archivos de prueba que tocan el generador, no con una lista de nombres; el informe de un subagente se guarda en un archivo apenas llega, y que lo haya escrito no quiere decir que terminó: antes de medir se mira con `ps` qué más corre; al despertar se trae la rama de la PM antes de seguir con lo que venía; regla de la PM: `/code-review high` se corre siempre, aunque sea sólo arnés, va hasta el SHA que se entrega, y un commit que nace de sus hallazgos pasa por el adversario; regla de la PM: en un vencido de sólo arnés, un último commit que cambia únicamente comentarios no necesita revisor si el informe lo dice, cualquier otro cambio sí. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que una D autoriza; subagentes hasta esfuerzo alto y sin consejero.
