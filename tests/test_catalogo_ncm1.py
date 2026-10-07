"""CATALOGO-NCM-1: el catálogo NCM vigente de ARCA (2026-10-07).

- El catálogo sale del ZIP que trajo Emi (`docs/pm/datos/`), con el importador.
- Una NCM dada de baja (estaba en el nomenclador de 2018 y no en el vigente)
  avisa que la posición ya no existe y que hay que buscar la nueva: aviso,
  no freno.
- La sugerencia de NCM no propone una posición dada de baja sin decirlo.
- El CSV breve de respaldo (`ncm_mercosur.csv`), con códigos que no existen,
  ya no se usa.
"""
import csv
import gzip
import io
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from proyecto_maria.core import ncm_catalog

RAIZ = Path(__file__).resolve().parents[1]
ZIP = RAIZ / "docs" / "pm" / "datos" / "arancel_ARCA_07102026.zip"


@pytest.fixture(autouse=True)
def _sin_cache():
    cachés = (ncm_catalog.load_catalog, ncm_catalog.get_catalog_metadata,
              ncm_catalog._codigos_vigentes, ncm_catalog._bajas)
    for f in cachés:
        f.cache_clear()
    yield
    for f in cachés:
        f.cache_clear()


def _codigos():
    return {it.codigo for it in ncm_catalog.load_catalog()}


def test_el_catalogo_es_el_vigente():
    codigos = _codigos()
    assert len(codigos) == 10504
    assert {"85171300", "85249100", "85491100"} <= codigos
    assert "85171231" not in codigos
    # Las NCM de los dos archivos reales siguen.
    assert {"84714900", "84798999"} <= codigos


def test_la_metadata_dice_de_donde_vino():
    meta = ncm_catalog.get_catalog_metadata()
    assert meta["updated_at"] == "2026-10-07"
    assert meta["source_file"] == "nomenclador_07102026.txt"
    assert meta["archive_sha256"] == "0fb407ceebd3db6ef4b9314ba51c204383db9c5d5c707eb34ce6ced85f2b5d44"
    assert meta["ncm_count"] == 10504
    assert "Emi" in meta["obtenido"]


def test_el_catalogo_es_el_que_sale_del_zip():
    with ZipFile(ZIP) as archivo:
        nombre = next(n for n in archivo.namelist() if "nomenclador" in n.lower())
        filas = ncm_catalog.parse_arca_nomenclador(archivo.read(nombre).decode("cp1252").splitlines())
    with gzip.open(ncm_catalog.DEFAULT_CSV, "rt", encoding="utf-8", newline="") as fh:
        guardadas = [(r["codigo"], r["descripcion"]) for r in csv.DictReader(fh)]
    assert guardadas == [(f["codigo"], f["descripcion"]) for f in filas]


# --- Las bajas -------------------------------------------------------------

def test_una_ncm_dada_de_baja_se_reconoce():
    baja = ncm_catalog.ncm_de_baja("8517.12.31")
    assert baja and baja["descripcion"]
    assert ncm_catalog.ncm_de_baja("85171300") is None  # vigente
    assert ncm_catalog.ncm_de_baja("99999999") is None  # nunca existió


def test_las_bajas_son_las_del_cambio_de_nomenclador():
    bajas = json.loads((ncm_catalog.DATA_DIR / "ncm_bajas.json").read_text(encoding="utf-8"))
    assert len(bajas["codigos"]) == 522
    assert not set(bajas["codigos"]) & _codigos()


@pytest.mark.parametrize("codigo, dice", [
    ("85171231", "se dio de baja"),
    ("8517.12.31.000X", "se dio de baja"),
    ("99999999", "no está en el nomenclador vigente"),
])
def test_el_aviso_dice_que_paso(codigo, dice):
    aviso = ncm_catalog.aviso_de_ncm(codigo)
    assert dice in aviso, aviso
    if dice == "se dio de baja":
        assert "8517.12.31" in aviso and "buscá la nueva" in aviso


@pytest.mark.parametrize("codigo", ["85171300", "8471.49.00.100D", "", "8471"])
def test_sin_aviso_para_una_vigente_o_incompleta(codigo):
    assert ncm_catalog.aviso_de_ncm(codigo) == ""


def test_la_validacion_avisa_la_baja_sin_frenar(client, auth_override):
    items = [{"pieza": "85171231000X", "descripcion": "Teléfono celular de prueba", "origen": "CN",
              "cantidad": 2, "valor_unitario": 100, "peso_unitario": 0.2}]
    r = client.post("/api/validate/smart", json={"items": items})
    assert r.status_code == 200, r.text
    datos = r.json()
    assert any("se dio de baja" in a for a in datos["advertencias"]), datos["advertencias"]
    assert not any("baja" in e for e in datos["errores"]), datos["errores"]


# --- La sugerencia ---------------------------------------------------------

def test_la_sugerencia_del_historial_marca_la_baja(client, auth_override, monkeypatch):
    from proyecto_maria import main
    monkeypatch.setenv("NCM_GEMINI_FALLBACK", "false")
    monkeypatch.setattr(main, "load_ncm_historial", lambda usuario: {
        "telefono celular de prueba": {"ncm": "85171231", "count": 3},
        "notebook de prueba": {"ncm": "84713012", "count": 1},
    })
    r = client.post("/api/ncm/sugerir", json={"descripcion": "telefono celular de prueba"})
    assert r.status_code == 200, r.text
    sug = {s["ncm"]: s for s in r.json()["sugerencias"]}
    assert sug["85171231"]["baja"] is True
    assert "se dio de baja" in sug["85171231"]["aviso"]


def test_un_codigo_dado_de_baja_escrito_lo_dice(client, auth_override, monkeypatch):
    monkeypatch.setenv("NCM_GEMINI_FALLBACK", "false")
    r = client.post("/api/ncm/sugerir", json={"descripcion": "8517.12.31"})
    assert r.status_code == 200, r.text
    datos = r.json()
    assert not any(s["ncm"].startswith("85171231") and not s.get("baja") for s in datos["sugerencias"])
    assert "se dio de baja" in datos.get("message", ""), datos


# --- El respaldo viejo -----------------------------------------------------

def test_el_respaldo_con_codigos_viejos_no_se_usa(tmp_path):
    assert not (ncm_catalog.DATA_DIR / "ncm_mercosur.csv").exists()
    assert not hasattr(ncm_catalog, "LEGACY_CSV")
    assert ncm_catalog.load_catalog(tmp_path / "no_existe.csv.gz") == []
