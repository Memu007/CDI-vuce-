#!/usr/bin/env bash
# Negativos de CLIENTE-1c en la API, la importación y el script de datos: cada
# sabotaje deshace una línea de la pieza y tests/test_cliente1c.py o
# tests/test_cliente1b_script.py tiene que fallar por ese motivo. (Los de la
# pantalla están en cliente1.sh.)
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/cliente1c.sh [SHA]
# Trabaja en un worktree descartable con SQLite propia: no toca tu copia ni
# datos compartidos. Sale con error si un sabotaje no encuentra su patrón o no
# pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
TMPD="$(mktemp -d)"; WT="$TMPD/wt"
git -C "$REPO" worktree add --detach "$WT" "$SHA" >/dev/null || exit 2
trap 'git -C "$REPO" worktree remove --force "$WT" >/dev/null 2>&1; rm -rf "$TMPD"' EXIT
cd "$WT"
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
FALLAS=0

correr() { "$PY" -m pytest -q --no-cov -p no:cacheprovider tests/test_cliente1c.py tests/test_cliente1b_script.py 2>&1; }

# sabotaje <archivo> <nombre> <texto original> <texto saboteado> <lo que el rojo tiene que decir>
sabotaje() {
  local archivo="$1" nombre="$2" viejo="$3" nuevo="$4" esperado="$5"
  git checkout -q -- proyecto_maria/ scripts/datos/
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
    echo "ROJO? | $nombre: rojo (salida $codigo), pero sin «$esperado»"; grep FAILED <<<"$salida" | head -3; FALLAS=$((FALLAS+1))
  fi
}

M=proyecto_maria/main.py
G=proyecto_maria/services/migration_service.py
D=scripts/datos/clientes_fecha_inic_activ.py
F=proyecto_maria/services/fecha_inic_activ.py
C=FAILED\ tests/test_cliente1c.py::
B=FAILED\ tests/test_cliente1b_script.py::

rm -f test.db
if ! correr >/dev/null; then
  echo "BASE  | la prueba ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FAILED; exit 1
fi

# D15: la operación copia sólo una fecha que sirve, AAAA-MM-DD.
sabotaje $M "la operación copia lo que trae, como antes" \
  'fecha_op = _fecha_inic_activ_o_vacia(data.get("comprador_fecha_inic_activ"))' \
  'fecha_op = str(data.get("comprador_fecha_inic_activ") or "").strip()' \
  "${C}test_la_operacion_solo_copia_una_fecha_que_sirve[20150-01-0]"
sabotaje $M "la operación corta a diez caracteres, como antes" \
  'fecha_op = _fecha_inic_activ_o_vacia(data.get("comprador_fecha_inic_activ"))' \
  'fecha_op = _fecha_inic_activ_o_vacia(str(data.get("comprador_fecha_inic_activ") or "")[:10])' \
  "${C}test_la_operacion_solo_copia_una_fecha_que_sirve[2015-03-15T00:00:00]"
sabotaje $M "la regla de la operación deja pasar la que no sirve" \
  $'    except HTTPException:\n        return ""' $'    except HTTPException:\n        return str(raw or "")' \
  "${C}test_la_operacion_solo_copia_una_fecha_que_sirve[2015-02-30]"
sabotaje $M "la operación pisa la fecha que ya tiene" \
  'if fecha_op and not (client.fecha_inic_activ or "").strip():' 'if fecha_op:' \
  "${C}test_la_operacion_no_pisa_la_fecha_que_ya_tiene"

# D16: la importación deja vacía la que no sirve y avisa la fila.
sabotaje $G "la vista previa no junta las fechas que no sirven" \
  '_collect_rows(sheet, mapping, rows, omitted, invalid_dates)' '_collect_rows(sheet, mapping, rows, omitted)' \
  "${C}test_la_vista_previa_avisa_la_fila_con_la_fecha_que_no_sirve"
