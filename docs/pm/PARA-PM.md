# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CSRF-1, entregada en `b1c9d70` (informe en el commit de arriba)

**Resultado.** Con `CSRF_ENFORCE=true` la telemetría v2 llega: `track()`
manda `X-CSRF-Token` y `/api/session/state` da 200. Antes daba 403. Un pedido
sin token desde otro origen da 403, tanto a la telemetría como a
`/auth/logout`. Cerrar sesión ahora pide el token (D16 b): `/auth/logout`
dejó de estar exento. El botón «Salir» sigue funcionando: lleva al inicio y
`/auth/current_user` da 401. Si el servidor rechaza el cierre, «Salir» lo
avisa y no lleva al inicio con la sesión abierta. Antes daba 403 en silencio,
iba a `/` y la sesión quedaba abierta; lo encontraron el `/code-review` y el
adversario. Producto `+6/−3`, en `main.py` y `app_v2.js`.

### Decisiones

- **D56. Dos clientes más mandan POST sin token y con enforce dan 403.** Ya
  pasaba antes de esta pieza, que no los toca:
  - la telemetría de la landing (`landing.html:561`, `/api/ui/event`), sólo
    cuando la persona tiene sesión abierta;
  - el `/logout` de la pantalla vieja (`app.js:4085`).

  (a) Arreglarlos en esta pieza.
  (b) Pieza aparte, chica.

  **Recomiendo (b).** La tarea nombra la telemetría v2 y el botón de la
  página. Sumar dos pantallas más agranda el diff sin que nadie haya pedido
  ese comportamiento.
- **D57. Una sesión sin la cookie `csrf_token` no se puede cerrar.** La
  cookie sólo se emite en login, register, verify-email y crear
  organización (`main.py:2894`, `3185`, `3243`, `9920`). Tiene el mismo
  `max_age` que `access_token`, así que no medí cuándo falta en la práctica:
  el caso la borra a mano. Sin ella, «Salir» ahora avisa en vez de llevar al
  inicio con la sesión abierta, pero no cierra.

  (a) Dejarlo así: riesgo bajo.
  (b) Pieza aparte: que un GET autenticado vuelva a emitir la cookie si falta.

  **Recomiendo (a), y (b) si aparece en soporte.** No lo hice: es
  funcionalidad fuera de la tarea y toca sesión.

### SHAs (desde `885ee89`)

| SHA | Qué |
|---|---|
| `1a77aae` | test: caso parametrizado `test_enforce_pide_token_a_logout_y_telemetria` (con y sin token, `Origin` de otro sitio), `pantalla_csrf1.js` (la telemetría de la página llega y «Salir» cierra con enforce), `sabotajes/csrf1.sh`, y el ayudante `salir()` de `pantalla_orden1.js` con token |
| `f32ea2f` | fix: `track()` manda el token; `/auth/logout` sale de las exenciones; `CHANGELOG.md` |
| `c01ca26` | test: «Salir» rechazado tiene que avisar (fase nueva en `pantalla_csrf1.js` y sabotaje 5); `test_prelaunch_block1` cierra sesión con token; el PID de la API en la trampa y el aviso si `/health` no contesta, en `csrf1.sh` |
| `b1c9d70` | fix: `logout()` avisa y no navega si el servidor no acepta el cierre; `CHANGELOG.md` |
| (este) | docs: informe |

### Rojos antes, en `885ee89`

Copié el caso y la pantalla de `b1c9d70` sobre un worktree de `885ee89`.

Corrí `pytest tests/test_csrf.py`:

```
FAILED tests/test_csrf.py::test_enforce_pide_token_a_logout_y_telemetria[/auth/logout-False-403]
=================== 1 failed, 10 passed, 5 warnings in 4.79s ===================
```

La fila de la telemetría sin token ya da 403 en la base, porque la ruta ya
exigía el token. Lo que faltaba era que la página lo mandara. Eso lo mide el
navegador.

`pantalla_csrf1.js` con API `CSRF_ENFORCE=true`:

```
FALLA: «Salir» rechazado no avisó y la página fue a /
```

Con la fase de «Salir» rechazado sacada, para ver la telemetría sola:

```
FALLA: la telemetría de la página dio 403
```

Sobre `b1c9d70`, la pantalla completa da `OK: CSRF-1 en el navegador` en la
base de `csrf1.sh`.

