#!/usr/bin/env bash
# Negativos de lo que muestra la pantalla para un origen: cada sabotaje deshace
# una llamada a `mostrar` (paises_maria.js), que en los catálogos pone el código
# que sale en el TXT en lugar del 434, o a `etiqueta`, que en el «Origen
# frecuente» y la procedencia de la revisión pone el código y el nombre del TXT.
# El caso de tests/test_catalogo3.py y la pantalla tienen que fallar con su frase.
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
ETIQUETA="return label(value) || String(value || '').trim();"
ETQ=test_la_etiqueta_es_la_del_txt

# 0. La etiqueta vaciada: se ve lo de antes, el código del TXT sólo en lugar del 434.
sabotaje casos $J "la etiqueta es lo que muestra el catálogo" "$ETIQUETA" "return mostrar(value);" \
  "AssertionError" $ETQ
sabotaje pantalla $J "la etiqueta es lo que muestra el catálogo" "$ETIQUETA" "return mostrar(value);" \
  "FALLA: el origen frecuente «434» se ve «423»"
sabotaje casos $J "la etiqueta es sólo el código" "$ETIQUETA" "return resolve(value) || String(value || '').trim();" \
  "AssertionError" $ETQ
sabotaje casos $J "la etiqueta escribe «null» por lo que falta" "$ETIQUETA" "return label(value) || String(value).trim();" \
  "AssertionError" $ETQ
sabotaje casos $J "la etiqueta deja los blancos de los bordes" "$ETIQUETA" \
  "return label(value) || String(value || '');" "AssertionError" $ETQ
sabotaje pantalla $CLI "el origen frecuente se ve como HTML" "kpiOrigen.textContent   = CDI.paisesMaria.etiqueta(" \
  "kpiOrigen.innerHTML   = CDI.paisesMaria.etiqueta(" "FALLA: el origen frecuente «<img"

# 1. `mostrar` pone el código del TXT en lugar del reemplazado.
sabotaje casos $J "mostrar devuelve lo que vino" "$MUESTRA" "return String(value ?? '');" \
  "At index 0 diff: '434' != '423'" test_holanda_y_paises_bajos_son_423
sabotaje casos $J "mostrar escribe «null» por lo que falta" "$MUESTRA" \
  "return (code && REEMPLAZOS[code[1]] && resolve(value)) || String(value);" \
  "'null' != ''" test_holanda_y_paises_bajos_son_423
sabotaje casos $J "mostrar recorta lo que no es el 434" "$MUESTRA" \
  "return (code && REEMPLAZOS[code[1]] && resolve(value)) || String(value ?? '').trim();" \
  "'Holanda' != ' Holanda '" test_holanda_y_paises_bajos_son_423
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
  "CDI.paisesMaria.etiqueta(normalized) : normalized" "normalized : normalized" \
  "FALLA: procedencia «434» del borrador se ve «434»"
sabotaje pantalla $REV "la procedencia escrita queda como se escribió" \
  "if (el.name === 'procedencia' && ev.type === 'change') el.value" "if (false) el.value" \
  "FALLA: procedencia «434» escrita se ve «434»"

# 3. Lo que se ve no se guarda solo, y mientras se escribe no se toca.
sabotaje pantalla $REV "la procedencia del borrador cambia en la operación" \
  "const normalized = valorEnLaRevision(key, op);" \
  "const normalized = key === 'procedencia' ? CDI.paisesMaria.etiqueta(valorEnLaRevision(key, op)) : valorEnLaRevision(key, op);" \
  "FALLA: procedencia «434» del borrador queda «423 · PAISES BAJOS» en la operación"
sabotaje pantalla $REV "la procedencia escrita se guarda como se ve" \
  "el.value = CDI.paisesMaria.etiqueta(value);" "el.value = op[el.name] = CDI.paisesMaria.etiqueta(value);" \
  "FALLA: procedencia «434» escrita queda «423 · PAISES BAJOS» en la operación"
sabotaje pantalla $CAT "el catálogo del proveedor manda el origen sin tocar" \
  "if (campoOrigen.value !== campoOrigen.defaultValue) cambios.origen" "cambios.origen" \
  "FALLA: cambiar sólo el NCM reescribe el origen guardado"
sabotaje pantalla $CLI "el catálogo del cliente pisa lo que se sigue escribiendo" \
  "if (field === 'origen' && input.value.trim() === value)" "if (field === 'origen')" \
  "FALLA: lo escrito mientras se guardaba «434» quedó «423»"
sabotaje pantalla $REV "el borrador muestra cada campo con su etiqueta" \
  "el.value = key === 'procedencia' ? CDI.paisesMaria.etiqueta(normalized) : normalized;" \
  "el.value = CDI.paisesMaria.etiqueta(normalized);" \
  "FALLA: la factura «434» del borrador se ve «423 · PAISES BAJOS»"
sabotaje pantalla $REV "lo escrito en cualquier campo pasa por la etiqueta" \
  "if (el.name === 'procedencia' && ev.type === 'change') el.value" "if (ev.type === 'change') el.value" \
  "FALLA: la factura «0434» escrita se ve «423 · PAISES BAJOS»"
sabotaje pantalla $CLI "el catálogo del cliente muestra el código de lo escrito" \
  "input.value = CDI.paisesMaria.mostrar(value);" "input.value = CDI.paisesMaria.resolve(value) || value;" \
  "FALLA: «nl» escrito en origen del catálogo del cliente se ve «423»"
sabotaje pantalla $REV "la procedencia cambia en cada tecla" \
  "if (el.name === 'procedencia' && ev.type === 'change') el.value" "if (el.name === 'procedencia') el.value" \
  "FALLA: «4340» escrito tecla por tecla se ve «423 · PAISES BAJOS0»"
sabotaje pantalla $CLI "el origen frecuente se ve como vino" \
  "CDI.paisesMaria.etiqueta(metricas.origen_frecuente) || '—'" "metricas.origen_frecuente || '—'" \
  "FALLA: el origen frecuente «434» se ve «434»"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
