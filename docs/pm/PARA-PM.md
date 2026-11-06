# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## COBRO-CORTE-1, vuelta 3, entregada en `ca50916` (informe en el commit de arriba)

| SHA | qué |
|---|---|
| `178eb4a` | producto: la respuesta tardía aprende el catálogo en el proveedor de su carga; «Generar» ya no queda trabado mientras otra espera, y lo pedido se genera cuando ésa vuelve; el respaldo al regenerar es una copia, no un enlace; CHANGELOG |
| `ffb2aca` | pruebas de `178eb4a`: pytest, pantalla con clics y sabotajes |
| `3fe7ffd` | producto: el cliente elegido mientras la generación espera se usa al guardar; «Reintentar» pide una sola generación (dos hallazgos del adversario, abajo) |
| `d9afd09` | pruebas de `3fe7ffd` y el contenido regenerado |
| `6f186c5` | pruebas: el doble clic en «Reintentar» pasa a su propia función (AVISO de chequeo-6 sobre `d9afd09`) |
| `d309be6` | pruebas: pasar a otro cliente mientras la generación espera, con su sabotaje (hallazgo del segundo `/code-review`) |
| `b4cb5f9` | producto: se saca la guarda `carga === CDI.state` delante del error sin red de la generación anterior, que no tenía efecto observable (abajo, «Un sabotaje en verde») |
| `86e2048` | pruebas: se retira el sabotaje de esa guarda |
| `4b071ac` | merge de tu rama (`d26c404`), que trae la limpieza y retira la v1: se acepta el borrado de `static/app.js` y se descartan mis cambios a la v1; en el CHANGELOG, la entrada del corte deja de nombrar la v1 |
| `ca50916` | pruebas: la pantalla y `cobro_corte1.sh` dejan los casos y los sabotajes de la v1 |

Base de la vuelta: `633c383`, que era tu merge. Producto de la vuelta: `+23/−21`. Después del merge de `d26c404`, la v1 ya no existe: los cambios de esta pieza a `static/app.js` se fueron con el archivo.

**Resultado.** Las tres cosas que pediste están cerradas:

- **Causa 2.** Todo lo que hace la respuesta sale de la carga que la pidió.
  - Al pedir, `fotoDeLaPantalla` toma el cliente, los totales y los valores del despachante.
  - El historial guarda en ese cliente.
  - `saveCatalogLearn(items, carga)` aprende en el proveedor de esa carga.
  - Si al pedir no había cliente, toma el que se le eligió a esa misma carga mientras esperaba, nunca el de la carga que sigue.
- **B ya no queda trabada.** «Generar» sólo se deshabilita por errores.
  - Si B pide con A en espera, el pedido queda anotado (`pedidaMientrasOtra`).
  - Cuando A vuelve, `onEnterReady()` genera con lo que hay en pantalla.
  - El caso maneja la pantalla con clics.
  - `pedidaMientrasOtra` tiene un camino real (el clic de B con A en espera) y su sabotaje da rojo, así que se queda.
- **Sin enlaces.** `_escribir_y_confirmar` respalda lo ya entregado con `shutil.copyfile` en vez de `os.link`.
  - Si el commit falla, la copia vuelve antes del rollback, como antes.
  - Lo que cuesta: una copia del TXT por regeneración, que pesa pocos KB.

**Nada para decidir.** Sin D. Hay un supuesto reversible: con un doble clic en «Reintentar», el primer clic oculta el error, así que el segundo ya no encuentra el botón. No hay candado aparte.

### Cómo se cumple cada punto

| | qué hace el producto | caso | sabotaje (`cobro_corte1.sh`) |
|---|---|---|---|
| Causa 2: historial, catálogo y cliente de la carga que pidió | `fotoDeLaPantalla` con `cliente`; `saveOperationToHistory` usa `foto.cliente \|\| carga.clienteActivo`; `saveCatalogLearn(items, carga)` | pantalla, `casosTardios`: «v2, generar» (el catálogo aprende en su proveedor y el historial va a su cliente), «v2, generar y sacar el cliente», «… pasar a otro cliente» y «… elegir el cliente» | «v2: el guardado toma el cliente de la pantalla», «v2: el guardado prefiere el cliente elegido después de pedir», «v2: sin cliente al pedir, el guardado no toma el que se le eligió a la carga», «v2: el catálogo aprende en el proveedor de la pantalla» |
| B genera cuando A vuelve | `vGenerate.disabled` sólo por errores; sin el corte de `onGenerate`; el `finally` llama a `onEnterReady()` si se pidió otra | pantalla, «v2, la carga nueva en «Listo» y la anterior vuelve bien / con un error», con clics en «Generar» | «v2: generar se deshabilita mientras otra espera», «v2: lo pedido mientras otra espera no se genera», «v2: al volver la anterior no se genera lo pedido» |
| Un doble clic en «Reintentar» pide una vez | «Reintentar» llama a `onEnterReady()`, que oculta el error y el botón | pantalla, `reintentarConDobleClic` | «v2: un doble clic en Reintentar pide dos generaciones» |
| Regenerar sin enlaces | `shutil.copyfile(ruta, respaldo)` | `test_regenerar_funciona_en_un_disco_sin_enlaces` (tres regeneraciones con `os.link` fallando dan 200, el archivo tiene lo regenerado y cuenta 1) y `al_confirmar_sin_enlaces` en `test_regenerar_con_una_falla_deja_entero_lo_ya_entregado` | «el respaldo es un enlace y no una copia», «regenerar deja el archivo ya entregado» y el que ya estaba, «un commit fallido deja el archivo nuevo», con el ancla nueva |

