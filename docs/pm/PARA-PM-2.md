# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ORIGEN-2 sobre `0d7401ed` (2026-11-20 01:50 UTC)

**Resultado.** Los seis puntos se cumplen en `0d7401ed`, contra la base `4fe296d4`.
- `producto +44/−42`. chequeo-6 da dos `AVISO`. Abajo va su salida entera, con el porqué de cada uno.
- Es migración: corrí los sabotajes con Postgres descartable, `/code-review` alto, un adversario Opus
  alto y `/security-review`.
- Antes de publicar hace falta la copia de la base que pediste. No la hice: es producción.
- **Lo que decidís vos:**
  - **D276.** Un alta sin origen se guarda «CN». Viene del modelo y ya era así.
  - **D277.** Un recorte viejo que es la sigla de otro país se ve como ese país: «EST» se ve
    «440 · ESTONIA».
  - Los dos van en «Decisiones», abajo.

## Qué cambió

**Servidor** (`main.py`, `models.py`).
- El alta y la edición pasan el origen por `origen_para_catalogo`, el validador del catálogo, dentro
  de `_textos_de_arriba_guardables`. Las dos rutas usan esa función, así que el chequeo está una vez.
- Un país se guarda como se escribió: nombre, código o etiqueta. Los espacios se juntan y una sigla
  de dos letras pasa a mayúsculas.
- Lo que no es un país da 400 con «No reconozco el origen «X»: usá el nombre o el código del país.» y
  no toca la fila.
- Vacío o `null`: la edición lo deja vacío y el alta toma «CN» del modelo (D276).
- La columna pasa a `text`:
  - el modelo;
  - las columnas que suma `_migrate_sync_clients_columns`;
  - la reconstrucción de SQLite;
  - en Postgres, `_migrate_catalogo_sin_tope`, que ya lleva a `text` las columnas del catálogo. Suma
    `("clients", ("default_origin",))` con el mismo `lock_timeout` y el mismo reintento.

**Pantalla** (`clientes.js`, `app_v2.css`, `dashboard_v2.html`).
- El selector de diez siglas pasa a un campo de texto con la tabla entera (308 países) en un
  `datalist`. Va en su propio renglón (supuesto 2).
- Al abrir, el campo muestra lo guardado con su `etiqueta`. Si no se toca, el origen no se manda y
  queda como estaba: «CN» no se reescribe «310 · CHINA».
- La comparación es con lo que muestra el campo, no con lo guardado: el campo pierde los saltos de
  línea. Un «A↵B» de antes se mandaba «AB» y daba 400 al guardar otro dato. Lo encontró
  `/code-review`.
- La etiqueta de arriba y «Origen habitual» usan `CDI.paisesMaria.etiqueta`, escapadas.
- La etiqueta de arriba:
  - va sin mayúsculas forzadas y en un renglón;
  - si no entra, se corta con «…» y el código queda entero;
  - el contenedor de las etiquetas puede bajar la moneda a otro renglón y no pasa del ancho de la
    ficha.

## Los seis puntos

1. **Nombre o código, validado como en el catálogo; lo que no es país dice por qué.**
   - Lo cubren `tests/test_origen2.py`, por alta y por edición:
     - «BRASIL», «Brasil», «Holanda», «países  bajos» y dos etiquetas (una de 54 caracteres) se
       guardan enteros;
     - «310», «0434», «ARG», «cn» y «  br » también se guardan;
     - «Narnia», «tierra media», «CHI», «HOL», «XX» y «<b>x</b>» dan 400 con el mensaje exacto, y no
       se crea ni se cambia nada.
   - En la pantalla, `escribir` de `pantalla_origen2.js`:
     - «Narnia» muestra el mensaje en el formulario, que queda abierto, y «CN» no cambia;
     - «Brasil» se guarda «Brasil» y se ve «203 · BRASIL»;
     - el alta con «Países Bajos» se ve «423 · PAISES BAJOS».
   - Sobre la base, el caso da «2 failed, 1 passed». Pasa el de editar otro dato, porque la base
     tampoco mandaba el origen sin tocarlo; ese caso cuida el código nuevo (sabotaje 2d).
2. **La ficha con código y nombre; un renglón; sin mayúsculas; capturas.**
   - `fichaDeCadaPais` guarda cada uno de los 308 códigos. En cada ancho de disposición (1280, 841,
     721, 641, 601, 561, 521, 481 y 320 px) mira:
     - la etiqueta de arriba en un renglón y adentro de la ficha, sin mayúsculas forzadas;
     - si se corta, con «…» y el código entero;
     - los seis orígenes corrientes (Emiratos, China, Países Bajos, Estados Unidos, Japón y Vietnam)
       enteros desde 400 px y su «Origen habitual» en un renglón.
   - `guardarOtroDato`: «CN», «Holanda», «CHI», «HOL», «A↵B», «tierra media» y un `<img onerror>`,
     sembrados en la base, se ven con su etiqueta o como quedaron. El formulario los muestra igual,
     guardar las notas no los toca y el HTML no corre.
   - `campoDelFormulario`: el campo ofrece 308 países; los corrientes entran enteros de 1280 a 481 px
     y el campo queda adentro del formulario a todos los anchos.
   - Capturas a 960 y 1280: `docs/pm/capturas/origen-2-960.png` y `origen-2-1280.png`.
