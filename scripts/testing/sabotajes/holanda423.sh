#!/usr/bin/env bash
# Negativos de lo que muestra la pantalla para Holanda: cada sabotaje deshace una
# llamada a `mostrar` (paises_maria.js), que pone el código que sale en el TXT en
# lugar del 434 guardado o escrito. El caso de tests/test_catalogo3.py y la
# pantalla tienen que fallar con su frase.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/holanda423.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite, una API local por
# corrida de pantalla y sin terceros: no toca tu copia ni datos compartidos.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo donde debe.
T=tests/test_catalogo3.py
PANTALLA=scripts/testing/pantalla_holanda423.js
source "$(dirname "$0")/_casos_y_pantalla.sh"
J=proyecto_maria/static/v2/paises_maria.js
CAT=proyecto_maria/static/v2/screens/catalogo.js
CLI=proyecto_maria/static/v2/screens/clientes.js
REV=proyecto_maria/static/v2/screens/review.js
MUESTRA="return (code && REEMPLAZOS[code[1]] && resolve(value)) || String(value ?? '');"

# 1. `mostrar` pone el código del TXT en lugar del reemplazado.
sabotaje casos $J "mostrar devuelve lo que vino" "$MUESTRA" "return String(value ?? '');" \
  "At index 0 diff: '434' != '423'" test_holanda_y_paises_bajos_son_423
sabotaje pantalla $J "mostrar devuelve lo que vino" "$MUESTRA" "return String(value ?? '');" \
  "FALLA: catálogo del proveedor: «434» guardado se ve «434»"

# 2. Cada lugar que muestra un origen guardado o escrito lo pasa por `mostrar`.
sabotaje pantalla $CAT "el catálogo del proveedor muestra lo guardado" \
  "const origen = CDI.paisesMaria.mostrar(p.origen);" "const origen = p.origen || '';" \
  "FALLA: catálogo del proveedor: «434» guardado se ve «434»"
sabotaje pantalla $CLI "el catálogo del cliente muestra lo guardado" \
  "CDI.escapeHtml(CDI.paisesMaria.mostrar(p.origen || 'XX'))" "CDI.escapeHtml(p.origen || 'XX')" \
  "FALLA: catálogo del cliente: «434» guardado se ve «434»"
sabotaje pantalla $CLI "el catálogo del cliente deja lo escrito" \
  "            if (field === 'origen' && input.value.trim() === value) input.value = CDI.paisesMaria.mostrar(value);
" "" \
  "FALLA: «434» escrito en el catálogo del cliente se ve «434»"
sabotaje pantalla $REV "la procedencia del borrador se ve como vino" \
  "CDI.paisesMaria.mostrar(normalized) : normalized" "normalized : normalized" \
  "FALLA: procedencia «434» del borrador se ve «434»"
sabotaje pantalla $REV "la procedencia escrita queda como se escribió" \
  "if (el.name === 'procedencia' && ev.type === 'change') el.value" "if (false) el.value" \
  "FALLA: procedencia «434» escrita se ve «434»"

# 3. Lo que se ve no se guarda solo, y mientras se escribe no se toca.
sabotaje pantalla $REV "la procedencia del borrador cambia en la operación" \
  "const normalized = valorEnLaRevision(key, op);" \
  "const normalized = key === 'procedencia' ? CDI.paisesMaria.mostrar(valorEnLaRevision(key, op)) : valorEnLaRevision(key, op);" \
  "FALLA: procedencia «434» del borrador queda «423» en la operación"
sabotaje pantalla $CAT "el catálogo del proveedor manda el origen sin tocar" \
  "if (campoOrigen.value !== campoOrigen.defaultValue) cambios.origen" "cambios.origen" \
  "FALLA: cambiar sólo el NCM reescribe el origen guardado"
sabotaje pantalla $CLI "el catálogo del cliente pisa lo que se sigue escribiendo" \
  "if (field === 'origen' && input.value.trim() === value)" "if (field === 'origen')" \
  "FALLA: lo escrito mientras se guardaba «434» quedó «423»"
sabotaje pantalla $REV "la procedencia cambia en cada tecla" \
  "if (el.name === 'procedencia' && ev.type === 'change') el.value" "if (el.name === 'procedencia') el.value" \
  "FALLA: «4340» escrito tecla por tecla se ve «4230»"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
