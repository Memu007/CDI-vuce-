"""VALOR-1: ajustes a incluir y a deducir, FOB casillero y seguro sugerido.

Los ajustes los carga la persona (el sistema no decide qué se descuenta) y
sólo sirven para las cuentas: el TXT lleva el FOB de la factura hasta saber
en qué campo van (D12). El seguro sugerido es el 1 % de (FOB de la factura +
flete) (D13). Datos inventados, con la forma de la factura del 24/10.
"""
import json
import re
import subprocess
from decimal import Decimal
from pathlib import Path

import pytest

from proyecto_maria.core import maria_generator as mg
from tests.test_maria7_rechazos_24_10 import LONA, _pedido, _registrar_con_cuit, _valor

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "proyecto_maria" / "static" / "v2" / "screens"


def _cuentas(items, **kw):
    # Por el módulo: contra la base, cada caso falla por su cuenta.
    return mg.cuentas_del_valor(items, **kw)


# --------------------------------------------------------- las cuentas


def test_fob_casillero_es_el_de_la_factura_mas_lo_que_se_incluye_menos_lo_que_se_deduce():
    items = [{"cantidad": 750, "valor_unitario": 1.85}]  # 1.387,50
    v = _cuentas(items, flete=100, ajustes_incluir=12.5, ajustes_deducir=50)
    assert v["fob_factura"] == 1387.50
    assert v["ajustes_incluir"] == 12.50 and v["ajustes_deducir"] == 50.00
    assert v["fob_casillero"] == 1350.00
    # 1 % de (1.387,50 + 100) = 14,875: va sobre el FOB de la factura (D13)
    assert v["seguro_sugerido"] == 14.88


def test_sin_ajustes_el_casillero_es_el_fob_de_la_factura():
    v = _cuentas([{"cantidad": 750, "valor_unitario": 1.85}], flete=7925, seguro=12.4)
    assert v["fob_casillero"] == v["fob_factura"] == 1387.50
    assert v["flete"] == 7925.00 and v["seguro"] == 12.40
    assert v["seguro_sugerido"] == 93.13  # 1 % de 9.312,50 = 93,125 → 93,13


def test_el_seguro_sugerido_redondea_la_mitad_hacia_arriba():
    # 1 % de 1.000,50 = 10,005: al par daría 10,00.
    v = _cuentas([{"cantidad": 1, "valor_unitario": 1000.5}])
    assert v["seguro_sugerido"] == 10.01


def test_los_ajustes_van_al_centavo_con_la_mitad_hacia_arriba():
    v = _cuentas([{"cantidad": 1, "valor_unitario": 1000}], ajustes_deducir=50.005, ajustes_incluir=0.125)
    assert v["ajustes_deducir"] == 50.01 and v["ajustes_incluir"] == 0.13
    assert v["fob_casillero"] == 950.12


def test_el_seguro_va_sobre_el_fob_de_la_factura():
    """D13: el 1 % va sobre el FOB antes de los ajustes."""
    v = _cuentas([{"cantidad": 1, "valor_unitario": 1000}], flete=100, ajustes_deducir=200, ajustes_incluir=50)
    assert v["seguro_sugerido"] == 11.00 and v["base_seguro"] == "FOB de la factura"
    assert v["fob_casillero"] == 850.00


def test_la_base_del_seguro_se_cambia_en_un_solo_lugar(monkeypatch):
    """Si hubiera que volver al FOB casillero, alcanza con cambiar
    BASE_SEGURO_SUGERIDO."""
    items = [{"cantidad": 1, "valor_unitario": 1000}]
    monkeypatch.setattr(mg, "BASE_SEGURO_SUGERIDO", "fob_casillero")
    v = _cuentas(items, flete=100, ajustes_deducir=200)
    assert v["seguro_sugerido"] == 9.00 and v["base_seguro"] == "FOB casillero"
    assert v["fob_casillero"] == 800.00


def test_deducir_mas_que_el_fob_no_es_un_casillero():
    with pytest.raises(ValueError, match=r"Los ajustes a deducir \(2\.000,00\) superan el FOB de la factura más "
                                         r"los ajustes a incluir \(1\.010,00\)"):
        _cuentas([{"cantidad": 1, "valor_unitario": 1000}], ajustes_incluir=10, ajustes_deducir=2000)


def test_deducir_justo_el_fob_da_casillero_cero():
    v = _cuentas([{"cantidad": 1, "valor_unitario": 1000}], ajustes_deducir=1000)
    assert v["fob_casillero"] == 0.0


