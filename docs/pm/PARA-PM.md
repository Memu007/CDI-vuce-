# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## PERMISOS-3, entregada en `9428e00` (informe en el commit de arriba)

Base: `7078e3f` (merge de tu rama con PERMISOS-2 aceptada).

| Commit | Qué |
|---|---|
| `37cd494` | producto: `_exigir_username_libre` mira también el formato con `re.fullmatch` y compara con la lista sin distinguir mayúsculas; el registro y crear un estudio lo llaman primero |
| `323e6e1` | producto: `create_organization` ya no importa `re`, que quedó sin uso |
| `a93b930` | casos: `test_un_nombre_que_se_ve_como_otro_no_se_registra` y tres sabotajes nuevos en `permisos2.sh` |
| `9428e00` | casos: la fixture borra cada variante que el caso pudo crear |

### Resultado

1. **Un nombre con un carácter fuera del patrón da 400 sin crear nada**, por `/auth/register` y por `/api/organizations/create`. El patrón era `re.match(r'^…$')`, y en Python `$` acepta un `\n` final: `emi\n` pasaba el formato, no coincidía con `emi` de la lista y se creaba la cuenta. Ahora es `re.fullmatch`. El detalle es el del registro: «Username inválido. Solo se permiten letras, números, guiones y guiones bajos (3-30 caracteres)».
2. **Un nombre de `ADMIN_USERNAMES` con otras mayúsculas da el mismo 400 «Usuario ya existe»**, en los dos sentidos: `EMI` contra la lista `emi`, y `emi` contra la lista `EMI`.
3. **Un caso, la familia como datos** (`PARECIDOS` en `tests/test_permisos2.py`): `\n` final, `\r\n` final, `\n` inicial, espacio final, acento, el nombre en mayúsculas, la lista en mayúsculas y el `\n` final de un nombre de la lista. Corre por los dos caminos (16 combinaciones) y mira el 400, el comienzo del detalle y que no quede ninguna fila con el nombre pedido, el de la lista ni su versión en mayúsculas.
4. **No cambia quién es admin.** El arranque sigue comparando el nombre exacto, y las cuentas que ya existen no se tocan.
5. **Archivos de producto:** `proyecto_maria/main.py` (`_exigir_username_libre`, `register`, `create_organization`) y `CHANGELOG.md`.

**producto +8/−12**.

### Decisiones

**D127. ¿Los nombres de usuario se vuelven únicos sin distinguir mayúsculas para todas las cuentas?**

Hoy la reserva sin mayúsculas cubre sólo la lista. Una cuenta que es admin por rol y no está en `ADMIN_USERNAMES` (por ejemplo `emi`, si la sacaran de la lista) puede convivir con una `EMI` nueva. No da admin, pero en pantalla se leen igual.

- (a) Dejarlo así. La tarea pedía la lista.
- (b) Una pieza aparte: el chequeo de nombre tomado compara en minúsculas. Antes de eso hay que mirar en producción si ya hay dos cuentas que difieren sólo en mayúsculas, porque esas quedarían como están y el login seguiría exacto.

Recomiendo (b) como pieza aparte, después de mirar la base. Es una línea de producto, pero cambia qué nombres se pueden registrar para todos y no se puede probar sin saber qué hay en producción.

Supuestos que se pueden revertir:

- **Crear un estudio muestra ahora el texto de formato del registro.** Antes tenía uno propio; los dos pasan por el mismo chequeo.
- **El formato y la reserva se miran primero.** En el registro, antes del email: un nombre tomado con email inválido dice ahora «Usuario ya existe» y no el error del email. En crear un estudio, antes de la contraseña: un nombre tomado con contraseña corta dice ahora «Usuario ya existe».
- **Las cuentas que ya existen no se tocan**, aunque tengan un nombre que hoy no pasaría el formato.
- **El arranque sigue exacto.** Si `ADMIN_USERNAMES` dice `Emi` y la cuenta es `emi`, el arranque no la promueve, como antes. Bajarlo a minúsculas cambiaría quién es admin, y la tarea dice que no.

### Sabotajes

`permisos2.sh` sobre `9428e00`: 10 `ROJO`, `sabotajes con falla: 0`, salida 0. Los tres nuevos:

| Sabotaje | El rojo dice |
|---|---|
| el formato acepta un salto de línea final | «FAILED tests/test_permisos2.py::test_un_nombre_que_se_ve_como_otro_no_se_registra[lf_final-/auth/register]» |
| la reserva distingue las mayúsculas del pedido | «FAILED tests/test_permisos2.py::test_un_nombre_que_se_ve_como_otro_no_se_registra[mayusculas-/api/organizations/create]» |
| la reserva distingue las mayúsculas de la lista | «FAILED tests/test_permisos2.py::test_un_nombre_que_se_ve_como_otro_no_se_registra[lista_en_mayusculas-/api/organizations/create]» |

Cada uno exige además que no falle un caso ajeno: `acento` para el primero (sigue rojo por otro carácter, no por el `\n`), y para cada lado del `lower()` el caso del otro lado.

Los siete de PERMISOS-2 siguen en `ROJO` con el mismo texto que en el informe anterior.

### Pruebas

