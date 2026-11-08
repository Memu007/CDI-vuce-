#!/usr/bin/env bash
# Negativos de LIMPIEZA-1: cada sabotaje vuelve a sacar pruebas de la CI (en
# el paso o en pytest.ini), esconde su resultado o vuelve a abrir un camino de
# publicación a Google Cloud, y tests/test_limpieza1.py tiene que fallar por
# ese motivo. Los controles cambian algo que no saca pruebas ni publica, y
# tienen que quedar verdes.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/limpieza1.sh [SHA]
# Trabaja en un worktree descartable: no toca tu copia. Los archivos nuevos se
# agregan al índice del worktree porque la prueba mira lo versionado.
# Sale con error si un sabotaje no encuentra su patrón, no pone rojo o un
# control no queda verde.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rmdir "$TMPD" 2>/dev/null' EXIT
cd "$WT"
FALLAS=0
CI=.github/workflows/ci.yml
RUN="        run: python -m pytest --no-cov"

correr() {
  "$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_limpieza1.py 2>&1
}

# reemplazar <archivo> <viejo> <nuevo>: <viejo> tiene que aparecer una sola vez.
reemplazar() {
  "$PY" - "$@" <<'PYEOF'
import sys
p, viejo, nuevo = sys.argv[1:4]
s = open(p, encoding="utf-8").read()
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
PYEOF
}

# nuevo <ruta> <contenido>: crea el archivo y lo agrega al índice.
nuevo() {
  mkdir -p "$(dirname "$1")" && printf '%s\n' "$2" > "$1" && git add -- "$1"
}

limpiar() {
  git reset -q --hard "$SHA" && git clean -fdq
}

# sabotaje <nombre> <lo que el rojo tiene que decir> <comando que sabotea...>
sabotaje() {
  local nombre="$1" esperado="$2"; shift 2
  limpiar
  if ! "$@"; then echo "ROTO  | $nombre: el sabotaje no se pudo aplicar"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  salida="$(correr)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "^E |FAILED|Error" <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  fi
}

# control <nombre> <comando...>: un cambio que no saca pruebas ni publica.
control() {
  local nombre="$1"; shift
  limpiar
  if ! "$@"; then echo "ROTO  | control $nombre: no se pudo aplicar"; FALLAS=$((FALLAS+1)); return; fi
  local salida
  if salida="$(correr)"; then
    echo "VERDE | control $nombre"
  else
    echo "ROJO  | control $nombre: la prueba falla con un cambio que no saca pruebas ni publica"
    grep -E "^E |FAILED" <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  fi
}

echo "== sin sabotaje"
salida="$(correr)" && echo "VERDE | base" || { echo "ROJO  | base: la prueba no pasa sin sabotaje"; echo "$salida" | tail -5; exit 1; }

echo "== la CI vuelve a sacar pruebas"
sabotaje "un --deselect en la suite" "la CI saca pruebas de la suite: ['--deselect'" \
  reemplazar $CI "$RUN" "$RUN --deselect tests/test_csrf.py::test_enforce_no_afecta_bearer_sin_cookie"
sabotaje "un -k en la suite" "la CI saca pruebas de la suite: ['-k', 'not quote']" \
  reemplazar $CI "$RUN" "$RUN -k 'not quote'"
sabotaje "un -m en la suite" "la CI saca pruebas de la suite: ['-m', 'not slow']" \
  reemplazar $CI "$RUN" "$RUN -m 'not slow'"
sabotaje "una ruta: corre sólo ese archivo" "la CI saca pruebas de la suite: ['tests/test_csrf.py']" \
  reemplazar $CI "$RUN" "$RUN tests/test_csrf.py"
sabotaje "un --ignore= en la suite" "la CI saca pruebas de la suite: ['--ignore=tests/test_pilar_b_quotes.py']" \
  reemplazar $CI "$RUN" "$RUN --ignore=tests/test_pilar_b_quotes.py"
sabotaje "un --lf en la suite" "la CI saca pruebas de la suite: ['--lf']" \
  reemplazar $CI "$RUN" "$RUN --lf"
sabotaje "el run en bloque, con el --deselect en otra línea" "la CI saca pruebas de la suite: ['--deselect'" \
  reemplazar $CI "$RUN" "        run: >-
          python -m pytest --no-cov
          --deselect tests/test_csrf.py::test_enforce_no_afecta_bearer_sin_cookie"
sabotaje "un --deselect en otro paso" "ci.yml saca pruebas con --deselect o --ignore" \
  reemplazar $CI "$RUN" "$RUN

      - name: Otra corrida
        run: python -m pytest --no-cov --deselect tests/test_csrf.py::test_enforce_no_afecta_bearer_sin_cookie"
