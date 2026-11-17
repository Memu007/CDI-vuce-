#!/usr/bin/env bash
# Negativos de los países sin sigla y del país nombrado al lado del código en el
# lector de despachos: cada sabotaje deshace una línea del arreglo y el caso de
# tests/test_catalogo3.py o la pantalla de importar despachos tienen que fallar
# con su frase. El «Origen frecuente» con 434 está en holanda423.sh, que corre
# esa pantalla.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/sin_sigla.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite, una API local por
# corrida de pantalla y sin terceros: no toca tu copia ni datos compartidos.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo donde debe.
T=tests/test_catalogo3.py
PANTALLA=scripts/testing/pantalla_despacho1b.js
source "$(dirname "$0")/_casos_y_pantalla.sh"
L=proyecto_maria/core/despacho_lector.py
CLI=proyecto_maria/static/v2/screens/clientes.js
CASO=test_un_codigo_sin_sigla_entra_por_el_despacho
AL_LADO=test_un_codigo_con_otro_pais_al_lado_no_da_ninguno
DEVUELVE='return _iso2_por_codigo_maria().get(codigo, f"{codigo:03d}")'
PAIS='tabla[c] != tabla[codigo]'
LARGO='len("".join(nombre)) > 2'
ENTRE='es_palabra(i - 1) and es_palabra(j)'
NO_APLICA=' if palabras != ("NA",) else None'
ENTERO="codigo = _paises_por_palabras().get(palabras)$NO_APLICA"

# 1. El lector: el código sin sigla sale, y un código con otro país al lado no da ninguno.
sabotaje casos $L "el código sin sigla no da origen" "$DEVUELVE" \
  "return _iso2_por_codigo_maria().get(codigo)" \
  "At index 0 diff: '310' != '143'" $CASO $AL_LADO
sabotaje casos $L "código y nombre de dos países dan el código" \
  "if any($PAIS for c in _paises_nombrados(resto)):" "if False:" \
  "At index 0 diff: '143' != None" $CASO $AL_LADO
sabotaje casos $L "se compara el código y no el país" \
  "$PAIS" "c != codigo" \
  "diff: '310' != '435'" $CASO $AL_LADO
sabotaje casos $L "la puntuación tapa el nombre de otro país" \
  'palabras = re.findall(r"\w+", _normalizar_pais(texto))' "palabras = _normalizar_pais(texto).split()" \
  "At index 147 diff: '310' != '271'" $CASO $AL_LADO
sabotaje casos $L "lo que no es un nombre entero se descarta" \
  "_paises_nombrados(resto)" "{codigo_de_pais(resto.strip())} - {None}" \
  "{'143 CHINA POPULAR': '143'}" $CASO $AL_LADO
sabotaje casos $L "gana el nombre más corto" \
  "range(min(len(palabras), i + largo), i, -1)" "range(i + 1, min(len(palabras), i + largo) + 1)" \
  "At index 125 diff: '310' != '229'" $CASO $AL_LADO
sabotaje casos $L "un número pegado al código es código" \
  'r"(\d{3})\b(?!\W*\d)(.*)"' 'r"(\d{3})\b(.*)"' \
  "{'143 310': '143', '143,00': '143', '143.5': '143'}" $AL_LADO
sabotaje casos $L "dos letras cuentan entre dos palabras" "or not ($ENTRE)" "or True" \
  "{'310 MADE IN CHINA': None, '310 PAIS DE ORIGEN': None}" $AL_LADO
sabotaje casos $L "dos letras junto a una palabra no cuentan" "$ENTRE" "es_palabra(i - 1) or es_palabra(j)" \
  "{'310 CHINA (AD)': 'CN'}" $AL_LADO
sabotaje casos $L "un número cuenta como palabra" "palabras[k].isalpha()" "True" \
  "{'310 CHINA AD 125': 'CN'}" $AL_LADO
sabotaje casos $L "tres letras no cuentan entre dos palabras" "$LARGO" 'len("".join(nombre)) > 3' \
  "{'143 PRODUCTO USA ORIGINAL': '143'}" $AL_LADO
sabotaje casos $L "fuera de la tabla, una palabra suelta da el país" "$ENTERO" \
  "codigo = min(_paises_nombrados(resto) or {None})" \
  "'900 CAROLINA DEL SUR': 'SR'" $AL_LADO
sabotaje casos $L "fuera de la tabla, el nombre no da el país" "$ENTERO" "codigo = None" \
  "At index 0 diff: None != 'REP CENTROAFRICANA'" $AL_LADO
sabotaje casos $L "fuera de la tabla, «NA» es Namibia" "$NO_APLICA" "" \
  "{'900 NA': 'NA'}" $AL_LADO

# 2. La pantalla de importar no corta lo que se escribe en el origen.
ORIGEN="(campo === 'origen' ? ' autocapitalize"
sabotaje pantalla $CLI "el origen del despacho vuelve a cortar en dos" \
  "$ORIGEN" "(campo === 'origen' ? ' maxlength=\"2\" autocapitalize" \
  "FALLA: 1280 px: el panel no se cerró al guardar"
sabotaje pantalla $CLI "el origen del despacho corta en tres" \
  "$ORIGEN" "(campo === 'origen' ? ' maxlength=\"3\" autocapitalize" \
  "FALLA: 1280 px: el origen «ARGELIA» escrito quedó \"ARG\""

echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
