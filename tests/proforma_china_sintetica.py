"""EXCEL-3: una proforma china con la misma forma que la del 2026-10-24, con
datos inventados (la real tiene datos de un cliente y no entra al repo).

Filas 1 a 9, los datos del proveedor y del comprador; fila 11, el encabezado;
48 renglones en 4 grupos (un color y un ancho cada uno, un largo por renglón,
el código y la especificación sólo en el primero); después Total, Discount,
Freight cost y otro Total; al final, el texto del pago y el banco.

`python tests/proforma_china_sintetica.py` vuelve a escribir el .xls de
`tests/fixtures/` (hace falta xlwt, que no está en requirements.txt: el .xls
se guarda hecho).
"""

ENCABEZADO = ["Item", "Part No.", "Specification", "Width(m)", "Length (m)", "SQ.MT. (sqm)",
              "QTY (Rolls)", "SM.TOTAL (sqm)", "Unit price (USD/sqm)", "Total Amount(USD)",
              "Gross Weight(kgs)", "Volume(CBM)"]

FILA_ENCABEZADO = 11  # en la planilla, contando desde 1

# (código, especificación, ancho en m, precio por m²)
GRUPOS = [
    ("DT-650-BL", "PVC TARPAULIN 650GSM BLUE", 3.2, 1.35),
    ("DT-650-WH", "PVC TARPAULIN 650GSM WHITE", 3.2, 1.40),
    ("DT-500-GR", "PVC TARPAULIN 500GSM GREY", 2.5, 1.10),
    ("DT-500-GN", "PVC TARPAULIN 500GSM GREEN", 2.0, 1.15),
]
LARGOS = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65]
DESCUENTO = -850.0
FLETE = 6400.0


def renglones() -> list[dict]:
    """Lo que la lectura tiene que devolver, renglón por renglón."""
    out = []
    for g, (codigo, espec, ancho, precio) in enumerate(GRUPOS):
        for k, largo in enumerate(LARGOS):
            rollos = 2 + (g + k) % 5
            m2_rollo = round(ancho * largo, 2)
            m2 = round(m2_rollo * rollos, 2)
            out.append({
                "codigo": codigo, "espec": espec, "ancho": ancho, "largo": largo,
                "m2_rollo": m2_rollo, "rollos": rollos, "m2": m2, "precio": precio,
                "importe": round(m2 * precio, 2), "bruto": round(m2 * 0.68, 2),
                "volumen": round(rollos * 0.05, 3), "primero": k == 0,
            })
    return out


def filas(etiquetas_en: int = 0) -> list[list]:
    """La planilla entera, fila por fila (None es una celda vacía).
    `etiquetas_en`: la columna de Total, Discount y Freight (0 = «Item»,
    2 = «Specification»)."""
    out = [
        ["DEMO TEXTILE (NINGBO) CO., LTD"],
        ["No. 1 Demo Road, Ningbo, China"],
        ["Proforma Invoice"],
        ["Buyer: COMPRADOR DEMO S.A."],
        ["CUIT: 30-00000000-1"],
        ["Date: 2026-10-20"],
        ["P/I No.: DEMO-PI-0001"],
        ["Freight term: CNF Buenos Aires"],
        ["Payment term: T/T"],
        [],
        list(ENCABEZADO),
    ]
    rs = renglones()
    for n, r in enumerate(rs):
        item = None
        if r["primero"]:
            # «1st container» en la columna Item: no es un código (punto 6).
            item = "1st container" if n == 0 else n // len(LARGOS) + 1
        out.append([
            item,
            r["codigo"] if r["primero"] else None,
            r["espec"] if r["primero"] else None,
            r["ancho"], r["largo"], r["m2_rollo"], r["rollos"], r["m2"], r["precio"],
            r["importe"], r["bruto"], r["volumen"],
        ])

    def etiqueta(texto, **valores):
        fila = [None] * len(ENCABEZADO)
        fila[etiquetas_en] = texto
        for nombre, v in valores.items():
            fila[ENCABEZADO.index(nombre)] = v
        return fila

    mercaderia = round(sum(r["importe"] for r in rs), 2)
    out.append(etiqueta("Total", **{
        "QTY (Rolls)": sum(r["rollos"] for r in rs),
        "SM.TOTAL (sqm)": round(sum(r["m2"] for r in rs), 2),
        "Total Amount(USD)": mercaderia,
        "Gross Weight(kgs)": round(sum(r["bruto"] for r in rs), 2),
        "Volume(CBM)": round(sum(r["volumen"] for r in rs), 3)}))
    out.append(etiqueta("Discount", **{"Total Amount(USD)": DESCUENTO}))
    out.append(etiqueta("Freight cost CNF Buenos Aires", **{
        "QTY (Rolls)": 1, "Unit price (USD/sqm)": FLETE, "Total Amount(USD)": FLETE}))
    out.append(etiqueta("Total", **{"Total Amount(USD)": round(mercaderia + DESCUENTO + FLETE, 2)}))
    out.append([])
    out.append(["Payment: 30% T/T in advance, 70% before shipment"])
    out.append(["Beneficiary bank: DEMO BANK OF NINGBO"])
    out.append(["Account No.: 0000 1111 2222 3333"])
    return out


def escribir_xls(ruta: str) -> None:
    import xlwt
    wb = xlwt.Workbook()
    ws = wb.add_sheet("PI")
    for i, fila in enumerate(filas()):
        for j, v in enumerate(fila):
            if v is not None:
                ws.write(i, j, v)
    wb.save(ruta)


if __name__ == "__main__":
    import os
    escribir_xls(os.path.join(os.path.dirname(__file__), "fixtures", "proforma_china_sintetica.xls"))
