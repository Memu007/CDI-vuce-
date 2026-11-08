# Reproducción ENTORNO-4 (Dev MARIA), 2026-11-08

Sobre `44b9759` (informe `96d7094`), base `4a6fdcd`. Veredicto: **aceptada,
sin integrar**.

| Qué | Resultado |
|---|---|
| `chequeo-6.py 4a6fdcd 44b9759` | `producto +19/−26`, avisos 0, historia vacío — igual al informe |
| `test_entorno1.py` + `test_billing_checkout.py` | `36 passed` |
| `entorno4.sh 44b9759` | 4 ROJO, `sabotajes sin rojo: 0`, rc 0 |
| `entorno3.sh 44b9759` | 4 ROJO, `sabotajes sin rojo: 0`, rc 0 |
| Mío: `ENVIRONMENT=production`, `FRONTEND_URL` vacía, espacio, tab o `/` | las cuatro: `RuntimeError: FRONTEND_URL no esta seteada…` |
| Mío: `ENVIRONMENT=Production`, `FRONTEND_URL=https://x.com/` | `'https://x.com'` (con mayúscula cuenta como producción) |

Leí el diff de producto entero: una sola `get_frontend_url` en `config.py`,
llamada al arrancar después de CORS; salen las copias de `main.py` y de
`billing_service.py` (la que caía a `:8000` sin avisar). `docker-compose.yml`
la exige con `:?`.

No corrí la suite completa: tomo la de la Dev (`5214 passed`, dos formas).
Sin adversario propio: arranque y configuración, sin rutas, sesión ni
permisos; la Dev pasó Sonnet alto y `/code-review`.

**Antes de publicar este SHA, Railway tiene que tener `FRONTEND_URL`**: sin
ella el deploy no arranca.
