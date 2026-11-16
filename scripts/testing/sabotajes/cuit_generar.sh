#!/usr/bin/env bash
# Negativos de CUIT-GENERAR: cada sabotaje deshace una regla del CUIT del
# despachante al generar el TXT (main.py, controles_maria.py) o de cómo la
# pantalla muestra el rechazo y deja corregirlo (finalize.js, profile.js, la
# plantilla), también en los avisos de antes de generar. Los casos de tests/test_cuit_generar.py tienen que fallar por ese
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
AVISOS=test_los_avisos_dicen_lo_mismo_que_el_400_del_cuit_del_despachante
DEL_PERFIL=("$MALO[guardado en el perfil]" "$MALO[guardado en el perfil, como lo manda la pantalla]"
            "$MALO[guardado con guiones y un espacio]")
DE_LA_OPERACION=("$MALO[en cuit_agr, con uno bueno en el perfil]"
                 "$MALO[en cuit_agr con guiones, sin CUIT en el perfil]")
DEL_ESTUDIO="$MALO[en el estudio elegido, con uno bueno en el perfil y en cuit_agr]"
CON_ESPACIO="$BUENO[cuit_agr con verificador 9, guiones y un espacio]"
AVISA_EL_MALO=("$AVISOS[malo en el perfil]" "$AVISOS[malo en cuit_agr]" "$AVISOS[malo en el estudio elegido]")
EN_BLANCO=("$AVISOS[cuit_agr en blanco, con uno bueno en el perfil]" "$AVISOS[cuit_agr en blanco, sin CUIT en el perfil]")
MIRA='if cuit and not cuit_valido(cuit):'
L2='cuit = sin_separadores(estudio.cuit if estudio is not None else cuit_agr) or del_perfil'
SEPARADORES='        return "".join(str(valor or "").replace("-", "").split())'
DEL_PERFIL_LIMPIO='del_perfil = sin_separadores((user or {}).get("cuit"))'
# Lo que muestra pytest cuando el error manda a recargar y el caso esperaba otro lugar.
RECARGA="recargá la página.']} != {'errors': ['El CUIT del despachante «20999999998»"
LLAMADA='        effective_cuit_agr, con_el_perfil = _cuit_del_despachante(estudio, request.cuit_agr, user)
'

# 1. No se genera con uno que no es un CUIT, venga del perfil, de la operación
#    o del estudio elegido.
sabotaje casos $M "sólo se cuentan los dígitos" \
  "$MIRA" 'if cuit and len(cuit) != 11:' \
  "guardado en el perfil: 200" "${DEL_PERFIL[@]}" "${DE_LA_OPERACION[@]}" "$DEL_ESTUDIO" "${AVISA_EL_MALO[@]}"
sabotaje casos $M "el del perfil no se mira" \
  "$MIRA" 'if cuit and not es_el_del_perfil and not cuit_valido(cuit):' \
  "guardado con guiones y un espacio: 200" "${DEL_PERFIL[@]}" "$AVISOS[malo en el perfil]"
sabotaje casos $M "el que manda la operación no se mira" \
  "$MIRA" 'if cuit and (es_el_del_perfil or estudio is not None) and not cuit_valido(cuit):' \
  "sin CUIT en el perfil: 200" "${DE_LA_OPERACION[@]}" "$AVISOS[malo en cuit_agr]"
sabotaje casos $M "el del estudio elegido no se mira" \
  "$MIRA" 'if cuit and estudio is None and not cuit_valido(cuit):' \
  "en el estudio elegido, con uno bueno en el perfil y en cuit_agr: 200" "$DEL_ESTUDIO" "$AVISOS[malo en el estudio elegido]"
sabotaje casos $M "se rechaza después de contar la operación" \
  "$LLAMADA" '        try:
            effective_cuit_agr, con_el_perfil = _cuit_del_despachante(estudio, request.cuit_agr, user)
        except HTTPException:
            await _contar_maria(db, user["username"], request.operacion_id, "x", "x", 1, "MARIA_x")
            raise
' \
  "lo que no se genera no queda contado ni guardado" "${DEL_PERFIL[@]}" "${DE_LA_OPERACION[@]}" "$DEL_ESTUDIO"

# 2. El error dice dónde se corrige, según de dónde salió.
sabotaje casos $M "dónde se corrige, al revés" \
  'elif es_el_del_perfil:' 'elif not es_el_del_perfil:' \
  "$RECARGA" "${DEL_PERFIL[@]}" "${DE_LA_OPERACION[@]}" "$AVISOS[malo en el perfil]" "$AVISOS[malo en cuit_agr]"
