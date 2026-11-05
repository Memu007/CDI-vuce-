#!/usr/bin/env bash
# Negativos de DESPACHO-1b (la devolución y la D41): cada sabotaje deshace
# un arreglo y tests/test_despacho1b.py tiene que fallar por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/despacho1b.sh [SHA]
# Con PG_DSN=postgresql://… (un Postgres descartable) corre además los que
# sólo se ven en Postgres, con scripts/testing/despacho1b_postgres.py.
# Trabaja en un worktree descartable con su propia SQLite y sin terceros: no
# toca tu copia ni datos compartidos. Sale con error si un sabotaje no
# encuentra su patrón, no pone rojo donde tiene que ponerlo o no se corrió.
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
LECTOR=proyecto_maria/core/despacho_lector.py
T=tests/test_despacho1b.py

pytest_d1b() {
  rm -f test.db
  DATABASE_URL=sqlite+aiosqlite:///./test.db ENVIRONMENT=test \
    "$PY" -m pytest -q --no-cov --timeout=120 -p no:randomly -p no:cacheprovider "$T" 2>&1
}

aplicar() {
  "$PY" - "$1" "$2" "$3" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
viejo, nuevo = sys.argv[2], sys.argv[3]
if s.count(viejo) != 1:
    sys.exit(f"patrón no encontrado una sola vez ({s.count(viejo)}): {viejo!r}")
open(p, "w", encoding="utf-8").write(s.replace(viejo, nuevo))
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
      grep -E "^FAILED" <<<"$salida" | head -5; FALLAS=$((FALLAS+1)); return
    fi
  done
  echo "ROJO  | $nombre: $(printf '«%s» ' "$@")"
}

# no_debe <nombre> <salida> <lo que el rojo no tiene que decir>...
no_debe() {
  local nombre="$1" salida="$2"; shift 2
  for prohibido in "$@"; do
    if grep -qF -- "$prohibido" <<<"$salida"; then
      echo "ANCHO | $nombre: también «$prohibido»"; FALLAS=$((FALLAS+1))
    fi
  done
}

# sabotaje <nombre> <archivo> <texto original> <texto saboteado> <casos en rojo>...
sabotaje() {
  local nombre="$1" archivo="$2" viejo="$3" nuevo="$4" salida codigo; shift 4
  git checkout -q -- proyecto_maria/
  if ! aplicar "$archivo" "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  salida="$(pytest_d1b)"; codigo=$?
  juzgar "$nombre" "$salida" "$codigo" "${@/#/FAILED $T::}"
  ULTIMA="$salida"
  git checkout -q -- proyecto_maria/
}

# Sin sabotaje tiene que estar en verde: si no, cualquier «ROJO» de abajo
# sería del rojo que ya había.
if ! salida="$(pytest_d1b)"; then
  echo "BASE  | test_despacho1b.py ya está en rojo sin sabotaje: no se puede medir nada"
  grep -E "^FAILED|passed|failed" <<<"$salida"; exit 1
fi
echo "BASE  | verde sin sabotaje en $SHA"

# 1) La memoria: cada tope corta antes de gastar, medido en un proceso aparte.
sabotaje "el lector sin tope de memoria" "$LECTOR" \
  "_MAX_MEMORIA_HIJO = 256 * 1024 * 1024" \
  "_MAX_MEMORIA_HIJO = 1 << 40" \
  "test_un_pdf_que_llena_la_memoria_se_rechaza" \
  "test_leer_un_pdf_que_llena_la_memoria_avisa"
sabotaje "el lector no avisa que se quedó sin memoria" "$LECTOR" \
  "    except MemoryError:
        return _SALIDA_SIN_MEMORIA" \
  "    except ImportError:
        return _SALIDA_SIN_MEMORIA" \
  "test_un_pdf_que_llena_la_memoria_se_rechaza" \
  "test_leer_un_pdf_que_llena_la_memoria_avisa"
sabotaje "una hoja que se queda sin memoria se saltea" "$LECTOR" \
  "        except MemoryError:
            raise
        except LimitReachedError:" \
  "        except LimitReachedError:" \
  "test_un_pdf_que_llena_la_memoria_se_rechaza"
sabotaje "los flujos sin tope" "$LECTOR" \
  "_MAX_FLUJO = 8 * 1024 * 1024" \
  "_MAX_FLUJO = 1 << 40" \
  "test_hojas_que_se_inflan_se_saltean_sin_gastar_memoria"
sabotaje "sin el chequeo de la hoja pesada" "$LECTOR" \
  "contenido is not None and len(contenido.get_data()) > _MAX_CONTENIDO_PAGINA" \
  "False" \
  "test_una_hoja_pesada_se_saltea_y_las_demas_se_leen"
sabotaje "sin el tope de 200 hojas" "$LECTOR" \
  "if len(paginas) > _MAX_PAGINAS:" \
  "if False:" \
  "test_mas_de_200_hojas_lee_las_primeras_200"
sabotaje "sin el tope del texto" "$LECTOR" \
  "if largo > _MAX_TEXTO:" \
  "if False:" \
  "test_el_texto_de_todas_las_hojas_tiene_tope"

# 2) La lectura cuadrática: la prueba mide el tope, no un tiempo.
sabotaje "sin el tope de 40 rótulos" "$LECTOR" \
  "if len(encontrados) > _MAX_COLUMNAS:" \
  "if False:" \
  "test_una_linea_con_mas_de_40_rotulos_no_se_lee[41-True]"
no_debe "sin el tope de 40 rótulos" "$ULTIMA" "test_una_linea_con_mas_de_40_rotulos_no_se_lee[40-False]"
sabotaje "sin el tope del largo de línea" "$LECTOR" \
  "if any(len(l) > _MAX_LARGO_LINEA for l in lineas):" \
  "if False:" \
  "test_una_linea_de_mas_de_2000_caracteres_no_se_lee[2001-True]"
no_debe "sin el tope del largo de línea" "$ULTIMA" "test_una_linea_de_mas_de_2000_caracteres_no_se_lee[2000-False]"
sabotaje "sin el tope de 500 renglones" "$LECTOR" \
  "if hay_mas or len(renglones) > MAX_RENGLONES:" \
  "if False:" \
  "test_mas_de_500_items_lee_los_primeros_500[501-True]" \
  "test_mas_de_500_renglones_con_subitems_lee_los_primeros_500[0]"
no_debe "sin el tope de 500 renglones" "$ULTIMA" "test_mas_de_500_items_lee_los_primeros_500[500-False]"
sabotaje "el tope cuenta el ítem además de sus subítems" "$LECTOR" \
  'sum(len(it["subitems"]) or 1 for it in items)' \
  'sum(1 + len(it["subitems"]) for it in items)' \
  "test_300_items_con_un_subitem_son_300_renglones_sin_aviso"
