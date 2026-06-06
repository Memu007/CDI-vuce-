"""Tests del CORE del producto: generación del MARIA.TXT (T12, Sprint 25 Día 8).

Dos capas:
1. Unit tests de `generate_maria_txt` (función pura, sin red ni DB): estructura
   del TXT, totales, formato NCM, códigos de país, proporcional flete/seguro.
2. E2E del endpoint `/generate_maria` (auth + validación + response shape).

NO testea la extracción con Gemini Vision (requiere red + tokens). Eso queda
en smoke manual. Acá protegemos la parte determinística: que el TXT que pega
el despachante en el Kit SIM salga bien armado.
"""
import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("EMAIL_VERIFICATION_REQUIRED", "false")

from proyecto_maria.core.maria_generator import (  # noqa: E402
    generate_maria_txt,
    validate_items_for_maria,
    get_pais_codigo,
)
from proyecto_maria.main import app  # noqa: E402


# ====================================================================
# 1. UNIT TESTS — generate_maria_txt (función pura)
# ====================================================================

ITEMS_OK = [
    {"pieza": "84713010", "descripcion": "Laptop", "cantidad": 10,
     "valor_unitario": 500, "peso_unitario": 2.5, "origen": "CN"},
    {"pieza": "85171200", "descripcion": "Celular", "cantidad": 20,
     "valor_unitario": 300, "peso_unitario": 0.2, "origen": "US"},
]


def test_txt_tiene_secciones_obligatorias():
    """El TXT debe contener las secciones que el Kit SIM espera."""
    txt = generate_maria_txt("OP123456", ITEMS_OK)
    for seccion in ("[DDT]", "[CPL]", "[DVD]", "[ART]", "[SBT]"):
        assert seccion in txt, f"Falta la sección {seccion}"


def test_txt_usa_crlf():
    """MARIA/Windows espera saltos de línea CRLF, no solo LF."""
    txt = generate_maria_txt("OP123456", ITEMS_OK)
    assert "\r\n" in txt, "El TXT debe usar CRLF"


def test_txt_un_art_por_item():
    """Debe haber exactamente un bloque [ART] por item."""
    txt = generate_maria_txt("OP123456", ITEMS_OK)
    assert txt.count("[ART]") == len(ITEMS_OK)


def test_txt_total_fob_correcto():
    """MDDTFOB debe ser la suma de cantidad*valor_unitario de todos los items."""
    txt = generate_maria_txt("OP123456", ITEMS_OK)
    # 10*500 + 20*300 = 5000 + 6000 = 11000
    assert "MDDTFOB=11000.00" in txt


def test_txt_usa_valor_total_si_viene():
    """Si el item trae valor_total explícito, se usa ese en vez de calcular."""
    items = [{"pieza": "84713010", "descripcion": "X", "cantidad": 3,
              "valor_unitario": 100, "valor_total": 999, "origen": "CN"}]
    txt = generate_maria_txt("OP1", items)
    assert "MDDTFOB=999.00" in txt


def test_txt_formatea_ncm_con_puntos():
    """NCM de 8+ dígitos se formatea con puntos para el Kit SIM."""
    items = [{"pieza": "84798999900H", "descripcion": "X", "cantidad": 1,
              "valor_unitario": 10, "origen": "CN"}]
    txt = generate_maria_txt("OP1", items)
    # 8479.89.99 + sufijo
    assert "IESPNCE=8479.89.99" in txt


def test_txt_incluye_cuit_agr():
    """El CUIT del despachante debe aparecer como CDDTAGR en la cabecera."""
    txt = generate_maria_txt("OP1", ITEMS_OK, cuit_agr="20304050607")
    assert "CDDTAGR=20304050607" in txt


def test_txt_sin_cuit_agr_no_emite_linea():
    """Si no hay CUIT del despachante, no se emite la línea CDDTAGR."""
    txt = generate_maria_txt("OP1", ITEMS_OK, cuit_agr="")
    assert "CDDTAGR=" not in txt


def test_txt_defaults_aduana_destinacion():
    """Sin config, usa defaults seguros (001 / IC04)."""
    txt = generate_maria_txt("OP1", ITEMS_OK)
    assert "CDDTBUR=001" in txt
    assert "CDDTTYPDEC=IC04" in txt


def test_txt_respeta_aduana_destinacion_custom():
    """Config custom de aduana/destinación se respeta."""
    txt = generate_maria_txt("OP1", ITEMS_OK, aduana_codigo="073", tipo_destinacion="IC05")
    assert "CDDTBUR=073" in txt
    assert "CDDTTYPDEC=IC05" in txt


