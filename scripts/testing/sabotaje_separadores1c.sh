#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_separadores1c.sh [SHA] [venv]
# Negativos discriminantes de SEPARADORES-1c: en la factura, los miles mal
# formados quedan sin leer; en la pantalla, el cero adelante pregunta o no
# cierra; el servidor no toma por blanco lo que la pantalla no lee; la
# pregunta propone formas que se leen como dice, con el signo. Cada sabotaje se aplica en un worktree descartable, corre los
# casos y tiene que dar ROJO con el motivo esperado. Si un patrón no se
# encuentra, el script sale con error.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-separadores1c"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
unset ENABLE_PDF_LLM_FALLBACK || true
PRUEBA="tests/test_separadores1c.py tests/test_separadores1b.py"
[ -d /opt/node22/bin ] && export PATH="/opt/node22/bin:$PATH"
correr() {
  "$VENV/bin/python" -m pytest -q --no-cov -p no:cacheprovider $PRUEBA 2>&1 || true
}

# reemplazar <archivo> <viejo> <nuevo> [veces]: falla si <viejo> no aparece
# exactamente esas veces (una, si no se dice)
reemplazar() {
  "$VENV/bin/python" - "$@" <<'PY'
import sys
p, viejo, nuevo = sys.argv[1:4]
veces = int(sys.argv[4]) if len(sys.argv) > 4 else 1
s = open(p, encoding="utf-8").read()
n = s.count(viejo)
if n != veces:
    sys.exit(f"PATRON NO ENCONTRADO ({n} veces) en {p}: {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
PY
}

FALLAS=0
caso() {  # caso <nombre> <texto que el rojo tiene que mostrar>
  local nombre="$1" espera="$2" salida
  salida="$(correr)"
  git checkout -q -- .
  if grep -q "passed" <<<"$salida" && ! grep -q "failed" <<<"$salida"; then
    echo "FALLA  $nombre: quedó verde"; FALLAS=$((FALLAS+1)); return
  fi
  if grep -qF -- "$espera" <<<"$salida"; then
    echo "ROJO   $nombre: $(grep -E '[0-9]+ failed' <<<"$salida" | tail -1)"
  else
    echo "FALLA  $nombre: rojo, pero sin «$espera»"; FALLAS=$((FALLAS+1))
    tail -15 <<<"$salida"
  fi
}

P=proyecto_maria/pdf_extractor.py
A=proyecto_maria/static/v2/montos_ar.js
G=proyecto_maria/core/maria_generator.py
C=proyecto_maria/core/controles_maria.py
T=tests/test_separadores1c.py

# --- 1. La factura: grupos de miles

# 1. la regla no se aplica: «0750.000» con «,» vuelve a dar 750000
reemplazar $P '    if _miles_mal_formados(t, decimal):
        return None
' ''
caso "factura_sin_regla" "FAILED $T::test_en_la_factura_miles_mal_formados_quedan_sin_leer[0750.000-,]"

# 2. la cabeza admite cero adelante
reemplazar $P 're.fullmatch(r"[1-9]\d{0,2}", grupos[0])' 're.fullmatch(r"\d{1,3}", grupos[0])'
caso "factura_cero_adelante" "FAILED $T::test_en_la_factura_miles_mal_formados_quedan_sin_leer[03,250-.]"

# --- 1. La pantalla: cero adelante

# 3. «01.500.000» vuelve a leerse 1500000
reemplazar $A "return /^[1-9]\\d{0,2}\$/.test(grupos[0])" "return /^\\d{1,3}\$/.test(grupos[0])"
caso "pantalla_miles_con_cero" "FAILED $T::test_en_la_pantalla_miles_con_cero_adelante_no_cierran[01.500.000-no cierran]"

# 4. «01234.500» vuelve a leerse 1234,5 sin preguntar
reemplazar $A "/^\\d{4,}\$/.test(partes[0]) && !/^0+\$/.test(partes[0])" "/^[1-9]\\d{3,}\$/.test(partes[0])"
caso "pantalla_no_pregunta_con_cero" "FAILED $T::test_en_la_pantalla_se_pregunta_con_formas_que_se_leen_igual[01234.500-"

# --- 2. La idea de «en blanco»

# 5. el generador vuelve a strip() de Python: \x85 sale 0 en el TXT
reemplazar $G '        valor = valor.strip(ESPACIOS)' '        valor = valor.strip()'
caso "generador_strip_python" "FAILED $T::test_lo_que_el_servidor_toma_como_blanco_la_pantalla_tambien"

# 6. los controles de la cabecera (semáforo, exportación) vuelven a strip() de Python
reemplazar $C 'not valor.strip(ESPACIOS))' 'not valor.strip())'
caso "controles_strip_python" "FAILED $T::test_el_semaforo_tampoco_lo_toma_como_blanco[flete-Flete: -\\x85]"

# --- 3. La pregunta

# 7. la lectura «sin separador» pierde el signo
reemplazar $A "const miles = escribir(signo * Number(partes[0] + partes[1]));" "const miles = escribir(Number(partes[0] + partes[1]));"
caso "pregunta_sin_signo" "FAILED $T::test_las_dos_formas_que_propone_se_leen_como_dice[-1234.500--1234500]"

# 8. la rama de la coma pierde el signo
reemplazar $A "const miles = (signo < 0 ? '-' : '') + partes[0] + '.' + partes[1];" "const miles = partes[0] + '.' + partes[1];"
caso "coma_sin_signo" "FAILED $T::test_las_dos_formas_que_propone_se_leen_como_dice[-3,480--3480]"

# 9. la lectura decimal vuelve a proponerse con tres decimales («2500,125»)
reemplazar $A "                const dec = escribir(signo * Number(partes[0] + '.' + partes[1]));
                return { valor: null, error: '¿' + miles + ' o ' + dec +
                    '? Escribilo sin" "                const dec = (signo < 0 ? '-' : '') + partes[0] + ',' + partes[1];
                return { valor: null, error: '¿' + miles + ' o ' + dec +
                    '? Escribilo sin"
caso "pregunta_tres_decimales" "FAILED $T::test_las_dos_formas_que_propone_se_leen_como_dice[2500.125-2500125]"

# 10. sin el tope de quince cifras se propone otro número
reemplazar $A "                if (partes[0].replace(/^0+/, '').length + 3 > 15) return { valor: null, error: NO_ES_NUMERO };
" ""
caso "pregunta_sin_tope" "FAILED $T::test_una_cifra_larga_pegada_no_traba_ni_propone_otro_numero"

if [ "$FALLAS" -ne 0 ]; then echo "FALLAN $FALLAS sabotajes"; exit 1; fi
echo "OK: los 10 sabotajes dan rojo por la razón esperada"
