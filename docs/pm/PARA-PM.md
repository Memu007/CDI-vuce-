# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CONEXIONES-1 G (sólo arnés): con el diff de F, 4 cuerpos de 500 MB de una cuenta impaga retienen +2,5 GB, el pico sube +4,5 GB y la otra cuenta espera ~3 s al soltar; en HEAD, nada. Decide la PM: D188, D189

| Qué | SHA |
|---|---|
| Arnés `scripts/testing/conexiones1_cuerpo.py` | `7ed91bac` |
| Este informe | el commit `docs:` que lo trae |

Base: `21df2a39` (informe de F). Producto commiteado: ninguno. Emi todavía
no dijo que sí a D182, así que corrí G y no la pieza de producto.

## Resultado, en corto

El arnés levanta la app real con Postgres 16 (gunicorn, 1 worker, como
producción) y una cuenta impaga manda cuerpos JSON de 1, 10, 100 y 500 MB a
`/api/operations/manual`, de a uno, 8×100 MB y 4×500 MB a la vez. Mientras tanto otra cuenta,
que sí puede cargar, pide su lista. Medí dos árboles: HEAD tal cual y HEAD con
el diff revisado de F aplicado. Ni la app ni uvicorn tienen tope de cuerpo para
esa ruta: 500 MB es el más grande que probé, no un límite de la app.

**El discriminante** es «lecturas de cuerpo en la ronda»: 0 en HEAD en todas
las rondas, N con el diff (1, 1, 1, 1, 8, 8, 8 y 4 en 4×500).

### 1. Cuánto tarda el 402

- **HEAD:** antes de leer el cuerpo. El 402 llega a los 0,007–0,011 s de
  empezar a mandar (1 a 4 MB enviados) de a uno, a 0,027–0,155 s con 8×100 y
  a 0,087–0,097 s con 4×500. El arnés corta la conexión en el 402; un
  atacante que siga mandando, abajo en «HEAD con keep-alive».
- **Con el diff:** recién con el cuerpo entero adentro. El arnés retiene los
  2 últimos bytes hasta que el proceso tiene todo lo demás («listo en»), y
  después mide desde que los suelta:

| Ronda | Listo en (s) | Al 402 tras soltar (s) | Total hasta el 402 (s) | MB enviados |
|---|---|---|---|---|
| 1×1 MB | 0.05 | 0.003 | ~0.05 | 1.0 |
| 1×10 MB | 0.05 | 0.009 | ~0.06 | 10.0 |
| 1×100 MB | 0.31 | 0.081 | ~0.39 | 100.0 |
| 1×500 MB | 1.47 | 0.345 | ~1.8 | 500.0 |
| 8×100 MB (1ª) | 2.24 | 0.625–0.66 | ~2.9 | 100.0 c/u |
| 8×100 MB (2ª) | 2.24 | 0.519–0.526 | ~2.8 | 100.0 c/u |
| 8×100 MB (3ª) | 2.4 | 0.559–0.565 | ~3.0 | 100.0 c/u |
| 4×500 MB | 6.32 | 2.933–2.939 | ~9.3 | 500.0 c/u |

El total es «listo en» más el tiempo tras soltar, y no se compara directo con
HEAD: con el diff el 402 espera a que llegue el cuerpo entero, así que el
atacante decide cuánto dura (si retiene los últimos bytes, lo que quiera;
uvicorn no tiene plazo para el cuerpo, leído y no medido). En loopback la
subida es cota inferior.

### 2. Cuánta memoria sube el proceso (RSS del worker, MB)