sabotaje "la primera hoja larga dice hoja 0" "$LECTOR" \
  '"El texto de la primera hoja es demasiado largo: no leí ninguna." if n == 1' \
  '"El texto de la primera hoja es demasiado largo: no leí ninguna." if n == 0' \
  "test_si_la_primera_hoja_pasa_el_tope_del_texto_no_dice_hoja_0"
sabotaje "la elección sin los dos de margen" "$LECTOR" \
  "k = bisect_right(inicios, inicio + 2) - 1" \
  "k = bisect_right(inicios, inicio) - 1" \
  "test_muchos_rotulos_reparten_igual_que_pocos"

# 3) El proceso aparte: si tarda, 504 y se mata; si se queda sin memoria, aviso.
sabotaje "no se mata al lector que tarda" "$LECTOR" \
  "                    proceso.kill()
                    await proceso.wait()" \
  "                    pass" \
  "test_leer_que_tarda_demasiado_da_504_y_mata_al_lector"
sabotaje "la ruta no ataja el tiempo" proyecto_maria/main.py \
  "    except TimeoutError:
        return JSONResponse(
            status_code=504," \
  "    except LookupError:
        return JSONResponse(
            status_code=504," \
  "test_leer_que_tarda_demasiado_da_504_y_mata_al_lector"
sabotaje "los errores del lector se juntan enteros" "$LECTOR" \
  "                _, salida, errores = await asyncio.gather(
                    _escribir(proceso.stdin, data), proceso.stdout.read(),
                    _final(proceso.stderr, _FINAL_DE_ERRORES))
                await proceso.wait()" \
  "                salida, errores = await proceso.communicate(data)
                errores = errores[-_FINAL_DE_ERRORES:]" \
  "test_los_errores_del_lector_no_se_juntan_enteros_en_memoria"
sabotaje "la ruta no ataja el PDF pesado" proyecto_maria/main.py \
  "    except PdfDemasiadoPesado as e:" \
  "    except LookupError as e:" \
  "test_leer_un_pdf_que_llena_la_memoria_avisa"

# 4) Los números y el peso por unidad.
sabotaje "los números sin tope" "$LECTOR" \
  "if not (0 <= valor < _MAX_NUMERO):" \
  "if not (0 <= valor):" \
  "test_guardar_un_numero_del_tope_para_arriba_da_422[cantidad]" \
  "test_guardar_un_numero_del_tope_para_arriba_da_422[valor_unitario]" \
  "test_guardar_un_numero_del_tope_para_arriba_da_422[kilo_neto]"
sabotaje "sin el chequeo del peso" "$LECTOR" \
  "if peso is not None and not (math.isfinite(peso) and peso < _MAX_NUMERO):" \
  "if False:" \
  "test_un_peso_por_unidad_infinito_no_se_guarda[1.0-1e-320]" \
  "test_un_peso_por_unidad_infinito_no_se_guarda[900000000000.0-1e-300]" \
  "test_un_peso_por_unidad_infinito_no_se_guarda[100000000000.0-1e-05]"
sabotaje "el peso sin el tope" "$LECTOR" \
  "math.isfinite(peso) and peso < _MAX_NUMERO" \
  "math.isfinite(peso)" \
  "test_un_peso_por_unidad_infinito_no_se_guarda[100000000000.0-1e-05]"
no_debe "el peso sin el tope" "$ULTIMA" \
  "test_un_peso_por_unidad_infinito_no_se_guarda[1.0-1e-320]" \
  "test_un_peso_por_unidad_infinito_no_se_guarda[900000000000.0-1e-300]"
sabotaje "el tope del peso deja afuera el máximo" "$LECTOR" \
  "peso < _MAX_NUMERO" \
  "peso <= _MAX_NUMERO" \
  "test_un_peso_por_unidad_justo_en_el_tope_marca_el_renglon"

# 5) Guardar: todo o nada, sin NUL, sin promediar con el vacío y sin sumar a
# un producto de otro NCM.
sabotaje "un commit por renglón" proyecto_maria/main.py \
  "client_id=client_id, **campos)
        await db.commit()" \
  "client_id=client_id, **campos)
            await db.commit()" \
  "test_guardar_si_falla_la_base_no_guarda_ninguno"
sabotaje "guardar sin sacar el NUL" proyecto_maria/main.py \
  "renglones = _sin_nul(body.get(\"renglones\"))" \
  "renglones = body.get(\"renglones\")" \
  "test_guardar_saca_el_nul_de_los_textos"
sabotaje "promedia con el valor vacío" proyecto_maria/services/client_memory.py \
  "    if not n:
        return nuevo, 1
" \
  "    if not n:
        return nuevo / 2, 2
" \
  "test_guardar_otra_vez_con_peso_no_lo_promedia_con_el_vacio"
sabotaje "la clave sin el NCM" proyecto_maria/services/client_memory.py \
  'f"{ncm8}\x1f{misma}"' \
  'f"{misma}"' \
  "test_guardar_no_funde_productos_con_ncm_distinto" \
  "test_guardar_no_toca_un_producto_que_ya_estaba_con_otro_ncm" \
  "test_aprender_con_puntos_suma_al_producto_del_despacho_y_no_a_otro"
no_debe "la clave sin el NCM" "$ULTIMA" "test_guardar_con_el_mismo_ncm_sigue_sumando"

# Lo que encontró el adversario: dos lecturas que daban 500.
sabotaje "el lector sin el tope de los números" "$LECTOR" \
  "elif not valor < _MAX_NUMERO:" \
  "elif False:" \
  "test_un_numero_del_tope_para_arriba_queda_faltante_y_leer_no_da_500[cantidad infinita]" \
  "test_un_numero_del_tope_para_arriba_queda_faltante_y_leer_no_da_500[kilo en el tope]"
sabotaje "el lector sólo frena el infinito" "$LECTOR" \
  "elif not valor < _MAX_NUMERO:" \
  "elif not math.isfinite(valor):" \
  "test_un_numero_del_tope_para_arriba_queda_faltante_y_leer_no_da_500[unitario en el tope]"
no_debe "el lector sólo frena el infinito" "$ULTIMA" \
  "test_un_numero_del_tope_para_arriba_queda_faltante_y_leer_no_da_500[cantidad infinita]"
sabotaje "el tope del lector deja afuera el máximo" "$LECTOR" \
  "elif not valor < _MAX_NUMERO:" \
  "elif not valor <= _MAX_NUMERO:" \
  "test_un_numero_del_tope_para_arriba_queda_faltante_y_leer_no_da_500[cantidad en el tope]"
