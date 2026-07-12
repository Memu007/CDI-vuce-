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
    {"pieza": "84713010", "descripcion": "Laptop Pro X1", "cantidad": 10,
     "valor_unitario": 500, "peso_unitario": 2.5, "origen": "CN"},
    {"pieza": "85171200", "descripcion": "Celular Samsung", "cantidad": 20,
     "valor_unitario": 300, "peso_unitario": 0.2, "origen": "US"},
]

_SBT_TEST = "AA(DEMO)-AB(DEMO)-CA00-"


def _gen(*args, **kwargs):
    """Wrapper que inyecta sbt_sufijo_valor por defecto en todos los tests."""
    kwargs.setdefault("sbt_sufijo_valor", _SBT_TEST)
    return generate_maria_txt(*args, **kwargs)


def test_txt_tiene_secciones_obligatorias():
    """El TXT debe contener las secciones que el Kit SIM espera."""
    txt = _gen("OP123456", ITEMS_OK)
    for seccion in ("[DDT]", "[CPL]", "[DVD]", "[ART]", "[SBT]"):
        assert seccion in txt, f"Falta la sección {seccion}"


def test_txt_usa_crlf():
    """MARIA/Windows espera saltos de línea CRLF, no solo LF."""
    txt = _gen("OP123456", ITEMS_OK)
    assert "\r\n" in txt, "El TXT debe usar CRLF"


def test_txt_un_art_por_item():
    """Debe haber exactamente un bloque [ART] por item."""
    txt = _gen("OP123456", ITEMS_OK)
    assert txt.count("[ART]") == len(ITEMS_OK)


def test_txt_total_fob_correcto():
    """MDDTFOB debe ser la suma de cantidad*valor_unitario de todos los items."""
    txt = _gen("OP123456", ITEMS_OK)
    # 10*500 + 20*300 = 5000 + 6000 = 11000
    assert "MDDTFOB=11000.00" in txt


def test_txt_usa_valor_total_si_viene():
    """Si el item trae valor_total explícito, se usa ese en vez de calcular."""
    items = [{"pieza": "84713010", "descripcion": "X", "cantidad": 3,
              "valor_unitario": 100, "valor_total": 999, "origen": "CN"}]
    txt = _gen("OP1", items)
    assert "MDDTFOB=999.00" in txt


def test_txt_formatea_ncm_con_puntos():
    """NCM de 8+ dígitos se formatea con puntos para el Kit SIM."""
    items = [{"pieza": "84798999900H", "descripcion": "X", "cantidad": 1,
              "valor_unitario": 10, "origen": "CN"}]
    txt = _gen("OP1", items)
    # 8479.89.99 + sufijo
    assert "IESPNCE=8479.89.99" in txt


def test_txt_incluye_cuit_agr():
    """El CUIT del despachante debe aparecer como CDDTAGR en la cabecera."""
    txt = _gen("OP1", ITEMS_OK, cuit_agr="20304050607")
    assert "CDDTAGR=20304050607" in txt


def test_txt_sin_cuit_agr_no_emite_linea():
    """Si no hay CUIT del despachante, no se emite la línea CDDTAGR."""
    txt = _gen("OP1", ITEMS_OK, cuit_agr="")
    assert "CDDTAGR=" not in txt


def test_txt_defaults_aduana_destinacion():
    """Sin config, usa defaults seguros (001 / IC04)."""
    txt = _gen("OP1", ITEMS_OK)
    assert "CDDTBUR=001" in txt
    assert "CDDTTYPDEC=IC04" in txt


def test_txt_respeta_aduana_destinacion_custom():
    """Config custom de aduana/destinación se respeta."""
    txt = _gen("OP1", ITEMS_OK, aduana_codigo="073", tipo_destinacion="IC05")
    assert "CDDTBUR=073" in txt
    assert "CDDTTYPDEC=IC05" in txt