| Ronda | HEAD antes → pico | Con el diff: antes → retenido · pico · después |
|---|---|---|
| 1×1 | 158.4 → 158.5 | 158.4 → 159.8 · 160.4 · 160.4 |
| 1×10 | 158.5 → 158.6 | 160.4 → 169.0 · 178.6 · 159.4 |
| 1×100 | 158.6 → 158.6 | 159.4 → 259.2 · 358.7 · 159.2 |
| 1×500 | 158.6 → 158.9 | 159.2 → 659.2 · 1158.8 · 158.9 |
| 8×100 (1ª) | 158.9 → 160.6 | 158.9 → 1060.8 · 1860.5 · 182.0 |
| 8×100 (2ª) | 160.6 → 160.8 | 182.0 → 1060.7 · 1860.3 · 183.6 |
| 8×100 (3ª) | 160.8 → 160.8 | 183.6 → 1062.0 · 1861.7 · 183.1 |
| 4×500 | 158.3 → 159.4 | 158.3 → 2658.7 · 4658.3 · 159.6 |

Con el diff el pico es unas 2 veces los bytes en vuelo (el cuerpo en partes y
después unido): 8×100 MB suben **+1,7 GB** y 4×500 MB **+4,5 GB** de pico,
con +2,5 GB retenidos mientras la impaga no suelta. El host tiene 15-16 GB;
no sé el límite del contenedor de Railway. Se libera después del 402; a veces
queda un remanente (233.1 MB tras 1×100 en la corrida de los copiables). En
HEAD sube 2 MB como mucho.

### 3. Si otra cuenta lo nota (lista de la otra cuenta, ms)

| Ronda | HEAD, soltado | Con el diff: retenido · soltado |
|---|---|---|
| 1×100 | 11.6 | 5.1 · 71.0 |
| 1×500 | 13.1 | 5.2 · 345.4 |
| 8×100 (1ª) | 9.1 | 5.2 · 631.7 |
| 8×100 (2ª) | — | 5.1 · 549.3 |
| 8×100 (3ª) | — | 6.3 · 600.4 |
| 4×500 | — | 6.6 · 3006.4 |

- Base sin carga: mediana 4.4–6.6 ms. `no_200` dio 0 en todas las mediciones:
  la otra cuenta nunca recibió un error.
- **Retenido no lo nota** (~5-7 ms). **Al soltar sí:** su pedido espera hasta
  ~630 ms con 8×100 y 3006 ms con 4×500, porque el worker es uno solo y el event loop queda ocupado juntando
  y uniendo los cuerpos.
- «Subiendo» no discrimina: HEAD también tuvo máximos de 85.0 ms (8×100) y
  147.1 ms (copiables), contra 85.0–88.2 con el diff. Lo atribuyo a la carga
  del loopback, no a la app.
- En HEAD algunas rondas no tienen muestra «soltado» (1×1, 1×10, 2ª y 3ª de
  8×100, 4×500): el arnés toma 0 o 1 muestra en esa fase. Con el diff
  «soltado» es también una sola muestra por ronda, sin percentiles.

### HEAD con keep-alive: un atacante que sigue mandando después del 402

El arnés corta la conexión al recibir el 402. El adversario armó una copia
que no la corta y sigue mandando; la corrí sobre HEAD (`1x100,4x100,8x100`):

- Cada impaga manda los 100.0 MB enteros, con el 402 a los 0,007–0,228 s.
- Memoria plana: RSS entre 158.4 y 161.1 MB en las tres rondas.
- La copia no está en el repo: es la del arnés sin el corte en el 402.
- Otra cuenta mientras suben: mediana 6.5 / 99.5 / 41.4 ms (n 1, 2 y 4),
  máximo 158.9 ms; `no_200` 0. Mismo orden que «subiendo» con el arnés.

En HEAD el costo de seguir mandando es CPU y ancho de banda, no memoria.

## Hallazgo: en HEAD el riesgo ya existe para cualquier cuenta recién registrada

De código, no medido:

- Los dos registros (`main.py` ~3488-3497 y ~10723-10745) dejan usuario y
  estudio en `billing_status="trial"` con `trial_ends_at` a +14 días.
  `tiene_acceso` (`billing_service.py:129`) deja pasar trial.
- Con `EMAIL_VERIFICATION_REQUIRED` en su valor por defecto (`"false"`,
  `main.py:225`) la cuenta queda verificada al registrarse. No sé qué valor
  tiene producción.
