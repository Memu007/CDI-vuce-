# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

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

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5, rama `claude/dev-maria`; rutina trig_01Ukttby1fc4sGVQfSn1jC9U (/respondio). PM principal session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `75a5fd30`. Aceptadas: las de antes (… PAISES-NOMBRES (D266) sobre `fa89e917`; ORIGEN-ETIQUETA (D261) sobre `5a28c13c`; CATALOGO-4 sobre `f5395b9f`). Pieza activa: CATALOGO-PAIS, vuelta entregada sobre `8140f496` (base `695a5377`; la entrega anterior, `4904e5a1`), espero el veredicto y D275. Después, sólo con CATALOGO-PAIS aceptada: ORIGEN-2 (migración VARCHAR(3) del origen habitual, revisión fuerte, calculadora fuera; su punto 3 suma que las filas ya cortadas en 3, «CHI» y «HOL», quedan igual, como datos en el caso de la migración). Próxima D: D276. Lecciones (además de las del historial de este archivo): el negativo de un arreglo va en el mismo SHA con el arreglo vaciado; cada número del informe sale de un log; un ancho en `ch` depende de la fuente: medir con Inter y con Liberation Sans (`fuente/arial.conf`); una regla de pantalla se mide en cada ancho de disposición, no sólo a 1280; un sabotaje que falla en el primer elemento de una lista no prueba los de atrás: el más exigente va primero; no editar `scripts/` mientras corre un guion de sabotaje: cortar las puertas y relanzarlas sobre el SHA nuevo; `catalogo3.sh` tarda ~80 min, sin tope de 3600 s; puertas con `setsid nohup`; horas, sólo de `date -u`; los comandos para la PM se prueban antes de escribirlos. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica; subagentes hasta esfuerzo alto, sin consejero, nunca Fable; detener los subagentes después de su informe. Letra ancha: tabla U+FF01..FF5E, no NFKC («№» da Noruega).