@pytest.mark.parametrize("campo,nombre", [("ajustes_incluir", "Ajustes a incluir"),
                                          ("ajustes_deducir", "Ajustes a deducir")])
@pytest.mark.parametrize("malo", [-1, float("nan"), float("inf"), "abc", 1e13])
def test_un_ajuste_invalido_dice_cual(campo, nombre, malo):
    with pytest.raises(ValueError, match=nombre):
        _cuentas([{"cantidad": 1, "valor_unitario": 10}], **{campo: malo})


# --------------------------- el FOB de la factura es el MDDTFOB del TXT


DOS_LONAS = [dict(LONA), {**LONA, "cantidad": 3, "valor_unitario": 3.335, "peso_kg": 2.0}]


def _pedido_con(items, **kw):
    p = _pedido()
    p["items"] = [{
        "pieza": it["pieza"], "descripcion": it["descripcion"], "origen": "CN",
        "cantidad": it["cantidad"], "valor_unitario": it["valor_unitario"],
        "peso_unitario": it["peso_kg"] / it["cantidad"], "unidad": it["unidad"],
        "grupo_id": it.get("grupo_id"),
    } for it in items]
    p.update(kw)
    return p


@pytest.mark.parametrize("items", [
    pytest.param([dict(LONA)], id="una_linea"),
    # MARIA-8: la misma posición va en un ítem con sub-ítems.
    pytest.param(DOS_LONAS, id="misma_posicion"),
    # Un grupo suma y redondea una vez: 10,005 + 10,005 = 20,01 (y no 20,02).
    pytest.param([{**LONA, "cantidad": 3, "valor_unitario": 3.335, "peso_kg": 1.0, "grupo_id": 1,
                   "descripcion": "Lona de PVC A"},
                  {**LONA, "cantidad": 3, "valor_unitario": 3.335, "peso_kg": 1.0, "grupo_id": 1,
                   "descripcion": "Lona de PVC B"}], id="grupo"),
    pytest.param([{**LONA, "cantidad": 3, "valor_unitario": 3.335, "peso_kg": 1.0},
                  {**LONA, "pieza": "39219090000X", "cantidad": 3, "valor_unitario": 3.335,
                   "peso_kg": 1.0}], id="cada_una_al_centavo"),
])
def test_el_fob_de_la_factura_es_el_mddtfob_del_txt(client, items, request):
    _registrar_con_cuit(client, "valor1_" + request.node.callspec.id)
    pedido = _pedido_con(items, ajustes_deducir=1)
    r = client.post("/generate_maria/avisos", json=pedido)
    assert r.status_code == 200, r.text
    fob = r.json()["valor"]["fob_factura"]
    g = client.post("/generate_maria", json=pedido)
    assert g.status_code == 200, g.text
    assert _valor(g.json()["content"], "MDDTFOB") == [f"{fob:.2f}"]


def test_el_txt_es_el_mismo_con_y_sin_ajustes(client):
    _registrar_con_cuit(client, "valor1_txt")
    sin = client.post("/generate_maria", json=_pedido())
    con = client.post("/generate_maria", json={**_pedido(), "ajustes_incluir": 300, "ajustes_deducir": 120.5})
    assert sin.status_code == con.status_code == 200, (sin.text, con.text)
    assert sin.json()["content"] == con.json()["content"]
    assert _valor(con.json()["content"], "MDDTFOB") == ["1387.50"]


def test_un_ajuste_que_no_cierra_no_frena_la_generacion(client):
    """Los ajustes no van al TXT: un casillero negativo se ve en la tarjeta,
    pero el TXT sale igual."""
    _registrar_con_cuit(client, "valor1_no_frena")
    r = client.post("/generate_maria", json={**_pedido(), "ajustes_deducir": 999999})
    assert r.status_code == 200, r.text


# ------------------------------------------------ los avisos de antes


def test_los_avisos_traen_las_cuentas_y_dicen_que_el_casillero_va_al_txt_mas_adelante(client):
    _registrar_con_cuit(client, "valor1_avisos")
    r = client.post("/generate_maria/avisos", json={**_pedido(), "ajustes_deducir": 87.5})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["valor"] == {
        "fob_factura": 1387.5, "ajustes_incluir": 0.0, "ajustes_deducir": 87.5,
        "fob_casillero": 1300.0, "flete": 7925.0, "seguro": 12.4, "seguro_sugerido": 93.13,
        "base_seguro": "FOB de la factura", "seguro_en_el_precio": False,
    }
    # Que no parezca que ya se descuenta (respuesta de la PM a D12).
    assert ("El TXT todavía lleva el FOB de la factura (DOL 1.387,50); el FOB casillero con los ajustes "
            "(DOL 1.300,00) va al TXT en una próxima versión.") in data["avisos"]


