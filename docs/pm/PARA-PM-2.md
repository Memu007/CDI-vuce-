# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## AVISOS-2b (arreglo de AVISOS-2): **entregada** en `aa115f4` (2026-11-08), base `8fda3d2`

| SHA | qué |
|---|---|
| `ffd1b95` | fix: el lector y el perfil usan la misma regla de código que el TXT; CHANGELOG |
| `cbe7b76` | test: casos del lector y del perfil, `IC_4` al caso de forma, sabotajes en `avisos2.sh` |
| `9cfe87c` | fix: el lector ya no calcula la destinación que después pisa (hallazgo de `/code-review`) |
| `aa115f4` | test: los sabotajes del lector leen la destinación de `documento` |
| este commit | docs: el informe |

**Producto +14/−7** (7 netas).

La base es `8fda3d2` y no `4db641b`: debajo están los commits de RESET-3
(`3d0083a..8fda3d2`), que ya había empezado cuando llegó tu veredicto. No
están entregados; son lo que sigue (abajo).

**El orden.** Tu canal (`dcf35c6`) dice «AVISOS-2b → RESET-3». Tu mensaje
de las 19:56 decía lo contrario: «cerrala y entregala [RESET-3], y después
AVISOS-2b». Lo leí recién con AVISOS-2b terminada y su suite corriendo. Seguí
el canal. RESET-3 es lo próximo que entrego.

Qué hace:

1. **D133 (a).** `codigo_de_destinacion` (`maria_generator.py`) es la regla:
   cuatro letras o números ASCII después de `strip()`, en mayúsculas, o `""`.
   `destinacion_del_txt` la usa (y da `ValueError` si queda vacía) y el
   lector (`validar_documento_importacion`) también: lo que no es código
   queda vacío y la revisión pone IC04, como con el vacío de hoy. Datos del
   caso: `"\u200b"*65 + "EC01"`, `IC-04`, `IC04 (consumo)`, `\u200bIC04`,
   `ＩＣ０４`, `IC_4` y `\u212aC04` quedan en `""`; ` ic04 ` queda en `IC04`.
2. **D135 (a).** El PUT del perfil pasa el default por `_destinacion_o_400`
   (la misma que los endpoints de importación): `IC041`, `IC0`, `EC01` e
   `IC_4` dan 400 y no cambia nada del perfil (ni el default ni el nombre
   que venía en el mismo pedido); ` ic04 ` guarda `IC04`; `""` lo vacía.
3. **`IC_4`** está en los datos de `test_lo_que_no_es_un_codigo_da_400_y_no_genera`.

Rojo de `cbe7b76` sobre `8fda3d2` (el producto sin arreglar): «19 failed,
62 passed». 14 son del lector y 4 del perfil. El 19.º era el caso del default
vacío, que yo había escrito mal; lo corregí antes de commitear.

**Corrijo a la baja un hallazgo del adversario.** Dijo que un default viejo
guardado antes de este arreglo (`IC04CONSUM`, `EC01`) traba todo guardado
del perfil. Desde la pantalla no pasa: el default es un `<select>`
(`dashboard_v2.html:1476`) con "", IC04, IC05, IT01, ZFI1 y TRAN.
`profile.js:166` lo carga con `p.default_tipo_destinacion || ''`, y un valor
que no está entre las opciones queda en "". Al guardar se manda "", la
respuesta es 200 y el default viejo se borra sin avisar. Ese default ya daba
400 en cada generación desde AVISOS-2. Sólo un cliente de la API que
reenvía el valor viejo recibe 400, y eso es lo que pide D135 (a). Por eso
no lo subo como D.

## Decisiones

**D137. El smoke quedó viejo desde ABUSO-1** (rojo de arriba). No frena
esta entrega.

- (a) El smoke espera el rechazo sin sesión en los dos eventos (lo que hace
  el producto hoy) y sigue con `by-cuit`. Sólo cambia el script.
- (b) El smoke inicia sesión con un usuario que crea para eso y manda los
  eventos con sesión.
- (c) Se retira y queda lo que cubre la suite.

Recomiendo **(a)**: es un cambio chico de script, no necesita credenciales
y vuelve a dar una señal verde o roja que signifique algo. (b) necesita un
usuario y una clave en el script. Si decís (a) o (b), lo hago como pieza
chica después de RESET-3.

Siguen abiertas:

- **D131**, de EMAIL-1: va a Emi.
- **D136**: no traigo tu rama hasta que me avises que INTEGRAR-1 está
  aceptada.

