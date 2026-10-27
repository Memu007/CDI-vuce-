#!/usr/bin/env bash
# Negativos de ESTUDIO-1b: cada sabotaje deshace una línea de la pieza y la
# prueba tiene que fallar por ese motivo. Primero la API
# (tests/test_estudio1b.py), después la pantalla
# (scripts/testing/pantalla_estudio1b.js).
#
# uso: PY=/ruta/al/venv/bin/python [PUERTO=8853] scripts/testing/sabotajes/estudio1b.sh [SHA]
# Trabaja en un worktree descartable con SQLite propia y sin terceros: no toca
# tu copia ni datos compartidos. Los sabotajes de la pantalla tocan también la
# API, así que cada corrida de la pantalla levanta la API de nuevo, con una
# base vacía.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PUERTO="${PUERTO:-8853}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
API=""
trap '[ -n "$API" ] && kill $API 2>/dev/null; git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
FALLAS=0

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4" esperado="$5"
  git checkout -q -- proyecto_maria/
  rm -f test.db
  if ! "$PY" - "$archivo" "$viejo" "$nuevo" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
viejo, nuevo = sys.argv[2], sys.argv[3]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
PYEOF
  then echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return; fi
  local salida codigo
  salida="$(correr)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep -E "FAILED|FALLA" <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  fi
}

M=proyecto_maria/main.py
T=tests/test_estudio1b.py

# ------------------------------------------------------------------ la API
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
correr() { "$PY" -m pytest -q --no-cov -p no:cacheprovider "$T" 2>&1; }

rm -f test.db
if ! correr >/dev/null; then
  echo "BASE  | la prueba de la API ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FAILED; exit 1
fi

# 1. D23 (b): generar con el CUIT del perfil cuenta como lo último usado.
sabotaje $M "el uso del perfil no se anota" \
  '        elif con_el_perfil:' '        elif False:' \
  "FAILED $T::test_generar_con_el_perfil_despues_de_un_estudio_preselecciona_el_perfil"
sabotaje $M "la preselección no mira el uso del perfil" \
  '        usados.append((_utc(uso_perfil.last_used_at), None))' '        pass' \
  "FAILED $T::test_generar_con_el_perfil_despues_de_un_estudio_preselecciona_el_perfil"
sabotaje $M "el uso del perfil cuenta sólo con cuit_agr vacío (la pantalla siempre lo manda)" \
  'con_el_perfil = estudio is None and bool(effective_cuit_agr) and effective_cuit_agr == cuit_del_perfil' \
  'con_el_perfil = estudio is None and not request.cuit_agr and bool(effective_cuit_agr)' \
  "FAILED $T::test_el_cuit_del_perfil_en_cuit_agr_cuenta_como_uso_del_perfil"
sabotaje $M "un cuit_agr ajeno cuenta como uso del perfil" \
  'con_el_perfil = estudio is None and bool(effective_cuit_agr) and effective_cuit_agr == cuit_del_perfil' \
  'con_el_perfil = estudio is None and bool(effective_cuit_agr)' \
  "FAILED $T::test_un_cuit_agr_propio_no_cuenta_como_uso_del_perfil"
# Anotado al recibir el pedido, sin esperar a que el TXT salga: un pedido que
# después da 400 (moneda vacía) cuenta como uso del perfil.
sabotaje $M "el uso del perfil se anota antes de generar" \
  $'    estudio = await _estudio_elegido(db, request.estudio_id, user["username"])\n    if not request.items:' \
  $'    estudio = await _estudio_elegido(db, request.estudio_id, user["username"])\n    if estudio is None:\n        await db.merge(UsoCuitPerfil(owner_username=user["username"], last_used_at=datetime.now(timezone.utc)))\n        await db.commit()\n    if not request.items:' \
  "FAILED $T::test_los_avisos_y_un_txt_que_no_sale_con_el_perfil_no_cuentan"
sabotaje $M "los avisos cuentan como uso del perfil" \
  $'    estudio = await _estudio_elegido(db, request.estudio_id, user["username"])\n    items = _items_con_procedencia(request)' \
  $'    estudio = await _estudio_elegido(db, request.estudio_id, user["username"])\n    if estudio is None:\n        await db.merge(UsoCuitPerfil(owner_username=user["username"], last_used_at=datetime.now(timezone.utc)))\n        await db.commit()\n    items = _items_con_procedencia(request)' \
  "FAILED $T::test_los_avisos_y_un_txt_que_no_sale_con_el_perfil_no_cuentan"
sabotaje $M "el uso del perfil se lee de otra cuenta" \
  '    uso_perfil = await db.get(UsoCuitPerfil, user["username"])' \
  '    uso_perfil = (await db.execute(select(UsoCuitPerfil).order_by(UsoCuitPerfil.last_used_at.desc()))).scalars().first()' \
  "FAILED $T::test_el_uso_del_perfil_es_de_cada_cuenta"
sabotaje $M "el estudio único gana aunque el perfil se haya usado después" \
  $'    if usados:\n        # Con la misma hora' \
  $'    if len(estudios) == 1:\n        preseleccionado = estudios[0].id\n    elif usados:\n        # Con la misma hora' \
  "FAILED $T::test_un_estudio_unico_cargado_despues_de_usar_el_perfil_no_gana"