def test_sin_ajustes_no_hay_aviso_del_casillero(client):
    _registrar_con_cuit(client, "valor1_sin_aviso")
    r = client.post("/generate_maria/avisos", json=_pedido())
    assert r.status_code == 200, r.text
    assert r.json()["valor"]["fob_casillero"] == 1387.5
    assert not any("FOB casillero" in a for a in r.json()["avisos"])


def test_un_ajuste_invalido_va_en_la_tarjeta_y_no_tapa_los_otros_avisos(client):
    _registrar_con_cuit(client, "valor1_invalido")
    sin_ajustes = client.post("/generate_maria/avisos", json=_pedido()).json()["avisos"]
    r = client.post("/generate_maria/avisos", json={**_pedido(), "ajustes_incluir": -5})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["valor"] == {"error": "Ajustes a incluir: «-5» no es un importe válido "
                                      "(entre 0 y 1.000.000.000.000)."}
    # Los demás avisos siguen todos: el ajuste inválido no los tapa.
    assert sin_ajustes and data["avisos"] == sin_ajustes


# VALOR-1b: por API, un ajuste que no es número no da 422.
@pytest.mark.parametrize("ajuste, error", [
    ("abc", "Ajustes a deducir: «abc» no es un importe."),
    (True, "Ajustes a deducir: no es un importe."),
    ([1], "Ajustes a deducir: no es un importe."),
    ({"x": 1}, "Ajustes a deducir: no es un importe."),
], ids=["texto", "verdadero", "lista", "objeto"])
def test_un_ajuste_que_no_es_numero_va_en_la_tarjeta_con_todos_los_avisos(client, request, ajuste, error):
    _registrar_con_cuit(client, "valor1b_aj_" + request.node.callspec.id)
    sin_ajustes = client.post("/generate_maria/avisos", json=_pedido()).json()["avisos"]
    r = client.post("/generate_maria/avisos", json={**_pedido(), "ajustes_deducir": ajuste})
    assert r.status_code == 200, r.text
    assert r.json()["valor"] == {"error": error}
    assert sin_ajustes and r.json()["avisos"] == sin_ajustes


def test_un_ajuste_que_no_es_numero_no_frena_el_txt(client):
    _registrar_con_cuit(client, "valor1b_aj_txt")
    sin = client.post("/generate_maria", json=_pedido())
    con = client.post("/generate_maria", json={**_pedido(), "ajustes_incluir": "abc", "ajustes_deducir": True})
    assert sin.status_code == con.status_code == 200, con.text
    # Cada generación es otra operación, con su id y su archivo: se compara el TXT.
    assert [con.json()[k] for k in ("content", "warnings")] == [sin.json()[k] for k in ("content", "warnings")]


def test_un_ajuste_escrito_como_texto_con_numero_se_toma():
    v = _cuentas([{"cantidad": 1, "valor_unitario": 1000}], ajustes_deducir="87.5")
    assert v["fob_casillero"] == 912.50


def test_un_error_de_tipo_que_se_escape_no_muestra_el_texto_de_python(client, monkeypatch):
    import proyecto_maria.main as main

    def cuentas(*a, **k):
        raise TypeError("float() argument must be a string or a real number, not 'list'")
    monkeypatch.setattr(main, "cuentas_del_valor", cuentas)
    _registrar_con_cuit(client, "valor1b_tipo")
    r = client.post("/generate_maria/avisos", json=_pedido())
    assert r.status_code == 200, r.text
    assert r.json()["valor"] == {"error": "Hay un dato que no es un número: no se pueden hacer las cuentas."}


@pytest.mark.parametrize("cambio, error", [
    ({"cantidad": "abc"}, "Renglón 2: la cantidad «abc» no es un número; no se pueden hacer las cuentas."),
    ({"valor_unitario": "x"}, "Renglón 2: el valor unitario «x» no es un número; no se pueden hacer las cuentas."),
    ({"valor_total": "z"}, "Renglón 2: el valor total «z» no es un número; no se pueden hacer las cuentas."),
    ({"cantidad": [1]}, "Renglón 2: la cantidad no es un número; no se pueden hacer las cuentas."),
    # Verdadero o falso no es un número (se tomaría como 1 o 0), igual que en los ajustes.
    ({"valor_total": True}, "Renglón 2: el valor total no es un número; no se pueden hacer las cuentas."),
    ({"cantidad": False}, "Renglón 2: la cantidad no es un número; no se pueden hacer las cuentas."),
], ids=["cantidad", "unitario", "total", "lista", "verdadero", "falso"])
def test_un_renglon_con_texto_en_vez_de_numero_se_nombra_sin_texto_de_python(client, request, cambio, error):
    _registrar_con_cuit(client, "valor1b_ren_" + request.node.callspec.id)
    r = client.post("/generate_maria/avisos", json={**_pedido(), "items": [LONA, {**LONA, **cambio}]})
    assert r.status_code == 200, r.text
    assert r.json()["valor"] == {"error": error}


