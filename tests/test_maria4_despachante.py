"""MARIA-4: lo que decide el despachante sale en el TXT.

- Estado de la mercadería (CARTUSO), por producto: 1 a 6; por defecto 2 con
  origen extranjero; con origen argentino no hay por defecto.
- IVA adicional (IVAADICIONAL1): reventa (NO_VALIDA, por defecto) o uso
  particular (IVAAD1), por operación con cambio por producto.
- Banco (BANCOSARGENTINA): código BCRA de 3 dígitos; sin banco la línea no sale.
- Empresa de digitalización (ARDIG-CUIT-PSAD): PSAD06 Modoc (por defecto) o
  PSAD01 Lakaut.

Prueba: respuestas 1, 2, 4 y 5 del despachante y los dos archivos reales
(2025: estado 3, uso particular, sin banco, PSAD06; 2026: estado 2,
reventa, banco 191, PSAD01). El archivo de 2025 sale idéntico en
`test_generar_maria_txt.py::test_golden_reproduce_estructura_real`.
"""
import pytest

from proyecto_maria.core.maria_generator import generate_maria_txt
from tests.test_maria_subitems import COMUN, ITEM_BASE, REFERENCIA, SUF_A, SUF_B


def _cpl(txt: str) -> list[tuple[str, str, str]]:
    """Bloques [CPL] como (NART, CCPL, MCPL), sin el relleno de espacios."""
    salida = []
    for bloque in txt.replace("\r\n", "\n").split("[CPL]")[1:]:
        campos = {}
        for ln in bloque.split("[")[0].split("\n"):
            if "=" in ln:
                k, v = ln.split("=", 1)
                campos.setdefault(k.strip(), v.strip())
        salida.append((campos.get("NART"), campos.get("CCPL"), campos.get("MCPL")))
    return salida


def _valor(txt: str, ccpl: str, nart: str = "0000"):
    return [m for n, c, m in _cpl(txt) if c == ccpl and n == nart]


def _cartuso(txt: str) -> list[str]:
    return [ln.split("=", 1)[1].strip() for ln in txt.replace("\r\n", "\n").split("\n")
            if ln.startswith("CARTUSO=")]


def _gen(items=None, **kw):
    return generate_maria_txt(items=items or [dict(ITEM_BASE)],
                              **{**COMUN, "sbt_sufijo_valor": SUF_A, **kw})


# --- Con los valores por defecto el TXT cambia a propósito ---------------

def test_por_defecto_estado_2_reventa_modoc_y_sin_banco():
    txt = _gen()
    assert _cartuso(txt) == ["2"]                         # antes: 3 fijo
    assert _valor(txt, "IVAADICIONAL1", "0001") == ["NO_VALIDA"]  # antes: IVAAD1 fijo
    assert _valor(txt, "ARDIG-CUIT-PSAD") == ["PSAD06"]
    assert _valor(txt, "BANCOSARGENTINA") == []


# --- Cada campo, elegido ----------------------------------------------------

@pytest.mark.parametrize("estado", [1, 2, 3, 4, 5, 6, "4"])
def test_estado_elegido_por_producto(estado):
    txt = _gen([dict(ITEM_BASE, estado=estado)])
    assert _cartuso(txt) == [str(estado)]


def test_estado_distinto_en_cada_producto():
    items = [dict(ITEM_BASE, estado=2), dict(ITEM_BASE, estado=6)]
    assert _cartuso(_gen(items)) == ["2", "6"]


def test_origen_argentino_sin_estado_no_se_inventa():
    with pytest.raises(ValueError, match="origen es argentino"):
        _gen([dict(ITEM_BASE, origen="AR")])


def test_origen_argentino_con_estado_elegido():
    assert _cartuso(_gen([dict(ITEM_BASE, origen="AR", estado=3)])) == ["3"]


@pytest.mark.parametrize("estado", [0, 7, "x", "2.5"])
def test_estado_fuera_de_la_tabla_se_rechaza(estado):
    with pytest.raises(ValueError, match="estado de la mercadería"):
        _gen([dict(ITEM_BASE, estado=estado)])


