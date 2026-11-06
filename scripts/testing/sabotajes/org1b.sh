#!/usr/bin/env bash
# Negativos de ORG-1b (D27 b): cada sabotaje deshace una parte del completado
# del email invitado en el registro y scripts/testing/pantalla_org1b.js tiene
# que fallar por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python [PUERTO=8852] scripts/testing/sabotajes/org1b.sh [SHA]
# Trabaja en un worktree descartable con su propia API, SQLite nueva y sin
# terceros: no toca tu copia ni datos compartidos. La landing se lee en cada
# pedido, así que los sabotajes de la pantalla se aplican con la API andando;
# el del servidor la reinicia.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PUERTO="${PUERTO:-8852}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
API=""
trap '[ -n "$API" ] && kill $API 2>/dev/null; git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
export ENVIRONMENT=development DATABASE_URL=sqlite+aiosqlite:///./local.db GEMINI_API_KEY=test-key \
       JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef EMAIL_VERIFICATION_REQUIRED=false \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares \
       ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x
export BASE_URL="http://127.0.0.1:$PUERTO"

levantar() {
  [ -n "$API" ] && { kill $API 2>/dev/null; wait $API 2>/dev/null; }
  "$PY" -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port "$PUERTO" >"$TMPD/api.log" 2>&1 &
  API=$!
  for _ in $(seq 1 60); do curl -fsS "$BASE_URL/health" >/dev/null 2>&1 && return 0; sleep 1; done
  echo "BASE  | la API no levantó"; tail -20 "$TMPD/api.log"; exit 1
}
levantar
FALLAS=0

correr() { node scripts/testing/pantalla_org1b.js 2>&1; }

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4" esperado="$5"
  git checkout -q -- proyecto_maria/
  if ! "$PY" - "$archivo" "$viejo" "$nuevo" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
viejo, nuevo = sys.argv[2], sys.argv[3]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  case "$archivo" in *.py) levantar ;; esac
  local salida codigo
  salida="$(correr)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep FALLA <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  fi
  case "$archivo" in *.py) git checkout -q -- proyecto_maria/; levantar ;; esac
}

H=proyecto_maria/templates/landing.html
M=proyecto_maria/main.py

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
if ! correr >/dev/null; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FALLA; exit 1
fi

sabotaje $H "no se completa el email" \
  "                    emailInput.value = invitedEmail;"$'\n' '' \
  "FALLA: con invitación válida el email no viene completo"
sabotaje $H "el email completo queda editable" \
  "                    emailInput.readOnly = true;"$'\n' '' \
  "FALLA: con invitación válida el email no es de sólo lectura"
sabotaje $H "además disabled (no viaja en el envío)" \
  "emailInput.readOnly = true;" "emailInput.readOnly = true; emailInput.disabled = true;" \
  "FALLA: con invitación válida el email está disabled"
sabotaje $H "la línea del email invitado no aparece" \
  "if (hint) hint.hidden = false;" "void hint;" \
  "FALLA: con invitación válida no se ve la línea del email invitado"
sabotaje $H "la línea se ve siempre" \
  '<small id="inviteEmailHint" class="auth-hint" hidden>' '<small id="inviteEmailHint" class="auth-hint">' \
  "FALLA: sin invite: se ve la línea del email invitado"
sabotaje $H "se bloquea aunque la invitación no traiga email" \
  "if (invitedEmail && emailInput) {" "if (emailInput) {" \
  "FALLA: válida sin email: el email no queda vacío y editable"
sabotaje $M "el servidor deja de exigir el email invitado" \
  "        if request.email != (invite_inv.email or \"\").strip().lower():" \
  "        if False and request.email != (invite_inv.email or \"\").strip().lower():" \
  "FALLA: con el email cambiado en el DOM el registro dio 200, no 400"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
