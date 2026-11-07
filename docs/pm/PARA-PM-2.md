# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ENTRADAS-1: **entregada**. Base `b1e2daf`. SHA entregado `589fd0b` más el informe (2026-11-07)

| Qué | SHAs |
|---|---|
| Rojos antes del arreglo | `7e8bb0d`, `94ef2fa` |
| Producto | `dea64a7` (claves y textos), `5001831` (topes de columna y respuestas de error) |
| Pruebas y negativos | `6a77109`, `9a057b5`, `ddfa3ea`, `589fd0b` |
| Suite completa | `1 failed, 5070 passed, 335 skipped, 3 xfailed in 779.47s`; el rojo es `test_despacho1b.py::test_las_hojas_leidas_antes_del_corte_dan_sus_productos` (avisos «El PDF da demasiado trabajo: leí hasta la hoja 2.»), el intermitente conocido que está en mi cola; solo da `1 passed in 1.18s`. No toca nada de ENTRADAS-1 |
| Merge de tu rama (sólo `docs/pm/`) | `c6265d5` |
| Informe | el commit `docs:` que sigue a `c6265d5` |

**Resultado.** Ningún texto de la familia de la tarea da 500. Lo comprobé en
SQLite (la suite) y en Postgres 16 local (`scripts/testing/entradas1_postgres.py`).

- **Claves nuevas.** Hay un solo validador, `ClaveNueva`, en las cuatro vías:
  reset, cambio de clave, registro y alta de estudio. Rechaza con 422 «La
  contraseña puede tener…» una clave que:
  - trae un surrogate suelto;
  - trae un NUL;
  - pasa de 72 bytes en UTF-8. La de 72 justos entra.

  En los tres casos no cambia nada: el link de reset sigue sirviendo, la clave
  vieja sigue y no se crea la cuenta.
- **Textos del alta.** Un surrogate o un NUL en el nombre o la invitación del
  registro, en el nombre del estudio o en el nombre del perfil se guarda como
  «�», con el `_guardable_en_pg` de la Dev 1 sin tocarlo. Los ítems de
  agrupar pasan por el mismo saneo. Usuario, email y plan ya daban 400 y
  siguen igual.
- **Topes de columna.** En Postgres, un texto más largo que su columna daba
  500:
  - nombre del registro de 101 → ahora 422;
  - nombre del estudio de 201 → ahora 422;
  - email de 101 en registro, alta de estudio, invitación y perfil → ahora 400.

  El justo entra en todos.
- **Cuerpos raros.** Un cuerpo no JSON con bytes que no son UTF-8 (con
  `text/plain`, con formulario o sin tipo), y `NaN`, `Infinity` y `1e999`,
  dan 422 en JSON válido: UTF-8 estricto y sin `NaN`. Agrupar y desagrupar ya
  no leen `request.json()` a mano: un cuerpo que no es JSON, una lista o un
  `grupo_id` enorme dan 4xx.
- **Respuestas de error.** Un 400 que repite texto ajeno con un surrogate
  (por ejemplo `comprador_pais`) era 500 al codificar. Ahora sale escapado y
  es JSON válido.

**Prueba.** `tests/test_entradas1.py` tiene 7 casos, uno por causa, con la
familia como datos (54 parametrizaciones):

1. clave que no se hashea, por vía y por clave mala;
2. clave de 72 bytes;
3. texto del alta;
4. texto más largo que su columna, con su contrapunto;
5. 422 de un cuerpo raro;
6. agrupar y desagrupar con cuerpo raro;
7. 400 con texto ajeno.

El NUL sólo rompe en Postgres, porque conftest ata la suite a SQLite. Ese lado
lo mide `scripts/testing/entradas1_postgres.py`.

## Decisiones

D97 y D98 las decidiste (a); D99 está con Emi. Nuevas:

- **D100. El frontend muestra «[object Object]» con un 422 en lista.** Lo
  encontró `/code-review`. Un 422 de pydantic trae `detail` como lista, y
  algunas pantallas hacen `alert(detail)`. No es nuevo: ya pasaba con
  cualquier 422. Esta pieza suma 422 donde antes había 500, como la clave de
  más de 72 bytes o el nombre largo.
  - (a) Una pieza chica de frontend: una función que muestre `msg` cuando
    `detail` es lista.
  - (b) Que estos 422 salgan como 400 con un texto plano.
  - (c) Dejarlo.

  **Recomiendo (a).** Arregla todos los 422, no sólo los de esta pieza.