def test_txt_incoterm_y_moneda():
    """Incoterm y moneda se reflejan en la cabecera."""
    txt = generate_maria_txt("OP1", ITEMS_OK, moneda="DOL", incoterm="CIF")
    assert "CDDTINCOTE=CIF" in txt
    assert "CDDTDEVFOB=DOL" in txt


def test_txt_proporcional_flete_seguro():
    """Flete y seguro se reparten proporcional al FOB de cada item."""
    # 1 item con todo el FOB → recibe el 100% del flete.
    items = [{"pieza": "84713010", "descripcion": "X", "cantidad": 1,
              "valor_unitario": 1000, "origen": "CN"}]
    txt = generate_maria_txt("OP1", items, flete=100, seguro=50)
    assert "MARTFLE=100.00" in txt
    assert "MARTASS=50.00" in txt


def test_get_pais_codigo_oficial_maria():
    """Códigos OFICIALES del Sistema MARIA (AFIP). La tabla vieja estaba mal:
    China era 218 (=México), Alemania 212 (=EEUU), España 210 (=Ecuador), etc.
    """
    assert get_pais_codigo("CN") == 310
    assert get_pais_codigo("China") == 310
    assert get_pais_codigo("US") == 212
    assert get_pais_codigo("Estados Unidos") == 212
    assert get_pais_codigo("Mexico") == 218
    assert get_pais_codigo("Alemania") == 438
    assert get_pais_codigo("Japon") == 320
    assert get_pais_codigo("") == 310  # default China (codigo oficial)
    assert get_pais_codigo("203") == 203  # ya numérico


def test_get_pais_codigo_no_colisiona_por_prefijo():
    """Regresión: nombres completos no deben colisionar por prefijo de 2 letras.

    Bug histórico: 'China' devolvía Chile y 'España' devolvía Estados Unidos
    porque el match por prefijo de 2 chars pegaba en el país equivocado antes
    del match exacto. Resultado: código de país errado en el TXT aduanero.
    """
    assert get_pais_codigo("China") == 310
    assert get_pais_codigo("Chile") == 208
    assert get_pais_codigo("España") == 410
    assert get_pais_codigo("Estados Unidos") == 212


def test_txt_no_filtra_datos_de_otro_cliente():
    """Regresión: sin domicilio/fecha del cliente NO deben aparecer los datos
    hardcodeados del sample (otro cliente) en la declaración aduanera.
    """
    txt = generate_maria_txt("OP1", ITEMS_OK)
    assert "DR. SALVADOR MAZZA 1996" not in txt
    assert "13/07/2016" not in txt
    # Sin dato, el bloque [CPL] correspondiente directamente no se emite.
    assert "CCPL=DOMICIL.ESTABLEC" not in txt
    assert "CCPL=FECHA INIC.ACTIV" not in txt


def test_txt_usa_datos_reales_del_cliente():
    """Cuando vienen domicilio y fecha del cliente, se emiten esos valores."""
    txt = generate_maria_txt(
        "OP1", ITEMS_OK,
        comprador_domicilio="AV. CORRIENTES 1234",
        comprador_fecha_inic_activ="01/03/2020",
    )
    assert "CCPL=DOMICIL.ESTABLEC" in txt
    assert "AV. CORRIENTES 1234" in txt
    assert "CCPL=FECHA INIC.ACTIV" in txt
    assert "01/03/2020" in txt


def test_txt_procedencia_default_es_origen():
    """Sin procedencia explícita, CARTPAYPRC debe igualar al origen (CARTPAYORI),
    no un hardcode. Antes era fijo 222 (que en la tabla oficial es Perú).
    """
    items = [{"pieza": "84713010", "descripcion": "X", "cantidad": 1,
              "valor_unitario": 100, "origen": "China"}]
    txt = generate_maria_txt("OP1", items)
    assert "CARTPAYORI=310" in txt   # China oficial
    assert "CARTPAYPRC=310" in txt   # procedencia = origen
    assert "CARTPAYPRC=222" not in txt


def test_txt_procedencia_explicita():
    """Si el item trae procedencia distinta al origen, se respeta."""
    items = [{"pieza": "84713010", "descripcion": "X", "cantidad": 1,
              "valor_unitario": 100, "origen": "China",
              "pais_procedencia": "Uruguay"}]
    txt = generate_maria_txt("OP1", items)
    assert "CARTPAYORI=310" in txt   # origen China
    assert "CARTPAYPRC=225" in txt   # procedencia Uruguay oficial