`al_confirmar_sin_enlaces` no distingue nada por sí solo: con la copia, `os.link` ya no se llama. Lo dejo como la guarda que pediste («sin perder lo ya entregado si el commit falla»): si alguien vuelve a enlazar, ese caso prueba que el commit fallido no rompe lo entregado.

### Puertas

| Puerta | SHA | Salida |
|---|---|---|
| suite completa | `ca50916` | `4518 passed, 101 skipped, 3 xfailed, 101 warnings in 604.99s (0:10:04)`, salida 0 |
| sabotajes `cobro_corte1.sh`, con Postgres | `ca50916` | `sabotajes con falla: 0`, salida 0: 88 ROJO (57 de pytest, 25 de la pantalla, 6 del lock en Postgres), ningún VERDE ni ROTO; las tres bases «en verde» |
| pantalla `pantalla_cobro_corte1.js` | `ca50916` | `pantalla COBRO-CORTE-1: OK`, salida 0; también «BASE  | la pantalla en verde» dentro de los sabotajes |
| `test_cobro_corte1.py` | `ca50916` | `98 passed in 68.35s` |
| `/code-review high` | `633c383..ffb2aca` y `ffb2aca..6f186c5` | abajo |
| `/security-review` | `633c383..6f186c5`, producto | sin hallazgos de confianza alta |
| chequeo-6 | `d26c404..ca50916` | `avisos: 3`, con su porqué abajo (salida entera abajo) |

Todo se corrió sobre `ca50916`, el SHA que entrego, que ya trae tu limpieza.

`smoke_friccion.sh` y `ataque_aislamiento.sh`: no corridos. La pieza no toca permisos ni sesión: el guardado sigue validando en el servidor que el cliente sea del dueño.

### Rojo antes

Cada caso nuevo, con el producto de antes (`8295bb5`, o `178eb4a` para los dos hallazgos del adversario):

| caso | producto | rojo |
|---|---|---|
| «v2, generar», el catálogo | `8295bb5` | `FALLA: v2, generar: aprendió en «http://127.0.0.1:8871/api/catalog/proveedor_b_sa/productos», no en el de su proveedor`, `SALIDA=1` |
| «v2, generar y sacar el cliente» (entonces se llamaba «cambiar de cliente») | `8295bb5` | `FALLA: v2, generar y cambiar de cliente: la respuesta tardía no se guardó en el cliente de su carga con su operación (mandó «undefined»)` |
| «v2, la carga nueva en «Listo»…», con clics | `8295bb5` | `FALLA: no deja generar: ` (B trabada) |
| `test_regenerar_funciona_en_un_disco_sin_enlaces` | `8295bb5` | `E   assert [500, 500, 500] == [200, 200, 200]` |
| «v2, generar y elegir el cliente» | `178eb4a` | `FALLA: v2, generar y elegir el cliente: la respuesta tardía no se guardó en el cliente de su carga con su operación (mandó «undefined»)` |
| `reintentarConDobleClic` | `178eb4a` | `FALLA: reintentar con doble clic pidió generar, guardar, generar, guardar` |

Con el producto de `ca50916`, los seis dan `OK` o pasan.

**«v2, generar y pasar a otro cliente»** cubre un hueco de las pruebas, no del producto, así que no tiene rojo sobre un producto viejo. El rojo es con el producto actual y la precedencia invertida (`carga.clienteActivo || foto.cliente`):

- «sacar el cliente» seguía en `OK`: no veía el defecto.
- El caso nuevo da `FALLA: v2, generar y pasar a otro cliente: la respuesta tardía no se guardó en el cliente de su carga con su operación (mandó «undefined»)` y `SALIDA=1`.

