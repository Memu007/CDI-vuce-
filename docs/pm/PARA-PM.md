# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CSRF-2, entregada en `fcd1072` (informe en el commit de arriba)

**Resultado.**
- **Rutas exentas.** El control CSRF exenta sólo un conjunto exacto de rutas:
  `/auth/login`, `/auth/register`, `/auth/request-password-reset`,
  `/auth/recover-username` y `/auth/reset-password`.
  - Ya no saltea rutas que empiezan parecido (`/auth/loginx`, `/healthx`,
    `/staticx`) ni las que dicen «webhook» en cualquier parte. Ejemplo:
    `DELETE /api/catalog/x/productos/abc-webhook`.
  - Las tres rutas de recuperación de cuenta andan con una cookie de sesión
    vieja.
- **`static/csrf.js` (nuevo).** Envuelve `fetch` en la landing y en la pantalla
  vieja: toda escritura al mismo origen lleva `X-CSRF-Token`.
  - Con `CSRF_ENFORCE=true`, la telemetría de la landing con sesión abierta y
    las escrituras de `app.js` dan 200.
  - El «Salir» de `app.js` cierra la sesión: después, `/auth/current_user` da
    401.
- **Alias `/logout`.** Hay una prueba que exige que cierre de verdad: con
  cookie y token, 200 y las dos cookies borradas.
- Producto `+37/−11`.

### Decisiones

- **D58. Duplicación con `app_v2.js`.** La v2 pone el token con su propio
  wrapper.
  - Opciones:
    - (a) a la cola de limpieza: cargar `csrf.js` también en `dashboard_v2` y
      sacar el header a mano de `app_v2.js`;
    - (b) dejarlo así.
  - Recomiendo (a). Es una sola regla en un solo lugar, y la v2 ya está
    cubierta por `csrf1.sh`. No lo hice acá porque la tarea no lo pide y
    tocaría la v2.
- **D59. Sesión con `access_token` pero sin `csrf_token`.** Una cookie de
  sesión emitida antes de CSRF da 403 en toda escritura, «Salir» incluido,
  hasta volver a entrar.
  - Ningún GET vuelve a emitir `csrf_token`: sólo lo hacen login y registro.
  - Es previo a esta pieza. Lo marcaron el `/code-review` y el adversario.
  - Opciones:
    - (a) pieza chica antes de activar el enforce en producción: emitir
      `csrf_token` si falta, por ejemplo en `/auth/current_user`;
    - (b) aceptar que esas cuentas vuelvan a entrar. Login y registro están
      exentos, así que pueden.
  - Recomiendo (a), si el enforce se va a prender con sesiones vivas. Si no,
    (b).
- **D60. El guard de la pantalla vieja depende de `localStorage`.**
  `dashboard.html` (la v1) manda a `/` si `localStorage.access_token` está
  vacío, y sólo `landing_legacy.html` lo llena.
  - Con la landing nueva, `/dashboard?v=1` no abre. Es previo a esta pieza.
  - La prueba lo esquiva poniendo el token antes de abrir.
  - Opciones:
    - (a) confirmar si la v1 todavía se usa y, si se usa, abrir una pieza;
    - (b) nada, si la v1 ya no tiene usuarios.
  - Recomiendo (a), nada más que confirmar.

Supuesto reversible: la familia de rutas de la prueba suma `/auth/register`,
que la tarea no nombraba. Lo pidió el adversario: sin esa fila, sacar
`/auth/register` de las exentas dejaba la prueba en verde.

### SHAs (desde `6e71766`, tu merge)

| SHA | Qué |
|---|---|
| `8abfed3` | fix: conjunto exacto de rutas exentas; `csrf.js` cargado en `landing.html` y `dashboard.html`; `CHANGELOG.md` |
| `965a415` | test: alias `/logout` con token; familia de rutas sin token (`RUTAS_SIN_TOKEN`); `pantalla_csrf2.js`; `csrf2.sh`; el arnés común `_csrf_comun.sh`, que ahora usa también `csrf1.sh` |
| `aa4eced` | fix: `csrf.js` mira el método primero, y un `fetch` mal armado falla en la promesa, como el nativo (hallazgos 2 y 8 del code-review) |
| `a6af49f` | test: la pantalla vieja entra con su token en `localStorage` (hallazgo 1); caso y sabotaje de la URL inválida |
| `fcd1072` | test: el chequeo de otro origen mira lo que `csrf.js` le pasa a `fetch` nativo, porque la CSP `connect-src 'self'` corta el pedido antes de la red y la prueba no lo veía nunca (adversario 1B); `/auth/register` entra a la familia, con su sabotaje (adversario 2) |
| (este) | docs: informe |

