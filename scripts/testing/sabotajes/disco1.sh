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
      grep -E "^(FAILED|E |FALLA)" <<<"$salida" | cut -c1-300 | head -8; FALLAS=$((FALLAS+1)); return
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
  "FAILED $T::test_confirmar_guarda_en_la_base_suma_y_actualiza_la_ncm" "confirmar otra vez suma uno y actualiza la NCM"
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
  "FAILED $T::test_confirmar_guarda_en_la_base_suma_y_actualiza_la_ncm" "el historial ya no se escribe en DATA_DIR"
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
  'os.replace(ruta, _ruta_migrado_libre(ruta))' 'pass' \
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
  $'        logging.warning("[DISCO-1] %s: %d entradas sin descripción o sin NCM no se cargaron", nombre, salteadas)' \
  $'        pass' \
  "FAILED $T::test_un_archivo_roto_va_al_log_y_no_frena_a_los_demas" "entradas sin descripción o sin NCM"
sabotaje "una entrada sin NCM se carga igual" 1 \
  'if not desc.strip() or not isinstance(ncm, str) or not ncm.strip():' 'if False:' \
  "FAILED $T::test_un_archivo_roto_va_al_log_y_no_frena_a_los_demas"
sabotaje "un nombre ambiguo se le carga al primero" 1 \
  '    if len(duenos) != 1:' '    if not duenos:' \
  "FAILED $T::test_un_archivo_sin_dueno_claro_no_se_le_carga_a_nadie"
sabotaje "el arranque no carga los archivos" 1 \
  $'    await _migrate_ncm_historial_archivos()\n' '' \
  "FAILED $T::test_el_arranque_carga_los_archivos" "assert [] == [1]"

# --- devolución de DISCO-1
sabotaje "la carga sin orden" 1 \
  $'        .where(NcmHistorial.owner_username == owner_username)\n        .order_by(NcmHistorial.id)' \
  $'        .where(NcmHistorial.owner_username == owner_username)' \
  "FAILED $T::test_sugerir_recorre_el_historial_en_el_orden_en_que_se_agrego"
sabotaje "todo el archivo en una sola sentencia" 1 \
  '_HISTORIAL_FILAS_POR_SENTENCIA = 150' '_HISTORIAL_FILAS_POR_SENTENCIA = 10**6' \
  "FAILED $T::test_importar_muchas_filas_va_en_tandas" "AssertionError: [7000]"
sabotaje "una cuenta cero o negativa se carga tal cual" 1 \
  'not isinstance(count, int) or count < 1:' 'not isinstance(count, int):' \
  "FAILED $T::test_un_archivo_viejo_con_cuenta_cero_o_negativa_carga_cuenta_uno" "'Codo sintetico cero', '7307.19.00', 0"
sabotaje "una descripción en blanco se carga" 1 \
  'if not desc.strip() or not isinstance(ncm, str)' 'if not isinstance(ncm, str)' \
  "FAILED $T::test_un_archivo_viejo_con_descripcion_en_blanco_no_la_carga"
sabotaje "el archivo cargado se borra" 1 \
  'os.replace(ruta, _ruta_migrado_libre(ruta))' 'os.remove(ruta)' \
  "FAILED $T::test_el_archivo_cargado_queda_como_migrado_con_su_contenido" "FileNotFoundError"
sabotaje "un .migrado anterior se pisa" 1 \
  $'    while os.path.exists(destino):' $'    while False:' \
  "FAILED $T::test_un_migrado_anterior_no_se_pisa" "FileNotFoundError"
sabotaje "las tandas reordenan por clave" 1 \
  $'    for i in range(0, len(filas), _HISTORIAL_FILAS_POR_SENTENCIA):' \
  $'    filas = sorted(filas, key=lambda f: f["clave"])\n    for i in range(0, len(filas), _HISTORIAL_FILAS_POR_SENTENCIA):' \
  "FAILED $T::test_importar_respeta_el_orden_del_archivo_para_sugerir" \
  "FAILED $T::test_un_archivo_viejo_se_carga_en_su_orden"
# En confirmar, 2001 letras también las frena el tope del catálogo: ahí el del
# historial lo distingue catalogolargo1.sh, con un texto que en NFC achica.
sabotaje "sin tope de descripción" 1 \
  '_HISTORIAL_MAX_DESCRIPCION = 2000' '_HISTORIAL_MAX_DESCRIPCION = 10**9' \
  "FAILED $T::test_importar_con_una_fila_que_la_base_no_guarda_da_400_y_no_guarda_nada[BBBB"