sabotaje "el medio par llega a la salida" "$LECTOR" \
  "texto = _MEDIO_PAR.sub(\"\\ufffd\", pagina.extract_text(extraction_mode=\"layout\") or \"\")" \
  "texto = pagina.extract_text(extraction_mode=\"layout\") or \"\"" \
  "test_un_caracter_suelto_que_no_es_unicode_avisa_y_leer_no_da_500"
sabotaje "el lector hereda todo el entorno" "$LECTOR" \
  "entorno = {k: os.environ[k] for k in (\"PATH\", \"HOME\", \"LANG\", \"LC_ALL\", \"PYTHONUSERBASE\")
               if k in os.environ}" \
  "entorno = dict(os.environ)" \
  "test_el_lector_no_hereda_los_secretos_del_proceso"
sabotaje "el lector lee el .env" "$LECTOR" \
  "    entorno[\"PYTHON_DOTENV_DISABLED\"] = \"1\"" \
  "    pass" \
  "test_el_lector_no_hereda_los_secretos_del_proceso"

# Devolución 20:07: trabajo y turnos.
sabotaje "sin el tope de CPU entre hojas" "$LECTOR" \
  "        if time.process_time() > hasta:" \
  "        if False:" \
  "test_fuera_del_hilo_principal_el_tope_se_mira_entre_hojas"
sabotaje "sin el temporizador de CPU" "$LECTOR" \
  "    if threading.current_thread() is not threading.main_thread() or not hasattr(signal, \"setitimer\"):" \
  "    if True:" \
  "test_una_sola_hoja_cara_se_corta_en_el_tope_de_cpu" \
  "test_el_lector_aparte_corta_una_sola_hoja_cara"
no_debe "sin el temporizador de CPU" "$ULTIMA" \
  "test_un_pdf_que_da_mucho_trabajo_deja_de_leerse_por_tiempo_de_cpu"
sabotaje "el corte de CPU es una Exception" "$LECTOR" \
  "class _DemasiadoTrabajo(BaseException):" \
  "class _DemasiadoTrabajo(Exception):" \
  "test_una_sola_hoja_cara_se_corta_en_el_tope_de_cpu" \
  "test_el_lector_aparte_corta_una_sola_hoja_cara"
sabotaje "la señal queda puesta" "$LECTOR" \
  "        signal.setitimer(signal.ITIMER_PROF, 0)
        signal.signal(signal.SIGPROF, anterior)" \
  "        pass" \
  "test_el_tope_de_cpu_deja_la_senal_como_estaba"
sabotaje "el hijo no recibe el tope de CPU" "$LECTOR" \
  "sys.executable, \"-m\", __name__, repr(float(limite_cpu_s))," \
  "sys.executable, \"-m\", __name__, repr(float(_MAX_CPU_LECTURA * 100))," \
  "test_el_lector_aparte_usa_el_tope_de_cpu_que_recibe" \
  "test_el_lector_aparte_tiene_tope_de_cpu_sin_pedirlo"
sabotaje "tres lectores a la vez" "$LECTOR" \
  "_HIJOS_A_LA_VEZ = 2" \
  "_HIJOS_A_LA_VEZ = 3" \
  "test_como_mucho_dos_lectores_a_la_vez"
sabotaje "un usuario lee varios a la vez" "$LECTOR" \
  "        if clave in leyendo:" \
  "        if False:" \
  "test_un_usuario_lee_un_despacho_a_la_vez_y_no_frena_a_otro"
sabotaje "la clave no se suelta al terminar" "$LECTOR" \
  "        leyendo.discard(clave)" \
  "        pass" \
  "test_un_usuario_lee_un_despacho_a_la_vez_y_no_frena_a_otro"
sabotaje "la ruta no pasa el usuario" proyecto_maria/main.py \
  "_pdf_read_timeout_s(), clave=user[\"username\"])" \
  "_pdf_read_timeout_s(), clave=None)" \
  "test_leer_con_otra_lectura_en_curso_da_429"
sabotaje "la ruta no ataja al lector ocupado" proyecto_maria/main.py \
  "    except LectorOcupado as e:" \
  "    except LookupError as e:" \
  "test_leer_con_otra_lectura_en_curso_da_429"

# Devolución 20:07: los mutantes vivos del adversario.
sabotaje "sin memoria al abrir es un PDF roto" "$LECTOR" \
  "        paginas = list(reader.pages)
    except MemoryError:
        raise
" \
  "        paginas = list(reader.pages)
" \
  "test_sin_memoria_al_abrir_el_pdf_no_se_disfraza_de_pdf_roto"
sabotaje "sin el tope de RunLength" "$LECTOR" \
  "        \"run_length_maximum_output_length\", " \
  "        " \
  "test_una_hoja_que_se_infla_con_run_length_se_saltea" \
  "test_los_topes_de_pypdf_cubren_todos_los_filtros"
sabotaje "sin el tope de trabajo de un flujo" "$LECTOR" \
  "\"jbig2_maximum_output_length\", \"stream_decoding_work_maximum_length\")}" \
  "\"jbig2_maximum_output_length\")}" \
  "test_los_topes_de_pypdf_cubren_todos_los_filtros"
sabotaje "el valor a la izquierda va al último rótulo" "$LECTOR" \
  "columnas[max(k, 0)][1]" \
  "columnas[k][1]" \
  "test_un_valor_a_la_izquierda_de_todos_los_rotulos_va_al_primero"
sabotaje "el tope de texto es otro" "$LECTOR" \
  "_MAX_TEXTO = 4 * 1024 * 1024" \
  "_MAX_TEXTO = 8 * 1024 * 1024" \
  "test_el_tope_de_texto_de_verdad_corta_en_la_hoja_10"
sabotaje "el tope de renglones deja afuera el 500" proyecto_maria/main.py \
  "if len(renglones) > MAX_RENGLONES:" \
  "if len(renglones) >= MAX_RENGLONES:" \
  "test_guardar_justo_el_tope_de_renglones_se_guarda"
sabotaje "un resultado que no es objeto pasa" "$LECTOR" \
  "    if not isinstance(resultado, dict):" \
  "    if False:" \
  "test_un_lector_que_no_devuelve_un_objeto_es_un_error"
sabotaje "el caño roto tapa el código de salida" "$LECTOR" \
  "    except (BrokenPipeError, ConnectionResetError):" \
  "    except LookupError:" \
  "test_un_lector_que_sale_sin_leer_todo_dice_con_que_salio"

