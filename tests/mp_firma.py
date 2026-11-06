"""Avisos de Mercado Pago firmados como los manda su panel de Webhooks."""
import hashlib
import hmac
import json


def aviso_firmado(tipo: str, data_id: str, secreto: str, req_id: str = "req-1") -> dict:
    """Los argumentos de `client.post` para un aviso con `x-signature` válida."""
    ts = "1700000000"
    v1 = hmac.new(secreto.encode(), f"id:{data_id};request-id:{req_id};ts:{ts};".encode(),
                  hashlib.sha256).hexdigest()
    return {"content": json.dumps({"type": tipo, "data": {"id": data_id}}),
            "headers": {"x-signature": f"ts={ts},v1={v1}", "x-request-id": req_id,
                        "content-type": "application/json"}}
