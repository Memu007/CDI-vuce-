# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## PRUEBAS-1 y PA-1b: entregadas

**Resultado: las dos están terminadas y queda una D.**
- **PRUEBAS-1** toca sólo pruebas; la PA-1b, la línea `:130` de la landing.
- La `:139` no la cambié: con los valores de hoy diría algo falso (D8).
- Todas las puertas dieron «sin rojo: 0» / «con falla: 0».
- La prueba de que la espera del foco distingue es **débil**: sin la espera,
  falló 1 de 30.

| Qué | SHA |
|---|---|
| Base | `913d282` |
| a) foco | `50b9677` (la espera), `35a681a` (la prueba de que distingue) |
| b) excel1 | `da6ae08` |
| b) excel2 | `e6e793f`, `f20d4a0` (corte a los 90 s) |
| b) maria1b | `99d4e3e` |
| c) e2e | `83f4d31`, `f5705cf`, `292c7e8`, `888af8b` |
| PA-1b, producto | `8db1ff7` |
| PA-1b, prueba | `0429283` |
| Tus merges | `99dce27`, `5909f82` (sólo `docs/pm`) |
| Informe | este commit |

**Dónde corrió cada puerta:**
- Sobre `35a681a`: `excel1`, `cliente1`, `pa1`, la e2e y el foco.
- Sobre `99d4e3e`: `maria1b`.
- Sobre `f20d4a0`: `excel2`.

De `35a681a` a este commit, fuera de `docs/pm` cambian sólo `maria1b.sh` y
`excel2.sh`, y cada uno se corrió sobre su commit.

Archivos de producto que toqué: `proyecto_maria/templates/landing.html` (una
línea) y `CHANGELOG.md`.

### Decisiones

- **D8. `landing.html:139`, el encabezado `<span>NCM</span>` de la tabla de
  la demo.**
  - Problema: las tres filas muestran códigos de 8 dígitos (`8544.42.00`,
    `8517.62.59`, `8504.40.29`). Si el encabezado dice «PA SIM», la demo
    muestra como posición SIM algo que no lo es.
  - (a) Pasa a «PA SIM» y los tres valores pasan a posiciones de 11 dígitos
    con su letra de control, sintéticas pero bien formadas.
  - (b) Queda «NCM», como decidiste para `enrich.js:207` en D6.
  - **Recomiendo (b):** la demo queda coherente sin inventar posiciones que
    alguien podría tomar por reales. Si preferís (a), es una pieza de minutos.

### a) El foco de `cliente1`

**Causa:** la que dijiste. `clientes.js:1613/:1626` hace
`setTimeout(() => fNombre.focus(), 80)`.

**Qué hice:**
- `formularioListo()` en `pantalla_cliente1.js` espera
  `document.activeElement.id === 'cfNombre'`, después de cada una de las
  cinco esperas de `#cfNombre`.
- Por la familia: no hay otra prueba que llene `cxForm`. Ni las de PA-1 ni
  la e2e lo hacen. Se busca con `grep -ln "cxForm\|cfNombre" scripts/testing/*.js config/*.js`.

**La prueba de que distingue** es `scripts/testing/sabotajes/foco_cliente1.sh`:
- Corre la prueba 100 veces con la espera y el temporizador de 80 ms del
  producto.
- Corre 30 veces con el temporizador acortado a 10 ms, sólo en un worktree
  descartable.
- Corre 30 veces sin la espera, con 10 ms.
- La corrida sin espera sólo cuenta las fallas que traen el síntoma: lo
  escrito en el domicilio aparece en la razón social. Para eso, el mensaje de
  falla de la prueba ahora muestra la razón social (`pantalla_cliente1.js:144`).

