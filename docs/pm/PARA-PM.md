# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ORDEN-1: entregada en el commit de este informe (código en `0d89c20`)

| Qué | SHA |
|---|---|
| Producto: arrastrar también los grupos y un borrador por pestaña | `82cea39` |
| Pruebas: TXT reordenado, subítems juntos, recarga, dos pestañas, arnés de pantalla y sabotajes | `e610881` |
| Pruebas: el arrastre que no arranca y la pestaña que toma la operación ajena se ven por su motivo | `d4d3b41` |
| Pruebas: sabotaje de la numeración corrida | `0d89c20` |
| Merge de tu rama (`fb11735`, sólo `docs/pm/`) | `dbba4b2` |
| Informe | este commit |

Diff de revisión: `git diff 69f7441..0d89c20 -- . ':!docs/pm' ':!.claude'`
(8 archivos, +882 −55). Archivos de producto para «Quién hace qué»:
`proyecto_maria/static/v2/app_v2.js`, `proyecto_maria/static/v2/screens/ncm.js`,
`proyecto_maria/static/v2/screens/upload.js` y `CHANGELOG.md`. No toqué
`maria_generator.py` ni nada del servidor.

**Resultado: los 14 sabotajes en rojo por su motivo; el TXT reordenado es el
original salvo el orden, con los subítems juntos y la numeración corrida;
recargar y dos pestañas conservan orden y productos. Una F en la suite que no
es de esta pieza (el `test_excel2` que ya me pasaste). `/code-review`,
`/security-review` y adversarios no corridos (sin presupuesto).**

El informe de GUARDAR-2 sigue en `cb42e8f`.

## Decisiones

**D1. Dónde vive el orden «guardado».** La tarea dice «guardar con otro orden
y volver a abrir conserva el orden». En v2 nada reabre una operación desde el
servidor: `OperationItem` (`models.py:239`) no tiene columna de posición, su
`id` es un UUID, el CSV sale con `.order_by(OperationItemModel.id)`
(`main.py:7614`) y las pantallas v2 (`despachante.js:97`, `clientes.js:1489`)
sólo listan operaciones. Hoy «volver a abrir» es el borrador del navegador.
- (a) El orden vive en el borrador local de cada pestaña (lo que entregué). Recargar, cerrar y volver a abrir el navegador lo conservan; otra computadora no.
- (b) Columna `posicion` en `OperationItem`, con migración, y que el guardado la escriba. Sirve el día que una pantalla reabra operaciones desde el servidor. Hoy nadie la leería.
- **Recomiendo (a)** hasta que exista «reabrir del servidor»; (b) sin quien la lea es una migración sin uso.

**D2. «El Excel» no existe en v2: contradigo la premisa.** El único Excel de
la operación sale de `POST /process_operation/` (`main.py:3238` →
`create_maria_excel`, `main.py:3282`) y sólo lo llama la pantalla vieja
(`static/app.js:1092` y `:3186`). v2 genera el TXT, que sí sigue el orden.
- (a) Se da por cumplido con el TXT y la tabla.
- (b) Pieza aparte: un Excel de la operación en v2, con el mismo orden.
- **Recomiendo (a)** y que (b) entre al roadmap sólo si Emi lo pide. Si «el Excel» era otra cosa, decime cuál y lo cubro.

**D3. El centavo del flete con dos FOB iguales depende del orden.** `repartir()`
(en `maria_generator.py`) le da el centavo que sobra al primero; si se
reordenan dos ítems con el mismo FOB, el centavo cambia de ítem. El total no
cambia. Lo dejé como xfail
(`test_con_dos_fob_iguales_el_flete_de_cada_item_no_depende_del_orden`).
- (a) Queda así: el TXT sigue siendo válido y suma igual.
- (b) Pieza para la Dev MARIA: desempatar por algo estable (por ejemplo, la posición original o la pieza).
- **Recomiendo (a)**: no es un error de importe y tocar el reparto pide sus propias pruebas.

## Qué faltaba y qué hice

