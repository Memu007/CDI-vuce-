# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## SUFIJO-BORRADOR (D227): entregada en `ee2ee3c`. Reprodujo en rojo y está arreglada: el sufijo de la operación vuelve a su campo al recargar, también el escrito sin generar y el borrado. El caso de «lo que se está escribiendo no se pisa» prueba los dos campos de ajustes. Dos decisiones: D236 y D237. Un error mío: `4271075` quedó subido con un rojo en `test_valor1c.py`

Integré tu rama hasta `7bae88f` (merge `48cb8ac`). Tus commits propios tocan
sólo `docs/pm/`.

| qué | SHA |
|---|---|
| base (mi informe anterior) | `9ed8b9a` |
| el caso de pantalla, rojo sobre el producto de hoy | `e553641` |
| el arreglo, primera versión (producto + `CHANGELOG.md`) | `03e68bc` |
| los dos campos de ajustes como datos del caso, con su sabotaje | `4271075` |
| integración de tu rama | `48cb8ac` |
| el arreglo después de `/code-review` (producto + `CHANGELOG.md`) | `8c54b99` |
| casos, pantalla de tres renglones y sabotajes | `7c26f5e` |
| el caso del botón mira también que se pidan las cuentas | `ee2ee3c` |
| informe | el commit siguiente |

**El rojo que subí.** `4271075` está en el remoto con
`tests/test_valor1c.py::test_al_entrar_a_validar_no_quedan_las_cuentas_de_antes`
en rojo (`ReferenceError: pintarSufijo is not defined`, `1 failed, 29 passed`):
ese caso extrae `onEnterValidating` y yo había corrido sólo
`test_valor1.py` antes de subir. Lo encontró `/code-review`. Arreglado en
`7c26f5e` (la función real entra en la lista del caso).

## Decisiones

**D236. El sufijo de una operación queda escrito en el campo de la
siguiente.** Venía de antes y no lo cambié. El campo `#sbtSufijoValor` no se
vacía al empezar otra operación en la misma carga de página. Con la operación
B recién empezada: el campo muestra el sufijo de A, las celdas por producto y
«Generar» usan el campo, pero los avisos se piden sin sufijo (la operación B
no lo tiene guardado) y el borrador de B tampoco lo guarda: después de
recargar, el campo aparece vacío.
- (a) dejarlo como está;
- (b) el campo muestra siempre lo que guarda la operación, vacío si no
  guarda nada. Saca la herencia y la copia campo → operación de «Generar»;
- (c) recordar el sufijo por cliente.

Recomiendo (b), como pieza aparte con su caso: el sufijo es un dato de la
operación y hoy B lo hereda sin que nadie lo escriba. Cambia lo que sale en
el TXT de quien hoy cuenta con que quede, por eso no lo hice acá. Si el
despachante cuenta con la repetición, es (c) y va a
`PREGUNTAS-DESPACHANTE.md`.

**D237. `orden1`, caso z22, tiene una carrera del arnés.** En la corrida
entera de pantallas sobre `4271075` dio rojo una vez (detalle en «El rojo de
`orden1`»). No depende de esta pieza: forzada, reproduce igual sobre la base
`9ed8b9a`.
- (a) lo arreglo yo como pieza aparte: z22 espera a que terminen los pedidos
  de avisos de la entrada a «Validación» antes de cerrar la sesión (una
  condición observable, sin espera fija);
- (b) queda anotado como intermitente conocido en
  `REPRODUCCION-ORDEN1-INTERMITENTE-2026-11-13.md`;
- (c) lo toma la Técnica, que tiene los sabotajes de z22 en `orden1b.sh`.

Recomiendo (a): `pantalla_orden1.js` es mío y el cambio no toca lo que z22
comprueba. No lo hice dentro de esta pieza porque es otra causa.

## Resultado

