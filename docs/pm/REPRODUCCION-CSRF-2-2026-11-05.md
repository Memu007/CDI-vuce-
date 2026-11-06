# Reproducción de CSRF-2 (2026-11-05, PM principal)

Producto `fcd1072`, informe `c44bf84`, base `6e71766`. Worktree aparte,
venv de PM.

## Pruebas

| Corrida | Resultado |
|---|---|
| `test_csrf` + `test_prelaunch_block1`, `CSRF_ENFORCE=true` | `70 passed` |
| lo mismo con `CSRF_ENFORCE=false` | `70 passed` |
| chequeo-6 `6e71766..fcd1072` | producto +37/−11, 1 AVISO (26 netas; el informe dice por qué), historia vacía |
| `csrf2.sh` | 10 ROJO, «sabotajes con falla: 0» |
| `csrf1.sh` sobre `fcd1072` | 8 ROJO, sin fallas |

Los 10 rojos de `csrf2.sh` cubren: el alias `/logout` que responde sin
cerrar, `webhook` en cualquier parte de la ruta, exentas por prefijo
(`/auth/loginx`), reset y registro que vuelven a pedir token, y `csrf.js`
(no pone el token, lo manda a otro origen, tira con URL inválida, la landing
o la pantalla vieja no lo cargan).

## Adversarios (contexto nuevo, esfuerzo alto)

**Opus**, uvicorn local con `CSRF_ENFORCE=true` y Chromium. Sin regresiones del diff:
- Recorrió registro, landing con sesión, v2 (clientes, checkout, salir), v1
  `?v=1` con sesión (backup, DELETE, `/logout`), verificación de mail desde
  otro origen, reset con sesión y `/dev/dashboard`: todas las escrituras van
  con token y dan 200, o el error es del negocio, no del control.
- `csrf.js`: 9 formas de llamar a `fetch` llevan token; otro origen, otro
  puerto, `//evil.test` y `data:` no lo llevan; URL inválida falla como el
  nativo.
- Sabotajes propios: con `or "webhook" in path` da 2 failed; con el `main.py`
  de la base, 8 failed.
- Bajo, preexistente, no llega a producción: «Simular Pago» del checkout demo
  hace `POST /api/payments/demo-confirm/…` sin token y da 403 con enforce
  prendido en desarrollo (`main.py:10221`). En producción esa página da 404.
- Informativo: escrituras a `/health`, `/static/…`, `/auth/verify-email`
  con cookie dan 403 en vez de 405.

**Sonnet**, uvicorn real con cookie de sesión y sin header. Sin bypass:
- Barra final, doble barra, `..`, `%2f`, `;`, mayúsculas, `X-Forwarded-Prefix`,
  forma absoluta, PUT/PATCH/DELETE, `X-HTTP-Method-Override`: todo 403.
- Las 5 exentas no leen la sesión ni `get_current_user`. Login CSRF por POST
  no entra: sólo acepta JSON, y el preflight desde otro origen da 400.
- Webhook de MP sin cookie pasa (es servidor a servidor, con firma); con
  cookie y sin token, 403.
- Bajo, depende del despliegue: con `--root-path` el conjunto exacto no
  coincide nunca y las exentas quedan controladas (falla cerrada). Hoy
  Railway no lo usa; con los prefijos de antes pasaba igual.
- Fuera del diff, preexistente, no reproducido: `GET /auth/verify-email` deja
  la sesión de la cuenta dueña del link; un atacante podría hacer entrar a la
  víctima en su propia cuenta con su link (login CSRF). Va a la cola.

## Antes de integrar

`git log --no-merges HEAD..c44bf84`: sólo commits de CSRF-2 (`8abfed3`,
`965a415`, `aa4eced`, `a6af49f`, `fcd1072`, `c44bf84`).
