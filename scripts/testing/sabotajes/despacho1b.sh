#!/usr/bin/env bash
# Negativos de DESPACHO-1b (la devolución y la D41): cada sabotaje deshace
# un arreglo y tests/test_despacho1b.py tiene que fallar por ese motivo.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/despacho1b.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y sin terceros: no
# toca tu copia ni datos compartidos. Sale con error si un sabotaje no
# encuentra su patrón o no pone rojo donde tiene que ponerlo.
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
  "            except MemoryError:
                raise
            except LimitReachedError:" \
  "            except LimitReachedError:" \
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
  "if peso is not None and not (math.isfinite(peso) and peso <= _MAX_NUMERO):" \
  "if False:" \
  "test_un_peso_por_unidad_infinito_no_se_guarda[1.0-1e-320]" \
  "test_un_peso_por_unidad_infinito_no_se_guarda[900000000000.0-1e-300]" \
  "test_un_peso_por_unidad_infinito_no_se_guarda[100000000000.0-1e-05]"
sabotaje "el peso sin el tope" "$LECTOR" \
  "math.isfinite(peso) and peso <= _MAX_NUMERO" \
  "math.isfinite(peso)" \
  "test_un_peso_por_unidad_infinito_no_se_guarda[100000000000.0-1e-05]"
no_debe "el peso sin el tope" "$ULTIMA" \
  "test_un_peso_por_unidad_infinito_no_se_guarda[1.0-1e-320]" \
  "test_un_peso_por_unidad_infinito_no_se_guarda[900000000000.0-1e-300]"

# 5) Guardar: todo o nada, sin NUL, sin promediar con el vacío y sin sumar a
# un producto de otro NCM.
sabotaje "un commit por renglón" proyecto_maria/main.py \
  "solo_mismo_ncm=True, **campos)
        await db.commit()" \
  "solo_mismo_ncm=True, **campos)
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
sabotaje "la ruta usa el respaldo por descripción" proyecto_maria/main.py \
  "client_id=client_id, solo_mismo_ncm=True, **campos)" \
  "client_id=client_id, **campos)" \
  "test_guardar_no_funde_productos_con_ncm_distinto" \
  "test_guardar_no_toca_un_producto_que_ya_estaba_con_otro_ncm" \
  "test_guardar_no_funde_descripciones_casi_iguales_con_ncm_distinto[tipo a y tipo b]" \
  "test_guardar_no_funde_descripciones_casi_iguales_con_ncm_distinto[mismo texto largo adelante]"
no_debe "la ruta usa el respaldo por descripción" "$ULTIMA" "test_guardar_con_el_mismo_ncm_sigue_sumando"
sabotaje "el upsert ignora solo_mismo_ncm" proyecto_maria/services/client_memory.py \
  "if existing is None and not solo_mismo_ncm:" \
  "if existing is None:" \
  "test_guardar_no_funde_productos_con_ncm_distinto" \
  "test_guardar_no_toca_un_producto_que_ya_estaba_con_otro_ncm"
no_debe "el upsert ignora solo_mismo_ncm" "$ULTIMA" "test_guardar_con_el_mismo_ncm_sigue_sumando"

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
sabotaje "sin el tope de CPU" "$LECTOR" \
  "            if time.process_time() > hasta:" \
  "            if False:" \
  "test_un_pdf_que_da_mucho_trabajo_deja_de_leerse_por_tiempo_de_cpu" \
  "test_el_lector_aparte_usa_el_tope_de_cpu_que_recibe" \
  "test_el_lector_aparte_tiene_tope_de_cpu_sin_pedirlo"
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
  "            paginas = list(reader.pages)
        except MemoryError:
            raise
" \
  "            paginas = list(reader.pages)
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
sabotaje "el NCM se guarda con puntos" "$LECTOR" \
  "ncm = re.sub(r\"\\D\", \"\", posicion)[:8] if _POSICION.match(posicion) else None" \
  "ncm = posicion[:10] if _POSICION.match(posicion) else None" \
  "test_el_mismo_ncm_con_o_sin_puntos_es_el_mismo_producto"
sabotaje "el upsert compara el NCM tal cual" proyecto_maria/services/client_memory.py \
  "            ncm_sin_puntos == digitos," \
  "            ClientProductHistory.ncm == ncm," \
  "test_lo_aprendido_con_puntos_y_el_despacho_son_el_mismo_producto"
sabotaje "el upsert compara la descripción cortada" proyecto_maria/services/client_memory.py \
  "            if _misma_descripcion(row.descripcion) == buscada:" \
  "            if row.descripcion_normalizada == desc_norm:" \
  "test_dos_textos_largos_con_el_mismo_comienzo_no_se_funden"

# Devolución 20:07: los promedios y los topes.
sabotaje "el promedio cuenta los usos sin valor" proyecto_maria/services/client_memory.py \
  "    if veces is None:  # fila de antes de contar por valor" \
  "    if True:" \
  "test_el_promedio_no_cuenta_los_usos_sin_valor" \
  "test_el_historial_de_operaciones_tampoco_cuenta_los_usos_sin_valor"
sabotaje "el promedio acepta infinitos" proyecto_maria/services/client_memory.py \
  "    if not math.isfinite(valor) or valor <= 0 or valor >= _MAX_VALOR:" \
  "    if valor <= 0:" \
  "test_aprender_un_peso_infinito_no_lo_guarda_y_el_catalogo_anda" \
  "test_cambiar_el_peso_a_algo_que_no_es_un_peso_da_400[inf]" \
  "test_cambiar_el_peso_a_algo_que_no_es_un_peso_da_400[1e400]"
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
sabotaje "guardar no mira la mitad de par" "$LECTOR" \
  "    if _MEDIO_PAR.search(descripcion):
        problemas.append" \
  "    if False:
        problemas.append" \
  "test_guardar_una_mitad_de_par_suelta_da_422"

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

echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
