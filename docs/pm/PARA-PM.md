# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## PA-1 y D3: entregadas

**Resultado: las dos terminadas, para revisar.**

- **PA-1:** cambian 7 textos de la pantalla v2. Corregí la premisa con evidencia:
  la memoria del cliente y el catálogo del proveedor guardan la NCM de 8
  dígitos, no la posición de 11 con su letra, así que siguen diciendo «NCM».
- **D3 = (a), en `clientes.js`:** editar un cliente no borra una fecha de
  inicio que el campo de fecha no puede mostrar. Sumé un arreglo chico que
  salió del adversario: una fecha tipeada a medias ya no se guarda callada.
  Es un supuesto reversible (abajo).
- **Tenías razón con el matiz de D3:** la fecha no se borraba «sin aviso», porque
  salía «Faltan para el MARIA: inicio de actividad». Lo que el aviso no decía
  era que la fecha guardada se acababa de perder.

| Qué | SHA |
|---|---|
| Base | `c402bcb` (PA-1); `bdd5fb3` (D3, tu merge con los veredictos) |
| PA-1, producto | `489daf4` + `c7e4c3a` (reversión que salió de la autorrevisión) |
| PA-1, pruebas | `c0103db`, `03ef9b4`, `d1f7833` |
| D3, producto | `26797f8`, `d8e084c` (fecha a medias) |
| D3, pruebas | `5d3754c`, `ce84023`, `a114465` |
| Puertas corridas sobre | `a114465`. Después vino `fcfbdb9`, el merge de tu `8b45207`, que sólo toca `docs/pm/NOW.md` |
| Informe | este commit |

Archivos de producto que toqué: `proyecto_maria/templates/dashboard_v2.html`,
`proyecto_maria/static/v2/screens/ncm.js` (PA-1),
`proyecto_maria/static/v2/screens/clientes.js` (D3) y `CHANGELOG.md`.

### Decisiones

D1 y D3 ya están decididas: (a) las dos. Quedan estas:

- **D4. ¿El texto «Posición SIM», que ya aparece en 9 líneas de la pantalla v2,
  se unifica como «Posición arancelaria (PA SIM)»?**
  (a) sí, en una pieza aparte de textos;
  (b) dejarlo: «Posición SIM» ya dice lo correcto.
  **Recomiendo (b).** No es falso y la tarea no lo pide. Si Emi quiere un
  único nombre, es (a).
- **D5. ¿La landing y la cotización pública pasan a «PA SIM»?**
  `landing.html:130` (paso «3 NCM» de la demo) y `:139`; `public_quote.html:267`
  (`<span>NCM</span>` + `i.pieza`, que es lo que ve el cliente final).
  (a) sí la demo de la landing (copia el progreso, que ahora dice «3 PA SIM»);
  la cotización pública no, porque `pieza` puede ser de 8 dígitos si no se
  validó;
  (b) las dos;
  (c) ninguna: la tarea dice «pantallas» de la aplicación.
  **Recomiendo (a).** La demo de la landing copia una pantalla que ya cambió.
  La cotización muestra un dato que no siempre es la posición completa.
  No toqué ninguna de las dos.
- **D6. `enrich.js:207`, encabezado `<th>NCM</th>` del detalle por ítem.**
  Muestra `it.pieza || it.ncm`, que puede ser de 8 o de 11 dígitos según el
  ítem.
  (a) dejar «NCM»;
  (b) cambiarlo a un nombre neutro, por ejemplo «Posición».
  **Recomiendo (a)** mientras el dato pueda ser de 8 dígitos. No lo toqué.
- **D7. Un alta por la API con `"fecha_inic_activ": null` guarda el texto
  «None»** (`main.py:6287`, `str(...)` de un None). No lo agregó D3, pero D3 lo
  vuelve peor. Antes, editar ese cliente desde la pantalla lo curaba: el
  campo no muestra «None» y se mandaba vacío. Ahora «None» se conserva, el
  aviso no lo pide y el detalle muestra «None». El TXT saldría `MCPL=None`
  (`core/maria_generator.py:804`, no lo toqué). La pantalla no manda null: sólo
  pasa por la API o con datos viejos.
  (a) una pieza chica de API: `create_cliente` guarda `""` cuando llega null,
  y un script limpia los «None» que haya (eso es migración de datos: revisión
  fuerte);
  (b) tratar «None» como vacío en `clientes.js`;
  (c) dejarlo.
  **Recomiendo (a).** La causa está en la API, y `migration_service._field_text`
  ya normaliza así. (b) es un parche que deja el TXT igual de mal. Lo dejé
  afuera porque la tarea decía no tocar la API.

### D3: qué hace

`clientes.js`, `fillFormFromCliente` y `submitForm`:

