#!/usr/bin/env bash
# Negativos de FRONT-422: cada sabotaje deshace una regla de la pieza y
# tests/test_front422.py tiene que fallar en el caso de esa regla.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/front422.sh [SHA]
# Trabaja en un worktree descartable con SQLite propia. Necesita `node`.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rmdir "$TMPD" 2>/dev/null' EXIT
cd "$WT"
FALLAS=0

# sabotaje <archivo> <nombre> <lo que el rojo tiene que decir> <viejo> <nuevo> [<viejo> <nuevo> ...]
# Cada <viejo> tiene que aparecer una sola vez en el archivo.
sabotaje() {
  local archivo="$1" nombre="$2" esperado="$3"; shift 3
  git checkout -q -- proyecto_maria/
  rm -f test.db
  if ! "$PY" - "$archivo" "$@" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
pares = sys.argv[2:]
for viejo, nuevo in zip(pares[::2], pares[1::2]):
    if s.count(viejo) != 1:
        sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
    s = s.replace(viejo, nuevo)
open(p, "w", encoding="utf-8").write(s)
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  salida="$(correr)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "FAILED|Error" <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  fi
}

T=tests/test_front422.py
L="FAILED $T::test_el_422_de_pydantic_se_lee_en_castellano"
D="FAILED $T::test_un_detail_de_texto_se_muestra_tal_cual"
E=proyecto_maria/static/errores.js
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
correr() { "$PY" -m pytest -q --no-cov -p no:cacheprovider -W ignore -rf "$T" 2>&1; }

rm -f test.db
if ! correr >/dev/null; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FAILED; exit 1
fi
echo "BASE  | en verde"

# --- Cada pantalla pasa el detail por el traductor
sabotaje proyecto_maria/static/v2/app_v2.js "CDI.api deja la lista como llegó" "$L[api-falta_campo]" \
  "cuerpo.detail = textoDeError(cuerpo.detail, 'Revisá los datos ingresados.');" ""
sabotaje proyecto_maria/templates/landing.html "el login tapa el motivo con el texto genérico" "$L[landing-falta_campo]" \
  "textoDeError(detail, (data" "(typeof detail === 'string' ? detail : null) || ((data"
sabotaje proyecto_maria/templates/reset_password.html "el reset muestra la lista cruda" "$L[reset-clave_73_bytes]" \
  "showError(textoDeError(data.detail, " "showError(String(data.detail) || ("

# --- Cada tipo de error de pydantic tiene su texto
sabotaje $E "falta un campo se dice con el msg de pydantic" "$L[reset-falta_campo]" \
  "case 'missing': return 'Falta ' + c + '.';" ""
sabotaje $E "un tipo equivocado se dice en genérico" "$L[api-tipo_equivocado]" \
  "case 'string_type': return mayuscula(c) + ' tiene que ser texto.';" ""
sabotaje $E "el tope de largo no se dice" "$L[landing-nombre_largo]" \
  "if (tope) return" "if (false) return"
sabotaje $E "el value_error conserva el prefijo en inglés" "$L[api-clave_73_bytes]" \
  ".replace(/^Value error, /, '')" ""
sabotaje $E "un JSON roto se dice en genérico" "$L[landing-no_es_json]" \
  "case 'json_invalid': return 'Los datos enviados no son JSON válido.';" ""
sabotaje $E "un cuerpo que no es objeto se dice en genérico" "$L[reset-no_es_objeto]" \
  "case 'model_attributes_type': case 'dict_type': return 'Los datos enviados tienen que ser un objeto.';" ""

# --- Un detail de texto no se toca
sabotaje $E "un detail de texto se reemplaza por el genérico" "$D[landing]" \
  "if (typeof detail === 'string' && detail.trim()) return detail;" ""

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
