#!/usr/bin/env bash
# Negativos de lo que muestra la pantalla para un origen: cada sabotaje deshace
# una llamada a `etiqueta` (paises_maria.js), que en los catálogos, el «Origen
# frecuente» y la procedencia de la revisión pone el código y el nombre del TXT,
# o el campo donde se ve y se escribe. El caso de tests/test_catalogo3.py y la
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
CSS=proyecto_maria/static/v2/app_v2.css
ETIQUETA="return label(value) || String(value || '').trim();"
ETQ=test_la_etiqueta_es_la_del_txt

# 0. La etiqueta vaciada: se ve lo que vino.
sabotaje casos $J "la etiqueta es lo que vino" "$ETIQUETA" "return String(value || '').trim();" \
  "AssertionError" $ETQ
sabotaje pantalla $J "la etiqueta es lo que vino" "$ETIQUETA" "return String(value || '').trim();" \
  "FALLA: catálogo del proveedor: «434» guardado se ve «434»"
sabotaje casos $J "la etiqueta es sólo el código" "$ETIQUETA" "return resolve(value) || String(value || '').trim();" \
  "AssertionError" $ETQ
sabotaje casos $J "la etiqueta escribe «null» por lo que falta" "$ETIQUETA" "return label(value) || String(value).trim();" \
  "AssertionError" $ETQ
sabotaje casos $J "la etiqueta deja los blancos de los bordes" "$ETIQUETA" \
  "return label(value) || String(value || '');" "AssertionError" $ETQ
sabotaje pantalla $CLI "el origen frecuente se ve como HTML" "kpiOrigen.textContent   = CDI.paisesMaria.etiqueta(" \
  "kpiOrigen.innerHTML   = CDI.paisesMaria.etiqueta(" "FALLA: el origen frecuente «<img"

# 1. Cada lugar que muestra un origen guardado o escrito lo pasa por `etiqueta`.
sabotaje pantalla $CAT "el catálogo del proveedor muestra lo guardado" \
  "const origen = CDI.paisesMaria.etiqueta(p.origen);" "const origen = p.origen || '';" \
  "FALLA: catálogo del proveedor: «434» guardado se ve «434»"
sabotaje pantalla $CAT "el catálogo del proveedor muestra lo guardado como HTML" \
  "value=\"' + CDI.escapeHtml(origen) + '\"" "value=\"' + origen + '\"" \
  "FALLA: catálogo del proveedor: «<img"
sabotaje pantalla $CLI "el catálogo del cliente muestra lo guardado" \
  "CDI.escapeHtml(CDI.paisesMaria.etiqueta(p.origen || 'XX'))" "CDI.escapeHtml(p.origen || 'XX')" \
  "FALLA: catálogo del cliente: «434» guardado se ve «434»"
sabotaje pantalla $CLI "el catálogo del cliente muestra lo guardado como HTML" \
  "CDI.escapeHtml(CDI.paisesMaria.etiqueta(p.origen || 'XX'))" "CDI.paisesMaria.etiqueta(p.origen || 'XX')" \
  "FALLA: catálogo del cliente: «<img"
sabotaje pantalla $CLI "el catálogo del cliente deja lo escrito" \
  "            if (field === 'origen' && input.value.trim() === value) input.value = CDI.paisesMaria.etiqueta(value);
" "" \
  "FALLA: «434» escrito en el catálogo del cliente se ve «434»"

# 2. El campo del origen deja escribir un nombre y lo muestra entero.
sabotaje pantalla $CLI "el catálogo del cliente corta el origen en 3" \
  "CDI.paisesMaria.etiqueta(p.origen || 'XX')) + '\" title=\"Origen\">'" \
  "CDI.paisesMaria.etiqueta(p.origen || 'XX')) + '\" title=\"Origen\" maxlength=\"3\">'" \
  "FALLA: «CHINA» escrito en origen del catálogo del cliente se ve «CHI»"
sabotaje pantalla $CSS "el origen del catálogo del cliente en el ancho de un código" \
  '.cx-catalogo-producto-input[data-field="origen"] { width: 22ch;' '.cx-catalogo-producto-input[data-field="origen"] { width: 36px;' \
  "FALLA: catálogo del cliente: «310 · CHINA» no entra en el campo"
sabotaje pantalla $CSS "el origen del catálogo del proveedor en el ancho de un código" \
  "    grid-template-columns: 1fr 2fr;
    gap: var(--s-2);
}
.catalogo-product-field {" "    grid-template-columns: 1fr 90px;
    gap: var(--s-2);
}
.catalogo-product-field {" \
  "FALLA: catálogo del proveedor: «423 · PAISES BAJOS» no entra en el campo"
sabotaje pantalla $CSS "el origen del catálogo del proveedor con su ancho propio" \
  "    width: 100%;
    min-width: 0;
    padding: 6px 8px;" "    padding: 6px 8px;" \
  "FALLA: catálogo del proveedor: el campo de origen se sale de su fila"
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
sabotaje casos proyecto_maria/core/catalog_service.py "guardar otro campo del proveedor borra el origen" \
  'if updates.get("origen") is not None:
        origen, aviso = origen_para_guardar(updates["origen"])' 'if True:
        origen, aviso = origen_para_guardar(updates.get("origen"))' \
  "AssertionError" test_cada_pais_del_catalogo_vuelve_a_su_codigo
sabotaje casos proyecto_maria/main.py "guardar otro campo del cliente borra el origen" \
  'if "origen" in body:
        origen, problema = origen_para_catalogo(body["origen"])' 'if True:
        origen, problema = origen_para_catalogo(body.get("origen"))' \
  "AssertionError" test_cada_pais_del_catalogo_vuelve_a_su_codigo
sabotaje pantalla $CLI "el catálogo del cliente pisa lo que se sigue escribiendo" \
  "if (field === 'origen' && input.value.trim() === value)" "if (field === 'origen')" \
  "FALLA: lo escrito mientras se guardaba «434» quedó «423 · PAISES BAJOS»"
sabotaje pantalla $REV "el borrador muestra cada campo con su etiqueta" \
  "el.value = key === 'procedencia' ? CDI.paisesMaria.etiqueta(normalized) : normalized;" \
  "el.value = CDI.paisesMaria.etiqueta(normalized);" \
  "FALLA: la factura «434» del borrador se ve «423 · PAISES BAJOS»"
sabotaje pantalla $REV "lo escrito en cualquier campo pasa por la etiqueta" \
  "if (el.name === 'procedencia' && ev.type === 'change') el.value" "if (ev.type === 'change') el.value" \
  "FALLA: la factura «0434» escrita se ve «423 · PAISES BAJOS»"
sabotaje pantalla $CLI "el catálogo del cliente muestra el código de lo escrito" \
  "input.value = CDI.paisesMaria.etiqueta(value);" "input.value = CDI.paisesMaria.resolve(value) || value;" \
  "FALLA: «434» escrito en el catálogo del cliente se ve «423»"
sabotaje pantalla $REV "la procedencia cambia en cada tecla" \
  "if (el.name === 'procedencia' && ev.type === 'change') el.value" "if (el.name === 'procedencia') el.value" \
  "FALLA: procedencia «434» escrita queda «423 · PAISES BAJOS» en la operación"
sabotaje pantalla $CLI "el origen frecuente se ve como vino" \
  "CDI.paisesMaria.etiqueta(metricas.origen_frecuente) || '—'" "metricas.origen_frecuente || '—'" \
  "FALLA: el origen frecuente «434» se ve «434»"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
