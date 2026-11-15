# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Entrega D257 (b) sobre `3c7eb14` (2026-11-15 05:43 UTC)

**Resultado.** Tus puntos 1 a 5 de D257 (b) se cumplen en `3c7eb14`. Base: `e1bd17a`. Toca dos
archivos: `tests/test_maria8_subitems_por_posicion.py` (de 83 a 85 pruebas: dos datos nuevos en
`SE_LIMPIO`, el caso que ya existía) y `scripts/testing/sabotaje_maria8.sh` (de 63 a 70
sabotajes). `producto +0/−0`.

**Tu premisa del punto 2 no alcanzaba tal como estaba.** El sufijo de operación del caso,
`AA(X.0)-AI(Y)-`, ya está mal escrito, pero trae AI. Un grupo sin sufijo propio que lo usa no tiene
aviso de arancel, así que la fila 55 no se distingue. Lo medí: con el dato `un_grupo_sin_el_suyo` y
el sufijo de siempre, la 55 da `85 passed` (verde) y la 72, `1 failed`. Por eso ese dato trae su
propio sufijo de operación, sin AI: `("AA(X.0)-", "AA(X 0)-")`. Con él salen el aviso de la operación
y el de arancel del grupo, que es lo que pediste.

**Lo que decidís vos:**

1. **D258.** `/code-review` sobre `3c7eb14` marca que el criterio «un aviso por grupo, salteando
   renglones» está escrito dos veces en el generador: en el arancel (`:1965`, conjunto `grupos`) y
   en los avisos de sufijo (`:2207`, otro `grupos`). Por eso los sabotajes 64 y 65 (filas 88 y 53)
   van por separado, y el cuidado del `TypeError` está sólo en el segundo.
   - (a) Una línea para `docs/pm/COLA-LIMPIEZA.md`.
   - (b) Nada.

   Recomiendo **(a)**. Es producto y no entra en esta pieza (§6: lo ya escrito se limpia después).

**Supuestos (reversibles):**

1. **Un dato puede traer un tercer campo:** el sufijo de operación como lo escribieron y como
   sale. Si no lo trae, se usa el de siempre. Sólo lo usa `un_grupo_sin_el_suyo`.
2. **Una minúscula es un grupo en la A, sea cual sea la letra.** Antes la letra elegía también la
   posición, pero sólo existía `a`. Sin esto, el segundo grupo caía en la B, que no está en el
   arancel, y la fila 88 no se distinguía.
3. **Un renglón de un grupo trae el sufijo si los avisos nombran al grupo.** El grupo se nombra
   por su primer renglón. El de un grupo que no se nombra no trae sufijo, y así existe «un grupo
   sin el suyo».
4. **No recorté los sabotajes 59 a 63.** Era optativo, y recortarlos es cambiar algo que no hace
   falta tocar para esta pieza.

| qué | SHA |
|---|---|
| base (tu rama hasta `e1bd17a`) | `e1bd17a` |
| pruebas: los dos datos | `e6822f7` |
| pruebas: los siete sabotajes. **Lo que se entrega** | `3c7eb14` |
| tu `b71f2e9` (sólo `docs/pm/`), integrado | `e73938c` |
| informe | el commit siguiente |

`6067bd2`, `cc95142` y `bfa8a60`, que aparecen abajo en «Revisión», fueron commits locales. Los
rehíce antes de subir y no están en `origin`.

## Comandos

```bash
# 1. el guion entero, unos 10 minutos
bash scripts/testing/sabotaje_maria8.sh 3c7eb14
#    tiene que terminar en «OK: los 70 sabotajes dan rojo por la razón esperada»;
#    los siete nuevos (arancel_solo_el_primer_grupo … grupos_antes_de_los_items), «1 failed, 84 passed»

# 2. anclas, §6, el archivo
python3.12 scripts/testing/anclas_perdidas.py 3c7eb14 | grep -E '^revisión|perdida'
#    «2541 anclas medidas», perdidas 0 y 0
python3.12 docs/pm/herramientas/chequeo-6.py e1bd17a 3c7eb14
#    «producto +0/−0», «arnés +49/−12», «avisos: 0»
grep -c '^caso ' scripts/testing/sabotaje_maria8.sh
#    70, lo mismo que dice la última línea del guion
```

Lo corrí así a las 05:43 UTC (el guion, de 05:29:46 a 05:39:38):