Comprobé la premisa antes de tocar: **el arrastre de un producto suelto ya
existía** en la tabla de `ncm.js`, y el TXT ya sale en el orden de los
productos, con los subítems juntos («orden de su primer renglón») y los
`NARTEXT` corridos. Supuse que «la pantalla de revisión» es esa tabla. Lo
que faltaba, con su rojo sobre `69f7441` (`rojo-69f7441.log`):

| Hueco | Rojo en la base |
|---|---|
| El grupo (MARIA-8) no se podía arrastrar | «FALLA: el grupo no tiene de dónde arrastrarlo» |
| Ctrl+Z justo después de arrastrar volvía el orden de antes | «FALLA: Ctrl+Z después de arrastrar vuelve el orden de antes: ["Equipo demo","Cable demo","Mouse demo"]» |
| Con dos pestañas, la segunda tomaba la operación de la primera | «FALLA: la segunda pestaña tomó la operación de la primera, que sigue abierta» |
| Una pestaña en la carga de archivos borraba la operación de otra | «FALLA: la pestaña que quedó en la carga de archivos borró la operación cerrada: se recupera null» |

El arrastre suelto y la recarga ya daban OK en la base; su rojo sale por
sabotaje.

Cambios:
- **`ncm.js`:** el grupo se arrastra entero desde su número (con `⋮⋮`) y se
  puede soltar sobre él, abierto o cerrado. Se mueven unidades (un producto
  suelto o un grupo entero), armadas con `buildRenderRows`, así que un grupo
  no se parte. Arrastrar anula el Ctrl+Z pendiente.
- **`app_v2.js`:** el borrador pasa a ser uno por pestaña
  (`cdi_v2_state:<id de pestaña>`, con fecha y si la pestaña se cerró). Al
  abrir, una pestaña recupera el suyo; si no tiene, adopta el más reciente
  cerrado o abandonado hace más de 3 minutos, nunca uno de una pestaña viva.
  La clave vieja (`cdi_v2_state` sin id) se lee como cerrada, así que nadie
  pierde lo que tenía al publicar.
- **`upload.js`:** empezar otra operación borra sólo el borrador de esa pestaña.

## Puertas

Suite sobre `e610881`, todo lo demás sobre `0d89c20`. Entre los dos sólo
cambiaron `scripts/testing/pantalla_orden1.js` y
`scripts/testing/sabotajes/orden1.sh`, que pytest no recoge. Los logs están
en mi scratchpad.

| Puerta | Salida |
|---|---|
| Suite desde worktree limpio (`suite-orden1.log`) | `= 1 failed, 3886 passed, 102 skipped, 3 xfailed, 95 warnings in 471.89s (0:07:51) =` |
| `compileall -q proyecto_maria` | salida 0 |
| `tests/test_orden1.py` | `24 passed, 1 xfailed, 3 warnings in 0.30s` |
| `node tests/test_doc1_upload.js` | `DOC-1 upload: 11 synthetic scenarios OK (state, rejection, races, client, catalog, draft, Excel).` |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| `pantalla_orden1.js` (Chromium) | `OK: ORDEN-1 en el navegador`, con las 6 líneas OK de abajo |
| `ataque_aislamiento.sh` (sobre `d4d3b41`, mismo producto) | `Bloqueado: 22   ·   Fugas: 0`, `✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.` |
| `sabotajes/orden1.sh 0d89c20` (`sab-orden1c.log`) | 14 ROJO, `sabotajes sin rojo: 0` |

Pantalla:
```
OK dos pestañas cerradas: al abrir otras dos se recuperan ORD-B y ORD-A
OK una pestaña en la carga de archivos no borra la operación que otra dejó a medias
OK arrastrar con el mouse cambia la tabla, el pedido y el TXT: 8544.42.00.900E · 3921.90.19.900Z · 8471.49.00.100D; las dos lonas, un ítem con dos subítems
OK el grupo se arrastra entero y se puede soltar sobre él, abierto o cerrado
OK recargar enseguida de arrastrar conserva el orden
OK Ctrl+Z después de arrastrar no deshace el orden
```

