# Dev → PM

Canal de la Dev hacia la PM. **Sólo lo escribe la Dev.** La PM lee acá y responde
en `docs/pm/PARA-DEV.md`. Informe más nuevo arriba.

> **Canal mudado a `CDI-vuce-` el 2026-09-17 (VUCE-2).** Los informes anteriores
> (BASE-1..3, DOCKER-1, DIVERGENCIA-1/2, ROADMAP-REVIEW, VUCE-1) viven en
> `Memu007/CDI`, `docs/pm/PARA-PM.md`, como archivo histórico.

---

## 2026-09-17 — VUCE-3 (entrega): agujero de cobro cerrado, suite en verde

**Los tres puntos entregados, y una aclaración de canal primero:** este bloque lo
escribiste en `Memu007/CDI` porque tu entorno no puede pushear a `CDI-vuce-` (403
del proxy). Lo mirroreé acá (`docs/pm/PARA-DEV.md`, con la nota de canal) y trabajé
desde esta rama. **El canal quedó partido: vos escribís en CDI, yo trabajo y
respondo acá.** Lo anoté como decisión pendiente de Emi en `DECISIONS.md` y `NOW.md`
(resolver tu permiso de push). Mientras tanto sigo mirroreando.

Commits en `CDI-vuce-` (rama `claude/project-deploy-review-4nct96`):

- `6926885` — fix(billing): corte de `active` vencido + 402 distinguible (producto).
- `f7ab985` — test: cerrar los 4 rojos de arrastre.
- `c7a86b3` — docs(pm): mirror de VUCE-3 + decisión de G7.3.
- este informe + estado — commit aparte.

**No mergeé, no deployé, no toqué `main`.**

### 1. El agujero de cobro, cerrado (lo más importante)

Extendí el corte por vencimiento a los `active`, con 7 días de gracia, en el cron de
arranque (`_check_expired_trials`) y en el gate (`require_active_billing`). Constante
`BILLING_GRACE_DAYS_ACTIVE = 7`.

**Rojo previo** contra `c7a86b3` (worktree limpio, test final):

```
tests/test_g7_3_corte_active.py::test_active_dentro_de_la_gracia_pasa PASSED
tests/test_g7_3_corte_active.py::test_active_pasada_la_gracia_da_402 FAILED
tests/test_g7_3_corte_active.py::test_active_vigente_no_se_toca PASSED
tests/test_g7_3_corte_active.py::test_trial_vencido_sin_gracia_da_402_con_codigo_propio FAILED
tests/test_g7_3_corte_active.py::test_cron_corta_active_pasada_la_gracia_y_respeta_la_gracia FAILED
=================== 3 failed, 2 passed ===================
```

Cada rojo por su razón: el `active` vencido 10 d **pasaba** el gate (daba 400 por
body, no 402); el `trial` daba `PLAN_LIMIT_EXCEEDED` (código indistinguible); el cron
dejaba al `active` en `active`. **Verde después:** los 5 pasan. Los tres casos que
pediste:

- `active` vencido 3 d → **pasa** (dentro de la gracia).
- `active` vencido 10 d → **402** `SUBSCRIPTION_PAST_DUE`, queda `past_due`.
- `active` vigente → pasa, sin tocar.

**El 402 distinguible, y dónde estuvo la parte difícil.** `get_current_user`
(`auth/dependencies.py:101`) ya pasaba a `past_due` un `trial` vencido **antes** de
mi gate, así que una vez en `past_due` no se puede saber por el estado si fue trial
vencido o renovación impaga. El único dato que distingue "pagó de verdad" de "nunca
pagó" es **`payment_provider`**: el webhook real de MP deja `"mercadopago"`, y el
registro con tarjeta deja `"simulated"` (`main.py:2874`). Ni `payment_customer_id`
ni `billing_period_started_at` sirven —el registro los setea igual—. Con eso:

- `PLAN_LIMIT_EXCEEDED` — trial/active vigente sin operaciones.
- `TRIAL_EXPIRED` — past_due/canceled sin pago real (nunca pagó).
- `SUBSCRIPTION_PAST_DUE` — past_due/canceled con pago real (renovación impaga).

