"""MARIA-7: lo que el MARIA rechazó el 2026-10-24.

Emi y el despachante cargaron en el MARIA un TXT de CDI de una factura real
(renglones de lonas de PVC, una posición SIM, origen China, CFR) y entró
después de doce correcciones a mano. Los datos reales no entran al
repositorio: este sintético tiene la misma forma con valores inventados.

Un caso por punto de la tarea (PARA-DEV-2.md, Tarea 1).
"""
import inspect
import re
from decimal import Decimal

import pytest

# Por el módulo y no por nombre: contra la base, cada caso falla por su
# cuenta (rojo antes) y no el archivo entero al importar.
from proyecto_maria.core import maria_generator as mg

CUIT_DESPACHANTE = "20111111112"
SUFIJO = "AA(MARCA)-AI(620G-GREY.008 150CMX50M)-"

# La forma de la factura del 24/10, inventada: lonas por metro cuadrado,
# posición 3921.90.19.900Z, China, CFR.
LONA = {
    "pieza": "39219019900Z", "descripcion": "Lona de PVC gris 620 g",
    "cantidad": 750, "valor_unitario": 1.85, "peso_kg": 465.125,
    "origen": "CN", "unidad": "m²",
}
COMUN = dict(
    # Como lo arma la pantalla: «FAC_» + el número de factura sin signos.
    operation_id="FAC_INV-20260457",
    numero_factura="INV-2026/0457",
    moneda="DOL", incoterm="CFR", cuit_agr=CUIT_DESPACHANTE,
    vendedor_nombre="PROVEEDOR LONAS DEMO", vendedor_id="91330000MA2DEMO01X",
    comprador_nombre="IMPORTADORA DEMO S.A.", comprador_cuit="30999999990",
    flete=7925.00, seguro=12.40, fecha_emision="10/10/2026",
    sbt_sufijo_valor=SUFIJO,
)


def _gen(items=None, **kw):
    # Sólo los parámetros que el generador conoce: contra la base (sin
    # `numero_factura`) cada caso falla por su defecto y no por un TypeError.
    conocidos = inspect.signature(mg.generate_maria_txt).parameters
    pedido = {k: v for k, v in {**COMUN, **kw}.items() if k in conocidos}
    return mg.generate_maria_txt(items=items or [dict(LONA)], **pedido)


def _valor(txt: str, campo: str) -> list:
    return re.findall(rf"^{campo}=(.*?)\r?$", txt, re.M)


# ---------------------------------------------------------------- 1. CRLF


def test_todas_las_lineas_terminan_en_crlf_tambien_la_ultima():
    txt = _gen()
    assert txt.endswith("\r\n")
    partes = txt.split("\r\n")
    assert partes[-1] == ""
    assert not any("\r" in p or "\n" in p for p in partes)


def test_el_fob_reescrito_al_final_tambien_lleva_crlf():
    """MDDTFOB se escribe cuando ya se conocen los ítems."""
    txt = _gen()
    assert re.search(r"^MDDTFOB=1387\.50\r\n", txt, re.M)


def test_un_salto_de_linea_dentro_de_un_valor_no_genera():
    """Llamado directo, sin la limpieza del endpoint: una línea partida no
    sale (antes salía «LDDTNOMFOD=A» y una línea «B» sin «=»)."""
    with pytest.raises(ValueError, match="salto de línea"):
        _gen(vendedor_nombre="PROVEEDOR\nPARTIDO")


def test_el_archivo_descargado_lleva_los_crlf(client):
    _registrar_con_cuit(client, "maria7_crlf")
    r = client.post("/generate_maria", json=_pedido())
    assert r.status_code == 200, r.text
    bajada = client.get(r.json()["download_url"])
    assert bajada.status_code == 200
    assert bajada.content == r.json()["content"].encode("utf-8")
    assert b"\r\n" in bajada.content and b"\n" not in bajada.content.replace(b"\r\n", b"")


# ------------------------------------------------------ 2. Identificador corto


def test_idso_iddt_e_iartespapu_van_cortos():
    txt = _gen()
    assert _valor(txt, "IDSO") == ["20260457"]
    assert set(_valor(txt, "IDDT")) == {"20260457"}
    assert _valor(txt, "IARTESPAPU") == ["202604570001"]


def test_el_numero_completo_sigue_en_la_referencia_interna():
    txt = _gen()
    assert re.search(r"CCPL=NRO\.REF\.INTERNA \r\nMCPL=FAC_INV-20260457 +\r\n", txt)


