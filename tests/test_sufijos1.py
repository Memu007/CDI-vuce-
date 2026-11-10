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
APP = ROOT / "proyecto_maria" / "static" / "v2" / "app_v2.js"

# Una página mínima para despachante.js: cada id existe; las celdas del
# sufijo y sus notas se leen de lo que la pantalla pintó en despachanteItems.
# El arancel falso propone AA con la marca y AI con el código para PLASTICO,
# con la unidad estadística de `unidades`; `modo` lo hace fallar ('falla',
# respuesta no ok) o tirar ('tira'); `frenar` lo deja colgado hasta soltar(),
# y `frenarOtras`, los demás pedidos (los del cliente) hasta soltarOtras().
_PAGINA = r"""
global.window = {};
const elementos = {};
function elemento(id) {
  if (!elementos[id]) {
    elementos[id] = { id, value: '', innerHTML: '', hidden: false, style: {}, textContent: '', dataset: {},
      oyentes: {}, classList: { contains: () => false },
      addEventListener(t, f) { (this.oyentes[t] = this.oyentes[t] || []).push(f); } };
  }
  return elementos[id];
}
const desescapar = s => s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"')
  .replace(/&#39;/g, "'").replace(/&amp;/g, '&');
let leido = { html: null, celdas: [], notas: [] };
function leerFilas() {
  const html = elemento('despachanteItems').innerHTML;
  if (leido.html === html) return leido;
  const celdas = [...html.matchAll(/<input [^>]*class="[^"]*\bdespachante-sufijo"[^>]*>/g)].map(m => ({
    value: desescapar(/ value="([^"]*)"/.exec(m[0])[1]), dataset: { row: /data-row="(\d+)"/.exec(m[0])[1] },
    classList: { contains: c => c === 'despachante-sufijo' } }));
  const notas = [...html.matchAll(/<div class="[^"]*\bdespachante-sufijo-nota"[^>]*data-row="(\d+)"[^>]*>(.*?)<\/div>/g)]
    .map(m => ({ dataset: { row: m[1] }, textContent: desescapar(m[2]),
      classList: { contains: c => c === 'despachante-sufijo-nota' } }));
  leido = { html, celdas, notas };
  return leido;
}
global.document = {
  activeElement: null,
  getElementById: elemento,
  querySelectorAll(sel) {
    if (sel === '.despachante-sufijo') return leerFilas().celdas;
    if (sel === '.despachante-sufijo-nota') return leerFilas().notas;
    return [];
  },
};
"""

_ARNES = r"""
const CDI = window.CDI; CDI.state = { operacion: { despachante: {} }, items: [] };
const D = CDI.despachante;
let pedidos = 0, modo = 'ok', frenar = false, colgados = [], frenarOtras = false, otras = [];
const unidades = { 'PLASTICO': '01' };
function soltar() { const c = colgados; colgados = []; c.forEach(r => r()); }
function soltarOtras() { const c = otras; otras = []; c.forEach(r => r()); }
CDI.api = async (ruta, op) => {
  if (ruta !== '/api/sufijos/propuesta') {
    if (frenarOtras) await new Promise(r => otras.push(r));
    return { ok: true, json: async () => ({ operaciones: [] }) };
  }
  pedidos += 1;
  const b = JSON.parse(op.body);
  if (frenar) await new Promise(r => colgados.push(r));
  await new Promise(r => setImmediate(r));
  if (modo === 'tira') throw new Error('sin red');
  if (modo === 'falla') return { ok: false, json: async () => ({ detail: 'caído' }) };
  return { ok: true, json: async () => ({ fuente: 'arancel de ARCA del 07/10/2026', items:
    b.items.map(x => x.pieza === 'PLASTICO' ? { posicion: x.pieza, en_la_tabla: true,
      unidad_estadistica: unidades['PLASTICO'], faltan: [],
      sufijo: (x.marca ? 'AA(' + x.marca + ')-' : '') + (x.codigo_parte ? 'AI(' + x.codigo_parte + ')-' : '') }
      : { posicion: x.pieza, en_la_tabla: false, sufijo: '', faltan: [] }) }) };
};
const tick = () => new Promise(r => setImmediate(r));
function operacion(texto) {
  CDI.state.operacion.sbt_sufijo_valor = texto;
  const campo = document.getElementById('sbtSufijoValor');
  campo.value = texto;
  (campo.oyentes.input || []).forEach(f => f({ target: campo }));
}
const celda = i => leerFilas().celdas.find(c => c.dataset.row === String(i));
const nota = i => { const n = leerFilas().notas.find(c => c.dataset.row === String(i)); return n ? n.textContent : null; };
function escribir(i, texto) {
  const c = celda(i);
  c.value = texto;
  (document.getElementById('despachanteWrap').oyentes.input || []).forEach(f => f({ target: c }));
}
// Lo que iría al pedido de cada producto si se genera ahora.
const viaja = () => CDI.state.items.map((it, i) => [D.sufijoDe(it, i), D.unidadesDe(it, i).unidad_estadistica]);
"""