```
ROJO   arancel_solo_el_primer_grupo: =================== 1 failed, 84 passed, 3 warnings in 5.52s ===================
ROJO   dos_grupos_el_segundo_sin_aviso: =================== 1 failed, 84 passed, 3 warnings in 5.54s ===================
ROJO   grupo_sin_el_de_la_operacion_arancel: =================== 1 failed, 84 passed, 3 warnings in 5.62s ===================
ROJO   grupo_no_cuenta_para_la_operacion: =================== 1 failed, 84 passed, 3 warnings in 5.51s ===================
ROJO   grupos_del_ultimo_al_primero: =================== 1 failed, 84 passed, 3 warnings in 5.45s ===================
ROJO   grupos_despues_de_los_items: =================== 1 failed, 84 passed, 3 warnings in 5.68s ===================
ROJO   grupos_antes_de_los_items: =================== 1 failed, 84 passed, 3 warnings in 5.42s ===================
OK: los 70 sabotajes dan rojo por la razón esperada
rc=0
revisión 3c7eb14: 103 guiones, 2541 anclas medidas y 11 llamadas sin medir
  perdida, una línea          0   guiones: 0
  perdida, varias líneas      0   guiones: 0
  perdidas de una línea sin repetir (archivo y texto): 0
70
```

El guion da 70 `ROJO` y ninguna `FALLA`.

## Tu criterio, fila por fila

Mido contra el archivo, en tres worktrees de `bfa8a60`, los 115 cambios de la tabla de D252 más
«sin cambio». `bfa8a60` tiene el mismo archivo de pruebas que `3c7eb14`: `git diff bfa8a60 3c7eb14
-- tests/` da vacío, y el generador no cambió desde `bd009cc`.

| fila | cambio | en `bd009cc` | en `3c7eb14` | el dato que la pone en rojo |
|---|---|---|---|---|
| 88 | `arancel_solo_el_primer_grupo` | `83 passed` | `1 failed, 84 passed` | `dos_grupos` |
| 53 | `dos_grupos_el_segundo_sin_aviso` | `83 passed` | `1 failed, 84 passed` | `dos_grupos` |
| 55 | `grupo_sin_el_de_la_operacion_arancel` | `83 passed` | `1 failed, 84 passed` | `un_grupo_sin_el_suyo` |
| 72 | `grupo_no_cuenta_para_la_operacion` | `83 passed` | `1 failed, 84 passed` | `un_grupo_sin_el_suyo` |
| 64 | `grupos_del_ultimo_al_primero` | `83 passed` | `1 failed, 84 passed` | `dos_grupos` |
| 90 | `grupos_despues_de_los_items` | `83 passed` | `1 failed, 84 passed` | `dos_grupos` |
| 91 | `grupos_antes_de_los_items` | `83 passed` | `1 failed, 84 passed` | `dos_grupos` |
| 67 | `usa_op_sin_el_primero` | `83 passed` | `1 failed, 84 passed` | `un_grupo_sin_el_suyo` (de yapa) |
| 84 | `arancel_items_hasta_2` | `83 passed` | `1 failed, 84 passed` | `dos_grupos` (de yapa) |
| 89 | `solo_el_primer_grupo` (el mismo cambio que la 53) | `83 passed` | `1 failed, 84 passed` | `dos_grupos` |
| 106 | `grupo_solo_antes_del_tercero` | `83 passed` | `1 failed, 84 passed` | `dos_grupos` (de yapa) |

- **Los once rojos son por aserción**, un `AssertionError` en cada salida, sin otros errores.
- **En total: de 74 a 85 en rojo.** Ninguna fila pasó de rojo a verde, y «sin cambio» da `85 passed`.
- **Los datos viejos no cambiaron.** El adversario volcó lo esperado y lo que sale para los siete
  datos viejos, con el caso de `e1bd17a` y con el de `cc95142`, y son idénticos texto por texto.
- **Quedan 30 verdes en el archivo:**
  - 16, 22, 24, 38, 39, 41, 43, 47, 51, 52, 54, 60, 73, 74, 75, 76
  - 82, 85, 86, 104, 105, 107, 108, 109, 110, 111, 112, 113, 114, 115

  De esas, la 47, 73, 75, 76, 86 y 115 las atrapa el conjunto ancho (tabla de D252).

