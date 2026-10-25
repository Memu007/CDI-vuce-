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
FUERA = "39211390999F"     # no está en el arancel (39211390900 sí, con G)
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
    assert (f"Posición 3921.13.90.999F (ítems 1 y 2): no está en el {FUENTE}. Los sufijos de "
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
                   "sufijos": [], "opciones": [], "unidad_estadistica": None,
                   "letra_de_control": ""}
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


def test_con_sub_items_la_estadistica_de_la_tabla_no_va_sola():
    # Con sub-ítems, kilos sólo cierra si la de la factura también es en kilos
    # (el generador lo frena): la pantalla no la pone sola.
    kilos = {PLASTICO: {"unidad_estadistica": "01"}}
    partido = {"pieza": PLASTICO, "unidad": "03", "subitems": [{"cantidad": 1}, {"cantidad": 2}]}
    assert [u["unidad_estadistica"] for u in _unidades_de([
        [partido, {}, kilos],
        [partido, {"unidad_estadistica": "01"}, kilos],      # la persona eligió kilos: va
    ])] == [None, "01"]


def _despachante(pasos):
    """Corre despachante.js en node con un CDI mínimo y un arancel falso que
    propone AA con la marca y AI con el código; `pasos` es JS que deja lo que
    se mide en `salida`."""
    codigo = (
        "global.window = {}; global.document = { getElementById: () => null };\n"
        + (V2 / "despachante.js").read_text(encoding="utf-8")
        + "\nconst CDI = window.CDI; CDI.state = { operacion: { despachante: {} }, items: [] };"
        + "\nlet pedidos = 0;"
        + "\nCDI.api = async (ruta, op) => { pedidos += 1; const b = JSON.parse(op.body);"
        + " await new Promise(r => setImmediate(r));"
        + " return { ok: true, json: async () => ({ fuente: 'arancel de ARCA del 07/10/2026', items:"
        + " b.items.map(x => x.pieza === '" + PLASTICO + "' ? { posicion: x.pieza, en_la_tabla: true,"
        + " unidad_estadistica: '01', faltan: [], sufijo: (x.marca ? 'AA(' + x.marca + ')-' : '')"
        + " + (x.codigo_parte ? 'AI(' + x.codigo_parte + ')-' : '') }"
        + " : { posicion: x.pieza, en_la_tabla: false, sufijo: '', faltan: [] }) }) }; };"
        + "\nconst salida = {}; const D = CDI.despachante;"
        + "\n(async () => {\n" + pasos + "\nconsole.log(JSON.stringify(salida)); })();"
    )
    r = subprocess.run(["node", "-e", codigo], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _producto(marca, codigo="", pieza=PLASTICO):
    return {"pieza": pieza, "marca": marca, "codigo_parte": codigo}


def test_la_propuesta_se_suma_a_lo_que_trae_el_de_la_operacion():
    # El de la operación tiene códigos que la propuesta no completa (PC01,
    # CA00): se conservan, y AA y AI salen del producto.
    casos = {
        "op_con_otros": ("AA(OPMARCA)-PC01-", "AA(ACME)-PC01-AI(X1)-"),
        "op_en_minusculas": ("aa(op)-ca00", "AA(ACME)-ca00-AI(X1)-"),
        "op_vacia": ("", "AA(ACME)-AI(X1)-"),
        "op_que_no_se_separa": ("AA(SIN CERRAR", ""),   # lo dice el servidor con el de la operación
    }
    pasos = "".join(
        f"CDI.state.items = [{json.dumps(_producto('ACME', 'X1'))}];"
        f"CDI.state.operacion.sbt_sufijo_valor = {json.dumps(op)};"
        f"await D.listo(); salida[{json.dumps(nombre)}] = D.sufijoDe(CDI.state.items[0], 0);\n"
        for nombre, (op, _) in casos.items())
    assert _despachante(pasos) == {nombre: esperado for nombre, (_, esperado) in casos.items()}


def test_lo_que_escribe_la_persona_va_tal_cual():
    salida = _despachante(
        f"CDI.state.operacion.sbt_sufijo_valor = 'AA(OP)-CA00-';"
        f"CDI.state.items = [{json.dumps(dict(_producto('ACME', 'X1'), sufijo='AA(MANO)-'))},"
        f" {json.dumps(_producto('ACME', pieza=FUERA))}];"
        "await D.listo(); salida.mano = D.sufijoDe(CDI.state.items[0], 0);"
        " salida.fuera = D.sufijoDe(CDI.state.items[1], 1);")
    assert salida == {"mano": "AA(MANO)-", "fuera": ""}


def test_la_propuesta_de_una_fila_no_pasa_al_producto_que_queda_en_su_lugar():
    # Se borra el primero: hasta que llega la propuesta nueva, el que queda
    # en la fila 0 no lleva la marca del borrado.
    salida = _despachante(
        f"CDI.state.items = [{json.dumps(_producto('SAMSUNG', 'S1'))}, {json.dumps(_producto('LG', 'L1'))}];"
        "await D.listo(); salida.antes = D.sufijoDe(CDI.state.items[1], 1);"
        "CDI.state.items.splice(0, 1);"
        "salida.en_el_medio = D.sufijoDe(CDI.state.items[0], 0);"
        "const viejo = D.listo(); CDI.state.items[0].marca = 'LG2';"   # cambia otra vez en vuelo
        "await D.listo(); await viejo; salida.despues = D.sufijoDe(CDI.state.items[0], 0);"
        "salida.pedidos = pedidos;")
    assert salida == {"antes": "AA(LG)-AI(L1)-", "en_el_medio": "",
                      "despues": "AA(LG2)-AI(L1)-", "pedidos": 3}


def test_listo_no_repite_el_pedido_en_curso():
    salida = _despachante(
        f"CDI.state.items = [{json.dumps(_producto('ACME'))}];"
        "await Promise.all([D.listo(), D.listo(), D.listo()]); await D.listo();"
        "salida.pedidos = pedidos;")
    assert salida == {"pedidos": 1}


def test_sin_la_tabla_la_nota_no_dice_que_la_posicion_no_esta():
    salida = _despachante(
        "CDI.api = async () => ({ ok: true, json: async () => ({ fuente: 'arancel de ARCA', sin_tabla: true,"
        " items: [{ posicion: 'X', en_la_tabla: false, sufijo: '', faltan: [] }] }) });"
        f"CDI.state.items = [{json.dumps(_producto('ACME'))}];"
        "await D.listo(); salida.nota = D.notaDe(CDI.state.items[0], 0);")
    assert salida == {"nota": "Falta la tabla del arancel de ARCA: cargalo a mano."}


# ------------------------------------------------- bordes de la revisión


def test_con_sub_items_el_aviso_de_unidad_no_manda_a_elegir_kilos():
    lona = dict(LONA, pieza=PLASTICO, subitems=[
        {"cantidad": 375, "valor_unitario": 1.85, "sufijo": "AA(DEMO)-AI(X1)-"},
        {"cantidad": 375, "valor_unitario": 1.85, "sufijo": "AA(DEMO)-AI(X2)-"}])
    avisos = [a for a in _avisos([lona]) if a.startswith("Unidad estadística")]
    assert avisos == [
        f"Unidad estadística: según el {FUENTE}, la posición 3920.10.10.100F va en 01 "
        f"(kilogramo); el ítem 1 sale en 03. Con sub-ítems sale en kilos sólo si la unidad "
        f"de la factura también es kilogramo y la cantidad es el kilo neto: declaralo así, "
        f"o sin sub-ítems, o confirmalo con el despachante."
    ]


def test_en_un_grupo_el_guion_final_no_hace_distintos_los_sufijos():
    a = dict(LONA, grupo_id="g1", sufijo="AA(DEMO)-AI(GRIS 1)-")
    assert _valor(_gen([a, dict(a, sufijo="AA(DEMO)-AI(GRIS 1)")]), "CSBTSVL") == ["AA(DEMO)-AI(GRIS 1)-"]


def test_un_codigo_con_el_valor_vacio_es_un_codigo_que_falta():
    avisos = _avisos([dict(LONA, pieza=PLASTICO, sufijo="AA( )-AI(620G)-")])
    assert (f"Sufijo de valor del ítem 1: según el {FUENTE}, la posición 3920.10.10.100F "
            f"pide AA (MARCA), y no está.") in avisos


def test_la_posicion_se_lee_con_puntos_y_sin_letras_de_mas():
    assert sa.consultar("3920.10.10.100F")["unidad_estadistica"] == "01"
    assert sa.consultar(" 3920.10.10.100f ")["unidad_estadistica"] == "01"
    for mal in ("3920.10.10.100X.", "39201010100FF", "39201010100X", "3920101010012"):
        assert sa.consultar(mal) is None, mal


def test_la_letra_de_control_equivocada_se_dice_como_tal():
    avisos = _avisos([dict(LONA, pieza="3920.10.10.100X", sufijo=PROPIO)])
    assert (f"Posición 3920.10.10.100X (ítem 1): en el {FUENTE} la letra de control de "
            f"3920.10.10.100 es F, no X. Revisá la posición; los sufijos de valor y la unidad "
            f"estadística no se completan ni se controlan.") in avisos
    assert not any(a.startswith("Posición 3920.10.10.100X (ítem 1): no está") for a in avisos)


def test_una_tabla_rota_es_una_tabla_que_falta(tmp_path):
    entera = gzip.compress(json.dumps({"unidades": {}}).encode())
    (tmp_path / "cortada.json.gz").write_bytes(entera[: len(entera) // 2])
    with gzip.open(tmp_path / "lista.json.gz", "wt") as fh:
        json.dump([1, 2], fh)
    assert sa.cargar(tmp_path / "cortada.json.gz") == {}
    assert sa.cargar(tmp_path / "lista.json.gz") == {}


def test_sin_la_tabla_la_propuesta_lo_dice(client, monkeypatch):
    _registrar_con_cuit(client, "sufijos1_sin_tabla")
    monkeypatch.setattr(sa, "cargar", lambda *a, **k: {})
    r = client.post("/api/sufijos/propuesta", json={"items": [{"pieza": PLASTICO}]})
    assert r.status_code == 200, r.text
    assert r.json()["sin_tabla"] is True
    monkeypatch.undo()
    assert client.post("/api/sufijos/propuesta", json={"items": [{"pieza": PLASTICO}]}).json()["sin_tabla"] is False


def test_la_propuesta_lee_la_ncm_antes_que_la_pieza(client):
    # Como el generador: si vienen las dos, manda la NCM.
    _registrar_con_cuit(client, "sufijos1_ncm")
    r = client.post("/api/sufijos/propuesta", json={"items": [{"ncm": PLASTICO, "pieza": "SKU-1"}]})
    assert r.json()["items"][0]["en_la_tabla"] is True


def test_la_propuesta_aguanta_texto_que_no_es_utf8_y_recorta_lo_largo(client, monkeypatch):
    _registrar_con_cuit(client, "sufijos1_bordes")
    r = client.post("/api/sufijos/propuesta", content=b'{"items": [{"pieza": "\\ud800", "marca": "\\udfff"}]}',
                    headers={"Content-Type": "application/json"})
    assert r.status_code == 200, r.text
    vistos = []
    original = sa.proponer
    monkeypatch.setattr(sa, "proponer", lambda it, c, **k: vistos.append(it) or original(it, c, **k))
    largo = "M" * 40000
    r = client.post("/api/sufijos/propuesta", json={"items": [
        {"pieza": PLASTICO, "marca": largo, "modelo": largo, "codigo_parte": largo}]})
    assert r.status_code == 200, r.text
    assert vistos and all(len(vistos[0][c]) <= 200 for c in ("marca", "modelo", "codigo_parte"))


def test_la_propuesta_dice_la_letra_de_control_que_corresponde(client):
    _registrar_con_cuit(client, "sufijos1_letra")
    r = client.post("/api/sufijos/propuesta", json={"items": [{"pieza": "3920.10.10.100X"}]})
    assert r.json()["items"][0]["en_la_tabla"] is False
    assert r.json()["items"][0]["letra_de_control"] == "F"


def test_con_la_letra_equivocada_la_nota_no_dice_que_la_posicion_no_esta():
    salida = _despachante(
        "CDI.api = async () => ({ ok: true, json: async () => ({ fuente: 'arancel de ARCA del 07/10/2026',"
        " items: [{ posicion: 'X', en_la_tabla: false, letra_de_control: 'F', sufijo: '', faltan: [] }] }) });"
        f"CDI.state.items = [{json.dumps(_producto('ACME'))}];"
        "await D.listo(); salida.nota = D.notaDe(CDI.state.items[0], 0);")
    assert salida == {"nota": "En el arancel de ARCA del 07/10/2026 la letra de control de esta "
                              "posición es F: revisá la posición."}
