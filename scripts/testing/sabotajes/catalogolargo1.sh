#!/usr/bin/env bash
# Negativos de CATALOGO-LARGO-1: cada sabotaje deshace una línea de la pieza y
# tests/test_catalogo_largo1.py tiene que ponerse roja por ese motivo. Con
# PG_URL (un Postgres local y descartable), también la migración contra
# scripts/testing/catalogo_largo1_postgres.py.
#
# uso: PY=/ruta/al/venv/bin/python [PG_URL=postgresql://cdi@127.0.0.1:5432/postgres] \
#        scripts/testing/sabotajes/catalogolargo1.sh [SHA]
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
T=tests/test_catalogo_largo1.py
PRUEBA=("$PY" -m pytest -q --no-cov -p no:cacheprovider "$T")
PRUEBA_PG=("$PY" -I scripts/testing/catalogo_largo1_postgres.py "$PG_URL")

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>
# Corre la prueba de "${CORRE[@]}".
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
  salida="$("${CORRE[@]}" 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "VERDE | $nombre: la prueba no lo vio"; FALLAS=$((FALLAS+1))
  elif grep -qF -- "$esperado" <<<"$salida"; then
    echo "ROJO  | $nombre: dice «$esperado»"
  else
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"
    grep -E "^E |^FALLA" <<<"$salida" | head -5; FALLAS=$((FALLAS+1))
  fi
}

M=proyecto_maria/main.py
CS=proyecto_maria/core/catalog_service.py

CORRE=("${PRUEBA[@]}")
if ! "${CORRE[@]}" >/dev/null 2>&1; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; exit 1
fi

sabotaje $CS "el catálogo mide el largo sin pasar a NFC" \
  '    if len(unicodedata.normalize("NFC", descripcion)) > MAX_DESCRIPCION:' \
  '    if len(descripcion) > MAX_DESCRIPCION:' \
  "FAILED $T::test_guardar_en_el_catalogo_respeta_el_tope[nfc-que-crece]"
sabotaje $CS "el tope no deja entrar el máximo" \
  '    if len(unicodedata.normalize("NFC", descripcion)) > MAX_DESCRIPCION:' \
  '    if len(unicodedata.normalize("NFC", descripcion)) >= MAX_DESCRIPCION:' \
  "FAILED $T::test_guardar_en_el_catalogo_respeta_el_tope[2000]"
sabotaje $CS "guardar en el catálogo no controla el largo" \
  '        validar_largo(desc)' \
  '        pass' \
  "FAILED $T::test_guardar_en_el_catalogo_respeta_el_tope[2001]"
sabotaje $CS "cambiar un producto no controla el largo" \
  '        validar_largo(val)' \
  '        pass' \
  "FAILED $T::test_cambiar_un_producto_respeta_el_tope_y_alcanza_claves_largas"
sabotaje $M "guardar-uso no controla el largo en NFC" \
  '        catalog_svc.validar_largo(descripcion)' \
  '        pass' \
  "FAILED $T::test_guardar_uso_guarda_en_las_dos_memorias_o_da_400[nfc-que-crece]"
sabotaje $M "el historial mide el largo en NFC" \
  '        if len(texto) > tope:' \
  '        if len(unicodedata.normalize("NFC", texto)) > tope:' \
  "FAILED $T::test_importar_el_historial_mide_el_texto_como_lo_guarda"
CORRE=("$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_despacho1b.py -k test_confirmar_un_ncm_dice_si_no_guardo_el_historial)
sabotaje $M "confirmar un NCM no avisa si no era un producto" \
  '            wrote_client = historial_guardado = entry is not None' \
  '            wrote_client = historial_guardado = True' \
  "FAILED tests/test_despacho1b.py::test_confirmar_un_ncm_dice_si_no_guardo_el_historial[no es un producto]"
CORRE=("${PRUEBA[@]}")
sabotaje $M "el catálogo da 500 en vez de 400 al guardar" \
  $'    except ValueError as e:\n        raise HTTPException(status_code=400, detail=str(e))\n    except Exception as e:\n        logging.exception("catalog_save error")' \
  $'    except Exception as e:\n        logging.exception("catalog_save error")' \
  "FAILED $T::test_guardar_en_el_catalogo_respeta_el_tope[2001]"
sabotaje $M "el catálogo da 500 en vez de 400 al cambiar" \
  $'    except ValueError as e:\n        raise HTTPException(status_code=400, detail=str(e))\n    except Exception as e:\n        logging.exception("catalog_update_product error")' \
  $'    except Exception as e:\n        logging.exception("catalog_update_product error")' \
  "FAILED $T::test_cambiar_un_producto_respeta_el_tope_y_alcanza_claves_largas"
sabotaje $M "la clave de la URL vuelve a tener tope de 500" \
  '    if not product_key or len(product_key) > catalog_svc.MAX_DESCRIPCION:' \
  '    if not product_key or len(product_key) > 500:' \
  "FAILED $T::test_cambiar_un_producto_respeta_el_tope_y_alcanza_claves_largas"

if [ -n "$PG_URL" ]; then
  CORRE=("${PRUEBA_PG[@]}")
  git checkout -q -- proyecto_maria/
  if ! "${CORRE[@]}" >/dev/null 2>&1; then
    echo "BASE  | la prueba en Postgres ya está en rojo sin sabotaje"; FALLAS=$((FALLAS+1))
  else
    sabotaje $M "el arranque no pasa las columnas a text" \
      '                await conn.exec_driver_sql(f"ALTER TABLE vendor_catalog_products ALTER COLUMN {columna} TYPE TEXT")' \
      '                pass' \
      "FALLA | primer arranque: las columnas son text"
  fi
else
  echo "SALTO | sin PG_URL: la migración no se midió"
fi

git checkout -q -- proyecto_maria/
echo "fallas: $FALLAS"
[ "$FALLAS" -eq 0 ]