3. **Migración en Postgres descartable** (`scripts/testing/origen2_postgres.py`, con
   `con_pg16.sh`).
   - Siembra con el esquema de `4fe296d4` (`character varying(3)`) cinco clientes: «CN», NULL, «»,
     «CHI» y «HOL».
   - Arranca dos veces la app de esta rama. En cada arranque, la columna es `text` y los cinco quedan
     iguales.
   - Después, por la API:
     - la edición guarda «BRASIL» entero;
     - el alta guarda entera la etiqueta de 54 caracteres, que en `VARCHAR(3)` Postgres rechaza;
     - «Narnia» da 400 sin tocar la fila;
     - editar otro dato deja «CHI».
4. **Negativo en el mismo SHA con el recorte de vuelta.** El sabotaje 0 de `origen2.sh` pone de vuelta
   las líneas de la base, palabra por palabra:
   - en Postgres, el alta y la edición dan rojo;
   - en los casos, alta y edición dan «AssertionError: BRASIL».
5. **`e2e_maria.sh` verde sobre `0d7401ed`.** Abajo, con el pytest entero.
6. **Afuera.** La calculadora y `calculadora.js:112`, en riesgos. No toqué código.

## Commits

| commit | qué |
|---|---|
| `b6c22ac9` fix | el origen se valida y se guarda entero; la columna a text; campo con la tabla; la ficha con su etiqueta; CHANGELOG |
| `6e46e747` test | `test_origen2.py`, `origen2_postgres.py`, `pantalla_origen2.js`, `sabotajes/origen2.sh` |
| `55060c5a` fix | el formulario compara con lo que muestra el campo; sale un `max-width` repetido |
| `fe3c33e1` test | «A↵B» en lo guardado; las anclas de los sabotajes en la línea de hoy |
| `b2b9cc29` docs | las capturas a 960 y 1280 |
| `0d7401ed` test | la frase de un sabotaje (abajo, «Un rojo con otra frase»). **Lo que se entrega** |
| `7dae3c2d` merge | tu rama hasta `b73d96ec` (el acta) |
| informe | el commit siguiente |

## Pruebas, sobre `0d7401ed`

| qué | resultado |
|---|---|
| `sabotajes/origen2.sh 0d7401ed`, con Postgres 16 descartable | BASE «3 passed», «OK: pantalla del origen habitual», «Postgres: fallas: 0»; 25 «ROJO», «sabotajes sin rojo: 0», rc=0, de 01:25:46 a 01:46:41 UTC (abajo, entera) |
| pytest entero, desde un worktree limpio | «6231 passed, 110 skipped, 3 xfailed, 117 warnings in 1266.57s (0:21:06)», rc=0; 0 «dejó». Hay 11 avisos «Event loop is closed» de aiosqlite, en tests de cobro, sesión, org y entradas: ninguno es de esta pieza, y es el aviso que ya conocés |
| `e2e_maria.sh`, en el mismo worktree | «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.», rc=0, worktree sin cambios |
| `origen2_postgres.py` solo | 8 «OK», «fallas: 0» (salida en el punto 3) |
| `tests/test_origen2.py` | «3 passed»; en la base `4fe296d4`, «2 failed, 1 passed» (alta y edición) |
| pantalla con Inter | «OK ficha: 308 países con código y nombre, la etiqueta en un renglón y todo adentro a 1280, 841, 721, 641, 601, 561, 521, 481, 320 px»; «OK guardar otro dato: «CN», «Holanda», «CHI», «HOL», «A↵B», «tierra media», «<img src=x onerror="window.__xss=1">» se ven con su etiqueta o como se guardaron, y quedan»; «OK formulario: 308 países para elegir; los corrientes, enteros en el campo a 1280, 841, 721, 641, 601, 561, 521, 481 px y adentro a 1280, 841, 721, 641, 601, 561, 521, 481, 320 px»; «OK formulario: «Narnia» dice por qué y no guarda; «Brasil» se guarda así y se ve «203 · BRASIL»»; «OK formulario: el alta con «Países Bajos» se guarda así y se ve «423 · PAISES BAJOS»» |
| pantalla con Liberation Sans (métricas de Arial) | las mismas cinco líneas «OK» y «OK: pantalla del origen habitual», rc=0, sobre `7dae3c2d` (el mismo producto) |
| chequeo-6 `4fe296d4 0d7401ed` | abajo, entera |

La pantalla con Inter y las capturas corrieron sobre `fe3c33e1`. `0d7401ed` sólo cambia una frase de
`sabotajes/origen2.sh`, así que el producto y la pantalla son los mismos. Las capturas muestran «Origen 203 · BRASIL»
en un renglón y sin mayúsculas forzadas.

**Un rojo con otra frase.** La primera corrida de los sabotajes fue sobre `fe3c33e1` y dio «sabotajes
sin rojo: 1», con 24 «ROJO» y esta línea:
```
ROJO? | lo que no entra se dibuja afuera: rojo (salida 1), pero sin «lo que no entra en la etiqueta se sale o se corta sin «…»»
FALLA: «109» a 320 px: el origen se sale de la ficha
```
- El rojo era bueno; la frase esperada, no. Sin `overflow: hidden`, la etiqueta es un ítem flex que
  crece al ancho de su texto y sale de la ficha, así que salta antes el chequeo de «se sale de la ficha».
