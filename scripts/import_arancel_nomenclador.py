#!/usr/bin/env python3
"""Genera el catálogo local de NCM desde el ZIP oficial de ARCA.

Uso:
    python scripts/import_arancel_nomenclador.py \
      --archive /tmp/arancel.zip --updated-at 2026-07-12

El archivo descargable se publica en:
https://www.arca.gob.ar/aduana/arancelintegrado/
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from proyecto_maria.core.ncm_catalog import DATA_DIR, parse_arca_nomenclador


SOURCE_URL = "https://www.arca.gob.ar/aduana/arancelintegrado/"
DOWNLOAD_URL = SOURCE_URL + "archivos/arancel.zip"
OUTPUT_PATH = DATA_DIR / "ncm_arca.csv.gz"
METADATA_PATH = DATA_DIR / "ncm_arca_metadata.json"


def _find_nomenclador(archive: ZipFile) -> str:
    matches = [name for name in archive.namelist() if "nomenclador" in name.lower()]
    if len(matches) != 1:
        raise ValueError("El ZIP de ARCA debe contener un único archivo nomenclador")
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--updated-at", required=True, help="Fecha publicada por ARCA (AAAA-MM-DD)")
    args = parser.parse_args()

    archive_bytes = args.archive.read_bytes()
    with ZipFile(args.archive) as archive:
        filename = _find_nomenclador(archive)
        # ARCA publica el TXT en Windows-1252.
        lines = archive.read(filename).decode("cp1252").splitlines()

    rows = parse_arca_nomenclador(lines)
    if len(rows) < 1000:
        raise ValueError(f"Catálogo incompleto: sólo se encontraron {len(rows)} NCM")

    with gzip.open(OUTPUT_PATH, "wt", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["codigo", "descripcion", "search_text", "source", "updated_at"])
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "source": "ARCA", "updated_at": args.updated_at})

    METADATA_PATH.write_text(json.dumps({
        "source": "ARCA",
        "source_url": SOURCE_URL,
        "download_url": DOWNLOAD_URL,
        "updated_at": args.updated_at,
        "archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
        "source_file": filename,
        "ncm_count": len(rows),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {len(rows)} NCM en {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
