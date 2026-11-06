# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## COBRO-CORTE-1, devolución de las 22:00, entregada en `8295bb5` (informe en el commit de arriba)

| SHA | qué |
|---|---|
| `eed4f36` | producto: lo que no se entrega no se cobra, la respuesta tardía no toca la carga nueva, el id que Postgres no guarda, el aviso «Sin cliente» y el candado al borrar; CHANGELOG |
| `441390d` | pruebas: un caso por causa y por punto, la pantalla y los sabotajes |
| `c978a88` | producto (refactor sin cambio de comportamiento): en v1, «anotá el id si es de la carga actual» va una sola vez, en `anotarOperacion` |
| `b285804`, `e7fcd6f` | pruebas: la respuesta tardía en su función, con los casos como datos |
| `1fea5ba` | producto: regenerar con una falla no rompe lo entregado; la respuesta tardía guarda lo de su carga (cliente en v1, totales y valores en v2); borrar y guardar leen el cliente después del candado |
| `892f487` | pruebas de `1fea5ba` |
| `e487090` | producto: el archivo vuelve antes del rollback, un `.anterior` viejo no pisa lo entregado, la carga nueva en «Listo» genera; el par candado + cliente pasa a `_cliente_con_cuenta_bloqueada` |
| `5466968` | pruebas de `e487090` |
| `fbea636` | pruebas: el arnés de `test_valor1c` sigue a `generateMaria` (la suite daba 3 rojos sobre `892f487`, abajo) |
| `92a981f` | merge de tu rama: no cambia nada fuera de `docs/pm` |
| `555cd98` | pruebas: el primer commit fallido no deja el TXT en las descargas (un sabotaje daba VERDE, abajo) |
| `8ef0752` | pruebas: tres sabotajes de la pantalla esperan el texto que da su rojo (daban ROJO?, abajo) |
| `8295bb5` | merge de tu rama (vuelta de las 01:55): sólo `docs/pm/NOW.md` |

Base: `7eda007` (tu rama con `d528a67` y `9213536`, como pediste).
Producto `+122/−60`: suma 62 netas porque las dos causas se arreglan en tres
lugares cada una (servidor, v2 y v1).

**Resultado.** Las dos causas, cerradas donde nacen:

- **Causa 1.** El conteo se confirma sólo con el archivo escrito.
  `_escribir_y_confirmar` (`main.py:5952`) escribe en `.parcial`, deja el
  archivo ya entregado con otro nombre (hardlink a `.anterior`), reemplaza
  atómico y recién ahí hace el commit. Si algo falla, primero vuelve el
  archivo entregado (o se borra el nuevo) y después el rollback. Lo que puede
  fallar después de contar (los supuestos) se arma antes.
- **Causa 2.** La respuesta pertenece a la carga que la pidió.
  - v2 (`finalize.js`) toma la carga, sus totales y los valores del
    despachante al pedir. La respuesta anota el id, guarda y marca «Listo»
    sólo en esa carga. Una carga nueva que llega a «Listo» mientras la anterior
    espera genera cuando ésa vuelve, y el error de la anterior no le cambia el
    paso ni se le muestra.
  - v1 (`app.js`) toma la carga y el cliente al pedir: `anotarOperacion` anota
    el id sólo si sigue en la misma carga.

**Nada para decidir.** Sin D. Supuestos reversibles:

- un `.anterior` o un `.parcial` que quede de un proceso cortado se descarta en
  la próxima regeneración del mismo archivo;
- un id con NUL o con un surrogate es una operación nueva y contada, como un
  id desconocido.

### Cómo se cumple cada causa y cada punto

