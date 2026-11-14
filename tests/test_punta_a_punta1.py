"""PUNTA-A-PUNTA-1: el recorrido de Emi entero, por HTTP, contra los archivos reales.

Lo que hace la pantalla v2, en orden y por las mismas rutas:
1. entra (registro y login de verdad, con la cookie y el token CSRF que manda
   `CDI.api`, app_v2.js);
2. sube la factura: un PDF por `/upload_pdf/public` (con un Gemini falso que
   «lee» los datos del archivo real: ni Gemini real ni internet), o un Excel
   con esos datos por `/upload_excel_v2/`;
3. revisa: completa lo que la persona escribe en la revisión y la NCM del
   paso de NCM, y pasa por `/api/validate/smart` como el semáforo;
4. genera con `/generate_maria`, con el pedido armado como `buildMariaRequest`
   (finalize.js), y
5. descarga el TXT por el `download_url`.

El TXT descargado se compara byte a byte con tests/fixtures/maria_golden_anon.TXT.
La pantalla no manda el número de operación del archivo real (D23 del informe
de la Dev 1), así que el esperado es el archivo real con esas líneas
cambiadas, nombradas en `_como_sale_por_la_pantalla`. El archivo real sin
cambios queda como `xfail` estricto: el día que la pantalla lo produzca, avisa.

El de subítems (maria_golden_subitems_anon.TXT) se compara entero, línea por
línea: ese archivo se guardó con LF y sin completar los campos con espacios.
Además de D23, la referencia de la factura sale del número de operación
(D25). Los subítems se cargan en el panel del paso de NCM (SUBITEMS-1;
antes, D24).
"""
import io
import json
import math
import os
import re
import sys
import types
import uuid

import pytest
from fastapi.testclient import TestClient

from proyecto_maria import main
from proyecto_maria.core.maria_generator import id_corto_maria
from tests.test_maria1a_lectura_factura import _pdf_en_blanco
from tests.test_maria_subitems import REFERENCIA as SUBITEMS_PATH
from tests.test_generar_maria_txt import _GOLDEN_PATH, golden_con_destino

CUIT_DESPACHANTE = "20111111112"
# El CUIT anonimizado del archivo real (30999999990) tiene mal el dígito
# verificador y desde MARIA-1b no deja generar: va uno válido y en el
# esperado se cambia sólo esa línea (como tests/test_maria1b_controles.py).
CUIT_IMPORTADOR = "30999999995"

# La factura del archivo real, como la leería Gemini y como la completaría la
# persona en la revisión y en el paso de NCM.
FACTURA = {
    "gemini": {
        "operacion": {
            "numero_factura": "000999001", "fecha_emision": "18/07/2025",
            "vendedor_nombre": "(00999) PROVEEDOR DEMO S.A.", "vendedor_id": "20999999991",
            "comprador_nombre": "IMPORTADORA DEMO S.A", "comprador_cuit": CUIT_IMPORTADOR,
            "comprador_domicilio": "CALLE FALSA 123",
            "moneda": "DOL", "incoterm": "DDP", "flete": "3221.66", "seguro": "50.00",
        },
        "items": [{"descripcion": "MAQUINA DEMO", "cantidad": "1", "valor_unitario": "5000.00",
                   "peso_total_linea": "1220", "origen": "Argentina"}],
    },
    "ncm": "84798999900H",
    # Lo que la persona escribe en la revisión (review.js; la procedencia se
    # elige de la lista de países) y en generar.
    "revision": {"fecha_embarque": "02/01/2026", "comprador_fecha_inic_activ": "01/01/2010",
                 "procedencia": "222 · PERU", "sbt_sufijo_valor": "AA(DEMO)-AB(DEMO)-CA00-"},
    # La tarjeta del despachante (despachante.js): lo que la persona elige.
    "despachante": {"iva_adicional": "IVAAD1"},
    "estados": ["3"],
}

SUF_A = ("AA(DemoPouchs)-AB(MODELO-A 001)-ZA(016384)-ZB(004400)-ZC(000256)"
         "-ZD(000001)-CA00-NA00-NB00-NC01-ND01-NE00-NF01-")
SUF_B = SUF_A.replace("MODELO-A 001", "MODELO-B 002")

