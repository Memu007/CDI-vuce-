#!/usr/bin/env bash
# Negativos de ENTRADAS-2: cada sabotaje deshace una regla de la pieza y
# tests/test_entradas2.py tiene que fallar en el caso de esa regla.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/entradas2.sh [SHA]
# Trabaja en un worktree descartable con SQLite propia.
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


T=tests/test_entradas2.py
M=proyecto_maria/main.py
NUM="FAILED $T::test_manual_con_numero_no_valido_da_400_y_no_guarda"
OBJ="FAILED $T::test_manual_con_algo_que_no_es_objeto_da_400"
GUA="FAILED $T::test_manual_guarda_lo_de_afuera_en_la_forma_que_entra_en_su_columna"
CLI="FAILED $T::test_texto_del_cliente_que_no_se_puede_guardar_queda_con_reemplazo"
SAV="FAILED $T::test_guardar_al_cliente_con_numero_no_valido_da_400_y_no_guarda"
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
correr() { "$PY" -m pytest -q --no-cov -p no:cacheprovider -W ignore -rf "$T" 2>&1; }

rm -f test.db
if ! correr >/dev/null; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FAILED; exit 1
fi
echo "BASE  | en verde"

# --- Operación manual
sabotaje $M "un número no finito pasa" "$NUM[nan]" \
  "    if not math.isfinite(numero):" "    if False:"
sabotaje $M "el total no se revisa" "$NUM[total_que_desborda]" \
  'total_value = _numero_de_afuera(sum(it["valor_unitario"] * it["cantidad"] for it in items), "El valor total")' \
  'total_value = sum(it["valor_unitario"] * it["cantidad"] for it in items)'
sabotaje $M "un cuerpo que no es objeto pasa" "$OBJ[cuerpo_lista]" \
  '    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail=_AVISO_NO_ES_OBJETO)
    client_id' '    client_id'
sabotaje $M "un ítem que no es objeto pasa" "$OBJ[item_texto]" \
  "if not all(isinstance(it, dict) for it in items_raw):" "if False:"
sabotaje $M "la descripción no se limpia" "$GUA[nul_en_descripcion]" \
  'descripcion=_guardable_en_pg(str(it.get("descripcion", "") or "")),' 'descripcion=str(it.get("descripcion", "") or ""),'
sabotaje $M "la pieza no se limpia" "$GUA[surrogate_en_pieza]" \
  'pieza=_guardable_en_pg(str(it.get("pieza", "") or ""))[:20],' 'pieza=str(it.get("pieza", "") or "")[:20],'
sabotaje $M "la pieza no se corta" "$GUA[pieza_mas_larga_que_su_columna]" \
  'pieza=_guardable_en_pg(str(it.get("pieza", "") or ""))[:20],' 'pieza=_guardable_en_pg(str(it.get("pieza", "") or "")),'
sabotaje $M "el grupo fuera de rango se guarda" "$GUA[grupo_id_fuera_de_rango]" \
  'grupo_id=_grupo_id_o_none(it.get("grupo_id")),' 'grupo_id=it.get("grupo_id"),'

# --- Clientes
sabotaje $M "el alta no limpia los textos" "$CLI[alta-nul]" \
  "    client = _guardable_en_pg(client)" "    pass"
sabotaje $M "la edición no limpia los textos" "$CLI[edicion-nul]" \
  "    client_data = _guardable_en_pg(client_data)" "    pass"
sabotaje $M "el email repetido en la edición no da 409" \
  "FAILED $T::test_editar_cliente_con_el_email_de_otro_da_409_y_no_cambia_nada" \
  'raise HTTPException(status_code=409, detail=f"Ya tenés un cliente con el email {email}") from e' 'raise'

# --- Guardar al cliente
sabotaje $M "un no finito fuera de los números leídos pasa" "$SAV[nan_en_resumen_que_va_crudo_al_json]" \
  "    if _tiene_no_finito(data):" "    if False:"
sabotaje $M "un entero de más pasa" "$SAV[resumen_items_enorme]" \
  "    if not -2**31 <= numero < 2**31:" "    if False:"
sabotaje $M "resumen.items de texto no se revisa" "$SAV[resumen_items_de_texto]" \
  'total_items=_entero_de_afuera(resumen.get("items", len(items)), "La cantidad de ítems"),' \
  'total_items=int(resumen.get("items", len(items))),'
sabotaje $M "la cantidad de un ítem no se revisa" "$SAV[cantidad_de_texto_en_items]" \
  'cantidad=_numero_de_afuera(item.get("cantidad"), "La cantidad"),' 'cantidad=float(item.get("cantidad") or 0),'

# --- Ruta, agrupar y clave
sabotaje $M "el NUL en la ruta llega a la ruta" "FAILED $T::test_nul_en_la_ruta_da_404_antes_de_llegar_a_la_ruta[GET-" \
  "app.add_middleware(_RutaSinNul)" ""
sabotaje $M "agrupar no tiene tope" "FAILED $T::test_agrupar_con_mas_ids_de_los_que_acepta_da_422" \
  "Field(default=[], max_length=10000)" "Field(default=[])"
sabotaje $M "el alta de estudio no pide número o símbolo" \
  "FAILED $T::test_alta_de_estudio_pide_la_misma_clave_que_el_registro" \
  "    _exigir_politica_de_clave(req.password)" '    if len(req.password) < 8: raise HTTPException(status_code=400, detail="corta")'

git checkout -q -- proyecto_maria/
echo "sabotajes con falla: $FALLAS"
[ "$FALLAS" -eq 0 ]