@pytest.mark.parametrize("producto, error", [
    ("basura", "Hay un producto mal formado (renglón 2): no se pueden hacer las cuentas."),
    ({**LONA, "cantidad": 10 ** 400}, "Hay un importe o una cantidad fuera de rango: no se pueden hacer las cuentas."),
], ids=["texto", "enorme"])
def test_un_producto_mal_formado_va_en_la_tarjeta_y_no_tira_los_avisos(client, request, producto, error):
    _registrar_con_cuit(client, "valor1_mal_" + request.node.callspec.id)
    r = client.post("/generate_maria/avisos", json={**_pedido(), "items": [LONA, producto]})
    assert r.status_code == 200, r.text
    assert r.json()["valor"] == {"error": error}


def test_un_casillero_negativo_va_en_la_tarjeta(client):
    _registrar_con_cuit(client, "valor1_negativo")
    r = client.post("/generate_maria/avisos", json={**_pedido(), "ajustes_deducir": 2000})
    assert r.status_code == 200, r.text
    assert r.json()["valor"]["error"].startswith("Los ajustes a deducir (2.000,00) superan")


# ------------------------------------------------------ la pantalla


def _funciones(archivo, nombres):
    fuente = (V2 / archivo).read_text(encoding="utf-8")
    partes = []
    for nombre in nombres:
        m = re.search(rf"\n(\s*)(?:async )?function {nombre}\([^)]*\) \{{.*?\n\1\}}", fuente, re.S)
        assert m, f"no está {nombre} en {archivo}"
        partes.append(m.group(0))
    return "\n".join(partes)


# Un DOM mínimo: cada id es un objeto con value, hidden y textContent.
DOM = """
const els = {};
function el(id) { return els[id] || (els[id] = { id, value: '', hidden: true, textContent: '', innerHTML: '',
    style: {}, validity: {}, listeners: {}, addEventListener(t, f) { this.listeners[t] = f; } }); }
const document = { activeElement: null, getElementById: el };
let refrescos = 0;
function refrescarAvisos() { refrescos++; }
let avisosTimer = null;
const CDI = { state: { operacion: OP, items: [] }, escapeHtml: s => String(s) };
const window = { CDI };
"""


def _con_montos(dom):
    # SEPARADORES-1: las pantallas leen los montos con montos_ar.js.
    return dom + (V2.parent / "montos_ar.js").read_text(encoding="utf-8") + "\n"


def _correr(codigo, op):
    salida = subprocess.run(["node", "-e", _con_montos(DOM.replace("OP", json.dumps(op))) + codigo],
                            capture_output=True, text=True)
    assert salida.returncode == 0, salida.stderr[-800:]
    return json.loads(salida.stdout)


def _pantalla(op, despues, valor=None, salida_propia=False):
    """Pinta `valor` como si hubiera vuelto con el pedido de ahora y después
    corre `despues`. El pedido es el buildMariaRequest de verdad."""
    nombres = ["ajusteMalEscrito", "importeEscrito", "cuentasViejas", "enlazarValor", "otroDeducir",
               "usarDescuento", "calcularSeguro", "seguroSinLeer", "pintarValor", "firmaDelPedido",
               "buildMariaRequest", "numeroDeFactura", "toNumber", "subitemsDelPedido", "ajusteDelPedido",
               "montoDelPedido", "dejarSeguro", "borrarSeguroCalculado"]
    codigo = ("let ultimoValor = null; let cuentasCon = null; let avisosSeq = 0; let valorEnlazado = false;\n"
              "let lastValidation = null; let semaforos = 0;\n"
              "CDI.semaforo = { refresh() { semaforos++; } };\n"
              f"const VALOR = {json.dumps(VALOR)};\n"
              "const SIN_CUENTAS = 'No se pudieron hacer las cuentas: mirá los avisos.';\n" +
              _funciones("finalize.js", nombres) +
              "\nfunction firmaDeAhora() { return firmaDelPedido(buildMariaRequest()); }"
              f"\npintarValor({json.dumps(valor)}, firmaDeAhora());\n{despues}\n"
              "console.log(JSON.stringify({op: CDI.state.operacion, refrescos, semaforos,"
              " els: Object.fromEntries(Object.entries(els).map(([k, v]) =>"
              " [k, {value: v.value, hidden: v.hidden, textContent: v.textContent, innerHTML: v.innerHTML}]))}));")
    if salida_propia:
        codigo = codigo[:codigo.rindex("console.log(JSON.stringify({op:")]
    return _correr(codigo, op)