- **D101. El alta de estudio acepta una clave más floja que el registro.**
  Pide sólo 8 caracteres, y el registro pide más. Ahora las dos pasan por
  `ClaveNueva`, pero la política de largo y de caracteres no la unifiqué:
  cambia qué claves se aceptan y la tarea no lo pide.
  - (a) Una pieza que use la misma política en las dos.
  - (b) Dejarlo.

  **Recomiendo (a).**
- **D102. `bcrypt` no está fijado en `requirements`.** El tope de 72 bytes
  que rechazamos es el de bcrypt 4.x/5.x. Una versión que cambie la conducta
  (truncar o rechazar distinto) no rompe esta prueba: la regla es nuestra y
  corre antes de bcrypt. Pero sí cambia qué hashes se generan.
  - (a) Fijar la versión.
  - (b) Dejarlo.

  **Recomiendo (a)**, como chore aparte.
- **D103. Queda código muerto en el registro.** `_email_valido` ya deja el
  email limpio y no vacío, así que saqué el `if request.email:`. Quedan otras
  ramas que ya no pueden pasar y un comentario con historia, que no toqué
  para no mezclar limpieza con arreglo (§6).
  - (a) A la cola de limpieza.
  - (b) Dejarlo.

  **Recomiendo (a).**

- **D104. Hay 500 previos con texto o números raros fuera de esta pieza.**
  Los encontró el adversario y los reprodujo en Postgres local. Ninguno lo
  causa esta pieza:

  | Severidad | Dónde | Qué pasa |
  |---|---|---|
  | media-alta | `POST /api/operations/manual` | `cantidad` `NaN` o `1e999`: 500 después del commit. Queda guardado `total_value=nan`, y desde ahí `GET /api/operations` y `/api/clientes/{id}/operaciones` dan 500 para ese usuario, para siempre. Probablemente también descuenta cupo (no lo medí) |
  | media | la misma ruta | NUL o surrogate en `descripcion` o `pieza`: 500 en Postgres |
  | media | `POST /api/clientes` y `/api/clientes/public` | NUL o surrogate en `nombre`: 500 en Postgres |
  | media-baja | operación manual | `grupo_id` 99999999999: 500 por desborde de int32 |
  | media-baja | `POST /api/clientes/{id}/operaciones` | `NaN` en `items` o `resumen`: 500 (JSON inválido) |
  | baja | `name` del perfil, `email` de clientes | `NaN` se guarda como el texto «nan» o «inf» |

  - (a) Una pieza nueva después de ENTORNO-2: operación manual y clientes,
    con la misma regla (números finitos, texto guardable, rango int32).
  - (b) Sólo riesgo (R5).

  **Recomiendo (a)**, empezando por la operación manual: deja al usuario sin
  ver sus operaciones y no se arregla solo.

Próxima D libre: D105.

## Supuestos y cambios de conducta (reversibles)

- **S1.** Un NUL o un surrogate en un texto que no es clave (nombres,
  invitación, ítems) se guarda como «�» y no se rechaza. Es lo que ya hace
  `TextoCodificable` en el resto de la app. Una clave sí se rechaza, porque
  sanearla en silencio cambiaría la clave del usuario.
- **S2.** Un 422 del registro no cuenta para su límite por IP. El límite corre
  dentro de la ruta y el 422 sale antes. Antes ese pedido daba 500 y tampoco
  sumaba bien.
- **S3.** El 400 que repite texto ajeno lo devuelve escapado: un NUL sale
  como `\u0000` y un surrogate como su escape. No lo sanea a «�», para que el
  mensaje diga lo que llegó.
- **S4.** El alta de estudio, la invitación y el perfil validan el email con
  la misma regla del registro (`_email_valido`), con tope de 100. El perfil
  antes no tenía tope y su mensaje era «Email no válido». Ahora es «Email no
  válido. Debe tener formato usuario@dominio.com». Por eso cambió una
  aserción en `tests/test_user_profile_coverage.py`, que ahora usa
  `startswith`.
- **S5.** El 422 ya no trae el campo `input`, porque puede ser la clave, bytes
  sueltos o un `NaN`. Busqué en `proyecto_maria/static` y en los templates, y
  nadie lo lee.