El front no se rompe: maneja el 402 por `res.status === 402` y por `billing_status`
(`app_v2.js:40`, `:625`), no por el string `code`. Ajusté dos tests que fijaban el
código viejo (mi `test_g7_cobro` G7.2, y `test_prelaunch_block3`); el de ops-límite
sigue en `PLAN_LIMIT_EXCEEDED`.

**Límite declarado:** un usuario activado por `simulate-charge` (demo/test) no tiene
`payment_provider="mercadopago"`, así que al vencer se marcaría `TRIAL_EXPIRED` y no
`SUBSCRIPTION_PAST_DUE`. En producción los 50 pagan por el webhook real, así que el
código es correcto para ellos; lo dejo dicho por si algún día se cobra por
`simulate-charge`.

### 2. ¿Emi puede ver quién está `past_due`? — no, y no lo construí

`admin_router` está montado (`main.py:1312`). Tiene monitoreo, errores, métricas y
`/cohort-retention` (admin, sólo lectura), **pero ese endpoint filtra a
`billing_status in ('active','trial')`** (`admin_router.py:351`) — excluye
justamente a los `past_due`/`canceled` que Emi necesitaría ver. **No existe forma de
listar quién está impago.** Como pediste, no lo construí: queda como tarea aparte, y
la anoté en `NOW.md`. El punto 1 sin esto corta bien pero nadie ve a quién.

### 3. Los cuatro rojos: cerrados, ninguno era producto

Suite: **`680 passed, 102 skipped, 0 failed`**, estable en orden aleatorio
(pytest-randomly) y fijo.

- **3 de `auto_ncm`** (`test_recent_changes_validation`, `test_pdf_avg_functional`):
  leían **rutas absolutas de tu máquina** —`/Users/Emi/CDI/static/index.html`,
  `.../script.js`—, que no existen en ningún otro entorno. Fallaban con
  `FileNotFoundError`, no porque el botón existiera. Los apunté al frontend real
  (`proyecto_maria/templates/` y `static/app.js`), con ruta relativa al repo.
  Verifiqué que los patrones prohibidos no están, así que el guard queda **vivo y en
  verde** (no borrado, no skip).
- **CSRF** (`test_enforce_no_afecta_bearer_sin_cookie`): **no es un bug de
  producto** —lo verifiqué antes de tocar nada, como pediste—. El nombre del test no
  matchea los patrones que apagan el atajo de auth de pytest, así que la app lo
  auto-autenticaba y daba 200 en vez de 401. Con el atajo apagado (= producción) el
  producto devuelve **401**, que es lo correcto: sin cookie ni token, con
  `CSRF_ENFORCE=true`, rebota por auth y no por CSRF, y **no hay 200**. Le agregué el
  fixture `sin_bypass_de_test`. No frené porque no había nada de producto que
  arreglar; si el probe hubiera dado 403 o 200 habría frenado.

### Riesgos y lo que quedó sin verificar

- **Nada probado contra Railway.** Todo contra el código y la suite, base descartable.
- **El listado admin de `past_due` no existe** y es media solución sin él: cortamos
  bien pero nadie ve a quién. Tarea aparte, tuya de decidir.
- **`simulate-charge` no marca `payment_provider="mercadopago"`**: ver el límite del
  punto 1.
- **`main` intacto.** No mergeé los 14 commits.
- **Canal partido** hasta que se resuelva tu permiso de push a `CDI-vuce-`.

---

## 2026-09-17 — VUCE-2 (entrega): convivencia ejecutada, G7 demostrada, G7.3 medida

**Los tres puntos entregados.** La convivencia según el camino 3 que decidiste;
G7.1/7.2/7.4 con su comando y salida; y el costo de G7.3 con un hallazgo medido que
cambia la cuenta. Todo en la rama de review: **no mergeé, no deployé, no toqué
`main`.**

Commits en `CDI-vuce-` (rama `claude/project-deploy-review-4nct96`):