- La ruta hace `request.json()` sin tope. Entonces, en HEAD, cualquiera que se
  registre puede mandar el mismo cuerpo de 500 MB y llega al parseo: mismo
  efecto de memoria que mide la tabla, más el costo del JSON (no medido).
- uvicorn 0.54 no tiene plazo para recibir el cuerpo (sólo keep-alive): un
  cliente lento retiene lo que mandó todo lo que quiera. Leído en
  `uvicorn/protocols/http/`, no medido.

Por eso el diff de F no crea el riesgo: lo extiende de trial y activas a las
impagas y sin cuota. Y un tope hace falta conteste lo que conteste Emi a D182.

## Decisiones

- **D188. ¿Qué hace la pieza de producto con el cuerpo de `/api/operations/manual`?**
  - **(a) Leer con tope (recomendada).** Reusar `_leer_cuerpo_con_tope`
    (`main.py:2926`, ya usada por ui-events) en `_leer_cuerpo`, con 413 si se
    pasa. Cubre las impagas del diff de F y también trial y activas en HEAD.
    El tope sale de medir el cuerpo legítimo más grande de una carga manual
    (D189); no lo invento.
  - **(b) La alternativa D186 (b):** no leer el cuerpo antes del 402. Las
    impagas vuelven a 0 lecturas, pero trial y activas siguen sin tope.
  - **(c) Aceptar el riesgo** con los números de arriba.
  - Por qué (a): es la única que cierra también el caso de HEAD, y la función
    ya existe y está probada.
- **D189. ¿De dónde sale el tope?**
  - **(a) Lo mido yo en la pieza de producto (recomendada):** el cuerpo de la
    carga manual más grande que permite la pantalla, con margen, y un caso que
    muestre 413 justo arriba y 200 justo abajo.
  - **(b) Lo fija Emi** con un número de negocio.
  - Aparte, para Emi: ¿producción tiene `EMAIL_VERIFICATION_REQUIRED=true`?
    No cambia la recomendación, pero sí cuánta gente puede llegar hoy al
    parseo sin tope.

Siguen abiertas, de antes: D182, D183 y D184 (Emi), y D186 y D187 (F).

## Declarado y no medido

- El proxy de Railway, el límite de memoria del contenedor y el ancho de banda
  real: loopback es una cota inferior para la subida y no muestra si el proxy
  ya corta cuerpos grandes.
- Más de 4×500 MB (8×500 sería del orden de +9 GB de pico por la proporción
  medida; no lo corrí) y más de 8 a la vez.
- El costo de parsear el JSON (el arnés manda un JSON válido grande y la
  impaga corta en el 402 antes del parseo).
- Una cuenta trial o activa en HEAD vía `request.json()`: deducido del código.
- La suite completa: G sólo agrega un script en `scripts/testing/`, no toca
  producto ni `tests/`.

## Hallazgos de la autorrevisión

| Revisor | Modelo y esfuerzo | Hallazgo | Qué hice |
|---|---|---|---|
| Yo | — | `FileNotFoundError` al leer `/proc/net/tcp6` en el contenedor | se salta el archivo si no existe |
| Yo | — | La marca del árbol decía «no lee» con el diff aplicado | busca `Depends(_leer_cuerpo)` |
| Yo | — | `httpx.ReadError` en la otra cuenta abortaba la medición | se anota como código y sigue |
| Adversario | Sonnet alto | (Alta) El tiempo al 402 con el diff no se compara con el de HEAD: el total es subida más 402 y lo controla el atacante | columna de totales y aclaración en §1 |
| Adversario | Sonnet alto | (Media-alta) Faltaba «el más grande × varios» | corrí 4×500 con el diff y en HEAD; va al título y a las tres tablas |
| Adversario | Sonnet alto | (Media) En HEAD con keep-alive el atacante manda todo | reproducido con su copia; memoria plana, sección propia |
| Adversario | Sonnet alto | (Media-baja) «soltado» es una sola muestra | declarado en §3 |
| Adversario | Sonnet alto | (Baja) Ruido en HEAD 8×100 (0,027 a 0,155 s), rondas sin repetir | queda; las 3 rondas de 8×100 muestran el rango |
| Adversario | Sonnet alto | (Baja) La marca del árbol es textual, sin hash; el árbol del diff trae además otros cambios de F | queda: la marca dice el SHA base y si hay cambios en `proyecto_maria` |
| Adversario | Sonnet alto | (Baja, no reproducido) Si falla `open_connection`, la tarea de muestreo queda huérfana | no corregido: no pasó en ninguna corrida |

