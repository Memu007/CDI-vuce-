"""RENDIMIENTO-1c: validar un PDF corre en un proceso aparte, con tope de
memoria y de tiempo, al subir facturas y al leer despachos.

El PDF es sintético: una hoja con 99 000 claves, repetida 200 veces en el
árbol de hojas. Pesa menos de 1 MB y abrirlo con pypdf para contar sus hojas
ocupa más de 1 GB.

Las dos pruebas de la app corren en un python nuevo: la memoria que se mide
es la de ese proceso (VmHWM de /proc), no la de pytest.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
solo_linux = pytest.mark.skipif(not Path("/proc/self/status").exists(), reason="mide /proc")


def pdf_que_se_infla(repeticiones=200, claves=99_000):
    from tests.pdf_bombas import _pdf

    def armar(add, objs):
        raiz = add(b"")
        extra = b" ".join(b"/K%d 1" % i for i in range(claves))
        hoja = add(b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 1 1] %s >>" % (raiz, extra))
        kids = b" ".join(b"%d 0 R" % hoja for _ in range(repeticiones))
        objs[raiz - 1] = b"<< /Type /Pages /Kids [" + kids + b"] /Count %d >>" % repeticiones
        return add(b"<< /Type /Catalog /Pages %d 0 R >>" % raiz)

    return _pdf(armar)


# La app con un usuario por pedido (cabecera x-usuario), sin límite de pedidos
# y sin lector con IA: la factura vuelve apenas pasa la validación.
_APP = r"""
import asyncio, json, re, sys, time
import httpx
from fastapi import Request
from proyecto_maria import main
from proyecto_maria.core.rate_limit import limiter
from tests.pdf_bombas import hojas
from tests.test_rendimiento1c import pdf_que_se_infla

limiter.enabled = False
main.lectura_automatica_disponible = lambda: False
async def _usuario(request: Request):
    u = request.headers.get("x-usuario", "a")
    return {"username": u, "roles": ["operador"], "effective_owner": u,
            "plan": "premium", "billing_status": "active"}
main.app.dependency_overrides[main.get_current_user] = _usuario
async def _cliente_propio(db, client_id, username):
    return None
main._get_owned_client = _cliente_propio

NORMAL = hojas([("FACTURA INVENTADA", 0)])
BOMBA = pdf_que_se_infla()

def pico_mb():
    return int(re.search(r"VmHWM:\s+(\d+)", open("/proc/self/status").read()).group(1)) // 1024

def subir(c, ruta, data, usuario="a"):
    return c.post(ruta, files={"file": ("x.pdf", data, "application/pdf")},
                  headers={"x-usuario": usuario})

FACTURA, DESPACHO = "/upload_pdf/public", "/api/clientes/c1/catalogo/despacho/leer"

async def memoria():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://t") as c:
        # Lo que se carga la primera vez (pypdf, el lector) entra en el antes.
        normales = [(await subir(c, r, NORMAL)).status_code for r in (FACTURA, DESPACHO)]
        antes = pico_mb()
        bombas = []
        for ruta in (FACTURA, DESPACHO):
            r = await subir(c, ruta, BOMBA)
            bombas.append([r.status_code, r.json().get("detail")])
        return {"normales": normales, "bombas": bombas, "antes_mb": antes, "crecio_mb": pico_mb() - antes}

async def diez_y_uno(ruta):
    real = asyncio.create_subprocess_exec
    hijos = []
    async def contar(*a, **k):
        hijos.append(1)
        return await real(*a, **k)
    asyncio.create_subprocess_exec = contar
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://t",
                                 timeout=120) as c:
        ruta = {"factura": FACTURA, "despacho": DESPACHO}[ruta]
        bombas = [asyncio.create_task(subir(c, ruta, BOMBA, "a")) for _ in range(10)]
        limite = time.monotonic() + 60
        while not hijos:  # la primera bomba de A ya está validándose
            assert time.monotonic() < limite, "ninguna validación empezó"
            await asyncio.sleep(0.01)
        t0 = time.monotonic()
        r = await subir(c, ruta, NORMAL, "b")
        demora = time.monotonic() - t0
        quedaban = sum(not b.done() for b in bombas)
        hechas = await asyncio.gather(*bombas)
    return {"b": [r.status_code, r.json().get("detail")], "demora_b": demora,
            "bombas_sin_terminar": quedaban,
            "bombas": sorted({(x.status_code, x.json().get("detail")) for x in hechas})}

