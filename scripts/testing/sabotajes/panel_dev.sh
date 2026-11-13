#!/usr/bin/env bash
# Negativos del panel de dev: cada sabotaje vuelve a interpretar como HTML una
# parte de la tabla de api_logs, o le saca el color, el gris o la insignia, y
# scripts/testing/pantalla_panel_dev.js tiene que fallar por ese motivo.
#
# uso: scripts/testing/sabotajes/panel_dev.sh [SHA]
# Trabaja en un worktree descartable, sin servidor ni base: no toca tu copia.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
cd "$WT" || exit 2
FALLAS=0
H=proyecto_maria/templates/dev_dashboard.html

correr() { node scripts/testing/pantalla_panel_dev.js 2>&1; }

# sabotaje <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>
sabotaje() {
  local nombre="$1" viejo="$2" nuevo="$3" esperado="$4"
  git checkout -q -- proyecto_maria/
  if ! node -e '
    const fs = require("fs"); const [p, viejo, nuevo] = process.argv.slice(1);
    const s = fs.readFileSync(p, "utf8"); const n = s.split(viejo).length - 1;
    if (n !== 1) { console.error(`patrón no encontrado una sola vez (${n})`); process.exit(1); }
    fs.writeFileSync(p, s.replace(viejo, () => nuevo));' "$H" "$viejo" "$nuevo"
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  salida="$(correr)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "FALLA | $esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep FALLA <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  fi
}

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
if ! correr >/dev/null; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FALLA; exit 1
fi
echo "BASE  | en verde"

sabotaje "las celdas interpretan el texto como HTML" \
  "td.textContent = texto == null ? '—' : String(texto);" \
  "td.innerHTML = texto == null ? '—' : String(texto);" \
  "elementos creados por el texto de api_logs"
sabotaje "el texto se interpreta como HTML fuera de la tabla" \
  "td.textContent = texto == null ? '—' : String(texto);" \
  "document.createElement('div').innerHTML = String(texto); td.textContent = texto == null ? '—' : String(texto);" \
  "imágenes pedidas por el texto de api_logs"
sabotaje "la insignia interpreta el método como HTML" \
  "metodo.textContent = log.method;" "metodo.innerHTML = log.method;" \
  "elementos creados por el texto de api_logs"
sabotaje "el estado pierde su color" \
  "tr.cells[3].className = log.status" "void tr.cells[3].className, log.status" \
  "color del estado"
sabotaje "la hora y la IP pierden el gris" \
  "tr.cells[0].className = tr.cells[5].className = 'text-muted';" "void 0;" \
  "hora e IP en gris"
sabotaje "el método pierde su insignia" \
  "tr.cells[1].replaceChildren(metodo);" "void metodo;" \
  "método en su insignia"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