- `283f713` — test(g7): evidencia de G7.1/7.2/7.4 (producto/regresión).
- `b3723ee` — docs(pm): mudanza del canal + convivencia (proceso).
- este informe — commit aparte.

Y en `Memu007/CDI`: el README-puntero de mudanza (rama
`claude/review-project-011CUK6vjo4ui6MfAg5Q3ztA`).

**Adenda incorporada.** Mientras cerraba esto entró tu confirmación de que Railway
deploya de `main` (auto-deploy, «Wait for CI» apagado). Actualicé la excepción del
push **de provisoria a permanente** —ya sin condición de salida, con el motivo
correcto— en `AGENTS.md` §2.ter, la regla de Cursor, `DECISIONS.md` y `NOW.md`. G6
lo dejé anotado como «demostrar el clic y escribir, no construir», sin tocarlo
(tocar deploys no es nuestro).

---

### Punto 1 — La convivencia (camino 3)

Ejecuté los cuatro puntos de tu decisión. **Sólo agregué; no pisé nada** de
`AGENTS.md`, `HANDOFF.md` ni `CHANGELOG.md`.

1. **`AGENTS.md` sigue siendo la puerta de entrada.** Le sumé una sección corta,
   **§2.ter «Canal PM/Dev»**: qué es, dónde vive (`docs/pm/`), cuándo aplica
   (trabajo planificado por la PM sigue las reglas del canal; el resto, las de
   ellos), y la excepción del push. No reescribí ninguna sección existente.

2. **La excepción del push a `main`, escrita como excepción, no como tachadura.**
   Va en dos lugares: en `AGENTS.md` §2.ter, y como nota aditiva al final de
   `.cursor/rules/persistencia-github-al-dia.mdc`, que es donde vive literalmente el
   `git push origin main` con `alwaysApply: true`. Con su motivo (la regla se
   escribió sin un servicio vivo atrás) y su condición de salida (cuando se confirme
   el branch que deploya Railway). Dejé el paso 5 de la regla intacto.

3. **El canal, mudado y adaptado (no copiado).** En `docs/pm/` de esta línea:
   `ONBOARDING-DEV.md`, `ONBOARDING-PM.md`, `DECISIONS.md`, `NOW.md`, `PARA-DEV.md`
   y este `PARA-PM.md`. Adaptaciones concretas:
   - Los onboardings **perdieron la sección 5 de CDI** (dos apps, 7 routers sin
     montar, `pytest.ini` con `--cov`, `PyJWT` faltante, sin Alembic): ninguna
     aplica acá. Verifiqué que `server_funcional.py` no existe en esta línea.
   - En su lugar quedó lo real de esta línea: el deploy en Railway, la rama con 14
     commits sin mergear, el aislamiento **ya hecho**, la convivencia con
     `AGENTS.md`, la baseline de la suite y el entorno con `--no-cov`.
   - `DECISIONS.md` y `NOW.md` con el estado post-VUCE-1 (G1 en verde) y las dos
     filas de convivencia que ya habías dejado escritas.
   - **No copié** `CLAUDE.md` ni `AGENTS.md` de CDI, como pediste.

4. **README-puntero en `CDI`:** un banner corto arriba del README diciendo que el
   producto se mudó y adónde.

**No encontré ningún otro choque de reglas** más allá del push. Su `AGENTS.md` §4
prohíbe forzar push y mergear sin aprobación, que coincide con lo nuestro; el resto
son convenciones (prefijos de commit, HANDOFF/CHANGELOG) que no chocan. Si aparece
uno al usar el canal, lo listo con las dos versiones y lo decidís vos.

**Una cosa que declaro y no resolví por mi cuenta:** `NOW.md` referenciaba
`ROADMAP-MVP.md` y `PROPUESTA-G1-G7.md`, y no estaban en tu lista de archivos a
mover. Los dejé en `CDI` y lo anoté en el `NOW.md` nuevo. Si los querés acá, es una
entrega chica aparte; no los traje para no ampliar el alcance solo.

---

### Punto 2 — G7: demostrado 7.1, 7.2 y 7.4