| | qué hace el producto | caso | sabotaje |
|---|---|---|---|
| Causa 1: se cobra antes de entregar | `_escribir_y_confirmar`: escribir, reemplazar y recién ahí confirmar; los supuestos antes de contar | `test_lo_no_entregado_no_queda_cobrado`, familia como datos: `importacion_al_escribir`, `importacion_despues_de_contar`, `importacion_al_confirmar` y `exportacion_al_escribir` | «se confirma el conteo antes de escribir», «lo escrito a medias queda en las descargas», «un primer commit fallido deja el archivo en las descargas», «los supuestos se arman después de contar» |
| Causa 1, al regenerar: lo ya entregado queda entero | `.parcial`, hardlink a `.anterior` y `os.replace`; si falla, vuelve el `.anterior` que enlazó esta regeneración, antes del rollback | `test_regenerar_con_una_falla_deja_entero_lo_ya_entregado`: `al_escribir`, `al_confirmar`, `al_confirmar_y_deshacer` (el rollback también falla) y `al_escribir_con_un_anterior_viejo` | «regenerar escribe sobre lo ya entregado», «un commit fallido deja el archivo nuevo», «se deshace la base antes de devolver el archivo», «se restaura un anterior que no es de esta regeneración» |
| Causa 2: la respuesta tardía no escribe en la carga que sigue | v2: la carga, sus totales y sus valores se toman al pedir. v1: la carga y el cliente se toman al pedir | pantalla, `casosTardios` con siete casos como datos: v2 generar y guardar, v1 generar y guardar, y la carga nueva en «Listo» con la anterior que vuelve bien, con un error o sin red | nueve de v2 («generar anota en la carga de la pantalla», «guardar anota…», «generar guarda con la carga de la pantalla», «el guardado toma los valores de la pantalla al responder», «la respuesta tardía marca lista la carga nueva», «el guardado toma el cliente de la pantalla», «la carga nueva en «Listo» no genera», «el error de la anterior cambia de paso a la carga nueva», «la anterior sin red le muestra el error a la carga nueva») y cuatro de v1 («generar anota en la carga nueva», «guardar anota…», «el guardado toma el cliente del selector al responder», «cancelar no empieza otra carga») |
| 3. un id con NUL o surrogate no da 500 | `_operacion_del_usuario` no busca en la base un id que Postgres no puede comparar (`_NO_GUARDABLE_EN_PG`) | `test_un_id_que_la_base_no_guarda_es_una_operacion_nueva` (generar, exportar, guardar × NUL, surrogate) y el caso 5 de `cobro_corte1_postgres.py`, que es donde el NUL da 500 | «un id que la base no guarda se busca igual», «Postgres recibe el id que no puede comparar» |
| 4. el aviso dice «Sin cliente» | `clientes.js`: «Sus operaciones quedan en el historial como «Sin cliente», sin el detalle de sus ítems. Se borran sus productos aprendidos y notas NCM. Esta acción no se puede deshacer.» | sin caso: es un texto | — |
| 5. `delete_cliente` toma el candado | `delete_cliente` y `save_client_operation` usan `_cliente_con_cuenta_bloqueada`: candado y después el cliente | caso 6 de Postgres (borrar espera el candado) y caso 7 (el guardado que esperaba detrás del borrado de su cliente da 404 sin operación, no un 500 por la FK) | «borrar cliente no espera el candado de la cuenta», «el guardado mira el cliente antes del candado» |

### Puertas

| Puerta | SHA | Salida |
|---|---|---|
| suite completa | `555cd98` | `4498 passed, 121 skipped, 3 xfailed, 101 warnings in 610.16s (0:10:10)`, salida 0; `compileall` salida 0 |
| suite completa | `fbea636` | `4497 passed, 121 skipped, 3 xfailed, 101 warnings in 631.93s (0:10:31)`, salida 0; `compileall` salida 0 |
| suite completa | `892f487` | `3 failed, 4492 passed, 121 skipped, 3 xfailed`: los tres de `test_valor1c` con «ReferenceError: fotoDeLaPantalla is not defined» (su arnés extrae `generateMaria` sola). Arreglado en `fbea636` |
| `test_cobro_corte1.py` + `test_valor1c.py` | `555cd98` | 126 passed, 7 warnings |
| sabotajes `cobro_corte1.sh`, con Postgres | `8295bb5` | 85 `ROJO`, 0 `ROJO?`, 0 `VERDE`, 0 `ROTO`; «sabotajes con falla: 0», salida 0 |
| sabotajes `cobro_corte1.sh`, con Postgres | `555cd98` | 82 `ROJO`, 3 `ROJO?`; «sabotajes con falla: 3», salida 1 (abajo) |
| `/code-review high` | `e7fcd6f..892f487` | 9 hallazgos, abajo |
| `/security-review` | `7eda007..HEAD`, producto | sin hallazgos |