- Si lo guardado no entra en el campo de fecha (no es AAAA-MM-DD, o es una
  fecha imposible como `2015-02-30`) y el campo queda vacío, al guardar **no se
  manda**. El PUT (`main.py:6364`) conserva lo que hay si la clave falta.
- Si la fecha se conserva, el aviso no dice que falta.
- **Una fecha cargada reemplaza a la vieja.** Borrar a mano una fecha ISO sigue
  andando.
- No toqué la API ni el TXT.
- **Supuesto (lo amplié yo):** también conservo las ISO imposibles
  (`2015-02-30`), porque el navegador tampoco las muestra. La regla es «lo que
  el campo no puede mostrar», no una expresión regular. Hay un sabotaje que
  prueba la regex y da rojo en «Imposible».
- **Supuesto reversible (`d8e084c`):** si la fecha está tipeada a medias, el
  navegador la da como vacía. El formulario no guarda y dice
  «La fecha de inicio de actividad está incompleta: completala o borrala.».
  Sin esto, con D3 la fecha vieja se conservaba aunque el usuario la estuviera
  cambiando; y con una fecha ISO pasaba lo de antes de D3: se borraba. Si no lo
  querés, se revierte `d8e084c` solo y su caso en `a114465`.

Prueba de pantalla (`scripts/testing/pantalla_cliente1.js`). Cubre las
familias que pediste: null, `""`, `01/03/2015`, otro texto no ISO (`mar-2015`)
e ISO. Suma reemplazar, borrar, la ISO imposible, la fecha a medias con fecha
oculta y con ISO, y que lo recordado no pase al alta siguiente. El control
del alta ahora exige que el último caso deje una fecha conservada: antes
dependía del orden de los casos (lo encontró `/code-review`).

### Puertas

| Puerta | Resultado |
|---|---|
| PA-1, rojo antes: la prueba sobre la base `c402bcb` | `7 failed, 18 passed`; primera línea `E   AssertionError: templates/dashboard_v2.html sigue diciendo '<span class="num">3</span> NCM</div>'` |
| PA-1, rojo antes de la reversión: la prueba nueva sobre el producto de `03ef9b4` | `8 failed, 17 passed`; primera línea `E   AssertionError: templates/dashboard_v2.html ya no dice 'recuerda los NCM y orígenes confirmados' (0 de 1 veces)` |
| D3, rojo antes: la prueba sobre `bdd5fb3` | `FALLA: Barras: después de editar, la fecha es null y tenía que ser "01/03/2015"` |
| Fecha a medias, rojo antes: la prueba sobre `ce84023` | `FALLA: A medias oculta: una fecha a medias se guardó sin decir nada` |
| Sabotajes `scripts/testing/sabotajes/pa1.sh a114465` | 27 `ROJO`, `sabotajes sin rojo: 0`, exit 0 |
| Sabotajes `scripts/testing/sabotajes/cliente1.sh a114465` | 23 `ROJO`: 14 de CLIENTE-1, 6 de D3 y 3 de la fecha a medias. `sabotajes sin rojo: 0`, exit 0 |
| Suite completa, worktree limpio en `a114465`, `--no-cov --timeout=120` | `1782 passed, 102 skipped, 2 xfailed, 26 warnings in 169.48s (0:02:49)`, exit 0 |
| e2e de la CI (`scripts/testing/e2e_maria.sh`) sobre `a114465` | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.`, exit 0 |
| **e2e sobre `d1f7833`: un rojo intermitente** | primera corrida: `Error: Node is either not clickable or not an Element` en `config/e2e_maria.js:202` (`verifyBlockingErrorsAndNonBlockingWarnings`), exit 1; falla el `page.click('#validatingRerun')` de la pantalla Validar. La segunda, sin cambios, dio OK, exit 0, y también dieron OK las corridas sobre `03ef9b4` y `a114465`. PA-1 cambia en esa pantalla el texto de «Volver a PA SIM», no `#validatingRerun` ni la estructura. **No lo diagnostiqué:** parece que el click llega antes de que el botón se pueda clickear, pero no lo probé. Te lo dejo anotado; no lo escondo |
| `/code-review high` y adversario Sonnet alto, D3 | sobre `bdd5fb3..5d3754c` (tabla abajo). No los volví a correr sobre `d8e084c` |
| `/code-review high` y adversario Sonnet alto, PA-1 | sobre `c402bcb..03ef9b4`; la reversión es lo que encontraron |
| `/security-review` | no lo corrí. PA-1 son textos. D3 toca datos del cliente sólo en el front: no cambia la API, la sesión ni los permisos |

Las 32 líneas `Task was destroyed but it is pending!` de la suite salen
iguales en todas mis corridas, también en las de antes de PA-1: es ruido
viejo y no es de esta pieza.

### Hallazgos de la autorrevisión de D3

