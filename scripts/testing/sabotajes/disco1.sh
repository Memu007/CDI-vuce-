#!/usr/bin/env bash
# Negativos de DISCO-1: cada sabotaje deshace una regla del historial de NCM
# en la base (por dueño, misma clave, confirmar suma y actualiza, importar
# igual que antes, confirmaciones a la vez, archivos viejos una sola vez, un
# archivo roto no frena) y tests/test_disco1.py tiene que fallar por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/disco1.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y un DATA_DIR
# temporal por prueba: no toca tu copia ni datos compartidos. Sale con error
# si un sabotaje no encuentra su patrón o no pone rojo donde tiene que ponerlo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
       DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
FALLAS=0

pytest_d1() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov -p no:randomly -p no:cacheprovider tests/test_disco1.py 2>&1
}

# aplicar <archivo> <viejo> <nuevo> [<viejo> <nuevo>]...: cada patrón tiene
# que estar una sola vez.
aplicar() {
  "$PY" - "$@" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
pares = sys.argv[2:]
for viejo, nuevo in zip(pares[::2], pares[1::2]):
    if s.count(viejo) != 1:
        sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
    s = s.replace(viejo, nuevo)
open(p, "w", encoding="utf-8").write(s)
PYEOF
}

# juzgar <nombre> <salida> <código> <lo que el rojo tiene que decir>...
juzgar() {
  local nombre="$1" salida="$2" codigo="$3"; shift 3
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1)); return
  fi
  for esperado in "$@"; do
    if ! grep -qF -- "$esperado" <<<"$salida"; then
      echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"
      grep -E "^(FAILED|E )" <<<"$salida" | head -8; FALLAS=$((FALLAS+1)); return
    fi
  done
  echo "ROJO  | $nombre: $(printf '«%s» ' "$@")"
}

# sabotaje <nombre> <n pares> <viejo> <nuevo> [...] <lo que el rojo tiene que decir>...
sabotaje() {
  local nombre="$1" n="$2"; shift 2
  local pares=("${@:1:$((n*2))}"); shift $((n*2))
  git checkout -q -- proyecto_maria/
  if ! aplicar "$M" "${pares[@]}"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  local salida codigo
  salida="$(pytest_d1)"; codigo=$?
  juzgar "$nombre" "$salida" "$codigo" "$@"
  git checkout -q -- proyecto_maria/
}

M=proyecto_maria/main.py
T=tests/test_disco1.py

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
if ! pytest_d1 >"$TMPD/base.log"; then
  echo "BASE  | las pruebas ya están en rojo sin sabotaje: no se puede medir nada"; grep -E "^FAILED" "$TMPD/base.log"; exit 1
fi

# --- confirmar: suma uno, actualiza la NCM, queda en la base
sabotaje "confirmar no suma" 1 \
  '"count": NcmHistorial.count + 1}' '"count": NcmHistorial.count}' \
  "FAILED $T::test_confirmar_guarda_en_la_base_suma_y_actualiza_la_ncm" "'count': 1"
sabotaje "confirmar no actualiza la NCM" 1 \
  'set_={"ncm": ins.excluded.ncm, "count": NcmHistorial.count + 1}' 'set_={"count": NcmHistorial.count + 1}' \
  "FAILED $T::test_confirmar_guarda_en_la_base_suma_y_actualiza_la_ncm" "8413.70.10"
sabotaje "confirmar no hace commit" 1 \
  $'        set_={"ncm": ins.excluded.ncm, "count": NcmHistorial.count + 1},\n    ))\n    await db.commit()' \
  $'        set_={"ncm": ins.excluded.ncm, "count": NcmHistorial.count + 1},\n    ))' \
  "FAILED $T::test_confirmar_guarda_en_la_base_suma_y_actualiza_la_ncm"
sabotaje "confirmar también escribe el archivo en DATA_DIR" 1 \
  $'    await _sumar_uso_ncm(db, user["username"], descripcion, ncm)\n' \
  $'    await _sumar_uso_ncm(db, user["username"], descripcion, ncm)\n    with open(os.path.join(DATA_DIR, f"ncm_historial_{_nombre_archivo_historial(user[\'username\'])}.json"), "w") as _f:\n        json.dump(await load_ncm_historial(db, user["username"]), _f)\n' \
  "FAILED $T::test_confirmar_guarda_en_la_base_suma_y_actualiza_la_ncm" "ncm_historial_"
sabotaje "la clave normaliza la descripción" 1 \
  'hashlib.sha256(descripcion.encode("utf-8"))' 'hashlib.sha256(descripcion.strip().lower().encode("utf-8"))' \
  "FAILED $T::test_la_clave_es_la_descripcion_tal_cual"

# --- por dueño
sabotaje "el historial no se filtra por dueño" 1 \
  $'        .where(NcmHistorial.owner_username == owner_username)\n        .order_by(NcmHistorial.id)\n    )\n    return {desc' \
  $'        .order_by(NcmHistorial.id)\n    )\n    return {desc' \
  "FAILED $T::test_un_dueno_no_ve_ni_pisa_el_historial_de_otro" "b ve el historial de a"

# --- dos confirmaciones a la vez: leer, sumar en Python y escribir pierde cuentas
sabotaje "confirmar lee y después escribe" 1 \
  $'    ins = _insert_ncm_historial().values(**_fila_ncm_historial(owner_username, descripcion, ncm))\n    await db.execute(ins.on_conflict_do_update(\n        index_elements=["owner_username", "clave"],\n        set_={"ncm": ins.excluded.ncm, "count": NcmHistorial.count + 1},\n    ))\n    await db.commit()' \
  $'    fila = (await db.execute(select(NcmHistorial).where(\n        NcmHistorial.owner_username == owner_username,\n        NcmHistorial.clave == _clave_ncm_historial(descripcion)))).scalar_one_or_none()\n    if fila is None:\n        db.add(NcmHistorial(**_fila_ncm_historial(owner_username, descripcion, ncm)))\n    else:\n        fila.count, fila.ncm = fila.count + 1, ncm\n    await db.commit()' \
  "FAILED $T::test_confirmaciones_a_la_vez_no_pierden_cuentas"

