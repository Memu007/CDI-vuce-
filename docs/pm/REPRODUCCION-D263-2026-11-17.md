# D263: reproducción de la PM

Entrega `9e5960d2` (informe `b039eabb`, canal `PARA-PM-2.md`). Base `d363fb38`. Producto:
`maria_generator.py`. `origen_de(item)` da el primero escrito entre `pais_origen` y `origen`, con `strip`.
Lo usan la validación, la clave de posición, la defensa del grupo, el generador y los supuestos «sin
procedencia» y «sin estado». Se fueron los dos `'CN'` de respaldo.
Veredicto: **aceptada sobre `9e5960d2`**.

## Corrido por la PM (2026-11-17, hasta las 11:50 UTC)

| Qué | Resultado |
|---|---|
| `chequeo-6.py d363fb38 9e5960d2` | producto +19/−13, arnés +77/−5, historia vacía, `avisos: 0`, como en el informe |
| el caso sobre `9e5960d2` | `1 passed` |
| rojo con el arreglo revertido (producto de `d363fb38`) | `1 failed`, «('4340', 'CN'): ['4340']» |
| suite completa sobre `9e5960d2` | `6200 passed, 110 skipped, 3 xfailed`, salida 0 |
| `e2e_maria.sh` sobre el SHA | «E2E MARIA OK…», salida 0 |
| `sabotajes/origen_txt.sh` (copia del SHA) | 4/4 `ROJO`, «sabotajes sin rojo: 0» |
| `sabotaje_maria3.sh` (copia del SHA) | «OK: los 32 sabotajes dan rojo por la razón esperada» |
| `sabotaje_maria4.sh` (copia del SHA) | «OK: los 8 sabotajes dan rojo por la razón esperada» |
| `sabotaje_maria8.sh` (copia del SHA) | «OK: los 70 sabotajes dan rojo por la razón esperada» |
| `sabotajes/catalogo3.sh` (copia del SHA) | `rc=0`, «fallas: 0» |
| anclas perdidas, `d363fb38` y `9e5960d2` | 1 en las dos (`limpieza1.sh:135`, `timeout-minutes: 20` de `ci.yml`), igual; 2586 → 2590 anclas medidas |
| `git diff 9e5960d2 b039eabb` | sólo `docs/pm/PARA-PM-2.md` |

## Cada lugar de `origen_de`, revertido de a uno

Cada lugar vuelve a su expresión de la base, los otros cinco quedan: la validación a
`item.get('origen')`; el generador y la clave de posición a `pais_origen or origen` (con `'CN'` de
respaldo); la defensa del grupo y los dos supuestos a `pais_origen or origen`. Ninguno con `strip`.
Corren los 50 archivos de prueba que tocan el generador, con `-x`.

| lugar revertido | con las pruebas | entrada que lo distingue (mía, `9e5960d2` → revertido) |
|---|---|---|
| validación | rojo: el caso de la Dev; también con `pais_origen or origen` sin `strip` («  »/BR da «Origen no reconocido '  '») | |
| generador | rojo: el caso de la Dev | |
| clave de posición | verde (2641 passed) | tres de la misma posición, un CN, `pais_origen` en blanco con `origen` BR, y un BR: 2 ART [310, 203] → 3 ART [310, 203, 203] |
| defensa del grupo | verde (2641 passed) | el mismo par BR con `grupo_id` g1: 200 → 400 «Grupo g1: todos los ítems deben tener el mismo origen» |
| supuesto «sin estado» | verde (2641 passed) | `pais_origen` en blanco, `origen` AR, procedencia AR: sin aviso de estado → aviso «…se declaró 2…» |
| supuesto «sin procedencia» | verde (2641 passed) | `pais_origen` en blanco sin `origen`: sin aviso → aviso de procedencia. Con `origen` BR los dos avisan igual |

Cada verde cambia de resultado con una entrada que manda la API y no la pantalla (un `pais_origen` en
blanco). El de «sin procedencia» sólo con un origen que falta, que es la familia de D269.
`origen_txt.sh` ancla el `strip` dentro de `origen_de`, para los seis a la vez, no cada lugar.
Decidido por la PM: estas cuatro filas van como criterio de D269. Al aceptarla, en cada lugar se cambia
`origen_de(item)` por la lectura sin `strip` (`pais_origen or origen`), de a uno, y falla la fila de
ese lugar.