- Antes lo frenaba el `max-width` de la etiqueta, que saqué en `55060c5a`.
- `0d7401ed` cambia sólo esa frase. Corté las puertas, que iban sobre `fe3c33e1`, y las relancé todas
  sobre `0d7401ed`.

**Salida de los sabotajes sobre `0d7401ed`, entera:**
```
BASE  | casos: ======================== 3 passed, 5 warnings in 3.46s =========================
BASE  | pantalla: OK: pantalla del origen habitual
BASE  | Postgres: fallas: 0
ROJO  | el alta recorta a 3: «FALLA | el alta guarda entero un origen de 54»
ROJO  | la edición recorta a 3: «FALLA | la edición guarda «BRASIL» entero»
ROJO  | el alta recorta a 3: «AssertionError: BRASIL», 1 casos
ROJO  | la edición recorta a 3: «AssertionError: BRASIL», 1 casos
ROJO  | la migración no toca el cliente: «FALLA | primer arranque: el origen es text»
ROJO  | lo que no es un país se guarda: «AssertionError: Narnia», 2 casos
ROJO  | lo escrito se guarda sin normalizar: «AssertionError: países  bajos», 2 casos
ROJO  | lo vacío no pasa por el validador: «AssertionError», 2 casos
ROJO  | guardar otro dato borra el origen: «AssertionError», 1 casos
ROJO  | la etiqueta de arriba muestra lo guardado: «FALLA: la ficha muestra «Origen 101» y «101 · BURKINA FASO»»
ROJO  | la etiqueta de arriba muestra HTML: «no «<img src=x»
ROJO  | «Origen habitual» muestra lo guardado: «FALLA: la ficha muestra «Origen 101 · BURKINA FASO» y «101»»
ROJO  | la etiqueta de arriba en mayúsculas: «la ficha fuerza las letras del origen»
ROJO  | la etiqueta de arriba baja de renglón: «la etiqueta del origen baja de renglón»
ROJO  | lo que no entra se dibuja afuera: «el origen se sale de la ficha»
ROJO  | lo que no entra se corta sin «…»: «lo que no entra en la etiqueta se sale o se corta sin «…»»
ROJO  | las etiquetas de arriba crecen fuera de la ficha: «el origen se sale de la ficha»
ROJO  | la moneda le quita lugar al origen: «no entra entera en la etiqueta»
ROJO  | el formulario manda el origen aunque no se toque: «FALLA: guardar otro dato reescribe «CN» → «310 · CHINA»»
ROJO  | el formulario muestra lo guardado: «FALLA: el formulario muestra «CN» para «CN»»
ROJO  | el formulario compara con lo guardado y no con lo que muestra: «FALLA: guardar otro dato con «A↵B» guardado da 400»
ROJO  | el formulario no ofrece los países: «FALLA: el formulario ofrece 0 países»
ROJO  | el campo no está unido a la lista: «FALLA: el formulario ofrece 0 países»
ROJO  | el origen comparte renglón con la moneda: «FALLA: «331 · EMIRATOS ARABES,UNID» no entra en el campo de origen a 1280 px»
sabotajes sin rojo: 0
```

## Decisiones

- **D276. Un alta sin origen se guarda «CN».**
  - Viene del `default="CN"` del modelo y ya era así en la base.
  - La pantalla muestra el campo vacío y la ficha después dice «Origen 310 · CHINA».
  - Lo señalaron `/code-review` y el adversario. Choca con «no se guarda en silencio» de tu punto 1.
  - Opciones:
    - **(a) dejarlo.** Es mi recomendación para esta pieza: no es un recorte;
    - **(b) que el alta guarde vacío.** Es una línea, pero cambia lo que ya esperan los clientes que se
      dan de alta sin origen;
    - **(c) que el formulario de alta muestre «310 · CHINA»** de entrada, para que se vea antes de
      guardar.
- **D277. Un recorte viejo que es la sigla de otro país se ve como ese país.**
  - La fila no cambia (punto 3). Lo que cambia es que la ficha ahora le pone código y nombre, y el
    servidor lo acepta como válido.
  - Ejemplos: «Estados Unidos» recortado queda «EST» y se ve «440 · ESTONIA»; «Austria» → «AUS» →
    «501 · AUSTRALIA»; «Argelia» → «ARG» → «200 · ARGENTINA».
  - De los 308 nombres de la tabla recortados a 3, 36 se ven como otro país (uno es Turquía con su
    otro código), 66 como el suyo y 206 como quedaron («CHI», «HOL»). Lo saqué con
    `CDI.paisesMaria` sobre la tabla.
  - No hay forma de distinguir un «EST» recortado de un «EST» escrito.
  - Para que haya filas así, alguien tuvo que mandar un nombre a la API: el selector viejo mandaba
    siglas de dos letras, y la importación no escribe este campo (lo revisó el adversario). Así que
    espero que no haya ninguna.
  - Para saberlo hay que mirar producción, y yo no la toco. La consulta de sólo lectura, probada en
    Postgres descartable (con «EST» dos veces da `[('EST', 2)]`):
    ```sql
    SELECT default_origin, count(*) FROM clients WHERE length(default_origin) = 3 GROUP BY 1 ORDER BY 1;
    ```
  - Opciones:
    - **(a) dejarlo como riesgo.** Es mi recomendación si la consulta da vacío o sólo siglas de tres
      letras escritas así;
    - **(b) si aparecen recortes, una pieza aparte** que los corrija con el dato real.

