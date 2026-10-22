"""Reproduce la pérdida de metadatos al normalizar una respuesta simulada.

No procesa documentos reales ni mide la precisión del modelo. No usa red,
no carga .env y sustituye tanto Gemini como el renderizador del PDF.
Uso: python3 auditoria_documentos_sinteticos.py RUTA_REPO [SHA ...]
"""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import types

sys.dont_write_bytecode = True
repo = Path(sys.argv[1]).resolve()
refs = sys.argv[2:] or ["a9b03cf", "99f3625"]
sys.path.insert(0, str(repo))
os.environ["GEMINI_API_KEY"] = "test-key"
os.environ["ENABLE_PDF_LLM_FALLBACK"] = "true"

dotenv = types.ModuleType("dotenv")
dotenv.load_dotenv = lambda *a, **k: None
sys.modules["dotenv"] = dotenv


class Page:
    def get_pixmap(self, **kwargs):
        return types.SimpleNamespace(tobytes=lambda *a: b"synthetic-image")


class Document:
    def __len__(self):
        return 1

    def __getitem__(self, index):
        return Page()

    def close(self):
        pass


fitz = types.ModuleType("fitz")
fitz.open = lambda **k: Document()
fitz.Matrix = lambda *a: a
sys.modules["fitz"] = fitz
pil = types.ModuleType("PIL")
pil.Image = object
sys.modules["PIL"] = pil

payload = {
    "tipo_documento": "despacho_oficializado",
    "operacion": {
        "tipo_documento": "despacho_oficializado",
        "tipo_destinacion": "EC02",
        "aduana_codigo": "073",
        "numero_factura": "",
        "fecha_emision": "01/01/2026",
        "vendedor_nombre": "AGENTE SINTETICO",
        "comprador_nombre": "EMPRESA SINTETICA",
        "moneda": "EUR",
        "incoterm": "FOB",
    },
    "items": [{
        "descripcion": "Instrumento sintetico",
        "cantidad": 2,
        "valor_unitario": 10,
        "peso_kg": 1.25,
        "peso_unitario": 1.25,
        "peso_bruto": 1.25,
        "peso_neto": 0.20,
        "origen": "IT",
    }],
}
google = types.ModuleType("google")
genai = types.ModuleType("google.generativeai")
google.generativeai = genai
genai.configure = lambda **k: None
genai.GenerativeModel = lambda *a, **k: types.SimpleNamespace(
    generate_content=lambda *a, **k: types.SimpleNamespace(text=json.dumps(payload))
)
sys.modules["google"] = google
sys.modules["google.generativeai"] = genai

original_sleep = time.sleep
time.sleep = lambda *a: None
try:
    for ref in refs:
        path = "proyecto_maria/pdf_extractor.py"
        source = subprocess.check_output(
            ["git", "-C", str(repo), "show", f"{ref}:{path}"], text=True
        )
        namespace = {"__file__": str(repo / path)}
        exec(compile(source, path, "exec"), namespace)
        with contextlib.redirect_stdout(io.StringIO()):
            result = namespace["process_pdf"](b"synthetic-pdf-only")
        operation = result["operacion"]
        item = result["items"][0]
        assert "tipo_documento" not in operation
        assert "tipo_destinacion" not in operation
        assert "aduana_codigo" not in operation
        assert operation["fecha_emision"] == "01/01/2026"
        assert operation["vendedor_nombre"] == "AGENTE SINTETICO"
        assert item["peso_unitario"] == 1.25
        assert "peso_neto" not in item
        assert not operation.get("avisos_peso")
        print(ref, "REPRODUCIDO: pierde clase documental, EC02 y aduana; acepta fecha, rol y peso sin contraste documental")
finally:
    time.sleep = original_sleep
