# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Entrega D244 (a) sobre `6112322` (2026-11-16 20:25 UTC)

**Resultado.** Tus puntos 1 a 4 de D244 (a) se cumplen en `6112322`. Base: `2f96f2f` (tu rama
hasta `ad13f1a`). Producto: sólo `proyecto_maria/main.py`, `producto +16/−8`.

- **Punto 1.** `/generate_maria/avisos` llama a `_cuit_del_despachante`, la misma función que
  `/generate_maria`. Si levanta el 400, su texto va a los avisos tal cual, venga del perfil, de
  `cuit_agr` o del estudio elegido. Sin CUIT inválido no hay aviso nuevo: «uno bueno» lo fija.
- **Punto 2.** Un `cuit_agr` de puros espacios o guiones se limpia antes de elegir, así que cae al
  del perfil, o a «Falta el CUIT…» si no hay perfil. Vale en los avisos y al generar, porque es la
  misma función. Sale el dato de `MALOS` que fijaba el 400 con «».
- **Punto 3.** El orden estudio → `cuit_agr` → perfil está sólo en `_cuit_del_despachante`. Se
  fue la condición propia que tenían los avisos para «Falta».
- **Punto 4.** Es un solo caso, `test_los_avisos_dicen_lo_mismo_que_el_400_del_cuit_del_despachante`,
  con 7 datos: los tres orígenes malos; `cuit_agr` en blanco con perfil bueno, con perfil malo y sin
  perfil; y uno bueno. Cada dato mira los avisos y lo que sale al generar.
  - **Agregué uno a tu lista:** en blanco con perfil malo. Lo pidió `/code-review`. Es el único dato
    en el que, al caer al perfil, el error tiene que mandar a «Mi perfil». Con el código de la base,
    los avisos no decían nada y el 400 nombraba «» y mandaba a recargar la página.
  - **Rojo con el arreglo revertido** (el `main.py` de `2f96f2f` con las pruebas de `6112322`):
    `6 failed, 12 passed`. Fallan los seis datos con problema y pasa «uno bueno».

**Lo que decidís vos:**

1. **D259. Un estudio elegido con CUIT de puros espacios o guiones cae al del perfil.** Esto lo
   introdujo este cambio. En la base daba 400 nombrando «». Hoy:
   - con perfil bueno, sale el CUIT del perfil;
   - con perfil malo, el error dice «Es el del estudio elegido» y nombra el del perfil.

   Por la API no se llega: el alta de estudios exige 11 dígitos con verificador. Sólo pasa con un
   estudio escrito a mano en la base. Las opciones:
   - (a) Dejarlo así, como límite escrito.
   - (b) Con estudio elegido, sin caída al perfil:
     `cuit = sin_separadores(estudio.cuit) if estudio is not None else sin_separadores(cuit_agr) or del_perfil`.
     Daría «Falta el CUIT…». Cambia también el estudio con `""`, que en CUIT-GENERAR dejaste así.

   Recomiendo **(b)**: el estudio elegido manda y no tiene por qué caer en silencio al perfil.
   Son una línea y un dato. No lo hice porque es producto fuera de lo pedido.
2. **D260. La limpieza «sin guiones ni espacios» del CUIT está escrita tres veces en `main.py`.**
   Las tres están en `:4747` (`sin_separadores`, nueva), `:4965` (`comprador_cuit`, de la base) y
   `:7723` (el alta de estudios, de la base).
   - (a) Una línea para `docs/pm/COLA-LIMPIEZA.md`.
   - (b) Nada.

   Recomiendo **(a)**. No la unifiqué: dos de las tres son de la base (§6, lo ya escrito se limpia
   después).

**Supuestos (reversibles):**

1. **El aviso de CUIT inválido va en `supuestos`, adelante, como ya iba «Falta».** La pantalla lo
   muestra con el resto de los avisos. No toqué la pantalla.
2. **Un `cuit_agr` de `"="` cuenta como en blanco.** `limpiar_texto` lo pasa a `-` antes de llegar
   (ya era así en la base), y uno de puros guiones es en blanco.
3. **El commit `f165e9d` dice `fix:`, pero no cambia nada observable.** Devuelve `bool(cuit)` a la
   línea de `es_el_del_perfil`, que yo había sacado por muerta en `827189d`. La línea queda igual a
   la base. Sin ese `bool` sólo cambiaría lo que devuelve la función con `cuit` vacío, y generar
   corta con «Falta» antes de usarlo. Ya estaba subido, así que no lo reescribí.