## Supuestos

1. El selector pasa a un campo de texto con `datalist`. Es la forma en que se escribe «el nombre o el
   código», y las 308 opciones pasan la validación del servidor.
2. El origen y la moneda iban en un renglón de dos columnas. Ahí el campo era angosto: a 1280 px no
   entraban 65 etiquetas, entre ellas Emiratos y Japón. Ahora cada uno va en su renglón. Lo cuida el
   sabotaje 5f.
3. «Origen habitual» baja de renglón con un nombre largo, como los demás datos de la grilla, y se lee
   entero. Los seis corrientes quedan en un renglón.

## Riesgos

1. **La calculadora** (`/api/ncm/calcular`) recorta el origen a 3: con «BRASIL» dejaría de contar como
   Mercosur. Su pantalla ofrece sólo siglas de dos letras. Además, `calculadora.js:112` no precarga un
   origen guardado como nombre o etiqueta. Es tu punto 6; no lo toqué.
2. **La migración de `clients` en el arranque.**
   - Usa el mismo `lock_timeout` de 5 s que las otras tres tablas.
   - El adversario lo reprodujo en su Postgres descartable: con otra sesión que tenía `clients` en una
     transacción abierta, el arranque se cortó a los 5,0 s con `LockNotAvailableError`.
   - El código prevé que el reinicio lo vuelva a intentar. Pero `clients` es la tabla más leída: en el
     despliegue, una transacción vieja que la tenga abierta corta el arranque hasta que se libere.
   - Va con la copia de la base.
3. **Cuántas etiquetas se cortan en la ficha.** Con Inter, cortadas con «…» y el código entero:
   1280:4 841:36 721:5 641:12 601:14 561:17 521:23 481:37 320:46. Con Liberation Sans: 1280:4 841:36 721:6 641:13 601:14 561:17 521:26 481:38 320:45. «Origen habitual» en dos renglones, con Inter: 1280:7 841:38 721:0 641:6 601:7 561:10 521:13 481:15 320:40.
4. **A 320 px Emiratos se corta** en la etiqueta y en el campo. El código queda a la vista.
5. **Los tipos del modelo y de `_migrate_sync_clients_columns`** no tienen sabotaje propio. En Postgres
   los cubre la migración, que lleva a `text` cualquier columna con tope, y su sabotaje (1) da rojo. En
   SQLite el largo no se hace cumplir.
6. **Ya estaban, no son de esta pieza** (de `/code-review` y del adversario):
   - la moneda se sigue recortando a 3 sin aviso («Dólar» → «DÓL»), y un select sin la moneda guardada
     la borra al guardar;
   - la reconstrucción de `clients` en SQLite (`_migrate_clients_email_nullable`) no copia
     `fecha_inic_activ` ni `column_mapping`. Sólo corre en una base SQLite vieja con email
     obligatorio.
   - Te los propongo para la cola.
7. **chequeo-6, los dos `AVISO`:**
   - el primero es la función anónima que envuelve todo `clientes.js`;
   - el otro, `init`, suma una sola línea, sin rama: llenar el `datalist` donde se toman los demás
     campos del formulario.
8. **Lo que no corrí:** navegadores reales de Windows y macOS, y la copia de la base de producción.

## Revisión

- **`/code-review` alto:** el salto de línea (arreglado, `55060c5a`), D276 y lo que ya estaba (riesgo
  6).
  - No atendí, con razón:
    - el orden de carga de `paises_maria.js`: `clientes.js` ya lo usaba en el catálogo;
    - el mensaje que repite lo escrito sin tope: el catálogo hace lo mismo, y sale con `textContent`.
- **Adversario Opus alto:** D277, el riesgo 2 y lo que ya estaba. No encontró otros caminos que
  escriban `default_origin`.
- **`/security-review`:** sin hallazgos.
  - Las dos vistas escapan: `clientes.js:1073` y `:1239`.
  - El error sale con `textContent`, y el `datalist` sale de la tabla fija.
  - La edición sigue pasando por `_get_owned_client`.

## chequeo-6

```
chequeo-6 4fe296d4..0d7401ed: avisos para mirar, no un veredicto
producto +44/−42
arnés +613/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/database/models.py: 617 → 617
  proyecto_maria/main.py: 12280 → 12287
  proyecto_maria/static/v2/screens/clientes.js: 2213 → 2219
  AVISO creció una función de más de 150: proyecto_maria/static/v2/screens/clientes.js:12 <anónima> 2202 → 2208, 1 en su propio cuerpo (§6: lo nuevo va aparte)
  AVISO creció una función de más de 150: proyecto_maria/static/v2/screens/clientes.js:66 <anónima>.init 167 → 168, 1 en su propio cuerpo (§6: lo nuevo va aparte)
avisos: 2
```
Los dos `AVISO` tienen su porqué en el riesgo 7.

## Comandos para reproducir

