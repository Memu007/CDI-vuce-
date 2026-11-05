"""RENDIMIENTO-1d: sacar el texto del PDF para adivinar el vendedor corre en
el proceso aparte, con los mismos topes que la validación.

El PDF es sintético: una hoja con 20 fuentes cuyo mapa de caracteres pesa
1,4 MB comprimido y 70 MB al inflarse. Pasa la validación, que no lee las
fuentes; sacar su texto en la app la hacía crecer más de 1 GB.

La app corre en un python nuevo: la memoria que se mide es la de ese proceso
(VmHWM de /proc), no la de pytest.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
solo_linux = pytest.mark.skipif(not Path("/proc/self/status").exists(), reason="mide /proc")

# Una factura sin vendedor, con un ítem: la app intenta adivinarlo del texto.
_APP = r"""
import asyncio, json, re
import httpx
from proyecto_maria import main
from proyecto_maria.core import ai_quota
from proyecto_maria.core.rate_limit import limiter
from tests.pdf_bombas import hojas, muchas_fuentes

limiter.enabled = False
main.lectura_automatica_disponible = lambda: True
ai_quota.enforce_pdf_quota = lambda *a, **k: None
main.app.dependency_overrides[main.get_current_user] = lambda: {
    "username": "r1d", "roles": ["operador"], "effective_owner": "r1d",
    "plan": "premium", "billing_status": "active"}
main.process_pdf = lambda *_: {
    "documento": {"tipo": "factura_comercial", "operacion": "importacion", "destinacion": ""},
    "items": [{"descripcion": "x"}], "operacion": {}}

def pico_mb():
    return int(re.search(r"VmHWM:\s+(\d+)", open("/proc/self/status").read()).group(1)) // 1024

async def subir(c, data):
    r = await c.post("/upload_pdf/public", files={"file": ("x.pdf", data, "application/pdf")})
    return [r.status_code, r.json().get("operacion", {}).get("vendedor_nombre")]

async def memoria():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://t") as c:
        # Lo que se carga la primera vez (pypdf, el proceso aparte) entra en el antes.
        normal = await subir(c, hojas([("VENDOR: ACME TRADING CO LTD", 0)]))
        antes = pico_mb()
        bomba = await subir(c, muchas_fuentes(20, 70 * 1024))
        return {"normal": normal, "bomba": bomba, "crecio_mb": pico_mb() - antes}

print(json.dumps(asyncio.run(memoria())))
"""


@solo_linux
def test_el_texto_del_vendedor_no_hace_crecer_la_app():
    entorno = dict(os.environ, PYTHONPATH=str(_REPO))
    r = subprocess.run([sys.executable, "-c", _APP], capture_output=True, text=True,
                       cwd=_REPO, timeout=300, env=entorno)
    assert r.returncode == 0, r.stderr[-3000:]
    m = json.loads(r.stdout.strip().splitlines()[-1])
    assert m["normal"] == [200, "ACME TRADING CO LTD"], m
    # Sin vendedor, la factura sigue: la adivinanza es opcional.
    assert m["bomba"] == [200, None], m
    assert m["crecio_mb"] < 150, f"la app creció {m['crecio_mb']} MB: {m}"