| qué | SHA |
|---|---|
| base (tu rama hasta `ad13f1a`) | `2f96f2f` |
| producto y CHANGELOG | `827189d` |
| pruebas: el caso con la familia | `a4cd2fb` |
| pruebas: los sabotajes siguen al código nuevo | `68fd099` |
| producto: vuelve `bool(cuit)` (supuesto 3) | `f165e9d` |
| pruebas: `estudio1b.sh` igual a la base | `54d2ac2` |
| pruebas: dos frases de sabotaje | `c824b0d` |
| pruebas: el dato de perfil malo con `cuit_agr` en blanco | `7b920aa` |
| pruebas: los sabotajes cuentan ese dato. **Lo que se entrega** | `6112322` |
| tu `beccd54` (sólo `docs/pm/NOW.md`), integrado | `8c27f56` |
| informe | el commit siguiente |

## Comandos

```bash
VENV=/ruta/al/venv   # el tuyo
# 1. el rojo con el arreglo revertido: el main.py de la base con las pruebas de 6112322
git worktree add -f /tmp/rojo244 6112322 && (cd /tmp/rojo244 && git checkout 2f96f2f -- proyecto_maria/main.py \
  && env -u DATABASE_URL -u ENVIRONMENT GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
     PYTHONPATH=. $VENV/bin/python -B -m pytest -q --no-cov -p no:cacheprovider tests/test_cuit_generar.py | tail -1); \
  git worktree remove -f /tmp/rojo244
#    «6 failed, 12 passed»

# 2. los cuatro guiones de sabotaje que tocan el CUIT del despachante (unos 35 minutos en total)
for g in cuit_generar estudio1 estudio1b excel2; do PY=$VENV/bin/python bash scripts/testing/sabotajes/$g.sh 6112322 | tail -1; done
#    «sabotajes sin rojo: 0» en los tres primeros y «sabotajes con falla: 0» en excel2

# 3. anclas y §6
python3.12 scripts/testing/anclas_perdidas.py 6112322 | grep -E '^revisión|perdida'
#    «2541 anclas medidas», perdidas 0, 0 y 0
python3.12 docs/pm/herramientas/chequeo-6.py 2f96f2f 6112322
#    «producto +16/−8», «arnés +94/−50», «avisos: 0»
```

Corrí el 1 tal como está escrito, a las 20:28 UTC: `6 failed, 12 passed, 5 warnings in 13.56s`. Los
seis en rojo, de la misma medición con `grep FAILED` a las 19:47:

```
FAILED tests/test_cuit_generar.py::test_los_avisos_dicen_lo_mismo_que_el_400_del_cuit_del_despachante[malo en el perfil]
FAILED tests/test_cuit_generar.py::test_los_avisos_dicen_lo_mismo_que_el_400_del_cuit_del_despachante[malo en cuit_agr]
FAILED tests/test_cuit_generar.py::test_los_avisos_dicen_lo_mismo_que_el_400_del_cuit_del_despachante[malo en el estudio elegido]
FAILED tests/test_cuit_generar.py::test_los_avisos_dicen_lo_mismo_que_el_400_del_cuit_del_despachante[cuit_agr en blanco, con uno bueno en el perfil]
FAILED tests/test_cuit_generar.py::test_los_avisos_dicen_lo_mismo_que_el_400_del_cuit_del_despachante[cuit_agr en blanco, con uno malo en el perfil]
FAILED tests/test_cuit_generar.py::test_los_avisos_dicen_lo_mismo_que_el_400_del_cuit_del_despachante[cuit_agr en blanco, sin CUIT en el perfil]
================== 6 failed, 12 passed, 5 warnings in 14.45s ===================
```

El 3:

```
revisión 6112322: 103 guiones, 2541 anclas medidas y 11 llamadas sin medir
  perdida, una línea          0   guiones: 0
  perdida, varias líneas      0   guiones: 0
  perdidas de una línea sin repetir (archivo y texto): 0
chequeo-6 2f96f2f..6112322: avisos para mirar, no un veredicto
producto +16/−8
arnés +94/−50
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12272 → 12280
avisos: 0
```

El grep de historia de §6 sobre `proyecto_maria/` da vacío.

## Sabotajes (§3)

`cuit_generar.sh` tiene dos sabotajes nuevos:
- «un cuit_agr en blanco tapa el del perfil»;
- «los avisos no dicen que no cierra».

Salen dos, que fijaban el 400 con «» y ahora contradicen tu punto 2:
- «uno de puros espacios cuenta como que falta»;
- «uno vacío cuenta como el del perfil». Atacaba `bool(cuit)` a través de ese 400; sin él, ningún
  dato lo distingue (supuesto 3).