Sabotajes (uno por motivo):
```
ROJO  | el generador no sigue el orden de los productos: dice «FAILED tests/test_orden1.py::test_el_txt_reordenado_es_el_original_salvo_el_orden_de_los_items»
ROJO  | los renglones de la misma posición no se juntan (subítems separados): dice «FAILED tests/test_orden1.py::test_los_subitems_quedan_juntos_bajo_su_item»
ROJO  | el ítem de la posición sale en su último renglón: dice «FAILED tests/test_orden1.py::test_el_txt_reordenado_es_el_original_salvo_el_orden_de_los_items»
ROJO  | los ítems no quedan numerados corridos: dice «FAILED tests/test_orden1.py::test_los_items_quedan_numerados_corridos»
ROJO  | empezar otra operación borra el borrador de todas las pestañas: dice «AssertionError [ERR_ASSERTION]: another tab keeps its draft»
ROJO  | empezar otra operación borra la clave vieja y no el borrador de la pestaña: dice «AssertionError [ERR_ASSERTION]: reload cannot restore A draft»
ROJO  | todas las pestañas guardan en la misma clave: dice «FALLA: con dos pestañas abiertas no quedan guardadas las dos operaciones»
ROJO  | una pestaña nueva toma la operación de otra que sigue abierta: dice «FALLA: la segunda pestaña tomó la operación de la primera, que sigue abierta»
ROJO  | la pestaña que queda en la carga borra el borrador de todas: dice «FALLA: la pestaña que quedó en la carga de archivos borró la operación cerrada»
ROJO  | soltar no reordena: dice «FALLA: arrastrar el cable arriba de todo deja»
ROJO  | el número de la fila no se puede arrastrar: dice «FALLA: el producto no tiene de dónde arrastrarlo»
ROJO  | el grupo no se arrastra: dice «FALLA: el grupo no tiene de dónde arrastrarlo»
ROJO  | al irse no se guarda el orden recién arrastrado: dice «FALLA: al recargar enseguida vuelve el orden de antes»
ROJO  | Ctrl+Z después de arrastrar vuelve la lista de antes: dice «FALLA: Ctrl+Z después de arrastrar vuelve el orden de antes»
```

Los sabotajes del generador se aplican sólo dentro del worktree descartable.

**La F de la suite** es la que me pasaste para después de ORDEN-1:
```
FAILED tests/test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal
E   AssertionError: la subida normal dio 400 a los 30.1 s: {"detail":"No pudimos abrir el Excel: tardó demasiado. Probá con otro archivo."}
```
Corrido solo, en la misma máquina: `normal: 200 en 30.1 s`, `1 passed`. Además,
la suite compartió la CPU con los sabotajes. ORDEN-1 no la toca: el único
`.py` del diff es `tests/test_orden1.py`. El diagnóstico va en la pieza
siguiente.

**Rojos del arnés que arreglé antes de entregar.** La primera corrida sobre
`e610881` (`sab-orden1.log`) dio `sabotajes sin rojo: 3`: tres `ROJO?` (en
rojo, pero sin el texto esperado) en «una pestaña nueva toma la operación»,
«el número de la fila no se puede arrastrar» y «el grupo no se arrastra». Había
dos causas:
- el arnés no esperaba a que la primera pestaña guardara sus borradores;
- un arrastre que no arrancaba seguía como si hubiera arrancado.

En `d4d3b41`, el arnés espera esos borradores y `arrastrar()` falla si no hay
un `dragstart` sin cancelar. `0d89c20` suma el sabotaje de la numeración.

## Comandos

```bash
git checkout 0d89c20
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov tests/test_orden1.py     # 24 passed, 1 xfailed
node tests/test_doc1_upload.js                         # DOC-1 upload: 11 synthetic scenarios OK (...)
PY=$(command -v python) PUERTO=8853 scripts/testing/sabotajes/orden1.sh 0d89c20   # 14 ROJO, «sabotajes sin rojo: 0»
# pantalla sola, con una API local levantada en BASE_URL (ENVIRONMENT=development):
BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_orden1.js       # «OK: ORDEN-1 en el navegador»
```

