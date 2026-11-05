"""RENDIMIENTO-1d: sacar el texto del PDF para adivinar el vendedor corre en
el proceso aparte, con los mismos topes que la validación.

El PDF es sintético: una hoja con 20 fuentes cuyo mapa de caracteres pesa
1,4 MB comprimido y 70 MB al inflarse. Pasa la validación, que no lee las
fuentes; sacar su texto en la app la hacía crecer más de 1 GB. Otro, de 1 KB,
da 28 millones de caracteres de texto: lo que vuelve a la app tiene tope.

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
from tests.pdf_bombas import hojas, muchas_fuentes, texto_que_se_infla

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
        salida = {"normal": normal}
        for nombre, bomba in (("fuentes", muchas_fuentes(20, 70 * 1024)), ("texto", texto_que_se_infla())):
            antes = pico_mb()
            salida[nombre] = await subir(c, bomba) + [pico_mb() - antes]
        return salida

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
    for bomba in ("fuentes", "texto"):
        # Sin vendedor, la factura sigue: la adivinanza es opcional.
        assert m[bomba][:2] == [200, None], m
        assert m[bomba][2] < 150, f"{bomba}: la app creció {m[bomba][2]} MB: {m}"


def test_el_texto_corta_cada_flujo_que_se_infla():
    """Una fuente de 40 MB al inflarse: el tope por flujo la corta en 8 MB,
    sin esperar al tope de memoria del proceso aparte."""
    import tracemalloc
    from proyecto_maria.core.despacho_lector import texto_plano_del_pdf
    from tests.pdf_bombas import muchas_fuentes
    pdf = muchas_fuentes(1, 40 * 1024)
    tracemalloc.start()
    try:
        texto_plano_del_pdf(pdf)
        pico_mb = tracemalloc.get_traced_memory()[1] >> 20
    finally:
        tracemalloc.stop()
    assert pico_mb < 50, f"sacar el texto llegó a {pico_mb} MB"


def test_el_texto_tiene_tope_de_cpu():
    """Dos hojas que cuestan casi un segundo de CPU cada una: con tope de
    0,2 s el texto se corta, en vez de esperar al tiempo máximo del vendedor."""
    from proyecto_maria.core.despacho_lector import _DemasiadoTrabajo, texto_plano_del_pdf
    from tests.pdf_bombas import trabajo
    with pytest.raises(_DemasiadoTrabajo):
        texto_plano_del_pdf(trabajo(hojas=2), limite_cpu_s=0.2)


def test_el_texto_no_ocupa_los_lugares_de_validar(monkeypatch):
    """Sacar el texto del vendedor es opcional: aunque tarde, de otros
    usuarios o del mismo, la validación de una subida no espera detrás."""
    import asyncio

    from proyecto_maria.core import despacho_lector
    from proyecto_maria.security.file_security import validate_file_upload
    from tests.pdf_bombas import hojas
    from tests.test_rendimiento1c import _Subida

    real = asyncio.create_subprocess_exec
    monkeypatch.setenv("PDF_VALIDATE_TIMEOUT_S", "1")
    normal = hojas([("UNO", 0)])

    async def escenario(lentos):
        lanzados = []

        async def lento(*args, **kwargs):
            lanzados.append(1)
            return await real(sys.executable, "-c", "import time; time.sleep(60)", **kwargs)

        monkeypatch.setattr(asyncio, "create_subprocess_exec", lento)
        ocupan = [asyncio.create_task(
            despacho_lector.validar_pdf_aparte(normal, 30, clave=u, modo="texto")) for u in lentos]
        while len(lanzados) < len(lentos):
            await asyncio.sleep(0.01)
        monkeypatch.setattr(asyncio, "create_subprocess_exec", real)
        try:
            await asyncio.wait_for(validate_file_upload(_Subida(normal), "pdf", clave="a"), 10)
            resultado = "pasó"
        except Exception as e:
            resultado = getattr(e, "status_code", repr(e))
        for tarea in ocupan:
            tarea.cancel()
        await asyncio.gather(*ocupan, return_exceptions=True)
        return resultado

    for lentos in (["b", "c"], ["a"]):
        assert asyncio.run(escenario(lentos)) == "pasó", lentos


@pytest.mark.parametrize("libera_antes_del_tope, esperado", [
    (0.5, {"leyó"}),            # esperó casi todo el tope
    (0.08, {"leyó"}),           # deja menos de lo que tarda un PDF normal
    (0.0, {"leyó", "sin lugar"}),
    (-0.2, {"sin lugar"}),      # no hubo lugar a tiempo
], ids=["casi-todo", "menos-que-un-pdf", "justo", "pasado"])
def test_esperar_para_leer_un_despacho_no_se_cobra_al_pdf(monkeypatch, libera_antes_del_tope, esperado):
    """B y C ocupan los dos lugares del lector y los liberan cerca del tope de A.
    A, con un PDF normal, se lee con su tiempo entero o se queda sin lugar:
    nunca vence leyendo por lo que esperó."""
    import asyncio
    import time

    from proyecto_maria.core import despacho_lector
    from tests.pdf_bombas import hojas
    from tests.test_rendimiento1c import TOPE, _Ocupante

    normal = hojas([("UNO", 0)])
    real = asyncio.create_subprocess_exec

    async def escenario():
        t = time.monotonic()
        assert isinstance(await despacho_lector.leer_despacho_aparte(normal, 30), dict)
        assert time.monotonic() - t > 0.08, "un PDF normal tarda menos que lo que deja el caso"
        loop = asyncio.get_running_loop()
        libre = asyncio.Event()

        async def ocupa(*_, **__):
            return _Ocupante(libre)

        monkeypatch.setattr(asyncio, "create_subprocess_exec", ocupa)
        ocupan = [asyncio.create_task(despacho_lector.leer_despacho_aparte(normal, 30, clave=u))
                  for u in ("b", "c")]
        semaforo = despacho_lector._SEMAFOROS[loop]

        async def ocupados():
            while not semaforo.locked():
                await asyncio.sleep(0)

        await asyncio.wait_for(ocupados(), 5)
        monkeypatch.setattr(asyncio, "create_subprocess_exec", real)
        loop.call_at(loop.time() + TOPE - libera_antes_del_tope, libre.set)
        try:
            leido = await despacho_lector.leer_despacho_aparte(normal, TOPE, clave="a")
            resultado = "leyó" if isinstance(leido, dict) else leido
        except despacho_lector.SinLugar:
            resultado = "sin lugar"
        except TimeoutError:
            resultado = "venció leyendo"
        libre.set()
        await asyncio.gather(*ocupan, return_exceptions=True)
        return resultado

    resultado = asyncio.run(escenario())
    assert resultado in esperado, resultado