print(json.dumps(asyncio.run({"memoria": memoria, "diez": diez_y_uno}[sys.argv[1]](*sys.argv[2:]))))
"""


def _correr(escenario, *args, **extra):
    entorno = {k: v for k, v in os.environ.items()}
    entorno["PYTHONPATH"] = str(_REPO)
    entorno.update(extra)
    r = subprocess.run([sys.executable, "-c", _APP, escenario, *args], capture_output=True, text=True,
                       cwd=_REPO, timeout=300, env=entorno)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


PESADO = "El PDF es demasiado pesado para abrirlo. Probá con otro archivo."


@solo_linux
def test_un_pdf_que_se_infla_no_hace_crecer_la_app():
    """Facturas y despachos: el PDF de 200 repeticiones se rechaza con un 400
    claro y la app no crece (antes crecía más de 1 GB)."""
    m = _correr("memoria")
    assert m["crecio_mb"] < 150, f"la app creció {m['crecio_mb']} MB: {m}"
    # La factura normal pasa la validación: el 503 es «sin lector con IA».
    assert m["normales"] == [503, 200], m
    assert m["bombas"] == [[400, PESADO], [400, PESADO]], m


@solo_linux
def test_diez_pdfs_pesados_de_uno_no_frenan_la_subida_de_otro():
    """Diez bombas a la vez de A: la factura normal de B no espera detrás de
    ellas. Se mide por orden, no por reloj: B termina con la mayoría de las
    bombas todavía en fila (sin la fila por usuario, B espera detrás de casi
    todas). Con 120 s, ninguna bomba se corta por tiempo en una máquina lenta."""
    # La factura de B pasa la validación y da 503 porque no hay lector con IA.
    for ruta, pasa in (("factura", 503), ("despacho", 200)):
        m = _correr("diez", ruta, PDF_VALIDATE_TIMEOUT_S="120")
        assert m["b"][0] == pasa, (ruta, m)
        assert m["bombas"] == [[400, PESADO]], (ruta, m)
        assert m["bombas_sin_terminar"] >= 5, f"{ruta}: B esperó detrás de las bombas de A: {m}"


def test_validar_aparte_devuelve_lo_mismo_que_antes():
    """Encriptado, sin hojas y roto dan los mismos 400 que antes; uno normal
    pasa con sus hojas."""
    import asyncio
    import io

    from pypdf import PdfWriter

    from proyecto_maria.core.despacho_lector import validar_pdf_aparte
    from tests.pdf_bombas import hojas

    w = PdfWriter()
    w.add_blank_page(200, 200)
    w.encrypt("una-clave")
    encriptado = io.BytesIO()
    w.write(encriptado)

    async def _todos():
        return [await validar_pdf_aparte(d, 30) for d in (
            hojas([("UNO", 0), ("DOS", 0)]), encriptado.getvalue(), b"%PDF-1.4 esto no es un pdf")]

    normal, encr, roto = asyncio.run(_todos())
    assert normal == {"encriptado": False, "paginas": 2}
    assert encr == {"encriptado": True, "paginas": 0}
    assert set(roto) == {"error"} and roto["error"], roto


def test_un_validador_que_se_cae_es_un_error_nuestro(monkeypatch, caplog):
    """Si el proceso que valida se cae sin contestar, es un 500 con su registro,
    no un «PDF inválido» que culpa al archivo."""
    import asyncio

    from fastapi import HTTPException

    from proyecto_maria.security.file_security import validate_file_upload
    from tests.pdf_bombas import hojas

    real = asyncio.create_subprocess_exec

    async def se_cae(*args, **kwargs):
        assert args[-1] == "validar"
        return await real(sys.executable, "-c", "import sys; sys.exit(7)", **kwargs)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", se_cae)

    with pytest.raises(HTTPException) as e:
        asyncio.run(validate_file_upload(_Subida(hojas([("UNO", 0)])), "pdf"))
    assert e.value.status_code == 500, e.value.detail
    assert "Invalid PDF" not in e.value.detail
    assert "el validador de PDF salió con 7" in caplog.text


class _Subida:
    filename, content_type = "x.pdf", "application/pdf"

    def __init__(self, data):
        self._data = data

    async def read(self, *_):
        return self._data

    async def seek(self, *_):
        return None


def test_esperar_un_lugar_no_culpa_al_archivo(monkeypatch):
    """Si un PDF normal no consigue lugar a tiempo, porque otros usuarios ocupan
    los dos o el mismo usuario ya está validando, es un 503 «probá de nuevo»,
    no el 400 que manda a cambiar de archivo. La fila del usuario se borra al
    terminar."""
    import asyncio

    from fastapi import HTTPException

    from proyecto_maria.core import despacho_lector
    from proyecto_maria.security.file_security import validate_file_upload
    from tests.pdf_bombas import hojas

    real = asyncio.create_subprocess_exec
    monkeypatch.setenv("PDF_VALIDATE_TIMEOUT_S", "1")
    normal = hojas([("UNO", 0)])

    async def escenario(lentos):
        lanzados = []

        async def lento(*args, **kwargs):  # un PDF que da mucho trabajo
            lanzados.append(1)
            return await real(sys.executable, "-c", "import time; time.sleep(60)", **kwargs)

        monkeypatch.setattr(asyncio, "create_subprocess_exec", lento)
        ocupan = [asyncio.create_task(despacho_lector.validar_pdf_aparte(normal, 30, clave=u))
                  for u in lentos]
        while len(lanzados) < len(lentos):
            await asyncio.sleep(0.01)
        monkeypatch.setattr(asyncio, "create_subprocess_exec", real)
        try:
            await asyncio.wait_for(validate_file_upload(_Subida(normal), "pdf", clave="a"), 10)
            resultado = "pasó"
        except HTTPException as e:
            resultado = (e.status_code, e.detail)
        for tarea in ocupan:
            tarea.cancel()
        await asyncio.gather(*ocupan, return_exceptions=True)
        return resultado, despacho_lector._VALIDANDO[asyncio.get_running_loop()][1]

    for lentos in (["b", "c"], ["a"]):
        resultado, filas = asyncio.run(escenario(lentos))
        assert resultado != "pasó" and resultado[0] == 503, (lentos, resultado)
        assert "otro archivo" not in resultado[1], (lentos, resultado)
        assert filas == {}, (lentos, filas)


def test_quedarse_sin_memoria_en_c_es_demasiado_pesado(monkeypatch):
    """Bajo el tope de memoria, pypdf puede fallar con SystemError en vez de
    MemoryError: es «demasiado pesado», no un «Invalid PDF» con texto interno."""
    import pypdf

    from proyecto_maria.core.despacho_lector import validar_pdf

    def sin_memoria(*_):
        raise SystemError("error return without exception set")

    monkeypatch.setattr(pypdf, "PdfReader", sin_memoria)
    with pytest.raises(MemoryError):
        validar_pdf(b"%PDF-1.4")


class _Ocupante:
    """Un hijo que valida hasta que `libre` se prende (o lo matan)."""

    def __init__(self, libre):
        self.libre, self.returncode = libre, None
        self.stdin = self.stdout = self.stderr = self

    def write(self, _):
        pass

    async def drain(self):
        pass

    def close(self):
        pass

    async def read(self, *_):
        await self.libre.wait()
        return b""

    async def wait(self):
        await self.libre.wait()
        self.returncode = 0
        return 0

    def kill(self):
        self.libre.set()


TOPE = 2.0


@pytest.mark.parametrize("libera_antes_del_tope, esperado", [
    (0.5, {"pasó"}),            # esperó casi todo el tope
    (0.08, {"pasó"}),           # deja menos de lo que tarda un PDF normal
    (0.0, {"pasó", 503}),       # el tope justo
    (-0.2, {503}),              # no hubo lugar a tiempo
], ids=["casi-todo", "menos-que-un-pdf", "justo", "pasado"])
def test_esperar_casi_todo_el_tope_no_culpa_al_archivo(monkeypatch, libera_antes_del_tope, esperado):
    """B y C ocupan los dos lugares y los liberan cerca del tope de A. A, con un
    PDF normal, se valida con su tiempo entero o recibe el 503 de «sin lugar»:
    nunca el 400 que lo manda a cambiar de archivo."""
    import asyncio
    import time

    from fastapi import HTTPException

    from proyecto_maria.core import despacho_lector
    from proyecto_maria.security.file_security import validate_file_upload
    from tests.pdf_bombas import hojas

    monkeypatch.setenv("PDF_VALIDATE_TIMEOUT_S", str(TOPE))
    normal = hojas([("UNO", 0)])
    real = asyncio.create_subprocess_exec

    async def escenario():
        t = time.monotonic()
        assert await despacho_lector.validar_pdf_aparte(normal, 30) == {"encriptado": False, "paginas": 1}
        assert time.monotonic() - t > 0.08, "un PDF normal tarda menos que lo que deja el caso"
        loop = asyncio.get_running_loop()
        libre = asyncio.Event()

        async def ocupa(*_, **__):
            return _Ocupante(libre)

        monkeypatch.setattr(asyncio, "create_subprocess_exec", ocupa)
        ocupan = [asyncio.create_task(despacho_lector.validar_pdf_aparte(normal, 30, clave=u))
                  for u in ("b", "c")]
        semaforo = despacho_lector._VALIDANDO[loop][0]
        while not semaforo.locked():
            await asyncio.sleep(0)
        monkeypatch.setattr(asyncio, "create_subprocess_exec", real)
        loop.call_at(loop.time() + TOPE - libera_antes_del_tope, libre.set)
        try:
            await validate_file_upload(_Subida(normal), "pdf", clave="a")
            resultado = "pasó"
        except HTTPException as e:
            resultado = e.status_code if e.status_code == 503 else (e.status_code, e.detail)
        libre.set()
        await asyncio.gather(*ocupan, return_exceptions=True)
        return resultado

    resultado = asyncio.run(escenario())
    assert resultado in esperado, resultado


def test_validar_tiene_tope_de_cpu(monkeypatch):
    """Un PDF que da más trabajo que el tope de CPU se corta y es «demasiado
    pesado»; uno normal, con el mismo tope, pasa."""
    import asyncio

    from fastapi import HTTPException

    from proyecto_maria.core import despacho_lector
    from proyecto_maria.security.file_security import validate_file_upload
    from tests.pdf_bombas import hojas

    # Validarlo gasta unos 0.25 s de CPU y menos de 100 MB.
    trabajoso = pdf_que_se_infla(repeticiones=10, claves=50_000)
    monkeypatch.setattr(despacho_lector, "_MAX_CPU_LECTURA", 0.05)

    async def subir(data):
        try:
            await validate_file_upload(_Subida(data), "pdf")
            return "pasó"
        except HTTPException as e:
            return e.status_code, e.detail

    assert asyncio.run(subir(hojas([("UNO", 0)]))) == "pasó"
    assert asyncio.run(subir(trabajoso)) == (400, PESADO)