# --- importar: suma igual y cuenta duplicados igual; todo o nada
sabotaje "importar le pone cuenta 1 a lo que ya estaba" 1 \
  'index_elements=["owner_username", "clave"], set_={"ncm": ins.excluded.ncm},' \
  'index_elements=["owner_username", "clave"], set_={"ncm": ins.excluded.ncm, "count": 1},' \
  "FAILED $T::test_importar_suma_igual_y_cuenta_duplicados_igual"
sabotaje "importar le suma uno a lo que ya estaba" 1 \
  'index_elements=["owner_username", "clave"], set_={"ncm": ins.excluded.ncm},' \
  'index_elements=["owner_username", "clave"], set_={"ncm": ins.excluded.ncm, "count": NcmHistorial.count + 1},' \
  "FAILED $T::test_importar_suma_igual_y_cuenta_duplicados_igual"
sabotaje "importar no actualiza la NCM de lo que ya estaba" 1 \
  'index_elements=["owner_username", "clave"], set_={"ncm": ins.excluded.ncm},' \
  'index_elements=["owner_username", "clave"], set_={"ncm": NcmHistorial.ncm},' \
  "FAILED $T::test_importar_suma_igual_y_cuenta_duplicados_igual"
sabotaje "importar hace commit por tanda" 1 \
  $'            index_elements=["owner_username", "clave"], set_={"ncm": ins.excluded.ncm},\n        ))\n    await db.commit()' \
  $'            index_elements=["owner_username", "clave"], set_={"ncm": ins.excluded.ncm},\n        ))\n        await db.commit()' \
  "FAILED $T::test_si_no_se_puede_guardar_lo_importado_da_500_y_no_queda_nada"

# --- archivos viejos: una sola vez, sin duplicar, sin frenar el arranque
sabotaje "cargar un archivo dos veces suma otra vez" 1 \
  'await db.execute(ins.on_conflict_do_nothing(index_elements=["owner_username", "clave"]))' \
  'await db.execute(ins.on_conflict_do_update(index_elements=["owner_username", "clave"], set_={"count": NcmHistorial.count + ins.excluded.count}))' \
  "FAILED $T::test_los_archivos_viejos_se_cargan_una_sola_vez"
sabotaje "cargar un archivo pisa lo confirmado después" 1 \
  'await db.execute(ins.on_conflict_do_nothing(index_elements=["owner_username", "clave"]))' \
  'await db.execute(ins.on_conflict_do_update(index_elements=["owner_username", "clave"], set_={"count": ins.excluded.count}))' \
  "FAILED $T::test_los_archivos_viejos_se_cargan_una_sola_vez"
sabotaje "el archivo cargado no se renombra" 1 \
  '        os.replace(ruta, ruta + ".migrado")' '        pass' \
  "FAILED $T::test_los_archivos_viejos_se_cargan_una_sola_vez" "el archivo cargado no se tiene que volver a leer"
sabotaje "un archivo roto frena a los demás" 2 \
  'except (OSError, ValueError) as e:' 'except OSError as e:' \
  $'                try:\n                    await _cargar_archivo_historial(db, ruta, por_nombre)\n                except Exception:\n                    await db.rollback()\n                    logging.exception("[DISCO-1] %s no se pudo cargar; queda en su lugar", os.path.basename(ruta))' \
  $'                await _cargar_archivo_historial(db, ruta, por_nombre)' \
  "FAILED $T::test_un_archivo_roto_va_al_log_y_no_frena_a_los_demas"
sabotaje "un archivo roto frena el arranque" 3 \
  'except (OSError, ValueError) as e:' 'except OSError as e:' \
  $'                try:\n                    await _cargar_archivo_historial(db, ruta, por_nombre)\n                except Exception:\n                    await db.rollback()\n                    logging.exception("[DISCO-1] %s no se pudo cargar; queda en su lugar", os.path.basename(ruta))' \
  $'                await _cargar_archivo_historial(db, ruta, por_nombre)' \
  $'    except Exception:\n        logging.exception("[DISCO-1] no se pudieron cargar los historiales de DATA_DIR")' \
  $'    finally:\n        pass' \
  "FAILED $T::test_un_archivo_roto_va_al_log_y_no_frena_a_los_demas" "JSONDecodeError"
sabotaje "las entradas salteadas no van al log" 1 \
  $'        logging.warning("[DISCO-1] %s: %d entradas sin NCM no se cargaron", nombre, salteadas)' \
  $'        pass' \
  "FAILED $T::test_un_archivo_roto_va_al_log_y_no_frena_a_los_demas" "entradas sin NCM"
sabotaje "una entrada sin NCM se carga igual" 1 \
  'if not desc.strip() or not isinstance(ncm, str) or not ncm.strip():' 'if False:' \
  "FAILED $T::test_un_archivo_roto_va_al_log_y_no_frena_a_los_demas"
sabotaje "un nombre ambiguo se le carga al primero" 1 \
  '    if len(duenos) != 1:' '    if not duenos:' \
  "FAILED $T::test_un_archivo_sin_dueno_claro_no_se_le_carga_a_nadie"
sabotaje "el arranque no carga los archivos" 1 \
  $'    await _migrate_ncm_historial_archivos()\n' '' \
  "FAILED $T::test_el_arranque_carga_los_archivos" "assert [] == [1]"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
