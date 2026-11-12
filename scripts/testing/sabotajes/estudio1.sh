#!/usr/bin/env bash
# Negativos de ESTUDIO-1: cada sabotaje deshace una línea de la pieza y la
# prueba tiene que fallar por ese motivo. Primero la API (tests/test_estudio1.py),
# después la pantalla (scripts/testing/pantalla_estudio1.js).
#
# uso: PY=/ruta/al/venv/bin/python [PUERTO=8852] scripts/testing/sabotajes/estudio1.sh [SHA]
# Trabaja en un worktree descartable con SQLite propia y sin terceros: no toca
# tu copia ni datos compartidos. La pantalla y el JS se leen en cada pedido,
# así que los sabotajes de la pantalla se aplican con la API andando.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
set -uo pipefail
REPO="$(git rev-parse --show-toplevel)"
SHA="$(git -C "$REPO" rev-parse "${1:-HEAD}")"
PY="${PY:-python}"
PUERTO="${PUERTO:-8852}"
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
T=tests/test_estudio1.py

# ------------------------------------------------------------------ la API
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
correr() { "$PY" -m pytest -q --no-cov -p no:cacheprovider "$T" 2>&1; }

rm -f test.db
if ! correr >/dev/null; then
  echo "BASE  | la prueba de la API ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FAILED; exit 1
fi

sabotaje $M "la operación usa un estudio de otra cuenta" \
  'select(Estudio).where(Estudio.id == estudio_id, Estudio.owner_username == username)' \
  'select(Estudio).where(Estudio.id == estudio_id)' \
  "FAILED $T::test_otro_usuario_no_ve_ni_borra_ni_usa_los_estudios_ajenos"
sabotaje $M "la lista muestra los estudios de otra cuenta" \
  'select(Estudio).where(Estudio.owner_username == user["username"]).order_by(Estudio.nombre, Estudio.id)' \
  'select(Estudio).order_by(Estudio.nombre, Estudio.id)' \
  "FAILED $T::test_otro_usuario_no_ve_ni_borra_ni_usa_los_estudios_ajenos"
sabotaje $M "se borra un estudio de otra cuenta" \
  'select(Estudio).where(Estudio.id == estudio_id, Estudio.owner_username == user["username"])' \
  'select(Estudio).where(Estudio.id == estudio_id)' \
  "FAILED $T::test_otro_usuario_no_ve_ni_borra_ni_usa_los_estudios_ajenos"
sabotaje $M "un estudio que no está cae en silencio al perfil" \
  $'    if estudio is None:\n        raise HTTPException(\n            status_code=400,\n            detail="El estudio elegido' \
  $'    if estudio is None:\n        return None\n        raise HTTPException(\n            status_code=400,\n            detail="El estudio elegido' \
  "FAILED $T::test_un_estudio_que_no_existe_da_error_y_no_cae_al_perfil"
sabotaje $M "el cuit_agr que manda la pantalla gana al estudio" \
  'effective_cuit_agr = estudio.cuit if estudio is not None else request.cuit_agr' \
  'effective_cuit_agr = request.cuit_agr or (estudio.cuit if estudio is not None else "")' \
  "FAILED $T::test_el_estudio_elegido_va_al_cddtagr_aunque_haya_perfil_y_cuit_agr"
sabotaje $M "el uso se anota antes de generar" \
  $'    estudio = await _estudio_elegido(db, request.estudio_id, user["username"])\n    if not request.items:' \
  $'    estudio = await _estudio_elegido(db, request.estudio_id, user["username"])\n    if estudio is not None:\n        estudio.last_used_at = datetime.now(timezone.utc)\n        await db.commit()\n    if not request.items:' \
  "FAILED $T::test_los_avisos_y_un_txt_que_no_se_genera_no_cuentan_como_uso"
sabotaje $M "los avisos anotan el uso" \
  $'    estudio = await _estudio_elegido(db, request.estudio_id, user["username"])\n    _textos_como_van_al_txt(request)\n' \
  $'    estudio = await _estudio_elegido(db, request.estudio_id, user["username"])\n    if estudio is not None:\n        estudio.last_used_at = datetime.now(timezone.utc)\n        await db.commit()\n    _textos_como_van_al_txt(request)\n' \
  "FAILED $T::test_los_avisos_y_un_txt_que_no_se_genera_no_cuentan_como_uso"
sabotaje $M "el uso no se anota" \
  '                estudio.last_used_at = datetime.now(timezone.utc)' \
  '                pass' \
  "FAILED $T::test_con_varios_se_preselecciona_el_ultimo_usado"
sabotaje $M "el error al generar no dice dónde cargarlo" \
  'detalle = FALTA_CUIT_DONDE_CARGARLO if str(e) == FALTA_CUIT_DEL_DESPACHANTE else str(e)' \
  'detalle = str(e)' \
  "FAILED $T::test_sin_estudio_ni_perfil_el_error_dice_donde_cargarlo"
