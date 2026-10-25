"""SUFIJOS-1: qué sufijos de valor pide cada posición y su unidad
estadística, del arancel de ARCA del 07/10/2026 (D22 a), sin red.

El caso del 24/10, en sintético: una posición de plásticos (capítulo 39)
pide AA (marca) y AI (código); `3920.10.10.100F` lleva kilogramo (01). Cada
producto que sale entero lleva su propio sufijo en `CSBTSVL`; lo que la tabla
pide y no está, la posición que no está y el AI repetido se avisan, con la
fuente. Datos inventados con la forma de la factura de lonas.
"""
import gzip
import hashlib
import json
import subprocess
from pathlib import Path
from zipfile import ZipFile

import pytest

from proyecto_maria.core import maria_generator as mg
from proyecto_maria.core import sufijos_arca as sa
from scripts import import_arancel_sufijos as imp
from tests.test_maria7_rechazos_24_10 import LONA, SUFIJO, _gen, _registrar_con_cuit, _valor
from tests.test_maria8_subitems_por_posicion import _bloques

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "docs" / "pm" / "datos" / "arancel_ARCA_07102026.zip"
FUENTE = "arancel de ARCA del 07/10/2026"
PLASTICO = "39201010100F"  # 3920.10.10.100F
FUERA = "39211390900F"     # no está en el arancel
PROPIO = "AA(MARCA DEMO)-AI(620G GRIS 150CMX50M)-"


def _avisos(items, **kw):
    return mg.supuestos_declarados(items, sbt_sufijo_valor=kw.pop("sbt_sufijo_valor", SUFIJO), **kw)


# ------------------------------------------------------------- la tabla


def test_el_capitulo_39_pide_marca_y_codigo_y_la_unidad_es_kilos():
    for posicion in ("3920.10.10.100F", PLASTICO, LONA["pieza"]):
        c = sa.consultar(posicion)
        assert [s["codigo"] for s in c["sufijos"]] == ["AA", "AI"], posicion
        assert c["unidad_estadistica"] == "01"
        assert c["fuente"] == FUENTE


def test_una_posicion_que_no_es_la_del_arancel_no_devuelve_nada():
    assert sa.consultar(FUERA) is None
    assert sa.consultar("3920.10.10.100A") is None  # la letra de control no es la suya
    assert sa.consultar("39201010") is None         # NCM de 8: no es una posición SIM
    assert sa.consultar("") is None
    assert sa.consultar(PLASTICO, tabla={}) is None  # sin tabla no se completa nada


def test_las_opciones_cerradas_se_agrupan_y_de_cada_grupo_alcanza_una():
    c = sa.consultar("0101.21.00.100")  # caballos reproductores
    grupos = {g["grupo"] for g in c["opciones"]}
    assert "NA" in grupos
    na = next(g for g in c["opciones"] if g["grupo"] == "NA")
    falta = sa.faltan(c, ["AX", "AV", na["opciones"][0]["codigo"]])
    assert not any(f.startswith("NA ") for f in falta), falta
    assert any(f.startswith("NA (elegí uno: NA01") for f in sa.faltan(c, ["AX", "AV"]))


def test_la_tabla_del_repositorio_es_la_que_sale_del_zip():
    with gzip.open(sa.TABLA, "rt", encoding="utf-8") as fh:
        guardada = json.load(fh)
    assert guardada == imp.armar(ZIP)
    assert guardada["archive_sha256"] == hashlib.sha256(ZIP.read_bytes()).hexdigest()


def test_las_descripciones_partidas_en_dos_lineas_se_unen():
    lineas = ["3@39@AA@123@MARCA", "3@3920.10.10.100@ZA@123@ESPESOR", "  EN MICRONES", ""]
    assert sa.parse_sufijos(lineas) == {"39": [["AA", "MARCA"]],
                                        "39201010100": [["ZA", "ESPESOR EN MICRONES"]]}
    with pytest.raises(ValueError, match="Continuación sin sufijo"):
        sa.parse_sufijos(["SUELTA"])
    with pytest.raises(ValueError, match="no se entiende"):
        sa.parse_sufijos(["3@39@A-1@123@MARCA"])


# ------------------------------------------------------------- el script


def _zip_sintetico(carpeta: Path) -> Path:
    ruta = carpeta / "arancel_sintetico.zip"
    with ZipFile(ruta, "w") as z:
        z.writestr("sufijos_01022026.txt", "3@39@AA@1@MARCA ÚNICA\r\n".encode("cp1252"))
        z.writestr("nomenclador_01022026.txt",
                   "2@3920.10.10.100F@x@x@x@x@x@x@01@\r\n".encode("cp1252"))
    return ruta