De `555cd98` a `8295bb5` sólo cambian `cobro_corte1.sh` (+4/−3) y `NOW.md`:
la suite y las pruebas de la pieza corridas sobre `555cd98` valen para el
producto entregado, que es el mismo.

`smoke_friccion.sh` y `ataque_aislamiento.sh`: no corridos. La pieza no toca
permisos: borrar y guardar siguen filtrando el cliente por dueño, ahora
después del candado.

### Rojo antes

Pruebas de `fbea636` sobre el producto de `7eda007`:
`12 failed, 113 passed`, salida 1.

- `test_un_id_que_la_base_no_guarda_es_una_operacion_nueva`:
  - `[surrogate-generar]` da 400 con «'utf-8' codec can't encode character '\ud800'…»;
  - `[surrogate-exportar]` y `[surrogate-guardar]` dan 500.
- `test_lo_no_entregado_no_queda_cobrado`, filas `[importacion_al_escribir]`,
  `[importacion_despues_de_contar]` y `[exportacion_al_escribir]`, con «lo que no se
  entregó quedó contado / assert 1 == 0».
- `test_regenerar_con_una_falla_deja_entero_lo_ya_entregado`, filas `[al_escribir]`
  y `[al_escribir_con_un_anterior_viejo]`, con «el archivo ya entregado cambió con
  una regeneración que falló».
- 4 de arnés: `test_sin_sesion_las_rutas_que_cuentan_dan_401` («_contar_maria() takes
  6 positional arguments but 7 were given») y 3 de `test_valor1c` («no está
  fotoDeLaPantalla en finalize.js»). No son el defecto: muestran que la prueba
  llama al producto nuevo.

Lo que pasa en la base y por qué:

- Las filas NUL de pytest pasan porque SQLite acepta el NUL. El punto 3 se ve
  en Postgres.
- `al_confirmar`, `al_confirmar_y_deshacer` e `importacion_al_confirmar` (ésta,
  corrida aparte con las pruebas de `555cd98`: `3 failed, 1 passed` en la
  familia) pasan porque cuidan defectos que nacieron en esta vuelta: en la base
  el commit iba antes de escribir. Los sostiene su sabotaje.

No corridos: el rojo antes de Postgres (casos 5 a 7) contra `7eda007` y el de
la pantalla contra la base. Lo que sí hay, sobre SHAs intermedios de esta
vuelta:

- `e7fcd6f`:
  - pantalla: «FALLA: v2, generar: guardó los valores de la carga nueva» y
    «FALLA: v1, generar: la respuesta tardía no se guardó en el cliente de su
    carga con su operación (mandó «undefined»)»;
  - Postgres: «FALLA | guardar en un cliente que se borró mientras esperaba: 404
    sin operación (esperó True, 500, 0 operaciones)».
- `892f487`:
  - `test_regenerar…`: 2 failed, 2 passed;
  - pantalla: «FALLA: v2, la carga nueva en «Listo» y la anterior vuelve bien: no terminó».

### Lo que encontraron los sabotajes

La primera corrida, sobre `fbea636`, dio
«VERDE | lo escrito a medias queda en las descargas: la prueba no lo vio».

- El sabotaje sacaba el borrado del archivo final en el `except`. Desde
  `1fea5ba` se escribe primero en `.parcial`, así que la falla al escribir ya
  no crea ese archivo.
- Ese borrado sólo actúa cuando falla el commit de una primera generación, y
  ninguna fila lo probaba. Sin él, el TXT quedaba en las descargas sin contar.
- En `555cd98`:
  - la fila `importacion_al_confirmar` cubre esa falla, con el sabotaje nuevo
    «un primer commit fallido deja el archivo en las descargas»;
  - el sabotaje viejo pasa a sacar la limpieza del `.parcial`, que es lo que
    su nombre dice.
- Corridos a mano antes del commit:
  - el nuevo da `1 failed` en `[importacion_al_confirmar]`;
  - el viejo da `4 failed`, entre ellos `[exportacion_al_escribir]`.

Esa corrida además se cortó por un error mío: edité el script mientras bash lo
ejecutaba y dio «syntax error near unexpected token» en la línea 317, salida 2.
No cuenta. Desde ahí, ninguna corrida tuvo el árbol tocado mientras corría.