@pytest.mark.parametrize("entrada,corto", [
    ("FAC_INV-20260457", "20260457"),
    ("FAC_110", "FAC110"),
    ("OP_20261024153012", "24153012"),
    ("000999001", "00999001"),
])
def test_id_corto_son_los_ultimos_ocho_letras_o_numeros(entrada, corto):
    assert mg.id_corto_maria(entrada) == corto


def test_un_identificador_sin_letras_ni_numeros_no_genera():
    with pytest.raises(ValueError, match="no tiene letras ni números"):
        _gen(operation_id="___")


# ------------------------------------------------ 3. CDDTAGR obligatorio


def test_sin_cuit_del_despachante_no_se_genera():
    with pytest.raises(ValueError, match="Falta el CUIT del despachante.*Mi perfil"):
        _gen(cuit_agr="")


def test_con_cuit_del_despachante_sale_cddtagr():
    assert _valor(_gen(), "CDDTAGR") == [CUIT_DESPACHANTE]


def test_endpoint_sin_cuit_ni_perfil_da_400_que_dice_donde_cargarlo(client):
    _registrar(client, "maria7_sin_cuit")
    r = client.post("/generate_maria", json=_pedido(cuit_agr=""))
    assert r.status_code == 400, r.text
    assert "Mi perfil" in r.text and "CDDTAGR" in r.text


def test_endpoint_toma_el_cuit_del_perfil(client):
    _registrar_con_cuit(client, "maria7_perfil")
    r = client.post("/generate_maria", json=_pedido(cuit_agr=""))
    assert r.status_code == 200, r.text
    assert _valor(r.json()["content"], "CDDTAGR") == [CUIT_DESPACHANTE]


def test_los_avisos_de_antes_de_generar_piden_el_cuit(client):
    _registrar(client, "maria7_avisos_cuit")
    r = client.post("/generate_maria/avisos", json=_pedido(cuit_agr=""))
    assert r.status_code == 200, r.text
    assert any("CUIT del despachante" in a for a in r.json()["avisos"])


# ------------------------------------------------------ 4. LDVDREFDOC


def test_la_referencia_de_la_factura_es_el_numero_real_con_ancho_fijo():
    assert _valor(_gen(), "LDVDREFDOC") == [f"{'INV-2026/0457':<28}"]


def test_sin_numero_de_factura_la_referencia_va_vacia_y_se_avisa():
    """No se inventa (antes salía «E» + el final del identificador)."""
    assert _valor(_gen(numero_factura=""), "LDVDREFDOC") == [" " * 28]
    avisos = mg.supuestos_declarados([dict(LONA)], numero_factura="")
    assert any("Número de factura" in a for a in avisos)


def test_un_numero_de_factura_mas_largo_que_el_campo_no_se_corta():
    with pytest.raises(ValueError, match="en el TXT entran 28"):
        _gen(numero_factura="X" * 29)


def test_el_endpoint_pasa_el_numero_de_factura(client):
    _registrar_con_cuit(client, "maria7_ref")
    r = client.post("/generate_maria", json=_pedido())
    assert r.status_code == 200, r.text
    assert _valor(r.json()["content"], "LDVDREFDOC") == [f"{'INV-2026/0457':<28}"]


# --------------------------------------------------------- 5. Unidades


def test_metro_cuadrado_se_declara_03():
    txt = _gen()
    assert _valor(txt, "CARTUNTDCL") == ["03"]
    assert _valor(txt, "QARTUNTDCL") == ["750.00"]


@pytest.mark.parametrize("escrita", ["m2", "M2", "m²", "SQM", "metros cuadrados", "03"])
def test_metro_cuadrado_escrito_de_varias_formas(escrita):
    assert _valor(_gen([dict(LONA, unidad=escrita)]), "CARTUNTDCL") == ["03"]


def test_sin_elegir_la_estadistica_es_la_declarada_como_antes():
    txt = _gen()
    assert _valor(txt, "CARTUNTEST") == ["03"]
    assert _valor(txt, "QARTUNTEST") == ["750.00"]


def test_estadistica_en_kilos_da_el_kilo_neto_al_centesimo():
    """Error 2122 del MARIA: en kilos, QARTUNTEST = QARTKGRNET."""
    txt = _gen([dict(LONA, unidad_estadistica="01")])
    assert _valor(txt, "QARTKGRNET") == ["465.125"]
    assert _valor(txt, "CARTUNTEST") == ["01"]
    assert _valor(txt, "QARTUNTEST") == ["465.13"]
    assert _valor(txt, "CARTUNTDCL") == ["03"]


