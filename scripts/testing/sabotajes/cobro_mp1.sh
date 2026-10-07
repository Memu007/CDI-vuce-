#!/usr/bin/env bash
# Negativos de COBRO-MP-1 (pasos 1 y 3): cada sabotaje deshace una línea de la pieza y
# tests/test_cobro_mp1.py tiene que ponerse roja por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/cobro_mp1.sh [SHA]
# Trabaja en un worktree descartable: no toca tu copia ni datos compartidos.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
# terceros simulados; la base y ENVIRONMENT las pone tests/conftest.py
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
FALLAS=0

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4" esperado="$5"
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
  salida="$("$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_cobro_mp1.py 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "^E " <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

M=proyecto_maria/main.py
T=tests/test_cobro_mp1.py

if ! "$PY" -m pytest -q --no-cov -p no:cacheprovider $T >/dev/null 2>&1; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; exit 1
fi

# Paso 1: cada pago se aplica una sola vez
sabotaje $M "un pago ya aplicado vuelve a aplicarse" \
  $'        return False\n    monto = pay_resp.get("transaction_amount")' \
  $'        return True\n    monto = pay_resp.get("transaction_amount")' \
  "FAILED $T::test_alternar_dos_pagos_viejos_no_renueva"
sabotaje $M "la organización vuelve a mirar sólo el último pago" \
  '                if not await _registrar_pago_mp(session, payment_id, f"org:{org_id}", update, pay_resp):' \
  '                if db_org.last_payment_id == payment_id:' \
  "FAILED $T::test_organizacion_alternar_dos_pagos_viejos_no_renueva"
sabotaje $M "el usuario vuelve a mirar sólo el último pago" \
  '            if not await _registrar_pago_mp(session, payment_id, username, update, pay_resp):' \
  '            if db_user.last_payment_id == payment_id:' \
  "FAILED $T::test_alternar_dos_pagos_viejos_no_renueva"
sabotaje $M "el pago se registra sin su tipo" \
  $'        tipo="topup" if update.get("action") == "topup" else str(update.get("plan") or ""),' \
  $'        tipo="",' \
  "FAILED $T::test_el_pago_aplicado_queda_registrado"

# Paso 3: el período se extiende desde su fin
sabotaje $M "pagar con la cuenta activa vuelve a contar desde hoy" \
  '    desde = fin if (getattr(cuenta, "billing_status", None) == "active" and fin and fin > ahora) else ahora' \
  '    desde = ahora' \
  "FAILED $T::test_pagar_con_la_cuenta_activa_extiende_desde_el_fin"
sabotaje $M "la organización vuelve a contar desde hoy" \
  '                _extender_periodo(db_org, update)' \
  '                pass' \
  "FAILED $T::test_organizacion_pagar_activa_extiende_desde_el_fin"
sabotaje $M "una cuenta vencida suma desde el fin viejo" \
  '    desde = fin if (getattr(cuenta, "billing_status", None) == "active" and fin and fin > ahora) else ahora' \
  '    desde = fin if fin else ahora' \
  "FAILED $T::test_pagar_con_la_cuenta_vencida_cuenta_desde_hoy"

echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
