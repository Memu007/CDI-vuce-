"""Segunda devolución de MARIA-5 y CATALOGO-NCM-1 (PM, 2026-10-07 19:30 UTC).

1. Una columna de peso desconocida («Peso por caja») nunca le gana a una
   reconocida; sola, se usa con aviso.
2. El bruto es bruto aunque diga «unitario».
3. Dos pesos de la línea que no coinciden: el aviso muestra los dos números.
5. Una NCM dada de baja: un solo aviso, cierto, también en /generate_maria/avisos.
6. Sin el archivo del catálogo no se inventan errores: un aviso.
De paso: los mensajes del peso dicen la razón real.
(El punto 4 es scripts/testing/pantalla_maria5.js.)
"""
import pytest

from proyecto_maria.core import controles_maria, ncm_catalog
from tests.test_maria5_centavos import _item
from tests.test_maria5_peso_excel import _subir
from tests.test_generar_maria_txt import _gen
from tests.test_maria_subitems import ITEM_BASE, SUF_A


# --- 1 y 2. Excel ----------------------------------------------------------

@pytest.mark.parametrize("columnas, pesos", [(["Peso por caja", "Peso"], [40, 2.5]),
                                             (["Peso", "Peso por caja"], [2.5, 40]),
                                             (["Peso por bulto", "Net weight"], [40, 25])])
def test_una_columna_desconocida_no_le_gana_a_una_reconocida(auth_override, client, columnas, pesos):
    data = _subir(client, columnas, pesos)
    assert data["items"][0]["peso_unitario"] == pytest.approx(2.5), data


def test_una_columna_desconocida_sola_se_usa_con_aviso(auth_override, client):
    data = _subir(client, ["Peso por caja"], [2.5])
    assert data["items"][0]["peso_unitario"] == pytest.approx(2.5)
    assert any("«Peso por caja»" in a and "revis" in a.lower() for a in data["avisos"]), data["avisos"]


@pytest.mark.parametrize("columna", ["Peso bruto unitario", "Gross weight per unit"])
def test_el_bruto_unitario_es_bruto(auth_override, client, columna):
    data = _subir(client, [columna, "Peso neto"], [3, 25])
    assert data["items"][0]["peso_unitario"] == pytest.approx(2.5)  # gana el neto
    data = _subir(client, [columna], [30])
    assert any("bruto" in a for a in data["avisos"]), data["avisos"]


# --- 3. Dos pesos de la línea ---------------------------------------------

def test_dos_pesos_de_la_linea_que_no_coinciden_muestran_los_numeros(auth_override, client):
    data = _subir(client, ["Peso neto", "Peso total"], [25, 27])
    assert data["items"][0]["peso_unitario"] == pytest.approx(2.5)
    assert any("27" in a and "25" in a and "«Peso total»" in a for a in data["avisos"]), data["avisos"]


# --- 5. La baja: un solo aviso y cierto ------------------------------------

ITEM_BAJA = {"pieza": "85171231000X", "descripcion": "Telefono celular de prueba", "origen": "CN",
             "cantidad": 2, "valor_unitario": 100, "peso_unitario": 0.2}


def test_la_baja_sale_una_vez_en_la_validacion(client, auth_override):
    r = client.post("/api/validate/smart", json={
        "items": [ITEM_BAJA], "operacion": {"moneda": "DOL", "incoterm": "FOB", "comprador_cuit": "30999999995"}})
    avisos = [a for a in r.json()["advertencias"] if "8517.12.31" in a or "85171231" in a]
    assert len(avisos) == 1 and "se dio de baja" in avisos[0], r.json()["advertencias"]
    assert not any("2018" in a for a in r.json()["advertencias"]), r.json()["advertencias"]


def test_la_baja_sale_en_los_avisos_antes_de_generar(client, auth_override):
    item = dict(ITEM_BASE, estado=2, pieza="85171231000X", ncm="85171231000X")
    r = client.post("/generate_maria/avisos", json={
        "operation_id": "OP1", "items": [item], "fecha_emision": "22/06/2026", "sbt_sufijo_valor": SUF_A,
        "moneda": "DOL", "incoterm": "EXW", "comprador_cuit": "30999999995"})
    assert r.status_code == 200, r.text
    assert sum("se dio de baja" in a for a in r.json()["avisos"]) == 1, r.json()["avisos"]


def test_ningun_aviso_dice_el_de_2018():
    errores, avisos = [], []
    controles_maria._control_ncm("99998888000A", 1, errores, avisos)
    assert avisos and not any("2018" in a for a in avisos), avisos


# --- 6. Sin catálogo -------------------------------------------------------

@pytest.fixture
def sin_catalogo(monkeypatch, tmp_path):
    """El catálogo apunta a un archivo que no existe."""
    original = ncm_catalog.load_catalog.__wrapped__
    monkeypatch.setattr(ncm_catalog, "load_catalog", lambda *a, **k: original(tmp_path / "no_existe.csv.gz"))
    ncm_catalog._codigos_vigentes.cache_clear()
    monkeypatch.setattr(controles_maria, "_CODIGOS", None)
    yield
    ncm_catalog._codigos_vigentes.cache_clear()
    controles_maria._CODIGOS = None


@pytest.mark.parametrize("pieza", ["9999999", "1012100000A", "99998888", "85171231000X"])
def test_sin_catalogo_no_se_inventan_errores(sin_catalogo, pieza):
    errores, avisos = [], []
    controles_maria._control_ncm(pieza, 1, errores, avisos)
    controles_maria._control_ncm(pieza, 2, errores, avisos)
    assert errores == [], errores
    assert len(avisos) == 1 and "catálogo" in avisos[0], avisos


# --- De paso: los mensajes del peso ---------------------------------------

@pytest.mark.parametrize("peso, dice, no_dice", [
    (float("nan"), "no es un número", "tope"), (float("inf"), "no es un número", "tope"),
    (-1, "negativo", "no es un número"), (2e12, "tope", "negativo"), (0.0004, "0.001", "negativo"),
])
def test_los_mensajes_del_peso_dicen_la_razon(peso, dice, no_dice):
    with pytest.raises(ValueError) as e:
        _gen("OP_PESO", [_item(10, peso_kg=peso)])
    assert dice in str(e.value) and no_dice not in str(e.value), str(e.value)


def test_un_peso_chico_en_el_aviso_no_es_cero(auth_override, client):
    data = _subir(client, ["Peso unitario", "Peso total"], [0.0004, 0.05])
    assert not any(" 0 kg" in a or "(0 kg" in a or "= 0 kg" in a for a in data["avisos"]), data["avisos"]