sabotaje $G "el resumen no cuenta las fechas que no sirven" \
  '"fechas_que_no_sirven": len(invalid_dates),' '"fechas_que_no_sirven": 0,' \
  "${C}test_la_vista_previa_avisa_la_fila_con_la_fecha_que_no_sirve"
sabotaje $G "el aviso da otra fila" \
  '{"sheet": sheet.name, "row": offset, "cuit": cuit, "value": raw_date}' \
  '{"sheet": sheet.name, "row": offset - 1, "cuit": cuit, "value": raw_date}' \
  "${C}test_la_vista_previa_avisa_la_fila_con_la_fecha_que_no_sirve"
sabotaje $G "el aviso no dice qué traía" \
  '"cuit": cuit, "value": raw_date}' '"cuit": cuit, "value": ""}' \
  "${C}test_la_vista_previa_avisa_la_fila_con_la_fecha_que_no_sirve"
sabotaje $G "avisa también la celda vacía" \
  '            if raw_date:' '            if True:' \
  "${C}test_sin_fechas_malas_no_hay_aviso"
sabotaje $F "el año vuelve a quedar sin rellenar" \
  'return date(anio, mes, dia).isoformat()' 'return f"{anio}-{mes:02d}-{dia:02d}" if date(anio, mes, dia) else None' \
  "${C}test_la_importacion_guarda_el_anio_con_cuatro_cifras"

# D25 (b): la importación sigue la regla del alta.
sabotaje $G "la importación guarda lo que trae, cortado" \
  'return fecha_del_alta(re.sub(r" 00:00:00\Z", "", text)) or ""' 'return text[:10]' \
  "${C}test_la_importacion_deja_vacia_la_fecha_que_el_alta_no_acepta[15-03-2015]"
sabotaje $G "la celda de fecha de Excel no se importa" \
  'return fecha_del_alta(re.sub(r" 00:00:00\Z", "", text)) or ""' 'return fecha_del_alta(text) or ""' \
  "${C}test_la_celda_de_fecha_de_excel_se_importa"
sabotaje $F "la regla acepta el año de dos cifras" \
  'r"([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})"' 'r"([0-9]{1,2})/([0-9]{1,2})/([0-9]{2,4})"' \
  "${C}test_la_importacion_deja_vacia_la_fecha_que_el_alta_no_acepta[15/03/15]"
sabotaje $F "la regla acepta dígitos de ancho completo" \
  'r"([0-9]{4})-([0-9]{2})-([0-9]{2})"' 'r"(\d{4})-(\d{2})-(\d{2})"' \
  "${C}test_la_importacion_deja_vacia_la_fecha_que_el_alta_no_acepta[\uff12\uff10\uff11\uff15-03-15]"
sabotaje $F "la regla no acepta D/M/AAAA" \
  'r"([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})"' 'r"([0-9]{2})/([0-9]{2})/([0-9]{4})"' \
  "${C}test_la_importacion_acepta_lo_que_acepta_el_alta[5/3/2015-2015-03-05]"
sabotaje $F "la regla acepta una fecha que no existe" \
  'return date(anio, mes, dia).isoformat()' 'return f"{anio:04d}-{mes:02d}-{dia:02d}"' \
  "${C}test_la_operacion_solo_copia_una_fecha_que_sirve[2015-02-30]"
sabotaje $M "la confirmación crea con lo que trae el lote" \
  'fecha_inic_activ=_fecha_inic_activ_o_vacia(str(record.get("fecha_inic_activ") or "")) or None,' \
  'fecha_inic_activ=str(record.get("fecha_inic_activ") or "").strip()[:10] or None,' \
  "${C}test_la_confirmacion_no_crea_con_una_fecha_que_no_sirve[20150-01-0]"
sabotaje $M "la confirmación rellena con lo que trae el lote" \
  '            incoming = _fecha_inic_activ_o_vacia(incoming)' '            pass' \
  "${C}test_la_confirmacion_no_rellena_con_una_fecha_que_no_sirve[2015-02-30]"

