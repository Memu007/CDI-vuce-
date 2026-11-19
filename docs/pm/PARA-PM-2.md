# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Entrega de CATALOGO-PAIS sobre `4904e5a1` (2026-11-19 21:45 UTC)

**Resultado.** Los seis criterios se cumplen en `4904e5a1`.
- `producto +8/−12`. chequeo-6 da «avisos: 0».
- No hay D nuevas.
- Lo que decidís vos: el riesgo 1. Unas cuarenta etiquetas largas se corren dentro del campo.

**El arreglo.**
- `catalogo.js` y `clientes.js` muestran el origen con `CDI.paisesMaria.etiqueta`, la de
  ORIGEN-ETIQUETA. `mostrar` quedó sin uso, así que lo saqué de `paises_maria.js`.
- El campo del cliente:
  - ya no tiene `maxlength="3"`;
  - mide `30ch` y muestra en mayúsculas;
  - al guardar, vuelve a mostrar la etiqueta.
- El campo del proveedor:
  - la grilla pasa a `1fr 2fr`;
  - el campo pasa a `width: 100%; min-width: 0`.

  Sin esto, «423 · PAISES BAJOS» no entraba y el campo se salía de la tarjeta.
- El servidor no cambia. El proveedor ya mandaba el origen sólo si cambió, y los dos PUT ya aceptaban
  nombre o código.

**Criterio por criterio.**
1. **Guardar otro campo deja el origen igual.**
   - `test_cada_pais_del_catalogo_vuelve_a_su_codigo` (`tests/test_catalogo3.py`) guarda otro campo
     en los 308 productos de cada catálogo (el NCM en el proveedor, el peso en el cliente) y compara
     las filas enteras.
   - La pantalla hace lo mismo con el NCM en el proveedor y con el peso en el cliente, y compara lo
     guardado.
2. **Toda la tabla va y vuelve.** El mismo caso guarda en cada producto la etiqueta que muestra la
   pantalla, como la manda cada pantalla. Cada uno vuelve a su código.
3. **Corregir por nombre o por código.** La pantalla escribe «CHINA», «nl» y «434» en el catálogo del
   cliente, y «0434» en el del proveedor.
4. **Lo que no se reconoce se ve como vino.** Un origen con HTML no se ejecuta en ninguno de los dos
   catálogos (`__xss`).
5. **El TXT sale igual.** No cambió ningún archivo Python de producto: el diff es CSS y JS de pantalla
   (comando 4). El e2e da OK.
6. **Negativo en el mismo SHA:** está en la tabla de pruebas.

**Lo que cambió por la revisión.**
- **El ancho del campo del cliente.**
  - 22ch cortaba Corea y Alemania. 24ch cortaba Corea con métricas de Arial: lo encontró el adversario.
    Lo puse en 30ch.
  - Lo medí con Inter y con Liberation Sans, que tiene las métricas de Arial: los seis orígenes que
    mira la pantalla entran con las dos.
  - El chequeo de ancho mira primero Emiratos, el más ancho de los seis. También mira primero que el
    campo no se salga de su fila y después que la etiqueta entre.
  - Así el sabotaje de 22ch da rojo sólo por Emiratos. Sin el 331 en la lista falla otro país, y
    entonces no da rojo. Lo comprobé a mano con las dos fuentes.