### Rojos antes

La `tests/test_csrf.py` final, copiada sobre `6e71766`:

```
FAILED tests/test_csrf.py::test_sin_token_solo_pasan_las_rutas_exentas_exactas[DELETE /api/catalog/x/productos/abc-webhook]
FAILED tests/test_csrf.py::test_sin_token_solo_pasan_las_rutas_exentas_exactas[POST /api/payments/webhook/x]
FAILED tests/test_csrf.py::test_sin_token_solo_pasan_las_rutas_exentas_exactas[POST /healthx]
FAILED tests/test_csrf.py::test_sin_token_solo_pasan_las_rutas_exentas_exactas[POST /staticx]
FAILED tests/test_csrf.py::test_sin_token_solo_pasan_las_rutas_exentas_exactas[POST /auth/loginx]
FAILED tests/test_csrf.py::test_sin_token_solo_pasan_las_rutas_exentas_exactas[POST /auth/request-password-reset]
FAILED tests/test_csrf.py::test_sin_token_solo_pasan_las_rutas_exentas_exactas[POST /auth/recover-username]
FAILED tests/test_csrf.py::test_sin_token_solo_pasan_las_rutas_exentas_exactas[POST /auth/reset-password]
=================== 8 failed, 18 passed, 5 warnings in 8.52s ===================
```

- **Alias `/logout`.** En la base ya delega (desde CSRF-1 vuelta 2), así que
  su prueba pasa. Lo que la mide es el sabotaje «el alias responde sin cerrar
  la sesión».
- **Pantalla sobre la base.** `FALLA: la telemetría de la landing dio 403 en
  /api/ui/event…`

### Puertas, sobre `fcd1072`

| Puerta | Resultado |
|---|---|
| suite completa (`pytest -q --no-cov --timeout=120`, base limpia) | `4438 passed, 121 skipped, 3 xfailed, 101 warnings in 639.62s`, salida 0. Al cerrar, asyncio imprime «Task was destroyed but it is pending!»: es ruido del cierre, no un fallo |
| `tests/test_csrf.py` | `26 passed` |
| `csrf2.sh fcd1072` | 10 ROJO, `sabotajes con falla: 0`, salida 0 |
| `csrf1.sh fcd1072` | 8 ROJO, `sabotajes con falla: 0`, salida 0 (el arnés común no rompió CSRF-1) |
| grep de historia de §6 | vacío (salida 1) |
| `/code-review high` (yo, sobre `965a415`) | 8 hallazgos: se arreglaron 1, 2 y 8; los demás, abajo |
| `/security-review` (subagente Sonnet, sobre `6e71766..a6af49f`) | sin hallazgos de confianza ≥7. `fcd1072` sólo toca pruebas |
| adversario Sonnet alto (sobre `965a415`) | 4 hallazgos, abajo |

No corrí `smoke_friccion.sh` ni `ataque_aislamiento.sh`. Esta pieza toca el
middleware CSRF y dos `<script>`, no datos ni aislamiento. Lo que cambia en el
backend lo miden `test_csrf.py` y la suite.

### Hallazgos