- **Reproduce.** `pantalla_sufijo_borrador1.js` (tres renglones: escrito sin
  generar, generado y devuelto a «Validación», borrado sin generar) sobre el
  producto de `9ed8b9a`:
  - `FALLA: escrito sin generar: se escribió «AA(000123)-AB(000456)», la operación recuperada guarda «» y el campo muestra «»`
  - `FALLA: generado y devuelto a la validación: se escribió «ROJO», la operación recuperada guarda «ROJO» y el campo muestra «»`
  - `FALLA: borrado sin generar: se escribió «», la operación recuperada guarda «ROJO» y el campo muestra «»`
- **El arreglo**, en `proyecto_maria/static/v2/screens/finalize.js`
  (**producto +14/−4**), tiene dos mitades que se necesitan:
  1. al entrar a «Validación» se pinta en el campo el sufijo guardado de la
     operación, antes de la tarjeta del despachante (que lee el campo);
  2. el sufijo se guarda en la operación al escribirlo, en el mismo lugar
     que los dos ajustes (`enlazarValor`), no sólo al apretar «Generar». El
     enlace propio que tenía en `enlazarAvisos` se fue.
- Sobre `7c26f5e` (el caso y el producto no cambiaron después):
  `OK escrito sin generar: el campo muestra «AA(000123)-AB(000456)» después de recargar`,
  `OK generado y devuelto a la validación: el campo muestra «ROJO» después de recargar`,
  `OK borrado sin generar: el campo muestra «» después de recargar`,
  `PANTALLA SUFIJO-BORRADOR OK`.
- **Cada mitad por separado da rojo** (commits descartables, no subidos; la
  pieza no pide revisión fuerte, así que no hay guion de sabotaje propio):
  - sin la llamada `pintarSufijo();`: los tres renglones en rojo, el primero
    `FALLA: escrito sin generar: se escribió «AA(000123)-AB(000456)», la operación recuperada guarda «AA(000123)-AB(000456)» y el campo muestra «»`;
  - sin `sbtSufijoValor` en `campos`: el segundo `OK`; el primero
    `… la operación recuperada guarda «» y el campo muestra «»` y el tercero
    `FALLA: borrado sin generar: se escribió «», la operación recuperada guarda «ROJO» y el campo muestra «ROJO»`.
- **«Volver» en el caso** es la devolución del servidor a «Validación» por un
  sufijo que no acepta («ROJO»): es el camino en el que el borrador sobrevive
  a «Generar». Cuando genera bien el borrador se borra y no hay qué recuperar.
- **`test_lo_que_se_esta_escribiendo_no_se_pisa`** corre los dos campos como
  datos. En `sabotaje_valor1.sh`, tu negativo es `pisa_incluir` (sacar
  `document.activeElement !== incluir`) y espera
  `{'valorIncluir': '99'} != {'valorIncluir': '12'}`; `pisa_lo_que_se_escribe`
  espera el de `valorDeducir`. Antes los dos esperaban el mismo texto.
- **`test_al_escribir_un_ajuste_el_boton_se_esconde_hasta_que_vuelvan_las_cuentas`**
  lleva ahora los tres campos y mira tres cosas: que la operación guarde lo
  escrito, que el botón se esconda y que salgan a pedirse las cuentas nuevas.
  Sin `sbtSufijoValor` en `campos` (sabotaje `sufijo_sin_guardar`):
  `{'sbtSufijoValor': ({}, False, 0)} != {'sbtSufijoValor': ({'sbt_sufijo_valor': '500'}, True, 1)}`,
  `1 failed, 75 deselected`. Con el producto de `9ed8b9a` y con el de
  `4271075` el caso, como estaba en `7c26f5e`, daba el mismo rojo sin el
  contador. Sin `programar();` en el manejador (sabotaje nuevo,
  `sin_pedir_cuentas`):
  `{'sbtSufijoValor': ({'sbt_sufijo_valor': '500'}, True, 0)} != {'sbtSufijoValor': ({'sbt_sufijo_valor': '500'}, True, 1)}`.
  El reloj del pedido corre en el acto dentro del caso: no hay espera.
