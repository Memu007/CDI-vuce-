#!/usr/bin/env python3
"""DOC-1: negativos aislados. Requiere el Python del entorno de pruebas."""
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
MUTACIONES = [
    ("clasificacion", "proyecto_maria/pdf_extractor.py",
     "    documento = result.get(\"documento\") if isinstance(result, dict) else None",
     "    return {\"tipo\": \"factura_comercial\", \"operacion\": \"importacion\", \"destinacion\": \"IC04\"}\n    documento = result.get(\"documento\") if isinstance(result, dict) else None",
     "test_rechazo_no_reintenta_ni_cae_fallback"),
    ("servidor", "proyecto_maria/main.py",
     "        return destinacion_del_txt(tipo_destinacion, exportacion)",
     "        return str(tipo_destinacion or \"\")", "test_ec_directa_nunca_entra_a_importacion"),
    ("generador", "proyecto_maria/core/maria_generator.py",
     "    tipo_destinacion = destinacion_del_txt(tipo_destinacion)",
     "    tipo_destinacion = destinacion_del_txt(tipo_destinacion, es_exportacion(tipo_destinacion))",
     "test_generador_directo_rechaza_ec"),
]
archive = subprocess.check_output(["git", "archive", "HEAD"], cwd=ROOT)
for nombre, archivo, original, cambio, caso in MUTACIONES:
    with tempfile.TemporaryDirectory(prefix="cdi_doc1_negativo_") as directory:
        destino = Path(directory)
        with tarfile.open(fileobj=io.BytesIO(archive)) as snapshot:
            snapshot.extractall(destino, filter="data")
        path = destino / archivo
        text = path.read_text()
        assert text.count(original) == 1, f"Patrón cambiado: {nombre}"
        path.write_text(text.replace(original, cambio))
        env = dict(os.environ, GEMINI_API_KEY="test-key", VUCE_MODE="fake", TARIFAR_MODE="fake",
                   AFIP_MODE="fake", DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares")
        resultado = subprocess.run([sys.executable, "-m", "pytest", "tests/test_doc1_documentos.py",
                                    "-k", caso, "-o", "addopts=", "--timeout=120", "-q"],
                                   cwd=destino, env=env, text=True, capture_output=True, timeout=150)
        salida = resultado.stdout + resultado.stderr
        assert resultado.returncode == 1 and f"FAILED tests/test_doc1_documentos.py::{caso}" in salida, salida
        assert "DID NOT RAISE" in salida or "AssertionError" in salida, salida
        print(f"DOC-1 negativo {nombre}: rojo por guarda desactivada (OK)")