FACTURA_SUBITEMS = {
    "gemini": {
        "operacion": {
            "numero_factura": "002720126", "fecha_emision": "22/06/2026",
            "vendedor_nombre": "(00272) PROVEEDOR SUBITEMS DEMO, CO", "vendedor_id": "82-1111111",
            "comprador_nombre": "IMPORTADORA DEMO S.A.", "comprador_cuit": CUIT_IMPORTADOR,
            "comprador_domicilio": "CALLE FALSA 123",
            "moneda": "DOL", "incoterm": "EXW", "flete": "365.00", "seguro": "75.47",
        },
        "items": [{"descripcion": "Equipo de demostracion para prueba", "cantidad": "6",
                   "valor_unitario": "1197.00", "peso_total_linea": "33", "origen": "China"}],
    },
    "ncm": "84714900100D",
    "revision": {"fecha_embarque": "12/08/2026", "comprador_fecha_inic_activ": "15/04/2004",
                 "aduana_codigo": "073", "gastos_anteriores_fob": "150",
                 "sbt_sufijo_valor": "AA(DemoPouchs)-CA00-"},
    "despachante": {"banco_bcra": "191", "empresa_digitalizacion": "PSAD01", "iva_adicional": "NO_VALIDA"},
    "estados": ["2"],
    "subitems": [{"cantidad": 2, "valor_unitario": 1197.00, "sufijo": SUF_A},
                 {"cantidad": 4, "valor_unitario": 1197.00, "sufijo": SUF_B}],
}

# Lo que el archivo real lleva y la pantalla no puede mandar o el generador
# no emite. Cada una es una D del informe de la Dev 1.
# D23: la pantalla arma el número de operación como «FAC_» + número de
#      factura (finalize.js, buildMariaRequest), no el número de 9 dígitos, y
#      el generador saca de ahí NDDTIMMTRN e IEXT («FAC_0»).
# D24 (resuelta en SUBITEMS-1): los subítems se cargan en el panel del paso de
#      NCM y viajan en el pedido de la pantalla.
# D25 (resuelta en MARIA-7): la referencia de la factura (LDVDREFDOC) es el
#      número de factura de la pantalla.
# MARIA-7: IDSO, IDDT e IARTESPAPU llevan los últimos 8 letras o números del
#      número de operación; con «FAC_» + los 9 dígitos dan lo mismo que el
#      archivo real recortado.


def _como_sale_por_la_pantalla(real: str, original: str, operation_id: str) -> str:
    """El archivo real con las líneas de D23 (y el CUIT válido) cambiadas."""
    cambios = {
        "NDDTIMMIOE=30999999990": f"NDDTIMMIOE={CUIT_IMPORTADOR}",
        f"IDSO={id_corto_maria(original)}": f"IDSO={id_corto_maria(operation_id)}",
        f"NDDTIMMTRN={original[:5]}": f"NDDTIMMTRN={operation_id[:5]}",
        f"MCPL={original}": f"MCPL={operation_id}",
        f"IDDT={id_corto_maria(original)}": f"IDDT={id_corto_maria(operation_id)}",
        f"IARTESPAPU={id_corto_maria(original)}0001": f"IARTESPAPU={id_corto_maria(operation_id)}0001",
        f"IEXT={original[:5]}-": f"IEXT={operation_id[:5]}-",
    }
    # El MCPL del número va completado a 40 con espacios: el largo no cambia.
    padded = f"MCPL={original:<40}"
    if padded in real:
        cambios.pop(f"MCPL={original}")
        cambios[padded] = f"MCPL={operation_id:<40}"
    # MARIA-7: LDVDREFDOC es el número de factura de la pantalla (D25).
    referencia = "LDVDREFDOC=E001-1" + " " * 22
    if referencia in real:
        cambios[referencia] = f"LDVDREFDOC={original:<28}"
    for antes, despues in cambios.items():
        assert antes in real, f"el archivo real ya no tiene {antes!r}"
        real = real.replace(antes, despues)
    return real


def _sin_relleno(txt: str) -> list:
    """Líneas sin los espacios del final ni el CR: el archivo de subítems se
    guardó así (LF, sin completar los campos y con un salto al final), el
    generador completa los campos y termina sin salto."""
    return [ln.rstrip() for ln in txt.replace("\r\n", "\n").rstrip("\n").split("\n")]