def test_el_script_frena_si_el_sha_no_es_el_del_leeme(tmp_path):
    ruta = _zip_sintetico(tmp_path)
    leeme = tmp_path / "LEEME.md"
    leeme.write_text(f"| {ruta.name} | {'0' * 64} |\n", encoding="utf-8")
    salida = tmp_path / "tabla.json.gz"
    assert imp.main(["--archive", str(ruta), "--leeme", str(leeme), "--salida", str(salida)]) == 1
    assert not salida.exists()
    leeme.write_text(f"| otro.zip | {hashlib.sha256(ruta.read_bytes()).hexdigest()} |\n", encoding="utf-8")
    assert imp.main(["--archive", str(ruta), "--leeme", str(leeme), "--salida", str(salida)]) == 1
    assert not salida.exists()


def test_el_script_lee_cp1252_y_sale_igual_byte_por_byte(tmp_path):
    ruta = _zip_sintetico(tmp_path)
    leeme = tmp_path / "LEEME.md"
    leeme.write_text(f"| {ruta.name} | {hashlib.sha256(ruta.read_bytes()).hexdigest()} |\n", encoding="utf-8")
    a, b = tmp_path / "a.json.gz", tmp_path / "b.json.gz"
    for salida in (a, b):
        assert imp.main(["--archive", str(ruta), "--leeme", str(leeme), "--salida", str(salida)]) == 0
    assert a.read_bytes() == b.read_bytes()
    tabla = json.loads(gzip.decompress(a.read_bytes()))
    assert tabla["sufijos"] == {"39": [["AA", "MARCA ÚNICA"]]}
    assert tabla["unidades"] == {"39201010100": ["F", "01"]}
    assert sa.fuente(tabla) == "arancel de ARCA del 01/02/2026"


# ------------------------------------------------------------- la propuesta


def test_el_valor_queda_con_letras_numeros_y_espacios():
    assert sa.valor_de_sufijo(" Señal-Ñandú  620G.GREY/008 ") == "Senal Nandu 620G GREY 008"
    assert sa.valor_de_sufijo(None) == ""


def test_se_propone_marca_y_codigo_y_se_marca_lo_que_falta():
    c = sa.consultar(PLASTICO)
    p = sa.proponer({"marca": "Demo", "modelo": "M1", "codigo_parte": "620G-GRIS"}, c)
    # AB no lo pide la posición: no se agrega aunque la IA lo haya leído.
    assert p == {"sufijo": "AA(Demo)-AI(620G GRIS)-", "completados": ["AA", "AI"], "faltan": []}
    p = sa.proponer({"marca": "Demo"}, c)
    assert p["sufijo"] == "AA(Demo)-"
    assert p["faltan"] == ["AI (CODIGO DE PRODUCTO O ARTICULO)"]
    assert sa.proponer({"marca": "Demo"}, None) == {"sufijo": "", "completados": [], "faltan": []}


def test_lo_que_no_entra_en_el_tope_queda_para_el_despachante():
    c = sa.consultar(PLASTICO)
    p = sa.proponer({"marca": "M" * 10, "codigo_parte": "C" * 200}, c, tope=120)
    assert p["sufijo"] == "AA(MMMMMMMMMM)-"
    assert p["faltan"] == ["AI (CODIGO DE PRODUCTO O ARTICULO)"]
    assert len(sa.proponer({"marca": "M" * 115}, c)["sufijo"]) <= 120


# ------------------------------------------------------------- el TXT


def test_un_producto_entero_lleva_su_propio_sufijo():
    txt = _gen([dict(LONA, sufijo=PROPIO)])
    assert _valor(txt, "CSBTSVL") == [PROPIO]


def test_el_propio_de_un_producto_entero_se_limpia_y_se_avisa():
    sucio = "AA(MARCA DEMO)-AI(620G-GRIS.150)-"
    assert _valor(_gen([dict(LONA, sufijo=sucio)]), "CSBTSVL") == ["AA(MARCA DEMO)-AI(620G GRIS 150)-"]
    assert any(a.startswith("Sufijo de valor del ítem 1:") for a in _avisos([dict(LONA, sufijo=sucio)]))


def test_sin_propio_un_producto_entero_lleva_el_de_la_operacion():
    assert _valor(_gen([dict(LONA)]), "CSBTSVL") == [mg.limpiar_sufijo(SUFIJO)[0]]


def test_dos_productos_enteros_con_su_codigo_cada_uno():
    a = dict(LONA, sufijo="AA(DEMO)-AI(GRIS 1)-")
    b = dict(LONA, pieza=PLASTICO, sufijo="AA(DEMO)-AI(NEGRA 2)-")
    assert _valor(_gen([a, b]), "CSBTSVL") == ["AA(DEMO)-AI(GRIS 1)-", "AA(DEMO)-AI(NEGRA 2)-"]