sabotaje $M "el aviso no dice dónde cargarlo" \
  'supuestos = [FALTA_CUIT_DONDE_CARGARLO, *supuestos]' \
  'supuestos = [FALTA_CUIT_DEL_DESPACHANTE, *supuestos]' \
  "FAILED $T::test_sin_estudio_ni_perfil_el_error_dice_donde_cargarlo"
sabotaje $M "con estudio el aviso igual pide el CUIT" \
  'if estudio is None and not str(request.cuit_agr or "").strip()' \
  'if not str(request.cuit_agr or "").strip()' \
  "FAILED $T::test_con_estudio_los_avisos_no_piden_el_cuit"
sabotaje $M "el CUIT del estudio no se mira" \
  'if not cuit_valido(cuit):' \
  'if not cuit:' \
  "FAILED $T::test_el_alta_rechaza_un_cuit_que_no_es_de_11_digitos[3022222222]"
sabotaje $M "el verificador del CUIT no se mira" \
  'if not cuit_valido(cuit):' \
  'if not re.fullmatch(r"[0-9]{11}", cuit):' \
  "FAILED $T::test_el_alta_rechaza_un_cuit_con_el_verificador_mal"
sabotaje $M "el CUIT con guiones no se guarda limpio" \
  'cuit = "".join(payload.cuit.replace("-", "").split()) if isinstance(payload.cuit, str) else ""' \
  'cuit = payload.cuit.replace("-", "") if isinstance(payload.cuit, str) else ""; cuit = payload.cuit if cuit_valido(cuit) else cuit' \
  "FAILED $T::test_el_alta_guarda_el_cuit_sin_guiones_y_lo_lista"
sabotaje $M "un CUIT numérico entra" \
  'cuit = "".join(payload.cuit.replace("-", "").split()) if isinstance(payload.cuit, str) else ""' \
  'cuit = "".join(str(payload.cuit).replace("-", "").split()) if payload.cuit is not None else ""' \
  "FAILED $T::test_el_alta_rechaza_un_cuit_que_no_es_de_11_digitos[30222222229]"
sabotaje $M "el nombre en blanco entra" \
  'nombre = payload.nombre.strip() if isinstance(payload.nombre, str) else ""' \
  'nombre = payload.nombre if isinstance(payload.nombre, str) else ""' \
  "FAILED $T::test_el_alta_rechaza_un_nombre_vacio_o_que_no_sirve[   ]"
sabotaje $M "el nombre con salto de línea entra" \
  'any(ord(c) < 32 or 0x7f <= ord(c) <= 0x9f or 0xd800' \
  'any(0x7f <= ord(c) <= 0x9f or 0xd800' \
  "FAILED $T::test_el_alta_rechaza_un_nombre_vacio_o_que_no_sirve[Estudio\\nInventado]"
sabotaje $M "el nombre con un surrogate suelto da 500" \
  ' or 0xd800 <= ord(c) <= 0xdfff' '' \
  "FAILED $T::test_el_alta_rechaza_un_nombre_con_un_surrogate_suelto"
sabotaje $M "el nombre de más de 200 entra" \
  'len(nombre) > 200' 'len(nombre) > 2000' \
  "FAILED $T::test_el_alta_rechaza_un_nombre_vacio_o_que_no_sirve[xxxxx"
sabotaje $M "el mismo CUIT dos veces en la cuenta da 500" \
  $'    except IntegrityError:\n        # El mismo CUIT ya está en la cuenta' \
  $'    except ValueError:\n        # El mismo CUIT ya está en la cuenta' \
  "FAILED $T::test_el_mismo_cuit_dos_veces_en_la_cuenta_no_se_guarda"
sabotaje proyecto_maria/database/models.py "el repetido mira todas las cuentas" \
  'UniqueConstraint("owner_username", "cuit", name="uq_estudios_owner_cuit")' \
  'UniqueConstraint("cuit", name="uq_estudios_owner_cuit")' \
  "FAILED $T::test_el_mismo_cuit_en_otra_cuenta_si_se_guarda"
sabotaje $M "con varios sin usar se elige uno igual" \
  '    elif len(estudios) == 1:' '    elif estudios:' \
  "FAILED $T::test_con_varios_se_preselecciona_el_ultimo_usado"
sabotaje $M "el único no se preselecciona" \
  '    elif len(estudios) == 1:' '    elif False:' \
  "FAILED $T::test_se_preselecciona_el_unico"
sabotaje $M "se preselecciona el usado hace más tiempo" \
  'preseleccionado = max(usados, key=lambda u: (u[0], u[1] is None))[1]' \
  'preseleccionado = min(usados, key=lambda u: (u[0], u[1] is None))[1]' \
  "FAILED $T::test_con_varios_se_preselecciona_el_ultimo_usado"