- **S6.** El registro ahora exige email. Ya lo exigía el modelo, y la rama
  `if request.email:` no podía ser falsa. No cambia la conducta.

## Rojo antes del arreglo

- **SQLite**, en `7e8bb0d` con los 36 casos de entonces:
  `22 failed, 14 passed in 9.52s`. Entre los rojos está
  `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff`.
- **Postgres.** Con el `main.py` de la base, la prueba da `fallas: 15` de 20.
  Las 15 que fallan:
  - la clave con NUL se acepta con 200 en las cuatro vías;
  - el NUL da 500 en registro.name, registro.invite_token, estudio.name,
    estudio.email, perfil.name y agrupar.item_ids;
  - un texto más largo que su columna da 500 en registro.name 101,
    registro.email 101, estudio.name 201, estudio.email 101 y perfil.email 101.

  Con HEAD da `fallas: 0`, las 20 OK.
- **Casos sumados después de `7e8bb0d`.** Su rojo lo muestran los sabotajes,
  más abajo, y la corrida de Postgres sobre la base.

## Negativos

`scripts/testing/sabotajes/entradas1.sh 589fd0b` corre en un worktree
descartable con SQLite propia. Da `BASE  | en verde`, 22 líneas `ROJO  |`,
cada una con el caso exacto que tiene que caer, y `sabotajes con falla: 0`.
Hay uno por regla:

- las cuatro vías de la clave;
- el tope de 72 bytes y su borde;
- los caracteres que no se guardan;
- cada texto del alta;
- cada tope de columna;
- el email del perfil y su nombre;
- agrupar sin modelo;
- desagrupar sin tope del entero;
- el 400 en UTF-8 estricto y con la respuesta común;
- el 422 que repite `input`.

Cada patrón aparece una sola vez en `main.py`; si no, el script dice `ROTO`.

## Autorrevisión

| Quién (modelo, esfuerzo) | Rango | Hallazgos | Qué hice |
|---|---|---|---|
| adversario-sonnet-alto | `b1e2daf..6a77109` | Surrogate dentro de un detail en lista; texto más largo que la columna da 500; agrupar y desagrupar leen el cuerpo a mano | Los tres arreglados en `5001831`, con casos en `ddfa3ea` |
| adversario-opus-alto | `b1e2daf..6a77109` | NUL sólo visible en Postgres; dos mecanismos de codificación | Prueba de Postgres; un solo `_JSONConTextoAjeno` |
| `/code-review high` | `b1e2daf..9a057b5` | 10 hallazgos | La prueba de Postgres corría en SQLite: arreglado en `9a057b5`. Lista no saneada, dos mecanismos, regex del perfil repetida y comentario del NUL equivocado: arreglados en `5001831`. Código muerto del registro: sacado en `5001831`, el resto es D103. Frontend «[object Object]»: D100. Política de clave del estudio: D101. CHANGELOG que decía 422 para «�» y `msg` que repite `input`: cerrados sin cambio, no se reproducen |
| adversario-opus-alto | `b1e2daf..589fd0b`, foco en `5001831` | Sin regresiones en la pieza. Contra Postgres 55432: 8 rutas × 8 cuerpos raros dan 64 respuestas en JSON válido y ningún 500. `allow_nan=False` ya estaba en Starlette, así que no crea 500 nuevos. Agrupar con `item_ids` nulo o enteros pasa de 400/500 a 422; ningún JS del producto llama agrupar ni desagrupar | 6 hallazgos **previos y fuera del diff**, reproducidos por el agente en Postgres: van a D104 y R5. No los arreglé: no son de la familia de la tarea |

## Puertas

| Puerta | Salida |
|---|---|
| Suite completa sobre `589fd0b` | `1 failed, 5070 passed, 335 skipped, 3 xfailed in 779.47s`; el rojo es `test_despacho1b.py::test_las_hojas_leidas_antes_del_corte_dan_sus_productos` (avisos «El PDF da demasiado trabajo: leí hasta la hoja 2.»), el intermitente conocido que está en mi cola; solo da `1 passed in 1.18s`. No toca nada de ENTRADAS-1 |
| `tests/test_entradas1.py` | `54 passed` |
| `python -m compileall -q proyecto_maria` | salida vacía, exit 0 |
| Sabotajes `entradas1.sh 589fd0b` | `sabotajes con falla: 0`, 22 `ROJO` |
| Postgres `entradas1_postgres.py` (55432) | HEAD `fallas: 0`, base `fallas: 15` |
| `smoke_friccion.sh` | **no corrido**: lo cubre la suite (cada ruta tocada tiene su caso con TestClient) y no levanté servidor |
| `ataque_aislamiento.sh` | **no corrido**: la pieza no toca permisos ni qué datos ve cada usuario |

