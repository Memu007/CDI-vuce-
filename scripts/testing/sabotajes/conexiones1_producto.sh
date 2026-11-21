#!/usr/bin/env bash
# Control de tests/test_conexiones1.py (aplicado desde scripts/testing/conexiones1_tests.diff)
# y de la recarga junto a la carga manual (scripts/testing/conexiones1_creditos.py).
# Cada sabotaje deshace una parte del arreglo y exige que fallen justo los casos
# que la miran, ni uno más ni uno menos.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/conexiones1_producto.sh [SHA]
# Trabaja en un worktree descartable; la corrida de créditos levanta su propio
# Postgres 16 con scripts/testing/con_pg16.sh.
# Sale con error si una corrida no da lo esperado.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
# Relativo, dejaría de valer después del cd al worktree.
case "$PY" in */*) PY="$(cd "$(dirname "$PY")" && pwd)/$(basename "$PY")";; esac
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rmdir "$TMPD" 2>/dev/null' EXIT
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
cd "$WT"
git apply scripts/testing/conexiones1_tests.diff || exit 2
FALLAS=0
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
  DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test

mal() { echo "MAL   | $1"; tail -20 <<<"$2"; FALLAS=$((FALLAS+1)); }

# casos <nombre> <caso que tiene que fallar>... ; TEXTO=<lo que el log tiene que tener>
casos() {
  local nombre="$1" salida codigo fallaron esperados; shift
  salida="$("$PY" -m pytest -q -rf -p no:cacheprovider --no-cov --timeout=120 tests/test_conexiones1.py 2>&1)"; codigo=$?
  fallaron="$(sed -nE 's/^FAILED tests\/test_conexiones1\.py::([^ ]+).*/\1/p' <<<"$salida" | sort | tr '\n' ' ')"
  esperados="$(printf '%s\n' "$@" | sed '/^$/d' | sort | tr '\n' ' ')"
  if [ "$codigo" -ne $(( $# > 0 )) ] || [ "$fallaron" != "$esperados" ]; then
    mal "$nombre: salida $codigo, fallaron «$fallaron», se esperaba «$esperados»" "$salida"; return
  fi
  if ! grep -q " passed" <<<"$salida"; then mal "$nombre: no pasó ningún caso" "$salida"; return; fi
  if [ -n "${TEXTO:-}" ] && ! grep -qF -- "$TEXTO" <<<"$salida"; then
    mal "$nombre: falta «$TEXTO»" "$salida"; return
  fi
  echo "BIEN  | $nombre: $(tail -1 <<<"$salida")"
  [ -n "$fallaron" ] && echo "        fallaron: $fallaron"
}

# creditos <nombre> <salida esperada> <texto>
creditos() {
  local salida codigo
  salida="$(PY="$PY" scripts/testing/con_pg16.sh "$PY" scripts/testing/conexiones1_creditos.py 2>&1)"; codigo=$?
  if [ "$codigo" -ne "$2" ] || ! grep -qF -- "$3" <<<"$salida"; then
    mal "$1: salida $codigo, esperaba $2 y «$3»" "$salida"; return
  fi
  echo "BIEN  | $1: salida $codigo, dice «$3»"
}

# en_codigo <archivo> <viejo> <nuevo>...: cambia el producto; lo deshace la
# llamada siguiente o el final del script. No toca el caso, que no está en git.
en_codigo() {
  git checkout -q -- proyecto_maria
  "$PY" - "$@" <<'PYEOF' || { echo "PATRÓN | $2"; FALLAS=$((FALLAS+1)); return 1; }
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
for viejo, nuevo in zip(sys.argv[2::2], sys.argv[3::2]):
    if s.count(viejo) != 1:
        sys.exit(f"patrón no encontrado una sola vez: {viejo!r}")
    s = s.replace(viejo, nuevo)
open(p, "w", encoding="utf-8").write(s)
PYEOF
}

M=proyecto_maria/main.py
T=test_la_espera_no_retiene_conexiones
B=test_la_base_caida_al_soltarla_no_corta_el_pedido
FIRMA_MANUAL='    _cobro=Depends(require_cupo_del_plan),
):
    """Crea una operación cargada manualmente'
SUELTA_COBRO='    await _soltar_conexion(db)
    return db_user'
TOPE='    if mirar_tope and (razon := billing_service.razon_del_tope(entidad)):'
CUPO="$TOPE
        raise HTTPException(status_code=402, detail=_detalle_402(entidad, razon))
"
SUELTA_ANALYZE='    await _soltar_conexion(db)
    mapper = GeminiMigrationHeaderMapper'
SUELTA_NCM='        await _soltar_conexion(db)
        try:
            de_gemini'
TRY='    try:
        await db.commit()
    except Exception as err:
        logging.warning("db release before slow wait failed: %s", err)
        await db.close()'

casos "sin sabotaje"
# Con un campo Body, FastAPI lee el cuerpo antes de mirar el plan y la cuota.
en_codigo "$M" "from fastapi import FastAPI," "from fastapi import Body, FastAPI," \
  "$FIRMA_MANUAL" "${FIRMA_MANUAL/),/),
    _cuerpo: dict = Body(None),}" &&
  casos "manual lee el cuerpo antes del 402" test_cuenta_que_no_puede_cargar_no_lee_el_cuerpo
# Sin el tope en la dependencia, la cuenta al tope sube y valida el cuerpo antes del 402.
en_codigo "$M" "$CUPO" "" &&
  casos "manual no mira el tope antes del cuerpo" test_cuenta_que_no_puede_cargar_no_lee_el_cuerpo
en_codigo "$M" "$SUELTA_COBRO" "    return db_user" &&
  casos "_billing_vigente no suelta" "$T[body-404]" "$T[body-400]" \
    "$T[process_pdf-422]" "$B[/api/ncm/sugerir]" "$B[/api/migrations/analyze]" "$B[/api/operations/manual]"
en_codigo "$M" "$SUELTA_NCM" "        try:
            de_gemini" &&
  casos "sugerir no suelta antes de Gemini" "$T[_suggest_ncm_with_gemini-200]" "$B[/api/ncm/sugerir]"
en_codigo "$M" "$SUELTA_ANALYZE" "    mapper = GeminiMigrationHeaderMapper" &&
  casos "analyze no suelta antes de leer el archivo" "$T[_read_sheets-200]" \
    test_analyze_con_el_pool_lleno_no_deja_nada_a_medias "$B[/api/migrations/analyze]"
en_codigo "$M" "$TRY" "    await db.commit()" &&
  TEXTO="conexión caída" casos "soltar sin try" \
    "$B[/api/ncm/sugerir]" "$B[/api/migrations/analyze]" "$B[/api/operations/manual]"
# rollback vence lo leído y analyze lee existing_clients sin await.
en_codigo "$M" "        await db.close()" "        await db.rollback()" &&
  TEXTO="MissingGreenlet" casos "rollback en vez de close" "$B[/api/migrations/analyze]"

git checkout -q -- proyecto_maria
creditos "créditos sin sabotaje" 0 "pierden: 0; no valen: 0; sin carrera: 0"
# La carga manual vuelve a vencer los créditos sin candado antes de contar.
en_codigo "$M" "async def require_billing_vigente(" 'async def _cupo_sin_candado(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == user["username"]))
    db_user = result.scalars().first()
    entidad, _ = await _get_billing_entity(db, db_user)
    await _vencer_y_guardar(db, entidad)
    ok, reason = billing_service.can_create_operation(entidad)
    if not ok:
        raise HTTPException(status_code=402, detail=_detalle_402(entidad, reason))
    return db_user


async def require_billing_vigente(' \
  "$FIRMA_MANUAL" "${FIRMA_MANUAL/require_cupo_del_plan/_cupo_sin_candado}" &&
  creditos "manual con el cupo sin candado (D188)" 1 "PIERDE | usuario, carrera"
# El tope de la dependencia vence los créditos sin candado y pisa la recarga.
en_codigo "$M" "$TOPE" '    if mirar_tope and (razon := billing_service.can_create_operation(entidad)[1]):' &&
  creditos "el tope de la dependencia vence créditos" 1 "PIERDE | usuario, carrera"
git checkout -q -- proyecto_maria
exit $((FALLAS > 0))