Test nuevo `tests/test_g7_cobro.py`, con el SDK de MercadoPago **mockeado**: no se
tocó ninguna cuenta real ni webhook a producción.

```
$ PYTHONPATH=/home/user/cdi-vuce- ./venv/bin/python -m pytest tests/test_g7_cobro.py -v --no-cov
tests/test_g7_cobro.py::test_g7_1_cobro_aprobado_activa_el_plan PASSED    [ 25%]
tests/test_g7_cobro.py::test_g7_2_corte_por_vencimiento_devuelve_402 PASSED [ 50%]
tests/test_g7_cobro.py::test_g7_2_control_trial_vigente_no_corta PASSED   [ 75%]
tests/test_g7_cobro.py::test_g7_4_reactivacion_tras_corte_vuelve_a_active PASSED [100%]
======================== 4 passed, 4 warnings in 2.29s =========================
```

Qué prueba cada uno, con la transición observable vía `GET /api/billing/me`:

- **G7.1 — Cobro.** Registro con tarjeta → `trial`. Webhook `topic=payment`
  aprobado (SDK mockeado) → `active`, con `trial_ends_at` a **+30 d** (lo setea
  `billing_service.process_payment:339`). El antes/después se afirma en el test, no
  se declara.
- **G7.2 — Corte por vencimiento.** Registro → `trial`; se adelanta `trial_ends_at`
  al pasado en la base descartable; `POST /api/operations/manual` → **402** con
  `code: PLAN_LIMIT_EXCEEDED` y `billing_status: past_due`. El control adjunto prueba
  que ese 402 lo causa el vencimiento: **con el trial vigente la misma llamada no da
  402** (da 400 por body vacío; el gate deja pasar).
- **G7.4 — Reactivación.** Desde `past_due` (tras el corte de arriba), un cobro
  exitoso vía `simulate-charge` → `active`. Es el camino sin gateway que vos misma
  señalaste para probarlo.

**Suite completa, sin regresión:**

```
$ PYTHONPATH=/home/user/cdi-vuce- ./venv/bin/python -m pytest tests/ -q --no-cov -p no:randomly
4 failed, 671 passed, 102 skipped, 6 warnings in 44.88s
```

667 (VUCE-1) + 4 nuevos = 671. Los 4 rojos son los preexistentes de siempre:
`test_csrf.py::test_enforce_no_afecta_bearer_sin_cookie` y los tres del botón
`auto_ncm`. Ninguno lo tocó este bloque.

**El límite de G7.1, declarado.** La propuesta pedía «un preapproval **real**
cobrado en el sandbox de MP». La pata que demostré es «webhook de pago aprobado →
`active`», que es la lógica nuestra y no necesita MP. Crear el preapproval real en
el sandbox necesita credenciales de MP y un webhook que apunte a la cuenta: ahí
frené, como pediste. Es el límite que te reservaste levantar. `simulate-charge`
alcanza para 7.2 y 7.4 y para la pata de webhook de 7.1; no alcanza para la pata de
gateway real.

---

### Punto 3 — G7.3: costo de las dos ramas, y un agujero que mide distinto la cuenta

Antes del costo, un hallazgo que cambia la premisa. **Lo medí, no lo supongo.**

**El «corte por calendario» hoy NO corta a un usuario `active`.** Sólo pasa a
`past_due` a los que están en `trial`:

```
$ grep -n 'past_due"' proyecto_maria/main.py
722:   .values(billing_status="past_due")     # cron de arranque: WHERE billing_status=="trial"
1766:  billing_entity.billing_status = "past_due"   # gate: if billing_status=="trial"
2003:  db_user.billing_status = "past_due"          # reactivate: solo canceled+vencido
```

`can_create_operation` (`billing_service.py:114`) deja pasar a cualquiera con
`status == "active"` sin mirar `trial_ends_at`. Medido con una sonda (usuario
llevado a `active` por webhook, `trial_ends_at` forzado 5 días al pasado, sin
renovación):

```
>>> SONDA G7.3: user ACTIVE, período vencido 5 días -> POST operación = 404
>>> billing_status tras el intento = active
```

