# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## FRONT-422 (D100): **en curso**: falta el resultado de las dos suites sobre `4dbdb0b` (2026-11-08)

| Qué | SHAs |
|---|---|
| Base | `19b7764` |
| Producto y CHANGELOG | `37ceeed`, `9ee40b8`, `8decbfc` |
| Pruebas y sabotajes | `ca54f74`, `1b93976`, `4dbdb0b` |
| Merge de tu rama (sólo `docs/pm/`) | `038a42d` = `ff88333` traído con merge |
| Informe | el commit `docs:` que sigue a `038a42d` |

**Resultado.** Un 422 de pydantic (`detail` en lista) ya no muestra «[object Object]», el texto en inglés ni un genérico que tapa el motivo. Pasa en las cuatro entradas que leen `detail`:
- `CDI.api` (`app_v2.js`), que usan todas las pantallas del panel, entre ellas revisión y finalizar;
- el login, el registro y el recuperar de la landing;
- el reset de contraseña.

Las cuatro pasan el `detail` por un solo traductor, `static/errores.js`. Dice qué campo falla y por qué, en castellano:
- falta un campo;
- no es JSON;
- no es un objeto;
- no es texto o no es un número;
- es más largo que el tope;
- el `value_error` del backend, sin el «Value error, ».

Si el error viene de una lista, agrega «(ítem N)». Un motivo que no está en esa lista dice «Revisá el campo «x».». Un `detail` de texto se muestra tal cual, como antes.

## Decisiones

**D108. Traducir el 422 en el backend en vez de en el front.** Lo levantó `/code-review`.
- (a) **Recomendada.** Dejarlo como está. Hoy el único `detail` en lista sale de `main.py:490` (el handler de `RequestValidationError`); el adversario lo verificó. Un solo traductor en el front cubre todas las pantallas, con prueba que corre las plantillas reales en node.
- (b) Pieza aparte. El handler de `main.py:490` devuelve `detail` como texto en castellano y `errores.js` queda para el texto.
  - Costo: cambia el contrato de la API para todo cliente que lea la lista. Hay tests viejos que leen `detail[0]["loc"]`; no los conté.
  - Ventaja: un cliente sin este JS (curl, otra app) también lee castellano.

**D107: ya la decidiste (a), ENTORNO-3 después de ENTRADAS-2.** La anoto en mi orden.

Próxima D libre: D109.

**Supuesto reversible.** `CAMPOS` traduce sólo los nombres de los formularios de sesión:
- `username`, `email`, `name` y `password`;
- `new_password` y `current_password`.

Cualquier otro campo se nombra técnico: «el campo «grupo_id»». Ampliar la tabla es una línea por campo.

## Archivos de producto que toqué

- `proyecto_maria/static/errores.js` (nuevo, 55 líneas): `textoDeError(detail, genérico)`.
- `proyecto_maria/static/v2/app_v2.js` (+9): `CDI.api` traduce el `detail` y conserva `status`.
- `proyecto_maria/static/v2/screens/finalize.js` (−11) y `review.js` (−11): su traductor propio sale; usan el común.
- `proyecto_maria/templates/dashboard_v2.html` (+1): carga `errores.js`.
- `proyecto_maria/templates/landing.html` (+3/−5): login, registro y recuperar.
- `proyecto_maria/templates/reset_password.html` (+2/−1): carga `errores.js`; el reset lo usa.
- `CHANGELOG.md`: una entrada.

`producto +73/−31`. Suma 42 líneas netas porque `errores.js` es el único traductor compartido: reemplaza las dos copias que tenían `finalize.js` y `review.js`, y cubre además la landing, el reset y `CDI.api`, que no tenían ninguno.

## Casos

`tests/test_front422.py` pide el 422 real al backend (TestClient) y se lo pasa al arnés `tests/front422_pantalla.js`. Ese arnés corre en node el código real de cada pantalla, cada una con su DOM mínimo:
- `api`: `CDI.api` de `app_v2.js`;
- `landing`: el submit del login de `landing.html`;
- `reset`: el submit de `reset_password.html`.

Devuelve lo que la persona lee. Un caso por causa, `test_el_422_de_pydantic_se_lee_en_castellano`, con estas entradas como datos, cada una en las tres pantallas:

| Entrada | Ruta | Lo que tiene que leer |
|---|---|---|
| `falta_campo` | `/auth/login` `{}` | «Falta el usuario. Falta la contraseña.» |
| `no_es_json` | `/auth/login` `nope` | JSON |
| `tipo_equivocado` | `/auth/login` `username: 1` | texto |
| `no_es_objeto` | `/auth/login` `[1]` | objeto |
| `nombre_largo` | `/auth/register` nombre de 101 | 100 |
| `clave_73_bytes` | `/auth/reset-password` | 72 bytes |
| `no_es_numero` | desagrupar `grupo_id: "x"` | número |
| `sin_texto_propio` | desagrupar `grupo_id: 2**40` | «Revisá el campo «grupo_id».» |
| `item_de_lista` | agrupar `item_ids: ["a", 2, 3]` | ítem 3 |
| `cambio_de_clave` | `/api/user/change-password` `{}` | «Falta la contraseña actual. Falta la contraseña nueva.» |

Cada entrada verifica además:
- que el texto es un `str` y no dice `[object Object]`, `Field required` ni `Input should`;
- que `CDI.api` devuelve `status` 422.

`test_un_detail_de_texto_se_muestra_tal_cual` cubre las tres pantallas con un `detail` de texto. Total: `33 passed`.

## Rojos, copiados de la salida

- **Base `19b7764`, con los casos y sin el producto:** `18 failed, 3 passed, 3 warnings in 1.51s`. El primero:
  `AssertionError: [{'type': 'missing', 'loc': ['body', 'username'], 'msg': 'Field required'}, {'type': 'missing', 'loc': ['body', 'password'], 'msg': 'Field required'}]`.
  Los 3 verdes eran el `detail` de texto, que ya se mostraba bien.
- **Sobre `9ee40b8`, con la entrada `cambio_de_clave` nueva:** `3 failed, 30 passed`, con `assert 'Falta la contraseña actual. Falta la contraseña nueva.' in 'Falta la contraseña.'`.
  - Causa: las dos claves se traducían igual y el `Set` que saca repetidos las juntaba en una.
  - Arreglo: `8decbfc`.
- La ronda de `9ee40b8` (número, ítem de lista, motivo sin texto propio) también tuvo su rojo antes del arreglo. Esa salida no la conservé al compactar el chat, así que no la copio. Sus tres sabotajes de abajo muestran el rojo con el arreglo revertido.

## Puertas (sobre `4dbdb0b`)

| Puerta | Salida |
|---|---|
| `tests/test_front422.py` | `33 passed` |
| `front422.sh 4dbdb0b` | `BASE \| en verde`, 17 `ROJO`, `sabotajes con falla: 0` |
| Suite completa, la mía (`ENVIRONMENT=test`, SQLite), worktree limpio | corriendo; no la doy por verde hasta copiar su salida |
| Suite completa, la de CI (`env -u DATABASE_URL ENVIRONMENT=testing …`), worktree limpio | corriendo; no la doy por verde hasta copiar su salida |
| `chequeo-6.py 19b7764 4dbdb0b` | abajo, 1 aviso (las +42, explicado arriba) |
| grep de historia de §6 sobre `proyecto_maria/` | vacío |
| `/code-review high` y adversario Opus alto | abajo |

```
chequeo-6 19b7764..4dbdb0b: avisos para mirar, no un veredicto
producto +73/−31
  AVISO producto suma 42 líneas netas: el informe dice por qué (§6: más de 20)
arnés +264/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/static/errores.js: nuevo, 55
  proyecto_maria/static/v2/app_v2.js: 1190 → 1199
  proyecto_maria/static/v2/screens/finalize.js: 1436 → 1425
  proyecto_maria/static/v2/screens/review.js: 1186 → 1175
avisos: 1
```

Sabotajes, salida entera:

```
Preparing worktree (detached HEAD 4dbdb0b)
BASE  | en verde
ROJO  | CDI.api deja la lista como llegó: dice «FAILED tests/test_front422.py::test_el_422_de_pydantic_se_lee_en_castellano[api-falta_campo]»
ROJO  | CDI.api devuelve el 422 como un 200: dice «FAILED tests/test_front422.py::test_el_422_de_pydantic_se_lee_en_castellano[api-falta_campo]»
ROJO  | el login tapa el motivo con el texto genérico: dice «FAILED tests/test_front422.py::test_el_422_de_pydantic_se_lee_en_castellano[landing-falta_campo]»
ROJO  | el reset muestra la lista cruda: dice «FAILED tests/test_front422.py::test_el_422_de_pydantic_se_lee_en_castellano[reset-clave_73_bytes]»
ROJO  | sólo se muestra el primer error: dice «FAILED tests/test_front422.py::test_el_422_de_pydantic_se_lee_en_castellano[api-falta_campo]»
ROJO  | el campo se dice con su nombre técnico: dice «FAILED tests/test_front422.py::test_el_422_de_pydantic_se_lee_en_castellano[landing-falta_campo]»
ROJO  | las dos claves del cambio de clave se leen como una: dice «FAILED tests/test_front422.py::test_el_422_de_pydantic_se_lee_en_castellano[reset-cambio_de_clave]»
ROJO  | falta un campo se dice con el msg de pydantic: dice «FAILED tests/test_front422.py::test_el_422_de_pydantic_se_lee_en_castellano[reset-falta_campo]»
ROJO  | un tipo equivocado se dice en genérico: dice «FAILED tests/test_front422.py::test_el_422_de_pydantic_se_lee_en_castellano[api-tipo_equivocado]»
ROJO  | el tope de largo no se dice: dice «FAILED tests/test_front422.py::test_el_422_de_pydantic_se_lee_en_castellano[landing-nombre_largo]»
ROJO  | el value_error conserva el prefijo en inglés: dice «FAILED tests/test_front422.py::test_el_422_de_pydantic_se_lee_en_castellano[api-clave_73_bytes]»
ROJO  | un JSON roto se dice en genérico: dice «FAILED tests/test_front422.py::test_el_422_de_pydantic_se_lee_en_castellano[landing-no_es_json]»
ROJO  | un cuerpo que no es objeto se dice en genérico: dice «FAILED tests/test_front422.py::test_el_422_de_pydantic_se_lee_en_castellano[reset-no_es_objeto]»
ROJO  | un número equivocado se dice en genérico: dice «FAILED tests/test_front422.py::test_el_422_de_pydantic_se_lee_en_castellano[api-no_es_numero]»
ROJO  | dos ítems de una lista se leen como uno: dice «FAILED tests/test_front422.py::test_el_422_de_pydantic_se_lee_en_castellano[landing-item_de_lista]»
ROJO  | un motivo sin texto propio se dice sin concordar: dice «FAILED tests/test_front422.py::test_el_422_de_pydantic_se_lee_en_castellano[reset-sin_texto_propio]»
ROJO  | un detail de texto se reemplaza por el genérico: dice «FAILED tests/test_front422.py::test_un_detail_de_texto_se_muestra_tal_cual[landing]»
sabotajes con falla: 0
SALIDA 0
```

Esta pieza no es de revisión fuerte (§3), pero dejo un script de sabotajes propio, `scripts/testing/sabotajes/front422.sh`, en vez de mostrar un rojo una sola vez. Es porque son 17 reglas de texto, una por motivo. Si preferís que no quede, se saca sin tocar los casos.

## Autorrevisión

| Quién (modelo, esfuerzo) | Hallazgo | Qué hice |
|---|---|---|
| `/code-review high` | 1. Dos ítems de una lista se leían como uno | Arreglado (`9ee40b8`), con su sabotaje |
| | 2. Tipos de pydantic sin texto (números, entre otros) | Números agregados (`9ee40b8`). El resto cae a «Revisá X.»; el CHANGELOG lo dice |
| | 3. `CAMPOS` sólo cubre los campos de sesión | Supuesto reversible, arriba |
| | 4. «X no es válido» no concordaba en género | Arreglado: «Revisá X.» |
| | 5. Un `value_error` en inglés se mostraría en inglés | Queda, R3. Los `value_error` del backend están en castellano |
| | 6. Traducir en el backend | D108 |
| | 7. Traducir dos veces (backend y front) | No: no hay traducción en el backend que se pise |
| | 8. Otras pantallas con su helper propio de error | A la cola de limpieza, propuesto, no dentro del arreglo |
| | 9. `errores.js` sin `?v=` de caché | Queda, R5. Misma convención que `csrf.js` |
| | 10. Script de sabotajes propio en una pieza que no es §3 | Queda, explicado arriba |
| adversario-opus-alto (sobre `ca54f74`) | Ningún hallazgo alto | — |
| | 1. media. No se miraba el `status` que devuelve `CDI.api` | Arreglado en los casos (`4dbdb0b`), con su sabotaje |
| | 2. media. `review.js:1000`, `:1065` y `finalize.js:1129` no se ejercitan: un `ReferenceError` ahí queda verde | Queda, R1 |
| | 3. baja, latente. `CAMPOS[nombre]` sin `hasOwnProperty`: un campo llamado `constructor` o `toString` daría un texto raro | Queda, R2. El backend no tiene campos con esos nombres |
| | 4. baja, latente. `value_error` en inglés | R3 |
| | 5. baja, latente. Un `msg` vacío daría «.» | R3 |
| | 6. baja. «La contraseña no es válido.» | Ya arreglado por «Revisá X.» |
| | 7. baja. `too_long` de una lista dice «caracteres» | R3. Ninguna ruta tiene hoy un tope de largo de lista |
| | 8. baja. `current_password` y `new_password` se leen igual | Arreglado (`8decbfc`), con su caso y su sabotaje |
| | 9. baja. Sacar `CAMPOS` queda verde | Arreglado: el caso pide «el usuario», con su sabotaje |
| | 10. baja. Mostrar sólo el primer error queda verde | Arreglado: el caso pide los dos, con su sabotaje |
| | 11. baja. `CDI.api` depende de que `errores.js` cargue antes | Queda, R4 |