- Los guiones enteros: `sabotaje_valor1.sh` sobre `ee2ee3c`,
  `OK: los 32 sabotajes dan rojo por la razón esperada`;
  `sabotaje_valor1c.sh` sobre `7c26f5e` (después no cambió nada de lo que
  corre), `OK: los 25 sabotajes dan rojo por la razón esperada`. `anclas_perdidas.py`: igual que sobre la base.

## Lo que cambia además, sin que lo pidieras (supuestos reversibles)

- **Mientras se escribe el sufijo, «Calcular seguro» y «Dejar seguro» se
  esconden hasta que vuelven las cuentas**, igual que al escribir un ajuste.
  El sufijo viaja en el pedido con el que se hacen las cuentas: sin esto, un
  clic en «Calcular seguro» justo después de escribirlo se perdía una vez
  (lo reproduje sobre `9ed8b9a` y sobre `4271075`). Está en `CHANGELOG.md`.
- **Los avisos ven el sufijo que está escrito.** Antes llevaban el del último
  «Generar». El pedido de `POST /generate_maria` no cambia.
- **La operación guarda el sufijo como se escribió, sin recortar espacios.**
  Quien lo usa lo recorta (`buildMariaRequest`, «Generar»).
- **El orden «pintar antes que la tarjeta del despachante» no tiene caso que
  lo fije.** Lo dice el comentario de la línea.

## Revisión adversarial

| quién | sobre | hallazgo | qué hice |
|---|---|---|---|
| `adversario-sonnet-alto` (Sonnet, alto) | `4271075` | baja: un clic en «Calcular seguro» se pierde una vez después de escribir el sufijo | reproducido; arreglado en `8c54b99` |
| | | comportamiento anterior: el campo hereda el sufijo de la operación anterior | D236 |
| `adversario-sonnet-medio` (Sonnet, medio) | `4271075..7c26f5e` | baja, de prueba: sin `programar();` en el manejador todo seguía en verde y los botones quedaban escondidos | reproducido (`106 passed` con la mutación); caso y sabotaje en `ee2ee3c` |
| | | baja, de prueba: con `input.value.trim()` el caso sigue en verde | queda: guardar sin recortar no es un requisito, es lo que hace el manejador compartido |
| | | baja, de prueba: `pintarSufijo` que pinta sólo si el campo está vacío no lo distingue ningún caso | queda: no conozco un camino con el campo lleno y otro sufijo guardado, salvo el de D236 |

Ningún hallazgo de producto en la segunda pasada. No corrió una sonda propia
de navegador ni el pedido de avisos fallando con el seguro calculado: eso lo
leyó. Lo que el primero comprobó sin hallazgo: el pedido de `/generate_maria` es
idéntico entre la base y el arreglo; el sufijo vaciado da «Ingresá el sufijo
de valor SBT. Es obligatorio.»; no hay borrador en el servidor (va en
`localStorage`). No corrió Firefox ni WebKit, ni dos pestañas en un navegador
real.

## `/code-review high` sobre `9ed8b9a..4271075`

Los revisores heredan Fable. Ocho hallazgos:

| # | hallazgo | qué hice |
|---|---|---|
| 1 | `test_valor1c.py` en rojo (`pintarSufijo is not defined`) | arreglado en `7c26f5e` |
| 2 | el campo hereda el sufijo de la operación anterior, y los avisos de la nueva se piden sin él | venía de antes: D236 |
| 3 | un clic en «Calcular seguro» se pierde después de escribir el sufijo | arreglado en `8c54b99`, con su caso |
| 4 | «Generar» copia otra vez el campo a la operación | queda: hace falta mientras D236 sea (a); se va con (b) |
| 5 | guardar el sufijo vivía en el enlace de los avisos | mudado a `enlazarValor` en `8c54b99` |
| 6 | el caso de pantalla no probaba escribir sin sufijo guardado ni borrar | tres renglones en `7c26f5e` |
| 7 | el sabotaje `pisa_incluir` esperaba el mismo texto que `pisa_lo_que_se_escribe` | cada uno espera su campo |
| 8 | `pintarSufijo` pinta sin mirar el foco, y pintaba el valor recortado | la operación ya guarda lo escrito sin recortar; lo que queda va como riesgo bajo, abajo |