sabotaje $M "el estudio único sin usar no gana" \
  '    elif len(estudios) == 1:' '    elif False:' \
  "FAILED $T::test_un_estudio_unico_sin_uso_del_perfil_gana"
sabotaje $M "se preselecciona lo usado hace más tiempo" \
  'preseleccionado = max(usados, key=lambda u: (u[0], u[1] is None))[1]' \
  'preseleccionado = min(usados, key=lambda u: (u[0], u[1] is None))[1]' \
  "FAILED $T::test_generar_con_el_perfil_despues_de_un_estudio_preselecciona_el_perfil"

# 2. estudio_id: sólo "" (o la falta del campo) es «sin estudio».
sabotaje $M "vuelve el strip: espacios caen al perfil" \
  $'    if estudio_id == "":\n        return None' \
  $'    if isinstance(estudio_id, str) and not estudio_id.strip():\n        return None' \
  "FAILED $T::test_un_estudio_id_escrito_como_vacio_da_400_y_no_cae_al_perfil[/generate_maria/avisos-  ]"
sabotaje $M "vuelve _vacio_escrito: «null» cae al perfil" \
  $'        "numero_factura",\n        mode="before",' \
  $'        "numero_factura", "estudio_id",\n        mode="before",' \
  "FAILED $T::test_un_estudio_id_escrito_como_vacio_da_400_y_no_cae_al_perfil[/generate_maria/avisos-null]"
sabotaje $M "un null de JSON o un 0 caen al perfil" \
  '    if estudio_id == "":' '    if not estudio_id:' \
  "FAILED $T::test_un_estudio_id_escrito_como_vacio_da_400_y_no_cae_al_perfil[/generate_maria/avisos-0]"
sabotaje $M "un estudio_id con espacios alrededor se acepta" \
  'select(Estudio).where(Estudio.id == estudio_id, Estudio.owner_username == username)' \
  'select(Estudio).where(Estudio.id == estudio_id.strip(), Estudio.owner_username == username)' \
  "FAILED $T::test_un_estudio_id_con_espacios_alrededor_da_400"

# 3. El nombre del estudio: sin caracteres invisibles ni de dirección.
sabotaje $M "el nombre con caracteres invisibles entra" \
  ' or unicodedata.category(c) == "Cf"' '' \
  "FAILED $T::test_el_alta_rechaza_un_nombre_invisible_o_al_reves[\\u202eodatnevnI oidutsE]"
sabotaje $M "se rechazan otros alfabetos" \
  'unicodedata.category(c) == "Cf"' 'unicodedata.category(c) in ("Cf", "Lo")' \
  "FAILED $T::test_el_alta_acepta_un_nombre_con_acentos_y_otros_alfabetos[Estudio \\u4e2d\\u6587]"

# ------------------------------------------------------------- la pantalla
git checkout -q -- proyecto_maria/
export ENVIRONMENT=development GEMINI_API_KEY=test-key \
       JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef EMAIL_VERIFICATION_REQUIRED=false \
       ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x
export BASE_URL="http://127.0.0.1:$PUERTO"
# Cada corrida, la API de nuevo (con lo saboteado) y una base vacía.
correr() {
  rm -f "$TMPD/local.db"
  DATABASE_URL="sqlite+aiosqlite:///$TMPD/local.db" "$PY" -m uvicorn proyecto_maria.main:app \
    --host 127.0.0.1 --port "$PUERTO" >"$TMPD/api.log" 2>&1 &
  API=$!
  for _ in $(seq 1 60); do curl -fsS "$BASE_URL/health" >/dev/null 2>&1 && break; sleep 1; done
  if ! curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
    echo "FALLA: la API no levantó"; tail -5 "$TMPD/api.log"; kill $API 2>/dev/null; wait $API 2>/dev/null; API=""; return 1
  fi
  local codigo
  node scripts/testing/pantalla_estudio1b.js 2>&1; codigo=$?
  kill $API 2>/dev/null; wait $API 2>/dev/null; API=""
  return $codigo
}
if ! correr >/dev/null; then
  echo "BASE  | la pantalla ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FALLA; exit 1
fi

J=proyecto_maria/static/v2/screens/estudios.js

sabotaje $M "pantalla: el uso del perfil no se anota" \
  '        elif con_el_perfil:' '        elif False:' \
  "FALLA: después de generar con el perfil, en la operación siguiente viene elegido"
sabotaje $M "pantalla: el estudio único sin usar no gana" \
  '    elif len(estudios) == 1:' '    elif False:' \
  "FALLA: el estudio único sin uso del perfil no viene elegido"
sabotaje $J "pantalla: sin preselección se elige el primer estudio" \
  ": (ids.indexOf(datos.preseleccionado) >= 0 ? datos.preseleccionado : '');" \
  ": (ids.indexOf(datos.preseleccionado) >= 0 ? datos.preseleccionado : ids[0]);" \
  "FALLA: después de generar con el perfil, en la operación siguiente viene elegido"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