@pytest.mark.parametrize("peso,esperado", [(2.675, "2.68"), (10.004, "10.00"), (0.005, "0.01")])
def test_los_kilos_se_redondean_igual_que_el_kilo_neto(peso, esperado):
    txt = _gen([dict(LONA, peso_kg=peso, unidad_estadistica="kg")])
    neto = Decimal(_valor(txt, "QARTKGRNET")[0])
    assert _valor(txt, "QARTUNTEST") == [esperado]
    assert abs(Decimal(esperado) - neto) <= Decimal("0.005")


@pytest.mark.parametrize("estadistica", ["02", "99", "rollos"])
def test_otra_unidad_estadistica_no_se_inventa(estadistica):
    with pytest.raises(ValueError, match="unidad estadística"):
        _gen([dict(LONA, unidad_estadistica=estadistica)])


def test_estadistica_en_kilos_con_subitems_pide_los_kilos_de_cada_uno():
    item = dict(LONA, unidad_estadistica="01", subitems=[
        {"cantidad": 500, "valor_unitario": 1.85, "sufijo": SUFIJO},
        {"cantidad": 250, "valor_unitario": 1.85, "sufijo": SUFIJO},
    ])
    with pytest.raises(ValueError, match="kilos de cada sub-ítem"):
        _gen([item])


def test_un_grupo_con_estadisticas_distintas_no_se_une():
    a = dict(LONA, grupo_id=1, unidad_estadistica="01")
    b = dict(LONA, grupo_id=1)
    with pytest.raises(ValueError, match="misma unidad estadística"):
        _gen([a, b])


def test_la_pantalla_manda_la_unidad_y_la_estadistica(client):
    _registrar_con_cuit(client, "maria7_unidades")
    r = client.post("/generate_maria", json=_pedido(unidad="03", unidad_estadistica="01"))
    assert r.status_code == 200, r.text
    txt = r.json()["content"]
    assert _valor(txt, "CARTUNTDCL") == ["03"]
    assert _valor(txt, "CARTUNTEST") == ["01"]
    assert _valor(txt, "QARTUNTEST") == ["465.13"]


# --------------------------------------------------------- 6. Caracteres


def test_dentro_del_sufijo_solo_letras_numeros_y_espacios():
    txt = _gen()
    assert _valor(txt, "CSBTSVL") == ["AA(MARCA)-AI(620G GREY 008 150CMX50M)-"]


@pytest.mark.parametrize("entrada,limpio", [
    ("AA(MÁRCA Ñ)-CA00-", "AA(MARCA N)-CA00-"),
    ("AI(150CM(X)50M)-", "AI(150CM X 50M)-"),
    ("AA(A&B/C#1)-AB(OK 2)-", "AA(A B C 1)-AB(OK 2)-"),
    ("CA00-NA00-NB00-", "CA00-NA00-NB00-"),
    ("AA(SIN CIERRE-", "AA(SIN CIERRE-"),
])
def test_limpiar_sufijo(entrada, limpio):
    assert mg.limpiar_sufijo(entrada)[0] == limpio


def test_el_sufijo_de_cada_subitem_tambien_se_limpia():
    item = dict(LONA, subitems=[
        {"cantidad": 500, "valor_unitario": 1.85, "sufijo": "AA(MARCA)-AI(620G-GREY 150CM)-"},
        {"cantidad": 250, "valor_unitario": 1.85, "sufijo": "AA(MARCA)-AI(620G-GREY 300CM)-"},
    ])
    assert _valor(_gen([item]), "CSBTSVL") == [
        "AA(MARCA)-AI(620G GREY 150CM)-", "AA(MARCA)-AI(620G GREY 300CM)-"]


def test_lo_que_se_cambia_en_el_sufijo_se_avisa():
    item = dict(LONA, subitems=[{"cantidad": 750, "sufijo": "AA(X.Y)-"}])
    avisos = mg.supuestos_declarados([item], sbt_sufijo_valor=SUFIJO)
    assert any("Sufijo de valor:" in a and "AI(620G GREY 008 150CMX50M)" in a for a in avisos)
    assert any("ítem 1, sub-ítem 1" in a and "AA(X Y)-" in a for a in avisos)
    assert not any("Sufijo" in a for a in mg.supuestos_declarados([dict(LONA)], sbt_sufijo_valor="AA(OK)-"))


def test_el_aviso_del_sufijo_llega_a_la_pantalla(client):
    _registrar_con_cuit(client, "maria7_aviso_sufijo")
    r = client.post("/generate_maria/avisos", json=_pedido())
    assert r.status_code == 200, r.text
    assert any("Sufijo de valor" in a for a in r.json()["avisos"])


# ------------------------------------------------- 7. IDTRIB-PROVEEDOR