Ése es su sabotaje en `cobro_corte1.sh`.

### Hallazgos de la autorrevisión

**Adversario: uno solo, Sonnet alto, sobre `178eb4a`**, porque es la vuelta de una devolución de plata. Reproduje lo que dijo antes de anotarlo.

| # | hallazgo | qué hice |
|---|---|---|
| A1 | dos clics en «Generar» piden dos generaciones | Con `dblclick` y con `Enter` se genera una vez y los totales quedan bien (`valor_total [1387.5]`). Sólo pasa con dos `click()` sincrónicos desde JS: la segunda generación sale y el guardado queda con los totales en cero (`valor_total [0]`). Un clic real lleva a «Listo», donde el botón ya no está. Va a riesgos; no hay código para esto. La segunda generación reusa la operación por su id y no cuenta. |
| A2 | un doble clic en «Reintentar» pide dos generaciones | reproducido (rojo arriba), arreglado en `3fe7ffd` |
| A3 | `os.link` con un `.anterior` que es el mismo archivo da `SameFileError` | no aplica: `os.link` sale en `178eb4a` y nunca se publicó |
| A4 | `al_confirmar_sin_enlaces` no distingue nada | cierto; queda como guarda, arriba |

**`/code-review high` sobre `633c383..ffb2aca`**

| # | hallazgo | qué hice |
|---|---|---|
| 1 | sin cliente al pedir, el guardado no toma el que se elige mientras espera (también lo vio el adversario) | reproducido (rojo arriba), arreglado en `3fe7ffd` |
| 2 y 3 | pedir otra vez la misma carga mientras espera la regenera | riesgo, abajo |
| 4 | `SameFileError` con `os.link` | no aplica (A3) |
| 5 | `pedidaMientrasOtra` | es la guarda pedida, con camino real y sabotaje |
| 6 a 10 | un caso que faltaba (6), uno falso (7) y tres cosméticos (8 a 10) | el 6, agregado; los demás, sin cambio |

**`/code-review high` sobre `ffb2aca..6f186c5`**

| # | hallazgo | qué hice |
|---|---|---|
| 1 | el mismo que el 2 y el 3 de la primera tanda | riesgo, abajo |
| 2 | sacar el cliente no distingue la precedencia del guardado | confirmado: con la precedencia invertida daba `OK`. Caso «pasar a otro cliente» y sabotaje en `d309be6` |
| 3 | en `reintentarConDobleClic`, una segunda generación que saliera después del guardado se escaparía del registro | Con el sabotaje aplicado corrí el caso 6 veces y las 6 dio `FALLA: reintentar con doble clic pidió …`: tres con `generar, guardar, generar, guardar` y tres con `generar, guardar, generar`. La segunda generación sale siempre antes de la respuesta del guardado; el comentario del caso lo dice. Sin cambio. |
| 4 | un comportamiento que es el pedido | sin cambio |
| 5 a 7 | `open().read()` en `tests/test_cobro_corte1.py:902`, `cargaNuevaV2` repetida, predicados duplicados en `anotar` | nits de pruebas, sin cambio |

### Riesgos

- **El doble clic sincrónico en «Generar»** (A1): dos pedidos al servidor y un guardado con los totales en cero. No hay doble cobro. Con clics reales no pasa.
- **Pedir otra vez la misma carga mientras espera** (code-review 2 y 3): se regenera la misma operación, que no cuenta otra vez. Con un 402, el modal sale dos veces.
- **B genera con lo que hay en pantalla al volver A.** Si el usuario cambió algo entre su clic y la vuelta de A, sale lo nuevo, que es lo que ve.
- **Siguen en la cola, decididos por vos:** el commit que tira error en Python y los candados de `delete_cliente`. El alert de v1 se fue con la v1.

### Un sabotaje en verde

El sabotaje que sacaba la guarda `carga === CDI.state`, puesta delante del error sin red de la generación anterior, daba VERDE. La causa es que el `finally` de esa generación llama a `onEnterReady()` en el mismo tick, y eso oculta el error antes de que se vea. La guarda no tenía efecto observable, así que `b4cb5f9` la saca y `86e2048` retira su sabotaje. Ninguno de los dos cambia el comportamiento, y por eso no llevan línea en el CHANGELOG.

### Lo que no salió limpio