sabotaje "sin tope de NCM" 1 \
  '_HISTORIAL_MAX_NCM = 20' '_HISTORIAL_MAX_NCM = 10**9' \
  "FAILED $T::test_confirmar_con_algo_que_la_base_no_guarda_da_400_y_no_guarda[Bomba sintetica-888" \
  "FAILED $T::test_importar_con_una_fila_que_la_base_no_guarda_da_400_y_no_guarda_nada[Bomba sintetica-8413.70.10.0000000000000"
sabotaje "el tope no deja entrar el máximo" 1 \
  '        if len(texto) > tope:' '        if len(texto) >= tope:' \
  "FAILED $T::test_confirmar_en_el_tope_entra"
sabotaje "el NUL pasa" 1 \
  $'        if "\\x00" in texto:' $'        if False:' \
  "FAILED $T::test_confirmar_con_algo_que_la_base_no_guarda_da_400_y_no_guarda[Bomba\\x00sintetica" \
  "FAILED $T::test_confirmar_con_algo_que_la_base_no_guarda_da_400_y_no_guarda[Bomba sintetica-8413.70.10\\x00" \
  "FAILED $T::test_importar_con_una_fila_que_la_base_no_guarda_da_400_y_no_guarda_nada[Bomba\\x00sintetica"
sabotaje "medio par UTF-16 pasa" 1 \
  $'        if not _es_utf8(texto):\n            return' $'        if False:\n            return' \
  "FAILED $T::test_confirmar_con_algo_que_la_base_no_guarda_da_400_y_no_guarda[Bomba\\ud800sintetica" \
  "FAILED $T::test_importar_con_una_fila_que_la_base_no_guarda_da_400_y_no_guarda_nada[Bomba\\ud800sintetica"
sabotaje "confirmar no revisa" 1 \
  $'    problema = _problema_historial(descripcion, ncm)\n    if problema:' $'    problema = None\n    if problema:' \
  "FAILED $T::test_confirmar_con_algo_que_la_base_no_guarda_da_400_y_no_guarda[Bomba\\x00sintetica"
sabotaje "importar no revisa" 1 \
  $'            problema = _problema_historial(desc, ncm)\n            if problema:' $'            problema = None\n            if problema:' \
  "FAILED $T::test_importar_con_una_fila_que_la_base_no_guarda_da_400_y_no_guarda_nada[Bomba\\x00sintetica"
sabotaje "la fila mala va a errores y lo demás se guarda" 1 \
  $'        except HTTPException:\n            raise\n        except Exception as exc:\n            errores.append' \
  $'        except Exception as exc:\n            errores.append' \
  "FAILED $T::test_importar_con_una_fila_que_la_base_no_guarda_da_400_y_no_guarda_nada[BBBB" "assert 200 == 400"
sabotaje "un archivo viejo con un carácter que la base no guarda se carga" 1 \
  $'        if _problema_historial(desc, ncm):\n            invalidas += 1' $'        if False:\n            invalidas += 1' \
  "FAILED $T::test_un_archivo_viejo_con_caracteres_que_la_base_no_guarda_los_saltea"
sabotaje "la carga de archivos viejos no aplica los topes" 1 \
  $'        if _problema_historial(desc, ncm):\n            invalidas += 1' \
  $'        if "\\x00" in desc + ncm or not _es_utf8(desc + ncm):\n            invalidas += 1' \
  "FAILED $T::test_un_archivo_viejo_con_caracteres_que_la_base_no_guarda_los_saltea" "At index 0 diff: ('CCCCCCCCCC"
sabotaje "un NUL en el cliente pasa" 1 \
  'if "\x00" in client_id or not _es_utf8(client_id):' 'if False:' \
  "FAILED $T::test_confirmar_con_un_cliente_que_no_sirve_no_suma[cliente\\x00sintetico-400]" \
  "FAILED $T::test_confirmar_con_un_cliente_que_no_sirve_no_suma[cliente\\ud800sintetico-400]"
