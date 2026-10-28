"""LIMPIEZA-1: la CI corre la suite entera y el sitio se publica sólo por Railway.

X2 de la auditoría del 2026-10-06: la CI excluía a mano 10 pruebas desde julio
(presupuestos públicos, una de CSRF). Pasaban, pero si se rompían nadie lo veía.
X4: `cloudbuild.yaml` era un segundo camino de publicación, a Google Cloud, que
CDI no usa (DECISIONS.md: el sitio es sólo Railway).
"""
import re
import shlex
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CI = REPO / ".github" / "workflows" / "ci.yml"

# Opciones de pytest que sacan pruebas de la corrida.
FILTROS_LARGOS = {"--deselect", "--ignore", "--ignore-glob", "--lf", "--last-failed",
                  "--sw", "--stepwise", "--sw-skip", "--stepwise-skip"}
FILTROS_CORTOS = {"-k", "-m"}

# gcr.io y docker.pkg.dev: subir la imagen a Google sin pasar por gcloud.
GOOGLE_CLOUD = re.compile(r"\bgcloud\b|cloudbuild|setup_gcp|deploy-cloud-run|google-github-actions"
                          r"|gcr\.io|docker\.pkg\.dev")


def _filtros(tokens):
    """Los argumentos que sacan pruebas: un filtro o una ruta (corre sólo esa)."""
    malos = []
    for tok in tokens:
        if tok.startswith("--"):
            if tok.split("=")[0] in FILTROS_LARGOS:
                malos.append(tok)
        elif tok.startswith("-"):
            if tok[:2] in FILTROS_CORTOS:
                malos.append(tok)
        else:
            malos.append(tok)
    return malos


def _comando_de_la_suite():
    texto = CI.read_text(encoding="utf-8")
    paso = re.search(r"- name: Suite completa\n(.*?)(?=\n\s*- name:|\n  \S|\Z)", texto, re.S)
    assert paso, "ci.yml no tiene el paso «Suite completa»"
    run = re.search(r"\brun:[ \t]*(?:[>|][-+]?)?(.*)", paso.group(1), re.S)
    assert run, "el paso «Suite completa» no tiene run"
    tokens = shlex.split(" ".join(run.group(1).split()))
    assert "pytest" in tokens, f"el paso «Suite completa» no corre pytest: {tokens}"
    return tokens[tokens.index("pytest") + 1:]


def test_la_ci_corre_la_suite_sin_sacar_pruebas():
    malos = _filtros(_comando_de_la_suite())
    assert not malos, f"la CI saca pruebas de la suite: {malos}"


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
    yo = Path(__file__).resolve().relative_to(REPO).as_posix()
    excluidos = ("docs/archive/", "viejo/", "venv/")
    hallados = []
    for rel in filter(None, archivos):
        if rel == yo or rel.startswith(excluidos) or rel.endswith((".md", ".txt")):
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