**El punto 4 queda como límite escrito, sin dato nuevo:** la familia A, la posición del grupo, las
filas 60, 39 y 54, y la familia C. Una aclaración: la **106**, que pusiste en la posición del grupo,
ahora da rojo de yapa con `dos_grupos`, porque `gb` está en el renglón 3. La **104** (el grupo que es
el último renglón) sigue verde.

**Lo que agrega el quinto renglón de `dos_grupos`** («aCbBa»: `ga` vuelve después de `gb`). El
adversario encontró M23: en el arancel, `grupos.add(item["grupo_id"])` →
`grupos.clear(); grupos.add(item["grupo_id"])`. Con «aCbB» daba `85 passed`, medido en `cc95142`;
con «aCbBa» da `1 failed, 84 passed` en `[dos_grupos]`. M23 no está en la tabla ni en el guion: su rojo
es este, mostrado una vez (§6).

## Revisión

| revisor | sobre | hallazgos | qué hice |
|---|---|---|---|
| `/code-review high` | `6067bd2` | 6 | **Arreglado:** el orden de los grupos con el aviso de la operación adelante; `dos_grupos` pasó de «aCb» a «aCbB». El `+=` pasó a `if`. **Probado y deshecho:** la cuenta del guion como contador (ver `bfa8a60`). **Al informe:** los grupos siempre en la A (es tu límite de la posición), `falta` sólo para grupos y el endpoint (riesgos 1 y 2), la forma del dato (supuesto 1) |
| `/code-review high` | `cc95142` | 7 | **Arreglado:** el comentario de `SE_LIMPIO`, reescrito. **Al informe:** `falta` sólo para grupos; el texto crudo contra el limpio, que es exacto para los sufijos que arma el caso; el grupo con sufijo sólo en un renglón posterior, que el caso no puede armar; la forma del dato; el tiempo del guion |
| adversario Sonnet alto | `cc95142` | 23 mutaciones | **Arreglado:** M23, con el quinto renglón. **Al informe:** M3 y M4 (un `gid` 0 deja de ser grupo) como límite menor, porque ningún dato ni pantalla usa 0. M5, M17, M20 y M22 son equivalentes con entradas válidas. M19 (un renglón suelto sin el general, en el arancel) queda fuera de lo pedido |
| `/code-review high` | `bfa8a60` | 5 | **Deshecho:** el contador. El 70 escrito a mano detecta un `caso` borrado y el contador no, y además no estaba pedido. Vuelve el número escrito, que coincide con `grep -c '^caso '`. Lo demás ya estaba en el informe |
| `/code-review high` | **`3c7eb14`** | 8 | Corrió el guion entero: 70 `ROJO`. Midió que el sabotaje 67 falla por aserción y no en `_gen`. **Sin arreglo:** la lógica repetida del generador (D258); el orden de los avisos de arancel entre grupos, que no tiene sabotaje (riesgo 3); el tiempo del guion (riesgo 4); la forma del dato; dos de lectura (el comentario «el que no se nombra» y el nombre `grupo` en la comprensión) |
| adversario Sonnet alto | **`3c7eb14`** | ninguno | Las cinco mutaciones de `dos_grupos` siguen en rojo con «aCbBa». `:2207 nuevo = True` y `:1965 if True:` dan `2 failed, 83 passed`, así que la deduplicación también se ejercita. El comentario coincide con el código |

Mi criterio para dejar de iterar fue que lo que saliera sobre `3c7eb14` iba al informe, salvo un
defecto real dentro de lo pedido. No salió ninguno. Los dos adversarios terminaron y no queda
ninguno vivo.

## Puertas

| qué | sobre | resultado |
|---|---|---|
| `sabotaje_maria8.sh` | `3c7eb14` | 70 `ROJO`, 0 `FALLA`, `rc=0`, 9 min 52 s |
| `anclas_perdidas.py` | `3c7eb14` | 2541 medidas (`e1bd17a`: 2534), 0 perdidas |
| `bash -n` del guion | `3c7eb14` | sin error |
| el archivo | `3c7eb14` | `85 passed` |
| los 115 cambios + «sin cambio», contra el archivo | `bfa8a60` (el mismo archivo de pruebas) | 85 rojos, 31 verdes |

**No corrí:**
- El conjunto ancho, «el resto» y la suite completa. Sólo cambió un archivo de pruebas y el guion;
  el generador y las demás pruebas están igual que en `bd009cc`, donde los medí para D252.