def test_iva_uso_particular_por_operacion_y_cambio_por_producto():
    items = [dict(ITEM_BASE), dict(ITEM_BASE, iva_adicional="NO_VALIDA")]
    txt = _gen(items, iva_adicional="IVAAD1")
    assert _valor(txt, "IVAADICIONAL1", "0001") == ["IVAAD1"]
    assert _valor(txt, "IVAADICIONAL1", "0002") == ["NO_VALIDA"]


@pytest.mark.parametrize("kw", [{"iva_adicional": "IVAAD2"}, {"empresa_digitalizacion": "PSAD99"},
                                {"banco_bcra": "19"}, {"banco_bcra": "abc"}])
def test_valores_no_validos_se_rechazan(kw):
    with pytest.raises(ValueError):
        _gen(**kw)


def test_banco_y_lakaut():
    txt = _gen(banco_bcra="191", empresa_digitalizacion="PSAD01")
    assert _valor(txt, "BANCOSARGENTINA") == ["191"]
    assert _valor(txt, "ARDIG-CUIT-PSAD") == ["PSAD01"]


def test_grupo_con_estados_distintos_se_rechaza():
    items = [dict(ITEM_BASE, grupo_id=1, estado=2),
             dict(ITEM_BASE, grupo_id=1, estado=6)]
    with pytest.raises(ValueError, match="mismo estado"):
        _gen(items)


# --- El archivo real de 2026 ------------------------------------------------

def test_archivo_real_2026_cuatro_campos_y_su_orden():
    """Cargando sus valores (estado 2, reventa, banco 191, Lakaut) salen los
    cuatro campos como en el archivo real, y el banco en el mismo lugar."""
    subitems = [
        {"cantidad": 2, "valor_unitario": 1197.00, "sufijo": SUF_A},
        {"cantidad": 4, "valor_unitario": 1197.00, "sufijo": SUF_B},
    ]
    item = dict(ITEM_BASE, subitems=subitems, estado=2)
    txt = generate_maria_txt(items=[item], **{**COMUN, "banco_bcra": "191",
                                               "empresa_digitalizacion": "PSAD01",
                                               "iva_adicional": "NO_VALIDA"})
    real = open(REFERENCIA, encoding="utf-8").read()

    for t in (txt, real):
        assert _cartuso(t) == ["2"]
        assert _valor(t, "BANCOSARGENTINA") == ["191"]
        assert _valor(t, "ARDIG-CUIT-PSAD") == ["PSAD01"]
        assert _valor(t, "IVAADICIONAL1", "0001") == ["NO_VALIDA"]

    def orden(t):
        nombres = [c for n, c, m in _cpl(t) if n == "0000"]
        return [c for c in nombres if c in ("BANCOSARGENTINA", "ARDIG-SETI-OPC", "ARDIG-CUIT-PSAD")]

    assert orden(txt) == orden(real) == ["BANCOSARGENTINA", "ARDIG-SETI-OPC", "ARDIG-CUIT-PSAD"]


# --- El endpoint --------------------------------------------------------------

def test_endpoint_pasa_los_valores_y_avisa_lo_que_falta(client, auth_override):
    cuerpo = dict(
        operation_id="002720126", items=[dict(ITEM_BASE, estado=5)],
        incoterm="EXW", flete=365.0, seguro=75.47, fecha_emision="22/06/2026",
        aduana_codigo="073", sbt_sufijo_valor=SUF_A,
        banco_bcra="191", empresa_digitalizacion="PSAD01", iva_adicional="IVAAD1",
    )
    r = client.post("/generate_maria", json=cuerpo)
    assert r.status_code == 200, r.text
    supuestos = " | ".join(r.json().get("supuestos", [])).lower()
    assert "estado de la mercadería" not in supuestos
    assert "banco: no se declaró" not in supuestos

    sin = dict(cuerpo, banco_bcra="", items=[dict(ITEM_BASE, origen="AR")])
    r = client.post("/generate_maria", json=sin)
    assert r.status_code == 400, r.text
    assert "origen es argentino" in r.text