# Devolución 20:07: identidad del producto.
sabotaje "el lector no acepta el NCM de 10 dígitos" "$LECTOR" \
  "    ncm = ncm_para_historial(posicion)" \
  "    ncm = posicion[:10] if _POSICION.match(posicion) else None" \
  "test_el_mismo_producto_por_dos_vias_queda_en_una_fila[guardar-guardar]" \
  "test_el_mismo_producto_por_dos_vias_queda_en_una_fila[aprender-guardar]"
sabotaje "el lector vuelve a la regla vieja del NCM" "$LECTOR" \
  "    ncm = ncm_para_historial(posicion)" \
  "    ncm = re.sub(r\"\\D\", \"\", posicion)[:8] if _POSICION.match(posicion) else None" \
  "test_guardar_un_despacho_con_otros_digitos_marca_el_renglon[arabigo]" \
  "test_guardar_un_despacho_con_otros_digitos_marca_el_renglon[ancho completo]"
sabotaje "la clave compara la descripción cortada" proyecto_maria/services/client_memory.py \
  '    misma = unicodedata.normalize("NFC", descripcion.casefold())' \
  '    misma = unicodedata.normalize("NFC", descripcion.casefold())[:200]' \
  "test_dos_textos_largos_con_el_mismo_comienzo_no_se_funden" \
  "test_dos_descripciones_que_comparten_275_caracteres_son_dos_productos[aprender]"

# Devolución 20:07: los promedios y los topes.
sabotaje "el promedio cuenta los usos sin valor" proyecto_maria/services/client_memory.py \
  "    if veces is None:  # fila de antes de contar por valor" \
  "    if True:" \
  "test_el_promedio_no_cuenta_los_usos_sin_valor" \
  "test_el_historial_de_operaciones_tampoco_cuenta_los_usos_sin_valor"
sabotaje "el historial de operaciones cuenta los usos sin valor" proyecto_maria/services/client_service.py \
  "existing.veces_valor, usado, item.get('valor_unitario'))" \
  "None, usado, item.get('valor_unitario'))" \
  "test_el_historial_de_operaciones_tampoco_cuenta_los_usos_sin_valor"
sabotaje "el promedio acepta infinitos" proyecto_maria/services/client_memory.py \
  "    if not math.isfinite(valor) or valor <= 0 or valor >= _MAX_VALOR:" \
  "    if valor <= 0:" \
  "test_un_infinito_guardado_antes_no_rompe_el_catalogo_y_se_arregla" \
  "test_cambiar_el_peso_a_algo_que_no_es_un_peso_da_400[1e400]" \
  "test_un_producto_nuevo_no_guarda_valores_fuera_del_tope"
sabotaje "el promedio acepta números con otros dígitos" proyecto_maria/services/client_memory.py \
  "        if not _DECIMAL.fullmatch(valor):" \
  "        if False:" \
  "test_aprender_ignora_los_numeros_con_otros_digitos[learn]" \
  "test_aprender_ignora_los_numeros_con_otros_digitos[operacion]" \
  "test_cambiar_un_producto_valida_igual_que_guardar[guion bajo]" \
  "test_cambiar_un_producto_valida_igual_que_guardar[peso arabigo]"
sabotaje "el catálogo manda el infinito guardado" proyecto_maria/main.py \
  "    return valor if valor is None or math.isfinite(valor) else None" \
  "    return valor" \
  "test_un_infinito_guardado_antes_no_rompe_el_catalogo_y_se_arregla"