def _numero_js(v) -> float:
    """toNumber de finalize.js: Number(v) y, si no es finito, 0. Number()
    acepta espacios alrededor, «0x10» y «1e3», y no «1_000» ni «inf»."""
    if v is None or isinstance(v, bool):
        return float(bool(v))
    if isinstance(v, (int, float)):
        return float(v) if math.isfinite(v) else 0.0
    t = str(v).strip()
    if t == "":
        return 0.0
    if re.fullmatch(r"0[xX][0-9a-fA-F]+", t):
        return float(int(t, 16))
    if not re.fullmatch(r"[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?", t):
        return 0.0
    n = float(t)
    return n if math.isfinite(n) else 0.0


def _formatear_ncm(raw: str) -> str:
    """CDI.formatNcm (app_v2.js): lo que el paso de NCM guarda en it.pieza,
    con puntos y la letra separada: «8479.89.99.900 H»."""
    s = str(raw or "").strip()
    letra = s[-1].upper() if s and s[-1].isascii() and s[-1].isalpha() else ""
    d = re.sub(r"[^0-9]", "", s)[:11]
    if len(d) <= 4:
        base = d
    elif len(d) <= 6:
        base = d[:4] + "." + d[4:]
    elif len(d) <= 8:
        base = d[:4] + "." + d[4:6] + "." + d[6:]
    else:
        base = d[:4] + "." + d[4:6] + "." + d[6:8] + "." + d[8:]
    return base + (" " + letra if letra else "")


def _leer(path: str) -> str:
    with open(path, "r", newline="") as f:
        return f.read()


# ---------------------------------------------------------------- entorno


@pytest.fixture(autouse=True)
def _entorno(monkeypatch):
    """Sin atajos de autenticación: login de verdad y CSRF exigido."""
    from proyecto_maria.core.rate_limit import limiter
    monkeypatch.setattr(limiter, "enabled", False)
    monkeypatch.setenv("CSRF_ENFORCE", "true")
    monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "false")
    guardados = dict(main.app.dependency_overrides)
    main.app.dependency_overrides.clear()
    yield
    main.app.dependency_overrides.clear()
    main.app.dependency_overrides.update(guardados)


def _gemini_falso(monkeypatch, respuesta: dict) -> None:
    """Gemini falso que devuelve `respuesta`, en la copia «pdf_directo» (sin
    PyMuPDF, la de producción). Como tests/test_maria1a_lectura_factura.py."""
    respuesta = dict(respuesta, documento={"tipo": "factura_comercial", "operacion": "importacion", "destinacion": ""})
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("ENABLE_PDF_LLM_FALLBACK", "true")
    monkeypatch.setattr("time.sleep", lambda s: None)

    class _Modelo:
        def __init__(self, nombre):
            pass

        def generate_content(self, partes):
            return types.SimpleNamespace(text=json.dumps(respuesta))

    falso = types.SimpleNamespace(configure=lambda **kw: None, GenerativeModel=_Modelo)
    google = sys.modules.get("google") or types.ModuleType("google")
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setattr(google, "generativeai", falso, raising=False)
    monkeypatch.setitem(sys.modules, "google.generativeai", falso)
    monkeypatch.setitem(sys.modules, "fitz", None)