sabotaje "un -k por PYTEST_ADDOPTS" "ci.yml le pasa opciones a pytest por PYTEST_ADDOPTS" \
  reemplazar $CI '          EMAIL_VERIFICATION_REQUIRED: "false"' '          EMAIL_VERIFICATION_REQUIRED: "false"
          PYTEST_ADDOPTS: "-k not quote"'

sabotaje "un -k dentro de un grupo de cortas" "la CI saca pruebas de la suite: ['-vknot quotes']" \
  reemplazar $CI "$RUN" "$RUN -vk\"not quotes\""
sabotaje "un --co: junta las pruebas y no las corre" "la CI saca pruebas de la suite: ['--co']" \
  reemplazar $CI "$RUN" "$RUN --co"
sabotaje "un --setup-only" "la CI saca pruebas de la suite: ['--setup-only']" \
  reemplazar $CI "$RUN" "$RUN --setup-only"
sabotaje "un --override-ini que cambia qué archivos junta" "la CI saca pruebas de la suite: ['--override-ini=python_files=test_l*.py']" \
  reemplazar $CI "$RUN" "$RUN --override-ini=python_files=test_l*.py"
sabotaje "un -o que borra addopts" "la CI saca pruebas de la suite: ['-o', 'addopts=']" \
  reemplazar $CI "$RUN" "$RUN -o addopts="
sabotaje "un || true que tapa el rojo" "la CI saca pruebas de la suite: ['||']" \
  reemplazar $CI "$RUN" "$RUN||true"
sabotaje "el paso con continue-on-error" "la CI puede esconder el resultado de la suite: ['continue-on-error: true']" \
  reemplazar $CI "      - name: Suite completa" "      - name: Suite completa
        continue-on-error: true"
sabotaje "el job con continue-on-error" "la CI puede esconder el resultado de la suite: ['continue-on-error: true']" \
  reemplazar $CI "    timeout-minutes: 20" "    timeout-minutes: 20
    continue-on-error: true"
sabotaje "el paso con if: false" "la CI puede esconder el resultado de la suite: ['if: false']" \
  reemplazar $CI "      - name: Suite completa" "      - name: Suite completa
        if: false"
sabotaje "el paso corre en otra carpeta" "la CI puede esconder el resultado de la suite: ['working-directory: proyecto_maria']" \
  reemplazar $CI "      - name: Suite completa" "      - name: Suite completa
        working-directory: proyecto_maria"

echo "== pytest.ini vuelve a sacar pruebas"
sabotaje "un --deselect en addopts" "pytest.ini saca pruebas en addopts: ['--deselect=tests/test_pilar_b_quotes.py::test_share_quote_valid']" \
  reemplazar pytest.ini "addopts =" "addopts =
    --deselect=tests/test_pilar_b_quotes.py::test_share_quote_valid"
sabotaje "un -k en addopts" "pytest.ini saca pruebas en addopts: ['-k', 'not quotes']" \
  reemplazar pytest.ini "addopts =" "addopts =
    -k \"not quotes\""
sabotaje "testpaths más chico" "pytest.ini cambia qué pruebas junta" \
  reemplazar pytest.ini "testpaths = tests" "testpaths = tests/unit"

echo "== vuelve un camino a Google Cloud"
sabotaje "vuelve cloudbuild.yaml" "queda un camino a Google Cloud: ['cloudbuild.yaml'" \
  git checkout -q 8b45207 -- cloudbuild.yaml
sabotaje "un script nuevo con gcloud run deploy" "scripts/deployment/publicar.sh: gcloud" \
  nuevo scripts/deployment/publicar.sh 'gcloud run deploy cdi --source .'
sabotaje "un workflow con la acción de Google" "google-github-actions" \
  nuevo .github/workflows/publicar.yml '      - uses: google-github-actions/deploy-cloudrun@v2'
sabotaje "un workflow que sube la imagen a gcr.io" ".github/workflows/publicar.yml: gcr.io" \
  nuevo .github/workflows/publicar.yml '        run: docker push gcr.io/cdi/app:latest'
sabotaje "un archivo setup_gcp.sh sin gcloud adentro" "queda un camino a Google Cloud: ['setup_gcp.sh']" \
  nuevo setup_gcp.sh 'echo hola'

echo "== controles"
control "un .md que nombra gcloud" nuevo docs/deployment/NOTAS.md 'Antes se usaba gcloud run deploy.'
control "la suite con -q y --timeout" reemplazar $CI "$RUN" "$RUN -q --timeout=120"
control "la suite con -p, -W y -rA, que toman valor y no filtran" reemplazar $CI "$RUN" "$RUN -p no:cacheprovider -W ignore -rA"

limpiar
echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
