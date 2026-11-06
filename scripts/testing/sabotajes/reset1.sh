#!/usr/bin/env bash
# Negativos de RESET-1: cada sabotaje deshace una parte de la pieza y
# tests/test_reset1.py tiene que ponerse roja por ese motivo. Con
# PG_URL (un Postgres local y descartable), también los usos a la vez contra
# scripts/testing/reset1_postgres.py.
#
# uso: PY=/ruta/al/venv/bin/python [PG_URL=postgresql://cdi@127.0.0.1:55432/postgres] \
#        scripts/testing/sabotajes/reset1.sh [SHA]
# Trabaja en un worktree descartable: no toca tu copia ni datos compartidos.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PG_URL="${PG_URL:-}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
# terceros simulados; la base y ENVIRONMENT las pone tests/conftest.py
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
FALLAS=0
T=tests/test_reset1.py
PRUEBA=("$PY" -m pytest -q --no-cov -p no:cacheprovider "$T")
PRUEBA_PG=("$PY" -I scripts/testing/reset1_postgres.py "$PG_URL")

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>...
# Corre la prueba de "${CORRE[@]}".
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4" esperado falta=""; shift 4
  git checkout -q -- proyecto_maria/
  if ! "$PY" - "$archivo" "$viejo" "$nuevo" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p).read()
viejo, nuevo = sys.argv[2], sys.argv[3]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w").write(s.replace(viejo, nuevo))
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  salida="$("${CORRE[@]}" 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
    return
  fi
  for esperado in "$@"; do grep -qF -- "$esperado" <<<"$salida" || falta="$esperado"; done
  if [ -z "$falta" ]; then
    echo "ROJO  | $nombre: dice «$*»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$falta»"
    grep -E "^E |^FALLA" <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

M=proyecto_maria/main.py
M=proyecto_maria/main.py
N=test_el_link_no_sirve_despues_de_un_cambio
VIEJO='el link viejo sigue sirviendo'
TODOS='    if hecho.rowcount == 1 and valores.keys() & {"password", "email"}:
        await db.execute(links)
'
GUARDA='    if not await guardar_si_la_clave_sigue(db, user.username, user.password, consumir=data.token,
                                           password=hash_password(data.new_password),
                                           active_jti=uuid.uuid4().hex):
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
'
SIN_GUARDA='    user.password = hash_password(data.new_password)
    user.active_jti = uuid.uuid4().hex
    reset_token.is_used = True
    await db.commit()
'

CORRE=("${PRUEBA[@]}")
if ! "${CORRE[@]}" >/dev/null 2>&1; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; exit 1
fi

sabotaje $M "cambiar la clave o el email no mata los links de antes" "$TODOS" '' \
  "FAILED $T::${N}[cambio de clave]" "FAILED $T::${N}[cambio de email]" "FAILED $T::${N}[otro reset]" "$VIEJO"
sabotaje $M "cambiar el email no mata los links de antes" \
  'valores.keys() & {"password", "email"}' 'valores.keys() & {"password"}' \
  "FAILED $T::${N}[cambio de email]" "$VIEJO"
sabotaje $M "el reset guarda sin compare-and-swap ni consumo" "$GUARDA" "$SIN_GUARDA" \
  "FAILED $T::${N}[otro reset]" "$VIEJO"

if [ -n "$PG_URL" ]; then
  CORRE=("${PRUEBA_PG[@]}")
  git checkout -q -- proyecto_maria/
  if ! "${CORRE[@]}" >/dev/null 2>&1; then
    echo "BASE  | la prueba en Postgres ya está en rojo sin sabotaje"; FALLAS=$((FALLAS+1))
  else
    sabotaje $M "el reset no consume su link" 'consumir=data.token,' '' \
      "FALLA | el cambio de email que llega primero mata el link"
    sabotaje $M "el reset que pierde la carrera dice que guardó" \
      '        raise HTTPException(status_code=400, detail="Token inválido o expirado")
    return {"message": "Contraseña actualizada exitosamente"}' \
      '        pass
    return {"message": "Contraseña actualizada exitosamente"}' \
      "FALLA | el mismo link dos veces a la vez" "FALLA | el cambio de email que llega primero mata el link"
    sabotaje $M "el reset guarda sin compare-and-swap ni consumo" "$GUARDA" "$SIN_GUARDA" \
      "FALLA | el mismo link dos veces a la vez" "FALLA | el cambio de email que llega primero mata el link"
  fi
else
  echo "SALTO | sin PG_URL: los usos a la vez no se midieron"
fi

git checkout -q -- proyecto_maria/
echo "fallas: $FALLAS"
[ "$FALLAS" -eq 0 ]
