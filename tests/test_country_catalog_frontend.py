"""Contrato de la tabla de países visible en la pantalla NCM."""
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COUNTRIES_JS = ROOT / "proyecto_maria" / "static" / "v2" / "paises_maria.js"


def test_country_catalog_uses_maria_codes_and_legacy_aliases():
    bootstrap = f"""
global.window = {{ CDI: {{}} }};
require({json.dumps(str(COUNTRIES_JS))});
const countries = window.CDI.paisesMaria;
const result = {{
  count: countries.countries.length,
  chinaFromIso: countries.resolve('CN'),
  chinaFromName: countries.resolve('China'),
  chinaFromLabel: countries.resolve('310 · CHINA'),
  vietnam: countries.resolve('Vietnam'),
  label: countries.label('CN'),
  invalid: countries.resolve('XX')
}};
console.log(JSON.stringify(result));
"""
    completed = subprocess.run(
        ["node", "-e", bootstrap], check=True, capture_output=True, text=True
    )
    result = json.loads(completed.stdout)

    assert result == {
        "count": 309,
        "chinaFromIso": "310",
        "chinaFromName": "310",
        "chinaFromLabel": "310",
        "vietnam": "337",
        "label": "310 · CHINA",
        "invalid": "",
    }