`orden1.sh` levanta su propia API con SQLite en un directorio temporal y
borra su worktree al terminar.

## No corrido

- `/code-review high`, `/security-review` y los adversarios: sin presupuesto
  para subagentes hasta las 18:00 UTC de hoy (son las 02:11). Si hay vuelta
  después, los corro.
- El ataque corrió sobre `d4d3b41`, no sobre `0d89c20`. Entre los dos
  cambiaron sólo scripts de prueba.
- Arrastrar con el dedo (táctil) y con el teclado: no lo probé. Hoy el arrastre
  es sólo con mouse, como ya era antes.
- Los arneses viejos de pantalla que también tocan el arrastre: no los
  corrí; ya estaban rotos antes de esta pieza.

## Observaciones (no las cambié)

- La pantalla no junta en una sola fila los renglones de la misma posición
  (MARIA-8); el TXT sí. La numeración de la pantalla (filas) no es la del TXT
  (ítems).
- Reordenar dos renglones de la misma posición cambia el orden de sus
  `[SBT]` dentro del ítem. Es lo que se espera de «el orden que queda», pero
  es el único cambio del TXT que no es mover un ítem entero.
- Si los miembros de un grupo estaban separados en la lista, el primer
  arrastre los deja contiguos, como ya se ven en la tabla.

## Riesgos

- **Táctil y teclado:** sin arrastre, como antes.
- **Borradores en el navegador:** uno por pestaña. Los de pestañas cerradas
  que nadie adopta no vencen; con muchas operaciones a medias, se puede llenar
  la cuota de `localStorage` (y entonces no se guarda el borrador, como ya
  pasaba con uno solo).
- **Dos pestañas nuevas que se abren a la vez** pueden adoptar el mismo
  borrador abandonado: queda duplicado, sin pérdida.
- **Duplicar una pestaña** copia su id de pestaña: las dos escriben la misma
  clave, como pasaba con todas antes de esta pieza.
- **Pestaña congelada más de 3 minutos** (el navegador la suspende) o vuelta
  desde la caché de atrás/adelante: otra pestaña puede adoptar su operación.
  Al volver, la primera guarda otra vez la suya; queda duplicada, sin pérdida.
- **Cerrar dos y abrir una sola** recupera la más reciente; la otra queda
  guardada pero oculta hasta abrir otra pestaña.
- **Otro usuario en el mismo navegador** puede adoptar un borrador abandonado
  del anterior. Ya pasaba con la clave única.
- **`filaDe` de `despachante.js`** busca la fila por posición: no lo toqué.
- Al arrastrar hacia abajo, la línea que marca dónde cae (`border-top`) se
  dibuja arriba de la fila de destino, pero el producto queda debajo de
  ella. Hacia arriba coincide. Las pruebas comprueban el orden que queda, no
  la línea.
- Un aviso que aparece mientras se arrastra puede mover la tabla.
- `gid` va sin escapar en el HTML de la fila del grupo (ya estaba así; viene
  del propio armado de grupos).
- La CI no corre `tests/test_doc1_upload.js`.
- `test_excel2` sin margen respecto al corte de 30 s: es la pieza siguiente.

/compact conservar: Dev técnica (Dev 1), sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica, rutina trig_011UpBfwEu9TUzoNUrviqoP5 (/respondio horaria); aviso a la PM principal session_01B7FVQspcEHF7PqNv797wNM con send_message priority next («Dev técnica: …»). ORDEN-1 entregada: código 0d89c20 (producto 82cea39; pruebas e610881, d4d3b41, 0d89c20), D1–D3 abiertas. GUARDAR-2 (cef45ce) en revisión: si vuelve, primero. Siguiente: diagnóstico del rojo de test_excel2 (ocho libros) con una D, sin subir el corte de 30 s ni aflojar la prueba. Reglas: sólo pide la PM o Emi; nada se publica sin el «dale» de Emi para el SHA; nunca main ni push --force; sin secretos ni datos reales; subagentes hasta alto, nunca Fable, sin presupuesto hasta 2026-10-28 18:00 UTC.