sabotaje casos $M "el del estudio elegido manda a corregir como si lo mandara la operación" \
  '        if estudio is not None:
            donde' '        if False:
            donde' \
  "$RECARGA" "$DEL_ESTUDIO" "$AVISOS[malo en el estudio elegido]"
sabotaje casos $M "el del perfil guardado con guiones se nombra como está guardado" \
  "$DEL_PERFIL_LIMPIO" 'del_perfil = str((user or {}).get("cuit") or "")' \
  "{'errors': ['El CUIT del despachante «20-99999999 8»" "$MALO[guardado con guiones y un espacio]"
sabotaje casos $M "el del perfil guardado con un espacio en el medio se nombra con el espacio" \
  "$DEL_PERFIL_LIMPIO" 'del_perfil = str((user or {}).get("cuit") or "").replace("-", "").strip()' \
  "{'errors': ['El CUIT del despachante «2099999999 8»" "$MALO[guardado con guiones y un espacio]"
sabotaje casos $M "se nombra como llegó" \
  "$SEPARADORES" '        return str(valor or "")' \
  "assert ['20-11111118 9'] == ['20111111189']" "$MALO[guardado con guiones y un espacio]" \
  "$MALO[en cuit_agr con guiones, sin CUIT en el perfil]" "$CON_ESPACIO" "${EN_BLANCO[@]}"
sabotaje casos $M "un espacio en el medio queda en el CDDTAGR" \
  "$SEPARADORES" '        return str(valor or "").replace("-", "").strip()' \
  "assert ['2011111118 9'] == ['20111111189']" "$MALO[guardado con guiones y un espacio]" "$CON_ESPACIO"

# 3. Cuál se usa: el estudio, si no cuit_agr, si no el del perfil.
sabotaje casos $M "el del perfil manda sobre cuit_agr" \
  "$L2" 'cuit = sin_separadores(estudio.cuit if estudio is not None else del_perfil) or sin_separadores(cuit_agr)' \
  "cuit_agr, aunque el del perfil sea malo: 400" "$MALO[en cuit_agr, con uno bueno en el perfil]" \
  "$BUENO[cuit_agr, aunque el del perfil sea malo]" "$AVISOS[malo en cuit_agr]" "$AVISOS[uno bueno]"
sabotaje casos $M "el estudio elegido no manda" \
  "$L2" 'cuit = sin_separadores(cuit_agr) or del_perfil' \
  "el estudio, aunque los otros dos sean malos: 400" "$BUENO[el estudio, aunque los otros dos sean malos]" "$DEL_ESTUDIO" \
  "$AVISOS[malo en el estudio elegido]"
sabotaje casos $M "un cuit_agr en blanco tapa el del perfil" \
  "$L2" 'cuit = sin_separadores((estudio.cuit if estudio is not None else cuit_agr) or del_perfil)' \
  "AssertionError: cuit_agr en blanco, con uno bueno en el perfil: avisan ['Falta el CUIT" \
  "$AVISOS[cuit_agr en blanco, con uno bueno en el perfil]"
sabotaje casos $M "los avisos no dicen que no cierra" \
  '        supuestos = [*e.detail["errors"], *supuestos]' '        pass' \
  "AssertionError: malo en el perfil: avisan [], sale ['El CUIT del despachante «20999999998»" "${AVISA_EL_MALO[@]}"
sabotaje casos $C "el verificador sale siempre de «11 − resto»" \
  'esperado = 0 if resto == 0 else 9 if resto == 1 else 11 - resto' 'esperado = 11 - resto' \
  "cuit_agr con verificador 0: 400" "$BUENO[cuit_agr con verificador 0]" "$CON_ESPACIO"

# 4. En la pantalla: no se genera, el error queda a la vista con el nombre del
#    campo, y corregido en «Mi perfil» se genera sin recargar.
sabotaje pantalla $M "el servidor sólo cuenta los dígitos" \
  "$MIRA" 'if cuit and len(cuit) != 11:' \
  "FALLA: con 20999999998 guardado en el perfil se generó el TXT: CDDTAGR=20999999998"
sabotaje pantalla $M "el error manda a corregirlo en la operación" \
  'elif es_el_del_perfil:' 'elif not es_el_del_perfil:' \
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