- La suite pasó, pero trae un `PytestUnhandledThreadExceptionWarning` en `test_estudio1b.py::test_un_estudio_id_escrito_como_vacio_da_400_y_no_cae_al_perfil[/generate_maria/avisos-  ]`: un hilo de aiosqlite le contesta a un event loop ya cerrado (`RuntimeError: Event loop is closed`). Es un aviso, no una falla, y sale de un test que esta pieza no toca.
- La primera corrida de sabotajes sobre `d309be6` y la primera sobre `ca50916` terminaron en «BASE  | la pantalla ya está en rojo sin sabotaje» y `FALLA: la API no levantó`. La causa está en el arnés, no en el producto: `scripts/testing/con_pg16.sh` guarda el puerto de su Postgres en `PUERTO`, y si `PUERTO` venía exportado, `cobro_corte1.sh` recibe el puerto del Postgres y levanta la API encima de él. La corrida que vale (arriba) fija el puerto de la API dentro del comando que recibe `con_pg16.sh`.
- **Hallazgo fuera de la pieza:** el mismo choque afecta a `cobro_mp1.sh`, `cobro_mp2.sh` y `backup1a.sh` cuando quien llama a `con_pg16.sh` ya tiene `PUERTO` en el entorno; sin eso, la variable no pasa al comando y no hay choque. El arreglo es renombrar la variable interna de `con_pg16.sh` (por ejemplo, `PG_PUERTO`). No lo toqué: va con BACKUP-1a o a la cola, como decidas.
- Los sabotajes sobre `86e2048` los corté yo con el merge, por eso salieron con 143. No cuentan: valen los de `ca50916`.
- `/security-review` cubre `633c383..6f186c5`. De ahí al SHA entregado, el producto sólo saca una guarda de la UI (`b4cb5f9`) y el merge trae tu limpieza, que no revisé como seguridad.

### chequeo-6

Uso `d26c404` como base: `633c383` no es ancestro de tu rama, y desde ahí el rango contaría tu limpieza como mía. Lo que mide es lo que mi rama suma sobre la tuya: las tres vueltas de COBRO-CORTE-1 y COBRO-MP-2.

```
chequeo-6 d26c404..ca50916: avisos para mirar, no un veredicto
producto +351/−261
  AVISO producto suma 90 líneas netas: el informe dice por qué (§6: más de 20)
arnés +1541/−298
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11237 → 11293
  proyecto_maria/services/billing_service.py: 412 → 414
  proyecto_maria/static/v2/app_v2.js: 1190 → 1192
  proyecto_maria/static/v2/screens/clientes.js: 1984 → 1984
  proyecto_maria/static/v2/screens/finalize.js: 1357 → 1387
  AVISO creció una función de más de 150: proyecto_maria/static/v2/screens/finalize.js:9 <anónima> 1349 → 1379, 6 en su propio cuerpo (§6: lo nuevo va aparte)
  proyecto_maria/static/v2/screens/profile.js: 587 → 587
  proyecto_maria/static/v2/screens/upload.js: 718 → 718
  AVISO función nueva de 67 líneas: scripts/testing/pantalla_cobro_corte1.js:33 casosTardios (§6: ~60)
avisos: 3
```

- **90 líneas netas de producto:** es lo acumulado de las tres vueltas de COBRO-CORTE-1 y de COBRO-MP-2, que todavía no están en tu rama. Esta vuelta sola es `+23/−21`.
- **`finalize.js:9 <anónima>`:** es el IIFE que envuelve el archivo entero, no una función de lógica. Lo nuevo está en funciones propias dentro de él.
- **`casosTardios`, 67 líneas:** es una lista de casos escritos como datos (§6, «un caso por causa»), y se achicó al sacar la v1. Partirla separaría casos que comparten `cargaNuevaV2` y `pedirV2`.

### Para reproducir

```bash
git checkout ca50916
# 1. todo «passed»
DATABASE_URL=sqlite+aiosqlite:///./t.db GEMINI_API_KEY=test-key ENVIRONMENT=test python -m pytest -q --no-cov tests/test_cobro_corte1.py
# 2. todo ROJO y «sabotajes con falla: 0»; sin PG, la parte de Postgres dice «NO CORRIDO»
PY=$(which python) PG=postgresql://<usuario>@127.0.0.1:<puerto> scripts/testing/sabotajes/cobro_corte1.sh ca50916
# 3. «avisos: 3», los de arriba
python docs/pm/herramientas/chequeo-6.py d26c404 ca50916
```

### Archivos de producto tocados

- `proyecto_maria/main.py` (`_escribir_y_confirmar`)
- `proyecto_maria/static/v2/screens/finalize.js`
- `CHANGELOG.md`

---

/compact conservar: Dev 1, rama claude/dev-tecnica. COBRO-CORTE-1 (vuelta 3) entregada en ca50916, sobre tu merge d26c404 (informe en el commit de arriba), sin D. Sigue COBRO-MP-2 (D62), empezando por los rojos de sus sabotajes. Nada se publica sin el «dale» de Emi; nunca main.