**Salida exacta** (sobre `35a681a`, 1532 s):
```
con espera, 80 ms: 100 bien, 0 fallas de 100
con espera, 10 ms: 30 bien, 0 fallas de 30
        FALLA: Imposible: la edición no se guardó: Calle Inventada 1 (razón social: Cliente Inventado D3 Imposible 1792879567178Calle Inventada 2)
sin espera, 10 ms: 29 bien, 1 fallas de 30 (1 con el texto del domicilio en la razón social)
mediciones con falla: 0
```

**Es débil:** sin la espera falla 1 de 30 aun con 10 ms. Con 80 ms no lo
medí sin la espera; tu medición fue de 2 en 82.
- El script exige al menos una falla con el síntoma. Si una corrida no la
  ve, sale en rojo con «VERDE | sin la espera no falló nunca con el síntoma».
- No subí M para hacerlo más seguro, porque cada corrida tarda unos 8 s.
- Si querés más margen: `M=100`, con unos 15 minutos más.

### b) Los sabotajes viejos

**`excel1.sh`**
- Los cuatro patrones ahora apuntan al código de hoy.
- «El total en la columna de código» se sabotea con
  `_es_fila_de_total(descripcion)`, que es el defecto viejo. Con `rotulo`
  solo no da rojo, como dijiste.
- **Por qué `test_mapeo_guardado_no_deja_afuera_encabezados_nuevos` ya no
  distinguía `elegido = g`:**
  - La prueba subía «Qty».
  - La lectura encuentra «Qty» sola, por su lista de nombres, sin el mapeo.
  - El peso lo elige sin mirar el mapeo (MARIA-5).
  - Por eso, con el mapeo saboteado, el resultado era el mismo.
  - Ahora la prueba sube «Qty (pcs)», que sólo se encuentra si lo detectado
    completa el mapeo.

**`excel2.sh`**
- Los tres patrones ahora apuntan al código de hoy.
- Ahora corre sólo la prueba que nombra cada sabotaje, no `test_excel2.py`
  entero.
- **Por qué tardaba:** la medí sobre `35a681a`, antes del corte.
  - La corrida entera tardó 594 s.
  - Cada sabotaje tarda 3–5 s, salvo dos.
  - «El encabezado enorme» tarda 19 s.
  - «Una combinada vuelve a recorrerse hasta su última fila» tarda **448 s**.
- **Por qué la combinada tarda tanto:**
  - La prueba falla a los 10 s (`hilo.join(10)` y después
    `assert not hilo.is_alive()`).
  - pytest imprime el FAILED y «1 failed in 14.74s» a los 15 s.
  - Pero el proceso recién termina a los 438 s: el hilo daemon con la
    lectura saboteada sigue trabajando, y la salida del intérprete lo espera.
- **Arreglo, sólo en el script (`f20d4a0`):**
  - Cada corrida se corta con `timeout 90` (`LIMITE=` para cambiarlo) y
    `PYTHONUNBUFFERED=1`.
  - El rojo se sigue leyendo del resumen ya impreso, y la línea dice
    «cortado a los 90 s».
  - Un sabotaje que se cuelgue sin imprimir el FAILED esperado sale como
    «ROJO?» y cuenta como falla: el corte no esconde nada.
  - Con el corte, `excel2.sh` pasó de 594 s a 232 s.

**`maria1b.sh`**
- Los dos patrones ahora apuntan al código de hoy.
- El de la cantidad es `cantidad_mala = _fuera_de_rango(cantidad)` →
  `cantidad_mala = False`.
- El rojo exige «Item 1: Cantidad inválida», así que distingue.
- El chartsheet se busca en `security/file_security.py`.
- No toqué `controles_maria.py`.

### c) El rojo de `#validatingRerun`

**Causa:**
- Al entrar a Validación, la pantalla pide `/generate_maria/avisos` y pinta
  los avisos arriba de los botones: el botón baja unos 560 px.
- `page.click()` hace dos pasos: lleva el botón al centro y después calcula
  dónde clickear.
- Si los avisos llegan entre esos dos pasos, el botón queda fuera de la
  pantalla. Puppeteer da entonces «Node is either not clickable or not an
  Element».
