"""Reproduce destinación EC02 con indicador de importación en cada SHA.

Sólo ejecuta el generador con datos inventados; no guarda TXT ni usa red.
En los SHA viejos la EC02 explícita sale con CDDTIMPEXP=I (el hallazgo);
desde MARIA-7 el generador la rechaza y pide el CUIT del despachante.
Uso: python3 auditoria_generador_sintetico.py RUTA_REPO [SHA ...]
"""
from pathlib import Path
import inspect
import subprocess
import sys

sys.dont_write_bytecode = True
repo = Path(sys.argv[1]).resolve()
refs = sys.argv[2:] or ["a9b03cf", "99f3625", "HEAD"]
CUIT_FICTICIO = "20111111112"  # inventado, dígito verificador válido
for ref in refs:
    path = "proyecto_maria/core/maria_generator.py"
    source = subprocess.check_output(
        ["git", "-C", str(repo), "show", f"{ref}:{path}"], text=True
    )
    namespace = {"__file__": str(repo / path)}
    exec(compile(source, path, "exec"), namespace)
    generar = namespace["generate_maria_txt"]
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
    if "cuit_agr" in inspect.signature(generar).parameters:
        args["cuit_agr"] = CUIT_FICTICIO
    default = generar(**args).splitlines()
    assert "ISTA=IC04" in default
    assert "CDDTTYPDEC=IC04" in default
    assert "CDDTIMPEXP=I" in default
    try:
        explicit = generar(**args, tipo_destinacion="EC02").splitlines()
    except ValueError as error:
        assert "exportación" in str(error), error
        print(ref, "CORREGIDO: default IC04/I; EC02 explícita rechazada:", error)
        continue
    assert "ISTA=EC02" in explicit
    assert "CDDTTYPDEC=EC02" in explicit
    assert "CDDTIMPEXP=I" in explicit
    print(ref, "REPRODUCIDO: default IC04/I; EC02 explícita conserva CDDTIMPEXP=I")
    print(ref, next(line for line in explicit if line.startswith("QARTKGRNET=")))
