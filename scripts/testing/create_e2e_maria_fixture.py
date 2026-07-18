"""Genera la planilla determinística usada por el E2E de MARIA.

El archivo se escribe exclusivamente en el directorio temporal que recibe el
runner. Así no hay PDFs, planillas ni datos de prueba persistentes en el repo.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from openpyxl import Workbook


HEADERS = [
    "PIEZA",
    "DESCRIPCION",
    "ORIGEN",
    "CANTIDAD",
    "VALOR UNITARIO",
    "PESO UNITARIO",
]

ROWS = [
    ["84713000", "Modulo de prueba E2E A", "US", 1, 100.00, 0.40],
    ["84713000", "Modulo de prueba E2E B", "US", 1, 100.00, 0.40],
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Items"
    sheet.append(HEADERS)
    for row in ROWS:
        sheet.append(row)
    workbook.save(args.output)


if __name__ == "__main__":
    main()
