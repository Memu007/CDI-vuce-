"""Contrato del flujo masivo NCM: una NCM + unir seleccionados."""
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NCM_JS = ROOT / "proyecto_maria" / "static" / "v2" / "screens" / "ncm.js"
COUNTRIES_JS = ROOT / "proyecto_maria" / "static" / "v2" / "paises_maria.js"


def _run_node(case_js: str) -> dict:
    bootstrap = f"""
global.window = {{ CDI: {{
  registerScreen: function() {{}},
  formatNcm: function(raw) {{
    const s = String(raw || '').trim();
    const m = s.match(/[A-Za-z]$/); const letter = m ? m[0].toUpperCase() : '';
    const d = s.replace(/[^0-9]/g, '').slice(0, 11);
    let base = d.length <= 4 ? d : d.length <= 6 ? d.slice(0,4)+'.'+d.slice(4) :
      d.length <= 8 ? d.slice(0,4)+'.'+d.slice(4,6)+'.'+d.slice(6) :
      d.slice(0,4)+'.'+d.slice(4,6)+'.'+d.slice(6,8)+'.'+d.slice(8);
    return base + (letter ? ' ' + letter : '');
  }}
}} }};
global.document = {{ getElementById: () => null, addEventListener: () => {{}}, querySelector: () => null }};
global.requestAnimationFrame = (fn) => fn();
require({json.dumps(str(COUNTRIES_JS))});
require({json.dumps(str(NCM_JS))});
{case_js}
"""
    completed = subprocess.run(
        ["node", "-e", bootstrap], check=True, capture_output=True, text=True
    )
    return json.loads(completed.stdout)


def test_seleccionar_45_asigna_una_ncm_y_un_grupo_en_un_paso():
    result = _run_node("""
const items = Array.from({length: 50}, (_, i) => ({
  pieza: i < 45 ? '' : '9405.10.00', origen: 'CN', unidad: '07', grupo_id: null
}));
const selected = Array.from({length: 45}, (_, i) => i);
const result = window.CDI.ncmBatch.applyNcmAndGroup(items, selected, '84713000900R');
console.log(JSON.stringify({ result, items }));
""")
    assert result["result"]["ok"] is True
    assert result["result"]["count"] == 45
    assert len({item["grupo_id"] for item in result["items"][:45]}) == 1
    assert all(item["pieza"] == "8471.30.00.900 R" for item in result["items"][:45])
    assert all(item["grupo_id"] is None for item in result["items"][45:])


def test_no_sobrescribe_origenes_distintos_al_unir():
    result = _run_node("""
const items = [
  {pieza:'', origen:'CN', unidad:'07', grupo_id:null},
  {pieza:'', origen:'US', unidad:'07', grupo_id:null}
];
const result = window.CDI.ncmBatch.applyNcmAndGroup(items, [0, 1], '84713000900R');
console.log(JSON.stringify({ result, items }));
""")
    assert result["result"]["ok"] is False
    assert result["result"]["title"] == "Origen distinto"
    assert all(item["grupo_id"] is None for item in result["items"])


def test_unir_normaliza_aliases_de_origen_al_codigo_maria():
    result = _run_node("""
const items = [
  {pieza:'', origen:'CN', unidad:'07', grupo_id:null},
  {pieza:'', origen:'China', unidad:'07', grupo_id:null}
];
const result = window.CDI.ncmBatch.applyNcmAndGroup(items, [0, 1], '84713000900R');
console.log(JSON.stringify({ result, items }));
""")
    assert result["result"]["ok"] is True
    assert [item["origen"] for item in result["items"]] == ["310", "310"]


def test_solo_posicion_sim_11_mas_dc_queda_lista():
    result = _run_node("""
console.log(JSON.stringify({
  ncm8: window.CDI.ncmBatch.isValidSimPosition('8471.30.00'),
  ncm8dc: window.CDI.ncmBatch.isValidSimPosition('8471.30.00 R'),
  simSinDc: window.CDI.ncmBatch.isValidSimPosition('8471.30.00.900'),
  simCompleta: window.CDI.ncmBatch.isValidSimPosition('8471.30.00.900 R')
}));
""")
    assert result == {
        "ncm8": False,
        "ncm8dc": False,
        "simSinDc": False,
        "simCompleta": True,
    }


def test_elegir_ncm_8_continua_a_vuce_sin_error_intermedio():
    source = NCM_JS.read_text(encoding="utf-8")

    assert "CDI.toast('Falta la posición SIM'" not in source
    assert "scheduleVucePreview(clean.slice(0, 8), true)" in source
    assert "Buscando posiciones SIM completas…" in source
    assert "Elegir para ver posiciones SIM + DC" in source


def test_varias_posiciones_sim_exigen_eleccion_explicita():
    source = NCM_JS.read_text(encoding="utf-8")

    assert "Elegí una de las ' + simOptions.length + ' posiciones SIM" in source
    assert "hasSeveralSim ? ' disabled' : ''" in source
    assert "button.disabled = !select.value" in source