VALOR = {"fob_factura": 1387.5, "ajustes_incluir": 0.0, "ajustes_deducir": 0.0, "fob_casillero": 1387.5,
         "flete": 7925.0, "seguro": 0.0, "seguro_sugerido": 93.13, "base_seguro": "FOB de la factura"}


def test_el_descuento_de_la_planilla_se_ofrece_y_no_se_pone_solo():
    r = _pantalla({"descuento": 87.5, "filas_excel_descuento": [14]}, "", VALOR)
    assert "ajustes_deducir" not in r["op"]
    assert r["els"]["valorDeducir"]["value"] == ""
    assert r["els"]["valorDescuento"]["hidden"] is False
    assert r["els"]["valorDescuentoTexto"]["textContent"] == "La planilla trae un descuento de 87,50 (fila 14)."
    assert r["els"]["valorUsarDescuento"]["hidden"] is False


def test_usar_el_descuento_no_pisa_otro_ajuste_a_deducir():
    r = _pantalla({"descuento": 87.5, "ajustes_deducir": "50"}, "usarDescuento();", VALOR)
    assert r["op"]["ajustes_deducir"] == "50"
    assert r["els"]["valorUsarDescuento"]["hidden"] is True
    assert r["els"]["valorDescuentoTexto"]["textContent"] == (
        "La planilla trae un descuento de 87,50. Ajustes a deducir ya tiene otro importe: "
        "si el descuento va aparte, sumalo a mano.")


def test_el_boton_pone_el_descuento_como_ajuste_a_deducir():
    r = _pantalla({"descuento": 87.5}, "usarDescuento();", VALOR)
    # SEPARADORES-1: se escribe como lo escribiría la persona.
    assert r["op"]["ajustes_deducir"] == "87,5"
    assert r["els"]["valorDeducir"]["value"] == "87,5"
    assert r["refrescos"] == 1


def test_sin_descuento_no_se_ofrece_nada():
    r = _pantalla({}, "", VALOR)
    assert r["els"]["valorDescuento"]["hidden"] is True


def test_el_boton_del_seguro_aparece_sin_seguro():
    r = _pantalla({}, "", VALOR)
    assert r["els"]["valorCalcularSeguro"]["hidden"] is False
    assert r["els"]["valorCalcularSeguro"]["textContent"] == (
        "Calcular seguro (1 % de FOB de la factura + flete): 93,13")


def test_el_boton_del_seguro_pone_el_sugerido_y_pide_las_cuentas_de_nuevo():
    r = _pantalla({}, "calcularSeguro();", VALOR)
    assert r["op"]["seguro"] == 93.13 and r["op"]["seguro_calculado"] is True
    assert r["refrescos"] == 1 and r["semaforos"] == 1
    # Hasta que vuelvan, el botón no se ofrece con las cuentas de antes.
    assert r["els"]["valorCalcularSeguro"]["hidden"] is True


def test_despues_de_calcular_el_seguro_la_nota_dice_la_base():
    # Lo que se pinta cuando vuelve la cuenta con el seguro nuevo.
    r = _pantalla({}, "calcularSeguro(); pintarValor({...VALOR, seguro: 93.13}, firmaDeAhora());", VALOR)
    assert r["els"]["valorCalcularSeguro"]["hidden"] is True
    assert r["els"]["valorSeguroNota"]["textContent"] == "Seguro calculado: 1 % de (FOB de la factura + flete)."


def test_con_error_en_las_cuentas_no_se_calcula_el_seguro():
    r = _pantalla({}, "ultimoValor = {error: 'x'}; calcularSeguro();", {"error": "x"})
    assert "seguro_calculado" not in r["op"] and r["refrescos"] == 0


# VALOR-1b: las cuentas valen sólo para el pedido con que se hicieron. Cada
# camino por el que cambia el pedido sin pasar por los campos de ajustes.


def test_el_seguro_sugerido_de_otra_operacion_no_se_usa():
    r = _pantalla({}, "CDI.state.operacion = {flete: 100}; calcularSeguro();", VALOR)
    assert r["op"] == {"flete": 100}
    assert r["refrescos"] == 1