El informe dice que la clave de posición queda cubierta por
`test_supuestos_leen_el_origen_como_el_generador` (`tests/test_maria4_despachante.py:78`). No lo
sostiene: ese caso lee el aviso de estado con `pais_origen` «CN», y la clave revertida quedó verde.

## Negativos míos por el endpoint (`/generate_maria`), base → `9e5960d2`

Ítems sueltos: `pais_origen` «4340», «ATLANTIDA» o en blanco con `origen` válido, y `pais_origen`
válido sin `origen`, dan lo mismo que el caso de la Dev. En cada 200, `CARTPAYORI` es el valor
validado. Renglones que se juntan y grupos (`grupo_id`), con «Celular Samsung», misma posición:

| ítems (`pais_origen`/`origen`) | base | `9e5960d2` |
|---|---|---|
| automático: BR/CN + CN | 200, [310, 203, 310] | igual |
| automático: BR/CN + BR/AR | 200, [310, 203] (juntos) | igual |
| automático: 4340/CN + CN | 200 con `4340` en el TXT | 400, «Item 2: Origen no reconocido '4340'» |
| automático: CN + 4340/CN | 200 con `4340` | 400, ítem 3 |
| grupo: BR/CN + BR | 200, [310, 203] | igual |
| grupo: BR/CN + CN | 400, «Grupo g1: todos los ítems deben tener el mismo origen» | igual |
| grupo: 4340/CN + CN | 400, error del grupo | 400, «Item 2: Origen no reconocido» |
| grupo: en blanco/BR + BR | 400, error del grupo (rechazo de más) | 200, [310, 203] |

El arreglo vale también en grupos y renglones juntos, y corrige dos defectos de la base.

## Adversario (Opus alto, sin red, `GEMINI_API_KEY` vacía)

No encontró una entrada por `/generate_maria` que saque un origen distinto del validado, ni 310 en
silencio. Lo que dejó:
1. `/generate_maria/avisos` toma un origen vacío o «XX» como China (310) en el aviso de renglones
   juntos y en el de estado. Ya estaba en la base. Se alcanza desde la pantalla: `finalize.js` manda
   «XX» con el origen en blanco. Generar frena con «Origen no reconocido 'XX'», así que no llega al
   TXT, pero el aviso engaña. **Va como pieza de MARIA (D269).**
2. `generate_maria_txt` llamada sin validar escribe 310 (D268, abajo).
3. Cambios que sólo ve quien manda `pais_origen` por la API: la pantalla no lo manda
   (`finalize.js` arma el ítem campo por campo). En cada caso, el TXT trae el valor validado.
4. El caso cubre el ítem suelto; grupos y renglones juntos no tienen caso en `tests/` que distinga
   `origen_de`. Mis negativos de arriba lo muestran una vez, no lo anclan. Va con D269 (arriba).

## Unidad (riesgo escrito de la Dev)

La unidad se lee con la misma cadena `unidad or unidad_medida or um` en los seis lugares, y la
validación no la revisa. `unidad="  "` con `unidad_medida="KG"` sale 07, pero con el aviso «la unidad
no se reconoce y se declaró 07». La pantalla manda sólo `unidad` (`despachante.js`, `unidadesDe`).
Decidido por la PM: riesgo escrito, no pieza.

## Decidido por la PM

- **D268** (el generador no se defiende solo): riesgo escrito, no pieza. El único llamador
  (`main.py`, `/generate_maria`) valida antes; no hay camino de hoy. Si aparece otro llamador, su
  pieza lleva la validación.
- **Cambios por API:** aceptados. Son correcciones: el TXT dice lo que se validó.
- **Sub-ítems:** el origen de un sub-ítem se ignora sin aviso; ya pasaba y la pantalla no lo manda.
  Riesgo escrito.

## No corrido

- `e2e_maria.sh` sobre la unión con mi rama: mi rama sólo cambia `docs/pm`, así que el producto es el
  del SHA.
- `despacho1b.sh` y `catalogo_largo2.sh` (Postgres): no anclan nada de lo tocado.
