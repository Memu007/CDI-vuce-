#!/usr/bin/env bash
# uso: scripts/testing/sabotaje_org1.sh [SHA] [venv]
# Negativos discriminantes de ORG-1 (invitaciones al estudio): sin 500 con la
# fecha con zona de Postgres, atada al email invitado, tope de usuarios del
# plan y un solo uso. Cada sabotaje se aplica en un worktree descartable,
# corre los casos y tiene que dar ROJO con el motivo esperado. Si un patrón no
# se encuentra, el script sale con error.
# Lo que sólo se ve en Postgres (el bloqueo del estudio en la carrera por el
# último lugar) lo cubre scripts/testing/org1_postgres.py.
set -euo pipefail
SHA="${1:-HEAD}"
VENV="${2:-${VENV:-/tmp/cdi-dev2/venv}}"
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "$SHA")"
TMP="$(mktemp -d)"
WT="$TMP/sabotaje-org1"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1 || true; rm -rf "$TMP"' EXIT
cd "$WT"

export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
PRUEBA=tests/test_org1.py
correr() {
  "$VENV/bin/python" -m pytest -q --no-cov -p no:cacheprovider -p no:randomly "$PRUEBA" 2>&1 || true
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

M=proyecto_maria/main.py
T=tests/test_org1.py

# --- 1. Sin 500 en las dos bases

# 1. vuelve a lo de hoy: la fecha de la invitación contra datetime.utcnow()
reemplazar $M "if invite_inv.expires_at and _utc(invite_inv.expires_at) < datetime.now(timezone.utc):" \
              "if invite_inv.expires_at and invite_inv.expires_at < datetime.utcnow():"
reemplazar $M "if inv.expires_at and _utc(inv.expires_at) < datetime.now(timezone.utc):" \
              "if inv.expires_at and inv.expires_at < datetime.utcnow():"
caso "fecha_sin_zona" "FAILED $T::test_registro_con_invitacion_vigente_entra_al_estudio[postgres_con_zona]"

# --- 2. Atada al email

# 2. vuelve a lo de hoy: cualquiera con el enlace entra
reemplazar $M '        if request.email != (invite_inv.email or "").strip().lower():
            raise HTTPException(status_code=400, detail="Esta invitación es para otro email. Registrate con el email al que te invitaron.")
' ''
caso "sin_email" "FAILED $T::test_registro_con_otro_email_400_y_la_invitacion_sigue[sqlite_sin_zona-{nuevo}]"

# --- 3. Tope del plan

# 3. vuelve a lo de hoy al invitar: sin tope
reemplazar $M "    if clean_email not in emails_pendientes and len(emails_miembros) + len(emails_pendientes) >= tope:" \
              "    if False:"
caso "invitar_sin_tope" "FAILED $T::test_invitar_hasta_el_tope_del_plan[sqlite_sin_zona-2]"

# 4. el tope fijo en 3 en vez del plan
reemplazar $M '    tope = billing_service.get_plan(org.plan or "premium")["users"]
    emails_miembros' '    tope = 3
    emails_miembros'
caso "tope_fijo" "FAILED $T::test_invitar_hasta_el_tope_del_plan[sqlite_sin_zona-4]"

# 5. la guarda: una pendiente vencida también ocupa lugar
reemplazar $M "        if not inv.expires_at or _utc(inv.expires_at) > ahora
" ""
caso "vencida_ocupa" "FAILED $T::test_invitacion_pendiente_vencida_no_ocupa_lugar[sqlite_sin_zona]"

# 6. la guarda: reinvitar a una pendiente ocupa otro lugar
reemplazar $M "if clean_email not in emails_pendientes and len(" "if len("
caso "reinvitar_ocupa" "FAILED $T::test_reinvitar_un_email_pendiente_no_ocupa_otro_lugar"

# 7. vuelve a lo de hoy al registrarse: sin tope
reemplazar $M "        if len(await _emails_de_miembros(db, invite_org.id)) >= tope:" \
              "        if False:"
caso "registro_sin_tope" "FAILED $T::test_registro_con_el_estudio_lleno_400_sin_gastar_la_invitacion[sqlite_sin_zona]"

# --- 4. Un solo uso, de verdad

# 8. vuelve a lo de hoy: se gasta sin mirar si seguía pendiente
reemplazar $M '            .where(Invitation.id == invite_inv.id, Invitation.status == "pending")' \
              '            .where(Invitation.id == invite_inv.id)'
caso "gasto_sin_condicion" "FAILED $T::test_invitacion_gastada_entre_la_lectura_y_el_alta_no_crea_usuario"

# 9. contar los miembros antes de gastar la invitación: en SQLite nada hace
#    esperar al otro registro y los dos entran por el último lugar
reemplazar $M '        tope = billing_service.get_plan(invite_org.plan or "premium")["users"]
        if len(await _emails_de_miembros(db, invite_org.id)) >= tope:
            await db.rollback()  # la invitación queda pendiente
            raise HTTPException(status_code=400, detail=f"El estudio ya tiene los {tope} usuarios de su plan.")
' ''
reemplazar $M '        # La invitación se gasta en la misma transacción que el alta' '        tope = billing_service.get_plan(invite_org.plan or "premium")["users"]
        if len(await _emails_de_miembros(db, invite_org.id)) >= tope:
            raise HTTPException(status_code=400, detail=f"El estudio ya tiene los {tope} usuarios de su plan.")
        # La invitación se gasta en la misma transacción que el alta'
caso "contar_antes" "FAILED $T::test_carrera_dos_invitaciones_por_el_ultimo_lugar"

if [ "$FALLAS" -ne 0 ]; then echo "FALLAN $FALLAS sabotajes"; exit 1; fi
echo "OK: los 9 sabotajes dan rojo por la razón esperada"