### Sabotajes (`csrf1.sh b1c9d70`)

```
ROJO  | cerrar sesión vuelve a estar exento: dice «FAILED tests/test_csrf.py::test_enforce_pide_token_a_logout_y_telemetria[/auth/logout-False-403]»
ROJO  | la telemetría se exenta en vez de mandar el token: dice «FAILED tests/test_csrf.py::test_enforce_pide_token_a_logout_y_telemetria[/api/session/state-False-403]»
ROJO  | la telemetría de la página sale sin el token: dice «FALLA: la telemetría de la página dio 403»
ROJO  | «Salir» sale sin el token: dice «FALLA: «Salir» no llevó al inicio»
ROJO  | «Salir» rechazado lleva al inicio igual: dice «FALLA: «Salir» rechazado no avisó y la página fue a /»
sabotajes con falla: 0
```

### Puertas

| Puerta | Sobre | Resultado |
|---|---|---|
| `csrf1.sh` | `b1c9d70` | dos bases en verde, cinco ROJO con su texto, «sabotajes con falla: 0», salida 0 |
| Suite completa, worktree limpio | `b1c9d70` | `4423 passed, 121 skipped, 3 xfailed, 101 warnings in 643.06s (0:10:43)`, salida 0 |
| `orden1.sh` (usa `salir()` de `pantalla_orden1.js`) | `b1c9d70` | bases en verde, 76 ROJO, «sabotajes sin rojo: 0», salida 0 |
| `orden1b.sh` | `b1c9d70` | base en verde, 28 ROJO, «sabotajes sin rojo: 0», salida 0 |
| `test_prelaunch_block1` + `test_csrf`, con `CSRF_ENFORCE` en `false` y en `true` | `c01ca26` | `55 passed` las dos |
| `smoke_friccion.sh`, API con `CSRF_ENFORCE=true` | `b1c9d70` | `==> OK · telemetría + alias session/state + by-cuit protegido`, salida 0 |
| `compileall -q proyecto_maria` | `b1c9d70` | salida 0 |
| chequeo-6 `885ee89..b1c9d70` | `b1c9d70` | 0 avisos, abajo |
| Historia (grep de §6) | `b1c9d70` | vacío |

No corrí Safari ni Firefox, sólo Chromium. Tampoco corrí
`ataque_aislamiento.sh`: cubre clientes y descargas, y la pieza toca sólo la
exención de `/auth/logout` y dos llamadas de la página.

### chequeo-6

```
chequeo-6 885ee89..b1c9d70: avisos para mirar, no un veredicto
producto +6/−3
arnés +169/−7
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11307 → 11306
  proyecto_maria/static/v2/app_v2.js: 1199 → 1203
avisos: 0
```

### Revisiones

| Quién | Modelo y esfuerzo | Sobre | Hallazgo | Qué hice |
|---|---|---|---|---|
| `/code-review high` | esta sesión, alto | `885ee89..f32ea2f` | 1. La telemetría de la landing va sin token | D56 |
| | | | 2. `logout()` ignora el 403 y lleva al inicio con la sesión abierta | Arreglado en `b1c9d70`, con su rojo (sabotaje 5) |
| | | | 3. El `/logout` de v1 va sin token | D56. Ya daba 403 antes |
| | | | 4. Sin cookie `csrf_token` no hay cómo cerrar sesión | D57 |
| | | | 5. La trampa de `csrf1.sh` no veía el PID de la API (subshell) | Arreglado en `c01ca26` |
| | | | 6. Si `/health` no contesta, el script corre igual sin avisar | Arreglado en `c01ca26` |
| | | | 7. El header repetido en `track()` y en `api()` | Queda. `track()` no pasa por `api()` a propósito, y el comentario de ahí dice por qué. Las dos leen el mismo `getCsrfToken()`: no es un chequeo repetido |
| | | | 8. El `Origin` de los negativos no lo lee el servidor | Queda porque la tarea dice «desde otro origen». Lo que rechaza es la falta de token |
| | | | 9. Sólo se mira la primera telemetría | Todas salen del mismo `track()` |
| `adversario-sonnet-alto` | Sonnet, alto | `f32ea2f` | 1. Medio: el mismo «Salir» silencioso; lo reprodujo (`POST /auth/logout 403`, URL `/`, `current_user` 200) | Arreglado en `b1c9d70` |
| | | | 2. Bajo: `test_prelaunch_block1` cierra sesión sin token y con enforce da rojo | Arreglado en `c01ca26`. Con `false` y `true`: `55 passed` |
| | | | 3. Bajo, ya existía: v1 `/logout` | D56 |
| | | | Los cuatro sabotajes de entonces dan rojo. En v2 no encontró otros POST que den 403: `POST /api/session/state 200` ×5. Tampoco nada que deje entrar a quien no debe | — |
| Seguridad | subagente Sonnet, con las instrucciones de `/security-review` | `885ee89..b1c9d70` | «Sin hallazgos». Descartó XSS en el aviso nuevo porque `toast()` pone título y texto con `textContent` | Lo comprobé en `app_v2.js:236-257` |