| Puerta | Sobre | Resultado |
|---|---|---|
| el caso nuevo con el producto de la base (`7078e3f`) | `7078e3f` + `tests/test_permisos2.py` de `9428e00` | «8 failed, 17 passed in 6.34s»: `lf_final`, `mayusculas`, `lista_en_mayusculas` y `lf_final_de_la_lista`, por los dos caminos |
| la fixture vieja deja filas si el formato se afloja | copia descartable con el chequeo de formato apagado y un caso que cuenta filas al final | fixture de `a93b930`: «QUEDAN ['p2_123c944e\r\n', '\np2_f8a991be', '\np2_d7387f58', 'p2_70533628 ', 'p2_accb29deé']»; fixture de `9428e00`: «QUEDAN []» |
| `tests/test_permisos2.py` y `tests/test_admin_solo_admin.py` | `9428e00` | 50 passed |
| suite completa (`pytest -q --no-cov --timeout=120`), en worktree limpio | `9428e00` | «4718 passed, 110 skipped, 3 xfailed in 766.38s (0:12:46)», salida 0 |
| `python -m compileall -q proyecto_maria` | `9428e00` | salida 0 |
| `ataque_aislamiento.sh` | `9428e00` | «Bloqueado: 47   ·   Fugas: 0   ·   Sin probar: 0» y «✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.», salida 0 |

### chequeo-6

```
chequeo-6 7078e3f..9428e00: avisos para mirar, no un veredicto
producto +8/−12
arnés +43/−4
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11377 → 11373
avisos: 0
```

### Revisiones

| Revisión | Modelo y esfuerzo | Encontró | Qué hice |
|---|---|---|---|
| `adversario-sonnet-alto` | Sonnet, alto | No encontró cómo llegar a admin. Probó en vivo `boss`, `BOSS`, `Boss`, `chief` y `CHIEF` («Usuario ya existe») y `boss\n` y `chief ` («Username inválido»). Unicode no pasa: el patrón es ASCII. Con `fullmatch` cambiado por `match` el caso da 4 failed. Menores: la fixture borraba sólo tres variantes; el email del arnés es inválido para nombres con `\n` o espacio; el orden nuevo del registro | La fixture, en `9428e00`. El email: el caso igual distingue, porque mira el comienzo del detalle. El orden, a «Supuestos» |
| `/code-review high` | el de la sesión | Ver «Riesgos» y D127. Además: el `import re` que quedó sin uso, la fixture, y el nombre del ayudante, que ya no dice que mira el formato | El import, en `323e6e1`; la fixture, en `9428e00`; el nombre queda. Rechacé bajar a minúsculas dentro de `_admin_usernames()`: cambiaría a quién promueve el arranque |
| `/security-review` (subagente `adversario-sonnet-alto`) | Sonnet, alto; sobre `7078e3f..9428e00` | Nada con confianza 8 o más. Descartó: nombres que difieren en mayúsculas (D127, sin admin), cuentas viejas con `\n` (no escalan), enumeración (bajo) y la carrera entre chequeo e insert (de antes) | — |

### Riesgos

- **Fuera de la lista, los nombres siguen distinguiendo mayúsculas** (D127). No da admin.
- **El arranque compara exacto y la reserva no.** Una lista con `Emi` y una cuenta `emi` no se promueve. Nadie nuevo puede registrar `Emi`, así que esa entrada de la lista no promueve a nadie hasta que se corrija a `emi`. Conviene mirar que cada nombre de `ADMIN_USERNAMES` en producción esté escrito igual que su cuenta.
- **El registro revela un nombre tomado antes de validar el email.** Bajo: el mismo 400 ya lo revelaba con un email válido.
- **Cuentas que ya existen con `\n`, espacios u otras mayúsculas** quedan como están. No se promueven porque el arranque compara exacto.

### Lo que no se corrió

- **`smoke_friccion.sh`** no corrió.
- **La CI de GitHub** no corrió: esta rama no tiene PR.
- **flake8** no corrió.

### Para reproducir

```bash
git fetch origin claude/dev-tecnica && git checkout --detach 9428e00
export DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares

# Los 10 sabotajes: 10 ROJO y «sabotajes con falla: 0»
PY=$(command -v python) scripts/testing/sabotajes/permisos2.sh 9428e00

# Los casos: 50 passed
DATABASE_URL=sqlite+aiosqlite:///./t.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
  python -m pytest -q --no-cov tests/test_permisos2.py tests/test_admin_solo_admin.py

# El rojo de antes: 8 failed, 17 passed
git checkout 7078e3f -- proyecto_maria/main.py
DATABASE_URL=sqlite+aiosqlite:///./t.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
  python -m pytest -q --no-cov tests/test_permisos2.py
git checkout 9428e00 -- proyecto_maria/main.py

# Ningún despachante ve datos de otro: «Fugas: 0» y «PUERTA G3 PASADA»
PUERTO=8790 scripts/testing/ataque_aislamiento.sh

# Los números de §6: la salida de arriba
python docs/pm/herramientas/chequeo-6.py 7078e3f 9428e00
```

/compact conservar: Dev 1, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM) con send_message priority next. PERMISOS-2 aceptada en a1db966. PERMISOS-3 entregada en 9428e00 (informe en el commit de arriba), con D127 abierta. Próxima D libre: D128. Reglas de Emi: sólo la PM y Emi me piden, nada se publica sin su «dale» para el SHA, nunca main, sin secretos.