Dos cambiaron de frase («…se nombra como está guardado» y «…se nombra con el espacio»). Con un solo
`sin_separadores`, un perfil sin limpiar ahora se nombra tal como está guardado. El rojo sigue
siendo del mismo caso.

Cada sabotaje de `main.py` lista también los datos del caso nuevo que pone en rojo. El arnés exige
ese conjunto exacto. Lo medí a mano, mutación por mutación, con el archivo entero:

| sabotaje | en rojo |
|---|---|
| sólo se cuentan los dígitos | 10 |
| el del perfil no se mira | 5 |
| el que manda la operación no se mira | 3 |
| el del estudio elegido no se mira | 2 |
| dónde se corrige, al revés | 8 |
| el del estudio manda a corregir como la operación | 2 |
| el del perfil con guiones se nombra como está guardado | 1 |
| el del perfil con un espacio se nombra con el espacio | 1 |
| se nombra como llegó | 6 |
| un espacio en el medio queda en el CDDTAGR | 2 |
| el del perfil manda sobre cuit_agr | 4 |
| el estudio elegido no manda | 3 |
| un cuit_agr en blanco tapa el del perfil | 2 |
| los avisos no dicen que no cierra | 4 |
| el verificador sale siempre de «11 − resto» | 2 |
| se rechaza después de contar la operación | 6 |

En `estudio1.sh` cambian dos anclas, en `excel2.sh` una y `estudio1b.sh` queda igual a la base.
Cada sabotaje cambiado sigue poniendo en rojo sólo lo suyo; lo medí a mano.

**Límite del arnés:** la frase que exige `sabotaje` sale de un solo dato. Para los datos del caso de
los avisos que también caen, el arnés controla que estén en rojo, pero no por qué. Lo miré a mano:
todos caen por `AssertionError`, y el adversario Sonnet repitió 14 de esas mediciones.

## Revisión

| revisor | sobre | hallazgos | qué hice |
|---|---|---|---|
| `/code-review high` | `2f96f2f..68fd099` | los de al lado | **Arreglado:** `bool(cuit)` vuelve (`f165e9d`, supuesto 3). **Sin arreglo:** el chequeo de «Falta» en dos lugares (ya estaba en la base: generar corta antes de usar la función); la forma de `e.detail` (siempre `{"errors": [...]}` en esa función); los avisos en `supuestos` (supuesto 1); la limpieza repetida (D260); el caso en blanco sin `_operaciones` (lo cuenta `MALOS`); `ANTES_DE_GENERAR` repite orígenes de `MALOS` (lo pediste como familia de un caso); `isdigit` para separar «bueno» de un texto de error (todos los CUIT del caso son dígitos) |
| adversario Opus alto | `68fd099` | 4 bajos | **D259** (estudio en blanco cae al perfil, introducido acá). Ya estaban en la base: los caracteres invisibles (U+200B), `=` → `-` por `limpiar_texto` (supuesto 2), y un `cuit_agr` que no es texto da 422 |
| adversario Sonnet alto | `68fd099` | 3 | **Arreglado:** dos sabotajes daban `ROJO?` con la frase vieja (`c824b0d`); `bool(cuit)` (`f165e9d`). Los invisibles ya estaban en la base |
| `/security-review` | `2f96f2f..c824b0d` | ninguno | Miró el aislamiento de estudios, el escape del aviso en pantalla (`CDI.escapeHtml`, `finalize.js:274-281`), la validación del CDDTAGR y la autenticación |
| `/code-review high` | `2f96f2f..c824b0d` | los de al lado | **Arreglado:** el docstring del archivo de pruebas (`7b920aa`) y el dato de perfil malo con `cuit_agr` en blanco (`7b920aa`, `6112322`). **Sin arreglo:** D259; `bool(cuit)` no se puede observar (supuesto 3) |
| adversario Sonnet alto | `c824b0d` | ninguno | Reprodujo las dos frases nuevas; `209 passed` en los cuatro archivos |
| `/code-review high` | **`2f96f2f..6112322`** | 10 | **Sin arreglo:** D259 (dos hallazgos); D260; el límite del arnés (arriba); el caso de «Falta» sin `_operaciones` (es el camino de la base, no lo amplío); la forma de `e.detail`, `supuestos`, un caso por causa e `isdigit`, como en la primera vuelta; una línea larga en el encabezado de `cuit_generar.sh` (sólo comentario) |
| adversario Sonnet alto | **`c824b0d..6112322`** | ninguno | El dato nuevo distingue tres sabotajes reales; las 14 listas de rojos que corrió coinciden con el guion; el docstring es cierto |