# ------------------------------------------------------------- la pantalla
git checkout -q -- proyecto_maria/
export ENVIRONMENT=development DATABASE_URL=sqlite+aiosqlite:///./local.db GEMINI_API_KEY=test-key \
       JWT_SECRET_KEY=clave-inventada-solo-local-0123456789abcdef EMAIL_VERIFICATION_REQUIRED=false \
       ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x
"$PY" -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port "$PUERTO" >"$TMPD/api.log" 2>&1 &
API=$!
for _ in $(seq 1 60); do curl -fsS "http://127.0.0.1:$PUERTO/health" >/dev/null 2>&1 && break; sleep 1; done
curl -fsS "http://127.0.0.1:$PUERTO/health" >/dev/null || { echo "BASE  | la API no levantó"; tail -20 "$TMPD/api.log"; exit 1; }
export BASE_URL="http://127.0.0.1:$PUERTO"
correr() { node scripts/testing/pantalla_estudio1.js 2>&1; }
if ! correr >/dev/null; then
  echo "BASE  | la pantalla ya está en rojo sin sabotaje: no se puede medir nada"; correr | grep FALLA; exit 1
fi

H=proyecto_maria/templates/dashboard_v2.html
J=proyecto_maria/static/v2/screens/estudios.js
F=proyecto_maria/static/v2/screens/finalize.js

sabotaje $J "el nombre se muestra como HTML" \
  "info.textContent = e.nombre + ' · '" "info.innerHTML = e.nombre + ' · '" \
  "FALLA: el nombre del estudio se interpretó como HTML"
sabotaje $J "el único preseleccionado queda como elegido" \
  $'        if (elegidoAhora && ids.indexOf(elegidoAhora) < 0) elegidoAhora = null;   // lo borró\n        select.value = elegidoAhora !== null ? elegidoAhora\n            : (ids.indexOf(datos.preseleccionado) >= 0 ? datos.preseleccionado : \'\');' \
  $'        elegidoAhora = ids.indexOf(elegidoAhora) >= 0 ? elegidoAhora\n            : (ids.indexOf(datos.preseleccionado) >= 0 ? datos.preseleccionado : \'\');\n        select.value = elegidoAhora;' \
  "FALLA: con dos sin usar, ya viene uno elegido"
sabotaje $J "lo elegido que se borró queda pegado" \
  "        if (elegidoAhora && ids.indexOf(elegidoAhora) < 0) elegidoAhora = null;   // lo borró" "" \
  "FALLA: después de borrar, viene elegido"
sabotaje $J "borrar no pide confirmación" \
  "const ok = await CDI.confirm({" "const ok = true || await CDI.confirm({" \
  "FALLA: borrar no pide confirmación"
sabotaje $J "después del alta no se refresca la operación" \
  $'            await renderPerfil();\n            render();\n        } catch (err) {\n            mostrarError(String(err.message || err));\n        } finally {' \
  $'            await renderPerfil();\n        } catch (err) {\n            mostrarError(String(err.message || err));\n        } finally {' \
  "FALLA: con estudios, el selector no aparece"
sabotaje $J "el error del alta no se muestra" \
  "            mostrarError(String(err.message || err));
        } finally {" "        } finally {" \
  "FALLA: el CUIT corto no muestra error"
sabotaje $F "el pedido no lleva el estudio" \
  "estudio_id: CDI.estudios ? CDI.estudios.elegido() : ''," "estudio_id: ''," \
  "FALLA: estudio_id del pedido"
sabotaje $F "al validar no se leen los estudios" \
  "Promise.resolve(CDI.estudios ? CDI.estudios.render() : null)" "Promise.resolve(null)" \
  "FALLA: sin estudios, el hint no aparece"
sabotaje $J "lo elegido pasa a la operación siguiente" \
  "        if (elegidoPara !== operacionActual()) {   // otra operación" \
  "        if (false) {   // otra operación" \
  "FALLA: en la operación siguiente queda lo elegido en la anterior"
sabotaje $F "generar no espera la lista de estudios" \
  "        if (CDI.estudios) await CDI.estudios.listo();" "" \
  "FALLA: generar antes de la lista manda estudio_id"
sabotaje $J "un alta o un borrado no refresca los avisos" \
  "        if (antes !== despues) wrap.dispatchEvent(new Event('change'));" "" \
  "FALLA: después del alta, los avisos siguen pidiendo el CDDTAGR"
sabotaje $J "sin lista ni perfil, el hint promete el perfil" \
  "            hint.textContent = (CDI.currentUser && CDI.currentUser.cuit)
                ? 'No se pudieron leer tus estudios: se usa el CUIT de tu perfil.'" \
  "            hint.textContent = true
                ? 'No se pudieron leer tus estudios: se usa el CUIT de tu perfil.'" \
  "FALLA: hint sin perfil y sin lista"
sabotaje $H "el selector toma el ancho de la opción más larga" \
  '<select id="estudioSelect" class="form-input" style="width:100%;max-width:100%" hidden>' \
  '<select id="estudioSelect" class="form-input" hidden>' \
  "FALLA: la tarjeta del estudio se sale del teléfono"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
