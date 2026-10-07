#!/usr/bin/env bash
# Negativos de GUARDAR-1: cada sabotaje deshace una línea de la pieza y
# tests/test_guardar1.py tiene que ponerse roja por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/guardar1.sh [SHA]
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
  salida="$("$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_guardar1.py 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "^E " <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

M=proyecto_maria/main.py
C=proyecto_maria/services/client_memory.py
T=tests/test_guardar1.py

if ! "$PY" -m pytest -q --no-cov -p no:cacheprovider $T >/dev/null 2>&1; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; exit 1
fi

sabotaje $C "el historial vuelve a guardar la SIM completa" \
  '    ncm = ncm_para_historial(ncm) or ""' \
  '    ncm = (ncm or "").strip()' \
  "FAILED $T::test_guardar_con_la_sim_completa_deja_el_ncm_en_el_historial"
sabotaje $C "la SIM se corta a 10 caracteres" \
  '    return digitos[:8] if len(digitos) >= 8 else None' \
  '    return ncm[:10]' \
  "FAILED $T::test_la_forma_del_ncm_que_guarda_el_historial[84714900100D-84714900]"
sabotaje $M "el historial vuelve a ir en el mismo commit que la operación" \
  $'        billing_service.record_operation_created(billing_entity)\n        await db.commit()\n        operation_id = operation.id' \
  $'        billing_service.record_operation_created(billing_entity)\n        await db.flush()\n        operation_id = operation.id' \
  "FAILED $T::test_si_el_historial_falla_la_operacion_igual_se_guarda"
sabotaje $M "editar vuelve a cortar a 10 caracteres" \
  '        row.ncm = ncm_nuevo' \
  '        row.ncm = str(body["ncm"]).strip()[:10]' \
  "FAILED $T::test_editar_un_producto_con_la_sim_completa_no_deja_un_codigo_cortado"
sabotaje $M "editar vuelve a aceptar cualquier cosa" \
  '            raise HTTPException(status_code=400, detail="El NCM no es válido: tiene que tener sus 8 dígitos.")' \
  '            pass' \
  "FAILED $T::test_editar_un_producto_con_la_sim_completa_no_deja_un_codigo_cortado"
sabotaje $M "el contador del plan vuelve a ir después de guardar la operación" \
  $'        billing_service.record_operation_created(billing_entity)\n        await db.commit()\n        operation_id = operation.id' \
  $'        await db.commit()\n        billing_service.record_operation_created(billing_entity)\n        await db.commit()\n        operation_id = operation.id' \
  "FAILED $T::test_si_falla_el_contador_del_plan_no_queda_una_operacion_gratis"
sabotaje $M "la respuesta vuelve a callar que el historial falló" \
  $'    except Exception:\n        historial_guardado = False\n        await db.rollback()' \
  $'    except Exception:\n        await db.rollback()' \
  "FAILED $T::test_si_el_historial_falla_la_operacion_igual_se_guarda"
sabotaje $M "la moneda vuelve a no recortarse" \
  '            currency=str(data.get("currency") or "USD")[:3],' \
  '            currency=data.get("currency") or "USD",' \
  "FAILED $T::test_datos_largos_de_la_operacion_no_impiden_guardarla"
sabotaje $M "aprender vuelve a contar lo que no guardó" \
  '        return entrada is not None' \
  '        return True' \
  "FAILED $T::test_aprender_no_cuenta_lo_que_no_guardo"

sabotaje $M "el historial vuelve a ir sin savepoint por producto" \
  $'        async with db.begin_nested():\n            entrada = await upsert(db, **campos)\n            await db.flush()' \
  $'        if True:\n            entrada = await upsert(db, **campos)\n            await db.flush()' \
  "FAILED $T::test_un_producto_malo_no_se_lleva_el_historial_de_los_demas"
sabotaje $M "el NUL vuelve a llegar a la base" \
  '        data = _sin_nul(await request.json())' \
  '        data = await request.json()' \
  "FAILED $T::test_un_grupo_fuera_de_rango_y_el_nul_en_otros_textos_no_impiden_guardar"
sabotaje $M "un grupo fuera de rango vuelve a llegar a la base" \
  '    return numero if numero is not None and -2**31 <= numero < 2**31 else None' \
  '    return numero' \
  "FAILED $T::test_un_grupo_fuera_de_rango_y_el_nul_en_otros_textos_no_impiden_guardar"

echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
