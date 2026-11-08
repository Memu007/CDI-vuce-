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

# Opciones de pytest que sacan pruebas de la corrida, no las corren o cambian la configuración.
LARGAS_CON_VALOR = {"--deselect", "--ignore", "--ignore-glob", "--override-ini", "--config-file"}
LARGAS_SIN_VALOR = {"--lf", "--last-failed", "--sw", "--stepwise", "--sw-skip", "--stepwise-skip",
                    "--co", "--collect-only", "--setup-only", "--setup-plan"}
CORTAS_MALAS = set("kmoc")
# En un grupo como -vk, la primera corta que toma valor se lleva el resto o el token siguiente.
CORTAS_CON_VALOR = CORTAS_MALAS | set("pWrn")
OPERADORES = set("|&;()<>")

# gcr.io y docker.pkg.dev: subir la imagen a Google sin pasar por gcloud.
GOOGLE_CLOUD = re.compile(r"\bgcloud\b|cloudbuild|setup_gcp|deploy-cloud-run|google-github-actions"
                          r"|gcr\.io|docker\.pkg\.dev")


def _filtros(tokens):
    """Los argumentos que sacan pruebas: un filtro con su valor, una ruta que existe
    (corre sólo esa) o un operador de shell, que cambia qué cuenta como resultado."""
    malos, sigue = [], None
    for tok in tokens:
        if sigue is not None:
            if sigue:
                malos.append(tok)
            sigue = None
        elif set(tok) <= OPERADORES:
            malos.append(tok)
        elif tok.startswith("--"):
            nombre = tok.split("=")[0]
            if nombre in LARGAS_SIN_VALOR or nombre in LARGAS_CON_VALOR:
                malos.append(tok)
                if nombre == tok and nombre in LARGAS_CON_VALOR:
                    sigue = True
        elif tok.startswith("-"):
            for i, letra in enumerate(tok[1:], start=2):
                if letra in CORTAS_CON_VALOR:
                    if letra in CORTAS_MALAS:
                        malos.append(tok)
                    if i == len(tok):
                        sigue = letra in CORTAS_MALAS
                    break
        elif (REPO / tok.split("::")[0]).exists():
            malos.append(tok)
    return malos


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
    tokens = _tokens(" ".join(run.group(1).split()))
    assert "pytest" in tokens, f"el paso «Suite completa» no corre pytest: {tokens}"
    return tokens[tokens.index("pytest") + 1:]


def test_la_ci_corre_la_suite_sin_sacar_pruebas():
    malos = _filtros(_comando_de_la_suite())
    assert not malos, f"la CI saca pruebas de la suite: {malos}"


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
    malos = _filtros(_tokens(pytest_ini.get("addopts", "")))
    assert not malos, f"pytest.ini saca pruebas en addopts: {malos}"
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
