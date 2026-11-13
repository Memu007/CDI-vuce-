#!/usr/bin/env bash
# Negativos de CUIT-GENERAR: cada sabotaje deshace una regla del CUIT del
# despachante al generar el TXT (main.py, controles_maria.py) o de cómo la
# pantalla muestra el rechazo y deja corregirlo (finalize.js, profile.js, la
# plantilla). Los casos de tests/test_cuit_generar.py tienen que fallar por ese
# motivo y ningún otro; la pantalla, con su frase.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/cuit_generar.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite, una API local por
# corrida de pantalla y sin terceros: no toca tu copia ni datos compartidos.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo donde debe.
T=tests/test_cuit_generar.py
PANTALLA=scripts/testing/pantalla_cuit_generar1.js
source "$(dirname "$0")/_casos_y_pantalla.sh"
M=proyecto_maria/main.py
C=proyecto_maria/core/controles_maria.py
F=proyecto_maria/static/v2/screens/finalize.js
P=proyecto_maria/static/v2/screens/profile.js
H=proyecto_maria/templates/dashboard_v2.html
MALO=test_con_un_cuit_del_despachante_malo_no_se_genera_y_dice_donde_corregirlo
BUENO=test_con_un_cuit_del_despachante_bueno_se_genera
DEL_PERFIL=("$MALO[guardado en el perfil]" "$MALO[guardado en el perfil, como lo manda la pantalla]"
            "$MALO[guardado con guiones]")
DE_LA_OPERACION=("$MALO[en cuit_agr, con uno bueno en el perfil]"
                 "$MALO[en cuit_agr con guiones, sin CUIT en el perfil]")
MIRA='if crudo and not cuit_valido(cuit):'
LLAMADA='        effective_cuit_agr, con_el_perfil = _cuit_del_despachante(estudio, request.cuit_agr, user)
'

# 1. No se genera con uno que no es un CUIT, venga del perfil o de la operación.
sabotaje casos $M "sólo se cuentan los dígitos" \
  "$MIRA" 'if crudo and len(cuit) != 11:' \
  "guardado en el perfil: 200" "${DEL_PERFIL[@]}" "${DE_LA_OPERACION[@]}"
sabotaje casos $M "el del perfil no se mira" \
  "$MIRA" 'if crudo and not es_el_del_perfil and not cuit_valido(cuit):' \
  "guardado con guiones: 200" "${DEL_PERFIL[@]}"
sabotaje casos $M "el que manda la operación no se mira" \
  "$MIRA" 'if crudo and es_el_del_perfil and not cuit_valido(cuit):' \
  "sin CUIT en el perfil: 200" "${DE_LA_OPERACION[@]}"
sabotaje casos $M "se rechaza después de contar la operación" \
  "$LLAMADA" '        try:
            effective_cuit_agr, con_el_perfil = _cuit_del_despachante(estudio, request.cuit_agr, user)
        except HTTPException:
            await _contar_maria(db, user["username"], request.operacion_id, "x", "x", 1, "MARIA_x")
            raise
' \
  "lo que no se genera no queda contado ni guardado" "${DEL_PERFIL[@]}" "${DE_LA_OPERACION[@]}"

# 2. El error dice dónde se corrige, según de dónde salió.
sabotaje casos $M "dónde se corrige, al revés" \
  '" if es_el_del_perfil' '" if not es_el_del_perfil' \
  "corregilo ahí.']} != {'errors': ['El CUIT del despachante «20999999998»" "${DEL_PERFIL[@]}" "${DE_LA_OPERACION[@]}"
sabotaje casos $M "el del perfil guardado con guiones no se reconoce como el del perfil" \
  'del_perfil = "".join(str((user or {}).get("cuit") or "").replace("-", "").split())' \
  'del_perfil = str((user or {}).get("cuit") or "")' \
  "corregilo ahí.']} != {'errors': ['El CUIT del despachante «20999999998»" "$MALO[guardado con guiones]"
sabotaje casos $M "se nombra como llegó" \
  'cuit = "".join(str(crudo).replace("-", "").split())' 'cuit = str(crudo)' \
  "assert ['20-11111118-9'] == ['20111111189']" "$MALO[en cuit_agr con guiones, sin CUIT en el perfil]" "$BUENO[cuit_agr con verificador 9 y guiones]"

# 3. Cuál se usa: el estudio, si no cuit_agr, si no el del perfil.
sabotaje casos $M "el del perfil manda sobre cuit_agr" \
  'crudo = (estudio.cuit if estudio is not None else cuit_agr) or del_perfil' \
  'crudo = (estudio.cuit if estudio is not None else del_perfil) or cuit_agr' \
  "cuit_agr, aunque el del perfil sea malo: 400" \
  "$MALO[en cuit_agr, con uno bueno en el perfil]" "$BUENO[cuit_agr, aunque el del perfil sea malo]"
sabotaje casos $M "el estudio elegido no manda" \
  'crudo = (estudio.cuit if estudio is not None else cuit_agr) or del_perfil' \
  'crudo = cuit_agr or del_perfil' \
  "el estudio, aunque los otros dos sean malos: 400" "$BUENO[el estudio, aunque los otros dos sean malos]"
sabotaje casos $C "el verificador sale siempre de «11 − resto»" \
  'esperado = 0 if resto == 0 else 9 if resto == 1 else 11 - resto' 'esperado = 11 - resto' \
  "cuit_agr con verificador 0: 400" "$BUENO[cuit_agr con verificador 0]" "$BUENO[cuit_agr con verificador 9 y guiones]"

# 4. En la pantalla: no se genera, el error queda a la vista con el nombre del
#    campo, y corregido en «Mi perfil» se genera sin recargar.
sabotaje pantalla $M "el servidor sólo cuenta los dígitos" \
  "$MIRA" 'if crudo and len(cuit) != 11:' \
  "FALLA: con 20999999998 guardado en el perfil se generó el TXT: CDDTAGR=20999999998"
sabotaje pantalla $M "el error manda a corregirlo en la operación" \
  '" if es_el_del_perfil' '" if not es_el_del_perfil' \
  "la pantalla no dice cuál es ni «Corregilo en «Mi perfil», campo «Mi CUIT (despachante)».»: error: El CUIT"
sabotaje pantalla $F "la pantalla no muestra los errores del servidor" \
  "const texto = (detail && Array.isArray(detail.errors)) ? detail.errors.join(' ') : detail;" 'const texto = detail;' \
  "campo «Mi CUIT (despachante)».»: error: [object Object]"
sabotaje pantalla $H "el campo del perfil se llama de otra manera" \
  '<label class="field-label" for="pfCuit">Mi CUIT (despachante)</label>' '<label class="field-label" for="pfCuit">CUIT</label>' \
  "la pantalla no dice cuál es ni «Corregilo en «Mi perfil», campo «CUIT».»"
sabotaje pantalla $P "el CUIT corregido no llega a la operación sin recargar" \
  '                CDI.currentUser.cuit = data.profile.cuit;
' '' \
  "FALLA: corregido en «Mi perfil», «Reintentar» terminó en «error: El CUIT del despachante «20999999998»"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