class _Pantalla:
    """Lo que hace la pantalla v2 por HTTP, con su estado (CDI.state)."""

    def __init__(self):
        self.http = TestClient(main.app)
        self.operacion: dict = {}
        self.items: list = []
        self.usuario: dict = {}

    def _post(self, url, **kw):
        # CDI.api manda el token CSRF de la cookie en todo lo que no es GET.
        kw.setdefault("headers", {})["X-CSRF-Token"] = self.http.cookies.get("csrf_token") or ""
        return self.http.post(url, **kw)

    def entrar(self):
        nombre = f"pap_{uuid.uuid4().hex[:10]}"
        clave = "clave-de-prueba-123"
        r = self.http.post("/auth/register", json={
            "username": nombre, "password": clave, "email": f"{nombre}@test.cdi", "name": nombre})
        assert r.status_code in (200, 201), r.text[:300]
        # El CUIT del despachante, cargado en el perfil.
        r = self.http.put("/api/user/profile", json={"cuit": CUIT_DESPACHANTE},
                          headers={"X-CSRF-Token": self.http.cookies.get("csrf_token") or ""})
        assert r.status_code == 200, r.text[:300]
        self.http.cookies.clear()
        r = self.http.post("/auth/login", json={"username": nombre, "password": clave})
        assert r.status_code == 200, r.text[:300]
        assert self.http.cookies.get("access_token") and self.http.cookies.get("csrf_token")
        r = self.http.get("/auth/current_user")  # app_v2.js → CDI.currentUser
        assert r.status_code == 200, r.text[:300]
        self.usuario = r.json()

    def subir(self, nombre: str, contenido: bytes, ruta: str):
        r = self._post(ruta, files={"file": (nombre, contenido)})
        assert r.status_code == 200, r.text[:400]
        data = r.json()
        assert data.get("items"), data  # upload.js rechaza 0 ítems
        self.operacion = dict(data.get("operacion") or {})
        self.items = [dict(it) for it in data["items"]]

    def revisar(self, ncm: str, campos: dict, despachante: dict, estados: list):
        # Paso de NCM: la NCM elegida queda en it.pieza con el formato de la
        # pantalla (ncm.js, CDI.formatNcm).
        for it in self.items:
            it["pieza"] = _formatear_ncm(ncm)
        # Revisión: lo que la persona escribe va a CDI.state.operacion.
        self.operacion.update(campos)
        # Tarjeta del despachante: lo elegido va a operacion.despachante y el
        # estado de cada producto a it.estado (despachante.js, alElegir).
        self.operacion["despachante"] = dict(despachante)
        for it, estado in zip(self.items, estados):
            it["estado"] = estado
        # Semáforo y pantalla «validando»: items + cabecera.
        r = self._post("/api/validate/smart", json={
            "items": self._items_para_validar(), "operacion": self._cabecera()})
        assert r.status_code == 200, r.text[:400]
        assert r.json().get("success") is True, r.text[:400]
        assert not r.json().get("errores"), r.json().get("errores")

    def _items_para_validar(self):
        """buildItemsForValidation (finalize.js) y semaforo.js."""
        return [{"pieza": str(it.get("pieza") or "").strip(),
                 "descripcion": str(it.get("descripcion") or "").strip(),
                 "origen": str(it.get("origen") or "XX").strip().upper() or "XX",
                 "cantidad": _numero_js(it.get("cantidad")),
                 "valor_unitario": _numero_js(it.get("valor_unitario")),
                 "peso_unitario": _numero_js(it.get("peso_unitario"))} for it in self.items]

    def _cabecera(self):
        """cabeceraParaValidar (finalize.js)."""
        p = self.pedido()
        return {k: p[k] for k in ("moneda", "incoterm", "comprador_cuit", "flete", "seguro")}

    def pedido(self) -> dict:
        """buildMariaRequest (finalize.js), campo por campo. Es una copia: si
        finalize.js cambia y esto no, la prueba no lo ve."""
        op = self.operacion
        factura = str(op.get("numero_factura") or "").strip()
        assert factura, "sin número de factura la pantalla usa la hora: OP_<fecha>"
        operation_id = "FAC_" + re.sub(r"[^a-zA-Z0-9_-]", "", factura)

        def texto(v):
            return str(v or "").strip()

        numero = _numero_js

        elegidos = op.get("despachante") or {}
        items = [{
            "pieza": texto(it.get("pieza")), "descripcion": texto(it.get("descripcion")),
            "origen": texto(it.get("origen") or "XX").upper() or "XX",
            "cantidad": numero(it.get("cantidad")), "valor_unitario": numero(it.get("valor_unitario")),
            "peso_unitario": numero(it.get("peso_unitario")), "codigo_parte": texto(it.get("codigo_parte")),
            "grupo_id": it.get("grupo_id") or None,
            # despachante.js, unidadesDe (MARIA-7): la del producto o la de la
            # operación; la estadística viaja sólo si es kilos.
            "unidad": it.get("unidad") or elegidos.get("unidad") or None,
            "unidad_estadistica": "01" if (it.get("unidad_estadistica") or elegidos.get(
                "unidad_estadistica") or "DCL") == "01" else None,
            "estado": it.get("estado") or None, "iva_adicional": it.get("iva_adicional") or None,
            # subitemsDelPedido: sólo si el producto está partido (SUBITEMS-1).
            **({"subitems": [{"cantidad": numero(s.get("cantidad")), "valor_unitario": numero(s.get("valor_unitario")),
                              **({"sufijo": texto(s.get("sufijo"))} if texto(s.get("sufijo")) else {})}
                             for s in it["subitems"]]} if it.get("subitems") else {}),
        } for it in self.items]
        # despachante.js, valores(): sin cliente activo no hay propuesta.
        despachante = {
            "banco_bcra": elegidos["banco_bcra"] if elegidos.get("banco_bcra") is not None else "",
            "empresa_digitalizacion": elegidos.get("empresa_digitalizacion") or None,
            "iva_adicional": elegidos.get("iva_adicional") or None,
        }
        # paises_maria.js, resolve(): de la lista sale «222 · PERU» y va «222».
        procedencia = texto(op.get("procedencia"))
        codigo = re.match(r"^(\d{3})(?:\s*[·-].*)?$", procedencia)
        return {
            "operation_id": operation_id, "numero_factura": factura, "items": items, **despachante,
            "moneda": texto(op.get("moneda")).upper(), "incoterm": texto(op.get("incoterm")).upper(),
            "cuit_agr": re.sub(r"[-\s]", "", str(op.get("cuit_agr") or self.usuario.get("cuit") or "")),
            "vendedor_nombre": texto(op.get("vendedor_nombre")), "vendedor_id": texto(op.get("vendedor_id")),
            "comprador_nombre": texto(op.get("comprador_nombre")),
            "comprador_cuit": re.sub(r"[-\s]", "", str(op.get("comprador_cuit") or "")),
            "comprador_domicilio": texto(op.get("comprador_domicilio")),
            "comprador_fecha_inic_activ": texto(op.get("comprador_fecha_inic_activ")),
            "flete": numero(op.get("flete")), "seguro": numero(op.get("seguro")),
            "gastos_anteriores_fob": numero(op.get("gastos_anteriores_fob")),
            "procedencia": codigo.group(1) if codigo else procedencia,
            "bl_numero": texto(op.get("bl") or op.get("bl_numero")),
            "puerto_origen": texto(op.get("puerto_origen")),
            "puerto_destino": texto(op.get("puerto_destino") or "ARBUE") or "ARBUE",
            "buque_nombre": texto(op.get("buque") or op.get("buque_nombre")),
            "viaje_numero": texto(op.get("viaje_numero")),
            "fecha_embarque": texto(op.get("fecha_embarque")), "fecha_emision": texto(op.get("fecha_emision")),
            "contenedor_numero": texto(op.get("contenedor_numero")),
            "contenedor_tipo": texto(op.get("contenedor_tipo")),
            "contenedor_peso": numero(op.get("contenedor_peso")),
            "aduana_codigo": texto(op.get("aduana_codigo") or "001") or "001",
            "tipo_destinacion": texto(op.get("tipo_destinacion") or "IC04").upper() or "IC04",
            "sbt_sufijo_valor": texto(op.get("sbt_sufijo_valor")),
        }

    def cargar_subitems(self, indice: int, subitems: list):
        """El panel de subítems del paso de NCM (ncm.js): lo que se escribe
        queda en it.subitems."""
        self.items[indice]["subitems"] = [dict(s) for s in subitems]

    def generar_y_descargar(self, pedido: dict | None = None) -> tuple[str, str]:
        pedido = pedido or self.pedido()
        r = self._post("/generate_maria", json=pedido)
        assert r.status_code == 200, r.text[:600]
        data = r.json()
        # onDownload (finalize.js): <a href=download_url download>.
        bajada = self.http.get(data["download_url"])
        assert bajada.status_code == 200, bajada.text[:300]
        assert "attachment" in bajada.headers.get("content-disposition", "")
        txt = bajada.content.decode("utf-8")
        assert txt == data["content"], "lo descargado no es lo que mostró la pantalla"
        # Que las corridas no dejen archivos en data/descargas.
        archivo = os.path.join(main._user_downloads_dir(self.usuario["username"]), data["filename"])
        if os.path.exists(archivo):
            os.remove(archivo)
        return txt, pedido["operation_id"]


