"""MARIA-1d: un campo que Gemini devuelve vacío queda vacío.

Antes, `str(None)` dejaba «None» en el número de factura, el vendedor, el
comprador y el domicilio, y «NON» en la moneda y el incoterm. Llegaba al TXT
(`IDSO=FAC_None`, `CDDTINCOTE=NON`). Lo que queda vacío y el TXT necesita se
avisa antes de generar. Las dos copias del lector, con Gemini falso.
"""
import pytest

from proyecto_maria.core.maria_generator import supuestos_declarados
from tests.test_maria1a_lectura_factura import COPIAS, _leer
from tests.test_maria_subitems import ITEM_BASE, SUF_A

CAMPOS_TEXTO = ["numero_factura", "vendedor_nombre", "vendedor_id", "vendedor_direccion",
                "comprador_nombre", "comprador_domicilio", "moneda", "incoterm", "fecha_emision"]

VACIA = {
    "operacion": {c: None for c in CAMPOS_TEXTO + ["comprador_cuit", "vendedor_pais", "flete", "seguro"]},
    "items": [{"descripcion": "Equipo de prueba", "version": None, "codigo_parte": None,
               "cantidad": 2, "valor_unitario": 3, "peso_kg": 1, "origen": "CN"}],
}


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("campo", CAMPOS_TEXTO)
def test_campo_nulo_queda_vacio(monkeypatch, copia, campo):
    op = _leer(monkeypatch, copia, VACIA)["operacion"]
    assert op[campo] == "", f"{campo} = {op[campo]!r}"


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("campo", ["moneda", "incoterm"])
def test_moneda_e_incoterm_ausentes_no_se_inventan(monkeypatch, copia, campo):
    """Si la factura no los trae, no se pone DOL ni FOB: se eligen en la
    revisión, donde son obligatorios."""
    factura = {"operacion": {"numero_factura": "F-1"}, "items": VACIA["items"]}
    assert _leer(monkeypatch, copia, factura)["operacion"][campo] == ""


@pytest.mark.parametrize("copia", COPIAS)
def test_lo_que_se_leyo_llega_limpio(monkeypatch, copia):
    factura = {"operacion": {"numero_factura": " INV-7 ", "vendedor_nombre": "Proveedor Inventado",
                             "moneda": "dol", "incoterm": "exw", "comprador_domicilio": "Calle Falsa 123"},
               "items": VACIA["items"]}
    op = _leer(monkeypatch, copia, factura)["operacion"]
    assert (op["numero_factura"], op["vendedor_nombre"], op["moneda"], op["incoterm"],
            op["comprador_domicilio"]) == ("INV-7", "Proveedor Inventado", "DOL", "EXW", "Calle Falsa 123")


def _pedido_como_la_pantalla(op, items):
    """Arma el pedido como `finalize.js`, `buildMariaRequest` (con los valores
    que la revisión exige: fecha, moneda, incoterm y el sufijo)."""
    factura = (op.get("numero_factura") or "").strip()
    return {
        "operation_id": ("FAC_" + factura) if factura else "OP_20261007120000",
        # Lo que el lector leyó de cada producto, con la NCM y el resto que se
        # cargan en NCM.
        "items": [dict(ITEM_BASE, estado=2, descripcion=it["descripcion"], origen=it["origen"],
                       codigo_parte=it.get("codigo_parte", "")) for it in items],
        "moneda": op.get("moneda") or "DOL",
        "incoterm": op.get("incoterm") or "FOB",
        "vendedor_nombre": op.get("vendedor_nombre", ""),
        "vendedor_id": op.get("vendedor_id", ""),
        "comprador_nombre": op.get("comprador_nombre", ""),
        "comprador_cuit": op.get("comprador_cuit", ""),
        "comprador_domicilio": op.get("comprador_domicilio", ""),
        # La revisión exige la fecha (devolución de MARIA-3).
        "fecha_emision": op.get("fecha_emision") or "22/06/2026",
        "sbt_sufijo_valor": SUF_A,
    }


