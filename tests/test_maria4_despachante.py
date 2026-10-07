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

@pytest.mark.parametrize("origen, estado", [("CN", 2), ("CN", 4), ("CN", 6), ("CN", "4"),
                                            ("AR", 1), ("AR", 3), ("AR", 5)])
def test_estado_elegido_por_producto(origen, estado):
    txt = _gen([dict(ITEM_BASE, origen=origen, estado=estado)])
    assert _cartuso(txt) == [str(estado)]


@pytest.mark.parametrize("origen, estado", [("CN", 1), ("CN", 3), ("CN", 5),
                                            ("AR", 2), ("AR", 4), ("AR", 6), ("200", "2")])
def test_estado_que_no_corresponde_al_origen_se_rechaza(origen, estado):
    """Devolución de la PM: un estado argentino con origen extranjero, o uno
    importado con origen argentino, no se genera."""
    with pytest.raises(ValueError, match="no corresponde al origen"):
        _gen([dict(ITEM_BASE, origen=origen, estado=estado)])


def test_supuestos_leen_el_origen_como_el_generador():
    """Devolución de la PM: con pais_origen y origen distintos, el generador
    usa pais_origen; los supuestos también."""
    from proyecto_maria.core.maria_generator import supuestos_declarados
    item = dict(ITEM_BASE, pais_origen="CN", origen="AR")
    assert _cartuso(_gen([item])) == ["2"]          # el generador lo toma como China
    texto = " | ".join(supuestos_declarados([item])).lower()
    assert "estado de la mercadería: en el/los ítem(s) 1" in texto


def test_la_pantalla_vieja_muestra_los_avisos_de_generate_maria():
    """Devolución de la PM: la v1 muestra warnings y supuestos de la respuesta."""
    import pathlib
    fuente = (pathlib.Path(__file__).resolve().parents[1] / "proyecto_maria" / "static" / "app.js").read_text(encoding="utf-8")
    tramo = fuente[fuente.index("endpoint = '/generate_maria';"):]
    tramo = tramo[:tramo.index("window.location.href = data.download_url")]
    assert "data.supuestos" in tramo and "data.warnings" in tramo


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
             dict(ITEM_BASE, grupo_id=1, estado=4)]
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
        operation_id="002720126", items=[dict(ITEM_BASE, estado=6)],
        moneda="DOL", comprador_cuit="30999999995",  # MARIA-1b
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


def test_lo_elegido_se_guarda_con_la_operacion_y_vuelve_en_los_listados(client, auth_override):
    """La pantalla propone el último banco del cliente y la última empresa del
    usuario leyendo `maria` de sus operaciones guardadas."""
    r = client.post("/api/clientes", json={"nombre": "Cliente MARIA-4", "cuit": "30712345678"})
    assert r.status_code in (200, 201), r.text
    cid = (r.json().get("cliente") or r.json()).get("id")
    elegido = {"banco_bcra": "191", "empresa_digitalizacion": "PSAD01", "iva_adicional": "IVAAD1"}
    r = client.post(f"/api/clientes/{cid}/operaciones", json={
        "operation_id": "M4-1", "source": "pdf_v2", "currency": "USD",
        "resumen": {"items": 1, "valor_total": 10, "peso_total": 1, "maria": elegido},
        "items": [{"pieza": "84714900100D", "descripcion": "Equipo", "origen": "CN",
                   "cantidad": 1, "valor_unitario": 10, "peso_unitario": 1}],
    })
    assert r.status_code in (200, 201), r.text

    ops = client.get(f"/api/clientes/{cid}/operaciones").json()["operaciones"]
    assert ops[0]["maria"] == elegido
    ops = client.get("/api/operations").json()["operaciones"]
    assert any(o.get("maria") == elegido for o in ops)


def test_iva_en_minusculas_se_normaliza():
    txt = _gen(iva_adicional="ivaad1")
    assert _valor(txt, "IVAADICIONAL1", "0001") == ["IVAAD1"]


def test_grupo_con_iva_distinto_se_rechaza():
    items = [dict(ITEM_BASE, grupo_id=1, iva_adicional="IVAAD1"),
             dict(ITEM_BASE, grupo_id=1, iva_adicional="NO_VALIDA")]
    with pytest.raises(ValueError, match="mismo IVA"):
        _gen(items)


def test_grupo_con_el_mismo_valor_escrito_distinto_se_acepta():
    """El valor por defecto y el mismo valor escrito salen igual en el TXT."""
    items = [dict(ITEM_BASE, grupo_id=1), dict(ITEM_BASE, grupo_id=1, estado="2", iva_adicional="no_valida")]
    txt = _gen(items)
    assert _cartuso(txt) == ["2"]


@pytest.mark.parametrize("banco", ["١٩١", "²³⁴", "１９１"])
def test_banco_con_digitos_que_no_son_0_a_9_se_rechaza(banco):
    with pytest.raises(ValueError, match="BCRA"):
        _gen(banco_bcra=banco)


def test_los_listados_recortan_lo_guardado(client, auth_override):
    r = client.post("/api/clientes", json={"nombre": "Cliente largo", "cuit": "30712345670"})
    cid = (r.json().get("cliente") or r.json()).get("id")
    client.post(f"/api/clientes/{cid}/operaciones", json={
        "operation_id": "M4-L", "source": "pdf_v2", "currency": "USD",
        "resumen": {"items": 1, "maria": {"banco_bcra": "9" * 5000, "iva_adicional": {"a": [1]}}},
        "items": [{"pieza": "84714900100D", "descripcion": "Equipo", "origen": "CN",
                   "cantidad": 1, "valor_unitario": 10, "peso_unitario": 1}],
    })
    maria = client.get(f"/api/clientes/{cid}/operaciones").json()["operaciones"][0]["maria"]
    assert len(maria["banco_bcra"]) <= 12 and maria["iva_adicional"] == ""