sabotaje "el cliente se revisa después de escribir" 2 \
  $'    if client_id:\n        if "\\x00" in client_id or not _es_utf8(client_id):\n            raise HTTPException(status_code=400, detail="El cliente tiene un carácter que no es texto válido.")\n        await _get_owned_client(db, client_id, user["username"])\n' '' \
  $'    await _sumar_uso_ncm(db, user["username"], descripcion, ncm)\n' \
  $'    await _sumar_uso_ncm(db, user["username"], descripcion, ncm)\n    if client_id:\n        if "\\x00" in client_id or not _es_utf8(client_id):\n            raise HTTPException(status_code=400, detail="El cliente tiene un carácter que no es texto válido.")\n        await _get_owned_client(db, client_id, user["username"])\n' \
  "FAILED $T::test_confirmar_con_un_cliente_que_no_sirve_no_suma[cliente-ajeno-sintetico-404]"

# Postgres: con la transacción abortada, sugerir sin rollback no sugiere nada.
# SQLite no aborta la transacción: sólo se ve contra un Postgres local.
sabotaje_pg() {
  local nombre="$1" viejo="$2" nuevo="$3"; shift 3
  if [ -z "${PG_URL:-}" ]; then
    echo "SIN PG| $nombre: falta PG_URL (un Postgres local y descartable)"; SIN_PG=$((SIN_PG+1)); return
  fi
  git checkout -q -- proyecto_maria/
  if ! aplicar "$M" "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  local salida codigo
  salida="$(timeout 900 "$PY" scripts/testing/disco1_postgres.py "$PG_URL" 2>&1)"; codigo=$?
  juzgar "$nombre" "$salida" "$codigo" "$@"
  git checkout -q -- proyecto_maria/
}
SIN_PG=0
sabotaje_pg "sugerir sin rollback si falla la memoria del cliente" \
  $'            await db.rollback()\n            logging.warning("ncm suggestion client memory unavailable: %s", err)' \
  $'            logging.warning("ncm suggestion client memory unavailable: %s", err)' \
  "FALLA | falla la memoria del cliente: sigue el historial: []" \
  "FALLA | falla la memoria del cliente: sigue el proveedor: [('historial', None)]"
sabotaje_pg "sugerir sin rollback si falla el catálogo del proveedor" \
  $'            await db.rollback()\n            logging.warning("ncm suggestion vendor catalog unavailable: %s", err)' \
  $'            logging.warning("ncm suggestion vendor catalog unavailable: %s", err)' \
  "FALLA | falla el catálogo del proveedor: sigue el historial: []"
sabotaje_pg "importar sin el bloqueo por dueño" \
  $'    if not IS_SQLITE:\n        from sqlalchemy import text as sa_text\n        await db.execute(sa_text("SELECT pg_advisory_xact_lock' \
  $'    if False:\n        from sqlalchemy import text as sa_text\n        await db.execute(sa_text("SELECT pg_advisory_xact_lock' \
  "FALLA | dos importaciones a la vez en orden contrario, vuelta 0: [200, 500]" \
  "FALLA | la carga del archivo de A espera a la importación de A: terminó"
sabotaje_pg "importar sin tomar el bloqueo (la carga sí lo toma)" \
  $'    await _bloquear_historial(db, owner_username)\n' '' \
  "FALLA | dos importaciones a la vez en orden contrario, vuelta 0: [200, 500]" \
  "FALLA | la carga del archivo de A espera a la importación de A: terminó"
sabotaje_pg "cargar archivos viejos sin tomar el bloqueo" \
  $'    await _bloquear_historial(db, dueno)\n' '' \
  "FALLA | la carga del archivo de A espera a la importación de A: terminó"
sabotaje_pg "el bloqueo sin el dueño en la clave" \
  'f"ncm_historial:{owner_username}"' '"ncm_historial:"' \
  "FALLA | la importación de B no espera el bloqueo de A: esperó" \
  "FALLA | la carga del archivo de B no espera el bloqueo de A: esperó"
sabotaje_pg "importar todo en una sola sentencia (Postgres)" \
  '_HISTORIAL_FILAS_POR_SENTENCIA = 150' '_HISTORIAL_FILAS_POR_SENTENCIA = 10**6' \
  "FALLA | importar 7000 filas en Postgres: 500"
[ "$SIN_PG" -eq 0 ] || echo "sabotajes de Postgres sin correr: $SIN_PG"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
