"""EXCEL-1 (D12): leer un Excel no frena el sitio.

Cada ruta que lee un Excel lo hace en otro hilo y con tiempo máximo, como el
PDF (RENDIMIENTO-1). Las pruebas simulan una lectura lenta que retiene el
hilo y miden cuánto tarda /health desde que empieza esa lectura.
"""
import asyncio
import io
import time

import httpx
import pandas
import pytest

from proyecto_maria import main

LENTO_S = 1.5
INICIO = {}
USUARIO = {"username": "exc1", "roles": ["operador"], "effective_owner": "exc1",
           "plan": "premium", "billing_status": "active"}


def _xlsx() -> bytes:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Cliente", "CUIT", "Descripcion", "NCM", "Cantidad", "Precio"])
    ws.append(["ACME SA", "30712345678", "Notebook", "8471.30.12", 2, 500])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


XLSX = _xlsx()


def _bloquear():
    # La primera lectura lenta marca el inicio: si después viene otra (la
    # validación y la lectura del mismo archivo), no lo pisa.
    INICIO.setdefault("t", time.monotonic())
    time.sleep(LENTO_S)


@pytest.fixture(autouse=True)
def _entorno(monkeypatch):
    from proyecto_maria.core.rate_limit import limiter
    monkeypatch.setattr(limiter, "enabled", False)
    monkeypatch.setattr(main, "_POOL_LECTURA_PDF", None)
    main.app.dependency_overrides[main.get_current_user] = lambda: dict(USUARIO)
    yield
    main.app.dependency_overrides.pop(main.get_current_user, None)


@pytest.fixture
def excel_lento(monkeypatch):
    original = pandas.read_excel

    def _lento(*a, **k):
        _bloquear()
        return original(*a, **k)
    monkeypatch.setattr(pandas, "read_excel", _lento)


async def _health_mientras(pedido):
    INICIO.clear()
    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://t", timeout=30) as c:
        lento = asyncio.create_task(pedido(c))
        limite = time.monotonic() + 10
        while "t" not in INICIO:
            assert time.monotonic() < limite, "la lectura lenta nunca empezó"
            await asyncio.sleep(0.005)
        h = await c.get("/health")
        demora = time.monotonic() - INICIO["t"]
        assert h.status_code == 200
        return demora, await lento


def _archivo(nombre="planilla.xlsx"):
    return {"file": (nombre, XLSX,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}


RUTAS = {
    "upload_excel_v2": lambda c: c.post("/upload_excel_v2/", files=_archivo()),
    "ncm_import_historial": lambda c: c.post("/api/ncm/import-historial", files=_archivo()),
    "migraciones_analyze": lambda c: c.post("/api/migrations/analyze", files=_archivo()),
}


@pytest.mark.parametrize("ruta", sorted(RUTAS))
def test_health_responde_mientras_se_lee_un_excel(excel_lento, ruta):
    demora, r = asyncio.run(_health_mientras(RUTAS[ruta]))
    assert r.status_code < 500, f"{ruta}: {r.status_code} {r.text[:200]}"
    assert demora < 0.5, f"{ruta}: /health tardó {demora:.2f} s mientras se leía un Excel"


def test_health_responde_mientras_se_valida_un_excel(monkeypatch):
    import openpyxl
    original = openpyxl.load_workbook

    def _lento(*a, **k):
        _bloquear()
        return original(*a, **k)
    monkeypatch.setattr(openpyxl, "load_workbook", _lento)
    demora, r = asyncio.run(_health_mientras(RUTAS["upload_excel_v2"]))
    assert r.status_code < 500, r.text[:200]
    assert demora < 0.5, f"/health tardó {demora:.2f} s mientras se validaba un Excel"


@pytest.mark.parametrize("ruta", sorted(RUTAS))
def test_leer_un_excel_tiene_tiempo_maximo(excel_lento, monkeypatch, ruta):
    monkeypatch.setenv("EXCEL_READ_TIMEOUT_S", "0.3")

    async def _ir():
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t", timeout=30) as c:
            t0 = time.monotonic()
            r = await RUTAS[ruta](c)
            return r, time.monotonic() - t0

    r, demora = asyncio.run(_ir())
    assert r.status_code == 504, f"{ruta}: {r.status_code} {r.text[:200]}"
    cuerpo = r.json()
    assert cuerpo.get("code") == "lectura_excel_demasiado_larga", cuerpo
    assert "tardó demasiado" in str(cuerpo.get("detail")), cuerpo
    assert demora < LENTO_S, f"{ruta}: esperó toda la lectura ({demora:.2f} s)"