def test_txt_incoterm_y_moneda():
    """Incoterm y moneda se reflejan en la cabecera."""
    txt = _gen("OP1", ITEMS_OK, moneda="DOL", incoterm="CIF")
    assert "CDDTINCOTE=CIF" in txt
    assert "CDDTDEVFOB=DOL" in txt


def test_txt_proporcional_flete_seguro():
    """Flete y seguro se reparten proporcional al FOB de cada item."""
    # 1 item con todo el FOB → recibe el 100% del flete.
    items = [{"pieza": "84713010", "descripcion": "X", "cantidad": 1,
              "valor_unitario": 1000, "origen": "CN"}]
    txt = _gen("OP1", items, flete=100, seguro=50)
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
    txt = _gen("OP1", ITEMS_OK)
    assert "DR. SALVADOR MAZZA 1996" not in txt
    assert "13/07/2016" not in txt
    # Sin dato, el bloque [CPL] correspondiente directamente no se emite.
    assert "CCPL=DOMICIL.ESTABLEC" not in txt
    assert "CCPL=FECHA INIC.ACTIV" not in txt


def test_txt_usa_datos_reales_del_cliente():
    """Cuando vienen domicilio y fecha del cliente, se emiten esos valores."""
    txt = _gen(
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
    txt = _gen("OP1", items)
    assert "CARTPAYORI=310" in txt   # China oficial
    assert "CARTPAYPRC=310" in txt   # procedencia = origen
    assert "CARTPAYPRC=222" not in txt


def test_txt_procedencia_explicita():
    """Si el item trae procedencia distinta al origen, se respeta."""
    items = [{"pieza": "84713010", "descripcion": "X", "cantidad": 1,
              "valor_unitario": 100, "origen": "China",
              "pais_procedencia": "Uruguay"}]
    txt = _gen("OP1", items)
    assert "CARTPAYORI=310" in txt   # origen China
    assert "CARTPAYPRC=225" in txt   # procedencia Uruguay oficial


def test_txt_unidad_default_es_unidad():
    """Sin unidad explícita, CARTUNTDCL debe ser 07 (UNIDAD)."""
    items = [{"pieza": "84713010", "descripcion": "X", "cantidad": 5,
              "valor_unitario": 100, "origen": "China"}]
    txt = _gen("OP1", items)
    assert "CARTUNTDCL=07" in txt
    assert "CARTUNTEST=07" in txt


def test_txt_unidad_kg_y_par():
    """La unidad del item se mapea al código oficial: kg=01, par=08."""
    items = [{"pieza": "84713010", "descripcion": "A", "cantidad": 10,
              "valor_unitario": 100, "origen": "China", "unidad": "kg"}]
    txt = _gen("OP1", items)
    assert "CARTUNTDCL=01" in txt   # kilogramo oficial
    assert "CARTUNTDCL=07" not in txt

    items2 = [{"pieza": "64041100", "descripcion": "Zapatillas", "cantidad": 20,
               "valor_unitario": 50, "origen": "China", "unidad_medida": "pares"}]
    txt2 = _gen("OP2", items2)
    assert "CARTUNTDCL=08" in txt2   # par oficial


def test_txt_fecha_embarque_no_se_inventa():
    """Sin fecha de embarque, NO debe emitirse DDDTVENEMB (antes inventaba hoy+365)."""
    txt = _gen("OP1", ITEMS_OK)
    assert "DDDTVENEMB" not in txt


def test_txt_fecha_embarque_real_se_usa():
    """Con fecha de embarque real, se emite tal cual."""
    txt = _gen("OP1", ITEMS_OK, fecha_embarque="15/08/2026")
    assert "DDDTVENEMB=15/08/2026" in txt


# ---------- Golden regression (op real del despachante, anonimizada) ----------

# Inputs que reproducen la operación real 001790125 (importador VOWYNNS) con
# TODOS los datos identificatorios anonimizados. NCM/pesos/montos quedan reales
# para validar los cálculos. Ver tests/fixtures/maria_golden_anon.TXT.
GOLDEN_INPUTS = dict(
    operation_id="000999001",
    items=[{
        "pieza": "84798999900H", "descripcion": "MAQUINA DEMO",
        "cantidad": 1, "valor_unitario": 5000, "valor_total": 5000,
        "peso_kg": 1220, "origen": "AR", "pais_procedencia": "PE",
    }],
    moneda="DOL", incoterm="DDP",
    cuit_agr="20111111112",
    vendedor_nombre="(00999) PROVEEDOR DEMO S.A.",
    vendedor_id="20999999991",
    comprador_nombre="IMPORTADORA DEMO S.A",
    comprador_cuit="30999999990",
    comprador_domicilio="CALLE FALSA 123",
    comprador_fecha_inic_activ="01/01/2010",
    flete=3221.66, seguro=50,
    fecha_embarque="02/01/2026", fecha_emision="18/07/2025",
    sbt_sufijo_valor="AA(DEMO)-AB(DEMO)-CA00-",
    aduana_codigo="001", tipo_destinacion="IC04",
)

_GOLDEN_PATH = os.path.join(os.path.dirname(__file__), "fixtures",
                            "maria_golden_anon.TXT")


def test_golden_reproduce_estructura_real():
    """El generador debe reproducir el TXT validado por el despachante (anonimizado).

    Snapshot de regresión: si cambia el output del generador, este test avisa.
    Ya verificamos manualmente que esta estructura coincide con el TXT real
    (op 001790125) que el Kit SIM aceptó.
    """
    with open(_GOLDEN_PATH, "r", newline="") as f:
        esperado = f.read()
    generado = generate_maria_txt(**GOLDEN_INPUTS)
    assert generado == esperado


def test_golden_calculos_clave():
    """Valida los cálculos contra los números reales conocidos de la operación."""
    txt = _gen(**GOLDEN_INPUTS)
    assert "MARTBASIMP=8271.66" in txt          # FOB 5000 + flete 3221.66 + seg 50
    assert "MCPL=3271.66" in txt                # GTOS-POS-FOB = flete + seguro
    assert "IESPNCE=8479.89.99.900H" in txt     # NCM con sufijo SIM preservado
    assert "CARTPAYORI=200" in txt              # Argentina
    assert "CARTPAYPRC=222" in txt              # procedencia distinta del origen


def test_golden_no_filtra_datos_reales():
    """El fixture NO debe contener datos del cliente real (VOWYNNS)."""
    with open(_GOLDEN_PATH, "r", newline="") as f:
        contenido = f.read().upper()
    for prohibido in ("VOWYNNS", "VITTO", "ARDEN", "SALVADOR MAZZA",
                       "30715958844", "20324717073", "20613363263"):
        assert prohibido.upper() not in contenido


# ---------- Hotfix SBT: sin sufijo de valor, no se genera ----------


def test_sbt_sin_sufijo_bloquea_generacion():
    """Sin sbt_sufijo_valor, generate_maria_txt lanza ValueError con mensaje claro."""
    with pytest.raises(ValueError, match="sufijo de valor SBT"):
        generate_maria_txt("OP1", ITEMS_OK)


def test_sbt_sin_sufijo_endpoint_devuelve_400(client):
    """Sin sbt_sufijo_valor en el endpoint → 400 controlado (no 500)."""
    _register(client, "maria_sbt")
    resp = client.post("/generate_maria", json={
        "operation_id": "OP_SBT",
        "items": ITEMS_OK,
    })
    assert resp.status_code == 400, resp.text
    detail = resp.json().get("detail", "")
    assert "sufijo de valor SBT" in detail


def test_sbt_con_sufijo_explicito_genera():
    """Con sbt_sufijo_valor explícito, el TXT se genera normalmente."""
    txt = generate_maria_txt("OP1", ITEMS_OK, sbt_sufijo_valor="AA(MICLIENTE)-AB(OTRO)-CA00-")
    assert "CSBTSVL=AA(MICLIENTE)-AB(OTRO)-CA00-" in txt


def test_sbt_no_contiene_vowynns_ni_vitto():
    """Ningún TXT generado con sufijo explícito contiene VOWYNNS ni VITTO."""
    txt = generate_maria_txt("OP1", ITEMS_OK, sbt_sufijo_valor="AA(CLIENTE1)-AB(CLIENTE2)-CA00-")
    assert "VOWYNNS" not in txt
    assert "VITTO" not in txt


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
    """Items válidos + auth + SBT explícito → 200 + filename + content con secciones MARIA."""
    _register(client, "maria1")
    resp = client.post("/generate_maria", json={
        "operation_id": "OP777",
        "items": ITEMS_OK,
        "moneda": "DOL",
        "incoterm": "FOB",
        "sbt_sufijo_valor": "AA(DEMO)-AB(DEMO)-CA00-",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert data["filename"].endswith(".TXT")
    assert "[DDT]" in data["content"]
    assert "[ART]" in data["content"]
    assert "CSBTSVL=AA(DEMO)-AB(DEMO)-CA00-" in data["content"]


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
    """Con SBT explícito + CUIT en perfil → 200 y el TXT usa el CUIT del perfil."""
    _register(client, "maria3", cuit="20111222333")
    resp = client.post("/generate_maria", json={
        "operation_id": "OP3",
        "items": ITEMS_OK,
        "sbt_sufijo_valor": "AA(DEMO)-AB(DEMO)-CA00-",
        # sin cuit_agr a propósito
    })
    assert resp.status_code == 200, resp.text
    assert "CDDTAGR=20111222333" in resp.json()["content"]


def test_get_pais_codigo_vietnam_thailand_indonesia_malaysia():
    assert get_pais_codigo("VN") == 337
    assert get_pais_codigo("Vietnam") == 337
    assert get_pais_codigo("vietnam") == 337
    assert get_pais_codigo("TH") == 335
    assert get_pais_codigo("Thailand") == 335
    assert get_pais_codigo("Tailandia") == 335
    assert get_pais_codigo("ID") == 316
    assert get_pais_codigo("Indonesia") == 316
    assert get_pais_codigo("MY") == 326
    assert get_pais_codigo("Malaysia") == 326
    assert get_pais_codigo("Malasia") == 326


def test_pais_reconocido_cases():
    from proyecto_maria.core.maria_generator import pais_reconocido
    assert pais_reconocido("XX") is False
    assert pais_reconocido("Vietnam") is True
    assert pais_reconocido("VN") is True
    assert pais_reconocido("cn") is True
    assert pais_reconocido("Brazil") is True
    assert pais_reconocido("UnknownCountry") is False
    assert pais_reconocido("") is False
    assert pais_reconocido(None) is False


def test_validate_items_for_maria_unrecognized_origin():
    # Origen no reconocido
    items_bad = [
        {"pieza": "84713010", "descripcion": "Laptop", "cantidad": 10,
         "valor_unitario": 500, "peso_unitario": 2.5, "origen": "XX"}
    ]
    valido, errores = validate_items_for_maria(items_bad)
    assert valido is False
    assert any("origen no reconocido" in e.lower() for e in errores)


def test_generate_maria_unrecognized_origin_returns_400(client):
    _register(client, "maria4")
    resp = client.post("/generate_maria", json={
        "operation_id": "OP_BAD_ORIGIN",
        "items": [
            {"pieza": "84713010", "descripcion": "Laptop", "cantidad": 10,
             "valor_unitario": 500, "peso_unitario": 2.5, "origen": "XX"}
        ],
        "moneda": "DOL",
        "incoterm": "FOB",
    })
    assert resp.status_code == 400
    assert any("origen no reconocido" in e.lower() for e in resp.json()["detail"]["errors"])


def test_generate_maria_export_unrecognized_destination_returns_400(client):
    _register(client, "maria5")
    resp = client.post("/generate_maria_export", json={
        "operation_id": "EXP_BAD_DEST",
        "items": [
            {"pieza": "84713010", "descripcion": "Laptop", "cantidad": 10,
             "valor_unitario": 500, "peso_kg": 2.5}
        ],
        "moneda": "DOL",
        "incoterm": "FOB",
        "comprador_pais": "XX",
        "comprador_nombre": "Test Buyer",
    })
    assert resp.status_code == 400
    assert any("país de destino no reconocido" in e.lower() for e in resp.json()["detail"]["errors"])


def test_validations_smart_country_warning():
    from proyecto_maria.core.validations import run_smart_validations
    from proyecto_maria.models.operations import Item
    
    # Item con origen XX
    item_xx = Item(
        pieza="84713010", descripcion="Laptop Super Pro", cantidad=10,
        valor_unitario=500.0, peso_unitario=2.5, origen="XX"
    )
    res = run_smart_validations([item_xx])
    assert any("Origen 'XX' debe reemplazarse por país real" in w for w in res["advertencias"])

    # Item con origen no reconocido
    item_bad = Item(
        pieza="84713010", descripcion="Laptop Super Pro", cantidad=10,
        valor_unitario=500.0, peso_unitario=2.5, origen="InvalidCountry"
    )
    res_bad = run_smart_validations([item_bad])
    assert any("no reconocido por el sistema MARIA" in w for w in res_bad["advertencias"])


# ====================================================================
# AGRUPACIÓN — unidades clasificatorias (grupo_id)
# ====================================================================

def test_agrupacion_2_items_mismo_grupo_genera_2_art():
    """3 items donde 2 tienen mismo grupo_id → 2 [ART] (no 3).

    Items:
    - Silla (grupo 1): cant=2, valor=50, peso=3
    - Mesa (grupo 1): cant=2, valor=20, peso=1
    - Lámpara (sin grupo): cant=5, valor=10, peso=0.5

    Grupo 1 combinado: cant=4, valor_total=140, peso=4
    """
    items = [
        {"pieza": "94037000", "descripcion": "Silla de madera de roble", "cantidad": 2,
         "valor_unitario": 50, "peso_unitario": 3, "origen": "CN", "grupo_id": 1},
        {"pieza": "94037000", "descripcion": "Mesa de madera de roble", "cantidad": 2,
         "valor_unitario": 20, "peso_unitario": 1, "origen": "CN", "grupo_id": 1},
        {"pieza": "94051000", "descripcion": "Lámpara de mesa LED", "cantidad": 5,
         "valor_unitario": 10, "peso_unitario": 0.5, "origen": "CN"},
    ]
    txt = _gen("OP_AGRUP", items)

    # 2 [ART]: grupo combinado + lámpara sola
    assert txt.count("[ART]") == 2, f"Esperaba 2 [ART], got {txt.count('[ART]')}"

    # Grupo combinado: MARTFOB = 2*50 + 2*20 = 140
    assert "MARTFOB=140.00" in txt, f"Falta MARTFOB=140.00 en txt"

    # Grupo combinado: QARTKGRNET = 3+1 = 4 (peso sumado)
    assert "QARTKGRNET=4.000" in txt, f"Falta QARTKGRNET=4.000 en txt"

    # Grupo combinado: QARTUNTDCL = 2+2 = 4 (cantidad sumada)
    assert "QARTUNTDCL=4.00" in txt, f"Falta QARTUNTDCL=4.00 en txt"

    # Lámpara sola: MARTFOB = 5*10 = 50
    assert "MARTFOB=50.00" in txt, f"Falta MARTFOB=50.00 de lámpara sola"


# ---------- Hotfix SBT: validación de caracteres de control ----------


def test_sbt_con_salto_de_linea_devuelve_400(client):
    """SBT con \\n → 400 (inyección de líneas prohibida)."""
    _register(client, "maria_sbt_nl")
    resp = client.post("/generate_maria", json={
        "operation_id": "OP_NL",
        "items": ITEMS_OK,
        "sbt_sufijo_valor": "AA(OK)-AB(OK)\nCA00-",
    })
    assert resp.status_code == 400, resp.text
    detail = resp.json().get("detail", "")
    assert "salto" in detail.lower() or "control" in detail.lower()


def test_sbt_con_carriage_return_devuelve_400(client):
    """SBT con \\r → 400."""
    _register(client, "maria_sbt_cr")
    resp = client.post("/generate_maria", json={
        "operation_id": "OP_CR",
        "items": ITEMS_OK,
        "sbt_sufijo_valor": "AA(OK)\r-AB(OK)-CA00-",
    })
    assert resp.status_code == 400, resp.text


def test_sbt_excede_120_chars_devuelve_400(client):
    """SBT con más de 120 caracteres → 400."""
    _register(client, "maria_sbt_long")
    resp = client.post("/generate_maria", json={
        "operation_id": "OP_LONG",
        "items": ITEMS_OK,
        "sbt_sufijo_valor": "A" * 121,
    })
    assert resp.status_code == 400, resp.text
    detail = resp.json().get("detail", "")
    assert "120" in detail


def test_sbt_endpoint_genera_seccion_sbt(client):
    """Con SBT válido, el endpoint genera 200 y el TXT contiene [SBT]."""
    _register(client, "maria_sbt_ok")
    resp = client.post("/generate_maria", json={
        "operation_id": "OP_SBT_OK",
        "items": ITEMS_OK,
        "sbt_sufijo_valor": "AA(CLIENTE)-AB(OTRO)-CA00-",
    })
    assert resp.status_code == 200, resp.text
    content = resp.json()["content"]
    assert "[SBT]" in content
    assert "CSBTSVL=AA(CLIENTE)-AB(OTRO)-CA00-" in content


def test_sbt_trim_aplicado(client):
    """El backend aplica trim al SBT: espacios al final no rompen."""
    _register(client, "maria_sbt_trim")
    resp = client.post("/generate_maria", json={
        "operation_id": "OP_TRIM",
        "items": ITEMS_OK,
        "sbt_sufijo_valor": "  AA(TRIM)-AB(TRIM)-CA00-  ",
    })
    assert resp.status_code == 200, resp.text
    content = resp.json()["content"]
    assert "CSBTSVL=AA(TRIM)-AB(TRIM)-CA00-" in content


def test_sbt_request_frontend_contiene_campo():
    """El contrato del endpoint incluye sbt_sufijo_valor en MariaRequest."""
    from proyecto_maria.main import MariaRequest
    req = MariaRequest(
        operation_id="OP_FRONTEND",
        items=ITEMS_OK,
        sbt_sufijo_valor="AA(FRONT)-AB(FRONT)-CA00-",
    )
    assert req.sbt_sufijo_valor == "AA(FRONT)-AB(FRONT)-CA00-"


def test_sbt_flujo_completo_desde_dashboard(client):
    """Flujo completo: registrar, validar, generar con SBT → 200 + [SBT] en TXT."""
    _register(client, "maria_e2e_sbt")
    # Paso 1: validar items
    val = client.post("/api/validate/smart", json={"items": ITEMS_OK})
    assert val.status_code == 200
    # Paso 2: generar con SBT
    resp = client.post("/generate_maria", json={
        "operation_id": "OP_E2E_SBT",
        "items": ITEMS_OK,
        "sbt_sufijo_valor": "AA(E2E)-AB(E2E)-CA00-",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert "[SBT]" in data["content"]
    assert "CSBTSVL=AA(E2E)-AB(E2E)-CA00-" in data["content"]
    assert data["filename"].endswith(".TXT")