def test_despues_de_usar_el_descuento_no_se_calcula_con_las_cuentas_de_antes():
    r = _pantalla({"descuento": 87.5}, "usarDescuento();", VALOR)
    assert r["els"]["valorCalcularSeguro"]["hidden"] is True
    r = _pantalla({"descuento": 87.5}, "usarDescuento(); calcularSeguro();", VALOR)
    assert "seguro" not in r["op"] and r["op"]["ajustes_deducir"] == "87,5"


def test_un_seguro_puesto_despues_de_las_cuentas_no_se_pisa_con_el_sugerido_viejo():
    # Lo escribió a mano (review.js) o vino al restaurar la operación.
    r = _pantalla({}, "CDI.state.operacion.seguro = '15'; calcularSeguro();", VALOR)
    assert r["op"] == {"seguro": "15"}
    assert r["refrescos"] == 1


def test_un_flete_cambiado_despues_de_las_cuentas_no_se_calcula_con_el_viejo():
    r = _pantalla({"flete": 7925}, "CDI.state.operacion.flete = 100; calcularSeguro();", VALOR)
    assert r["op"] == {"flete": 100}


def test_una_cuenta_vieja_que_llega_tarde_no_pisa_el_seguro_recien_calculado():
    # Cuentas hechas con seguro 0 que se pintan después de calcular.
    r = _pantalla({}, "const vieja = firmaDeAhora(); calcularSeguro();"
                      " pintarValor({...VALOR, seguro_sugerido: 50}, vieja); calcularSeguro();", VALOR)
    assert r["op"]["seguro"] == 93.13


def test_la_firma_no_cambia_por_el_numero_de_operacion_y_si_por_lo_demas():
    # Sin factura, el número de operación lleva la hora: no invalida nada.
    r = _pantalla({}, "console.log(JSON.stringify([firmaDelPedido({operation_id: 'OP_1', flete: 1}) ==="
                      " firmaDelPedido({operation_id: 'OP_2', flete: 1}), firmaDelPedido({flete: 1}) ==="
                      " firmaDelPedido({flete: 2})])); process.exit(0);", VALOR, salida_propia=True)
    assert r == [True, False]


def test_sin_firma_no_se_calcula():
    r = _pantalla({}, "pintarValor(VALOR); calcularSeguro();", VALOR)
    assert "seguro" not in r["op"]


def test_el_seguro_calculado_deja_de_avisarse_como_no_leido():
    r = _pantalla({"campos_sin_leer": ["seguro", "flete"], "campos_completados": ["flete"]},
                  "calcularSeguro();", VALOR)
    assert sorted(r["op"]["campos_completados"]) == ["flete", "seguro"]
    assert r["semaforos"] == 1


def test_si_la_factura_puede_traer_seguro_se_avisa_antes_de_calcularlo():
    r = _pantalla({"campos_sin_leer": ["seguro"]}, "", VALOR)
    assert r["els"]["valorCalcularSeguro"]["hidden"] is False
    assert r["els"]["valorSeguroNota"]["textContent"] == (
        "La factura puede traer un seguro que no pudimos leer: revisala antes de calcularlo.")
    r = _pantalla({"campos_sin_leer": ["seguro"], "campos_completados": ["seguro"]}, "", VALOR)
    assert r["els"]["valorSeguroNota"]["textContent"] == ""


def test_sin_operacion_todavia_el_boton_igual_pone_el_seguro():
    r = _pantalla(None, "calcularSeguro();", VALOR)
    assert r["op"] == {"seguro": 93.13, "seguro_calculado": True}


def test_al_escribir_un_ajuste_el_boton_se_esconde_hasta_que_vuelvan_las_cuentas():
    r = _pantalla({}, "", VALOR)
    assert r["els"]["valorCalcularSeguro"]["hidden"] is False
    # El sufijo de la operación no es un ajuste, pero cambia el pedido con el que se hicieron las cuentas.
    campos = {"valorIncluir": "ajustes_incluir", "valorDeducir": "ajustes_deducir",
              "sbtSufijoValor": "sbt_sufijo_valor"}
    vistos = {}
    for campo in campos:
        # El pedido de las cuentas nuevas sale con un reloj: acá corre en el acto.
        r = _pantalla({}, f"globalThis.setTimeout = f => f(); enlazarValor(); const c = el('{campo}');"
                          " c.value = '500'; (c.listeners.input || (() => 0))();", VALOR)
        vistos[campo] = (r["op"], r["els"]["valorCalcularSeguro"]["hidden"], r["refrescos"])
    assert vistos == {campo: ({atributo: "500"}, True, 1) for campo, atributo in campos.items()}