El adversario verificó como bien hechos tres puntos:
- el único `detail` en lista del backend es `main.py:490`;
- el orden de carga de los scripts;
- ningún `innerHTML` recibe este texto: va por `textContent` o por el `toast` que ya escapaba.

Lo que miré y dejé afuera:
- `public_quote.html:223`: `hash` es `str` y no puede dar un 422 de lista.
- `topbar_financials`, `tour` y `dev_dashboard`: no leen `detail`.

## Riesgos

- **R1, media.** Tres lugares de `review.js` (`:1000`, `:1065`) y `finalize.js` (`:1129`) llaman a `textoDeError` y no tienen prueba que los corra. Un error de nombre ahí no lo ve ninguna prueba. Esos módulos dependen mucho del DOM y no hay arnés de node para ellos; armarlo no era proporcional a la pieza. Una mirada en el navegador los cubriría.
- **R2, baja, latente.** Un campo llamado `constructor`, `toString` u otra propiedad heredada daría un texto raro. Hoy no hay ninguno.
- **R3, baja, latente.** El texto en inglés sólo pasa si el backend manda un `value_error` en inglés. Un `msg` vacío daría «.». Un tope de lista diría «caracteres».
- **R4, baja.** Si `errores.js` no carga, `CDI.api` falla con `ReferenceError` en vez de mostrar el genérico.
- **R5, baja.** `errores.js` sin `?v=`: un navegador con caché vieja lo actualiza cuando vence la caché, como `csrf.js`.

## Lo que no corrí

- Ningún navegador real ni capturas. El arnés de node corre el código real de las plantillas con un DOM mínimo, no la página entera.
- Las tres llamadas de R1.
- `smoke_friccion.sh` y `ataque_aislamiento.sh`: no toqué backend, datos, sesión ni permisos.

## Comandos copiables

```bash
# desde la raíz, con el venv del proyecto; necesita node
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
rm -f test.db; python -m pytest -q --no-cov -p no:cacheprovider tests/test_front422.py
#   → 33 passed
PY=$(command -v python) scripts/testing/sabotajes/front422.sh 4dbdb0b
#   → «BASE | en verde», 17 líneas ROJO, «sabotajes con falla: 0»
python3 docs/pm/herramientas/chequeo-6.py 19b7764 4dbdb0b
#   → producto +73/−31, avisos: 1 (las +42)
git grep -n 'object Object' 4dbdb0b -- proyecto_maria/static proyecto_maria/templates
#   → vacío
```

/compact conservar: Dev MARIA (session_01C8gCBjvn36wnYC6qG2Sixi), rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM session_01B7FVQspcEHF7PqNv797wNM con send_message next. FRONT-422 (D100) entregada en 4dbdb0b (base 19b7764), D108 abierta (recomendé a: dejar la traducción en el front), próxima D libre D109. D107 decidida (a): ENTORNO-3 después de ENTRADAS-2. Sigue ENTRADAS-2 (D101, D104) y después ENTORNO-3. Corte de rutinas 2026-11-08 15:50 UTC. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; TXT y proforma reales nunca en el repo.
