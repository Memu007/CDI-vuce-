"""
Smoke test de aislamiento multi-tenant (D6 del plan integrado).

Verifica que dos usuarios autenticados no se vean datos entre sí:

    1. login como `premium` → crea cliente "Importadora Alice"
    2. login como `basico`  → lista clientes → NO debe ver "Importadora Alice"
    3. login como `basico`  → crea cliente "Importadora Bob"
    4. login como `premium` → lista clientes → NO debe ver "Importadora Bob"
    5. cross-access: basico intenta GET /api/clientes/{id_de_alice} → 404

Uso:
    python -m proyecto_maria.scripts.test_multitenant
    python -m proyecto_maria.scripts.test_multitenant --base http://127.0.0.1:8010

Sale con exit code 0 si todo pasa, 1 si alguna aserción falla.
"""

from __future__ import annotations

import argparse
import sys
from typing import Tuple

import httpx


DEFAULT_BASE = "http://127.0.0.1:8010"


def banner(title: str) -> None:
    print(f"\n=== {title} ===")


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def login(client: httpx.Client, username: str, password: str) -> None:
    r = client.post("/auth/login", json={"username": username, "password": password})
    if r.status_code != 200:
        fail(f"Login {username} devolvió {r.status_code}: {r.text[:200]}")
    print(f"  · login OK como {username}")


def list_clientes(client: httpx.Client) -> list:
    r = client.get("/api/clientes")
    if r.status_code != 200:
        fail(f"GET /api/clientes devolvió {r.status_code}: {r.text[:200]}")
    data = r.json()
    if not data.get("success"):
        fail(f"/api/clientes success=False: {data}")
    return data.get("clientes", [])


def create_cliente(client: httpx.Client, nombre: str, email: str) -> dict:
    r = client.post(
        "/api/clientes",
        json={"nombre": nombre, "email": email, "telefono": "", "direccion": ""},
    )
    if r.status_code not in (200, 201):
        fail(f"POST /api/clientes devolvió {r.status_code}: {r.text[:200]}")
    data = r.json()
    if not data.get("success"):
        fail(f"POST /api/clientes success=False: {data}")
    return data["cliente"]


def cleanup_cliente(client: httpx.Client, cid: str) -> None:
    r = client.delete(f"/api/clientes/{cid}")
    if r.status_code not in (200, 404):
        print(f"  · WARN: cleanup de {cid} devolvió {r.status_code}")


def run(base: str) -> int:
    with httpx.Client(base_url=base, timeout=10.0) as alice, httpx.Client(
        base_url=base, timeout=10.0
    ) as bob:
        banner("1) Login alice (premium) y bob (basico)")
        login(alice, "premium", "premium123")
        login(bob, "basico", "basico123")

        banner("2) Pre-check: sin auth debe dar 401")
        with httpx.Client(base_url=base) as anon:
            r = anon.get("/api/clientes")
            if r.status_code != 401:
                fail(f"Endpoint sin auth debería ser 401, fue {r.status_code}")
            print("  · 401 correcto")

        banner("3) Alice crea 'Importadora Alice'")
        c_alice = create_cliente(alice, "Importadora Alice", "alice@test.dev")
        print(f"  · cliente creado id={c_alice['id']}")

        banner("4) Bob lista sus clientes — NO debe ver el de Alice")
        bob_list = list_clientes(bob)
        nombres_bob = [c["nombre"] for c in bob_list]
        if any(c["id"] == c_alice["id"] for c in bob_list):
            fail(f"Bob vio el cliente de Alice! Bob ve: {nombres_bob}")
        print(f"  · Bob NO ve el cliente de Alice (ve: {nombres_bob})")

        banner("5) Bob crea 'Importadora Bob'")
        c_bob = create_cliente(bob, "Importadora Bob", "bob@test.dev")
        print(f"  · cliente creado id={c_bob['id']}")

        banner("6) Alice lista — NO debe ver el cliente de Bob")
        alice_list = list_clientes(alice)
        if any(c["id"] == c_bob["id"] for c in alice_list):
            fail(f"Alice vio el cliente de Bob! Alice ve: {[c['nombre'] for c in alice_list]}")
        print(f"  · Alice NO ve el cliente de Bob (ve: {[c['nombre'] for c in alice_list]})")

        banner("7) Cross-access: Bob pide GET /api/clientes/{id_de_alice}")
        r = bob.get(f"/api/clientes/{c_alice['id']}")
        if r.status_code != 404:
            fail(f"Esperado 404 para cross-access, fue {r.status_code}: {r.text[:200]}")
        print("  · 404 correcto (Bob no ve cliente de Alice aunque conozca el ID)")

        banner("8) Cross-access: Bob intenta DELETE del cliente de Alice")
        r = bob.delete(f"/api/clientes/{c_alice['id']}")
        if r.status_code != 404:
            fail(f"Esperado 404 para DELETE cross-access, fue {r.status_code}")
        # Confirmar que Alice sigue viendo su cliente.
        still = list_clientes(alice)
        if not any(c["id"] == c_alice["id"] for c in still):
            fail("El DELETE cross-access borró el cliente de Alice!")
        print("  · cliente de Alice intacto tras intento cross-delete")

        banner("9) Notas NCM: alice guarda nota privada en 8471")
        r = alice.post("/api/ncm/notas", json={"ncm": "84713010", "nota": "Nota privada de Alice"})
        if r.status_code != 200:
            fail(f"POST /api/ncm/notas devolvió {r.status_code}")
        print("  · nota guardada")

        banner("10) Bob lee notas del mismo NCM — NO debe ver la nota de Alice")
        r = bob.get("/api/ncm/notas/8471")
        if r.status_code != 200:
            fail(f"GET /api/ncm/notas devolvió {r.status_code}")
        notas_bob = r.json().get("notas", [])
        if "Nota privada de Alice" in notas_bob:
            fail(f"Bob leyó la nota de Alice: {notas_bob}")
        print(f"  · Bob NO ve la nota de Alice (ve: {notas_bob})")

        banner("11) Alice confirma que su nota está")
        r = alice.get("/api/ncm/notas/8471")
        notas_alice = r.json().get("notas", [])
        if "Nota privada de Alice" not in notas_alice:
            fail(f"Alice no ve su propia nota: {notas_alice}")
        print(f"  · Alice ve su nota (total: {len(notas_alice)} notas)")

        banner("12) Cleanup")
        cleanup_cliente(alice, c_alice["id"])
        cleanup_cliente(bob, c_bob["id"])
        # Borra la última nota de Alice (idx es posicional dentro del owner).
        idx = len(notas_alice) - 1
        alice.delete(f"/api/ncm/notas/8471/{idx}")

        banner("OK: aislamiento multi-tenant confirmado (clientes + notas NCM)")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE, help="URL base del servidor")
    args = parser.parse_args()
    return run(args.base)


if __name__ == "__main__":
    sys.exit(main())
