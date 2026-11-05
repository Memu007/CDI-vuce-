# Reproducción COBRO-MP-1 vuelta 3 — 2026-11-05 (PM)

Producto `9048b6a`, base `4ef59f4`, informe `9298ab6` (rama `claude/dev-tecnica`).
Adversario Opus alto con contexto nuevo + reproducción propia de la PM.

## Veredicto: devolución por una causa

**Causa:** el 409 nuevo de D13 (c) manda a «cancelá el plan primero», pero
`cancel_billing` sólo acepta `trial`/`active`/`past_due`/`canceled`. Una cuenta
con `billing_status` fuera de esa lista (`none`, `None`, `expired`) y una
suscripción `authorized` queda sin salida. En `4ef59f4` el checkout la sacaba
(200). `none` es el valor por defecto de la migración para usuarios previos al
cobro.

Reproducido por la PM (prueba de 14 líneas abajo), en `9048b6a`:

```
SALIDA none 409 Tu suscripción en Mercado Pago sigue activa. Si acabás de pa | cancel 409 No se puede cancelar desde el estado actual: none | checkout 409 authorized
SALIDA None 409 ... | cancel 409 No se puede cancelar desde el estado actual: None | checkout 409 authorized
SALIDA expired 409 ... | cancel 409 No se puede cancelar desde el estado actual: expired | checkout 409 authorized
SALIDA trial 409 ... | cancel 200 ok | checkout 200 cancelled
```

En `4ef59f4`: `none`, `None`, `expired` → checkout 200, `cancelled`.

Prueba (sólo en el scratchpad de la PM, no va al producto):

```python
"""Negativos del revisor sobre checkout y cancelar (no van al repo)."""
import pytest
from tests.test_cobro_mp2 import CREADAS, PEDIDOS, SUS, _leer, _mp, _suscripto  # noqa: F401
from tests.test_prelaunch_block2 import _set_user, client  # noqa: F401


@pytest.mark.parametrize("estado", ["none", None, "expired", "trial"])
def test_salida_del_409(client, estado):
    usuario, sid = _suscripto(client, "negd13", billing_status=estado, dias=-5)
    r1 = client.post("/api/billing/checkout", json={"plan": "premium"})
    r2 = client.post("/api/billing/cancel")
    r3 = client.post("/api/billing/checkout", json={"plan": "premium"})
    print("\nSALIDA", estado, r1.status_code, r1.json().get("detail", "")[:60], "| cancel", r2.status_code,
          r2.json().get("detail", r2.json())if r2.status_code != 200 else "ok", "| checkout", r3.status_code, SUS[sid])
```

## Lo que se sostiene

- Pruebas de cobro (`test_cobro_mp1*`, `test_cobro_mp2`, `test_cobro_corte1`, `test_webhook_ipn`, `test_g7_cobro`): `307 passed`.
- `cobro_mp1_postgres.py` en Postgres 16: 35 OK, `fallas: 0` (incluye NUL anidado).
- Suite completa sobre `9048b6a`: `4407 passed, 121 skipped, 3 xfailed`, salida 0.
- Sabotajes repetidos a mano, todos en rojo: `authorized` fuera de la tupla (4 failed); `sin_cuenta in (None, "")` (los mismos 4 ids); sin el 409 de D13 (4 failed); sin cuenta → rechazado (18 failed); sin el 404 (2 failed).
- 16 cuerpos raros por los dos avisos: ningún 500, ninguna doble acreditación (`44 passed`).
- D18 se reproduce como lo describe el informe.

No corrido: `cobro_mp1.sh` y `cobro_mp2.sh` enteros (sustituidos por los 5 sabotajes a mano), `smoke_friccion.sh`, `ataque_aislamiento.sh`, nada contra Mercado Pago real (D30 abierto).

## chequeo-6 4ef59f4 9048b6a

```
producto +181/−73
  AVISO producto suma 108 líneas netas: el informe dice por qué (§6: más de 20)
arnés +1030/−80
  AVISO historia en proyecto_maria/static/v2/app_v2.js:35: // el servidor exija CSRF (ORDEN-1b).
  AVISO creció una función de más de 150: proyecto_maria/static/v2/app_v2.js:7 <anónima> 1134 → 1198
  AVISO comentario nuevo de 4 líneas: proyecto_maria/static/v2/app_v2.js:32
  AVISO comentario nuevo de 3 líneas: proyecto_maria/static/v2/app_v2.js:843
  AVISO creció una función de más de 150: scripts/testing/pantalla_orden1.js:275 <anónima> 1044 → 1343
avisos: 6
```