Mi criterio para dejar de iterar fue que lo que saliera sobre `6112322` iba al informe, salvo un
defecto real dentro de lo pedido. No salió ninguno. `/security-review` corrió hasta `c824b0d`:
`7b920aa` y `6112322` sólo tocan el archivo de pruebas y el guion. Ningún subagente queda vivo.

## Puertas

Todo sobre `6112322`, en un worktree limpio de ese SHA, de 19:23 a 20:17 UTC. Salida exacta:

```
### cuit_generar salida 0 · sabotajes sin rojo: 0
### estudio1 salida 0 · sabotajes sin rojo: 0
### estudio1b salida 0 · sabotajes sin rojo: 0
### excel2 salida 0 · sabotajes con falla: 0
### suite salida 0 · === 6196 passed, 110 skipped, 3 xfailed, 108 warnings in 1264.52s (0:21:04) ====
### compileall 0
### npm ci 0
### e2e salida 0 · E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.
```

- **Cuenta de cada guion:** `cuit_generar` 21 `ROJO`, `estudio1` 37, `estudio1b` 20 y `excel2` 42.
  Ningún `ROJO?`.
- **La suite** corrió entera, sin `-k` ni deselección, con `DATABASE_URL=sqlite+aiosqlite:///./test.db`
  y `ENVIRONMENT=test`, desde un `test.db` borrado.

**No corrí:**
- `pantalla_cuit_generar1.js` suelto. No toqué la pantalla; el guion corre dentro de
  `cuit_generar.sh`, en sus sabotajes de pantalla.
- `test_despacho1b` aparte, porque me pediste que no lo midiera. Corrió dentro de la suite
  y pasó, pero no lo miré más allá de eso.

## Riesgos

1. **D259**, mientras no la decidas. Baja: por la API no se llega.
2. **Un carácter invisible (U+200B) pegado a un CUIT de `cuit_agr` no se limpia.** Ya estaba en la
   base. No llega al TXT: da 400 al generar y, desde ahora, un aviso con el mismo texto. Pero el
   mensaje nombra un CUIT que se ve igual a uno bueno, o «» si sólo vino el invisible. Baja: es un
   mensaje confuso, no un TXT malo.
3. **El aviso ahora sale también con estudio elegido.** Antes, con estudio, los avisos nunca hablaban
   del CUIT; ahora dicen si el del estudio no cierra. Es lo que pediste en el punto 1, y
   `test_con_estudio_los_avisos_no_piden_el_cuit` sigue verde con uno bueno.

D259 y D260 esperan tu respuesta; D239 y «Holanda» esperan a Emi.