sabotaje "el PUT guarda cualquier peso" proyecto_maria/main.py \
  "            if peso is None:
                raise HTTPException(status_code=400, detail=\"El peso tiene que ser un número positivo.\")" \
  "            if peso is None:
                peso = 0.0" \
  "test_cambiar_el_peso_a_algo_que_no_es_un_peso_da_400[inf]" \
  "test_cambiar_el_peso_a_algo_que_no_es_un_peso_da_400[dos]"
no_debe "el PUT guarda cualquier peso" "$ULTIMA" "test_cambiar_el_peso_a_cero_lo_borra"
sabotaje "la búsqueda manda el infinito guardado" proyecto_maria/services/client_memory.py \
  "        \"valor_unitario_avg\": _finito(best_row.valor_unitario_avg)," \
  "        \"valor_unitario_avg\": best_row.valor_unitario_avg," \
  "test_un_infinito_guardado_antes_no_rompe_la_busqueda"
sabotaje "el peso cargado hereda los usos" proyecto_maria/main.py \
  "row.peso_unitario_avg, row.veces_peso = peso, 1" \
  "row.peso_unitario_avg, row.veces_peso = peso, max(row.veces_peso or 0, 1)" \
  "test_el_peso_que_carga_la_persona_cuenta_como_un_uso"
sabotaje "false es un peso cero" proyecto_maria/main.py \
  "if peso is None or (not isinstance(peso, bool) and peso in (\"\", 0, \"0\")):" \
  "if peso is None or peso in (\"\", 0, \"0\"):" \
  "test_cambiar_el_peso_a_algo_que_no_es_un_peso_da_400[false]"
no_debe "false es un peso cero" "$ULTIMA" "test_cambiar_el_peso_a_cero_lo_borra"
sabotaje "«0» en texto no borra el peso" proyecto_maria/main.py \
  "peso in (\"\", 0, \"0\")):" \
  "peso in (\"\", 0)):" \
  "test_cambiar_el_peso_a_cero_lo_borra[cero en texto]"
no_debe "«0» en texto no borra el peso" "$ULTIMA" "test_cambiar_el_peso_a_cero_lo_borra[cero]"
sabotaje "el PUT no ataja el entero enorme" proyecto_maria/services/client_memory.py \
  "    except (TypeError, ValueError, OverflowError):  # 10**400 no entra en un float" \
  "    except (TypeError, ValueError):" \
  "test_cambiar_el_peso_a_algo_que_no_es_un_peso_da_400[entero enorme]"
sabotaje "aprender no ataja el entero enorme" proyecto_maria/main.py \
  "        except (TypeError, ValueError, OverflowError):  # 10**400 no entra en un float" \
  "        except (TypeError, ValueError):" \
  "test_aprender_un_entero_enorme_no_da_500[peso_unitario]" \
  "test_aprender_un_entero_enorme_no_da_500[valor_unitario]" \
  "test_aprender_un_entero_enorme_no_da_500[cantidad]"
sabotaje "guardar no mira la mitad de par" "$LECTOR" \
  "    if _MEDIO_PAR.search(descripcion):
        problemas.append" \
  "    if False:
        problemas.append" \
  "test_guardar_una_mitad_de_par_suelta_da_422"
sabotaje "el origen con mitad de par se repite" "$LECTOR" \
  "    if _MEDIO_PAR.search(escrito):" \
  "    if False:" \
  "test_guardar_un_origen_con_mitad_de_par_da_422[solo]" \
  "test_guardar_un_origen_con_mitad_de_par_da_422[con una letra]"

# D47: el valor unitario sólo en dólares.
sabotaje "guarda el valor de cualquier divisa" proyecto_maria/main.py \
  "        if not en_dolares and campos[\"valor_unitario\"] is not None:" \
  "        if False:" \
  "test_guardar_un_despacho_que_no_esta_en_dolares_no_guarda_el_valor[en euros]" \
  "test_guardar_un_despacho_que_no_esta_en_dolares_no_guarda_el_valor[sin divisa]"
no_debe "guarda el valor de cualquier divisa" "$ULTIMA" "test_guardar_un_despacho_en_dolares_guarda_el_valor[USD]"
sabotaje "DOL no es dólar" proyecto_maria/main.py \
  "in (\"USD\", \"DOL\")" \
  "in (\"USD\",)" \
  "test_guardar_un_despacho_en_dolares_guarda_el_valor[DOL]"
no_debe "DOL no es dólar" "$ULTIMA" "test_guardar_un_despacho_en_dolares_guarda_el_valor[USD]"
sabotaje "la divisa no recorta los espacios" proyecto_maria/main.py \
  'body["divisa"].strip().upper() in' \
  'body["divisa"].upper() in' \
  "test_guardar_un_despacho_en_dolares_guarda_el_valor[ usd ]"
no_debe "la divisa no recorta los espacios" "$ULTIMA" "test_guardar_un_despacho_en_dolares_guarda_el_valor[dol]"
sabotaje "la divisa distingue minúsculas" proyecto_maria/main.py \
  'body["divisa"].strip().upper() in' \
  'body["divisa"].strip() in' \
  "test_guardar_un_despacho_en_dolares_guarda_el_valor[dol]"
no_debe "la divisa distingue minúsculas" "$ULTIMA" "test_guardar_un_despacho_en_dolares_guarda_el_valor[USD]"

# Vuelta 4: una regla de identidad en las cinco vías.
C=proyecto_maria/services/client_memory.py
M=proyecto_maria/main.py
F=test_cada_forma_del_mismo_producto_suma_a_la_misma_fila
sabotaje "la clave distingue mayúsculas" "$C" \
  'unicodedata.normalize("NFC", descripcion.casefold())' \
  'unicodedata.normalize("NFC", descripcion)' \
  "$F[minusculas]"
sabotaje "la clave sin NFC" "$C" \
  '    misma = unicodedata.normalize("NFC", descripcion.casefold())' \
  '    misma = descripcion.casefold()' \
  "test_las_minusculas_de_dos_formas_de_lo_mismo_son_el_mismo_producto"
no_debe "la clave sin NFC" "$ULTIMA" "test_la_n_compuesta_y_la_descompuesta_son_el_mismo_producto"
sabotaje "la descripción sin NFC" "$C" \
  '    texto = unicodedata.normalize("NFC", texto)' \
  '    pass' \
  "test_la_n_compuesta_y_la_descompuesta_son_el_mismo_producto"
sabotaje "la descripción no junta los espacios" "$C" \
  're.sub(r"\s+", " ", str(descripcion or "")' \
  're.sub(r" ", " ", str(descripcion or "")' \
  "$F[espacios]"
sabotaje "el NCM no acepta guiones" "$C" \
  '_NCM = re.compile(r"[0-9]+(?:[.\- ][0-9]+)*[A-Z]?")' \
  '_NCM = re.compile(r"[0-9]+(?:[. ][0-9]+)*[A-Z]?")' \
  "$F[guiones]"
sabotaje "el NCM no acepta puntos" "$C" \
  '_NCM = re.compile(r"[0-9]+(?:[.\- ][0-9]+)*[A-Z]?")' \
  '_NCM = re.compile(r"[0-9]+(?:[\- ][0-9]+)*[A-Z]?")' \
  "$F[puntos]"
sabotaje "el NCM no acepta espacios" "$C" \
  '_NCM = re.compile(r"[0-9]+(?:[.\- ][0-9]+)*[A-Z]?")' \
  '_NCM = re.compile(r"[0-9]+(?:[.\-][0-9]+)*[A-Z]?")' \
  "$F[espacios en el ncm]"
sabotaje "el NCM sin recortar las puntas" "$C" \
  '    ncm = str(ncm).strip().upper()' \
  '    ncm = str(ncm).upper()' \
  "test_cambiar_un_producto_guarda_la_forma_de_la_regla"
sabotaje "el NCM sólo de 8 dígitos" "$C" \
  '    if not 8 <= len(digitos) <= 11 or (ncm[-1].isalpha() and len(digitos) != 11):' \
  '    if len(digitos) != 8:' \
  "$F[10 digitos]" "$F[sim]" \
  "test_aprender_con_10_digitos_y_guardar_el_despacho_da_una_fila"
sabotaje "la letra SIM en minúscula no es la misma" "$C" \
  '    ncm = str(ncm).strip().upper()' \
  '    ncm = str(ncm).strip()' \
  "$F[sim en minuscula]"

# Vuelta 4: la base sostiene la identidad.
sabotaje "sin el índice único" proyecto_maria/database/models.py \
  '"owner_username", "client_id", "clave", unique=True),' \
  '"owner_username", "client_id", "clave", unique=False),' \
  "test_seis_guardados_a_la_vez_dejan_una_fila"
sabotaje "la fila recién creada suma otra vez" "$C" \
  '    if insertada:
        return existing' \
  '    pass' \
  "test_seis_guardados_a_la_vez_dejan_una_fila"
sabotaje "un producto nuevo guarda el peso sin tope" "$C" \
  '            peso_unitario_avg=valor_para_promedio(peso_unitario) or 0.0,' \
  '            peso_unitario_avg=peso_unitario or 0.0,' \
  "test_un_producto_nuevo_no_guarda_valores_fuera_del_tope"
sabotaje "la migración no une" "$M" \
  '            if len(grupo) < 2:' \
  '            if True:' \
  "test_la_migracion_une_los_duplicados_y_es_idempotente"
sabotaje "la migración cuenta filas, no usos" "$M" \
  '"veces_usado": sum(max(f["veces_usado"] or 1, 1) for f in grupo)}' \
  '"veces_usado": len(grupo)}' \
  "test_la_migracion_une_los_duplicados_y_es_idempotente"
sabotaje "la migración deja la fila más vieja" "$M" \
  '            queda = max(grupo, key=lambda f: (' \
  '            queda = min(grupo, key=lambda f: (' \
  "test_la_migracion_une_los_duplicados_y_es_idempotente"
sabotaje "la migración promedia sin pesar los usos" "$M" \
  'cambios[promedio] = sum(v * n for v, n in usos if n) / total if total else None' \
  'cambios[promedio] = sum(v for v, n in usos if n) / sum(1 for _, n in usos if n) if total else None' \
  "test_la_migracion_une_los_duplicados_y_es_idempotente"
D=test_aprender_ignora_los_numeros_con_otros_digitos
sabotaje "learn convierte los números con float()" "$M" \
  '            valor_unitario=valor,
            cantidad=cantidad,
            peso_unitario=peso,' \
  '            valor_unitario=float(valor or 0) or None,
            cantidad=float(cantidad or 0) or None,
            peso_unitario=float(peso or 0) or None,' \
  "$D[learn]"
no_debe "learn convierte los números con float()" "$ULTIMA" "$D[operacion]"
sabotaje "la operación convierte los números con float()" "$M" \
  '                valor_unitario=item.get("valor_unitario"),' \
  '                valor_unitario=float(item.get("valor_unitario") or 0) or None,' \
  "$D[operacion]"
no_debe "la operación convierte los números con float()" "$ULTIMA" "$D[learn]"
sabotaje "learn aprende el producto con un valor que no es un número" "$M" \
  '                float(numero or 0)' \
  '                pass' \
  "test_aprender_un_entero_enorme_no_da_500[peso_unitario]" \
  "test_aprender_un_entero_enorme_no_da_500[valor_unitario]" \
  "test_aprender_un_entero_enorme_no_da_500[cantidad]"
sabotaje "la migración escribe la clave antes de unir" "$M" \
  '                cambian[fila["id"]] = clave' \
  '                await conn.execute(text(
                    "UPDATE client_product_history SET clave = :clave WHERE id = :id"),
                    {"clave": clave, "id": fila["id"]})' \
  "test_la_migracion_une_la_fila_sin_clave_que_dejo_la_version_anterior" \
  "test_la_migracion_reescribe_claves_cruzadas"
