# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## PERMISOS-2, entregada en `a1db966` (informe en el commit de arriba)

Base: `bc5d6b4`. El código está en `a1db966`, un merge de tu rama que trae `75942ce` y sólo toca `docs/pm`. El informe va en el commit de arriba.

| Commit | Qué |
|---|---|
| `0d65cc3` | producto: `_es_admin` mira sólo el rol, el registro y crear un estudio rechazan un nombre de la lista, el arranque lee los roles con `roles_de` |
| `6fa309f` | casos: `tests/test_permisos2.py` y los de `test_admin_solo_admin.py` que esperaban lo de antes |
| `052ec48` | `permisos2.sh` |
| `2082647` | producto: el comentario de quién es admin cambia sólo lo que cambió |
| `3076947` | `aislamiento2.sh` sigue la línea nueva de `_es_admin`; en `admin2.sh` sale un sabotaje que ya no distingue nada (abajo, «Decisiones»); el rechazo del registro exige su texto |
| `ae8d844` | merge de tu rama (`docs/pm`) |
| `2c0f73e` | el caso de cobro que pediste y su sabotaje en `cobro_mp4.sh` (punto 1 de la tarea; sin cambio de producto) |
| `f6d62cc` | `ataque_aislamiento.sh` frena si no pudo crear al administrador |
| `a1db966` | merge de tu rama (`docs/pm`) |

COBRO-MP-4 (con D124): leí que la aceptaste sobre `0fb991c`, sin integrar. SEGURO-2, sobre `d160738`.

### Resultado

1. **El caso de cobro (punto 1).** `test_si_falla_la_suya_la_duena_no_concilia_ni_toca_la_que_paga`: la dueña con sid propio que no paga y otra cuenta autorizada; falla el PUT de la dueña, la respuesta es 503 y la que paga sigue `authorized`. Con el desempate invertido (`key=lambda c: (c is db_user, paga[c])`) da rojo (abajo). Para que distinga, el GET falla recién después del PUT: si falla antes, cancelar corta antes de ordenar y el caso queda verde con o sin el sabotaje.
2. **PERMISOS-2.**
   - `_es_admin` es `"admin" in roles_de(user)`. Estar en `ADMIN_USERNAMES` ya no alcanza.
   - El registro (`/auth/register`) y crear un estudio (`/api/organizations/create`) rechazan un nombre de la lista con el mismo 400 «Usuario ya existe» que un nombre tomado. Los dos usan un solo chequeo, `_exigir_username_libre`, que reemplaza el de nombre repetido que tenía cada uno.
   - **La cuenta que ya existe sigue siendo admin al reiniciar.** El arranque le pone el rol a la cuenta de la lista, como hasta ahora; ahora lee los roles con `roles_de`, así que también los arregla si estaban guardados como texto o como otro formato. El caso registra la cuenta sin la lista, comprueba 403, pone el nombre en la lista y levanta la app dos veces con el arranque entero (`with TestClient(main.app)`): da 200 las dos veces y `admin` queda una sola vez. Corre con roles `None`, `[]`, `["operador"]`, `"administrador"` y `{"admin": False}`.
   - El CHANGELOG dice cómo sumar un admin nuevo: que se registre primero, después agregar su nombre a la lista y reiniciar.
3. **Archivos de producto:**
   - `proyecto_maria/main.py`: `_es_admin`, `_exigir_username_libre` (nueva), `register`, `create_organization` y el arranque (`lifespan`);
   - `CHANGELOG.md`.

**producto +15/−15**.

### Decisiones

Nada para decidir. Supuestos que se pueden revertir:

- **En `admin2.sh` saqué el sabotaje «cohort-retention vuelve a pedir el rol».** Buscaba un caso que esta pieza cambió: antes, estar en la lista sin el rol tenía que entrar; ahora tiene que dar 403. Con la regla nueva ese sabotaje no distingue nada. Lo que cubría lo cubre ahora el primer sabotaje de `permisos2.sh`.
- **`ataque_aislamiento.sh` frena si no pudo crear al administrador** (`f6d62cc`). Antes descartaba la respuesta del registro: si fallaba, el ataque seguía y daba sus resultados sin admin. La tarea no lo pedía.
- **Que el arranque arregle roles guardados como texto u otro formato** tampoco lo pedía la tarea. Sin eso, una cuenta de la lista con `roles` guardado como `"administrador"` quedaba sin admin después de esta pieza, porque `roles_de` no ve `admin` ahí y el arranque de antes no lo sumaba.