La de `555cd98` dio tres `ROJO?`: el sabotaje rompía lo que debía y el
caso lo vio, pero con otro texto que el esperado. Reproducidos uno por uno:

- «v2: generar anota en la carga de la pantalla»: la carga vieja guarda sin
  id y salta antes el chequeo del guardado: «FALLA: v2, generar: la respuesta
  tardía no se guardó en el cliente de su carga con su operación (mandó «»)».
- «v2: la anterior sin red le muestra el error a la carga nueva»: el texto
  real dice «la anterior se queda sin red», no el nombre del caso.
- «v1: guardar anota en la carga nueva»: generar también guarda, así que lo ve
  antes «FALLA: v1, generar: la carga nueva quedó con la operación». Corrido
  sólo el caso de guardar, da por su cuenta «FALLA: v1, guardar: la carga nueva
  quedó con la operación «la-operacion-de-la-carga-anterior», no «»».

`8ef0752` cambia sólo esos tres textos esperados; sobre `8295bb5` los tres dan
`ROJO` con el texto nuevo.

### Hallazgos de la autorrevisión

Adversario Sonnet alto (uno solo, como pide la vuelta), sobre `eed4f36`:

| # | hallazgo | qué hice |
|---|---|---|
| 1 | regenerar con la escritura fallando pisa el TXT ya entregado (reproducido: 1745 bytes pasan a 5) | arreglado en `1fea5ba` (`.parcial`, hardlink y reemplazo atómico); caso y sabotajes en `892f487` |
| 2 | guardar contra un cliente que se borra a la vez da 500 por la FK (reproducido en Postgres: 13 de 18) | arreglado en `1fea5ba`: el cliente se lee después del candado y da 404; caso 7 de Postgres |
| 3 | v2: el guardado tardío toma la validación y los valores de la carga nueva | arreglado en `1fea5ba`: se toman al pedir; caso y sabotaje en `892f487` |
| 4 | `PATCH /api/operations/{id}/estado`, agrupar y desagrupar dan 500 con NUL en Postgres | queda como riesgo: no cuentan ni exponen nada, y sólo le pasa a quien manda el NUL |
| 5 (plausible) | `CancelledError` durante el commit, con el commit ya en el servidor: cobra sin entregar | queda como riesgo: no se pudo disparar y el cliente tampoco recibe la respuesta |
| 6 (plausible) | v1: el guardado tardío toma el cliente del selector al responder | arreglado en `1fea5ba` (`carga.cliente`); caso y sabotaje en `892f487` |

`/code-review high` (Opus, alto) sobre `e7fcd6f..892f487`:

| # | hallazgo | qué hice |
|---|---|---|
| 1 | el rollback iba antes de devolver el archivo: si fallaba, se perdía lo entregado | arreglado en `e487090`; fila `al_confirmar_y_deshacer` y su sabotaje |
| 2 | la carga nueva en «Listo» quedaba en el spinner por `generateInFlight` (regresión mía) | arreglado en `e487090` con `pedidaMientrasOtra`; tres casos de la pantalla |
| 3 | si fallaba el `.parcial`, se restauraba un `.anterior` viejo | arreglado en `e487090` con `enlazado`; fila `al_escribir_con_un_anterior_viejo` |
| 4 | el error de una carga reemplazada llegaba a la carga nueva | arreglado en `e487090`: guarda en el `catch`; dos casos de la pantalla |
| 5 | v1 (`app.js:3408`): la respuesta tardía muestra el alert de supuestos, «¡Generado!» y la descarga | queda como riesgo: v1, y no anota ni guarda nada en la carga nueva |
| 6 | el `FOR UPDATE` queda tomado tras el 404 hasta cerrar la sesión | descartado: son milisegundos, en la misma petición |
| 7 | en un volumen sin hardlinks, `os.link` falla y toda regeneración da 500 | queda como riesgo, abajo |
| 8 | altura: fotos de globales sueltos en v2 | a la cola de limpieza |
| 9 | el par candado + cliente estaba repetido en dos rutas | arreglado en `e487090`: `_cliente_con_cuenta_bloqueada` |

`/security-review` a mano sobre el producto `7eda007..HEAD`: sin hallazgos.
Los nombres `.parcial` y `.anterior` salen del archivo de la operación, que
arma el servidor, dentro de la carpeta del usuario.

### Riesgos