def test_txt_unidad_default_es_unidad():
    """Sin unidad explícita, CARTUNTDCL debe ser 07 (UNIDAD)."""
    items = [{"pieza": "84713010", "descripcion": "X", "cantidad": 5,
              "valor_unitario": 100, "origen": "China"}]
    txt = generate_maria_txt("OP1", items)
    assert "CARTUNTDCL=07" in txt
    assert "CARTUNTEST=07" in txt


def test_txt_unidad_kg_y_par():
    """La unidad del item se mapea al código oficial: kg=01, par=08."""
    items = [{"pieza": "84713010", "descripcion": "A", "cantidad": 10,
              "valor_unitario": 100, "origen": "China", "unidad": "kg"}]
    txt = generate_maria_txt("OP1", items)
    assert "CARTUNTDCL=01" in txt   # kilogramo oficial
    assert "CARTUNTDCL=07" not in txt

    items2 = [{"pieza": "64041100", "descripcion": "Zapatillas", "cantidad": 20,
               "valor_unitario": 50, "origen": "China", "unidad_medida": "pares"}]
    txt2 = generate_maria_txt("OP2", items2)
    assert "CARTUNTDCL=08" in txt2   # par oficial


# ---------- validate_items_for_maria ----------


def test_validate_items_ok():
    valido, errores = validate_items_for_maria(ITEMS_OK)
    assert valido is True
    assert errores == []


def test_validate_items_sin_ncm():
    items = [{"pieza": "", "descripcion": "X", "cantidad": 1, "valor_unitario": 10}]
    valido, errores = validate_items_for_maria(items)
    assert valido is False
    assert any("ncm" in e.lower() or "pieza" in e.lower() for e in errores)


def test_validate_items_cantidad_cero():
    items = [{"pieza": "84713010", "descripcion": "X", "cantidad": 0, "valor_unitario": 10}]
    valido, errores = validate_items_for_maria(items)
    assert valido is False
    assert any("cantidad" in e.lower() for e in errores)


def test_validate_items_valor_cero():
    items = [{"pieza": "84713010", "descripcion": "X", "cantidad": 1, "valor_unitario": 0}]
    valido, errores = validate_items_for_maria(items)
    assert valido is False
    assert any("valor" in e.lower() for e in errores)


# ====================================================================
# 2. E2E TESTS — endpoint /generate_maria (auth + validación)
# ====================================================================


@pytest.fixture(scope="module", autouse=True)
def _init_db_once():
    """Dispara el lifespan una vez para crear tablas (conftest global usa
    archivo SQLite temporal compartido)."""
    with TestClient(app) as _:
        pass
    yield


@pytest.fixture
def client():
    from proyecto_maria.core.rate_limit import limiter
    limiter.enabled = False
    return TestClient(app)


def _register(client, username, cuit=None):
    payload = {
        "username": username,
        "password": "originalpass123",
        "email": f"{username}@test.cdi",
        "name": f"User {username}",
    }
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code in (200, 201), resp.text
    if cuit:
        # Guardar CUIT en perfil para testear el fallback cuit_agr.
        r = client.put("/api/user/profile", json={"cuit": cuit})
        assert r.status_code == 200, r.text


def test_generate_maria_happy_path(client):
    """Items válidos + auth → 200 + filename + content con secciones MARIA."""
    _register(client, "maria1")
    resp = client.post("/generate_maria", json={
        "operation_id": "OP777",
        "items": ITEMS_OK,
        "moneda": "DOL",
        "incoterm": "FOB",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert data["filename"].endswith(".TXT")
    assert "[DDT]" in data["content"]
    assert "[ART]" in data["content"]


def test_generate_maria_requires_auth(client):
    """Sin cookie → 401 (no se genera TXT para anónimos)."""
    client.cookies.clear()
    resp = client.post("/generate_maria", json={
        "operation_id": "OP1",
        "items": ITEMS_OK,
    })
    assert resp.status_code == 401


def test_generate_maria_items_invalidos_devuelve_400(client):
    """Items sin NCM → 400 con errores de validación."""
    _register(client, "maria2")
    resp = client.post("/generate_maria", json={
        "operation_id": "OP2",
        "items": [{"pieza": "", "descripcion": "X", "cantidad": 1, "valor_unitario": 10}],
    })
    assert resp.status_code == 400


def test_generate_maria_usa_cuit_del_perfil(client):
    """Si la request no manda cuit_agr pero el user lo tiene en perfil, se usa."""
    _register(client, "maria3", cuit="20111222333")
    resp = client.post("/generate_maria", json={
        "operation_id": "OP3",
        "items": ITEMS_OK,
        # sin cuit_agr a propósito
    })
    assert resp.status_code == 200, resp.text
    assert "CDDTAGR=20111222333" in resp.json()["content"]
