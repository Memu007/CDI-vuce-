#!/usr/bin/env bash
# Negativos de los países sin sigla en el lector de despachos: cada sabotaje
# deshace una línea del arreglo y el caso de tests/test_catalogo3.py o la
# pantalla de importar despachos tienen que fallar con su frase. El «Origen
# frecuente» con 434 está en holanda423.sh, que corre esa pantalla.
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
DEVUELVE='return _iso2_por_codigo_maria().get(codigo, f"{codigo:03d}") if codigo else por_nombre or None'
PROPIO='codigo_de_pais(f"{codigo:03d} · {nombre}") is None'

# 1. El lector: el código sin sigla sale, y código y nombre de dos países no dan ninguno.
sabotaje casos $L "el código sin sigla no da origen" "$DEVUELVE" \
  "return _iso2_por_codigo_maria().get(codigo) or por_nombre or None" \
  "At index 0 diff: '310' != '143'" $CASO
sabotaje casos $L "código y nombre de dos países dan el código" \
  "if codigo and por_nombre and $PROPIO:" "if False:" \
  "At index 0 diff: '143' != None" $CASO
sabotaje casos $L "el nombre se compara por sigla y no con su código" \
  "$PROPIO" "codigo_de_pais(por_nombre) != codigo" \
  "diff: '310' != '435'" $CASO

# 2. La pantalla de importar deja escribir el código de tres cifras.
sabotaje pantalla $CLI "el origen del despacho vuelve a cortar en dos" \
  "' maxlength=\"3\" autocapitalize" "' maxlength=\"2\" autocapitalize" \
  "FALLA: 1280 px: el panel no se cerró al guardar"

echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