El 404 es «cliente inexistente» (validación posterior al gate), **no** el 402 del
gate: el usuario pasó. Y siguió `active`. Sin scheduler externo
(`grep apscheduler|celery|repeat_every` → vacío; el único cron corre al arranque y
sólo sobre `trial`).

**Qué significa:** el corte por calendario que la propuesta daba por red de
contención de la rama «descartar» **sólo funciona para quien nunca pagó** (trial
vencido). Para un estudio que pagó una vez y después le rechazan la renovación, hay
servicio ilimitado **indefinido** hasta que alguien lo toque a mano.

#### Rama A — Implementar la señal de impago

Qué falta hoy (`main.py:7796`, `process_payment:297`): el webhook sólo maneja
`topic=="payment"` y `process_payment` sólo actúa con `status=="approved"`. Habría
que agregar (a) una rama para pago **rechazado/fallido** de renovación → `past_due`,
y (b) una rama para `topic=="subscription_preapproval"` (cancelación/pausa avisada
por MP) → `canceled`/`past_due`. La firma HMAC y la idempotencia del webhook ya
existen.

- **Código:** ~1–1,5 días (dos ramas nuevas en un handler que ya está armado + sus
  tests con el SDK mockeado, como los de este bloque).
- **No-código, y es el costo real:** configurar en MP que mande esos eventos y
  probarlo contra el **sandbox** de MP → credenciales y una cuenta de prueba. Eso
  no es mío (frené en el mismo límite que G7.1). Estimo medio día tuyo/de Emi más
  la espera de MP.
- **Riesgo:** una señal externa mal manejada corta a alguien que sí pagó. Hay que
  tratar reintentos y estados intermedios de MP, no sólo «rechazado».

#### Rama B — Descartar (corte por calendario)

Con el agujero de arriba, «descartar» **no es 0 costo hoy**: para que el corte por
calendario haga lo que la propuesta dice, hay que **extenderlo a los `active`
vencidos**. Es una línea en cada lugar: cambiar `== "trial"` por
`in ("trial","active")` en el cron (`main.py:719`) y en el gate (`main.py:1762`).

- **Código:** ~2–3 horas con su regresión (rojo previo: hoy un `active` vencido pasa
  el gate; verde: da 402).
- **Consecuencia de negocio aceptada:** hasta 30 días de servicio gratis tras un
  impago (desde el último pago exitoso), y una cancelación en MP no se refleja
  hasta ese vencimiento. Para 50 estudios contratados que ya dijeron que sí —no
  altas anónimas— es tolerable.

#### Recomendación

**Para el MVP, rama B, pero cerrando el agujero: no la «descartar» pura de hoy.**
Descartar la señal de impago está bien; lo que no está bien es dejar el corte por
calendario como está, porque no corta a los que pagaron. Con las dos líneas del cron
y el gate, un impago corta a los 30 días para todos, sin depender de MP. La señal de
impago (rama A) queda para cuando haya que reaccionar más rápido que 30 días, que
para un B2B contratado no es la semana 1.

La decisión es tuya y de Emi; el número está. **Lo que no recomiendo es descartar
G7.3 sin tocar nada**, porque eso no es «corte por calendario»: es «sin corte para
quien pagó».

---

### Riesgos y lo que quedó sin verificar

- **Nada probado contra el servicio vivo de Railway.** Todo es contra el código y
  la suite, con base descartable. Mismo alcance abierto que G3.
- **MP no se tocó de verdad.** Todo con el SDK mockeado o `simulate-charge`. La pata
  de gateway real de G7.1 queda para vos/Emi.
- **No hay recorrido de producto propio** en esta línea: el `recorrido.py` era de
  CDI y no se mudó (chequeaba cuentas que acá no existen). Anotado como pendiente en
  el `ONBOARDING-PM` y el `NOW` nuevos.
- **Los 4 rojos de la suite** son preexistentes y fuera de alcance salvo que los
  asignes.
- **`main` intacto:** no mergeé los 14 commits ni pusheé a `main`. Sigue esperando
  tu confirmación del branch de Railway.
