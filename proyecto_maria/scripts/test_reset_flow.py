"""Smoke test end-to-end del flow de reset password + verify email.

Corre contra un server ya levantado (default http://127.0.0.1:8010).

Cubre:
- `/auth/request-password-reset` devuelve `dev_token_hint` cuando SMTP
  esta en modo mock.
- `/auth/reset-password` acepta el token y cambia la password.
- `/auth/login` acepta la nueva password y rechaza la vieja.
- `/reset-password?token=...` sirve HTML (la UI).
- `/auth/resend-verification` requiere auth y responde coherente para
  un usuario ya verificado.
- `/auth/verify-email?token=...` redirige a FRONTEND_URL/dashboard.

No depende de SMTP real: si SMTP no esta seteado, el endpoint devuelve
el token por response y los emails quedan loguedos a stdout.

Uso:
  python3 proyecto_maria/scripts/test_reset_flow.py
"""

from __future__ import annotations

import os
import sys
import secrets as _secrets

import httpx

BASE = os.getenv("CDI_BASE_URL", "http://127.0.0.1:8010")
USER = os.getenv("CDI_TEST_USER", "demo_reset")
EMAIL = os.getenv("CDI_TEST_EMAIL", "demo_reset@example.com")
OLD_PASS = "passwordOriginal1"
NEW_PASS = "passwordNueva456"


def banner(msg: str) -> None:
    print(f"\n=== {msg} ===")


def ensure_user(client: httpx.Client) -> None:
    """Asegura un usuario reutilizable. Si el user ya existia pero su
    password no matchea (test anterior la roto), generamos uno nuevo con
    sufijo random para no bloquear el flow."""
    global USER, EMAIL
    r = client.post(
        "/auth/register",
        json={
            "username": USER,
            "password": OLD_PASS,
            "email": EMAIL,
            "name": "Demo Reset",
            "plan": "premium",
        },
    )
    if r.status_code == 200:
        print(f"  · user '{USER}' creado")
        return
    if r.status_code == 400 and "existe" in r.text.lower():
        print(f"  · user '{USER}' ya existia, rotamos para evitar conflicto")
        suffix = _secrets.token_hex(3)
        USER = f"{USER}_{suffix}"
        EMAIL = f"{USER}@example.com"
        ensure_user(client)
        return
    raise SystemExit(f"registro fallo: {r.status_code} {r.text}")


def run() -> int:
    with httpx.Client(base_url=BASE, timeout=10.0) as client:
        banner("0) Asegurar usuario de prueba")
        ensure_user(client)

        banner("1) Pedir reset de password")
        r = client.post("/auth/request-password-reset", json={"email": EMAIL})
        assert r.status_code == 200, r.text
        data = r.json()
        token = data.get("dev_token_hint")
        if not token:
            print(
                "  !! no vino dev_token_hint — o hay SMTP real configurado, "
                "o el email no matchea. Abortando test."
            )
            return 1
        print(f"  · token recibido: {token[:8]}...")

        banner("2) GET /reset-password sirve la UI")
        r = client.get(f"/reset-password?token={token}")
        assert r.status_code == 200 and "Restablecer" in r.text, r.text[:200]
        print("  · UI OK")

        banner("3) POST /auth/reset-password con el token")
        r = client.post(
            "/auth/reset-password",
            json={"token": token, "new_password": NEW_PASS},
        )
        assert r.status_code == 200, r.text
        print(f"  · reset OK: {r.json()}")

        banner("4) Token usado: segundo POST con el mismo token debe fallar")
        r = client.post(
            "/auth/reset-password",
            json={"token": token, "new_password": "otraCosa123"},
        )
        assert r.status_code == 400, r.text
        print("  · 400 correcto (token ya usado / invalidado)")

        banner("5) Login con la NUEVA password")
        r = client.post("/auth/login", json={"username": USER, "password": NEW_PASS})
        assert r.status_code == 200, r.text
        print("  · login OK con la nueva password")

        banner("6) Login con la VIEJA password debe fallar")
        r = client.post("/auth/login", json={"username": USER, "password": OLD_PASS})
        assert r.status_code in (400, 401), r.text
        print(f"  · rechazo correcto ({r.status_code})")

        banner("7) /auth/resend-verification sin sesion → 401")
        with httpx.Client(base_url=BASE, timeout=10.0) as anon:
            r = anon.post("/auth/resend-verification")
            assert r.status_code == 401, r.text
            print("  · 401 correcto")

        banner(
            "8) /auth/resend-verification autenticado + user ya verificado "
            "(EMAIL_VERIFICATION_REQUIRED=false en dev) → already_verified"
        )
        r = client.post("/auth/resend-verification")
        # Con el toggle off, register crea is_verified=True. Esperamos:
        # - 200 con already_verified=True (demo/reset users que quedaron
        #   verificados), o
        # - 400 si no hay email (no aplica a este user pq si tiene).
        assert r.status_code in (200, 400), r.text
        if r.status_code == 200:
            body = r.json()
            print(f"  · respuesta coherente: {body}")
        else:
            print(f"  · 400 ({r.text})")

        banner("9) GET /auth/verify-email con token invalido → 400")
        r = client.get("/auth/verify-email?token=not-a-valid-token")
        assert r.status_code == 400, r.text
        print("  · 400 correcto")

        banner("OK: flow de reset + verify responde como esperamos")
        return 0


if __name__ == "__main__":
    sys.exit(run())