## chequeo-6

```
chequeo-6 b1e2daf..HEAD: avisos para mirar, no un veredicto
producto +60/−33
  AVISO producto suma 27 líneas netas: el informe dice por qué (§6: más de 20)
arnés +500/−1
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11964 → 11991
avisos: 1
```

**Por qué +27.** Estas cuatro cosas no se resuelven sacando código:

- `_JSONConTextoAjeno`, unos 8;
- los modelos `AgruparRequest` y `DesagruparRequest`, que reemplazan el
  `request.json()` a mano;
- los topes de largo;
- la regla de largo del email.

Lo que sí resté: las dos regex de email repetidas (invitación y perfil) pasan
a `_email_valido`, y el `if request.email:` del registro se fue.

## Riesgos

- **R1, media.** Lo de D100: con esta pieza, más pedidos dan 422 en lista. El
  usuario ve «[object Object]» donde antes veía un error genérico de 500.
- **R2, baja.** Un detail con `float('nan')` en una ruta real haría que
  `allow_nan=False` levante y el 4xx se vuelva 500. No encontré ninguna ruta
  que ponga un float en el detail. El adversario lo confirma: Starlette ya
  usaba `allow_nan=False` y el `ctx` de pydantic no trae el `input`, así que
  sólo pasaría si un handler mete un float a propósito.
- **R3, baja.** Un nombre que es sólo `" \x00 "` queda «�». Está fuera de la
  tarea.
- **R4, baja.** Lo de D102: `bcrypt` sin fijar.
- **R5, media-alta.** Lo de D104: un `NaN` en la cantidad de una operación
  manual rompe para siempre la lista de operaciones de ese usuario. Es previo.
- La CI deselecciona tests (CLAUDE.md §5), así que no reemplaza la suite.

## Comandos copiables

```bash
# desde la raíz, con el venv del proyecto
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
rm -f test.db; python -m pytest -q --no-cov -p no:cacheprovider tests/test_entradas1.py
#   → 54 passed
PY=$(command -v python) scripts/testing/sabotajes/entradas1.sh 589fd0b
#   → BASE  | en verde, 22 ROJO, «sabotajes con falla: 0»
python scripts/testing/entradas1_postgres.py postgresql://cdi@127.0.0.1:55462/postgres
#   → 20 OK, «fallas: 0» (con tu Postgres local; crea y borra su propia base)
git diff b1e2daf 589fd0b -- proyecto_maria/ | grep '^+' | grep -E '[A-Z]{4,}(-[A-Z]{2,})*-[0-9]|caso [0-9]'
#   → vacío
```

## Archivos de producto tocados

- `proyecto_maria/main.py`

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP, aviso a la PM session_01B7FVQspcEHF7PqNv797WNM priority next. ENTRADAS-1 ENTREGADA sobre 589fd0b (producto dea64a7/5001831: ClaveNueva única en las cuatro vías, 422 para surrogate/NUL/>72 bytes; textos del alta saneados a «�»; topes de columna 4xx; _JSONConTextoAjeno para 400 y 422). D abiertas: D99 (con Emi), D100 (UI [object Object] con 422), D101 (política de clave del estudio), D102 (fijar bcrypt), D103 (código muerto del registro), D104 (500 previos en operación manual y clientes: NaN, NUL, int32). Próxima D libre D105. Sigue: ABUSO-2 (login bueno de otra cuenta no limpia login:<ip>; tope de recuperar usuario con emails equivalentes en PG, U+0130; revisión fuerte y /security-review) → rojo de despacho1b → ENTORNO-2 (ENVIRONMENT ausente o desconocido se porta como producción en CSRF, cookies, /docs, DATABASE_URL, VUCE y ENABLE_SIMULATE_CHARGE). Reglas de Emi: nada se publica sin su «dale» para el SHA (no propongo SHA), nunca main, nunca force/amend de lo pusheado, sin secretos ni datos reales, subagentes hasta alto sin Fable, no uso advisor, Postgres local 55432.