sabotaje "la migración no vacía las claves que cambian" "$M" \
  '        for id_ in cambian:' \
  '        for id_ in ():' \
  "test_la_migracion_reescribe_claves_cruzadas"
sabotaje "la migración que falla se calla" "$M" \
  'async def _migrate_product_history_clave():' \
  'async def _migrate_product_history_clave():
    try:
        await _sin_atajar()
    except Exception as e:
        print(repr(e))


async def _sin_atajar():' \
  "test_la_migracion_que_falla_no_sigue_callada"

# Vuelta 4: los NCM con otros dígitos y lo que no es un producto, por vía.
O=test_un_ncm_con_otros_digitos_da_400_por_cada_via
sabotaje "aprender no mira los dígitos" "$M" \
  '_AVISO_MEDIO_PAR)
    if any(tiene_digito_no_ascii(' \
  '_AVISO_MEDIO_PAR)
    if False and any(tiene_digito_no_ascii(' \
  "$O[aprender-arabigo]" "$O[aprender-ancho completo]" "$O[aprender-mezclado]"
no_debe "aprender no mira los dígitos" "$ULTIMA" "$O[operacion-arabigo]"
sabotaje "/operaciones no mira los dígitos" "$M" \
  '        if any(tiene_digito_no_ascii(' \
  '        if False and any(tiene_digito_no_ascii(' \
  "$O[operacion-arabigo]" "$O[operacion-ancho completo]" "$O[operacion-mezclado]"
sabotaje "el cambio no mira los dígitos" "$M" \
  '        if tiene_digito_no_ascii(str(body["ncm"])):' \
  '        if False:' \
  "$O[cambio-arabigo]" "$O[cambio-ancho completo]" "$O[cambio-mezclado]"
sabotaje "guardar-uso no mira los dígitos" "$M" \
  '    if tiene_digito_no_ascii(ncm):' \
  '    if False:' \
  "$O[guardar-uso-arabigo]" "$O[guardar-uso-ancho completo]" "$O[guardar-uso-mezclado]"
sabotaje "los dígitos de ancho completo pasan" "$C" \
  '    return any(c.isdigit() and not "0" <= c <= "9" for c in texto)' \
  '    return any(c.isdigit() and not "0" <= c <= "9" and not "０" <= c <= "９" for c in texto)' \
  "$O[aprender-ancho completo]" "$O[guardar-uso-ancho completo]"
no_debe "los dígitos de ancho completo pasan" "$ULTIMA" "$O[aprender-arabigo]"
sabotaje "aprender acepta lo que no es objeto" "$M" \
  '    if not all(isinstance(item, dict) for item in items):' \
  '    if False:' \
  "test_aprender_un_item_que_no_es_un_objeto_da_400[texto]" \
  "test_aprender_un_item_que_no_es_un_objeto_da_400[lista]"
sabotaje "aprender no mira el medio par" "$M" \
  'tiene_medio_par, upsert_client_product_history,
    )
    if tiene_medio_par(body):' \
  'tiene_medio_par, upsert_client_product_history,
    )
    if False:' \
  "test_aprender_con_medio_par_da_400[origen]" "test_aprender_con_medio_par_da_400[clave]"
sabotaje "/operaciones no mira el medio par" "$M" \
  '        if tiene_medio_par(data):' \
  '        if False:' \
  "test_una_operacion_con_medio_par_da_400_y_no_queda[unidad]"
sabotaje "el cambio no mira el medio par" "$M" \
  'tiene_digito_no_ascii, tiene_medio_par, valor_para_promedio,
    )
    if tiene_medio_par(body):' \
  'tiene_digito_no_ascii, tiene_medio_par, valor_para_promedio,
    )
    if False:' \
  "test_cambiar_con_medio_par_da_400[origen]"
sabotaje "aprender acepta 501" "$M" \
  '    if len(items) > 500:' \
  '    if len(items) > 501:' \
  "test_aprender_tiene_tope_de_500_productos[501-400]"
no_debe "aprender acepta 501" "$ULTIMA" "test_aprender_tiene_tope_de_500_productos[500-200]"

# Vuelta 4: el cambio valida igual que guardar.
V=test_cambiar_un_producto_valida_igual_que_guardar
sabotaje "el cambio guarda la descripción como viene" "$M" \
  '            row.descripcion = descripcion_del_producto(body["descripcion"])' \
  '            row.descripcion = str(body["descripcion"]).strip()' \
  "$V[vacia]" "$V[larga]" "test_cambiar_un_producto_guarda_la_forma_de_la_regla"
sabotaje "el cambio no recalcula la clave" "$M" \
  '    row.clave = producto[2] if producto else None' \
  '    pass' \
  "test_el_mismo_producto_por_dos_vias_queda_en_una_fila[cambio-guardar]"