### Sabotajes

`permisos2.sh` sobre `6fa309f`: 7 `ROJO`, `sabotajes con falla: 0`.

| Sabotaje | El rojo dice |
|---|---|
| ADMIN_USERNAMES vuelve a dar admin sin el rol | «FAILED tests/test_admin_solo_admin.py::test_en_admin_usernames_sin_el_rol_no_entra» |
| el registro deja pasar un nombre de la lista | «FAILED tests/test_permisos2.py::test_un_nombre_de_admin_usernames_no_se_registra[solo-/auth/register]» |
| crear un estudio deja pasar un nombre de la lista | «FAILED tests/test_permisos2.py::test_un_nombre_de_admin_usernames_no_se_registra[en_una_lista-/api/organizations/create]» |
| el chequeo compartido no reserva la lista | «FAILED tests/test_permisos2.py::test_un_nombre_de_admin_usernames_no_se_registra[en_una_lista-/auth/register]» |
| el arranque no pone el rol | «FAILED tests/test_permisos2.py::test_la_cuenta_de_admin_usernames_sigue_siendo_admin_al_reiniciar[None]» |
| el arranque mira roles como texto o clave | «FAILED tests/test_permisos2.py::test_la_cuenta_de_admin_usernames_sigue_siendo_admin_al_reiniciar[roles4]» |
| el arranque suma admin aunque ya lo tenga | «FAILED tests/test_permisos2.py::test_la_cuenta_de_admin_usernames_sigue_siendo_admin_al_reiniciar[roles2]» |

`cobro_mp4.sh` sobre `2c0f73e`: `BASE  | en verde`, 9 `ROJO`, `sabotajes con falla: 0`, salida 0. El nuevo:

| Sabotaje | El rojo dice |
|---|---|
| el desempate pone primero a quien pide, antes que a la que paga | «FAILED tests/test_cobro_mp2.py::test_si_falla_la_suya_la_duena_no_concilia_ni_toca_la_que_paga» |

Los sabotajes de admin de piezas anteriores, porque esta pieza cambia la línea que rompían:

- `admin2.sh` sobre `2082647`: 4 `ROJO`, `sabotajes con falla: 0`.
- `aislamiento2.sh`, sólo el ataque de admin, sobre `ae8d844`: «ROJO  | admin: cualquier usuario es administrador: «FUGA  | Beto en GET /api/admin/stats/summary»», `sabotajes con falla: 0`, salida 0.

### Pruebas

| Puerta | Sobre | Resultado |
|---|---|---|
| suite completa (`pytest -q --no-cov --timeout=120`) | el código de `a1db966` (corrió sobre `f6d62cc`; `a1db966` sólo suma `docs/pm`) | «4702 passed, 110 skipped, 3 xfailed in 745.02s (0:12:25)», salida 0 |
| `python -m compileall -q proyecto_maria` | `a1db966` | salida 0 |
| `ataque_aislamiento.sh` | `f6d62cc` | «Bloqueado: 47   ·   Fugas: 0   ·   Sin probar: 0» y «✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.» |

### chequeo-6

```
chequeo-6 bc5d6b4..a1db966: avisos para mirar, no un veredicto
producto +15/−15
arnés +227/−28
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11377 → 11377
avisos: 0
```

### Revisiones

| Revisión | Modelo y esfuerzo | Encontró | Qué hice |
|---|---|---|---|
| `adversario-opus-alto` | Opus, alto | No encontró cómo entrar como admin sin el rol. Riesgos: el arranque es ahora la única vía y sus errores se tragan; una cuenta con un nombre de la lista registrada antes de esta pieza sigue recibiendo el rol; el 400 deja ver qué nombres están en la lista | Van a «Riesgos» |
| `/code-review high` | el de la sesión | Dos sabotajes rotos: `aislamiento2.sh` buscaba la línea de `_es_admin` que saqué y `admin2.sh` un caso que cambié. El arranque traga los errores y un commit que falla saltea los nombres que siguen. El nombre tomado antes de esta pieza. El ataque no miraba si se creó el administrador. El caso del 400 no miraba el texto. Repetición de ayudantes en el arnés y diez arranques más en la suite | Los sabotajes, en `3076947`; el ataque, en `f6d62cc`; el texto del 400, en `3076947`. Lo del arranque y el nombre tomado, a «Riesgos». Los ayudantes y los arranques quedan: son pocos y el caso tiene que mostrar el arranque entero |
| `/security-review` (subagente general) | Opus, alto; sólo leyó código | Nada con confianza 8 o más | — |