def test_mientras_se_rehacen_las_cuentas_no_se_calcula_con_las_viejas():
    # Se escribe un ajuste y se toca el botón antes de que vuelvan las cuentas.
    r = _pantalla({}, "enlazarValor(); els.valorDeducir.value = '500';"
                      " els.valorDeducir.listeners.input(); calcularSeguro();", VALOR)
    assert r["op"] == {"ajustes_deducir": "500"}
    assert r["els"]["valorCalcularSeguro"]["hidden"] is True


def test_un_numero_que_el_campo_no_entiende_queda_marcado_y_a_la_vista():
    # SEPARADORES-1: el campo es de texto y guarda lo escrito tal cual.
    r = _pantalla({}, "enlazarValor(); els.valorIncluir.value = '1-2';"
                      " els.valorIncluir.listeners.input(); pintarValor(VALOR);",
                  VALOR)
    assert r["op"]["ajustes_incluir"] == "1-2"
    assert r["els"]["valorIncluir"]["value"] == "1-2"
    assert r["els"]["valorError"]["textContent"] == "Ajustes a incluir: no es un número."


def test_lo_que_se_esta_escribiendo_no_se_pisa():
    # En el campo en foco está lo que la persona escribe: lo guardado no lo pisa.
    campos = {"valorIncluir": "ajustes_incluir", "valorDeducir": "ajustes_deducir"}
    vistos = {campo: _pantalla(
        {}, f"els.{campo}.value = '12'; document.activeElement = els.{campo};"
            f" CDI.state.operacion.{atributo} = '99'; pintarValor(VALOR);", VALOR
    )["els"][campo]["value"] for campo, atributo in campos.items()}
    assert vistos == {"valorIncluir": "12", "valorDeducir": "12"}


def test_un_ajuste_mal_escrito_se_ve_en_el_campo_que_llega_vacio():
    # La página se recargó: el campo arranca vacío y la operación trae el texto.
    campos = {"ajustes_incluir": "valorIncluir", "ajustes_deducir": "valorDeducir"}
    vistos = {el: _pantalla({campo: "1-2"}, "", VALOR)["els"][el]["value"] for campo, el in campos.items()}
    assert vistos == {"valorIncluir": "1-2", "valorDeducir": "1-2"}


def _avisos(despues):
    """refrescarAvisos de verdad, con CDI.api que contesta cuando se le dice."""
    stubs = ("let ultimoValor = null; let cuentasCon = null; let avisosSeq = 0;\n"
             "const SIN_CUENTAS = 'No se pudieron hacer las cuentas: mirá los avisos.';\n"
             "function stripLeadingIcon(s) { return s; } function extractItemRef() { return ''; }\n"
             "let pedidoAhora = {}; function buildMariaRequest() { return pedidoAhora; }\n"
             "const pendientes = []; CDI.state.items = [{}];\n"
             "CDI.api = () => new Promise(ok => pendientes.push(ok));\n"
             "function contestar(i, okHttp, data) { pendientes[i]({ok: okHttp, json: async () => data}); }\n")
    codigo = stubs + _funciones("finalize.js", ["ajusteMalEscrito", "importeEscrito", "otroDeducir", "pintarValor",
                                                "borrarSeguroCalculado", "seguroSinLeer", "firmaDelPedido", "refrescarAvisos",
                                                "avisosDeLosMontos", "alCentavoDelTxt"]) + (
        f"\n(async () => {{ {despues}; await new Promise(r => setTimeout(r, 0));"
        " console.log(JSON.stringify({ultimoValor, cuentasCon, error: els.valorError.textContent,"
        " cuentas: els.valorCuentas.innerHTML})); })();")
    return _correr(codigo, {})


def test_si_fallan_los_avisos_la_tarjeta_lo_dice():
    r = _avisos("const p = refrescarAvisos(); contestar(0, false, {detail: 'Procedencia: no'}); await p")
    assert r["error"] == "No se pudieron hacer las cuentas: mirá los avisos."
    assert r["cuentas"] == ""


def test_una_respuesta_vieja_no_pisa_las_cuentas_nuevas():
    r = _avisos("const a = refrescarAvisos(); const b = refrescarAvisos();"
                    f" contestar(1, true, {{avisos: [], valor: {json.dumps(VALOR)}}}); await b;"
                    " contestar(0, true, {avisos: [], valor: {error: 'vieja'}}); await a")
    assert r["ultimoValor"] == VALOR


