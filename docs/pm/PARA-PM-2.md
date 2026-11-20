# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ADMIN-USUARIOS-1 sobre `b06b47fa` (2026-11-20 19:52 UTC)

**Resultado.** Se cumple en `b06b47fa`, contra la base `e5d943e4`.
- `/dev/dashboard` suma una sección «Usuarios» de sólo lectura, con búsqueda por usuario o email y
  páginas de 50.
- La ruta es `GET /api/admin/usuarios`, en `admin_router.py`; `main.py` no se toca. Sin sesión da 401,
  si no es admin da 403, y en ninguno de los dos casos sale un dato.
- `producto +160/−12`. chequeo-6 da un `AVISO`; va abajo con su porqué.
- Toqué tres anclas de dos guiones de otras piezas (`cobro_corte1.sh`, `cobro_mp2.sh`) porque mi cambio en
  `billing_service.py` movió las líneas donde anclaban. Siguen dando rojo (abajo).
- **Para decidir: D278.** El estado de cobro que se ve es el guardado, no el efectivo. Mostrar el
  efectivo pide sacar la regla de `main.py`.

| SHA | qué |
|---|---|
| `63cb1e7a` | feat: la ruta, la sección del panel, `como_utc`/`extra_vencidos` en `billing_service`; CHANGELOG |
| `392bc2b2` | test: `test_admin_usuarios1.py`, la ruta en `test_admin_solo_admin.py`, `pantalla_panel_dev.js` y el guion `sabotajes/admin_usuarios1.sh` |
| `b06b47fa` | test: tres anclas de `cobro_corte1.sh` y `cobro_mp2.sh` siguen a `como_utc` |

Archivos de producto: `routers/admin_router.py`, `services/billing_service.py`,
`templates/dev_dashboard.html`.

## D278 — el estado de cobro que muestra la lista

Hoy la lista muestra `billing_status` como está guardado, más su «hasta» (`trial_ends_at`). Pero el
paso de `trial`/`active` a `past_due` se hace recién cuando la cuenta usa algo
(`_vencer_si_corresponde`, `main.py:2210`, con 7 días de gracia para `active`, `main.py:789`).
Entonces una cuenta que no entra hace semanas puede figurar «active hasta 2026-10-01» cuando ya está
cortada. Calcularlo en la lista sin escribir pide esa regla, y la regla vive en `main.py`, que está
cambiando la Técnica.
- **(a) Recomiendo:** una pieza chica antes de ADMIN-CREDITOS-1 que mueva a `billing_service` el
  predicado («¿esta cuenta ya venció?»), deje que `main.py` lo use, y haga que la lista muestre el
  estado efectivo. Va antes porque, para dar créditos, el admin va a mirar esta lista.
- **(b)** Dejarlo así: se ve lo guardado con su fecha, y el admin lo deduce.

## Qué cambió

- **La lectura** (`admin_router.py:410-465`): un `select` sólo de las columnas que se muestran, sin
  traer objetos del ORM.
  - No hay objeto que guardar.
  - Ningún secreto llega a la ruta: contraseña, `active_jti`, tokens, ids de Mercado Pago y tarjeta no
    se leen.
  - La organización entra con `outerjoin`. Si la cuenta es de un estudio, plan y saldo son los del
    estudio, y `saldo_del_estudio: true` lo dice.
  - Un `organization_id` que apunta a un estudio que ya no está cuenta como cuenta propia, como hace
    `_get_billing_entity` al cobrar.
- **Los vencidos:** `billing_service.extra_vencidos(fecha)` es la regla que ya usaba
  `_expire_extra_ops`, sacada a una función que no escribe. La lista la aplica al saldo de quien paga:
  muestra 0 y sin vencimiento, sin tocar la base.
- **Fechas:** `billing_service.como_utc` lee como UTC una columna sin zona: las que suma la migración de
  arranque son `TIMESTAMP` sin zona, y SQLite no guarda la zona. Ahora la usan `_expire_extra_ops`,
  `vigente` y la lista; antes eran dos copias de la misma regla. La respuesta sale siempre con
  `+00:00`.
