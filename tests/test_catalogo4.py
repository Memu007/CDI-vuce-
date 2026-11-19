"""Ante dos productos del proveedor igual de parecidos a lo leído gana el último confirmado y, a la
misma hora o sin fecha, el contenido de la fila: no el orden en que la base las devuelve.

El mismo escenario corre en Postgres con scripts/testing/catalogo4_postgres.py.
"""
import uuid

from proyecto_maria.core.catalog_service import _vendor_key, clave_de_producto
from tests.test_catalogo_largo2 import NCM, _escribir, _match

OTRO = "84714900"
# (leído, a, b, gana): «a» y «b» igual de parecidos a lo leído empatan (gana None); si no, gana «a».
FAMILIA = [
    ("Tornillo acero inox M8", "Tornillo acero inox M8 zincado", "Tornillo acero inox M8 hexagonal", None),
    ("Cable cobre 2,5mm² rojo", "Cable cobre 2,5mm2 rojo flexible", "Cable cobre 2,5mm2 rojo rigido", None),
    ("Bolt Ｍ８ steel zinc", "Bolt M8 steel zinc nut", "Bolt M8 steel zinc washer", None),
    ("Tornillo acero inox M8 zincado", "Tornillo acero inox M8 zincado largo", "Tornillo acero inox M8", "a"),
    ("Tornillo acero inox M8", "Tornillo acero inox M8", "Tornillo acero inox M8 zincado", "a"),
]
# Con «k» vacía, las dos filas a la misma hora; si no, sólo la de clave «k» fechada.
_FECHA = ("update vendor_catalog_products set ultima_vez=case when :k in ('', product_key) "
          "then current_timestamp end where vendor_id=:v")


def sugeridos(client, escribir):
    """Por cada fila de FAMILIA y cada orden de carga, el NCM sugerido después de cada confirmación;
    con las dos filas a la misma hora; con sólo «a» fechada; con sólo «b»; sin fecha; y con las dos
    guardadas juntas en un lote, nuevas y otra vez."""
    vistos = []
    for leido, a, b, _ in FAMILIA:
        ncm = {a: NCM, b: OTRO}
        for orden in ((a, b, a, b), (b, a, b, a)):
            vendor = f"Proveedor catalogo4 {uuid.uuid4().hex[:8]}"
            pasos = []
            for desc in orden:
                r = client.post("/api/ncm/guardar-uso",
                                json={"descripcion": desc, "ncm": ncm[desc], "vendor_name": vendor})
                assert r.status_code == 200, r.text
                pasos.append(_match(client, vendor, leido)["ncm"])
            for clave in ("", clave_de_producto(a), clave_de_producto(b)):
                escribir(_FECHA, k=clave, v=_vendor_key(vendor))
                pasos.append(_match(client, vendor, leido)["ncm"])
            escribir("update vendor_catalog_products set ultima_vez=null where vendor_id=:v", v=_vendor_key(vendor))
            pasos.append(_match(client, vendor, leido)["ncm"])
            lote = f"{vendor} lote"
            for _ in range(2):
                r = client.post(f"/api/catalog/{_vendor_key(lote)}/productos", json={
                    "vendor_name": lote, "productos": [{"descripcion": d, "ncm": ncm[d]} for d in orden[:2]]})
                assert r.status_code == 200, r.text
                pasos.append(_match(client, lote, leido)["ncm"])
            vistos.append(pasos)
    return vistos


def errores(vistos):
    """Lo que no sale como se espera: (fila de FAMILIA, orden, sugeridos)."""
    malos = []
    for n, (leido, a, b, gana) in enumerate(FAMILIA):
        ncm = {a: NCM, b: OTRO}
        uno, otro = vistos[2 * n], vistos[2 * n + 1]
        misma_hora, sin_fecha, lote, lote_otra_vez = (
            p if p in (NCM, OTRO) else "uno de los dos" for p in (uno[4], uno[7], uno[8], uno[9]))
        for orden, pasos in zip(((a, b, a, b), (b, a, b, a)), (uno, otro)):
            # Sin empate, «a» apenas está cargada; con empate, la recién confirmada, la fechada y, a
            # la misma hora, sin fecha o en un lote, la misma en los dos órdenes de carga.
            esperado = ([ncm[a if a in orden[:i + 1] else b] for i in range(4)] + [NCM] * 6 if gana else
                        [ncm[d] for d in orden] + [misma_hora, NCM, OTRO, sin_fecha, lote, lote_otra_vez])
            if pasos != esperado:
                malos.append((leido, orden[0], pasos))
    return malos


def test_un_empate_de_parecido_no_depende_del_orden_de_las_filas(client):
    assert errores(sugeridos(client, _escribir)) == []