def test_un_grupo_con_sufijos_distintos_no_se_genera():
    a = dict(LONA, grupo_id="g1", sufijo="AA(DEMO)-AI(GRIS 1)-")
    b = dict(LONA, grupo_id="g1", sufijo="AA(DEMO)-AI(NEGRA 2)-")
    with pytest.raises(ValueError, match="Grupo g1: todos los ítems deben llevar el mismo sufijo de valor"):
        _gen([a, b])
    with pytest.raises(ValueError, match="Grupo g1: todos los ítems deben llevar el mismo sufijo de valor"):
        _gen([a, dict(b, sufijo="")])


def test_un_grupo_con_el_mismo_sufijo_sale_con_ese():
    a = dict(LONA, grupo_id="g1", sufijo="AA(DEMO)-AI(GRIS 1)-")
    assert _valor(_gen([a, dict(a)]), "CSBTSVL") == ["AA(DEMO)-AI(GRIS 1)-"]


def test_con_kilos_la_unidad_estadistica_sale_01_sin_aviso():
    lona = dict(LONA, pieza=PLASTICO, unidad_estadistica="01")
    assert _valor(_gen([lona]), "CARTUNTEST") == ["01"]
    assert not any(a.startswith("Unidad estadística") for a in _avisos([lona]))


def test_si_la_unidad_estadistica_no_es_la_del_arancel_se_avisa():
    lona = dict(LONA, pieza=PLASTICO)  # m², sin elegir la estadística
    assert _valor(_gen([lona]), "CARTUNTEST") == ["03"]  # no se cambia sola
    avisos = [a for a in _avisos([lona, dict(lona)]) if a.startswith("Unidad estadística")]
    assert avisos == [
        f"Unidad estadística: según el {FUENTE}, la posición 3920.10.10.100F va en 01 "
        f"(kilogramo); los ítems 1 y 2 salen en 03. Elegí «Kilogramo (01)» en «Lo que "
        f"decide el despachante»."
    ]


# ------------------------------------------------------------- los avisos


def test_lo_que_la_posicion_pide_y_falta_se_avisa_con_la_fuente():
    avisos = _avisos([dict(LONA, pieza=PLASTICO, sufijo="AA(DEMO)-")])
    assert (f"Sufijo de valor del ítem 1: según el {FUENTE}, la posición 3920.10.10.100F "
            f"pide AI (CODIGO DE PRODUCTO O ARTICULO), y no está.") in avisos
    assert not any("pide" in a for a in _avisos([dict(LONA, pieza=PLASTICO, sufijo=PROPIO)]))


def test_tambien_falta_en_el_de_la_operacion_cuando_lo_usa_un_producto():
    avisos = _avisos([dict(LONA, pieza=PLASTICO)], sbt_sufijo_valor="AA(DEMO)-")
    assert any(a.startswith("Sufijo de valor del ítem 1: según el") and "pide AI" in a for a in avisos)


def test_un_grupo_se_controla_una_vez():
    a = dict(LONA, pieza=PLASTICO, grupo_id="g1", sufijo="AA(DEMO)-")
    pide = [x for x in _avisos([a, dict(a)]) if "pide AI" in x]
    assert pide == [f"Sufijo de valor del grupo g1: según el {FUENTE}, la posición "
                    f"3920.10.10.100F pide AI (CODIGO DE PRODUCTO O ARTICULO), y no está."]


def test_una_posicion_fuera_del_arancel_se_marca_para_el_despachante():
    avisos = _avisos([dict(LONA, pieza=FUERA, sufijo=PROPIO), dict(LONA, pieza=FUERA, sufijo="AA(B)-AI(C)-")])
    assert (f"Posición 3921.13.90.900F (ítems 1 y 2): no está en el {FUENTE}. Los sufijos de "
            f"valor y la unidad estadística no se completan ni se controlan: cargalos a mano "
            f"con el despachante.") in avisos


def test_el_codigo_ai_repetido_entre_productos_se_avisa():
    a = dict(LONA, sufijo="AA(DEMO)-AI(GRIS 1)-")
    b = dict(LONA, pieza=PLASTICO, sufijo="AA(OTRA)-AI(GRIS 1)-")
    repetidos = [x for x in _avisos([a, b, dict(LONA, pieza=PLASTICO, sufijo="AA(DEMO)-AI(NEGRA)-")])
                 if x.startswith("Código de artículo")]
    assert repetidos == ["Código de artículo (AI): «GRIS 1» se repite en los ítems 1 y 2; "
                         "cada producto lleva el suyo."]


