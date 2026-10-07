"""Escenario de RENDIMIENTO-1b, para correr en un proceso aparte.

Cuatro subidas en paralelo de un PDF armado (un /Length que se apunta a sí
mismo: pdfminer no termina nunca de leerlo) y después una subida buena.
Imprime una línea JSON con lo que pasó. Lo corre tests/test_rendimiento1b.py
con un tiempo límite: si la lectura vuelve a colgarse, este proceso no
termina y la prueba lo informa en vez de colgar la suite.
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("ENVIRONMENT", "testing")

import httpx  # noqa: E402

from proyecto_maria import main  # noqa: E402

PDF_ARMADO = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 1 1] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 5 0 R >>
stream
BT ET
endstream
endobj
5 0 obj
5 0 R
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000198 00000 n 
0000000256 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
277
%%EOF
"""
PDF_BUENO = (Path(__file__).parent / "test_factura.pdf").read_bytes()


def preparar():
    from proyecto_maria.core import ai_quota
    from proyecto_maria.core.rate_limit import limiter
    limiter.enabled = False
    main.lectura_automatica_disponible = lambda: True
    ai_quota.enforce_pdf_quota = lambda *a, **k: None
    main.app.dependency_overrides[main.get_current_user] = lambda: {
        "username": "rend1b", "roles": ["operador"], "effective_owner": "rend1b",
        "plan": "premium", "billing_status": "active"}
    # La lectura con IA, simulada: devuelve ítems sin vendedor, así la
    # adivinanza del vendedor lee el texto del PDF.
    main.process_pdf = lambda *_: {"items": [{"descripcion": "x"}], "operacion": {}}


async def correr():
    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://t", timeout=60) as c:
        def subir(datos, nombre):
            return c.post("/upload_pdf/public", files={"file": (nombre, datos, "application/pdf")})
        t0 = time.monotonic()
        armados = await asyncio.gather(*[subir(PDF_ARMADO, f"armado{i}.pdf") for i in range(4)])
        t1 = time.monotonic()
        bueno = await subir(PDF_BUENO, "bueno.pdf")
        t2 = time.monotonic()
        return {
            "armados": [r.status_code for r in armados],
            "armados_s": round(t1 - t0, 2),
            "bueno": bueno.status_code,
            "bueno_s": round(t2 - t1, 2),
        }


if __name__ == "__main__":
    preparar()
    print(json.dumps(asyncio.run(correr())), flush=True)
    # Sin esperar a los hilos: si quedó alguno colgado, que se note en el
    # tiempo límite de quien corre este script y no en una espera eterna.
    os._exit(0)
