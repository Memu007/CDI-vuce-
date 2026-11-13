#!/usr/bin/env bash
# Negativos de CUIT-PERFIL: cada sabotaje deshace una regla de lo que «Mi perfil»
# guarda como CUIT (main.py, controles_maria.py) o de cómo la pantalla muestra el rechazo
# (profile.js). Los casos de tests/test_cuit_perfil.py tienen que fallar por ese
# motivo y ningún otro; la pantalla, con su frase.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/cuit_perfil.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite, una API local por
# corrida de pantalla y sin terceros: no toca tu copia ni datos compartidos.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo donde debe.
T=tests/test_cuit_perfil.py
PANTALLA=scripts/testing/pantalla_cuit_perfil1.js
source "$(dirname "$0")/_casos_y_pantalla.sh"
M=proyecto_maria/main.py
C=proyecto_maria/core/controles_maria.py
P=proyecto_maria/static/v2/screens/profile.js
MALO=test_lo_que_no_es_un_cuit_no_se_guarda
BUENO=test_un_cuit_bueno_se_guarda_sin_separadores
GUARDADO=test_uno_malo_que_ya_estaba_guardado_queda_hasta_que_se_corrige
VERIFICADOR=("$MALO[verificador equivocado]" "$MALO[verificador equivocado, con guiones]"
             "$MALO[verificador equivocado, de una empresa]" "$MALO[d\\xedgitos de ancho completo]")
LARGO=("$MALO[diez d\\xedgitos]" "$MALO[doce d\\xedgitos]")

# 1. Lo que se guarda es un CUIT: once dígitos y su verificador.
sabotaje casos $M "sólo se cuentan los dígitos" \
  'if not cuit_valido(digits):' 'if len(digits) != 11:' \
  "verificador equivocado: 200" "${VERIFICADOR[@]}" "$GUARDADO"
sabotaje casos $M "no se mira nada" \
  'if not cuit_valido(digits):' 'if False:' \
  "diez dígitos: 200" "${VERIFICADOR[@]}" "${LARGO[@]}" "$GUARDADO"
sabotaje casos $M "el rechazo deja guardado el resto del pedido" \
  '            if not cuit_valido(digits):
' '            if not cuit_valido(digits):
                await db.commit()
' \
  "el pedido rechazado no deja nada guardado" "${VERIFICADOR[@]}" "${LARGO[@]}" "$GUARDADO"
sabotaje casos $M "uno malo ya guardado pasa si llega igual" \
  'if not cuit_valido(digits):' 'if not cuit_valido(digits) and digits != u.cuit:' \
  "Con el malo" "$GUARDADO"

# 2. Uno bueno queda sin separadores; el vacío lo borra.
sabotaje casos $M "se guarda como llegó" \
  '            u.cuit = digits' '            u.cuit = raw_cuit' \
  "'20-11111111-2' == '20111111112'" \
  "$BUENO['20-11111111-2']" "$BUENO[' 20 11111111 2 ']" "$BUENO['20.11111111.2']" "$BUENO['30-71234567-1']"
sabotaje casos $M "el vacío no lo borra" \
  '            u.cuit = None' '            pass' \
  "'20111111112' == ''" "$BUENO['']"
sabotaje casos $C "el verificador sale siempre de «11 − resto»" \
  'esperado = 0 if resto == 0 else 9 if resto == 1 else 11 - resto' 'esperado = 11 - resto' \
  "assert 400 == 200" "$BUENO['20111111120']" "$BUENO['20111111189']"

# 3. En la pantalla: no se guarda, el error del servidor queda junto al campo y
#    el malo que ya estaba se muestra.
sabotaje pantalla $M "el servidor sólo cuenta los dígitos" \
  'if not cuit_valido(digits):' 'if len(digits) != 11:' \
  "FALLA: «Mi perfil» guardó 20-99999999-8, que tiene el verificador equivocado"
sabotaje pantalla $P "la pantalla no dice lo que contestó el servidor" \
  "throw new Error((data && data.detail) || 'No se pudo guardar');" "throw new Error('No se pudo guardar');" \
  "FALLA: con 20-99999999-8 escrito terminó en «error: No se pudo guardar» y no en el error del CUIT"
sabotaje pantalla $P "el campo no queda marcado" \
  "        cuitInput.classList.add('is-error');
" '' \
  "FALLA: el campo del CUIT no queda marcado"
sabotaje pantalla $P "el que ya estaba guardado no se muestra" \
  "cuitInput.value = p.cuit ? CDI.formatCuit(p.cuit) : '';" "cuitInput.value = '';" \
  "FALLA: con 20-99999999-8 ya guardado, el campo muestra «»"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