sabotaje "el choque del cambio da 500" "$M" \
  '    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409' \
  '    except LookupError:
        await db.rollback()
        raise HTTPException(status_code=409' \
  "test_el_mismo_producto_por_dos_vias_queda_en_una_fila[guardar-cambio]"
no_debe "el choque del cambio da 500" "$ULTIMA" "test_cambiar_un_producto_a_si_mismo_no_es_un_choque"

# Vuelta 4: el tope de CPU cubre el hijo entero.
sabotaje "entender el texto sin tope de CPU" "$LECTOR" \
  '        with _tope_de_cpu(limite_cpu_s - (time.process_time() - inicio)):' \
  '        with _tope_de_cpu(1e9):' \
  "test_el_tope_de_cpu_cubre_entender_el_texto"
sabotaje "entender el texto no descuenta lo gastado" "$LECTOR" \
  '        with _tope_de_cpu(limite_cpu_s - (time.process_time() - inicio)):' \
  '        with _tope_de_cpu(limite_cpu_s):' \
  "test_el_tope_de_cpu_cubre_entender_el_texto"
sabotaje "el temporizador de CPU no se repite" "$LECTOR" \
  '    signal.setitimer(signal.ITIMER_PROF, max(segundos, 0.001), 0.05)' \
  '    signal.setitimer(signal.ITIMER_PROF, max(segundos, 0.001))' \
  "test_un_corte_por_cpu_que_se_traga_un_finalizador_vuelve_a_cortar"
sabotaje "un corte por CPU parece escaneado" "$LECTOR" \
  '        avisos.append(f"El PDF da demasiado trabajo: leí hasta la hoja {len(textos)}.")
        salteadas = True' \
  '        avisos.append(f"El PDF da demasiado trabajo: leí hasta la hoja {len(textos)}.")' \
  "test_un_corte_por_cpu_en_la_primera_hoja_no_dice_que_es_escaneado"
sabotaje "extraer se lleva el tope entero" "$LECTOR" \
  "_hojas_del_pdf(data, limite_cpu_s * _PARTE_PARA_EXTRAER)" \
  "_hojas_del_pdf(data, limite_cpu_s)" \
  "test_las_hojas_leidas_antes_del_corte_dan_sus_productos"
no_debe "extraer se lleva el tope entero" "$ULTIMA" "test_el_tope_de_cpu_cubre_entender_el_texto"

# Vuelta 4, autorrevisión: el largo se mide como se guarda y la respuesta de
# la operación dice si quedó algo sin guardar.
sabotaje "el largo se mide antes de NFC" "$LECTOR" \
  'elif len(unicodedata.normalize("NFC", descripcion)) > _MAX_DESCRIPCION:' \
  'elif len(descripcion) > _MAX_DESCRIPCION:' \
  "test_guardar_una_descripcion_que_crece_al_normalizar_da_422"
sabotaje "la operación no avisa lo que no guardó" proyecto_maria/main.py \
  "            if not await _historial_de_un_producto(db, upsert_client_product_history, **campos):" \
  "            if await _historial_de_un_producto(db, upsert_client_product_history, **campos) is None:" \
  "test_una_operacion_con_un_producto_que_no_se_guarda_lo_dice"

# Vuelta 4, adversario sobre 7e96b32: la operación, confirmar un NCM y el
# cambio de origen validan como guardar.
OBJ=test_una_operacion_con_productos_que_no_son_objetos_da_400
sabotaje "operación sin revisar objetos" proyecto_maria/main.py \
  '        if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
            raise HTTPException(status_code=400, detail=_AVISO_NO_ES_OBJETO)
' \
  '' \
  "$OBJ[numero]" "$OBJ[texto]" "$OBJ[nulo]" "$OBJ[lista]" \
  "$OBJ[items texto]" "$OBJ[items objeto]" \
  "$OBJ[items objeto vacio]" "$OBJ[items cero]" "$OBJ[items texto vacio]"
no_debe "operación sin revisar objetos" "$ULTIMA" "test_aprender_un_item_que_no_es_un_objeto_da_400"
sabotaje "operación revisa sólo la lista" proyecto_maria/main.py \
  'not isinstance(items, list) or not all(isinstance(item, dict) for item in items)' \
  'not isinstance(items, list)' \
  "$OBJ[numero]" "$OBJ[texto]" "$OBJ[nulo]" "$OBJ[lista]"
no_debe "operación revisa sólo la lista" "$ULTIMA" "$OBJ[items texto]" "$OBJ[cuerpo lista]"
sabotaje "operación con un cuerpo que no es objeto" proyecto_maria/main.py \
  '        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail=_AVISO_NO_ES_OBJETO)
        # Faltar' \
  '        # Faltar' \
  "$OBJ[cuerpo lista]"
sabotaje "operación con ítems vacíos de otro tipo" proyecto_maria/main.py \
  '        items = data.get("items")
        items = [] if items is None else items
' \
  '        items = data.get("items") or []
' \
  "$OBJ[items objeto vacio]" "$OBJ[items cero]" "$OBJ[items texto vacio]"
no_debe "operación con ítems vacíos de otro tipo" "$ULTIMA" "$OBJ[numero]"
VACIA=test_una_operacion_sin_productos_ni_resumen_se_guarda_vacia
sabotaje "operación sin ítems no es vacía" proyecto_maria/main.py \
  '        items = [] if items is None else items
' \
  '' \
  "$VACIA[sin nada]" "$VACIA[nulos]"
sabotaje "operación sin resumen no es vacía" proyecto_maria/main.py \
  '        resumen = {} if resumen is None else resumen
' \
  '' \
  "$VACIA[sin nada]" "$VACIA[nulos]"
sabotaje "operación vacía cuenta un producto" proyecto_maria/main.py \
  'total_items=int(resumen.get("items", len(items))),' \
  'total_items=int(resumen.get("items", len(items) + 1)),' \
  "$VACIA[sin nada]" "$VACIA[nulos]"
sabotaje "operación vacía con valor" proyecto_maria/main.py \
  'total_value=float(resumen.get("valor_total", 0) or 0),' \
  'total_value=float(resumen.get("valor_total", 0) or 1),' \
  "$VACIA[sin nada]" "$VACIA[nulos]"
RES=test_una_operacion_con_un_resumen_que_no_es_un_objeto_da_400
sabotaje "operación sin revisar el resumen" proyecto_maria/main.py \
  '        if not isinstance(resumen, dict):
            raise HTTPException(status_code=400, detail="El resumen tiene que ser un objeto.")
' \
  '' \
  "$RES[lista]" "$RES[texto]" "$RES[numero]"
sabotaje "confirmar sin medio par" proyecto_maria/main.py \
  '    # Lo que la base no puede guardar se rechaza antes de sumar el uso.
    if tiene_medio_par(data):' \
  '    if False:' \
  "test_confirmar_un_ncm_con_medio_par_da_400_y_no_guarda_nada"
sabotaje "confirmar deja el NUL del origen" proyecto_maria/main.py \
  'origin = _sin_nul(str(data.get("origen") or "")).strip()' \
  'origin = str(data.get("origen") or "").strip()' \
  "test_confirmar_un_ncm_saca_el_nul_del_origen_y_del_proveedor"
sabotaje "confirmar deja el NUL del proveedor" proyecto_maria/main.py \
  'vendor_name = _sin_nul(str(data.get("vendor_name") or "")).strip()' \
  'vendor_name = str(data.get("vendor_name") or "").strip()' \
  "test_confirmar_un_ncm_saca_el_nul_del_origen_y_del_proveedor"
NONCM=test_confirmar_algo_que_no_es_un_ncm_da_400_y_no_guarda_nada
sabotaje "confirmar con la clave de sugerir" proyecto_maria/main.py \
  '    ncm_base = ncm_para_historial(ncm)
' \
  '    ncm_base = _ncm_suggestion_key(ncm)
' \
  "$NONCM[texto con 8 digitos]" "$NONCM[letra sin sim]" "$NONCM[corto]"
ORI=test_cambiar_el_origen_valida_igual_que_guardar
MAY=test_cambiar_el_origen_guarda_el_codigo_en_mayusculas
sabotaje "el PUT no valida el origen" proyecto_maria/main.py \
  '        origen, problema = origen_para_catalogo(body["origen"])
        if problema:
            raise HTTPException(status_code=400, detail=problema)
        row.origen_frecuente = origen or "XX"
' \
  '        row.origen_frecuente = str(body["origen"]).strip()[:3] or "XX"
' \
  "$ORI[lista]" "$ORI[tres letras]" "$ORI[numeros]" "$ORI[pais que no existe]" "$ORI[nombre]" \
  "$MAY[minusculas]" "$MAY[nulo]"
sabotaje "el PUT no saca el NUL" proyecto_maria/main.py \
  'body = _sin_nul(body) if isinstance(body, dict) else {}' \
  'body = body if isinstance(body, dict) else {}' \
  "$MAY[nul]"
no_debe "el PUT no saca el NUL" "$ULTIMA" "$MAY[minusculas]"
sabotaje "el PUT guarda el origen vacío" proyecto_maria/main.py \
  'row.origen_frecuente = origen or "XX"' \
  'row.origen_frecuente = origen' \
  "$MAY[vacio]" "$MAY[nulo]"
no_debe "el PUT guarda el origen vacío" "$ULTIMA" "$MAY[minusculas]"
# Code-review sobre 0c3a059: el origen es texto y ASCII en guardar y en el PUT.
TODO_O_NADA=test_guardar_es_todo_o_nada
sabotaje "el origen sin isascii" "$LECTOR" \
  'escrito.isascii() and ' \
  '' \
  "$TODO_O_NADA[ancho completo]" "$TODO_O_NADA[acento]" "$TODO_O_NADA[i sin punto]" \
  "$ORI[ancho completo]" "$ORI[acento]" "$ORI[i sin punto]"
sabotaje "el origen se mira en mayúsculas" "$LECTOR" \
  '    escrito = (valor or "").strip()
' \
  '    escrito = (valor or "").strip().upper()
' \
  "$TODO_O_NADA[i sin punto]" "$TODO_O_NADA[ligadura]" "$ORI[nombre]" "$ORI[i sin punto]" "$ORI[ligadura]" \
  "$ORI[ese aguda]"
sabotaje "el origen que no es texto" "$LECTOR" \
  '    if not isinstance(valor, (str, type(None))):
        return None, "El origen tiene que ser el código de dos letras."
' \
  '' \
  "$TODO_O_NADA[origen numero]" "$ORI[lista]" "$ORI[numero]"

sabotaje "confirmar un NCM no avisa que la base falló" proyecto_maria/main.py \
  '        logging.warning("ncm confirmation memory unavailable: %s", err)
        historial_guardado = False
' \
  '        logging.warning("ncm confirmation memory unavailable: %s", err)
' \
  "test_confirmar_un_ncm_dice_si_no_guardo_el_historial[la base falla]"
sabotaje "confirmar un NCM no avisa que el producto no entró" proyecto_maria/main.py \
  '            wrote_client = historial_guardado = entry is not None' \
  '            wrote_client = entry is not None' \
  "test_confirmar_un_ncm_dice_si_no_guardo_el_historial[crece al normalizar]"

# Lo que sólo Postgres muestra: la espera por la fila y la fila que cambia de
# clave o se borra mientras se espera. Sin PG_DSN no se corren y se dice.
MEMORIA=proyecto_maria/services/client_memory.py
sabotaje_pg() {
  local nombre="$1" viejo="$2" nuevo="$3" salida codigo; shift 3
  if [ -z "${PG_DSN:-}" ]; then
    echo "NO CORRIDO | $nombre: falta PG_DSN"; NO_CORRIDOS=$((NO_CORRIDOS+1)); return
  fi
  git checkout -q -- proyecto_maria/
  if ! aplicar "$MEMORIA" "$viejo" "$nuevo"; then
    echo "ROTO  | $nombre: el sabotaje no encontró su patrón"; FALLAS=$((FALLAS+1)); return
  fi
  salida="$("$PY" scripts/testing/despacho1b_postgres.py "$PG_DSN" 2>&1)"; codigo=$?
  juzgar "$nombre" "$salida" "$codigo" "${@/#/FALLA | }"
  git checkout -q -- proyecto_maria/
}
NO_CORRIDOS=0
sabotaje_pg "el upsert no espera la fila" \
  '    ).with_for_update().execution_options(populate_existing=True)' \
  '    ).execution_options(populate_existing=True)' \
  "dos procesos guardan y aprenden el mismo producto a la vez: una fila con 16 usos"
sabotaje_pg "el upsert no reintenta si la fila se fue" \
  '    for _ in range(3):' \
  '    for _ in range(1):' \
  "operacion, la fila cambia de clave mientras espera" "operacion, la fila se borra mientras espera" \
  "aprender, la fila cambia de clave mientras espera" "aprender, la fila se borra mientras espera" \
  "guardar, la fila cambia de clave mientras espera" "guardar, la fila se borra mientras espera" \
  "guardar-uso, la fila cambia de clave mientras espera" "guardar-uso, la fila se borra mientras espera"
echo "sin Postgres, no corridos: $NO_CORRIDOS"

echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ] && [ "$NO_CORRIDOS" -eq 0 ]