```bash
VENV=/ruta/al/venv
# 1. sabotajes con Postgres 16 descartable (21 min) → BASE «3 passed», «OK: pantalla del origen habitual»,
#    «Postgres: fallas: 0»; 25 «ROJO», «sabotajes sin rojo: 0»
PY=$VENV/bin/python scripts/testing/con_pg16.sh bash -c 'PG_URL="$BACKUP1A_PG_URL" scripts/testing/sabotajes/origen2.sh 0d7401ed' | grep -E "^(BASE|ROJO|VERDE|ROTO|NO CORRIDO)|sin rojo"
# 2. la migración sola (1 min)                       → 8 «OK», «fallas: 0»
PY=$VENV/bin/python scripts/testing/con_pg16.sh bash -c '"$PY" -I scripts/testing/origen2_postgres.py "$BACKUP1A_PG_URL"' 2>&1 | grep -E "^(OK|FALLA)|fallas"
# 3. el caso (5 s)                                   → «3 passed»
env -u DATABASE_URL -u ENVIRONMENT GEMINI_API_KEY=test-key PYTHONPATH=. $VENV/bin/python -B -m pytest -q --no-cov -p no:cacheprovider tests/test_origen2.py | tail -1
# 4. §6                                              → «producto +44/−42», «avisos: 2»
python3 docs/pm/herramientas/chequeo-6.py 4fe296d4 0d7401ed
```
- Corrí el 1 desde un guion, con `PY` puesto también adentro del `bash -c`. Comprobé aparte que `PY`
  llega adentro de `con_pg16.sh`.
- El 2, el 3 y el 4 los corrí tal cual, y dieron esa salida.
- Para D277, la consulta de sólo lectura en producción no es para correr acá: es la de arriba.

## Vuelta de CATALOGO-PAIS sobre `8140f496` (2026-11-19 23:45 UTC)

**Resultado.** Los dos puntos de tu devolución se cumplen en `8140f496`.
- Esta vuelta da `producto +2/−2`: sólo `app_v2.css`. La pieza entera, contra `695a5377`, da
  `producto +9/−13`. chequeo-6 da «avisos: 0» en las dos.
- No toqué el servidor ni `tests/`. Por eso no corrí `catalogo3.sh` ni la suite: es tu regla de
  puertas (comando 4).
- **Lo que decidís vos:** D275. Para que la fila siga en un renglón, el campo del origen del cliente se
  achica en las ventanas medianas, y ahí se corren más etiquetas que en `4904e5a1`. Lo detallo en el
  riesgo 1.

**El arreglo** (`ae3b27a3`). Son dos reglas del CSS del cliente:
```css
.cx-catalogo-producto-main { flex: 1; min-width: 0; }
.cx-catalogo-producto-input[data-field="origen"] { flex: 1 1 36px; min-width: 36px; max-width: 30ch; }
```
- El campo parte de 36 px, el ancho de la base. Por eso la fila baja de renglón en el mismo ancho que
  en la base.
- Después crece con lo que sobra de la fila, hasta 30ch.
- Ya no tiene `text-transform: uppercase`.
- El catálogo del proveedor no cambia: ya no forzaba mayúsculas, y su fila ya tenía el alto de la base.

**Punto 1: nada baja de renglón.**
- `enUnRenglon` (`scripts/testing/pantalla_holanda423.js`) es un solo caso para los dos catálogos.
- Saca los anchos de los cortes `max-width` de los estilos de la página, más uno, y los recorre hasta
  un piso: 460 px el cliente y 320 px el proveedor.
- En cada ancho mira dos cosas en cada fila:
  - que todas sus partes compartan un renglón (el «kg» es una parte);
  - que la fila tenga el mismo alto que a 1280 px.
- Si no encuentra las filas o sus partes, falla.
- El piso del cliente es 460 porque a 450 la base también baja de renglón: el barrido da «450–440:
  87*» con la base y con el arreglo.

**Punto 2: lo no reconocido se ve como se guardó.**
- `comoSeGuardo` mira en los dos catálogos cinco formas: «Narnia», «tierra media», «ATLANTIDA», el
  HTML y «-».
- Para cada una exige `text-transform: none` y `font-variant-caps: normal` en el campo.
- «Narnia» va primero: en mayúsculas no se ve igual, y «ATLANTIDA» sí.

**El rojo con el ancho fijo, en el mismo SHA.** Puse el CSS de `4904e5a1` sobre `8140f496` y la pantalla
dio:
«FALLA: catálogo del cliente a 841 px: baja de renglón la fila de «999 · OTROS PAISES»», salida 1.
- Las mayúsculas de vuelta las cubren dos sabotajes (abajo): uno por catálogo.

## Commits

| commit | qué |
|---|---|
| `ae3b27a3` fix | el campo del cliente se achica hasta el ancho de la base y crece hasta 30ch, sin mayúsculas; el CHANGELOG |
| `97bbd99d` test | `enUnRenglon`, `comoSeGuardo`, las formas mezcladas y siete sabotajes |
| `8140f496` test | el chequeo falla si no encuentra filas o sus partes; el comentario, en dos líneas. **Lo que se entrega** |
| informe | el commit siguiente, con las capturas |

## Pruebas, todas sobre `8140f496`

