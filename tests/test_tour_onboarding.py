"""Contrato del tour de ingreso del dashboard v2.

El tour debe ser corto y, sobre todo, no prometer automatizaciones que el
flujo PDF -> MARIA no realiza.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "proyecto_maria" / "templates" / "dashboard_v2.html"
TOUR_JS = ROOT / "proyecto_maria" / "static" / "v2" / "screens" / "tour.js"
NCM_JS = ROOT / "proyecto_maria" / "static" / "v2" / "screens" / "ncm.js"
APP_JS = ROOT / "proyecto_maria" / "static" / "v2" / "app_v2.js"
APP_CSS = ROOT / "proyecto_maria" / "static" / "v2" / "app_v2.css"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_tour_has_four_truthful_steps_and_one_welcome():
    html = _read(TEMPLATE)

    assert html.count('<article class="tour-welcome-slide') == 4
    assert 'id="tourWelcomeCounter">1 / 4<' in html
    assert "Subir mi primera factura" in html
    assert "Saltar por ahora" in html
    assert 'id="welcomeCard"' not in html

    for expected in (
        "Subí la factura",
        "Revisá lo importante",
        "Algunos pesos pueden venir estimados",
        "NCM 8 + SIM 3 + letra DC",
        "CDI recuerda lo confirmado",
        "Al generar el TXT guarda la operación",
        "Completá el SBT",
        "validalo en Kit MARIA antes de oficializar",
    ):
        assert expected in html

    for false_promise in (
        "Vos no tipeás nada",
        "se guarda automáticamente",
        "El cliente aparece solo",
        "Sin errores",
        "Dejá notas por cliente",
    ):
        assert false_promise not in html


def test_tour_state_navigation_and_upload_focus_contract():
    js = _read(TOUR_JS)

    assert "const KEY = 'cdi_tour_v3'" in js
    assert "const LEGACY_KEY = 'cdi_tour_v2'" in js
    assert "const WELCOME_SLIDES_COUNT = 4" in js
    assert 'data-tour-slide="' in js
    assert 'aria-current="step"' in js
    assert "event.key === 'ArrowRight'" in js
    assert "event.key === 'ArrowLeft'" in js
    assert "event.key === 'Escape'" in js
    assert "document.getElementById('uploadPickBtn')" in js
    assert "upload.focus()" in js


def test_legacy_welcome_logic_is_gone_and_mobile_modal_can_scroll():
    app_js = _read(APP_JS)
    css = _read(APP_CSS)

    assert "setupWelcomeCard" not in app_js
    assert "cdi_welcome_seen" not in app_js
    assert "max-height: calc(100vh - 20px)" in css
    assert "overflow-y: auto" in css


def test_contextual_ncm_hint_keeps_human_confirmation_explicit():
    html = _read(TEMPLATE)
    ncm_js = _read(NCM_JS)

    assert "CDI prepara los datos para que los revises" in html
    assert "CDI propone y vos confirmás" in ncm_js