Supuestos que podés rechazar:

- Un invisible solo (`\u200b`) como default del perfil da 400, no vacía el
  default: `strip()` no lo saca y no es un código.
- `ABCD` o `1234` se aceptan en el perfil y en el lector: son la regla de
  AVISOS-2 (cuatro letras o números), no una lista de destinaciones.

## Comandos

```bash
git checkout aa115f4
# negativos de AVISOS-2 y 2b: «BASE | ... 155 passed», 16 ROJO, «sabotajes sin rojo: 0»
PY=python scripts/testing/sabotajes/avisos2.sh aa115f4
# negativos de AVISOS-1, que comparten es_exportacion: «BASE | ... 151 passed», 22 ROJO, «sabotajes sin rojo: 0»
PY=python scripts/testing/sabotajes/avisos1.sh aa115f4
# producto +14/−7, «avisos: 0»
python docs/pm/herramientas/chequeo-6.py 8fda3d2 aa115f4
# los casos de la pieza solos: 0 failed
python -m pytest -q --no-cov tests/test_avisos2.py
```

Los cuatro sabotajes nuevos de `avisos2.sh`, cada uno con lo que dice su rojo:

| sabotaje | dice |
|---|---|
| el lector pasa la destinación sin mirar la forma | `FAILED tests/test_avisos2.py::test_el_lector_deja_vacio_lo_que_no_es_un_codigo[IC_4--pymupdf]` y `…[IC-04--pdf_directo]` |
| el lector mira la forma del texto ya en minúsculas | `FAILED …test_el_lector_deja_vacio_lo_que_no_es_un_codigo[\u212aC04--pymupdf]` |
| el perfil guarda el default sin mirar la forma | `FAILED tests/test_avisos2.py::test_el_perfil_solo_guarda_un_codigo_de_importacion[IC041-400-IC05]` y `…[IC_4-400-IC05]` |
| el perfil guarda una exportación | `FAILED …test_el_perfil_solo_guarda_un_codigo_de_importacion[EC01-400-IC05]` |

## Puertas

Todo sobre `aa115f4`, desde un worktree limpio.

| puerta | salida exacta |
|---|---|
| suite completa (`pytest -q --no-cov --timeout=120`) | `==== 5432 passed, 335 skipped, 3 xfailed, 98 warnings in 1052.07s (0:17:32) ====`, salida 0 (AVISOS-2 había dado 5406 passed) |
| `compileall -q proyecto_maria` | sin salida, `compileall 0` |
| `smoke_friccion.sh` contra uvicorn local (entorno de test) | **rojo**: `[FAIL] POST /api/ui/event`, salida 1. Igual sobre `8fda3d2`: no es de esta pieza (abajo y D137) |
| `avisos2.sh aa115f4` | `BASE  \| ======================= 155 passed, 5 warnings in 28.67s =======================`; 16 `ROJO`; `sabotajes sin rojo: 0` |
| `avisos1.sh aa115f4` | `BASE  \| ====================== 151 passed, 17 warnings in 10.91s =======================`; 22 `ROJO`; `sabotajes sin rojo: 0` |
| `chequeo-6.py 8fda3d2 aa115f4` | `avisos: 0` (abajo, entera) |
| grep de historia de §6 | vacío |

**El rojo del smoke.** El endpoint contesta
`{"ok":false,"detail":"Evento sin sesión no admitido"}`: es el rechazo que
agregó ABUSO-1 (`a3abd92`), y el smoke (último cambio en `b88da9c`) sigue
mandando el evento sin sesión. Lo levanté sobre `8fda3d2` con el mismo
entorno y da el mismo `[FAIL] POST /api/ui/event`. Los otros dos pasos los
corrí a mano en los dos SHAs: `/api/session/state` da el mismo rechazo y
`by-cuit` da `401`, como pide el smoke. Ninguno de los tres pasos toca lo que
cambió esta pieza. Desde ABUSO-1 nadie lo había corrido: los informes y las
reproducciones lo declaran no corrido.

**No corrido:**

- `ataque_aislamiento.sh`: la pieza no toca datos de otros, sesión ni
  permisos.
- `/security-review` con subagentes, como lo pide el skill. La pieza toca el
  perfil, y por eso lo hice, pero a mano y en la sesión, sin subagentes. Sin
  hallazgos:
  - sólo achica lo que se acepta (`[A-Z0-9]{4}` o vacío);
  - el texto del 400 es fijo;
  - el front lo muestra con `textContent`.