### Riesgos

- **Bajo, D57.** Sin cookie `csrf_token`, «Salir» avisa y no cierra.
- **Bajo, D56.** Con enforce, la telemetría de la landing (con sesión) y el
  «Salir» de la pantalla vieja siguen dando 403, como antes.
- El sabotaje 4 (sin token en `api()`) rompe todas las escrituras de la
  página, no sólo el logout. El rojo se distingue igual por el texto.
- `CSRF_ENFORCE` sigue como esté en Railway. Esta pieza no lo prende.

### Comandos para reproducir

```bash
# 1. Sabotajes: dos bases en verde, cinco ROJO, «sabotajes con falla: 0»
PY=venv/bin/python scripts/testing/sabotajes/csrf1.sh b1c9d70
# 2. El caso: 11 passed
python -m pytest -q --no-cov tests/test_csrf.py
# 3. Números de §6: 0 avisos
python docs/pm/herramientas/chequeo-6.py 885ee89 b1c9d70
```

### Archivos de producto tocados

`proyecto_maria/main.py` y `proyecto_maria/static/v2/app_v2.js` (y
`CHANGELOG.md`).

---

## COBRO-MP-1 vuelta 5, entregada en `736fed6` (informe en el commit de arriba)

**Resultado.** Lo que promete la confirmación de cancelar sale de la misma
cuenta cuyo acceso muestra la pantalla: `/billing/me` calcula
`cancelar_corta_acceso` con `billing_entity` (la organización si hay, si no
la fila del usuario), igual que el resto de la respuesta. Caso nuevo con la
familia como datos: organización `past_due` vencida con fila `trial` +10,
organización `active` +20 con fila `past_due` vencida, y dos cuentas sin
organización. Las dos filas con organización dan ROJO en `9161e0a` y verde
ahora. Producto `+3/−2`, en `main.py`.

**Nada para decidir.** D51 (quién cancela lo de una organización) sigue
siendo pieza aparte; abajo, en «Riesgos», los casos que deja abiertos, con lo
que midió el adversario.

### SHAs (desde `3bfd1e1`, tu merge)

| SHA | Qué |
|---|---|
| `e0a54f7` | test: caso `test_cancelar_avisa_por_la_cuenta_que_da_el_acceso` (cuatro filas) y dos sabotajes en `cobro_mp1.sh`, uno por dirección; las anclas de los dos sabotajes viejos de `cancelar_corta_acceso` pasan a `billing_entity` |
| `96ce417` | fix: `cancelar_corta_acceso(billing_entity)` en `/billing/me`; `CHANGELOG.md` |
| `736fed6` | test: el caso mide sólo el aviso (ver «Revisiones», hallazgo del adversario) |
| (este) | docs: informe de las dos piezas |

### Rojo en `9161e0a`

El caso de `736fed6` copiado sobre un worktree de `9161e0a`,
`pytest tests/test_cobro_mp1_cde.py -k cancelar_avisa`:

```
E   AssertionError: el perfil promete otra cosa: {'billing_status': 'past_due', 'trial_ends_at': '2026-10-26T10:20:51.876453', ...
E   AssertionError: el perfil promete otra cosa: {'billing_status': 'active', 'trial_ends_at': '2026-11-25T10:20:52.444468', ...
FAILED tests/test_cobro_mp1_cde.py::test_cancelar_avisa_por_la_cuenta_que_da_el_acceso[org_impaga_fila_en_prueba]
FAILED tests/test_cobro_mp1_cde.py::test_cancelar_avisa_por_la_cuenta_que_da_el_acceso[org_activa_fila_impaga]
============ 2 failed, 2 passed, 31 deselected, 5 warnings in 2.39s ============
```