- **Búsqueda:** `icontains` con `autoescape`. No distingue mayúsculas, y `%` y `_` cuentan como letras.
  Tiene un tope de 100 caracteres.
- **Páginas:** `desde` (0 a 1 000 000) y `cuantos` (1 a 200, 50 por defecto). Fuera de eso da 422.
  `total` cuenta lo que encuentra la búsqueda.
- **Panel:**
  - las filas se arman con `textContent`;
  - las fechas son el día en la Argentina;
  - las páginas siguen la búsqueda que se pidió, aunque después se cambie el campo;
  - una respuesta que llega tarde no pisa la de un pedido posterior;
  - sin red dice «No se pudo leer» y no muestra páginas.

## La prueba

`tests/test_admin_usuarios1.py` tiene 8 casos. Siembra 8 cuentas y 2 estudios con un prefijo propio.
- Las cuentas:
  - con créditos vigentes;
  - con créditos vencidos;
  - sin créditos;
  - un integrante, que gasta los del estudio;
  - un integrante con los suyos vigentes y los del estudio vencidos;
  - una cuenta cuyo estudio ya no está;
  - una admin por rol guardado;
  - un rol «administrador», que no es admin.
- Cada cuenta y cada estudio llevan secretos con valor único: contraseña, `active_jti`, cancelación,
  recuperación, invitación, ids de Mercado Pago y tarjeta. Se buscan en el texto entero de la
  respuesta, y las claves prohibidas en todo el JSON.
- La foto de la base se saca al sembrar, porque los otros casos también miran, en cualquier orden. Al
  final se compara contra ella, columna por columna, en `users`, `organizations`,
  `password_reset_tokens` e `invitations`.
- La búsqueda corre con `PRAGMA case_sensitive_like = ON`. El `LIKE` de SQLite no distingue
  mayúsculas, el de Postgres sí: sin eso, una búsqueda que distingue daba verde.
- `test_admin_solo_admin.py` recorre las rutas de la app y les pide 401 sin sesión y 403 a un no admin.
  Ahora además exige que `GET /api/admin/usuarios` esté entre ellas.

**Rojo con el producto revertido en el mismo SHA.** Los tres archivos de producto vuelven a
`e5d943e4` sobre `b06b47fa` (`comandos_pm.log`):
```
================== 8 failed, 14 warnings, 27 errors in 2.63s ===================
```
Los 8 son de `test_admin_usuarios1.py`, por un 404. Los 27 son de `test_admin_solo_admin.py`, que
exige la ruta en la app. Con el producto: `35 passed`.

**Guion propio** (`scripts/testing/sabotajes/admin_usuarios1.sh b06b47fa`, `sab3.log`): 27 `ROJO` de
27, `sabotajes sin rojo: 0`, rc=0, cada uno con el caso que nombra. Rompen:
- el permiso: sin `require_admin`;
- el secreto: una clave prohibida, o el id de pago con otro nombre;
- la escritura: mirar vence y guarda, en las cuentas o en los estudios;
- el saldo: vencidos como vigentes, la regla al revés, el vencimiento mirado en la cuenta y no en quien
  paga, el integrante con lo suyo, sin «del estudio», nadie admin, un rol que contiene «admin», un
  estudio que ya no está tomado como estudio;
- búsqueda y páginas: no filtra, sin tope, sin `le=200`, `desde` sin tope, distingue mayúsculas, `%` y
  `_` como comodines;
- fechas: sin zona;
- el panel: HTML, el día de UTC, «Anteriores» y «Siguientes» de más, la página que sigue el campo, sin
  red, la respuesta tardía.

## Puertas sobre `b06b47fa`

