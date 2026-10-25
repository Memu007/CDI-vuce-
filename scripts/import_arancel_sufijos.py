#!/usr/bin/env python3
"""Genera la tabla local de sufijos de valor y unidad estadística por
posición SIM (SUFIJOS-1) desde el ZIP del Arancel Integrado de ARCA.

Uso:
    python scripts/import_arancel_sufijos.py \
      --archive docs/pm/datos/arancel_ARCA_07102026.zip

Antes de leer nada comprueba que el SHA-256 del ZIP sea el que anota
`docs/pm/datos/LEEME.md` para ese archivo: si no coincide, frena. No usa la
red. La fecha del arancel sale del nombre de `sufijos_DDMMAAAA.txt` y viaja
con la tabla («arancel de ARCA del 07/10/2026»).

Es aparte de `import_arancel_nomenclador.py` porque aquel reescribe el
catálogo de NCM y sus bajas, y acá sólo se suma la tabla de sufijos.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path
from zipfile import ZipFile

from proyecto_maria.core.ncm_catalog import DATA_DIR
from proyecto_maria.core.sufijos_arca import TABLA, parse_sufijos, parse_unidades

LEEME = Path(__file__).resolve().parents[1] / "docs" / "pm" / "datos" / "LEEME.md"


def sha_del_leeme(leeme: Path, nombre: str) -> str | None:
    """El SHA-256 que el LEEME anota en la fila del archivo `nombre`."""
    for linea in leeme.read_text(encoding="utf-8").splitlines():
        if nombre in linea:
            encontrado = re.search(r"\b[0-9a-f]{64}\b", linea)
            if encontrado:
                return encontrado.group(0)
    return None


def _uno(archive: ZipFile, patron: str) -> str:
    nombres = [n for n in archive.namelist() if re.fullmatch(patron, Path(n).name)]
    if len(nombres) != 1:
        raise ValueError(f"El ZIP de ARCA debe tener un único {patron}")
    return nombres[0]


def armar(archive_path: Path, leeme: Path = LEEME) -> dict:
    datos = archive_path.read_bytes()
    sha = hashlib.sha256(datos).hexdigest()
    esperado = sha_del_leeme(leeme, archive_path.name)
    if esperado is None:
        raise ValueError(f"{leeme} no anota el SHA-256 de {archive_path.name}")
    if sha != esperado:
        raise ValueError(f"El SHA-256 de {archive_path.name} es {sha} y el LEEME dice {esperado}")
    with ZipFile(archive_path) as archive:
        suf = _uno(archive, r"sufijos_\d{8}\.txt")
        nom = _uno(archive, r"nomenclador_\d{8}\.txt")
        # ARCA publica los TXT en Windows-1252.
        sufijos = parse_sufijos(archive.read(suf).decode("cp1252").splitlines())
        unidades = parse_unidades(archive.read(nom).decode("cp1252").splitlines())
    ddmmaaaa = re.search(r"(\d{8})", Path(suf).name).group(1)
    return {
        "fuente": "ARCA, Arancel Integrado",
        "fecha": f"{ddmmaaaa[4:]}-{ddmmaaaa[2:4]}-{ddmmaaaa[:2]}",
        "archive_sha256": sha,
        "archivos": [Path(suf).name, Path(nom).name],
        "sufijos": dict(sorted(sufijos.items())),
        "unidades": dict(sorted(unidades.items())),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--leeme", type=Path, default=LEEME)
    parser.add_argument("--salida", type=Path, default=TABLA)
    args = parser.parse_args(argv)
    try:
        tabla = armar(args.archive, args.leeme)
    except ValueError as error:
        print(f"No se generó la tabla: {error}", file=sys.stderr)
        return 1
    # Sin nombre ni fecha en la cabecera: el mismo ZIP da el mismo .gz byte por byte.
    with open(args.salida, "wb") as crudo, gzip.GzipFile(filename="", fileobj=crudo, mode="wb", mtime=0) as fh:
        fh.write(json.dumps(tabla, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    print(f"{args.salida}: {len(tabla['unidades'])} posiciones SIM, "
          f"{sum(len(v) for v in tabla['sufijos'].values())} sufijos, del {tabla['fecha']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