@pytest.mark.parametrize("copia", COPIAS)
def test_ningun_none_en_el_txt_de_una_factura_vacia(monkeypatch, client, auth_override, copia):
    r = _leer(monkeypatch, copia, VACIA)
    pedido = _pedido_como_la_pantalla(r["operacion"], r["items"])
    resp = client.post("/generate_maria", json=pedido)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    txt = data["content"]
    for basura in ("None", "NON", "null"):
        assert basura not in txt, f"«{basura}» en el TXT"
    assert "None" not in data["filename"]
    avisos = " | ".join(data["supuestos"]).lower()
    assert "vendedor" in avisos and "importador" in avisos


def test_avisa_lo_que_falta_de_la_caratula():
    avisos = " | ".join(supuestos_declarados(
        [dict(ITEM_BASE)], vendedor_nombre="", comprador_nombre="", comprador_cuit="",
        moneda="", incoterm="")).lower()
    for palabra in ("vendedor", "nombre del importador", "cuit del importador", "moneda", "incoterm"):
        assert palabra in avisos, palabra


def test_con_la_caratula_completa_no_avisa():
    avisos = " | ".join(supuestos_declarados(
        [dict(ITEM_BASE)], vendedor_nombre="Proveedor", comprador_nombre="Importadora",
        comprador_cuit="30999999990", moneda="DOL", incoterm="FOB")).lower()
    assert "carátula" not in avisos


def test_sin_los_datos_de_la_caratula_no_se_evaluan():
    """Quien no pasa esos datos (llamadas viejas) no recibe el aviso."""
    assert "carátula" not in " | ".join(supuestos_declarados([dict(ITEM_BASE)])).lower()


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("vacio", ["None", "null", "N/A", " none "])
def test_el_vacio_escrito_como_texto_queda_vacio(monkeypatch, copia, vacio):
    factura = {"operacion": {"numero_factura": vacio, "moneda": vacio, "incoterm": vacio,
                             "vendedor_nombre": vacio}, "items": VACIA["items"]}
    op = _leer(monkeypatch, copia, factura)["operacion"]
    assert (op["numero_factura"], op["moneda"], op["incoterm"], op["vendedor_nombre"]) == ("", "", "", "")


@pytest.mark.parametrize("copia", COPIAS)
def test_una_descripcion_que_no_es_texto_no_tira_el_producto(monkeypatch, copia):
    factura = {"operacion": {}, "items": [dict(VACIA["items"][0], descripcion=4521)]}
    items = _leer(monkeypatch, copia, factura)["items"]
    assert [i["descripcion"] for i in items] == ["4521"]


def test_el_prompt_no_pide_adivinar_la_moneda():
    import pathlib
    texto = (pathlib.Path(__file__).resolve().parents[1] / "proyecto_maria" / "pdf_extractor.py").read_text()
    assert "Ante duda, DOL" not in texto


@pytest.mark.parametrize("valor", ["²", "99999", "٢٢٢", "Narnia"])
@pytest.mark.parametrize("clave", ["pais_procedencia", "procedencia"])
def test_procedencia_rara_de_un_producto_avisa_igual_antes_y_al_generar(client, auth_override, valor, clave):
    """Veredicto de MARIA-3: antes daba 200 sin aviso en /avisos y 400 al
    generar. El mismo texto en los dos."""
    item = dict(ITEM_BASE, estado=2, **{clave: valor})
    cuerpo = {"operation_id": "OP1", "items": [item], "fecha_emision": "22/06/2026",
              "sbt_sufijo_valor": SUF_A, "comprador_cuit": "30999999990"}
    r = client.post("/generate_maria", json=cuerpo)
    assert r.status_code == 400, r.text
    errores = r.json()["detail"]["errors"]
    mensaje = [e for e in errores if "Procedencia" in e]
    assert mensaje, errores
    avisos = client.post("/generate_maria/avisos", json=cuerpo).json()["avisos"]
    assert mensaje[0] in avisos, avisos