# La ficha dice si la guardada le sirve al TXT, con el criterio del generador.
sabotaje $M "la ficha no dice si la guardada sirve" \
  '"fecha_inic_activ_sirve": _fecha_inic_activ_sirve(c.fecha_inic_activ),' \
  '"fecha_inic_activ_sirve": bool(c.fecha_inic_activ),' \
  "${C}test_la_ficha_dice_si_la_fecha_guardada_sirve[2015-02-30]"
sabotaje $M "la ficha decide con la regla del alta, no con la del generador" \
  '        fecha_inicio_actividad(guardada)' '        _fecha_inic_activ_o_vacia(guardada) or int("no sirve")' \
  "${C}test_la_ficha_dice_si_la_fecha_guardada_sirve[\uff12\uff10\uff11\uff15-03-15]"
sabotaje $M "la ficha dice que sirve una vacía" \
  $'    if not str(guardada or "").strip():\n        return False\n' '' \
  "${C}test_la_ficha_dice_si_la_fecha_guardada_sirve[vacia]"

# El script de datos no muestra la clave.
sabotaje $D "un --base mal escrito sale con el error de Python" \
  'except (ArgumentError, ValueError):' 'except ZeroDivisionError:' \
  "${B}test_un_base_mal_escrito_no_muestra_la_clave[sin-dos-puntos]"
sabotaje $D "un puerto que no es número sale con el error de Python" \
  'except (ArgumentError, ValueError):' 'except ArgumentError:' \
  "${B}test_un_base_mal_escrito_no_muestra_la_clave[puerto-texto]"
sabotaje $D "una base que no responde sale con el traceback" \
  'except Exception as e:  # noqa: BLE001' 'except ZeroDivisionError as e:  # noqa: BLE001' \
  "${B}test_una_base_que_no_responde_no_muestra_la_clave"
sabotaje $D "el error del driver muestra la clave" \
  'detalle = _tapar(f"{type(e).__name__}: {e}", secretos, visibles)' 'detalle = f"{type(e).__name__}: {e}"' \
  "${B}test_si_el_error_de_la_base_nombra_la_clave_no_se_muestra[simple]"
sabotaje $D "se tapa sólo la clave tal cual, no la escapada" \
  $',\n                  "(?i:" + "".join(f"%{b:02x}" for b in c.encode()) + ")"}' '}' \
  "${B}test_si_el_error_de_la_base_nombra_la_clave_no_se_muestra[escapada]"
# EXCEL-3f, H1-bis: la clave escapada como la escriba SQLAlchemy o el driver.
sabotaje $D "se tapa la clave escapada entera, no carácter por carácter (H1-bis)" \
  'patrones = {f: _escrito_de_cualquier_forma(f) for f in formas}' \
  'patrones = {f: "(?:" + "|".join(map(re.escape, {f, __import__("urllib.parse").parse.quote(f, safe=""), __import__("urllib.parse").parse.quote_plus(f)})) + ")" for f in formas}' \
  "${B}test_la_clave_con_espacio_y_otro_escapado_no_se_ve_como_la_escriba_el_error[sqlalchemy-barra]"
sabotaje $D "el %XX en minúscula no se tapa" \
  '"(?i:" + "".join(f"%{b:02x}"' '"(?:" + "".join(f"%{b:02X}"' \
  "${B}test_la_clave_con_espacio_y_otro_escapado_no_se_ve_como_la_escriba_el_error[minusculas-barra]"
sabotaje $D "el «+» por el espacio no se tapa" \
  '            formas.add(r"\+")' '            pass' \
  "${B}test_la_clave_con_espacio_y_otro_escapado_no_se_ve_como_la_escriba_el_error[quote_plus-barra]"
sabotaje $D "la clave escrita con ascii() no se tapa" \
  're.escape(ascii(c)[1:-1]), ' '' \
  "${B}test_la_clave_con_espacio_y_otro_escapado_no_se_ve_como_la_escriba_el_error[ascii-enie]"