## Riesgos

- Medí en loopback con 1 worker; en Railway la red y el proxy cambian los
  tiempos (el orden de magnitud de la memoria no).
- El arnés usa el estado del proceso (`/proc/<pid>/status`, conexiones TCP);
  corre en Linux.
- Las medianas de «subiendo» varían entre corridas; por eso no las uso como
  discriminante.

## Comandos copiables

Desde la raíz del repo, con el entorno virtual del proyecto activado y
Postgres 16 disponible para `con_pg16.sh`. El diff de F sale del informe
anterior (`21df2a39`). Cada corrida tarda unos 2 minutos.

```bash
git fetch origin claude/dev-tecnica
git worktree add --detach /tmp/g origin/claude/dev-tecnica && cd /tmp/g
PY=$(command -v python) scripts/testing/con_pg16.sh python scripts/testing/conexiones1_cuerpo.py --rondas 1x100,8x100   # → «retenidas 0 · lecturas de cuerpo en la ronda 0» en las dos rondas, pico ~161 MB, «medición válida»
git show 21df2a39:docs/pm/PARA-PM.md | awk '/^```diff$/{f=1;next} /^```$/{f=0} f' > /tmp/f.diff
git apply --check /tmp/f.diff && git apply /tmp/f.diff
PY=$(command -v python) scripts/testing/con_pg16.sh python scripts/testing/conexiones1_cuerpo.py --rondas 1x100,8x100   # → «retenidas 8 · lecturas de cuerpo en la ronda 8», pico ~1960 MB, soltado ~618 ms, «medición válida»
```

Sin `--rondas` corre las de las tablas (`1x1,1x10,1x100,1x500,8x100,8x100,8x100`).

Lo que dieron en mi corrida (árbol `7ed91bac`):

- HEAD: 1×100 «listo en 0.05 s · retenidas 0 · lecturas de cuerpo en la ronda 0», RSS 158.8 → pico 159.0; 8×100 «listo en 0.26 s · retenidas 0 · lecturas de cuerpo en la ronda 0», pico 161.1, soltado 6.8 ms; «medición válida».
- Con el diff: 1×100 «listo en 0.31 s · retenidas 1 · lecturas de cuerpo en la ronda 1», 158.7 → pico 359.0; 8×100 «listo en 2.39 s · retenidas 8 · lecturas de cuerpo en la ronda 8», 233.1 → pico 1960.1 → 185.7, al 402 en 0.586–0.592 s, soltado 618.5 ms; «medición válida».

## Puertas

| Puerta | Resultado |
|---|---|
| Arnés completo, HEAD `21df2a39` | medición válida · rc=0 |
| Arnés completo, `21df2a39` con el diff de F | medición válida · rc=0 |
| 4×500, HEAD y con el diff | medición válida · rc=0 las dos |
| Copia del adversario sin corte, HEAD | medición válida · rc=0 |
| Copiables en un árbol limpio `7ed91bac` (HEAD y con el diff) | medición válida · rc=0 las dos |
| `git apply --check` del diff de F sobre `7ed91bac` | limpio |
| chequeo-6 | 0 avisos |

**No corrido:** suite completa, smoke y ataques (no hay producto ni casos
nuevos en `tests/`).

<details><summary>chequeo-6 21df2a39..HEAD (HEAD = 7ed91bac)</summary>

```
chequeo-6 21df2a39fed2cfedee261325ca327bce34f968bf..HEAD: avisos para mirar, no un veredicto
producto +0/−0
arnés +366/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

</details>