| qué | resultado |
|---|---|
| `holanda423.sh` | 34 «ROJO», «sabotajes sin rojo: 0», de 23:30:52 a 23:43:30 UTC (abajo) |
| `paises_nombres.sh` | 9 «ROJO», «OK: todos los sabotajes en rojo» |
| `e2e_maria.sh`, desde un worktree limpio | «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.», worktree sin cambios |
| pantalla con Inter | «OK catálogo del proveedor: 324 filas en un renglón y con su alto a 841, 721, 641, 601, 561, 521, 481, 320 px» y «OK catálogo del cliente: 325 filas en un renglón y con su alto a 841, 721, 641, 601, 561, 521, 481, 460 px» (BASE de `holanda423.sh`: «OK: pantalla Holanda→423») |
| pantalla con Liberation Sans (métricas de Arial) | las mismas dos líneas y «OK: pantalla Holanda→423» |
| negativo: el CSS de `4904e5a1` en `8140f496` | «FALLA: catálogo del cliente a 841 px: baja de renglón la fila de «999 · OTROS PAISES»», salida 1 |
| la guarda nueva, con el selector de las partes roto a mano | «FALLA: catálogo del cliente: no encuentra las filas o sus partes», salida 1 |
| barrido de 1600 a 320 px, cada 10 y en cada corte ±1, con las dos fuentes | igual a la base `695a5377`: cliente «1600–460: 82,82,82», proveedor «1600–320: 156,156» |
| chequeo-6 | abajo, entero |

`holanda423.sh`:
```
BASE  | casos: ================== 113 passed, 5 warnings in 68.74s (0:01:08) ==================
BASE  | pantalla: OK: pantalla Holanda→423
ROJO  | la etiqueta es lo que vino: «AssertionError», 1 casos
ROJO  | la etiqueta es lo que vino: «FALLA: catálogo del proveedor: «434» guardado se ve «434»»
ROJO  | la etiqueta es sólo el código: «AssertionError», 1 casos
ROJO  | la etiqueta escribe «null» por lo que falta: «AssertionError», 1 casos
ROJO  | la etiqueta deja los blancos de los bordes: «AssertionError», 1 casos
ROJO  | el origen frecuente se ve como HTML: «FALLA: el origen frecuente «<img»
ROJO  | el catálogo del proveedor muestra lo guardado: «FALLA: catálogo del proveedor: «434» guardado se ve «434»»
ROJO  | el catálogo del proveedor muestra lo guardado como HTML: «FALLA: catálogo del proveedor: «<img»
ROJO  | el catálogo del cliente muestra lo guardado: «FALLA: catálogo del cliente: «434» guardado se ve «434»»
ROJO  | el catálogo del cliente muestra lo guardado como HTML: «FALLA: catálogo del cliente: «<img»
ROJO  | el catálogo del cliente deja lo escrito: «FALLA: «434» escrito en el catálogo del cliente se ve «434»»
ROJO  | el catálogo del cliente corta el origen en 3: «FALLA: «CHINA» escrito en origen del catálogo del cliente se ve «CHI»»
ROJO  | el origen del catálogo del cliente no llega a Emiratos: «FALLA: catálogo del cliente: «331 · EMIRATOS ARABES,UNID» no entra en el campo»
ROJO  | el origen del catálogo del cliente no crece con la fila: «FALLA: catálogo del cliente: «331 · EMIRATOS ARABES,UNID» no entra en el campo»
ROJO  | el origen del catálogo del cliente con ancho fijo: «FALLA: catálogo del cliente a 841 px: baja de renglón la fila de «»
ROJO  | el origen del catálogo del cliente no se achica hasta el ancho de la base: «FALLA: catálogo del cliente a 460 px: baja de renglón la fila de «»
ROJO  | el origen del catálogo del cliente en mayúsculas: «FALLA: catálogo del cliente: «Narnia» guardado no se ve con sus letras»
ROJO  | el origen del catálogo del proveedor en mayúsculas: «FALLA: catálogo del proveedor: «Narnia» guardado no se ve con sus letras»
ROJO  | los campos del catálogo del proveedor bajan de renglón en el teléfono: «FALLA: catálogo del proveedor a 320 px: baja de renglón la fila de «»
ROJO  | el origen del catálogo del proveedor en el ancho de un código: «FALLA: catálogo del proveedor: «331 · EMIRATOS ARABES,UNID» no entra en el campo»
ROJO  | el origen del catálogo del proveedor con su ancho propio: «FALLA: catálogo del proveedor: el campo de origen se sale de su fila»
ROJO  | la procedencia del borrador se ve como vino: «FALLA: procedencia «434» del borrador se ve «434»»
ROJO  | la procedencia escrita queda como se escribió: «FALLA: procedencia «434» escrita se ve «434»»
ROJO  | la procedencia del borrador cambia en la operación: «FALLA: procedencia «434» del borrador queda «423 · PAISES BAJOS» en la operación»
ROJO  | la procedencia escrita se guarda como se ve: «FALLA: procedencia «434» escrita queda «423 · PAISES BAJOS» en la operación»
ROJO  | el catálogo del proveedor manda el origen sin tocar: «FALLA: cambiar sólo el NCM reescribe el origen guardado»
ROJO  | guardar otro campo del proveedor borra el origen: «AssertionError», 1 casos
ROJO  | guardar otro campo del cliente borra el origen: «AssertionError», 1 casos
ROJO  | el catálogo del cliente pisa lo que se sigue escribiendo: «FALLA: lo escrito mientras se guardaba «434» quedó «423 · PAISES BAJOS»»
ROJO  | el borrador muestra cada campo con su etiqueta: «FALLA: la factura «434» del borrador se ve «423 · PAISES BAJOS»»
ROJO  | lo escrito en cualquier campo pasa por la etiqueta: «FALLA: la factura «0434» escrita se ve «423 · PAISES BAJOS»»
ROJO  | el catálogo del cliente muestra el código de lo escrito: «FALLA: «434» escrito en el catálogo del cliente se ve «423»»
ROJO  | la procedencia cambia en cada tecla: «FALLA: procedencia «434» escrita queda «423 · PAISES BAJOS» en la operación»
ROJO  | el origen frecuente se ve como vino: «FALLA: el origen frecuente «434» se ve «434»»
sabotajes sin rojo: 0
```
**Los siete nuevos** van del «no llega a Emiratos» al «bajan de renglón en el teléfono», menos el de
Emiratos, que ya estaba:
- El de 48 px de ancho mínimo da rojo a 460 px. Lo probé con las dos fuentes. A 841 px el campo mide
  66 px con Inter y 70 con Arial, así que a ese ancho un mínimo de 48 no se nota.