| puerta | resultado |
|---|---|
| chequeo-6 `e5d943e4 b06b47fa` | `producto +160/−12`, `avisos: 1` (salida entera abajo) |
| grep de historia de §6 | vacío |
| `admin_usuarios1.sh b06b47fa` | 27 `ROJO` de 27, `sabotajes sin rojo: 0`, rc=0 |
| `panel_dev.sh b06b47fa` | 6 `ROJO` de 6, `sabotajes sin rojo: 0`, rc=0 |
| las tres anclas tocadas, a mano en un worktree de `b06b47fa` | sin sabotaje `220 passed` (`test_cobro_corte1.py` + `test_cobro_mp2.py`); `como_utc`→`pass` en `extra_vencidos`: `FAILED …::test_con_el_tope_lleno_el_extra_paga_la_operacion_nueva`; `vigente`→`return False`: `FAILED …::test_la_cancelada_genera_hasta_el_fin_del_periodo` |
| `anclas_perdidas.py b06b47fa` | `perdida, una línea 1`: `limpieza1.sh:135` (`ci.yml`), igual que en la base `e5d943e4`; `está 2690` |
| sonda en Postgres 16 (servidor real, login real), columnas `timestamptz` y `timestamp` | las dos: `sin sesión 401 · comun 403`; el integrante con el saldo del estudio; vencidos en 0; `buscar JEF: ['jefa']`; `buscar %: 0`; página 2 bien; `base igual antes y después`; `errores en el log: 0`; rc=0 |
| suite completa desde worktree limpio sobre `b06b47fa` | `6241 passed, 110 skipped, 3 xfailed … in 1516.36s (0:25:16)`, rc=0, 0 cambios en el árbol |
| `/code-review` alto | sobre `e5d943e4..702f1961` (ver hallazgos) |
| adversarios Sonnet alto y Opus alto | sobre `e5d943e4..702f1961` (ver hallazgos) |

chequeo-6, salida entera:
```
chequeo-6 e5d943e4..b06b47fa: avisos para mirar, no un veredicto
producto +160/−12
  AVISO producto suma 148 líneas netas: el informe dice por qué (§6: más de 20)
arnés +540/−6
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/routers/admin_router.py: 403 → 465
  proyecto_maria/services/billing_service.py: 418 → 422
avisos: 1
rc=0
```
- **El `AVISO`:** es una función nueva, no un arreglo. Son ≈60 líneas de ruta y lectura en
  `admin_router.py` (+65/−3) y ≈80 de marcado y JS de la sección en `dev_dashboard.html` (+82).
  `billing_service.py` suma 4 netas (+13/−9), porque `como_utc` reemplaza dos copias de la misma
  regla.

No corrí `e2e_maria.sh`: no toqué `static/v2`. Tampoco volví a correr enteros `cobro_corte1.sh` ni
`cobro_mp2.sh`; probé a mano sólo los tres sabotajes cuyas anclas cambié (fila de arriba).

**Lo que no revisaron los adversarios.** Revisaron `702f1961`. Después cambió el producto, por sus
hallazgos: el tope de `desde`, `como_utc` en `_iso` y en `vigente`, `icontains`, y en el panel el
`try` y la respuesta tardía. Eso no tuvo otra pasada adversarial. Lo cubren el guion, la suite y la
sonda de Postgres, corridos sobre `b06b47fa`.

## Hallazgos