## El rojo de `orden1` (z22)

- Corrida entera de pantallas sobre `4271075`:
  `resumen: 32 verdes, 1 rojas: orden1`. En `orden1`, z22:
  `FALLA: page.evaluate: TypeError: Cannot read properties of null (reading 'click')`.
- El servidor registró, en ese orden: `POST /auth/logout 200`,
  `POST /generate_maria/avisos 401`, `GET /?next=%2Fdashboard 200`,
  `POST /auth/login 200`. La pestaña se fue al login porque un pedido de
  avisos llegó con la sesión cerrada; «Generar» ya no estaba en la página.
- **Causa:** al entrar a «Validación» salen dos pedidos de avisos; el segundo
  espera a la lista de estudios. z22 cierra la sesión apenas se habilita
  «Generar», sin esperar ese pedido. Si llega después del cierre, 401. No es
  un defecto del producto: una pestaña con la sesión cerrada tiene que ir al
  login.
- **No depende de la pieza.** z22 sola, 6 veces sobre `9ed8b9a` y 6 sobre
  `4271075`: 12 de 12 en verde. Forzada sobre la base `9ed8b9a` (commit
  descartable que retiene los pedidos de avisos hasta después de salir):
  `FORZADO: avisos retenidos 2, el primero que llega tras salir contesta 401`
  y la misma `FALLA: page.evaluate: TypeError: Cannot read properties of null (reading 'click')`.
- **Lo que no probé:** que el rojo de la corrida entera haya sido exactamente
  ese pedido. El registro del servidor no tiene horas; coincide el orden
  (`/api/estudios 200`, cierre, `avisos 401` por la misma conexión).
- La intermitencia anterior de z22 (`REPRODUCCION-ORDEN1-INTERMITENTE-2026-11-13.md`)
  tenía otra firma: 401 en `GET /auth/current_user`.
- En la corrida entera sobre `ee2ee3c`, `orden1` dio verde.

## Comandos

```bash
S=<carpeta descartable>; PY=<python del entorno virtual>
# rojo: el caso de hoy con el producto de la base (commit descartable)
git worktree add -q --detach $S/wt ee2ee3c
ROJO=$(cd $S/wt && git checkout -q 9ed8b9a -- proyecto_maria/static/v2/screens/finalize.js \
  && git -c user.name=x -c user.email=x@x commit -qm descartable && git rev-parse HEAD)
git worktree remove --force $S/wt
SOLO=sufijo_borrador1 env -u DATABASE_URL -u ENVIRONMENT PY=$PY bash scripts/testing/correr_pantallas.sh $ROJO $S/rojo      # resumen: 0 verdes, 1 rojas: sufijo_borrador1
SOLO=sufijo_borrador1 env -u DATABASE_URL -u ENVIRONMENT PY=$PY bash scripts/testing/correr_pantallas.sh ee2ee3c $S/verde   # resumen: 1 verdes, 0 rojas
# los tres campos de la tarjeta del valor y los dos de «no se pisa»
bash scripts/testing/sabotaje_valor1.sh ee2ee3c <entorno virtual>    # OK: los 32 sabotajes dan rojo por la razón esperada
bash scripts/testing/sabotaje_valor1c.sh ee2ee3c <entorno virtual>   # OK: los 25 sabotajes dan rojo por la razón esperada
```

## Puertas

Todas sobre `ee2ee3c`, una por vez.