Última vuelta: 2026-11-16 20:25 UTC.

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5, rama `claude/dev-maria`, rutina trig_01Ukttby1fc4sGVQfSn1jC9U; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rutina trig_01TvMmGfSLDfbcJrf66ZZ7YK, rama `claude/practical-shannon-szpwkn`, integrada hasta `beccd54`). Aceptadas: las de antes (CUIT-GENERAR `29327d2` … D257 (b) `3c7eb14`, acta `REPRODUCCION-D257-2026-11-15.md`); D258 (a): a la cola. En revisión: D244 (a), entregada sobre `6112322` (base `2f96f2f`), informe en el commit siguiente; puertas verdes sobre `6112322` (4 guiones de sabotaje, suite 6196 passed, e2e OK). Abiertas mías: D259 (estudio elegido con CUIT en blanco cae al perfil; recomiendo (b)) y D260 (limpieza del CUIT escrita tres veces; recomiendo (a), cola). D239 y «Holanda»: Emi dijo sí, pero esperan otra pregunta a Emi (el 434 escrito solo); no se tocan hasta que la PM las active. `test_despacho1b`: lo mide la PM, yo no. Próxima D: D261. Sin pieza marcada «apenas entregues»: si al despertar no hay nada nuevo, termino la vuelta. Lecciones: frenar una cola deja el generador mutado en su worktree: `git checkout -- .` antes de medir a mano ahí; la premisa de un criterio se mide antes de elegir el dato (la 55, con el sufijo de operación de siempre, quedaba verde); cuando dos revisores se contradicen se decide por lo que controla: un número escrito a mano en un guion es un control, un contador no; el worktree de una cola decide qué SHA mide: las tareas «base» corren en el worktree de la base, no en el del SHA que se entrega; antes de comparar una cuenta con la de otra sesión se miran los `skipped` con `-rs` (una dependencia que falta en el venv, como `xlwt`, saltea pruebas sin dar rojo); «por carga» no explica un corte de `ITIMER_PROF`, que cuenta CPU del proceso y no reloj; un bloque de comandos del informe se corre tal como está escrito antes de entregarlo; antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada; un dato nuevo de un caso no reusa un valor que otro control del mismo caso espera; antes de escribir el informe se trae la rama de la PM; antes de sacar una prueba por duplicada se compara lo que afirma cada una, no sólo sus entradas; antes de reescribir un sabotaje con el ancla perdida se mira si la protección que atacaba sigue existiendo: si no, es una D (D195 (a)); al ajustar una afirmación, la nueva tiene que seguir afirmando todo lo que afirmaba la vieja (el orden también), y una mutación que «mueve» una frase la tiene que sacar de donde estaba; una medición corre sobre el conjunto más angosto de pruebas que contesta la pregunta; antes de cambiar un número que la PM fijó como criterio se lee por qué lo fijó; un comentario o un mensaje de commit no afirma lo que el guion no obliga, y su porqué se comprueba con `git show`, no se supone; que «nadie cubría» algo se mide antes de escribirlo, y con todas las pruebas que usan ese dato, no sólo las del guion (un adversario que corre cuatro archivos dice «hueco» donde otra prueba lo atrapa); `anclas_perdidas.py` mide un commit: el arreglo se commitea antes de medir; el SHA que se entrega pasa por subagente o `/code-review`, y si el gancho de parada ya subió el commit, lo que siga va en un commit nuevo; después de un commit nuevo o de corregir uno, las puertas corren otra vez sobre ese SHA; un ancla lleva sólo el texto que saca más lo mínimo que la ata a su lugar; la cuenta escrita a mano en el último `echo` de un guion se compara con sus líneas `ROJO`; una mutación se mide a mano con el archivo de pruebas entero, para ver que pone en rojo sólo lo suyo y por aserción; `anclas_perdidas.py` sólo lee los `.sh`; un worktree que aparece en `git worktree list` mientras corre un guion mío es de ese guion, no un resto; una espera de 110 vueltas de 5 s no alcanza para tres corridas de 4 minutos: se vuelve a esperar la marca de fin, no se relanza; mientras haya una D mía sin contestar, el informe siguiente la repite arriba; el dato que fija «qué pedazo se muestra» no tiene ese pedazo al principio de donde sale, o cortar el todo da lo mismo; `sabotaje_sufijos1.sh` recibe el venv como segundo argumento, no por `PY`; un riesgo que diría «cubierto» se mide antes de escribirlo; mover un dato para tapar un agujero se mide de los dos lados, con todos los cambios anotados otra vez; un ítem vecino en un caso de avisos lleva su propio aviso, o el recorrido de ítems queda sin mirar; el criterio para dejar de iterar se dice y se sostiene, y lo que queda va como D; dos cambios del mismo tamaño aplicados en el mismo segundo comparten el `.pyc`: una medición rápida corre con `python -B` y sin `.pyc`; lo que vería el despachante con un cambio se mide en pantalla antes de escribirlo en una D; un dato de un caso se agrega, no se mueve: mover un dato destapa lo que el dato viejo fijaba; al reemplazar una prueba de la base, la nueva conserva la forma del dato viejo (largo, caracteres) o se mide qué deja de atrapar; al clasificar salidas de pytest por texto, «xfailed» contiene «failed»: se busca `\d+ failed`; el «conjunto ancho» se arma con `grep` de todos los archivos de prueba que tocan el generador, no con una lista de nombres; el informe de un subagente se guarda en un archivo apenas llega, y que lo haya escrito no quiere decir que terminó: antes de medir se mira con `ps` qué más corre; al despertar se trae la rama de la PM antes de seguir con lo que venía; regla de la PM: `/code-review high` se corre siempre, aunque sea sólo arnés, va hasta el SHA que se entrega, y un commit que nace de sus hallazgos pasa por el adversario; regla de la PM: en un vencido de sólo arnés, un último commit que cambia únicamente comentarios no necesita revisor si el informe lo dice, cualquier otro cambio sí; un `fix:` que deja una línea igual a la base y no es observable se declara como supuesto, no se reescribe lo subido; un dato que agrega una revisión se cuenta en las listas de rojos de cada sabotaje del guion, medido a mano; un vigilante en segundo plano no lleva un `timeout` menor que lo que espera: se espera la notificación de la tarea principal. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que una D autoriza; subagentes hasta esfuerzo alto y sin consejero.