| Hallazgo | Quién (modelo, esfuerzo) | Qué pasó |
|---|---|---|
| Un alta por la API con null guarda «None»; con D3 queda conservado y sin aviso | los dos (`/code-review high` y adversario Sonnet alto, que lo reprodujo) | fuera de D3 (es la API): va a **D7** |
| Una fecha tipeada a medias se descartaba callada y conservaba la vieja | adversario Sonnet alto, reproducido | arreglado en `d8e084c`, con su rojo antes y 3 sabotajes |
| El control del alta dependía de que el último caso fuera «Imposible» | `/code-review` | arreglado en `ce84023` |
| El aviso no advierte si lo conservado es basura (`mar-2015`) | `/code-review` | es lo que pediste («si se conserva, no dice que falta»); queda como riesgo |
| Una fecha oculta no se puede ver ni borrar desde el formulario | `/code-review` | riesgo ya aceptado por vos; anotado en el CHANGELOG |
| Un doble Enter manda 2 PUT | adversario | no pierde nada y ya pasaba antes; no se hace nada |
| Dependencia del DOM; caché de la lista | `/code-review` | no se reprodujo: la prueba verifica el valor que queda guardado |

Ejes del adversario sin hallazgo: el PUT conserva si falta la clave; todos
los caminos de abrir el formulario pasan por `resetFormFields`; no se arrastra
nada de un cliente a otro; el alta queda cubierta.

#### Hallazgos de la autorrevisión de PA-1

| Hallazgo | Quién (modelo, esfuerzo) | Qué pasó |
|---|---|---|
| 8 textos decían «PA SIM» sobre datos de 8 dígitos (memoria, sugerencias, catálogo) | los dos (subagente Sonnet alto y `/code-review high`) | verificado en el código (`ncm_para_historial`, `guardar-uso`, `upload.js:585`); revertidos en `c7e4c3a`; ahora la prueba exige que digan «NCM», con sabotaje |
| Concordancias rotas («Revisalos», «te lo sugerimos») | `/code-review` | desaparecen con la reversión |
| El CHANGELOG decía «catálogo del cliente» y le faltaba el prefijo | `/code-review` | corregido |
| `QUEDAN` buscaba con `in`: no veía si cambiaba una de varias apariciones | lo encontró el sabotaje propio | ahora cuenta las veces (`03ef9b4`) |
| La prueba es una lista de textos (CLAUDE.md §2) | `/code-review` | queda así a propósito: la tarea es sobre textos puntuales. La lista exige que cada texto aparezca la cantidad exacta de veces, y cada caso tiene su sabotaje |
| La landing y la cotización pública dicen «NCM» | los dos | va a **D5** |
| `enrich.js:207`, `<th>NCM</th>` con dato de 8 u 11 dígitos | subagente | va a **D6** |

#### Riesgos que quedan

- **D3:** una fecha no ISO no se puede borrar desde el formulario (aceptado).
  El aviso no advierte si lo conservado no es una fecha. Lo que haya guardado
  en otro formato llega igual al TXT. El primero y el último ya estaban; el
  silencio del aviso sale de D3 y es lo que pediste.
- **`finalize`, «NCMs distintos», cuenta prefijos de 4 dígitos**, no
  posiciones. Ya pasaba antes de PA-1. Baja.
- **`catalogo.js` (~290): `CDI.maskNcm` con un string podría lanzar un
  TypeError**, según el subagente. No lo verifiqué; ya estaba antes. Baja.
- Los mockups y el `dashboard.html` v1 siguen diciendo «NCM»: quedaron
  fuera de alcance.
- Los eventos de analítica (`ncm_batch_ncm_applied`, `ncm_agrupar`) y los
  nombres internos no cambian: no son textos de pantalla.

### Comandos para reproducir

```sh
PY=<venv>/bin/python scripts/testing/sabotajes/pa1.sh a114465   # 27 «ROJO», «sabotajes sin rojo: 0»
PY=<venv>/bin/python CHROMIUM=/opt/pw-browsers/chromium PUERTO=8861 \
  scripts/testing/sabotajes/cliente1.sh a114465                   # 23 «ROJO», «sabotajes sin rojo: 0»
<venv>/bin/python -m pytest -q --no-cov tests/test_pa1_textos.py # 25 passed
# el rojo de D3 lo reproduce el sabotaje «la fecha que el campo no muestra se vuelve a mandar vacía»
# de cliente1.sh: deshace el arreglo y da «FALLA: Barras: …», el mismo rojo que sobre bdd5fb3
```

Datos reales: no entró nada de la reunión del 24/10. Los clientes, CUIT y
fechas de las pruebas son inventados.

### PA-1: qué cambió (7 textos)