- Medido en el momento de la falla: el botón está en el documento
  (`isConnected`) y visible; está fuera de la pantalla.

**No era la validación anterior:** con `/api/validate/smart` demorado 3000 ms
la prueba pasa sin la espera, porque la segunda visita usa la validación
guardada (menos de 60 s) y no llama a ese servicio antes del click. Por eso la
prueba de la demora que pediste no distinguía, y la cambié por la demora de los
avisos.

**La espera** (`config/e2e_maria.js`, `entrarAValidacion`): espera las 2
respuestas de `/generate_maria/avisos` (`requestfinished`) y el panel pintado.
- No usa la red quieta: `/api/ui/event` usa `keepalive`, queda pendiente y
  `waitForNetworkIdle` da timeout.
- `page.route` no existe en Puppeteer (es de Playwright). La demora se hace
  con la intercepción de pedidos que la e2e ya usa.

**La prueba de que distingue** es `scripts/testing/sabotajes/e2e_rerun.sh`:
- La carrera dura microsegundos.
- El script demora los avisos 1500 ms y hace el click de «Volver a validar»
  con los pasos de `page.click()` por separado, así la carrera pasa siempre.

Salida exacta, sobre `35a681a`, 43 s:
```
VERDE | con la espera, avisos demorados, click partido: pasó (13 s)
ROJO  | sin la espera, avisos demorados, click partido: falló con «Node is either not clickable or not an Element» (14 s)
VERDE | sin la espera, validación demorada, click normal: pasó (16 s)
mediciones con falla: 0
```
Además, la e2e normal corrió 30 veces seguidas sobre `35a681a`: 30 bien, en
306 s.

**Límite de la prueba:** las dos respuestas de avisos de la prueba son
iguales. Esperar sólo la primera daría el mismo verde, así que ningún
sabotaje distingue la espera de la segunda. Esa parte está sostenida por
lectura del código, no por un rojo.

### PA-1b

- `landing.html:130`: el paso 3 de la demo dice «PA SIM».
- La prueba es un caso en `test_pa1_textos.py` y un sabotaje en `pa1.sh`
  que lo vuelve a «NCM».
- La `:139` va a D8.

### Puertas

| Puerta | SHA | Salida | Tiempo |
|---|---|---|---|
| `excel1.sh` | `35a681a` | 36 `ROJO`, `sabotajes con falla: 0`, exit 0 | 575 s |
| `excel2.sh` | `f20d4a0` | 42 `ROJO` (la combinada: «(90 s, cortado a los 90 s)»), `sabotajes con falla: 0`, exit 0 | 232 s |
| `excel2.sh`, antes del corte | `35a681a` | 42 `ROJO`, `sabotajes con falla: 0`, exit 0 | 594 s |
| `cliente1.sh` | `35a681a` | 23 `ROJO`, `sabotajes sin rojo: 0`, exit 0 | 126 s |
| `pa1.sh` | `35a681a` | 28 `ROJO`, `sabotajes sin rojo: 0`, exit 0 | 52 s |
| `maria1b.sh` | `99d4e3e` | 34 `ROJO`, `sabotajes con falla: 0`, exit 0 | 470 s |
| `foco_cliente1.sh` | `35a681a` | `mediciones con falla: 0`, exit 0 (salida arriba) | 1532 s |
| `e2e_rerun.sh` | `35a681a` | `mediciones con falla: 0`, exit 0 (salida arriba) | 43 s |
| e2e 30 veces | `35a681a` | 30 bien | 306 s |
| `/code-review high` | sobre `913d282..35a681a` | tabla abajo | |

**No corrí:**
- La suite completa: son pruebas y una línea de HTML.
- `/security-review`: no hay dinero, sesión, permisos ni datos.
- `/code-review` sobre lo que agregué después: el síntoma del foco, `maria1b`
  y el corte de `excel2`.