def test_las_cuentas_quedan_atadas_al_pedido_que_se_mando():
    r = _avisos(f"const p = refrescarAvisos(); contestar(0, true, {{avisos: [], valor: {json.dumps(VALOR)}}}); await p")
    assert r["cuentasCon"] == "{}"


def test_un_pedido_que_cambia_mientras_viajan_las_cuentas_no_se_les_pega():
    # La firma es la del pedido que se mandó, no la del de cuando vuelven.
    r = _avisos("const p = refrescarAvisos(); pedidoAhora = {flete: 100};"
                f" contestar(0, true, {{avisos: [], valor: {json.dumps(VALOR)}}}); await p")
    assert r["cuentasCon"] == "{}"


def test_el_boton_nombra_la_base_que_dice_el_servidor():
    r = _pantalla({}, "", {**VALOR, "base_seguro": "FOB casillero", "seguro_sugerido": 92.25})
    assert r["els"]["valorCalcularSeguro"]["textContent"] == (
        "Calcular seguro (1 % de FOB casillero + flete): 92,25")


def test_con_seguro_de_la_factura_no_se_ofrece_calcularlo():
    r = _pantalla({"seguro": 12.4}, "", {**VALOR, "seguro": 12.4})
    assert r["els"]["valorCalcularSeguro"]["hidden"] is True
    assert r["els"]["valorSeguroNota"]["textContent"] == "La operación ya trae seguro."


def test_un_seguro_calculado_con_otros_importes_se_ofrece_recalcular():
    r = _pantalla({"seguro": 93.13, "seguro_calculado": True},
                  "", {**VALOR, "seguro": 93.13, "seguro_sugerido": 92.25})
    assert r["els"]["valorCalcularSeguro"]["hidden"] is False
    assert r["els"]["valorCalcularSeguro"]["textContent"].startswith("Recalcular seguro")
    assert r["els"]["valorSeguroNota"]["textContent"] == "El seguro se calculó con otros importes."


def test_las_cuentas_se_ven_y_el_error_tambien():
    r = _pantalla({}, "", VALOR)
    assert "= FOB casillero" in r["els"]["valorCuentas"]["innerHTML"]
    assert "1.387,50" in r["els"]["valorCuentas"]["innerHTML"]
    r = _pantalla({"ajustes_deducir": "mal escrito"}, "", {"error": "Ajustes a deducir: x"})
    assert r["els"]["valorError"]["hidden"] is False
    assert r["els"]["valorError"]["textContent"] == "Ajustes a deducir: no es un número. Ajustes a deducir: x"
    assert r["els"]["valorCuentas"]["innerHTML"] == ""
    assert r["els"]["valorCalcularSeguro"]["hidden"] is True


def test_el_pedido_manda_los_ajustes_y_nunca_algo_que_frene_el_txt():
    codigo = _funciones("finalize.js", ["ajusteDelPedido"]) + (
        "\nconsole.log(JSON.stringify(['', null, undefined, '12.5', 'mal escrito', '1e999', 0, '0']"
        ".map(ajusteDelPedido)));")
    # Lo que no se lee viaja tal cual: el servidor lo dice en las cuentas y no
    # frena el TXT (SEPARADORES-1b, D19; test_separadores1b).
    assert _correr(codigo, {}) == [None, None, None, 12.5, "mal escrito", "1e999", 0, 0]
    fuente = (V2 / "finalize.js").read_text(encoding="utf-8")
    pedido = re.search(r"function buildMariaRequest\(\) \{.*?\n    \}", fuente, re.S).group(0)
    assert "ajustes_incluir: ajusteDelPedido(op.ajustes_incluir)" in pedido
    assert "ajustes_deducir: ajusteDelPedido(op.ajustes_deducir)" in pedido


def test_un_seguro_escrito_a_mano_deja_de_ser_el_calculado():
    stubs = ("let form = {}; const initialPdfValues = {};\n"
             "function updateFieldHint() {} function validateField() {} function renderMissingCount() {}\n"
             "function updateContinueEnabled() {} function renderIncotermWarning() {} function renderProrrateoPanel() {}\n")
    codigo = stubs + "const MONTOS = ['flete', 'seguro', 'gastos_anteriores_fob'];\n" + _funciones(
        "review.js", ["montoDelCampo", "onFieldChange"]) + (
        "\nonFieldChange({target: {name: 'seguro', type: 'number', value: '15'}});"
        "\nconsole.log(JSON.stringify(CDI.state.operacion));")
    assert _correr(codigo, {"seguro": 93.13, "seguro_calculado": True}) == {"seguro": 15}