Las dos filas sin organización pasan en `9161e0a`, como corresponde: ahí
`billing_entity` y la fila son la misma cuenta. Están porque las pediste.

### Sabotajes (`cobro_mp1.sh`)

| Sabotaje | Qué cambia | Rojo esperado |
|---|---|---|
| «/billing/me avisa por la fila del usuario y no por su organización» | vuelve a `cancelar_corta_acceso(db_user)` | `…[org_impaga_fila_en_prueba]` |
| «/billing/me dice que corta si corta la fila del usuario, aunque la organización siga» | `…(billing_entity) or …(db_user)` | `…[org_activa_fila_impaga]` |

Las dos filas nuevas, copiadas de la salida sobre `96ce417`:

```
ROJO  | C: /billing/me avisa por la fila del usuario y no por su organización: dice «FAILED tests/test_cobro_mp1_cde.py::test_cancelar_avisa_por_la_cuenta_que_da_el_acceso[org_impaga_fila_en_prueba]»
ROJO  | C: /billing/me dice que corta si corta la fila del usuario, aunque la organización siga: dice «FAILED tests/test_cobro_mp1_cde.py::test_cancelar_avisa_por_la_cuenta_que_da_el_acceso[org_activa_fila_impaga]»
```

### Puertas

| Puerta | Sobre | Resultado |
|---|---|---|
| `cobro_mp1.sh` | `96ce417` | las cinco bases en verde; 148 ROJO, entre ellos los dos de arriba; el control «sin mirar antes de insertar» sigue en verde, como tiene que ser; «sabotajes con falla: 0», salida 0 |
| Suite completa, worktree limpio | `96ce417` | `4419 passed, 121 skipped, 3 xfailed, 100 warnings in 928.88s (0:15:28)`, salida 0 |
| Suite completa, worktree limpio | `736fed6` | `4419 passed, 121 skipped, 3 xfailed, 100 warnings in 679.05s (0:11:19)`, salida 0 |
| `tests/test_cobro_mp1_cde.py` | `736fed6` | `35 passed, 3 warnings in 15.99s` |
| `compileall -q proyecto_maria` | `736fed6` | salida 0 |
| chequeo-6 `3bfd1e1..736fed6` (lo propio) | `736fed6` | 0 avisos, abajo |
| Historia (grep de §6) | `736fed6` | vacío |

`cobro_mp1.sh` corrió sobre `96ce417`. `736fed6` sólo borra las cinco
líneas de después del aviso en el caso nuevo (y el import que quedó sin uso);
los dos rojos nuevos salen de la aserción del aviso, que está antes y no
cambió. Lo mostré otra vez a mano sobre `736fed6` con el primer sabotaje
(`db_user`), en un worktree aparte:

```
FAILED tests/test_cobro_mp1_cde.py::test_cancelar_avisa_por_la_cuenta_que_da_el_acceso[org_impaga_fila_en_prueba]
FAILED tests/test_cobro_mp1_cde.py::test_cancelar_avisa_por_la_cuenta_que_da_el_acceso[org_activa_fila_impaga]
============ 2 failed, 2 passed, 31 deselected, 3 warnings in 1.74s ============
```

Son las dos filas con organización: con `db_user` fallan las dos
direcciones; el script espera la primera.

### chequeo-6

```
chequeo-6 3bfd1e1..736fed6: avisos para mirar, no un veredicto
producto +3/−2
arnés +38/−6
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11306 → 11307
avisos: 0
```

Desde `9161e0a` (tu base de revisión) da además el AVISO de la anónima de
`pantalla_orden1.js`, que es de ORDEN-1b y está explicado en su sección.

### Revisiones