**Las puertas y el foco corrieron a la vez:** compitieron por CPU, así que los
tiempos de esa tanda están inflados.

### Hallazgos de la autorrevisión

| Hallazgo | De quién | Qué hice |
|---|---|---|
| La espera nueva de la e2e no tenía una prueba que distinga la segunda respuesta | `/code-review high` | Queda como límite (arriba) |
| La prueba del foco no distinguía qué falla contaba | `/code-review high` | Se cuenta sólo la falla con el síntoma |
| Patrones y expectativas de los sabotajes | `/code-review high` | Arreglados |
| Los subítems de `excel2` (`main.py:4241`) no tienen un negativo propio | `/code-review high` | Riesgo, abajo |
| Dos cosas del producto, fuera de PRUEBAS-1 | `/code-review high` | No las toqué |
| «TOTAL AMOUNT» en otra columna entraría como producto | adversario Sonnet alto | No se reproduce: el rótulo ya la toma |

### Riesgos

- La prueba del foco es débil (1 de 30), ver a).
- La espera de la segunda respuesta de avisos no tiene sabotaje propio.
- El chequeo de subítems de `main.py:4241` no tiene un sabotaje en
  `excel2.sh`.
- El pie de los commits trae `Co-Authored-By: Claude Opus 5.5`, porque lo pide
  el aviso del sistema de la sesión. Choca con la regla de no poner el
  identificador del modelo en el repositorio. Si la regla manda, se cambia
  desde el próximo commit, sin reescribir los que ya están.

### Comandos para reproducir

```bash
PY=<venv>/bin/python
PY=$PY scripts/testing/sabotajes/excel2.sh       # 42 ROJO, la combinada «cortado a los 90 s», «sabotajes con falla: 0»
PY=$PY scripts/testing/sabotajes/excel1.sh       # 36 ROJO, «sabotajes con falla: 0»
PY=$PY scripts/testing/sabotajes/maria1b.sh      # 34 ROJO, «sabotajes con falla: 0»
PY=$PY scripts/testing/sabotajes/cliente1.sh     # 23 ROJO, «sabotajes sin rojo: 0»
PY=$PY scripts/testing/sabotajes/pa1.sh          # 28 ROJO, «sabotajes sin rojo: 0»
PY=$PY scripts/testing/sabotajes/e2e_rerun.sh    # VERDE, ROJO «Node is either not clickable…», VERDE; «mediciones con falla: 0»
PY=$PY scripts/testing/sabotajes/foco_cliente1.sh   # unos 25 min; «mediciones con falla: 0»
```

### Sigo con

EXCEL-3b. Ya tengo un borrador aislado y la revisión de un adversario. ESTUDIO-1
va cuando integres MARIA-7.

/compact conservar: Soy la Dev técnica (Dev 1) de CDI, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica (nunca main), rutina trig_011UpBfwEu9TUzoNUrviqoP5 min 15; aviso a la PM principal session_01B7FVQspcEHF7PqNv797wNM con send_message priority next empezando «Dev técnica:». PRUEBAS-1 + PA-1b entregadas (base 913d282; puertas sobre 35a681a, maria1b sobre 99d4e3e, excel2 sobre f20d4a0). Abierta para la PM: D8 (landing:139, recomiendo (b) dejar NCM). D4 (b), D5 (a), D6 (a), D7 (a) decididas. Sigo con EXCEL-3b (worktree $S/wt-3b, rama excel3b-wip, 3036ae9; adversario en $S/adv_excel3b_report.txt); ESTUDIO-1 después de que la PM integre MARIA-7. Reglas de Emi: sólo me piden la PM o Emi; nada se publica sin su «dale» para el SHA; nunca main; sin secretos ni datos reales; no tocar maria_generator.py, controles_maria.py ni el canal/rama de la Dev MARIA; subagentes hasta alto, sin Fable; esfuerzo medio.
