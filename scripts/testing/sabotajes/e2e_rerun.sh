#!/usr/bin/env bash
# PRUEBAS-1 c): la espera de config/e2e_maria.js antes de «Volver a validar»
# distingue el rojo «Node is either not clickable or not an Element».
#
# Causa: al entrar a Validación la pantalla pide los avisos del TXT
# (/generate_maria/avisos) y los pinta arriba de los botones: el botón baja
# unos 560 px. page.click() scrollea el botón al centro y después calcula
# dónde clickear; si los avisos llegan entre esos dos pasos, el botón quedó
# fuera de la pantalla y Puppeteer lanza ese error.
#
# El hueco entre el scroll y el cálculo dura microsegundos, así que una demora
# sola no lo abre a voluntad. Acá se demoran los avisos 1500 ms y el click de
# «Volver a validar» se hace con los mismos pasos de page.click() por
# separado (scroll, esperar a que se pinten los avisos, calcular el punto,
# clickear). Así la carrera pasa siempre:
#   con la espera:  la prueba pasa (el scroll se hace con los avisos ya puestos);
#   sin la espera:  la prueba falla con ese error.
# Una tercera corrida demora /api/validate/smart 3000 ms sin la espera, con el
# click normal: pasa, porque la segunda visita usa la validación guardada de
# menos de 60 s y no llama a ese servicio antes del click.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/e2e_rerun.sh [SHA]
# Trabaja en un worktree descartable; la e2e levanta su propia API y base.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
[ -d "$REPO/config/node_modules/puppeteer" ] || { echo "BASE  | falta config/node_modules: corré npm ci --prefix config"; exit 1; }
ln -s "$REPO/config/node_modules" "$WT/config/node_modules"
PATH="$(dirname "$PY"):$PATH"
cd "$WT"
E2E=config/e2e_maria.js
cp "$E2E" "$TMPD/original.js"

# variante <espera: si|no> <demora: avisos|validacion> <click: partido|normal>
variante() {
  "$PY" - "$TMPD/original.js" "$E2E" "$@" <<'PYEOF'
import sys
origen, destino, espera, demora, click = sys.argv[1:]
s = open(origen, encoding="utf-8").read()

def cambiar(viejo, nuevo, veces=1, ultima=False):
    global s
    n = s.count(viejo)
    if (ultima and n < 1) or (not ultima and n != veces):
        sys.exit(f"ROTO  | encontré {n} veces: {viejo!r}")
    if ultima:
        i = s.rindex(viejo)
        s = s[:i] + nuevo + s[i + len(viejo):]
    else:
        s = s.replace(viejo, nuevo)

ruta = {"avisos": "/generate_maria/avisos", "validacion": "/api/validate/smart"}[demora]
ms = {"avisos": 1500, "validacion": 3000}[demora]
cambiar("            void request.continue();\n",
        f"            if (url.origin === baseUrl && url.pathname === '{ruta}') {{\n"
        f"                setTimeout(() => void request.continue(), {ms});\n"
        "                return;\n            }\n"
        "            void request.continue();\n")
if espera == "no":
    # Sólo la visita del «Volver a validar»: vuelve la espera vieja.
    cambiar("    await validacionQuieta(page);",
            "    await page.waitForSelector('#validatingResults:not([hidden])');", ultima=True)
if click == "partido":
    cambiar("    await page.click('#validatingRerun');",
            "    const rerun = await page.$('#validatingRerun');\n"
            "    await rerun.scrollIntoView();\n"
            "    await page.waitForFunction(() => !document.getElementById('validatingAvisosPanel').hidden);\n"
            "    await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));\n"
            "    const punto = await rerun.clickablePoint();\n"
            "    await page.mouse.click(punto.x, punto.y);")
open(destino, "w", encoding="utf-8").write(s)
PYEOF
}

FALLAS=0
# correr <nombre> <tiene que: pasar|fallar> <espera> <demora> <click>
correr() {
  local nombre="$1" debe="$2"; shift 2
  variante "$@" || { FALLAS=$((FALLAS+1)); return; }
  local t=$SECONDS salida rc
  salida=$(bash scripts/testing/e2e_maria.sh 2>&1); rc=$?
  local tardo=$((SECONDS-t))
  if [ "$debe" = pasar ]; then
    if [ $rc -eq 0 ]; then echo "VERDE | $nombre: pasó (${tardo} s)"
    else echo "MAL   | $nombre: tenía que pasar y falló (${tardo} s)"; grep -m3 -i "error\|falló" <<<"$salida" | cut -c1-200 | sed 's/^/        /'; FALLAS=$((FALLAS+1)); fi
  else
    if [ $rc -ne 0 ] && grep -q "Node is either not clickable or not an Element" <<<"$salida"; then
      echo "ROJO  | $nombre: falló con «Node is either not clickable or not an Element» (${tardo} s)"
    else echo "MAL   | $nombre: tenía que fallar por el botón fuera de la pantalla (salida $rc, ${tardo} s)"; grep -m3 -i "error" <<<"$salida" | cut -c1-200 | sed 's/^/        /'; FALLAS=$((FALLAS+1)); fi
  fi
}

inicio=$SECONDS
correr "con la espera, avisos demorados, click partido" pasar si avisos partido
correr "sin la espera, avisos demorados, click partido" fallar no avisos partido
correr "sin la espera, validación demorada, click normal" pasar no validacion normal
echo "tardó $((SECONDS-inicio)) s"
echo "mediciones con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