- El de 841 px es tu ancho fijo de `4904e5a1`, sin las mayúsculas.

chequeo-6, entero:
```
chequeo-6 695a5377..8140f496: avisos para mirar, no un veredicto
producto +9/−13
arnés +259/−81
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/static/v2/paises_maria.js: 294 → 288
  proyecto_maria/static/v2/screens/catalogo.js: 404 → 404
  proyecto_maria/static/v2/screens/clientes.js: 2213 → 2213
avisos: 0
chequeo-6 4904e5a1..8140f496: avisos para mirar, no un veredicto
producto +2/−2
arnés +76/−3
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

**Capturas** de `8140f496`, con datos inventados, en `docs/pm/capturas/`:
- `catalogo-pais-cliente-1280-lista.png`, `catalogo-pais-cliente-960-lista.png` y
  `catalogo-pais-cliente-841-lista.png`;
- `catalogo-pais-proveedor-1280.png` y `catalogo-pais-proveedor-960.png`.

A 1280 y a 960 px las siete filas del cliente quedan en un renglón y «Narnia» se ve así. La de 841
muestra el riesgo 1.

## Revisiones

| quién | sobre | hallazgos | qué hice |
|---|---|---|---|
| `adversario-sonnet-alto` | `4904e5a1..97bbd99d` | nada serio; 5 observaciones | Barrió de 1500 a 300 px, de a 1 px: el arreglo baja de renglón en el mismo ancho que la base (455 px). Reprodujo tu rojo con el CSS de `4904e5a1`. Las observaciones son los riesgos 3, 4 y 5 y el punto de §6 del riesgo 6 |
| `/code-review high` | `4904e5a1..97bbd99d` | 1 importante, 5 menores | El importante, el campo que se achica a 841 px, es el riesgo 1. Arreglé dos menores en `8140f496`: verde sin filas medidas y el comentario de tres líneas. Los otros tres son los riesgos 3, 4 y 5 |

`8140f496` cambia sólo esa guarda y el comentario. No le pedí otra revisión: lo cubren las puertas de
arriba y el rojo de la guarda.

## Comandos

```bash
VENV=/ruta/al/venv
# 1. pantalla y sabotajes (13 min)  → BASE «OK: pantalla Holanda→423», 34 «ROJO», «sabotajes sin rojo: 0»
PATH=$VENV/bin:$PATH PY=$VENV/bin/python scripts/testing/sabotajes/holanda423.sh 8140f496 | grep -E "^(BASE|ROJO|VERDE|ROTO)|sin rojo"
# 2. nombres (20 s)                  → 9 «ROJO», «OK: todos los sabotajes en rojo»
PATH=$VENV/bin:$PATH PY=$VENV/bin/python scripts/testing/sabotajes/paises_nombres.sh 8140f496 | grep -E "^(BASE|ROJO|VERDE|ROTO)|OK:"
# 3. §6                              → «producto +2/−2», «avisos: 0»
python3 docs/pm/herramientas/chequeo-6.py 4904e5a1 8140f496
# 4. sin servidor ni tests           → sólo app_v2.css
git diff --stat 4904e5a1 8140f496 -- proyecto_maria/ tests/
```
Los corrí y dieron esa salida. El 1 lo corrí con `bash` delante, desde un guion, y con el resto de la
línea igual.

## Riesgos

1. **D275: en una ventana mediana el campo del cliente se achica, y se corren más etiquetas.**
   - La causa: entre 841 y unos 1040 px el panel del cliente se angosta. Para que la fila siga en un
     renglón, el que cede es el campo del origen: el NCM y el peso tienen ancho fijo.
   - Las mediciones sobre los 308 países (log de `ae3b27a3`, con el mismo CSS que `8140f496`):

     | ancho | Inter: campo | Inter: no entran | Arial: campo | Arial: no entran |
     |---|---|---|---|---|
     | 1600 a 1041 px | 208 px | 36 | 180 px | 44 |
     | 960 px | 158 px | 61 | 162 px | 56 |
     | 841 px | 66 px | 301 | 70 px | 290 |
     | 840 y 720 px | 208 px | 36 | 180 px | 44 |
     | 641 px | 206 px | 38 | 180 px | 44 |
     | 600 px | 181 px | 42 | 180 px | 44 |
     | 521 px | 102 px | 163 | 106 px | 145 |
     | 460 px | 41 px | 308 | 45 px | 308 |

   - A 841 px, «423 · PAISES BAJOS» se ve «423 · PAISI» (captura de 841). A 960 se corta Emiratos;
     los otros seis de la captura entran.
   - Antes de esta pieza el campo mostraba sólo el código, a cualquier ancho. Con `4904e5a1` medía
     208 px a cualquier ancho, pero la fila bajaba de renglón.
   - Tu punto 1 no deja que el campo crezca sin que la fila baje de renglón. Las opciones que veo:
     - **(a) aceptarlo como riesgo.** Es mi recomendación: la etiqueta se lee moviendo el cursor
       dentro del campo, como en tu riesgo 1 aceptado;
     - **(b) una pieza aparte** que ponga la etiqueta entera en el `title` del campo, que hoy dice
       «Origen».
2. **La página tiene barra horizontal entre 641 y 1140 px, y entre 460 y 521 px.**
   - Viene de la base, que hace lo mismo.
   - A 960 y a 841 px la página mide 1147 px de ancho (salida de las capturas).
   - No lo toqué.
3. **Los anchos salen sólo de los cortes `max-width` en px.**
   - Hoy no hay cortes `min-width`, ni en `em`, ni anidados en `@supports` o `@container`. Lo
     confirmó el adversario en `app_v2.css`.
   - Si alguno aparece, el chequeo no mide ese corte, y tampoco mide los anchos entre dos cortes.
4. **El alto se compara con el de la misma fila a 1280 px, no con el de la base.**
   - Hoy son iguales: el barrido da 82 px en el cliente y 156 en el proveedor, en la base y en el
     arreglo, a todo ancho.
   - El piso de 460 px es una constante. El adversario midió de a 1 px y la base baja de renglón
     recién a 455, así que de 456 a 459 px no se mide.
   - La igualdad es exacta, después de redondear. Con las dos fuentes no vi diferencias de medio píxel.
5. **El chequeo de mayúsculas mira el estilo del campo quieto.**
   - Una regla sólo para `:focus` o `:hover` no se vería.
   - El proveedor manda lo escrito en mayúsculas (`catalogo.js:312`). Eso no cambia lo no reconocido:
     el servidor no lo guarda (`origen_para_guardar` devuelve vacío con aviso).
   - Cambio de comportamiento: en el cliente, lo escrito en minúsculas («cn») se ve como se escribió
     hasta guardar, y después como la etiqueta.
6. **Los siete sabotajes nuevos son de CSS de pantalla.**
   - §6 pide guion de sabotaje sólo en lo de §3. Los sumé a `holanda423.sh` porque pediste «todos sus
     sabotajes en rojo» y «el chequeo nuevo con su rojo», y el guion ya era de esta pieza.
   - Si preferís dejar sólo el rojo del negativo en el informe, son treinta líneas que se sacan.
7. **Lo que no corrí:**
   - `catalogo3.sh` y la suite: no cambió el servidor ni `tests/`.
   - `/security-review`: el cambio es CSS.
   - Navegadores reales de Windows y macOS.
   - Ventanas más angostas que el piso (460 px y 320 px): ahí la base también baja de renglón.

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5, rama `claude/dev-maria`; rutina trig_01Ukttby1fc4sGVQfSn1jC9U (/respondio). PM principal session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `b73d96ec`. Aceptadas: las de antes (… ORIGEN-ETIQUETA (D261) sobre `5a28c13c`; CATALOGO-4 sobre `f5395b9f`; CATALOGO-PAIS sobre `8140f496`, D275 (a)). Pieza activa: ORIGEN-2, entregada sobre `0d7401ed` (base `4fe296d4`), espero el veredicto y D276–D277. Afuera, decidido: la calculadora recorta a 3 y `calculadora.js:112`, como riesgo sin código. Próxima D: D278. Lecciones (además de las del historial de este archivo): el negativo de un arreglo va en el mismo SHA con el arreglo vaciado; cada número del informe sale de un log; un ancho en `ch` depende de la fuente: medir con Inter y con Liberation Sans (`fuente/arial.conf`); una regla de pantalla se mide en cada ancho de disposición, no sólo a 1280; un sabotaje que falla en el primer elemento de una lista no prueba los de atrás: el más exigente va primero; sacar una regla de CSS puede cambiar qué chequeo pone el rojo de otro sabotaje: relanzar el guion entero después; no editar `scripts/` mientras corre un guion de sabotaje: cortar las puertas y relanzarlas sobre el SHA nuevo; un campo de texto pierde los saltos de línea de lo que se le pone; puertas con `setsid nohup`; horas, sólo de `date -u`; los comandos para la PM se prueban antes de escribirlos. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica; subagentes hasta esfuerzo alto, sin consejero, nunca Fable; detener los subagentes después de su informe. Letra ancha: tabla U+FF01..FF5E, no NFKC («№» da Noruega).