def _excel_de(factura: dict) -> bytes:
    """La misma factura como planilla del proveedor (el país por nombre)."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["NCM", "Descripcion", "Pais de origen", "Cantidad", "Precio Unitario", "Peso Neto"])
    for it in factura["gemini"]["items"]:
        ws.append([factura["ncm"], it["descripcion"], it["origen"], float(it["cantidad"]),
                   float(it["valor_unitario"]), float(it["peso_total_linea"])])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _por_pdf(monkeypatch, factura: dict) -> _Pantalla:
    _gemini_falso(monkeypatch, factura["gemini"])
    p = _Pantalla()
    p.entrar()
    p.subir("factura.pdf", _pdf_en_blanco(), "/upload_pdf/public")
    p.revisar(factura["ncm"], factura["revision"], factura["despachante"], factura["estados"])
    if factura.get("subitems"):
        p.cargar_subitems(0, factura["subitems"])
    return p


def _por_excel(factura: dict) -> _Pantalla:
    p = _Pantalla()
    p.entrar()
    p.subir("factura.xlsx", _excel_de(factura), "/upload_excel_v2/")
    # Sin cliente elegido la planilla no trae cabecera: la persona la escribe
    # en la revisión (los mismos datos que el PDF trae leídos).
    cabecera = {k: v for k, v in factura["gemini"]["operacion"].items()}
    p.revisar(factura["ncm"], {**cabecera, **factura["revision"]}, factura["despachante"],
              factura["estados"])
    if factura.get("subitems"):
        p.cargar_subitems(0, factura["subitems"])
    return p


# ------------------------------------------------------------------ pruebas


def test_pdf_de_punta_a_punta_da_el_archivo_real(monkeypatch):
    txt, operation_id = _por_pdf(monkeypatch, FACTURA).generar_y_descargar()
    assert txt == _como_sale_por_la_pantalla(golden_con_destino(_leer(_GOLDEN_PATH)), "000999001", operation_id)


def test_excel_de_punta_a_punta_da_el_archivo_real():
    txt, operation_id = _por_excel(FACTURA).generar_y_descargar()
    assert txt == _como_sale_por_la_pantalla(golden_con_destino(_leer(_GOLDEN_PATH)), "000999001", operation_id)


@pytest.mark.xfail(strict=True, reason="D23 (va a MARIA-6): la pantalla manda «FAC_» + número de "
                   "factura como número de operación")
def test_pdf_de_punta_a_punta_da_el_archivo_real_sin_cambios(monkeypatch):
    txt, _ = _por_pdf(monkeypatch, FACTURA).generar_y_descargar()
    assert txt == golden_con_destino(_leer(_GOLDEN_PATH)).replace("NDDTIMMIOE=30999999990", f"NDDTIMMIOE={CUIT_IMPORTADOR}")


@pytest.mark.parametrize("camino", ["pdf", "excel"])
def test_subitems_de_punta_a_punta_dan_el_archivo_real(monkeypatch, camino):
    p = _por_pdf(monkeypatch, FACTURA_SUBITEMS) if camino == "pdf" else _por_excel(FACTURA_SUBITEMS)
    txt, operation_id = p.generar_y_descargar()
    esperado = _como_sale_por_la_pantalla(_leer(SUBITEMS_PATH), "002720126", operation_id)
    # D25: el archivo real lleva «110»; la pantalla, el número de factura.
    esperado = esperado.replace("LDVDREFDOC=110", "LDVDREFDOC=002720126")
    assert _sin_relleno(txt) == _sin_relleno(esperado)


def test_el_recorrido_pasa_por_el_login_y_el_csrf_de_verdad(monkeypatch):
    """Sin atajos: sin el token CSRF la generación se rechaza, y sin sesión
    también. Si no, el recorrido de arriba no probaría lo que hace la pantalla."""
    p = _por_pdf(monkeypatch, FACTURA)
    sin_csrf = p.http.post("/generate_maria", json=p.pedido())
    assert sin_csrf.status_code == 403, sin_csrf.text[:200]
    p.http.cookies.clear()
    monkeypatch.setattr("proyecto_maria.auth.dependencies._is_testing_runtime", lambda: False)
    sin_sesion = p.http.post("/generate_maria", json=p.pedido())
    assert sin_sesion.status_code == 401, sin_sesion.text[:200]


def test_una_factura_con_coma_decimal_da_el_mismo_archivo(monkeypatch):
    """La misma factura escrita a la europea: «5.000,00», «3.221,66». El peso
    «1.220» solo es ambiguo: es 1220 kg porque la factura usa la coma."""
    factura = {**FACTURA, "gemini": {
        "operacion": {**FACTURA["gemini"]["operacion"], "flete": "3.221,66", "seguro": "50,00"},
        "items": [{**FACTURA["gemini"]["items"][0], "valor_unitario": "5.000,00", "peso_total_linea": "1.220"}],
    }}
    txt, operation_id = _por_pdf(monkeypatch, factura).generar_y_descargar()
    assert txt == _como_sale_por_la_pantalla(golden_con_destino(_leer(_GOLDEN_PATH)), "000999001", operation_id)


def _bloques(txt: str, nombre: str) -> list:
    """Los bloques [nombre] del TXT como diccionarios clave → valor."""
    bloques = []
    for parte in txt.replace("\r\n", "\n").split("\n\n"):
        lineas = [l for l in parte.split("\n") if l]
        if lineas and lineas[0] == f"[{nombre}]":
            bloques.append(dict(l.split("=", 1) for l in lineas[1:]))
    return bloques


def test_dos_productos_reparten_flete_y_seguro_por_su_fob(monkeypatch):
    """El archivo real tiene un solo producto: con dos se ve el prorrateo.
    FOB 3000 y 2000 (5000 en total), flete 3221,66 y seguro 50."""
    factura = {**FACTURA, "gemini": {
        "operacion": FACTURA["gemini"]["operacion"],
        "items": [
            {"descripcion": "MAQUINA DEMO GRANDE", "cantidad": "1", "valor_unitario": "3000.00",
             "peso_total_linea": "700", "origen": "Argentina"},
            {"descripcion": "MAQUINA DEMO CHICA", "cantidad": "2", "valor_unitario": "1000.00",
             "peso_total_linea": "260", "origen": "Argentina"},
        ],
    }, "estados": ["3", "5"]}
    # Estados distintos: con la misma posición, origen, procedencia y estado
    # desde MARIA-8 irían en un solo ítem con dos sub-ítems.
    txt, _ = _por_pdf(monkeypatch, factura).generar_y_descargar()
    ddt = _bloques(txt, "DDT")[0]
    arts = _bloques(txt, "ART")
    assert ddt["MDDTFOB"] == "5000.00" and len(arts) == 2, (ddt, arts)
    assert [a["MARTFOB"] for a in arts] == ["3000.00", "2000.00"]
    # El peso: QARTKGRNET es el neto de toda la línea (respuesta 3 del
    # despachante y D23 de la Dev 2). La máquina chica son 2 unidades con 260 kg
    # la línea: se declaran 260 kg, no 520.
    assert [a["QARTKGRNET"] for a in arts] == ["700.000", "260.000"], arts
    # Flete y seguro, en proporción al FOB de cada producto.
    for a, parte in zip(arts, (0.6, 0.4)):
        assert abs(float(a["MARTFLE"]) - 3221.66 * parte) <= 0.01, a
        assert abs(float(a["MARTASS"]) - 50 * parte) <= 0.01, a
        assert abs(float(a["MARTBASIMP"]) - (float(a["MARTFOB"]) + float(a["MARTFLE"])
                                             + float(a["MARTASS"]))) <= 0.01, a
    assert abs(sum(float(a["MARTFLE"]) for a in arts) - float(ddt["MDDTFLE"])) <= 0.01


@pytest.mark.xfail(strict=True, reason="D23/D25: desde MARIA-7 LDVDREFDOC es el número de factura "
                   "de la pantalla; este sintético carga 002720126 (el número de operación del "
                   "despachante en el archivo real) y el real dice 110")
def test_subitems_dan_la_referencia_de_la_factura_del_archivo_real(monkeypatch):
    p = _por_pdf(monkeypatch, FACTURA_SUBITEMS)
    txt, _ = p.generar_y_descargar()
    assert "LDVDREFDOC=110" in _sin_relleno(txt)


def test_la_pantalla_sola_da_los_subitems_del_archivo_real(monkeypatch):
    """Sin agregarle los subítems al pedido: los carga el panel de subítems
    del paso de NCM (SUBITEMS-1; antes, D24)."""
    txt, _ = _por_pdf(monkeypatch, FACTURA_SUBITEMS).generar_y_descargar()
    assert "CARTSBITEM=S" in _sin_relleno(txt)
