#!/usr/bin/env bash
# Negativos de los nombres de país: con todo el arreglo vaciado (los nombres que
# leen el servidor y la pantalla y la letra ancha) fallan los casos de la tabla,
# de Países Bajos y de la letra ancha; después, cada parte por separado.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/paises_nombres.sh [SHA]
# Trabaja en un worktree descartable: no toca tu copia ni datos compartidos.
# Necesita node para el caso de la pantalla.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo donde debe.
T=tests/test_paises_nombres.py
source "$(dirname "$0")/_casos_y_pantalla.sh"
G=proyecto_maria/core/maria_generator.py
J=proyecto_maria/static/v2/paises_maria.js
F=proyecto_maria/pdf_extractor.py
D=proyecto_maria/core/despacho_lector.py
LEEN_PY='for nombre in (*idiomas["en"], *idiomas["es"])}'
LEEN_JS='for (const nombre of [...idiomas.en, ...idiomas.es]) ALIASES[normalize(nombre)] ??= code;'
ANCHO='_ANCHO_COMPLETO = {c: c - 0xFEE0 for c in range(0xFF01, 0xFF5F)}'
TABLA=test_cada_pais_se_reconoce_por_su_nombre_en_ingles_y_en_castellano
PANT=test_la_pantalla_reconoce_los_mismos_nombres_que_el_servidor
DIF=test_los_nombres_dificiles_dan_su_pais_o_ninguno
# Holanda y Países Bajos ya eran alias de la tabla.
PB=(); for n in Netherlands "The Netherlands" NETHERLANDS Holland; do
  PB+=("test_paises_bajos_es_423_solo_con_423_o_con_434[$n]"); done
# Los nombres de ancho completo ya los pliega la normalización; las cifras y las siglas, no.
ancha() { local e; for e in "$@"; do echo "test_la_letra_ancha_se_lee_como_la_comun[$e]"; done; }
mapfile -t LA < <(ancha "310 BR" 310 434 BR CN "310 \\xb7 CHINA")
mapfile -t LA_DESPACHO < <(ancha "310 BR" 310 434)
mapfile -t LA_FACTURA < <(ancha 310 434 BR CN "310 \\xb7 CHINA")

# 1. Todo el arreglo vaciado a la vez: el ayudante aplica un solo cambio por sabotaje.
git checkout -q -- proyecto_maria/
aplicar $G "$LEEN_PY" "${LEEN_PY%\}} if False}" && aplicar $J "$LEEN_JS" "" && aplicar $F "$ANCHO" "_ANCHO_COMPLETO = {}" || exit 2
vistos="$(correr_casos | grep -E "^(FAILED|ERROR) [^ ]" | sed -E "s/^[A-Z]+ //; s/ - .*//" | sort)"
git checkout -q -- proyecto_maria/
for caso in "$TABLA" "${PB[0]}" "${LA[0]}"; do
  if grep -qF "$T::$caso" <<<"$vistos"; then echo "ROJO  | todo vaciado: $caso"
  else echo "VERDE | todo vaciado: $caso no falla"; FALLAS=$((FALLAS+1)); fi
done

# 2. Sólo la letra ancha vaciada: fallan los de la letra ancha y nada más.
sabotaje casos $F "sin letra ancha" "$ANCHO" "_ANCHO_COMPLETO = {}" "AssertionError" "${LA[@]}"

# 3. Cada parte por separado.
sabotaje casos $G "el servidor no lee los nombres" "$LEEN_PY" "${LEEN_PY%\}} if False}" \
  "AssertionError" "$TABLA" "$PANT" "${PB[@]}" "$DIF"
sabotaje casos $J "la pantalla no lee los nombres" "$LEEN_JS" "" "AssertionError" "$PANT"
sabotaje casos $D "el despacho no lee la letra ancha" 'str(texto or "").translate(_ANCHO_COMPLETO)' \
  'str(texto or "")' "AssertionError" "${LA_DESPACHO[@]}"
sabotaje casos $F "la factura no lee la letra ancha" "str(raw or '').translate(_ANCHO_COMPLETO).strip()" \
  "str(raw or '').strip()" "AssertionError" "${LA_FACTURA[@]}"
sabotaje casos $J "un nombre de la norma choca con el de otro país" '"es": ["Sudáfrica"]}' \
  '"es": ["Sudáfrica", "República de Sudáfrica"]}' "AssertionError" "$TABLA" \
  test_un_nombre_nuevo_no_cambia_el_pais_de_un_nombre_que_ya_se_reconocia

[ "$FALLAS" -eq 0 ] && echo "OK: todos los sabotajes en rojo" || { echo "FALLAS: $FALLAS"; exit 1; }
