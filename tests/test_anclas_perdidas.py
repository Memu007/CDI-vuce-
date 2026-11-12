"""El conteo de anclas de `scripts/testing/anclas_perdidas.py`, sobre guiones
inventados que se le dan en memoria: no lee el repositorio ni corre nada."""
import pytest

from scripts.testing.anclas_perdidas import Guion, clase, medir

GUION = "scripts/testing/sabotajes/inventado.sh"
REEMPLAZAR = '''reemplazar() {
  python3 - "$@" <<'PY'
import sys
p, viejo, nuevo = sys.argv[1:4]
s = open(p).read()
open(p, "w").write(s.replace(viejo, nuevo))
PY
}
'''
CON_VECES = '''reemplazar() {
  python3 - "$@" <<'PY'
import sys
p, viejo, nuevo = sys.argv[1:4]
veces = int(sys.argv[4]) if len(sys.argv) > 4 else 1
s = open(p).read()
assert s.count(viejo) == veces
open(p, "w").write(s.replace(viejo, nuevo))
PY
}
'''
ARCHIVOS = {"a.py": "uno = 1\ndos = 2\ndos = 2\ncafé = 'A'\n"}


def filas(guion, archivos=ARCHIVOS):
    arbol = {GUION: guion, **archivos}
    return list(medir(Guion(GUION, arbol.get), arbol.get))


def clases(guion, archivos=ARCHIVOS):
    return [clase(fila) for fila in filas(guion, archivos)]


@pytest.mark.parametrize("llamada, esperada", [
    ('reemplazar a.py "uno = 1" "uno = 0"', "está"),
    ('reemplazar a.py "tres = 3" "tres = 0"', "perdida, una línea"),
    ("reemplazar a.py $'uno = 1\\ntres = 3' x", "perdida, varias líneas"),
    ('reemplazar a.py "dos = 2" "dos = 0"', "otra cantidad"),
    ('reemplazar no_esta.py "uno = 1" "uno = 0"', "perdida, una línea"),
    ('reemplazar a.py "$(cat ancla.txt)" "uno = 0"', "no medido"),
], ids=["esta", "perdida", "perdida_varias_lineas", "esta_dos_veces", "sin_archivo", "sin_ejecutar"])
def test_cada_llamada_da_una_fila_con_su_clase(llamada, esperada):
    guion = REEMPLAZAR + llamada + "\n"

    [fila] = filas(guion)

    assert clase(fila) == esperada
    assert fila[:2] == (GUION, guion.count("\n"))


@pytest.mark.parametrize("definicion", [
    "if true; then\n  " + REEMPLAZAR.replace("\n}", "\n  }") + "fi\n",
    REEMPLAZAR.replace("reemplazar() {", "function reemplazar {"),
    REEMPLAZAR.replace("reemplazar() {", "function reemplazar() {"),
    REEMPLAZAR.replace("  python3", "  { true; }\n  python3"),
    REEMPLAZAR.replace("  python3", "  LC_ALL=C python3"),
], ids=["con_sangria", "function_sin_parentesis", "function_con_parentesis", "llaves_adentro",
        "variable_adelante"])
def test_la_llamada_se_cuenta_como_sea_que_esté_escrita_la_función(definicion):
    assert clases(definicion + 'reemplazar a.py "uno = 1" "uno = 0"\n') == ["está"]


@pytest.mark.parametrize("llamada, esperadas", [
    ('reemplazar a.py "uno = 1" "uno = 0" 2>/dev/null', ["está"]),
    ('reemplazar a.py "uno = 1" "uno = 0" 2>&1 | tail -1', ["está"]),
    ('reemplazar a.py "dos = 2" "dos = 0" 2', ["está"]),
    ('reemplazar a.py "uno = 1" "uno = 0" "$CUANTAS"', ["no medido"]),
    ('reemplazar a.py "uno = 1" "uno = 0" muchas', ["no medido"]),
], ids=["descriptor_a_un_archivo", "descriptor_a_la_salida", "veces_pedidas", "veces_sin_conocer",
        "veces_sin_numero"])
def test_las_veces_pedidas_son_un_argumento_y_no_el_descriptor_de_una_redirección(llamada, esperadas):
    assert clases(CON_VECES + llamada + "\n") == esperadas


@pytest.mark.parametrize("ancla, esperada", [
    ("$'caf\\xc3\\xa9 = \\'A\\''", "está"),
    ("$'café = \\'\\101\\''", "está"),
    ("$'caf\\u00e9 = \\'A\\''", "está"),
    ("$'uno\\x20= 1'", "está"),
], ids=["bytes_utf8", "octal", "unicode", "un_byte"])
def test_los_escapes_entre_comillas_con_dólar_dan_lo_mismo_que_en_bash(ancla, esperada):
    assert clases(REEMPLAZAR + f"reemplazar a.py {ancla} x\n") == [esperada]


@pytest.mark.parametrize("bloque", [
    "for ((i = 0; i < 2; i++)); do\n  LLAMADA\ndone\n",
    "VACIA=\ncase $VACIA in\n  *) LLAMADA ;;\nesac\n",
    "case \"$1\" in\n  a) echo a ;;\n  *) LLAMADA ;;\nesac\n",
    "for valor in uno dos; do\n  LLAMADA\ndone\n",
], ids=["for_con_cuenta", "case_de_un_valor_vacio", "case_sin_valor_conocido", "for_de_palabras"])
def test_la_llamada_dentro_de_un_bloque_se_cuenta_una_vez(bloque):
    llamada = 'reemplazar a.py "uno = 1" "uno = 0"'

    assert clases(REEMPLAZAR + bloque.replace("LLAMADA", llamada)) == ["está"]


def test_el_nombre_del_guion_no_es_un_argumento_de_la_función():
    guion = REEMPLAZAR + 'cambiar() { reemplazar "$0" "$1" "$2"; }\ncambiar "uno = 1" a.py\n'

    assert clases(guion) == ["no medido"]


def test_un_auxiliar_incluido_que_no_está_corta_con_su_nombre():
    guion = 'source "$(dirname "$0")/_comun.sh"\nreemplazar a.py "uno = 1" "uno = 0"\n'

    with pytest.raises(SystemExit, match="scripts/testing/sabotajes/_comun.sh"):
        filas(guion)


def test_las_funciones_de_un_auxiliar_incluido_se_siguen():
    guion = 'source "$(dirname "$0")/_comun.sh"\nreemplazar a.py "tres = 3" "tres = 0"\n'
    archivos = ARCHIVOS | {"scripts/testing/sabotajes/_comun.sh": REEMPLAZAR}

    assert clases(guion, archivos) == ["perdida, una línea"]