- **Hardlinks** (code-review #7): si las descargas viven en un volumen sin
  hardlinks, toda regeneración da 500 y no cobra. Railway usa un disco local
  que los soporta, pero no lo probé allí.
- Un `.anterior` o `.parcial` de un proceso cortado queda en disco hasta la
  próxima regeneración. Sólo lo ve su dueño.
- Borrar un cliente toma el candado de la cuenta y de la org, y la escritura a
  disco ocurre con el candado tomado: los pedidos de la misma cuenta esperan
  esos milisegundos.
- `CancelledError` con el commit ya en el servidor (adversario #5).
- `PATCH /estado`, agrupar y desagrupar dan 500 con NUL en Postgres
  (adversario #4).
- La fila NUL × guardar de pytest no distingue el defecto en SQLite. Lo
  distingue el caso 5 de Postgres.
- v1: la respuesta tardía igual muestra sus avisos y descarga (code-review #5).
- El `onLeave` de «Listo» que limpia la carga pedida no tiene caso propio.
- Observación, no de esta pieza: con pedidos en paralelo sobre SQLite, la API
  registra «database is locked» al escribir el historial del cliente
  (`main.py:7593`, existe desde `7e9c989`). Es una escritura que puede fallar
  sin cortar el guardado, y aparece también en la pantalla sin sabotaje (2 veces,
  en verde).

### chequeo-6

```
chequeo-6 7eda007..8295bb5: avisos para mirar, no un veredicto
producto +122/−60
  AVISO producto suma 62 líneas netas: el informe dice por qué (§6: más de 20)
arnés +417/−13
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11302 → 11333
  proyecto_maria/static/app.js: 6765 → 6772
  AVISO creció una función de más de 150: proyecto_maria/static/app.js:3263 generateMariaTxt 190 → 191, 1 en su propio cuerpo (§6: lo nuevo va aparte)
  proyecto_maria/static/v2/screens/clientes.js: 1984 → 1984
  proyecto_maria/static/v2/screens/finalize.js: 1360 → 1384
  AVISO creció una función de más de 150: proyecto_maria/static/v2/screens/finalize.js:9 <anónima> 1352 → 1376, 6 en su propio cuerpo (§6: lo nuevo va aparte)
  AVISO función nueva de 74 líneas: scripts/testing/pantalla_cobro_corte1.js:30 casosTardios (§6: ~60)
avisos: 4
salida 0
```

Por qué queda cada AVISO:

- las 62 netas: las dos causas en servidor, v2 y v1 (arriba);
- `generateMariaTxt`: la línea nueva toma la carga antes del fetch, y lo
  demás ya salió a `anotarOperacion`. Partir la función va a la cola de limpieza;
- `<anónima>` es el envoltorio del módulo de `finalize.js`, no una función;
- `casosTardios`: son los siete casos como datos, uno por línea de la tabla.

### Para reproducir

```bash
git checkout 8295bb5
# 1. «126 passed, 7 warnings»
DATABASE_URL=sqlite+aiosqlite:///./t.db GEMINI_API_KEY=test-key ENVIRONMENT=test python -m pytest -q --no-cov tests/test_cobro_corte1.py tests/test_valor1c.py
# 2. todo ROJO y «sabotajes con falla: 0»; sin PG, la parte de Postgres dice «NO CORRIDO»
PY=$(which python) PG=postgresql://<usuario>@127.0.0.1:<puerto> scripts/testing/sabotajes/cobro_corte1.sh 8295bb5
# 3. «avisos: 4»
python docs/pm/herramientas/chequeo-6.py 7eda007 8295bb5
```

### Archivos de producto tocados

`proyecto_maria/main.py` (generar, exportar, guardar, borrar cliente),
`proyecto_maria/static/app.js`,
`proyecto_maria/static/v2/screens/finalize.js`,
`proyecto_maria/static/v2/screens/clientes.js` (sólo el texto del aviso) y
`CHANGELOG.md`.

---

/compact conservar: Dev 1, rama claude/dev-tecnica. COBRO-CORTE-1
(devolución 22:00) entregada en 8295bb5 (informe en el commit de arriba), sin
D. Sigue COBRO-MP-2 (D62), empezando por los rojos de sus sabotajes. Nada se
publica sin el «dale» de Emi; nunca main.
