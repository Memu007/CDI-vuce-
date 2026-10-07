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
Además de D23, la pantalla no tiene dónde cargar los subítems (D24) y la
referencia de la factura sale del número de operación (D25).
"""
import io
import json
import re
import sys
import types
import uuid

import pytest
from fastapi.testclient import TestClient

from proyecto_maria import main
from tests.test_maria1a_lectura_factura import _pdf_en_blanco
from tests.test_maria_subitems import REFERENCIA as SUBITEMS_PATH
from tests.test_generar_maria_txt import _GOLDEN_PATH

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
# D24: la pantalla no tiene dónde cargar subítems: se agregan al ítem que ella
#      arma, como los recibe la ruta.
# D25: la referencia de la factura (LDVDREFDOC) sale del número de operación
#      («E126-1»); el archivo real lleva el de la factura («110»).


def _como_sale_por_la_pantalla(real: str, original: str, operation_id: str) -> str:
    """El archivo real con las líneas de D23 (y el CUIT válido) cambiadas."""
    cambios = {
        "NDDTIMMIOE=30999999990": f"NDDTIMMIOE={CUIT_IMPORTADOR}",
        f"IDSO={original}": f"IDSO={operation_id}",
        f"NDDTIMMTRN={original[:5]}": f"NDDTIMMTRN={operation_id[:5]}",
        f"MCPL={original}": f"MCPL={operation_id}",
        f"IDDT={original}": f"IDDT={operation_id}",
        f"IARTESPAPU={original}0001": f"IARTESPAPU={operation_id}0001",
        f"IEXT={original[:5]}-": f"IEXT={operation_id[:5]}-",
    }
    # El MCPL del número va completado a 40 con espacios: el largo no cambia.
    padded = f"MCPL={original:<40}"
    if padded in real:
        cambios.pop(f"MCPL={original}")
        cambios[padded] = f"MCPL={operation_id:<40}"
    for antes, despues in cambios.items():
        assert antes in real, f"el archivo real ya no tiene {antes!r}"
        real = real.replace(antes, despues)
    return real


def _sin_relleno(txt: str) -> list:
    """Líneas sin los espacios del final ni el CR: el archivo de subítems se
    guardó así (LF, sin completar los campos y con un salto al final), el
    generador completa los campos y termina sin salto."""
    return [ln.rstrip() for ln in txt.replace("\r\n", "\n").rstrip("\n").split("\n")]


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
        # Paso de NCM: la NCM elegida queda en it.pieza (ncm.js).
        for it in self.items:
            it["pieza"] = ncm
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
        assert not r.json().get("errores"), r.json().get("errores")

    def _items_para_validar(self):
        """buildItemsForValidation (finalize.js) y semaforo.js."""
        return [{"pieza": str(it.get("pieza") or "").strip(),
                 "descripcion": str(it.get("descripcion") or "").strip(),
                 "origen": str(it.get("origen") or "XX").strip().upper() or "XX",
                 "cantidad": float(it.get("cantidad") or 0),
                 "valor_unitario": float(it.get("valor_unitario") or 0),
                 "peso_unitario": float(it.get("peso_unitario") or 0)} for it in self.items]

    def _cabecera(self):
        """cabeceraParaValidar (finalize.js)."""
        p = self.pedido()
        return {k: p[k] for k in ("moneda", "incoterm", "comprador_cuit", "flete", "seguro")}

    def pedido(self) -> dict:
        """buildMariaRequest (finalize.js), campo por campo."""
        op = self.operacion
        factura = str(op.get("numero_factura") or "").strip()
        assert factura, "sin número de factura la pantalla usa la hora: OP_<fecha>"
        operation_id = "FAC_" + "".join(c for c in factura if c.isalnum() or c in "_-")

        def texto(v):
            return str(v or "").strip()

        def numero(v):
            try:
                return float(v)
            except (TypeError, ValueError):
                return 0.0

        items = [{
            "pieza": texto(it.get("pieza")), "descripcion": texto(it.get("descripcion")),
            "origen": texto(it.get("origen") or "XX").upper() or "XX",
            "cantidad": numero(it.get("cantidad")), "valor_unitario": numero(it.get("valor_unitario")),
            "peso_unitario": numero(it.get("peso_unitario")), "codigo_parte": texto(it.get("codigo_parte")),
            "grupo_id": it.get("grupo_id") or None, "unidad": it.get("unidad") or None,
            "estado": it.get("estado") or None, "iva_adicional": it.get("iva_adicional") or None,
        } for it in self.items]
        # despachante.js, valores(): sin cliente activo no hay propuesta.
        elegidos = op.get("despachante") or {}
        despachante = {
            "banco_bcra": elegidos["banco_bcra"] if elegidos.get("banco_bcra") is not None else "",
            "empresa_digitalizacion": elegidos.get("empresa_digitalizacion") or None,
            "iva_adicional": elegidos.get("iva_adicional") or None,
        }
        # paises_maria.js, resolve(): de la lista sale «222 · PERU» y va «222».
        procedencia = texto(op.get("procedencia"))
        codigo = re.match(r"^(\d{3})(?:\s*[·-].*)?$", procedencia)
        return {
            "operation_id": operation_id, "items": items, **despachante,
            "moneda": texto(op.get("moneda")).upper(), "incoterm": texto(op.get("incoterm")).upper(),
            "cuit_agr": str(op.get("cuit_agr") or self.usuario.get("cuit") or "").replace("-", "").replace(" ", ""),
            "vendedor_nombre": texto(op.get("vendedor_nombre")), "vendedor_id": texto(op.get("vendedor_id")),
            "comprador_nombre": texto(op.get("comprador_nombre")),
            "comprador_cuit": str(op.get("comprador_cuit") or "").replace("-", "").replace(" ", ""),
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
    return p


# ------------------------------------------------------------------ pruebas


def test_pdf_de_punta_a_punta_da_el_archivo_real(monkeypatch):
    txt, operation_id = _por_pdf(monkeypatch, FACTURA).generar_y_descargar()
    assert txt == _como_sale_por_la_pantalla(_leer(_GOLDEN_PATH), "000999001", operation_id)


def test_excel_de_punta_a_punta_da_el_archivo_real():
    txt, operation_id = _por_excel(FACTURA).generar_y_descargar()
    assert txt == _como_sale_por_la_pantalla(_leer(_GOLDEN_PATH), "000999001", operation_id)


@pytest.mark.xfail(strict=True, reason="D23: la pantalla manda «FAC_» + número de "
                   "factura como número de operación")
def test_pdf_de_punta_a_punta_da_el_archivo_real_sin_cambios(monkeypatch):
    txt, _ = _por_pdf(monkeypatch, FACTURA).generar_y_descargar()
    assert txt == _leer(_GOLDEN_PATH).replace("NDDTIMMIOE=30999999990", f"NDDTIMMIOE={CUIT_IMPORTADOR}")


@pytest.mark.parametrize("camino", ["pdf", "excel"])
def test_subitems_de_punta_a_punta_dan_el_archivo_real(monkeypatch, camino):
    p = _por_pdf(monkeypatch, FACTURA_SUBITEMS) if camino == "pdf" else _por_excel(FACTURA_SUBITEMS)
    pedido = p.pedido()
    pedido["items"][0]["subitems"] = FACTURA_SUBITEMS["subitems"]  # D24
    txt, operation_id = p.generar_y_descargar(pedido)
    esperado = _como_sale_por_la_pantalla(_leer(SUBITEMS_PATH), "002720126", operation_id)
    esperado = esperado.replace("LDVDREFDOC=110", f"LDVDREFDOC=E{operation_id[-3:]}-1")  # D25
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