| de | modelo y esfuerzo | hallazgo | qué hice |
|---|---|---|---|
| `/code-review` | alto | sin red, `fetch` tiraba y la tabla quedaba como estaba | `try` y «No se pudo leer»; sabotaje «sin red» |
| `/code-review` | alto | una respuesta tardía de otra búsqueda pisaba la última | contador de pedidos; sabotaje «respuesta tardía» |
| `/code-review` | alto | `desde` sin tope daba 500 con un número enorme | `le=1_000_000`, 422; sabotaje |
| `/code-review` y Sonnet | alto | una fecha sin zona salía sin `+00:00`, y el navegador la leía como hora local | `_iso` con `como_utc`; el caso exige `+00:00`; sabotaje |
| `/code-review` | alto | `lower()` en Python y en Postgres no bajan igual todas las letras | `icontains`: las dos minúsculas en la base |
| `/code-review` | alto | el rótulo «51–50 de 50» si se borran cuentas entre dos páginas | queda: riesgo 1 |
| `/code-review` y Opus | alto | el estado de cobro es el guardado, no el efectivo | D278 |
| Sonnet | alto | faltaban mayúsculas, `%` y `_`, y un estudio que ya no está | casos y sabotajes |
| Sonnet y Opus | alto | `get_current_user` guarda el paso a `past_due` del trial vencido de quien pide, y cada pedido suma una fila en `api_logs` | ya pasaba en cada ruta; riesgo 3 |
| Opus | alto | sin un estudio con créditos vencidos, mirar el vencimiento de la cuenta en vez del de quien paga, o vencer y guardar los estudios, daba verde | estudio vencido con integrante vigente; los dos sabotajes dan rojo |
| Opus | alto | `"admin" in str(roles)` daba verde | cuenta con rol «administrador»; sabotaje |
| Opus | alto | un plan guardado «trial» se cobra como Premium (`plan_de_la_cuenta`) y la lista dice «trial» | queda: riesgo 2 |
| guion | — | en SQLite, «distingue mayúsculas» daba verde | `PRAGMA case_sensitive_like` en el caso de búsqueda |
| `anclas_perdidas.py` | — | tres anclas de `cobro_corte1.sh`/`cobro_mp2.sh` perdidas por mi cambio | `b06b47fa` |

Ningún revisor encontró una fuga ni una forma de entrar sin ser admin.

## Supuestos (reversibles)

1. Se ve el estado de cobro guardado, con su «hasta» (D278).
2. Se ve el plan guardado, no el que se cobra (riesgo 2).
3. Una cuenta cuyo estudio ya no está muestra lo suyo, como al cobrar.
4. Páginas de 50, hasta 200; `desde` hasta 1 000 000; búsqueda hasta 100 caracteres.
5. Las fechas del panel son el día en la Argentina; la API las da en UTC con zona.
6. El orden es por usuario.

## Riesgos

1. **Bajo.** Si se borran cuentas entre dos páginas, el rótulo puede decir «51–50 de 50». Una página
   que no trae nada muestra «Ninguno».
2. **Bajo.** Una cuenta con el plan «trial» guardado, de antes, se ve «trial», pero se cobra como
   Premium. Hoy ningún código guarda «trial» como plan. Mostrar lo que se cobra es una línea con
   `plan_de_la_cuenta` y no toca `main.py`. Si querés, entra con D278 (a).
3. **Observación, de antes.** Mirar la lista, como cualquier ruta, guarda una fila en `api_logs`. Si
   quien pide tiene el trial vencido, también le guarda `past_due` (`get_current_user`,
   `auth/dependencies.py:146-153`). Sobre las cuentas listadas no escribe nada.
4. **Observación, de antes.** `/api/billing/me` devuelve `extra_ops_remaining` sin mirar si venció
   (`main.py:3694`). La lista dice 0 y el usuario ve el número viejo hasta su próxima operación.
5. **Observación, de antes.** «Pagos no aplicados», en el mismo panel, muestra el `payment_id` de
   Mercado Pago. La lista de usuarios no lo trae.
6. **Bajo.** En SQLite la búsqueda sólo baja letras ASCII («Ñ» no encuentra «ñ»). En Postgres sí.

## Comandos para vos