### Riesgos

- **Si falla el arranque, Emi puede quedar sin admin.** El rol lo pone sólo el arranque, dentro del mismo `try` de los usuarios de prueba, que traga el error y escribe «⚠️ Error creando usuarios demo»; si falla un commit, los nombres que siguen no se procesan. Pasa sólo en el primer arranque después de esta pieza, si la cuenta de Emi todavía no tiene el rol guardado: ahí recibiría 403. Una vez guardado, el rol queda. Antes de publicar conviene mirar en la base que su cuenta tenga `admin` en `roles`, o mirar el log del primer arranque («promovido a admin via ADMIN_USERNAMES»).
- **Un nombre de la lista registrado por otro antes de esta pieza** sigue recibiendo el rol en cada arranque. Esta pieza sólo frena los registros nuevos. Conviene mirar que cada nombre de `ADMIN_USERNAMES` en producción sea una cuenta conocida.
- **Sacar un nombre de la lista no le saca el rol.** Hay que sacarlo de `roles` a mano.
- **El 400 deja ver qué nombres están en la lista**: registrar uno da «Usuario ya existe» aunque nadie lo tenga. Es el mismo texto que un nombre tomado.
- **El chequeo compara el nombre tal cual llega.** Un nombre con espacios o un salto de línea no coincide con el de la lista; tampoco lo encontraría el arranque, así que no da admin.
- **Los usuarios de prueba** (sólo fuera de producción) siguen con su propio chequeo de roles, que no pasa por `roles_de`.

### Lo que no se corrió

- **`aislamiento2.sh` entero** no corrió: sólo el ataque de admin, que es el que toca esta pieza.
- **`cobro_mp2.sh`** no corrió: el caso nuevo vive en `test_cobro_mp2.py` y su sabotaje está en `cobro_mp4.sh`.
- **La CI de GitHub** no corrió: esta rama no tiene PR.
- **flake8** y **`smoke_friccion.sh`** no corrieron.

### Para reproducir

```bash
git fetch origin claude/dev-tecnica && git checkout --detach a1db966
export DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares

# Los 7 sabotajes de esta pieza: 7 ROJO y «sabotajes con falla: 0»
PY=$(command -v python) scripts/testing/sabotajes/permisos2.sh a1db966

# El caso de cobro y su sabotaje: 9 ROJO, el de «el desempate pone primero a quien pide»
PY=$(command -v python) scripts/testing/sabotajes/cobro_mp4.sh a1db966

# Los casos nuevos: todos passed
DATABASE_URL=sqlite+aiosqlite:///./t.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
  python -m pytest -q --no-cov tests/test_permisos2.py tests/test_admin_solo_admin.py \
  "tests/test_cobro_mp2.py::test_si_falla_la_suya_la_duena_no_concilia_ni_toca_la_que_paga"

# Ningún despachante ve datos de otro: «Fugas: 0» y «PUERTA G3 PASADA»
PUERTO=8790 scripts/testing/ataque_aislamiento.sh

# Los números de §6: la salida de arriba
python docs/pm/herramientas/chequeo-6.py bc5d6b4 a1db966
```

/compact conservar: Dev 1, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM) con send_message priority next. COBRO-MP-4 aceptada en 0fb991c; SEGURO-2 aceptada en d160738. PERMISOS-2 (con el caso de cobro del punto 1) entregada en a1db966 (informe en el commit de arriba). Próxima D libre: D127. Frenar 2026-11-08 15:50 UTC. Reglas de Emi: sólo la PM y Emi me piden, nada se publica sin su «dale» para el SHA, nunca main, sin secretos.