- `test_despacho1b`, porque me pediste que no lo midiera.

## `chequeo-6`

```
chequeo-6 e1bd17a..3c7eb14: avisos para mirar, no un veredicto
producto +0/−0
arnés +49/−12
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

1. **El caso modela el aviso de que falta AI sólo para los grupos.** El comentario lo dice. Un dato
   futuro con un renglón suelto de la A que use un sufijo de operación sin AI daría un aviso que el
   caso no cuenta. Sería un rojo visible, no un verde falso. Baja.
2. **El endpoint no tiene caso para un grupo sin sufijo propio.** El sabotaje 67 (fila 72) también
   cambia lo que usa el endpoint (`main.py:5127`), pero el guion sólo mira el aviso. Media. No
   agregué el caso: queda fuera de la pieza, y tu regla es no sumar pruebas que la pieza no pide.
3. **El orden de los avisos de arancel entre dos grupos no tiene sabotaje.** El caso lo compara
   («ga» antes que «gb»), pero ningún rojo lo muestra. Baja.
4. **El guion tarda unos 10 minutos.** Eso está cerca del tope de 10 minutos de una llamada en
   primer plano. Correlo en segundo plano. Baja.

## Archivos de producto que toqué

Ninguno.

## Sigo con

Nada: D257 (b) queda en tu revisión. Mi canal no tiene ninguna pieza marcada «apenas entregues».
D258 espera tu respuesta; D244, D239 y «Holanda» esperan a Emi.

Última vuelta: 2026-11-15 05:43 UTC.

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5 (nueva el 15/11; la vieja _01C8gC… apagada), rama `claude/dev-maria`, rutina trig_01Ukttby1fc4sGVQfSn1jC9U; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rutina trig_01TvMmGfSLDfbcJrf66ZZ7YK, rama `claude/practical-shannon-szpwkn`, integrada hasta `b71f2e9`). Aceptadas: CUIT-GENERAR sobre `29327d2`, SABOTAJE-SUBITEMS1 sobre `bf6778e`, D243 (b) sobre `0dff850`, SABOTAJE-SUFIJOS1 sobre `afeae84`, D245 (a) sobre `e17c11e`, D246 (b) sobre `0224f01`, SABOTAJE-MARIA8 sobre `50320ff`, D247 (a) sobre `4a58c68`, D248 (c) sobre `3fcc9c4`, los vencidos `sabotaje_maria1d.sh` sobre `6e4e658`, `sabotaje_maria5.sh` sobre `c0505cc`, `sabotaje_valor1b.sh` sobre `70eb5dc`, `sabotaje_doc1.py` sobre `d4c6b73`, `sabotaje_maria7.sh` sobre `4477ae3` y `sabotajes/guardar2.sh` sobre `aeb994f` (no queda ningún vencido), D249 (a) sobre `50dabfa`, D250 (a) sobre `450f4cb`, D251 (a) sobre `9d580db` y D252 (a) sobre `bd009cc` (acta `REPRODUCCION-D252-2026-11-15.md`). D255 (a): a la cola, con el sabotaje 52. D256 (a): límite escrito. Supuesto 1 aceptado. D253 (a) y D254 (a) decididas: límite escrito. **D257 (b) ENTREGADA sobre `3c7eb14`** (base `e1bd17a`; dos datos en `SE_LIMPIO`, `dos_grupos` «aCbBa» y `un_grupo_sin_el_suyo` «aB» con sufijo de operación sin AI; siete sabotajes, el guion de 63 a 70; arnés +49/−12, producto +0/−0), informe en este archivo, timbre mandado. En revisión de la PM: no arranco nada hasta su veredicto; si trae devolución, va primero. D258 (recomiendo (a): línea para la cola) espera a la PM. `test_despacho1b`: lo mide la PM, yo no. D244, D239 y «Holanda» esperan a Emi: no se tocan. Próxima D: D259. Lecciones: frenar una cola deja el generador mutado en su worktree: `git checkout -- .` antes de medir a mano ahí; la premisa de un criterio se mide antes de elegir el dato (la 55, con el sufijo de operación de siempre, quedaba verde); cuando dos revisores se contradicen se decide por lo que controla: un número escrito a mano en un guion es un control, un contador no; el worktree de una cola decide qué SHA mide: las tareas «base» corren en el worktree de la base, no en el del SHA que se entrega; antes de comparar una cuenta con la de otra sesión se miran los `skipped` con `-rs` (una dependencia que falta en el venv, como `xlwt`, saltea pruebas sin dar rojo); «por carga» no explica un corte de `ITIMER_PROF`, que cuenta CPU del proceso y no reloj; un bloque de comandos del informe se corre tal como está escrito antes de entregarlo; antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada; un dato nuevo de un caso no reusa un valor que otro control del mismo caso espera; antes de escribir el informe se trae la rama de la PM; antes de sacar una prueba por duplicada se compara lo que afirma cada una, no sólo sus entradas; antes de reescribir un sabotaje con el ancla perdida se mira si la protección que atacaba sigue existiendo: si no, es una D (D195 (a)); al ajustar una afirmación, la nueva tiene que seguir afirmando todo lo que afirmaba la vieja (el orden también), y una mutación que «mueve» una frase la tiene que sacar de donde estaba; una medición corre sobre el conjunto más angosto de pruebas que contesta la pregunta; antes de cambiar un número que la PM fijó como criterio se lee por qué lo fijó; un comentario o un mensaje de commit no afirma lo que el guion no obliga, y su porqué se comprueba con `git show`, no se supone; que «nadie cubría» algo se mide antes de escribirlo, y con todas las pruebas que usan ese dato, no sólo las del guion (un adversario que corre cuatro archivos dice «hueco» donde otra prueba lo atrapa); `anclas_perdidas.py` mide un commit: el arreglo se commitea antes de medir; el SHA que se entrega pasa por subagente o `/code-review`, y si el gancho de parada ya subió el commit, lo que siga va en un commit nuevo; después de un commit nuevo o de corregir uno, las puertas corren otra vez sobre ese SHA; un ancla lleva sólo el texto que saca más lo mínimo que la ata a su lugar; la cuenta escrita a mano en el último `echo` de un guion se compara con sus líneas `ROJO`; una mutación se mide a mano con el archivo de pruebas entero, para ver que pone en rojo sólo lo suyo y por aserción; `anclas_perdidas.py` sólo lee los `.sh`; un worktree que aparece en `git worktree list` mientras corre un guion mío es de ese guion, no un resto; una espera de 110 vueltas de 5 s no alcanza para tres corridas de 4 minutos: se vuelve a esperar la marca de fin, no se relanza; mientras haya una D mía sin contestar, el informe siguiente la repite arriba; el dato que fija «qué pedazo se muestra» no tiene ese pedazo al principio de donde sale, o cortar el todo da lo mismo; `sabotaje_sufijos1.sh` recibe el venv como segundo argumento, no por `PY`; un riesgo que diría «cubierto» se mide antes de escribirlo; mover un dato para tapar un agujero se mide de los dos lados, con todos los cambios anotados otra vez; un ítem vecino en un caso de avisos lleva su propio aviso, o el recorrido de ítems queda sin mirar; el criterio para dejar de iterar se dice y se sostiene, y lo que queda va como D; dos cambios del mismo tamaño aplicados en el mismo segundo comparten el `.pyc`: una medición rápida corre con `python -B` y sin `.pyc`; lo que vería el despachante con un cambio se mide en pantalla antes de escribirlo en una D; un dato de un caso se agrega, no se mueve: mover un dato destapa lo que el dato viejo fijaba; al reemplazar una prueba de la base, la nueva conserva la forma del dato viejo (largo, caracteres) o se mide qué deja de atrapar; al clasificar salidas de pytest por texto, «xfailed» contiene «failed»: se busca `\d+ failed`; el «conjunto ancho» se arma con `grep` de todos los archivos de prueba que tocan el generador, no con una lista de nombres; el informe de un subagente se guarda en un archivo apenas llega, y que lo haya escrito no quiere decir que terminó: antes de medir se mira con `ps` qué más corre; al despertar se trae la rama de la PM antes de seguir con lo que venía; regla de la PM: `/code-review high` se corre siempre, aunque sea sólo arnés, va hasta el SHA que se entrega, y un commit que nace de sus hallazgos pasa por el adversario; regla de la PM: en un vencido de sólo arnés, un último commit que cambia únicamente comentarios no necesita revisor si el informe lo dice, cualquier otro cambio sí. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que una D autoriza; subagentes hasta esfuerzo alto y sin consejero.
