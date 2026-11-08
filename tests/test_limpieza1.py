"""LIMPIEZA-1: la CI corre la suite entera y el sitio se publica sólo por Railway.

X2 de la auditoría del 2026-10-06: la CI excluía a mano 10 pruebas desde julio
(presupuestos públicos, una de CSRF). Pasaban, pero si se rompían nadie lo veía.
X4: `cloudbuild.yaml` era un segundo camino de publicación, a Google Cloud, que
CDI no usa (DECISIONS.md: el sitio es sólo Railway).
"""
import configparser
import re
import shlex
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CI = REPO / ".github" / "workflows" / "ci.yml"
INI = REPO / "pytest.ini"

# Lo único que la suite y addopts pueden llevar: nada que saque pruebas, que no las
# corra o que cambie la configuración. Una opción nueva se suma acá, a la vista.
PERMITIDAS = re.compile(r"-q|-v|--no-cov|--strict-markers|--tb=(short|long|line|native|auto)"
                        r"|--timeout=\d+|--timeout-method=(thread|signal)|--cov(=[\w.]+)?"
                        r"|--cov-report=[\w:/.-]+|--cov-fail-under=\d+")

# gcr.io y docker.pkg.dev: subir la imagen a Google sin pasar por gcloud.
GOOGLE_CLOUD = re.compile(r"\bgcloud\b|cloudbuild|setup_gcp|deploy-cloud-run|google-github-actions"
                          r"|gcr\.io|docker\.pkg\.dev")


def _no_permitidas(tokens):
    return [tok for tok in tokens if not PERMITIDAS.fullmatch(tok)]


def _tokens(texto):
    lex = shlex.shlex(texto, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    return list(lex)


def _job_tests():
    job = re.search(r"\n  tests:\n(.*?)(?=\n  \S|\Z)", CI.read_text(encoding="utf-8"), re.S)
    assert job, "ci.yml no tiene el job «tests»"
    return job.group(1)


def _comando_de_la_suite():
    paso = re.search(r"- name: Suite completa\n(.*?)(?=\n\s*- name:|\Z)", _job_tests(), re.S)
    assert paso, "ci.yml no tiene el paso «Suite completa»"
    run = re.search(r"\brun:[ \t]*(?:[>|][-+]?)?(.*)", paso.group(1), re.S)
    assert run, "el paso «Suite completa» no tiene run"
    return _tokens(" ".join(run.group(1).split()))


def test_la_ci_corre_la_suite_sin_sacar_pruebas():
    tokens = _comando_de_la_suite()
    # Lo que va antes (un cd, otra variable) cambia qué junta pytest sin nombrar una opción.
    assert tokens[:3] == ["python", "-m", "pytest"], f"la suite no arranca con «python -m pytest»: {tokens}"
    malos = _no_permitidas(tokens[3:])
    assert not malos, f"la suite corre con algo fuera de lo permitido: {malos}"


def test_nada_esconde_el_resultado_de_la_suite():
    """Un paso que no corre, que falla sin poner roja la CI o que corre en otra carpeta."""
    malos = re.findall(r"^\s*-?\s*((?:if|continue-on-error):.*)", _job_tests(), re.M)
    # En todo el archivo: «defaults» también cambia la carpeta de cada run.
    malos += re.findall(r"working-directory:.*", CI.read_text(encoding="utf-8"))
    assert not malos, f"la CI puede esconder el resultado de la suite: {malos}"


def test_pytest_ini_no_saca_pruebas():
    ini = configparser.ConfigParser(interpolation=None)
    ini.read(INI, encoding="utf-8")
    pytest_ini = ini["pytest"]
    malos = _no_permitidas(_tokens(pytest_ini.get("addopts", "")))
    assert not malos, f"pytest.ini suma en addopts algo fuera de lo permitido: {malos}"
    # Cambiar dónde o qué archivos busca también saca pruebas.
    esperado = {"testpaths": "tests", "python_files": "test_*.py", "python_classes": "Test*",
                "python_functions": "test_*"}
    recoleccion = {k: pytest_ini.get(k) for k in esperado}
    assert recoleccion == esperado, (
        f"pytest.ini cambia qué pruebas junta: {recoleccion}"
    )


def test_ci_yml_no_deselecciona_en_ningun_paso():
    texto = CI.read_text(encoding="utf-8")
    assert "--deselect" not in texto and "--ignore" not in texto, (
        "ci.yml saca pruebas con --deselect o --ignore"
    )
    # PYTEST_ADDOPTS suma opciones al comando sin que se vean en el run.
    assert "PYTEST_ADDOPTS" not in texto, "ci.yml le pasa opciones a pytest por PYTEST_ADDOPTS"


def test_no_queda_un_camino_de_publicacion_a_google_cloud():
    """Ni los tres archivos ni otro script o configuración que publique en Google Cloud.

    Los .md y .txt son documentación e historia: no publican nada.
    """
    archivos = subprocess.run(["git", "ls-files", "-z"], cwd=REPO, capture_output=True,
                              check=True).stdout.decode().split("\0")
    # Esta prueba y sus sabotajes nombran a Google Cloud para buscarlo.
    propios = {Path(__file__).resolve().relative_to(REPO).as_posix(),
               "scripts/testing/sabotajes/limpieza1.sh"}
    excluidos = ("docs/archive/", "viejo/", "venv/")
    hallados = []
    for rel in filter(None, archivos):
        if rel in propios or rel.startswith(excluidos) or rel.endswith((".md", ".txt")):
            continue
        if GOOGLE_CLOUD.search(rel):
            hallados.append(rel)
            continue
        ruta = REPO / rel
        if not ruta.is_file() or ruta.stat().st_size > 2_000_000:
            continue
        try:
            texto = ruta.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        m = GOOGLE_CLOUD.search(texto)
        if m:
            hallados.append(f"{rel}: {m.group(0)}")
    assert not hallados, f"queda un camino a Google Cloud: {hallados}"