- **El CHANGELOG decía «más de 26 letras».** Era falso: con Arial no entra «306 · CAMBODYA(EX-KAMPUCHE»,
  de 20 letras. Ahora dice «unos cuarenta de los 308».

## Commits

| commit | qué |
|---|---|
| `976c5d1a` fix | los dos catálogos con `etiqueta`, sin `maxlength`, el CSS del proveedor y el CHANGELOG |
| `41774734` test | el caso de toda la tabla, la pantalla y los sabotajes, dos de ellos del servidor |
| `07e8a6ba` fix | el campo del cliente a 24ch |
| `323c3b53` test | la pantalla mira el ancho, espera la fila redibujada y siembra con dueño |
| `b7346a89` test | el sabotaje del ancho del cliente |
| `ea846cde` fix | el campo del cliente a 30ch; el CHANGELOG |
| `87b044b1` test | el ancho se mira también con Emiratos |
| `456f6c42`, `d6e29625`, `6e2549a4` fix | el CHANGELOG, hasta dejar sólo lo medido |
| `ba8a9014`, `fe77aaaf`, `4904e5a1` test | Emiratos primero, la fila antes que el contenido, las frases de los sabotajes y el comentario. **Lo que se entrega** |
| informe | el commit siguiente |

## Pruebas, todas sobre `4904e5a1`

| qué | resultado |
|---|---|
| suite completa, desde un worktree limpio | «6228 passed, 110 skipped, 3 xfailed, 115 warnings in 1299.90s (0:21:39)», worktree sin cambios |
| `e2e_maria.sh`, desde ese worktree | «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.» |
| `holanda423.sh` | 28 «ROJO», «sabotajes sin rojo: 0» (abajo) |
| `catalogo3.sh` | 65 «ROJO», «fallas: 0», de 20:26:11 a 21:44:31 UTC (riesgo 7) |
| `paises_nombres.sh` | 9 «ROJO», «OK: todos los sabotajes en rojo» |
| pantalla con Inter y con Liberation Sans | «OK: pantalla Holanda→423» las dos |
| negativo: `proyecto_maria/` de la base `695a5377` con las pruebas de `4904e5a1` | «FALLA: catálogo del proveedor: «434» guardado se ve «423»», salida 1 |
| el caso pytest con el producto de la base | «113 passed». Es una guarda, no distingue el arreglo (riesgo 6) |
| chequeo-6 | abajo, entero |

El caso pytest del negativo lo corrí sobre `41774734`. `tests/` no cambió desde entonces.

`holanda423.sh`:
```
BASE  | casos: ================== 113 passed, 6 warnings in 72.29s (0:01:12) ==================
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
Los dos «borra el origen» rompen el servidor, uno el del proveedor y otro el del cliente: el PUT pisa
el origen con lo que llegue. Los dos dan rojo sólo en el caso de toda la tabla.

chequeo-6, entero:
```
chequeo-6 695a5377..4904e5a1: avisos para mirar, no un veredicto
producto +8/−12
arnés +185/−80
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/static/v2/paises_maria.js: 294 → 288
  proyecto_maria/static/v2/screens/catalogo.js: 404 → 404
  proyecto_maria/static/v2/screens/clientes.js: 2213 → 2213
avisos: 0
```

## Revisiones

| quién | sobre | hallazgos | qué hice |
|---|---|---|---|
| `adversario-sonnet-alto` | `41774734` | ninguno alto, 2 bajos | el de las etiquetas largas es el riesgo 1; el del «\n» de antes, el 2 |
| `/code-review high` | `695a5377..41774734` | 4 menores, 1 previo | arreglé 3 en `323c3b53`: siembra con dueño, espera de la fila nueva y un escrito que cambia lo guardado; el cuarto es el riesgo 1; el previo, el 3 |
| `adversario-sonnet-alto` | `b7346a89` | 1 medio, 1 bajo | el medio, 24ch que corta Corea con Arial, quedó en 30ch en `ea846cde`; el bajo es el riesgo 1 |
| `/code-review high` | `41774734..b7346a89` | 1 importante, 1 previo, 4 menores | el importante, «`ch` depende de la fuente», en `ea846cde`; Emiratos, la frase, el nombre del sabotaje y el CHANGELOG, en `ea846cde` y `87b044b1`; el previo es el riesgo 4 |
| yo | `87b044b1` | el CHANGELOG decía «más de 26 letras» | lo medí y lo corregí |
| `/code-review high` | `b7346a89..ba8a9014` | 5 menores | arreglé 4: la frase y el orden del sabotaje de Emiratos, el comentario y el CHANGELOG. El quinto, el campo que se sale en una fila angosta, no lo reproduje: a 390 px la fila mide 308 y el campo, 208, queda 88 px adentro |
| `adversario-sonnet-alto` | `b7346a89..fe77aaaf` | 3 bajos | el comentario y el CHANGELOG, en `6e2549a4` y `4904e5a1`; el tercero es el riesgo 4. Confirmó que los tres sabotajes de ancho dan rojo por su motivo, con las dos fuentes |

## Comandos

```bash
VENV=/ruta/al/venv
PT="env -u DATABASE_URL -u ENVIRONMENT GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=. $VENV/bin/python -B -m pytest -q --no-cov -p no:cacheprovider --timeout=300"
# 1. toda la tabla en los dos catálogos, en 4904e5a1                 → «1 passed, 112 deselected»
$PT tests/test_catalogo3.py -k test_cada_pais_del_catalogo_vuelve_a_su_codigo | tail -1
# 2. pantalla y sabotajes (12 min)   → BASE «OK: pantalla Holanda→423», 28 «ROJO», «sabotajes sin rojo: 0»
PATH=$VENV/bin:$PATH PY=$VENV/bin/python scripts/testing/sabotajes/holanda423.sh 4904e5a1 | grep -E "^(BASE|ROJO|VERDE|ROTO)|sin rojo"
# 3. §6                                                 → «producto +8/−12», «avisos: 0»
python3 docs/pm/herramientas/chequeo-6.py 695a5377 4904e5a1
# 4. el TXT: sólo cambian CSS y JS de pantalla           → app_v2.css, paises_maria.js, catalogo.js, clientes.js
git diff --stat 695a5377 4904e5a1 -- proyecto_maria/
```
Ya corrí los cuatro y dieron esa salida.

## Riesgos

1. **Unas cuarenta etiquetas largas se corren dentro del campo.**
   - Sobre los 308, a 1280 px, con Inter: 38 en el proveedor y 36 en el cliente. Con Liberation Sans
     (métricas de Arial): 38 y 44.
   - La más corta que no entra tiene 31 caracteres con Inter (Svalbard) y 26 con Arial (Camboya).
   - Se leen moviendo el cursor dentro del campo. El `title` sigue diciendo «Origen».
   - Si querés que se vean enteras (en el `title`, o con un campo más ancho), es otra pieza.
2. **Un origen viejo con salto de línea se reescribe al guardar sólo el NCM en el proveedor.** Viene de
   antes. Sólo pasa en filas sembradas por SQL, porque la API no lo guarda.
3. **Vaciar el origen del cliente lo muestra vacío y el servidor guarda «XX».** Viene de antes.
4. **La pantalla no ve un campo del cliente demasiado ancho ni de ancho cero.**
   - Lo encontró el adversario: con 70ch los campos vecinos bajan de línea, y la pantalla sigue verde.
   - No hay sabotaje de «se sale de su fila» en el cliente.
   - No nace en este tramo y no lo amplié.
5. **Fuentes reales de Windows y macOS, sin probar.** Probé Inter y Liberation Sans a 1280 px, y los
   anchos de 1280 a 390 px sólo con Inter. Con Arial, Emiratos queda a 10 px del borde. La página del
   teléfono mide 523 px de ancho, igual que en la base.
6. **El caso pytest es una guarda.** Con el producto de la base también da verde. La pantalla es la que
   distingue el arreglo, y los dos sabotajes del servidor muestran que el caso atrapa un origen pisado.
7. **`catalogo3.sh` pasa a tardar unos 80 minutos.**
   - Cada sabotaje corre `test_catalogo3.py` entero. El caso nuevo de toda la tabla tarda 40 s solo
     («1 passed, 112 deselected, 3 warnings in 40.41s»).
   - El tope de 3600 s de mi carril lo cortaba a las 21:26; a las 21:15 iba por 40 de 65. Le saqué el tope a mitad de
     corrida y terminó en el mismo log.
   - Si para tu reproducción pesa, partir el caso o correrlo aparte es una pieza de limpieza: no lo toqué.
8. **Lo que no corrí:**
   - `/security-review`. Lo de HTML lo cubren `__xss` y los tres sabotajes de escape.
   - Navegadores reales de Windows y macOS.
   - Postgres: no hay cambio de servidor ni de base.

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5, rama `claude/dev-maria`; rutina trig_01Ukttby1fc4sGVQfSn1jC9U (/respondio). PM principal session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `7ad4dbdb`. Aceptadas: las de antes (… PAISES-NOMBRES (D266) sobre `fa89e917`; ORIGEN-ETIQUETA (D261) sobre `5a28c13c`; CATALOGO-4 sobre `f5395b9f`). Pieza activa: CATALOGO-PAIS entregada sobre `4904e5a1` (base `695a5377`), espero el veredicto. Después, sólo con CATALOGO-PAIS aceptada: ORIGEN-2 (migración VARCHAR(3) del origen habitual, revisión fuerte, calculadora fuera). Próxima D: D275. Lecciones (además de las del historial de este archivo): el negativo de un arreglo va en el mismo SHA con el arreglo vaciado; cada número del informe sale de un log, también los del CHANGELOG y los comentarios; un ancho en `ch` depende de la fuente: medir con Inter y con Liberation Sans (`fuente/arial.conf`); un sabotaje que falla en el primer elemento de una lista no prueba los de atrás: el más exigente va primero; no editar `scripts/` mientras corre un guion de sabotaje: cortar las puertas y relanzarlas sobre el SHA nuevo; `catalogo3.sh` tarda ~80 min, sin tope de 3600 s; en una vuelta de datos, un adversario Sonnet alto y `/code-review high` hasta el SHA final, y otra pasada sobre los commits que nacen de ellos; puertas con `setsid nohup`; horas, sólo de `date -u`; los comandos para la PM se prueban antes de escribirlos. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica; subagentes hasta esfuerzo alto, sin consejero, nunca Fable; detener los subagentes después de su informe. Letra ancha: tabla U+FF01..FF5E, no NFKC («№» da Noruega).