| De | Modelo y esfuerzo | Hallazgo | Qué pasó |
|---|---|---|---|
| code-review 1 | yo, alto | la v1 redirige a `/` sin token en localStorage: la prueba pasaba sin abrir la pantalla vieja | arreglado en `a6af49f` |
| code-review 2 y 8 | yo, alto | `csrf.js` podía tirar antes de devolver la promesa (URL inválida, `init` nulo) | arreglado en `aa4eced`, con caso y sabotaje |
| code-review 3 / adversario «opinión» | yo, alto; Sonnet alto | sesión sin `csrf_token` trabada | previo: **D59** |
| code-review 4 | yo, alto | `csrf.js` duplica lo que hace `app_v2.js` | **D58** |
| code-review 5 / adversario 3 | yo, alto; Sonnet alto | exentas a mano; `POST /auth/login/` (con barra) con cookie da 403 | riesgo menor: ningún cliente usa la barra |
| code-review 6 | yo, alto | un detalle menor de la prueba | no lo reproduje; no queda |
| code-review 7 | yo, alto | la landing carga `csrf.js` sin `?v=` (es `FileResponse`, sin plantilla) | riesgo menor: después de un cambio de `csrf.js`, un navegador con caché puede seguir con el viejo |
| adversario 1A | Sonnet alto | la v1 redirige y la prueba no abre la pantalla vieja | ya estaba arreglado en `a6af49f` (el adversario miró `965a415`) |
| adversario 1B | Sonnet alto | la CSP bloquea el pedido a otro origen antes de `p.route`, así que el chequeo nunca puede ver el token | arreglado en `fcd1072`; el sabotaje del origen da ROJO con su texto |
| adversario 2 | Sonnet alto | sacar `/auth/register` de las exentas no pone rojo | arreglado en `fcd1072`, con su sabotaje |
| adversario 4 | Sonnet alto | `fetch(url, null)` tiraba `TypeError` | arreglado en `aa4eced` (`init \|\| {}`) |

### Riesgos

- **XHR y `sendBeacon` salen sin token.** La landing y `app.js` no los usan
  hoy (adversario y `grep`). Uno nuevo daría 403 con el enforce prendido.
- **Las exentas son una lista a mano, comparada exacta.** Una ruta pública
  nueva que no use la sesión va a pedir el token hasta que se sume. Falla
  cerrada, no abierta.
- **Otro origen.** Lo cubren dos defensas: la comparación de origen en
  `csrf.js` y la CSP `connect-src 'self'`. La prueba mide la primera.
- **`POST /api/payments/webhook` dejó de estar exento.** Mercado Pago no manda
  la cookie de sesión, y sin ella el middleware no valida. Un webhook con
  cookie da 403 (adversario).

### chequeo-6, salida entera

```
chequeo-6 6e71766..fcd1072: avisos para mirar, no un veredicto
producto +37/−11
  AVISO producto suma 26 líneas netas: el informe dice por qué (§6: más de 20)
arnés +218/−74
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11307 → 11304
  proyecto_maria/static/csrf.js: nuevo, 27
avisos: 1
```

El AVISO: `main.py` resta 3 líneas. Las 29 netas de más son `csrf.js` (27,
nuevo) y sus dos `<script>`. La landing y la v1 no tienen un wrapper de `fetch`
propio donde poner el token. Ponerlo a mano en cada llamada eran más líneas y
un lugar más para olvidárselo.

### Para reproducir

```bash
git checkout fcd1072
# 1. 26 passed
DATABASE_URL=sqlite+aiosqlite:///./t.db GEMINI_API_KEY=test-key ENVIRONMENT=test python -m pytest -q --no-cov tests/test_csrf.py
# 2. 10 ROJO, «sabotajes con falla: 0»
PY=$(which python) PUERTO=8879 scripts/testing/sabotajes/csrf2.sh fcd1072
# 3. 8 ROJO, «sabotajes con falla: 0» (el arnés común no rompió CSRF-1)
PY=$(which python) PUERTO=8880 scripts/testing/sabotajes/csrf1.sh fcd1072
# 4. 1 AVISO, explicado arriba
python docs/pm/herramientas/chequeo-6.py 6e71766 fcd1072
```

### Archivos de producto tocados

`proyecto_maria/main.py`, `proyecto_maria/static/csrf.js` (nuevo),
`proyecto_maria/templates/dashboard.html` y
`proyecto_maria/templates/landing.html` (y `CHANGELOG.md`).

---

/compact conservar: Dev 1, rama claude/dev-tecnica. CSRF-2 entregada en
fcd1072 (informe en el commit de arriba), con D58-D60. Sigue COBRO-CORTE-1, en
tu orden. Nada se publica sin el «dale» de Emi; nunca main.