def _pantalla(pasos):
    """Corre despachante.js en node con la página mínima; `pasos` es JS que
    deja lo que se mide en `salida`."""
    escape = APP.read_text(encoding="utf-8").split("function escapeHtml(s) {", 1)[1].split("\n    }", 1)[0]
    codigo = (
        _PAGINA
        + (V2 / "despachante.js").read_text(encoding="utf-8")
        + "\nwindow.CDI.escapeHtml = function (s) {" + escape + "\n};"
        + _ARNES.replace("'PLASTICO'", json.dumps(PLASTICO))
        + "\nconst salida = {};\n(async () => {\n" + pasos + "\nconsole.log(JSON.stringify(salida)); })()"
        + ".catch(e => { console.error(e); process.exit(1); });"
    )
    r = subprocess.run(["node", "-e", codigo], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _producto(marca, codigo="", pieza=PLASTICO, **mas):
    return dict({"pieza": pieza, "marca": marca, "codigo_parte": codigo}, **mas)


def _items(*productos):
    return f"CDI.state.items = {json.dumps(list(productos))};"


def test_la_estadistica_de_la_tabla_va_al_pedido_si_nadie_eligio_otra():
    lona = {"pieza": PLASTICO, "unidad": "03"}
    casos = [
        # producto, la de la operación, la unidad de la tabla
        (lona, {}, "01"),                                   # la tabla dice kilos: va 01
        (lona, {}, "03"),                                   # la tabla dice la declarada: nada
        ({"pieza": FUERA, "unidad": "03"}, {}, "01"),       # fuera de la tabla: nada
        (lona, {"unidad_estadistica": "DCL"}, "01"),        # la persona eligió la de la factura
        (dict(lona, unidad_estadistica="DCL"), {}, "01"),   # en el producto, también
        ({"pieza": FUERA, "unidad": "03"}, {"unidad_estadistica": "01"}, "01"),
    ]
    pasos = "salida.est = [];" + "".join(
        f"unidades[{json.dumps(PLASTICO)}] = {json.dumps(u)}; CDI.state.operacion.despachante = {json.dumps(op)};"
        f"{_items(dict(it, marca=f'M{n}'))} await D.render(); salida.est.push(viaja()[0][1]);\n"
        for n, (it, op, u) in enumerate(casos))
    assert _pantalla(pasos)["est"] == ["01", None, None, None, None, "01"]


def test_con_sub_items_la_estadistica_de_la_tabla_no_va_sola():
    # Con sub-ítems, kilos sólo cierra si la de la factura también es en kilos
    # (el generador lo frena): la pantalla no la pone sola.
    partido = {"pieza": PLASTICO, "unidad": "03", "subitems": [{"cantidad": 1}, {"cantidad": 2}]}
    salida = _pantalla(
        f"{_items(partido)} await D.render(); salida.sola = viaja()[0][1];"
        "CDI.state.operacion.despachante = { unidad_estadistica: '01' }; salida.elegida = viaja()[0][1];")
    assert salida == {"sola": None, "elegida": "01"}


def test_la_propuesta_se_suma_a_lo_que_trae_el_de_la_operacion():
    # El de la operación gana (H5): la propuesta sólo agrega los códigos que
    # faltan, y los demás de la operación (PC01, CA00) quedan.
    casos = {
        "op_con_otros": ("AA(OPMARCA)-PC01-", "AA(OPMARCA)-PC01-AI(X1)-"),
        "op_en_minusculas": ("aa(op)-ca00", "aa(op)-ca00-AI(X1)-"),
        "op_vacia": ("", "AA(ACME)-AI(X1)-"),
        "op_que_no_se_separa": ("AA(SIN CERRAR", ""),   # lo dice el servidor con el de la operación
    }
    pasos = "".join(
        f"{_items(_producto('ACME', 'X1'))} operacion({json.dumps(op)});"
        f"await D.render(); salida[{json.dumps(nombre)}] = [viaja()[0][0], celda(0).value];\n"
        for nombre, (op, _) in casos.items())
    assert _pantalla(pasos) == {nombre: [esperado, esperado] for nombre, (_, esperado) in casos.items()}


def test_lo_que_escribe_la_persona_va_tal_cual():
    salida = _pantalla(
        "operacion('AA(OP)-CA00-');"
        + _items(_producto('ACME', 'X1', sufijo='AA(MANO)-'), _producto('ACME', pieza=FUERA))
        + "await D.render(); salida.viaja = viaja().map(v => v[0]);")
    assert salida == {"viaja": ["AA(MANO)-", ""]}


def test_la_propuesta_de_una_fila_no_pasa_al_producto_que_queda_en_su_lugar():
    # Se borra el primero: hasta que se vuelve a pintar, el que queda en la
    # fila 0 no lleva la marca del borrado; si cambia otra vez mientras se
    # consulta, vale la última.
    salida = _pantalla(
        _items(_producto('SAMSUNG', 'S1'), _producto('LG', 'L1'))
        + "await D.render(); salida.antes = viaja()[1][0];"
        "CDI.state.items.splice(0, 1); salida.en_el_medio = viaja()[0];"
        "const viejo = D.render(); CDI.state.items[0].marca = 'LG2';"
        "await D.render(); await viejo; salida.despues = [viaja()[0][0], celda(0).value];"
        "salida.pedidos = pedidos;")
    assert salida == {"antes": "AA(LG)-AI(L1)-", "en_el_medio": ["", None],
                      "despues": ["AA(LG2)-AI(L1)-", "AA(LG2)-AI(L1)-"], "pedidos": 3}


def test_volver_a_pintar_no_repite_el_pedido_en_curso():
    salida = _pantalla(
        _items(_producto('ACME'))
        + "await Promise.all([D.render(), D.render(), D.render()]); await D.render();"
        "salida.pedidos = pedidos;")
    assert salida == {"pedidos": 1}


def test_sin_la_tabla_la_nota_no_dice_que_la_posicion_no_esta():
    salida = _pantalla(
        "CDI.api = async () => ({ ok: true, json: async () => ({ fuente: 'arancel de ARCA', sin_tabla: true,"
        " items: [{ posicion: 'X', en_la_tabla: false, sufijo: '', faltan: [] }] }) });"
        + _items(_producto('ACME'))
        + "await D.render(); salida.nota = nota(0);")
    assert salida == {"nota": "Falta la tabla del arancel de ARCA: cargalo a mano."}


# --------------------------------- la vuelta: lo que viaja es lo que se ve


NO_CONTESTO = "El arancel de ARCA no contestó: no se propone sufijo ni unidad; va el de la operación."
CONSULTANDO = "Consultando el arancel de ARCA…"
TOPE = "Con más de 500 productos no se consulta el arancel de ARCA: cargá los sufijos a mano."
D23 = ("El sufijo de la operación está vacío: cada producto sale sólo con lo que pide el "
       "arancel de ARCA")


@pytest.mark.parametrize("modo", ["falla", "tira"])
def test_si_el_arancel_no_contesta_no_viaja_nada_y_la_celda_lo_dice(modo):
    # H1: sin propuesta en pantalla no se agrega nada al generar (ni sufijo
    # ni kilos), y la celda y los avisos lo dicen. Al volver, se reintenta.
    salida = _pantalla(
        f"modo = {json.dumps(modo)}; operacion('PC02-');"
        + _items(_producto('BETA', 'K7'), _producto('GAMA', pieza=FUERA))
        + "await D.render(); salida.caido = [viaja(), celda(0).value, nota(0), nota(1), D.avisos()];"
        "const antes = pedidos; viaja(); D.todosConPropio(); salida.al_generar_no_pide = pedidos === antes;"
        "modo = 'ok'; await D.render(); salida.vuelve = [viaja(), celda(0).value, pedidos];")
    assert salida["caido"] == [[["", None], ["", None]], "", NO_CONTESTO, NO_CONTESTO, [NO_CONTESTO]]
    assert salida["al_generar_no_pide"] is True
    assert salida["vuelve"] == [[["PC02-AA(BETA)-AI(K7)-", "01"], ["", None]], "PC02-AA(BETA)-AI(K7)-", 2]


def test_con_mas_de_500_productos_no_se_consulta_y_se_dice():
    salida = _pantalla(
        f"CDI.state.items = Array.from({{ length: 501 }}, (_, i) => ({json.dumps(_producto('DELTA'))}));"
        "await D.render(); salida.r = [pedidos, viaja().every(v => v[0] === '' && v[1] === null),"
        " nota(0), nota(500), D.avisos()];")
    assert salida["r"] == [0, True, TOPE, TOPE, [TOPE]]


def test_mientras_consulta_no_viaja_nada_de_la_propuesta():
    salida = _pantalla(
        "frenar = true; operacion('PC02-');" + _items(_producto('BETA', 'K7'))
        + "const p = D.render(); await tick();"
        "salida.consultando = [viaja(), celda(0).value, nota(0), D.avisos()];"
        "soltar(); await p; salida.llego = [viaja(), celda(0).value, D.avisos()];")
    assert salida["consultando"] == [[["", None]], "", CONSULTANDO, [CONSULTANDO]]
    assert salida["llego"] == [[["PC02-AA(BETA)-AI(K7)-", "01"]], "PC02-AA(BETA)-AI(K7)-", []]


def test_mientras_consulta_otra_fila_la_que_no_cambio_tampoco_lleva_la_propuesta():
    # Cambia el segundo producto: mientras se consulta, la celda del primero
    # se pinta sin propuesta y dice que consulta; lo que viaja es eso.
    salida = _pantalla(
        "operacion('PC04-');" + _items(_producto('KAPA', 'M1'), _producto('LAMBDA', 'M2'))
        + "await D.render(); salida.antes = viaja()[0][0];"
        "frenar = true; CDI.state.items[1].codigo_parte = 'M3'; const p = D.render(); await tick();"
        "salida.consultando = [viaja()[0], celda(0).value, nota(0)];"
        "soltar(); await p; salida.llego = viaja().map(v => v[0]);")
    assert salida["antes"] == "PC04-AA(KAPA)-AI(M1)-"
    assert salida["consultando"] == [["", None], "", CONSULTANDO]
    assert salida["llego"] == ["PC04-AA(KAPA)-AI(M1)-", "PC04-AA(LAMBDA)-AI(M3)-"]


def test_la_propuesta_que_llego_y_no_se_pinto_no_viaja():
    # La propuesta del cliente todavía no llegó (la pantalla no se repinta
    # sola). Se pintó la de M1; el producto pasa a M2 y vuelve, y con M2 de
    # nuevo llega la de un pedido viejo. Hasta pintarla no viaja: ni la de
    # M1 (ya no es ese producto) ni la de M2.
    salida = _pantalla(
        "frenarOtras = true; operacion('PC05-');" + _items(_producto('SIGMA', 'M1'))
        + "D.render(); for (let k = 0; k < 5; k++) await tick();"
        "D.render(); await tick(); salida.pintado = viaja()[0];"
        "frenar = true; CDI.state.items[0].codigo_parte = 'M2'; D.render(); await tick();"
        "CDI.state.items[0].codigo_parte = 'M1'; D.render(); await tick();"
        "CDI.state.items[0].codigo_parte = 'M2'; soltar(); for (let k = 0; k < 5; k++) await tick();"
        "salida.sin_pintar = [pedidos, viaja()[0]];"
        "frenarOtras = false; soltarOtras(); await D.render(); salida.repintado = [viaja()[0], celda(0).value];")
    assert salida["pintado"] == ["PC05-AA(SIGMA)-AI(M1)-", "01"]
    assert salida["sin_pintar"] == [2, ["", None]]
    assert salida["repintado"] == [["PC05-AA(SIGMA)-AI(M2)-", "01"], "PC05-AA(SIGMA)-AI(M2)-"]


def test_lo_que_viaja_es_lo_que_muestra_la_celda():
    # Cada fila: el sufijo es el de la celda, y los kilos van sólo si la
    # nota los dice. Un producto que cambió y no se volvió a pintar no lleva
    # nada de la propuesta.
    salida = _pantalla(
        "operacion('CA03-');"
        + _items(_producto('OMEGA', 'Z2'), _producto('', ''), _producto('ETA', pieza=FUERA),
                 _producto('RHO', 'P4', unidad_estadistica='DCL'))
        + "await D.render();"
        "salida.filas = CDI.state.items.map((it, i) => [viaja()[i][0] === celda(i).value,"
        " viaja()[i][1] === '01', /unidad estadística 01/.test(nota(i))]);"
        "CDI.state.items[0].codigo_parte = 'Z3'; salida.cambiado = viaja()[0];")
    assert salida["filas"] == [[True, True, True], [True, True, True], [True, False, False], [True, False, True]]
    assert salida["cambiado"] == ["", None]


def test_si_cambia_el_de_la_operacion_la_celda_escrita_avisa():
    # H2: lo escrito va tal cual, pero si después cambia el de la operación
    # la fila lo avisa (y los avisos del botón); tocarla de nuevo lo acepta.
    aviso = "Lo escribiste con otro sufijo de la operación: revisalo, va tal cual."
    salida = _pantalla(
        "operacion('PC03-');" + _items(_producto('ZETA', 'Q9'), _producto('IOTA', 'Q8'))
        + "await D.render(); escribir(0, 'PC03-AA(ZETA)-');"
        "salida.igual = [nota(0), D.avisos()];"
        "operacion('PC07-');"
        "salida.cambio = [viaja().map(v => v[0]), celda(1).value, nota(0), D.avisos()];"
        "escribir(0, 'PC07-AA(ZETA)-'); salida.tocada = [nota(0), D.avisos()];"
        "operacion('PC09-'); escribir(0, ''); salida.vacia = [nota(0), viaja()[0][0]];"
        "await D.render(); operacion('PC11-'); salida.repintada = nota(0);")
    assert salida["igual"] == ["Según el arancel de ARCA del 07/10/2026: unidad estadística 01.", []]
    assert salida["cambio"][0] == ["PC03-AA(ZETA)-", "PC07-AA(IOTA)-AI(Q8)-"]
    assert salida["cambio"][1] == "PC07-AA(IOTA)-AI(Q8)-"
    assert aviso in salida["cambio"][2]
    assert salida["cambio"][3] == ["Ítem 1: " + aviso]
    assert aviso not in salida["tocada"][0] and salida["tocada"][1] == []
    assert aviso not in salida["vacia"][0] and salida["vacia"][1] == ""
    assert aviso not in salida["repintada"]


def test_en_un_grupo_no_viaja_un_sufijo_escrito_antes_de_agrupar():
    # H3: el grupo sale con el de la operación; lo escrito antes no viaja y
    # la celda no lo muestra.
    salida = _pantalla(
        "operacion('PC05-');"
        + _items(_producto('KAPPA', 'W1', sufijo='AA(KAPPA)-AI(W1)-', grupo_id='g7'),
                 _producto('KAPPA', 'W2', grupo_id='g7'))
        + "await D.render(); salida.viaja = viaja();"
        "salida.celdas = CDI.state.items.map((it, i) => D.celdaSufijo(it, i));")
    assert salida["viaja"] == [["", "01"], ["", "01"]]
    for html in salida["celdas"]:
        assert "<input" not in html and "W1" not in html
        assert "Va el de la operación para todo el grupo." in html
        assert "unidad estadística 01" in html


def test_con_sub_items_no_viaja_el_sufijo_del_producto():
    # H4: el producto pasó a sub-ítems; su sufijo de antes ya no se ve y no
    # viaja (cada sub-ítem lleva el suyo).
    salida = _pantalla(
        _items(_producto('SIGMA', 'V3', sufijo='AA(SIGMA)-AI(V3)-',
                         subitems=[{"cantidad": 1, "sufijo": "AA(SIGMA)-AI(V3 A)-"}]))
        + "await D.render(); salida.viaja = viaja()[0][0]; salida.celda = D.celdaSufijo(CDI.state.items[0], 0);")
    assert salida == {"viaja": "", "celda": '<span class="caption">Va en cada sub-ítem.</span>'}


def test_el_de_la_operacion_gana_y_lo_distinto_se_avisa_en_la_fila():
    # H5: la propuesta sólo agrega lo que falta; un AA distinto no lo pisa y
    # se avisa. Mayúsculas y espacios no son una diferencia.
    salida = _pantalla(
        _items(_producto('ZETA', 'Q9'))
        + "operacion('AA(PROPIA)-PC03-'); await D.render(); salida.distinto = [viaja()[0][0], nota(0)];"
        + _items(_producto('ZETA ROJA', 'Q9'))
        + "operacion('aa(zeta  roja)-pc03-'); await D.render(); salida.igual = [viaja()[0][0], nota(0)];"
        + _items(_producto('ZETA', 'Q9'))
        + "operacion('PC03-AI(R2)-'); await D.render(); salida.ai = [viaja()[0][0], nota(0)];")
    assert salida["distinto"][0] == "AA(PROPIA)-PC03-AI(Q9)-"
    assert "El arancel propone AA(ZETA); queda el de la operación: AA(PROPIA)." in salida["distinto"][1]
    assert salida["igual"][0] == "aa(zeta  roja)-pc03-AI(Q9)-"
    assert "El arancel propone" not in salida["igual"][1]
    assert salida["ai"][0] == "PC03-AI(R2)-AA(ZETA)-"
    assert "El arancel propone AI(Q9); queda el de la operación: AI(R2)." in salida["ai"][1]


def test_con_el_de_la_operacion_vacio_y_todos_con_el_propio_se_avisa():
    # D23 (c): no frena; avisa junto al botón.
    salida = _pantalla(
        _items(_producto('LAMBDA', 'N5'),
               _producto('MU', pieza=FUERA, subitems=[{"cantidad": 1, "sufijo": "AA(MU)-"}]))
        + "operacion(''); await D.render(); salida.vacio = [D.todosConPropio(), D.avisos()];"
        "operacion('PC04-'); salida.con_op = [D.todosConPropio(), D.avisos()];"
        "operacion(''); CDI.state.items.push({ pieza: " + json.dumps(FUERA) + ", marca: 'NU' });"
        "salida.uno_sin = [D.todosConPropio(), D.avisos()];")
    assert salida["vacio"] == [True, [D23]]
    assert salida["con_op"] == [True, []]
    assert salida["uno_sin"] == [False, []]


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


def test_un_codigo_con_el_valor_vacio_no_se_genera():
    # Antes salía con el aviso de un código que falta; desde SUFIJOS-2
    # (respuesta del despachante del 28/10) ninguno puede quedar vacío.
    with pytest.raises(ValueError, match=r"del ítem 1: «AA\( \)» está vacío"):
        _gen([dict(LONA, pieza=PLASTICO, sufijo="AA( )-AI(620G)-")])


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
    salida = _pantalla(
        "CDI.api = async () => ({ ok: true, json: async () => ({ fuente: 'arancel de ARCA del 07/10/2026',"
        " items: [{ posicion: 'X', en_la_tabla: false, letra_de_control: 'F', sufijo: '', faltan: [] }] }) });"
        + _items(_producto('ACME'))
        + "await D.render(); salida.nota = nota(0);")
    assert salida == {"nota": "En el arancel de ARCA del 07/10/2026 la letra de control de esta "
                              "posición es F: revisá la posición."}


# ------------------------------------------- bordes de la autorrevisión


def test_si_junto_con_el_de_la_operacion_no_entra_no_se_pierde_lo_de_la_operacion():
    # Lo que trae la operación (CA00, PC) no se cae para que entre la
    # propuesta: el producto va con el de la operación y el servidor avisa.
    op = "CA00-PC(" + "X" * 100 + ")-"
    salida = _pantalla(
        f"operacion({json.dumps(op)});" + _items(_producto('ACME', 'X1'))
        + "await D.render(); salida.sufijo = [viaja()[0][0], celda(0).value];")
    assert salida == {"sufijo": ["", ""]}


def test_en_un_grupo_la_celda_no_deja_escribir_un_sufijo_por_producto():
    # Un grupo sale con un solo sufijo, el de la operación: una celda por
    # producto dejaría escribir sufijos distintos y el TXT no se genera.
    salida = _pantalla(
        _items(_producto('ACME', 'X1', grupo_id=1), _producto('ACME', 'X2', grupo_id=1, sufijo='AA(G)-'))
        + "await D.render(); salida.celdas = CDI.state.items.map((it, i) => D.celdaSufijo(it, i));")
    for html in salida["celdas"]:
        assert "<input" not in html and "AA(G)" not in html
        assert "Va el de la operación para todo el grupo." in html


def test_una_ncm_de_ocho_no_se_dice_fuera_del_arancel():
    avisos = _avisos([dict(LONA, pieza="3920.10.10", sufijo=PROPIO)])
    assert ("Posición 3920.10.10 (ítem 1): no es una posición SIM completa (11 dígitos y la letra "
            "de control). Los sufijos de valor y la unidad estadística no se completan ni se "
            "controlan: cargalos a mano con el despachante.") in avisos
    assert not any("no está en el" in a for a in avisos)
    salida = _pantalla(
        "CDI.api = async () => ({ ok: true, json: async () => ({ fuente: 'arancel de ARCA del 07/10/2026',"
        " items: [{ posicion: '3920.10.10', en_la_tabla: false, sufijo: '', faltan: [] }] }) });"
        + _items(_producto('ACME', pieza='3920.10.10'))
        + "await D.render(); salida.nota = nota(0);")
    assert salida == {"nota": "No es una posición SIM completa (11 dígitos y la letra de control): "
                              "cargalo a mano."}


def test_un_grupo_que_no_se_puede_comparar_no_rompe_los_avisos():
    # Un pedido armado a mano con grupo_id lista: lo dice el generador, los
    # avisos no se caen (antes de SUFIJOS-1 tampoco se caían).
    avisos = _avisos([dict(LONA, pieza=PLASTICO, grupo_id=[1], sufijo="AA(DEMO)-")])
    assert isinstance(avisos, list)
