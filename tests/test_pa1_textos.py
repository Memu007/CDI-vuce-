"""PA-1: en pantallas, «NCM» pasa a «Posición arancelaria (PA SIM)» donde se
habla de la posición de 11 dígitos con su letra (reunión del 24/10).

Donde el texto habla a propósito de los 8 dígitos de la nomenclatura (la NCM
que se busca, la que trae VUCE, el capítulo de las notas, la calculadora,
la planilla maestra), «NCM» queda: cambiarlo diría algo falso.
"""
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1] / "proyecto_maria"
HTML = "templates/dashboard_v2.html"
NCM_JS = "static/v2/screens/ncm.js"
CLIENTES_JS = "static/v2/screens/clientes.js"
CATALOGO_JS = "static/v2/screens/catalogo.js"


def _leer(rel):
    return (RAIZ / rel).read_text(encoding="utf-8")


# (archivo, texto nuevo, texto viejo que no tiene que quedar)
CAMBIAN = [
    (HTML, '<span class="num">3</span> PA SIM</div>', '<span class="num">3</span> NCM</div>'),
    (HTML, "Continuar a PA SIM", "Continuar a NCM"),
    (HTML, ">Volver a PA SIM<", ">Volver a NCM<"),
    (HTML, "recuerda las posiciones arancelarias (PA SIM) y orígenes confirmados",
     "recuerda los NCM y orígenes confirmados"),
    (HTML, 'aria-label="Asistente de posición arancelaria (PA SIM)"', 'aria-label="Asistente NCM"'),
    (NCM_JS, "scheduleUndoClear('PA SIM ' + formatted", "scheduleUndoClear('NCM ' + formatted"),
    (NCM_JS, "scheduleUndoClear('PA SIM ' + result.ncm", "scheduleUndoClear('NCM ' + result.ncm"),
    (NCM_JS, "</strong> posiciones arancelarias (PA SIM)' + detailText", "</strong> NCM' + detailText"),
    (NCM_JS, "te sugerimos las posiciones arancelarias (PA SIM) que ya usó antes",
     "te sugerimos los NCM que ya usó antes"),
    (NCM_JS, 'title="PA SIM sugerida desde ', 'title="NCM sugerido desde '),
    (NCM_JS, "'Guardamos esta posición arancelaria (PA SIM) para '", "'Guardamos este NCM para '"),
    (NCM_JS, 'title="Refrescar desde el asistente de posición arancelaria"',
     'title="Refrescar desde el asistente NCM"'),
    (CLIENTES_JS, "pieza: 'Posición arancelaria (PA SIM)',", "pieza: 'NCM / Pieza',"),
    (CLIENTES_JS, 'title="Posición arancelaria (PA SIM)"', 'value="\' + CDI.escapeHtml(p.ncm) + \'" title="NCM"'),
    (CATALOGO_JS, "'<span>PA SIM</span>' +", "'<span>NCM</span>' +"),
]

# Hablan de los 8 dígitos: quedan con «NCM». (archivo, texto, cuántas veces):
# con el número exacto, cambiar una sola de varias apariciones también es rojo.
QUEDAN = [
    (HTML, "La NCM tiene 8 dígitos. Para declarar en MARIA completá 3 dígitos SIM y la letra DC.", 1),
    (HTML, "<small>NCM 8 + SIM 3 + DC</small>", 1),
    (HTML, "NCM 8 + SIM 3 + letra DC", 1),
    (HTML, '<label class="field-label" for="calcNcm">NCM</label>', 1),
    (HTML, "Recordatorios privados del capítulo NCM", 1),
    (HTML, "Importar planilla maestra de NCMs", 2),
    (NCM_JS, "La NCM de 8 dígitos todavía no fue asignada.", 1),
    # La NCM de 8 que se le consulta a VUCE: al cargar, sin respuesta y con respuesta.
    (NCM_JS, "'<span class=\"spotlight-vuce-ncm\">NCM ' + CDI.escapeHtml(formatted)", 2),
    (NCM_JS, "'<span class=\"spotlight-vuce-ncm\">NCM ' + CDI.escapeHtml(formattedBaseNcm)", 1),
    (NCM_JS, "La posición SIM debe tener 11 dígitos: NCM (8) + detalle SIM (3).", 1),
]


@pytest.mark.parametrize("archivo,nuevo,viejo", CAMBIAN, ids=[c[1][:50] for c in CAMBIAN])
def test_la_posicion_completa_se_llama_pa_sim(archivo, nuevo, viejo):
    texto = _leer(archivo)
    assert viejo not in texto, f"{archivo} sigue diciendo {viejo!r}"
    assert texto.count(nuevo) == 1, f"{archivo} no dice {nuevo!r}"


@pytest.mark.parametrize("archivo,texto,veces", QUEDAN, ids=[q[1][:50] for q in QUEDAN])
def test_los_8_digitos_siguen_siendo_ncm(archivo, texto, veces):
    hay = _leer(archivo).count(texto)
    assert hay == veces, f"{archivo} ya no dice {texto!r} ({hay} de {veces} veces)"