## Hallazgos de la autorrevisión

| quién | modelo y esfuerzo | hallazgo | qué hice |
|---|---|---|---|
| `adversario-sonnet-alto` | Sonnet, alto | un default viejo que no es código traba todo guardado del perfil (media) | corregido a la baja, arriba: sólo pasa por la API; desde la pantalla se borra en silencio |
| ídem | ídem | el perfil acepta tipos que no son texto: `true` guarda `TRUE` y `1234` guarda `1234` (baja) | riesgo, abajo |
| ídem | ídem | `true` en el lector queda `TRUE` (baja) | riesgo, abajo |
| ídem | ídem | `ABCD` y `1234` se aceptan (informativo) | es la regla; supuesto, arriba |
| ídem | ídem | `\u200b` solo ahora da 400 en el perfil (informativo) | supuesto, arriba |
| `/code-review high` sobre `8fda3d2..cbe7b76` | el de la sesión, alto | la destinación que calculaba la comprensión del lector quedó muerta: se pisaba siempre | arreglado en `9cfe87c`; los sabotajes que dependían de ella, reescritos en `aa115f4` (los dos dan rojo) |
| ídem | ídem | `IC-05` en el lector queda vacío y la revisión pone IC04, no IC05 | riesgo, abajo (ya previsto en D133) |
| ídem | ídem | 65 invisibles + `EC01` en el lector terminan como IC04 | riesgo ya decidido en D133 (a) |
| ídem | ídem | el default viejo traba el perfil | igual que el primero del adversario |
| ídem | ídem | el 400 del perfil se muestra en el lugar del error del CUIT (`profile.js:264`) | riesgo, abajo |
| ídem | ídem | con `EC01` el mensaje del perfil habla de «TXT de importación» | riesgo, abajo |
| ídem | ídem | doble `strip()` en `destinacion_del_txt` | queda: es una línea y no cambia nada |
| ídem | ídem | doble normalización en el perfil (`strip()` antes y `_destinacion_o_400` después) | queda: el `strip()` decide si se vacía |

## Riesgos

- Hasta que se decida D137, `smoke_friccion.sh` da rojo en cualquier SHA
  desde ABUSO-1, y no distingue nada.

- Un `IC-05` (o similar) que lee el modelo se pierde: la revisión pone IC04
  y la persona tiene que elegir IC05 a mano. Es lo que decidiste en D133 (a).
- El 400 del perfil aparece donde se muestra el error del CUIT
  (`profile.js:264`). Desde la pantalla no se puede provocar: el select sólo
  manda códigos válidos.
- Con `EC01` por la API, el mensaje dice lo mismo que en la generación de
  importación («TXT de importación»), aunque se esté guardando el perfil.
- Por la API, un `true` o un `1234` como default se guardan como `TRUE` y
  `1234`. Son cuatro letras o números, así que el TXT los acepta igual que
  antes de esta pieza.
- No hay migración: un default viejo que no es código sigue en la base hasta
  que la persona guarde el perfil desde la pantalla.

## chequeo-6

```
chequeo-6 8fda3d2..aa115f4: avisos para mirar, no un veredicto
producto +14/−7
arnés +57/−10
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/maria_generator.py: 2341 → 2347
  proyecto_maria/main.py: 12085 → 12086
  proyecto_maria/pdf_extractor.py: 2893 → 2893
avisos: 0
```

## Archivos de producto

`proyecto_maria/core/maria_generator.py`, `proyecto_maria/main.py`,
`proyecto_maria/pdf_extractor.py`.

## Lo que sigue

RESET-3 (D132 a, el tope de pedidos de reset por cuenta) ya está en la
rama, debajo de esta pieza (`3d0083a..8fda3d2`, base `2fba5c9`), y subido.
No lo entregué todavía: lo cierro con `/entregar` y te aviso.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (send_message next, «Dev MARIA: …»), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. AVISOS-2b entregada en aa115f4 (informe en este archivo, base 8fda3d2); abiertas D131 (de EMAIL-1, va a Emi) y D136 (decidida: no traigo tu rama hasta que INTEGRAR-1 esté aceptada); D137 abierta (el smoke viejo); la próxima D libre es la D138. Sigue la entrega de RESET-3 (3d0083a..8fda3d2, base 2fba5c9, ya subido), después OBSERVABILIDAD-1, ORG-1+D40 y D102. Nunca main, nada se publica sin el «dale» de Emi para el SHA, sin secretos, sólo datos inventados.