| Quién | Modelo y esfuerzo | Sobre | Hallazgo | Qué hice |
|---|---|---|---|---|
| `adversario-sonnet-alto` | Sonnet, alto | `96ce417` | 1. La segunda mitad del caso (el acceso después de cancelar) no distingue: con organización relee una organización que `cancel` no escribe. Lo probó: con `cancel` sin cambiar `billing_status`, las cuatro filas pasan | Lo reproduje leyendo el caso: en las cuatro filas el acceso ya coincidía antes de cancelar. Saqué esa mitad en `736fed6`; qué hace `cancel` con organización es D51 |
| | | | 2. Con organización en gracia (`active`, venció ayer) y fila `trial`, el aviso dice que corta y la organización sigue con acceso, porque `cancel` no la toca | Riesgo de D51, abajo |
| | | | 3. Con organización activa y fila `none` o `canceled` sin suscripción, la pantalla muestra «Cancelar» y da 409 | Ya existía. D51 |
| | | | 4. `suscripcion_abierta` y `renueva` mezclan la organización con `mp_preapproval_id` de la fila | Ya existía. D51 |
| | | | Las cinco mutaciones de la línea del aviso dan rojo en el archivo; los textos de los sabotajes están en sus rojos | — |
| `/code-review high` | esta sesión, alto | `3bfd1e1..96ce417` | 1. `cancel` decide `corta` y `service_until` con `db_user` | D51 |
| | | | 2. `cancel` no toca la organización | D51 |
| | | | 3. La aserción de después es tautológica con organización | Al principio la dejé; el adversario mostró que tampoco distingue sin organización. Sacada en `736fed6` |
| | | | 4. El botón se muestra y `cancel` da 409 | Ya existía. D51 |
| | | | 5. `renueva` y `suscripcion_abierta` salen de `db_user` | Ya existía. D51 |
| | | | 6. Las filas sin organización repiten otro caso | Quedan: las pediste en este caso |
| | | | 7. Los sabotajes no rompen `cancel` | Por diseño: la vuelta cambia el aviso, no `cancel` |
| Seguridad | subagente Sonnet, con las instrucciones de `/security-review` | `3bfd1e1..96ce417` | «Sin hallazgos» | — |
| Seguridad | subagente Sonnet, con las instrucciones de `/security-review` | `96ce417..736fed6` | «Sin hallazgos»: sólo `pantalla_orden1.js` y `test_cobro_mp1_cde.py`; el producto no lee `X-Prueba-Consulta` (grep en `proyecto_maria/`: 0) | Lo reproduje |

### Riesgos

- **Medio, es D51.** Con organización, `cancel` sigue cambiando sólo la fila
  del usuario. El aviso ahora dice lo que pasaría con la cuenta que da el
  acceso, pero `cancel` no actúa sobre ella. El adversario lo midió con
  organización `active` vencida ayer (gracia) y fila `trial`:
  `promesa_corta=True status_pantalla=active cancel=200 org_antes=active acceso_org_antes=True org_despues=active acceso_org_despues=True fila_despues=canceled`.
  La pantalla dice «dejás de usar CDI» y la organización sigue en gracia. La
  respuesta de `cancel` (`service_until`, el log) también sale de la fila.
- **Bajo, es D51.** Organización activa con fila `none` o `canceled` sin
  suscripción: botón «Cancelar» y 409.
- Ninguna fila del caso cubre organización `trial`, `canceled` o `none`, ni
  un `organization_id` sin organización (ahí `_get_billing_entity` cae a la
  fila). No las agregué: el aviso es una sola llamada con la entidad, y las
  dos direcciones ya la fijan.

### Comandos para reproducir

```bash
# 1. Sabotajes: los dos nuevos en ROJO con su fila, y «sabotajes con falla: 0»
PY=venv/bin/python scripts/testing/sabotajes/cobro_mp1.sh 736fed6
# 2. El caso: 4 passed
python -m pytest -q --no-cov tests/test_cobro_mp1_cde.py -k cancelar_avisa
# 3. Números de §6: 0 avisos
python docs/pm/herramientas/chequeo-6.py 3bfd1e1 736fed6
```

### Archivos de producto tocados

`proyecto_maria/main.py` (y `CHANGELOG.md`).

---


/compact conservar: Dev 1, rama claude/dev-tecnica. CSRF-1 entregada en
b1c9d70 (informe en el commit de arriba), con D56 y D57 para decidir.
COBRO-MP-1 vuelta 5 sigue en revisión (736fed6); si trae devolución, va primero.
Sigue COBRO-CORTE-1, en tu orden. Nada se publica sin el «dale» de Emi; nunca main.
