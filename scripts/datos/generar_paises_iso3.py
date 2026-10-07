"""Genera proyecto_maria/core/paises_iso3.py desde la norma ISO 3166-1.

Uso (una sola vez, fuera del producto; pycountry NO es dependencia):
    python -m venv /tmp/venv-iso && /tmp/venv-iso/bin/pip install pycountry
    /tmp/venv-iso/bin/python scripts/datos/generar_paises_iso3.py

Sólo entran los países cuyo código de dos letras está en la tabla oficial
VUCE (`PAISES_INDEC` de core/maria_generator.py): el código MARIA lo sigue
dando esa tabla; esto sólo traduce tres letras a dos.
"""
import ast
import importlib.metadata
import pathlib

import pycountry

RAIZ = pathlib.Path(__file__).resolve().parents[2]
GEN = RAIZ / "proyecto_maria" / "core" / "maria_generator.py"
SALIDA = RAIZ / "proyecto_maria" / "core" / "paises_iso3.py"

# La tabla oficial se lee del código fuente sin importar el producto.
arbol = ast.parse(GEN.read_text(encoding="utf-8"))
oficial = {}
for nodo in arbol.body:
    if isinstance(nodo, ast.Assign) and getattr(nodo.targets[0], "id", "") == "PAISES_INDEC" \
            and isinstance(nodo.value, ast.Dict):
        oficial = {k.value: v.value for k, v in zip(nodo.value.keys, nodo.value.values)}
        break
dos_letras = {k for k in oficial if len(k) == 2 and k.isalpha() and k.isupper()}

pares = sorted(
    (c.alpha_3, c.alpha_2) for c in pycountry.countries if c.alpha_2 in dos_letras
)
version = importlib.metadata.version("pycountry")
lineas = [
    '"""Códigos ISO 3166-1 de tres letras → dos letras.',
    "",
    f"Generado por scripts/datos/generar_paises_iso3.py desde pycountry {version}",
    "(norma ISO 3166-1). Sólo países cuyo código de dos letras está en la tabla",
    "oficial VUCE (`PAISES_INDEC`). No editar a mano: regenerar.",
    '"""',
    "",
    "ISO3_A_ISO2 = {",
]
lineas += [f'    "{a3}": "{a2}",' for a3, a2 in pares]
lineas += ["}", ""]
SALIDA.write_text("\n".join(lineas), encoding="utf-8")
print(f"{len(pares)} códigos escritos en {SALIDA.relative_to(RAIZ)}; "
      f"{len(dos_letras) - len(pares)} de dos letras sin par ISO: "
      f"{sorted(dos_letras - {a2 for _, a2 in pares})}")
