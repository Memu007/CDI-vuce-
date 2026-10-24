"""Reproduce destinación EC02 con indicador de importación en ambos SHA.

Sólo ejecuta el generador con datos inventados; no guarda TXT ni usa red.
Uso: python3 auditoria_generador_sintetico.py RUTA_REPO [SHA ...]
"""
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
repo = Path(sys.argv[1]).resolve()
refs = sys.argv[2:] or ["a9b03cf", "99f3625"]
for ref in refs:
    path = "proyecto_maria/core/maria_generator.py"
    source = subprocess.check_output(
        ["git", "-C", str(repo), "show", f"{ref}:{path}"], text=True
    )
    namespace = {"__file__": str(repo / path)}
    exec(compile(source, path, "exec"), namespace)
    args = dict(
        operation_id="SYNTHETIC-001",
        items=[{
            "pieza": "84714900100D", "descripcion": "Producto ficticio",
            "origen": "IT", "cantidad": 2, "valor_unitario": 10,
            "peso_unitario": 1.25,
        }],
        moneda="EUR", incoterm="FOB", sbt_sufijo_valor="AA(SINTETICO)-",
        fecha_emision="01/01/2026",
    )
    default = namespace["generate_maria_txt"](**args).splitlines()
    assert "ISTA=IC04" in default
    assert "CDDTTYPDEC=IC04" in default
    assert "CDDTIMPEXP=I" in default
    explicit = namespace["generate_maria_txt"](**args, tipo_destinacion="EC02").splitlines()
    assert "ISTA=EC02" in explicit
    assert "CDDTTYPDEC=EC02" in explicit
    assert "CDDTIMPEXP=I" in explicit
    print(ref, "REPRODUCIDO: default IC04/I; EC02 explícita conserva CDDTIMPEXP=I")
    print(ref, next(line for line in explicit if line.startswith("QARTKGRNET=")))