| puerta | salida |
|---|---|
| `pytest -q --no-cov --timeout=120` (entera) | `6126 passed, 110 skipped, 3 xfailed, 105 warnings in 1352.71s (0:22:32)` |
| `python -m compileall -q proyecto_maria` | sin salida, sale 0 |
| `correr_pantallas.sh ee2ee3c` (las 33) | `resumen: 33 verdes, 0 rojas` |
| `e2e_maria.sh` | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.` |
| `sabotaje_valor1.sh ee2ee3c` | `OK: los 32 sabotajes dan rojo por la razón esperada` |
| `sabotaje_valor1c.sh 7c26f5e` | `OK: los 25 sabotajes dan rojo por la razón esperada` |
| `anclas_perdidas.py ee2ee3c` | las mismas anclas perdidas que sobre `9ed8b9a`, ninguna nueva |
| grep de historia de §6 sobre `proyecto_maria/` | vacío |

No corrí: `smoke_friccion.sh` ni `ataque_aislamiento.sh` (la pieza no toca
servidor, datos, sesión ni permisos), `/security-review` (lo mismo), Firefox
ni WebKit.

## `chequeo-6`

```
chequeo-6 9ed8b9a..ee2ee3c: avisos para mirar, no un veredicto
producto +14/−4
arnés +173/−135
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/static/v2/screens/finalize.js: 1484 → 1494
  AVISO creció una función de más de 150: proyecto_maria/static/v2/screens/finalize.js:9 <anónima> 1476 → 1486, 3 en su propio cuerpo (§6: lo nuevo va aparte)
avisos: 1
```

- El `AVISO` queda: la función anónima de la línea 9 es el envoltorio del
  archivo entero; toda función de `finalize.js` vive adentro. Lo nuevo va en
  una función aparte (`pintarSufijo`), una llamada y una entrada en `campos`.
- `arnés +173/−135` cuenta también lo que trajo la integración de tu rama
  (casos de la Técnica). Lo mío está en `e553641`, `4271075`, `7c26f5e` y
  `ee2ee3c`.

## Riesgos

- **Bajo: `pintarSufijo` no mira el foco.** La operación sigue cada tecla,
  así que lo que pinta es lo que el campo ya tiene. La diferencia posible es
  un espacio al final: «Generar» guarda el sufijo recortado y, si el servidor
  devuelve a «Validación», el campo queda sin ese espacio. No lo construí.
- En «ready» el borrador ya se borró: si ahí falla algo y se recarga, la
  operación no vuelve. Ya era así; no es de esta pieza.
- Los avisos con el sufijo a medio escribir: mientras se tipea, el servidor
  puede contestar avisos de un sufijo incompleto. Se corrigen solos 400 ms
  después de la última tecla.

## Archivos de producto que toqué

`proyecto_maria/static/v2/screens/finalize.js`, `CHANGELOG.md`.

## Sigo con

**CUIT-GENERAR (D235 a)**: primero los dos rojos.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `7bae88f`). SUFIJO-BORRADOR (D227) entregada sobre `ee2ee3c`, con D236 (campo heredado entre operaciones; recomiendo (b) como pieza aparte) y D237 (carrera de z22 en `orden1`; recomiendo (a)) sin contestar. Pieza activa: CUIT-GENERAR (D235 a), producto con datos, revisión fuerte (§3): primero los dos rojos (un TXT con un CUIT malo ya guardado en el perfil y otro con `cuit_agr` malo), el mensaje dice dónde corregirlo; no tocar que `00000000000` pase `cuit_valido`. Después, los vencidos de `sabotajes-conocidos.txt`, uno por pieza. Próxima D: D238. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, sin secretos ni datos reales, VUCE y Gemini simulados, una corrida por vez, un rojo se diagnostica y no se repite hasta verde, las Devs no usan el consejero ni subagentes de esfuerzo muy alto.