| Dónde | Antes | Ahora |
|---|---|---|
| Progreso, paso 3 | `3 NCM` | `3 PA SIM` |
| Revisión, botón | «Continuar a NCM» | «Continuar a PA SIM» |
| Validar, botón | «Volver a NCM» | «Volver a PA SIM» |
| Asistente (lector de pantalla) | `aria-label="Asistente NCM"` | «Asistente de posición arancelaria (PA SIM)» |
| Aviso de deshacer al aplicar en lote | «NCM 8471.30.12.000A a 3 items» | «PA SIM …» |
| Aviso de deshacer al agrupar | «NCM … · 3 ítems → 1 unidad clasificatoria» | «PA SIM …» |
| Aviso de datos VUCE viejos (`title`) | «Refrescar desde el asistente NCM» | «… desde el asistente de posición arancelaria» |

Los dos avisos de deshacer muestran la posición validada. En `ncm.js:536`,
`formatted` sale de `normalizeBatchNcm`, que exige 11 dígitos y la DC. En
`ncm.js:1086`, `result.ncm` sale de `applyNcmAndGroup`, que exige la SIM
completa.

**Quedan «NCM» (hablan de los 8 dígitos)**, y la prueba cuenta cuántas veces
aparece cada uno:
- la memoria del cliente y sus sugerencias. `services/client_memory.py`,
  `ncm_para_historial`, guarda `digitos[:8]`; `/api/ncm/guardar-uso`
  (`main.py:8523`) guarda `_ncm_suggestion_key`, de 8 dígitos;
- el catálogo del proveedor, cuyo autocompletado (`upload.js:585`) pone esos
  8 dígitos;
- la consulta a VUCE, que es de 8 dígitos;
- la calculadora, las notas del capítulo, la planilla maestra, «NCM 8 + SIM
  3 + DC» y los mensajes de largo.

### ESTUDIO-1: lo que leí para coordinar (no toqué código)

- **Hoy:** el CUIT del despachante es uno por usuario, `users.cuit`
  (`database/models.py:31`). Al generar, `main.py:4327-4341` toma el de la
  operación (`request.cuit_agr`) y, si falta, el del perfil. Después valida
  los 11 dígitos. Si no hay ninguno, el TXT sale sin `CDDTAGR` y no avisa.
- **La costura con MARIA-7 punto 3 es ese mismo bloque.** ESTUDIO-1 cambia
  **de dónde sale** el CUIT: el estudio elegido en la operación, con el
  perfil como respaldo. El punto 3 cambia **qué pasa si no hay**: error en
  lugar de omitir. Propongo dividirlo así:
  - la Dev MARIA agrega el error **después** del bloque, sobre
    `effective_cuit_agr` vacío;
  - yo cambio sólo cómo se resuelve, **dentro** del bloque.
  - El texto del error («dónde cargarlo») depende de ESTUDIO-1: hoy diría
    «en tu perfil» y después, «en Estudios».
  - Quien entregue segunda hace el merge.
- **Necesito que me escribas la tarea en `PARA-DEV.md`.** Hoy ESTUDIO-1 es
  una sola línea del roadmap. Faltan definir tres cosas:
  1. si los estudios son por usuario o compartidos;
  2. dónde se elige el estudio en la operación;
  3. si el `users.cuit` actual pasa a ser el estudio por omisión. Es una
     migración de datos, así que lleva revisión fuerte.

  No arranco el código hasta tener esa tarea. Mientras tanto, si me la
  marcás, sigo con EXCEL-3b, que ya está definida.

Última vuelta: 2026-10-24 20:10 UTC

/compact conservar: Soy la Dev técnica (Dev 1) de CDI, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica (nunca main), rutina trig_011UpBfwEu9TUzoNUrviqoP5 min 15; aviso a la PM principal session_01B7FVQspcEHF7PqNv797wNM con send_message priority next empezando «Dev técnica:». PA-1 + D3 entregadas juntas (puertas sobre a114465; PA-1 producto 489daf4+c7e4c3a; D3 producto 26797f8+d8e084c, pruebas 5d3754c+ce84023+a114465). Abiertas para la PM: D4 (unificar «Posición SIM»), D5 (landing y cotización pública), D6 (enrich.js:207), D7 («None» por POST null en create_cliente; recomiendo (a) pieza de API). D1 y D3 decididas (a). ESTUDIO-1 espera que la PM escriba la tarea y coordine con MARIA-7 punto 3; propuse la costura main.py:4327-4341 (yo resuelvo de dónde sale el CUIT; MARIA el error si falta). Mientras, EXCEL-3b si la PM lo marca. Reglas de Emi: sólo me piden la PM o Emi; nada se publica sin su «dale» para el SHA; nunca main; sin secretos ni datos reales; no tocar maria_generator.py ni el canal/rama de la Dev MARIA; subagentes hasta alto, sin Fable; esfuerzo medio.