def test_el_ai_de_los_sub_items_tambien_cuenta():
    lona = dict(LONA, pieza=PLASTICO, subitems=[
        {"cantidad": 375, "valor_unitario": 1.85, "sufijo": "AA(DEMO)-AI(X1)-"},
        {"cantidad": 375, "valor_unitario": 1.85, "sufijo": "AA(DEMO)-AI(X1)-"}])
    repetidos = [x for x in _avisos([lona]) if x.startswith("Código de artículo")]
    assert repetidos == ["Código de artículo (AI): «X1» se repite en el ítem 1, sub-ítem 1 y "
                         "el ítem 1, sub-ítem 2; cada producto lleva el suyo."]


def test_el_aviso_de_renglones_juntos_dice_donde_se_carga():
    a = dict(LONA, pieza=PLASTICO)
    avisos = [x for x in _avisos([a, dict(a, descripcion="Lona de PVC negra")])
              if x.startswith("Sufijo de valor: en el ítem de los renglones")]
    assert len(avisos) == 1
    assert "«Sufijo de valor» de cada producto, en «Lo que decide el despachante»" in avisos[0]
    assert "todavía no deja" not in avisos[0]


# ------------------------------------------------------------- el endpoint


def test_la_propuesta_pide_sesion(client, sin_bypass_de_test):
    r = client.post("/api/sufijos/propuesta", json={"items": [{"pieza": PLASTICO}]})
    assert r.status_code == 401


def test_la_propuesta_por_producto(client):
    _registrar_con_cuit(client, "sufijos1_prop")
    r = client.post("/api/sufijos/propuesta", json={"items": [
        {"pieza": PLASTICO, "marca": "Demo", "codigo_parte": "620G-GRIS"},
        {"pieza": FUERA, "marca": "Demo"},
        {"pieza": "", "marca": "Demo"},
    ]})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["fuente"] == FUENTE
    uno, dos, tres = d["items"]
    assert uno["sufijo"] == "AA(Demo)-AI(620G GRIS)-"
    assert uno["unidad_estadistica"] == "01"
    assert uno["sufijos"] == [{"codigo": "AA", "descripcion": "MARCA"},
                              {"codigo": "AI", "descripcion": "CODIGO DE PRODUCTO O ARTICULO"}]
    assert uno["faltan"] == [] and uno["en_la_tabla"] is True
    assert dos == {"posicion": FUERA, "en_la_tabla": False, "sufijo": "", "faltan": [],
                   "sufijos": [], "opciones": [], "unidad_estadistica": None}
    assert tres["en_la_tabla"] is False and tres["sufijo"] == ""


def test_la_propuesta_rechaza_lo_que_no_es_una_lista(client):
    _registrar_con_cuit(client, "sufijos1_mal")
    for cuerpo in ({"items": "x"}, {"items": [1]}, {"items": [{"pieza": PLASTICO}] * 501}):
        r = client.post("/api/sufijos/propuesta", json=cuerpo)
        assert r.status_code in (400, 422), (cuerpo if len(str(cuerpo)) < 80 else "501", r.status_code)


# ------------------------------------------------------------- la pantalla


V2 = ROOT / "proyecto_maria" / "static" / "v2" / "screens"


def _unidades_de(casos):
    """Corre `unidadesDe` de despachante.js en node con un CDI mínimo."""
    codigo = (
        "global.window = {}; global.document = { getElementById: () => null };\n"
        + (V2 / "despachante.js").read_text(encoding="utf-8")
        + "\nconst CDI = window.CDI; CDI.state = { operacion: { despachante: {} } };"
        + f"\nconst casos = {json.dumps(casos)};"
        + "\nconsole.log(JSON.stringify(casos.map(([it, op, tabla]) => {"
        + " CDI.state.operacion.despachante = op; CDI.despachante.recordarTabla(tabla);"
        + " return CDI.despachante.unidadesDe(it); })));"
    )
    salida = subprocess.run(["node", "-e", codigo], check=True, capture_output=True, text=True)
    return json.loads(salida.stdout)


def test_la_estadistica_de_la_tabla_va_al_pedido_si_nadie_eligio_otra():
    kilos = {PLASTICO: {"unidad_estadistica": "01"}}
    m2 = {PLASTICO: {"unidad_estadistica": "03"}}
    lona = {"pieza": PLASTICO, "unidad": "03"}
    assert [u["unidad_estadistica"] for u in _unidades_de([
        [lona, {}, kilos],                                   # la tabla dice kilos: va 01
        [lona, {}, m2],                                      # la tabla dice la declarada: nada
        [lona, {}, {}],                                      # fuera de la tabla: nada
        [lona, {"unidad_estadistica": "DCL"}, kilos],        # la persona eligió la de la factura
        [dict(lona, unidad_estadistica="DCL"), {}, kilos],   # en el producto, también
        [{"pieza": FUERA, "unidad": "03"}, {"unidad_estadistica": "01"}, kilos],
    ])] == ["01", None, None, None, None, "01"]