sabotaje $D "la clave escrita en JSON no se tapa" \
  ' re.escape(json.dumps(c)[1:-1]),' '' \
  "${B}test_la_clave_con_espacio_y_otro_escapado_no_se_ve_como_la_escriba_el_error[json-enie]"
sabotaje $D "la comilla escapada con «\\» no se tapa" \
  $'\n                  re.escape("\\\\" + c),' '' \
  "${B}test_la_clave_con_espacio_y_otro_escapado_no_se_ve_como_la_escriba_el_error[repr-las-dos-comillas]"
sabotaje $D "un pedazo del host que es la clave escapada queda a la vista" \
  $'visibles = {v for v in visibles\n                if v and not any(re.fullmatch(p, v) for p in patrones.values())}' \
  'visibles = {v for v in visibles if v}' \
  "${B}test_un_pedazo_del_host_que_es_la_clave_escrita_de_otra_forma_se_tapa[quote]"
sabotaje $D "se nombra la base con la URL escrita, como antes" \
  'donde = _tapar(_donde(url), secretos, visibles)' 'donde = args.base.split("://", 1)[-1]' \
  "${B}test_una_clave_con_un_separador_no_se_ve_en_el_error[CLA/VESECRETA]"
sabotaje $D "se tapa sólo la clave que ve SQLAlchemy" \
  'secretos = {antes, antes.partition(":")[2], *re.split(_SEPARADORES, antes),' 'secretos = {' \
  "${B}test_si_el_error_repite_una_base_mal_armada_no_se_ve_la_clave[arroba]"
sabotaje $D "lo de antes del «@» se tapa entero, no por partes" \
  '*re.split(_SEPARADORES, antes),' '' \
  "${B}test_si_el_error_repite_una_base_mal_armada_no_se_ve_la_clave[arroba]"
sabotaje $D "se parte sólo en «:», «;» y «@», como antes" \
  '_SEPARADORES = r"[:;@/?#]"' '_SEPARADORES = r"[:;@]"' \
  "${B}test_si_el_error_repite_la_url_una_clave_con_separador_no_se_ve[CLA@VE/SE@CRETA]"
sabotaje $D "la clave en la consulta no se tapa" \
  $'    for valor in url.query.values():\n        secretos |= set(valor) if isinstance(valor, tuple) else {valor}\n' '' \
  "${B}test_si_el_error_repite_una_base_mal_armada_no_se_ve_la_clave[en-la-consulta]"
sabotaje $D "lo que conecta es la URL escrita, no la que se leyó" \
  'r = asyncio.run(revisar(url, args.arreglar_none))' 'r = asyncio.run(revisar(args.base, args.arreglar_none))' \
  "${B}test_lo_que_conecta_es_lo_que_se_lee"
sabotaje $D "una clave corta tapa el host del error" \
  $'visibles = {v for v in visibles\n                if v and not any(re.fullmatch(p, v) for p in patrones.values())}' 'visibles = set()' \
  "${B}test_una_clave_corta_no_tapa_el_host_en_el_error"
sabotaje $D "el host protege lo que es parte de la clave" \
  'for f in sorted(formas | visibles, key=len, reverse=True):' 'for f in sorted(formas | visibles, key=len):' \
  "${B}test_una_clave_que_empieza_como_el_host_se_tapa_entera"
sabotaje $D "un usuario corto rompe la palabra (sin mirar antes)" \
  '            patron = r"(?<!\w)" + patron' '            pass' \
  "${B}test_un_usuario_corto_no_rompe_el_mensaje[o]"
sabotaje $D "un usuario corto rompe la palabra (sin mirar después)" \
  '            patron += r"(?!\w)"' '            pass' \
  "${B}test_un_usuario_corto_no_rompe_el_mensaje[Connection]"
sabotaje $D "si tapar falla sale el traceback" \
  'except Exception:  # noqa: BLE001 - tapar nunca muestra un traceback' 'except ZeroDivisionError:' \
  "${B}test_si_tapar_falla_no_hay_traceback_ni_clave"

git checkout -q -- proyecto_maria/ scripts/datos/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