@pytest.mark.parametrize("cuenta", [
    "6222021234567890123",            # 19 dígitos, cuenta china
    "6222 0212 3456 7890",            # 16 con espacios
    "Account No: 1234567890",
    "IBAN DE89370400440532013000",
    "DE89370400440532013000",
    "A/C 0012-3456-78",
])
def test_una_cuenta_del_banco_no_va_como_idtrib(cuenta):
    txt = _gen(vendedor_id=cuenta)
    assert "IDTRIB-PROVEEDOR" not in txt
    assert mg.parece_cuenta_bancaria(cuenta)
    avisos = mg.supuestos_declarados([dict(LONA)], vendedor_id=cuenta)
    assert any("parece una cuenta del banco" in a for a in avisos)


@pytest.mark.parametrize("tributaria", [
    "91330000MA2DEMO01X",       # código chino de crédito social (18, con letras)
    "12345678000190",           # CNPJ, 14 dígitos
    "1234567890123",            # número de empresa japonés, 13
    "82-1111111",               # EIN
    "DE123456789",              # IVA alemán
    "20999999991",              # CUIT
])
def test_una_identificacion_tributaria_sigue_saliendo(tributaria):
    assert _valor(_gen(vendedor_id=tributaria), "MCPL").count(f"{tributaria:<40}") == 1
    assert not mg.parece_cuenta_bancaria(tributaria)


def test_sin_identificacion_no_se_inventa_y_se_avisa():
    assert "IDTRIB-PROVEEDOR" not in _gen(vendedor_id="")
    avisos = mg.supuestos_declarados([dict(LONA)], vendedor_id="")
    assert any("Identificación tributaria del proveedor: no se leyó" in a for a in avisos)


# ------------------------------------------------- la fecha no se toca


def test_la_fecha_de_emision_sale_como_antes():
    txt = _gen()
    assert re.search(r"CCPL=FECHAEMISIONFACT\r\nMCPL=10/10/2026 +\r\n", txt)


# ---------------------------------------------------------------- ayudas


def _registrar(client, usuario):
    r = client.post("/auth/register", json={
        "username": usuario, "password": "Clave-Segura-123", "email": f"{usuario}@cdi.test",
        "name": usuario,
    })
    assert r.status_code in (200, 201), r.text
    r = client.post("/auth/login", json={"username": usuario, "password": "Clave-Segura-123"})
    assert r.status_code == 200, r.text


def _registrar_con_cuit(client, usuario):
    _registrar(client, usuario)
    r = client.put("/api/user/profile", json={"cuit": CUIT_DESPACHANTE})
    assert r.status_code == 200, r.text


def _pedido(cuit_agr=CUIT_DESPACHANTE, unidad="m²", unidad_estadistica=None):
    """Lo que manda buildMariaRequest (finalize.js) para la lona."""
    return {
        "operation_id": COMUN["operation_id"], "numero_factura": COMUN["numero_factura"],
        "items": [{
            "pieza": LONA["pieza"], "descripcion": LONA["descripcion"], "origen": "CN",
            "cantidad": LONA["cantidad"], "valor_unitario": LONA["valor_unitario"],
            "peso_unitario": LONA["peso_kg"] / LONA["cantidad"],
            "unidad": unidad, "unidad_estadistica": unidad_estadistica,
        }],
        "moneda": "DOL", "incoterm": "CFR", "cuit_agr": cuit_agr,
        "vendedor_nombre": COMUN["vendedor_nombre"], "vendedor_id": COMUN["vendedor_id"],
        "comprador_nombre": COMUN["comprador_nombre"], "comprador_cuit": "30712345671",
        "flete": 7925.0, "seguro": 12.4, "fecha_emision": COMUN["fecha_emision"],
        "sbt_sufijo_valor": SUFIJO,
    }


def test_declarada_en_kilos_con_subitems_cierra_o_no_genera():
    """Con la declarada en kilos los QSBTUNTEST son las cantidades: si el kilo
    neto no suma lo mismo, la cantidad estadística no cerraría."""
    subs = [{"cantidad": 300, "valor_unitario": 1.85, "sufijo": SUFIJO},
            {"cantidad": 450, "valor_unitario": 1.85, "sufijo": SUFIJO}]
    igual = dict(LONA, unidad="kg", peso_kg=750, subitems=subs)
    txt = _gen([igual])
    assert _valor(txt, "QARTUNTEST") == ["750.00"]
    assert _valor(txt, "QSBTUNTEST") == ["300.00", "450.00"]
    with pytest.raises(ValueError, match="kilos de cada sub-ítem"):
        _gen([dict(igual, peso_kg=465.125)])