Cada uno ya corrido así (`comandos_pm.log`). Cambiá `V` por tu venv:
```bash
cd /home/user/CDI-vuce- && git fetch -q origin claude/dev-maria
V=/tmp/cdi-dev2/venv/bin/python          # tu venv
D=$(mktemp -d) && git worktree add -q --detach $D/wt b06b47fa && cd $D/wt && ln -s "$OLDPWD/config/node_modules" config/node_modules
E="env -u DATABASE_URL -u ENVIRONMENT GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=."
T="tests/test_admin_usuarios1.py tests/test_admin_solo_admin.py"
$E $V -m pytest -q --no-cov -p no:cacheprovider $T | tail -1                 # 1
node scripts/testing/pantalla_panel_dev.js | tail -1                          # 2
git checkout e5d943e4 -- proyecto_maria/ && $E $V -m pytest -q --no-cov -p no:cacheprovider $T | tail -1; git checkout -q HEAD -- proyecto_maria/   # 3
cd - >/dev/null; PY=$V scripts/testing/sabotajes/admin_usuarios1.sh b06b47fa | tail -2      # 4
git worktree remove --force $D/wt
```
Lo que muestra cada uno (unos 3 minutos en total):
1. `35 passed`.
2. `fallas: 0`.
3. Con el producto de la base, `8 failed, … 27 errors`.
4. `ROJO  | «Siguientes» en la última página: …` y después `sabotajes sin rojo: 0`.

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5, rama `claude/dev-maria`; rutina trig_01Ukttby1fc4sGVQfSn1jC9U (/respondio), prendida por la PM. PM principal session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `082b983f`. Aceptadas: las de antes (… CATALOGO-PAIS sobre `8140f496`, D275 (a); ORIGEN-2 sobre `0d7401ed`, D276 (a), D277 (a)); CATALOGO-PAIS-2 (D275 b) sobre `9459a0d4` el 2026-11-20 15:38 UTC, con supuestos 1–3 aceptados y riesgos 1–3 bajos; el vencido de `catalogo_largo2.sh` cerrado con `cbd7718c`. Pieza entregada: ADMIN-USUARIOS-1 sobre `b06b47fa` el 2026-11-20 19:52 UTC (producto `63cb1e7a`, pruebas `392bc2b2` y `b06b47fa`), con D278 abierta (estado de cobro efectivo: mover la regla de `main.py` a `billing_service`, recomendé (a) antes de ADMIN-CREDITOS-1); espero veredicto, sin pieza «apenas entregues». Lo pedido (sí de Emi del 20/11, no es «dale» de publicar): en el panel de admin, sección «Usuarios» de sólo lectura (usuario, email, plan, estado de cobro, operaciones del período, créditos extra vigentes y vencimiento, última recarga, estudio, admin); 401 sin sesión, 403 no admin; nunca contraseña, hash, `active_jti`, tokens, ids de Mercado Pago ni tarjeta; integrante muestra saldo y plan del estudio; mirar no escribe la base (vencidos como 0 sin `commit`); paginado o búsqueda; prueba: todas las rutas de admin dan 403 a no admin sacadas de la app, claves prohibidas en la respuesta entera, base igual después de mirar, rojo con cada arreglo revertido en el mismo SHA y guion de sabotaje propio (§3); puertas: chequeo-6, caso, guion, adversarios Sonnet y Opus alto, suite completa desde base limpia; `e2e_maria.sh` sólo si toco `static/v2`; sugerencia: rutas en `admin_router.py`, no tocar `main.py` (lo cambia la Técnica). ADMIN-CREDITOS-1 (dar créditos) no entra. Próxima D: D279. Lecciones (además de las del historial de este archivo): el negativo de un arreglo va en el mismo SHA con el arreglo vaciado; cada número del informe sale de un log, también las cuentas de líneas («25 ROJO» eran 24); `anclas_perdidas.py <SHA>` después de tocar líneas que anclan sabotajes, también de guiones ajenos, y antes de lanzar la suite (los tests leen los guiones); el `LIKE` de SQLite no distingue mayúsculas: `PRAGMA case_sensitive_like` en el caso; un adversario revisó un SHA: lo cambiado después se dice; un ancho en `ch` depende de la fuente: medir con Inter y con Liberation Sans (`fuente/arial.conf`); una regla de pantalla se mide en cada ancho de disposición; un sabotaje que falla en el primer elemento de una lista no prueba los de atrás; no editar `scripts/` mientras corre un guion de sabotaje: cortar las puertas y relanzarlas sobre el SHA nuevo; un valor puesto por código no dispara `input`; un campo de texto pierde los saltos de línea; puertas con `setsid nohup`; horas, sólo de `date -u`; los comandos para la PM se prueban antes de escribirlos; un borrador con huecos no se sube. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica; subagentes hasta esfuerzo alto, sin consejero, nunca Fable; detener los subagentes después de su informe. Letra ancha: tabla U+FF01..FF5E, no NFKC («№» da Noruega).
