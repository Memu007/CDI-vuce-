#!/usr/bin/env bash
# Negativos del origen habitual del cliente: cada sabotaje deshace una línea de
# lo que lo valida y lo guarda entero, de la migración o de cómo lo muestra la
# ficha y el formulario. Tienen que fallar con su frase tests/test_origen2.py,
# la pantalla y, con PG_URL (un Postgres local y descartable), la migración de
# scripts/testing/origen2_postgres.py. Sin PG_URL, esos se dicen no corridos.
#
# uso: PY=/ruta/al/venv/bin/python [PG_URL=postgresql://cdi@127.0.0.1:5432/postgres] \
#        scripts/testing/sabotajes/origen2.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite, una API local por
# corrida de pantalla y sin terceros: no toca tu copia ni datos compartidos.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo donde debe.
T=tests/test_origen2.py
PANTALLA=scripts/testing/pantalla_origen2.js
source "$(dirname "$0")/_casos_y_pantalla.sh"
PG_URL="${PG_URL:-}"
correr_pg() { "$PY" -I scripts/testing/origen2_postgres.py "$PG_URL" 2>&1; }
if [ -n "$PG_URL" ]; then
  salida="$(correr_pg)" || { echo "BASE  | la migración no pasa sin sabotaje"; tail -20 <<<"$salida"; exit 1; }
  echo "BASE  | Postgres: $(tail -1 <<<"$salida")"
fi
pg() { if [ -n "$PG_URL" ]; then sabotaje pg "$@"; else echo "NO CORRIDO | $2: sin PG_URL"; fi; }

M=proyecto_maria/main.py
CLI=proyecto_maria/static/v2/screens/clientes.js
CSS=proyecto_maria/static/v2/app_v2.css
HTML=proyecto_maria/templates/dashboard_v2.html
ES_PAIS=test_origen_habitual_es_un_pais_entero_o_da_400
OTRO=test_editar_otro_dato_deja_el_origen_que_ya_estaba
ALTA='    default_origin = client.get("default_origin")'
ALTA_VIEJA='    default_origin = str(client.get("default_origin", "")).strip().upper()[:3] or None'
EDICION='        client.default_origin = client_data["default_origin"]'
EDICION_VIEJA='        val = str(client_data.get("default_origin", "")).strip().upper()[:3]
        client.default_origin = val or None'

# 0. El recorte de vuelta, con lo de antes palabra por palabra.
pg $M "el alta recorta a 3" "$ALTA" "$ALTA_VIEJA" "FALLA | el alta guarda entero un origen de 54"
pg $M "la edición recorta a 3" "$EDICION" "$EDICION_VIEJA" "FALLA | la edición guarda «BRASIL» entero"
sabotaje casos $M "el alta recorta a 3" "$ALTA" "$ALTA_VIEJA" "AssertionError: BRASIL" "$ES_PAIS[alta]"
sabotaje casos $M "la edición recorta a 3" "$EDICION" "$EDICION_VIEJA" "AssertionError: BRASIL" "$ES_PAIS[edicion]"

# 1. La migración lleva la columna a text.
pg $M "la migración no toca el cliente" '                            ("operation_items", ("origen",)),
                            ("clients", ("default_origin",))):' '                            ("operation_items", ("origen",))):' \
  "FALLA | primer arranque: el origen es text"

# 2. Lo escrito se valida como en el catálogo.
sabotaje casos $M "lo que no es un país se guarda" '        origen, problema = origen_para_catalogo(limpio["default_origin"])
        if problema:' '        origen, problema = origen_para_catalogo(limpio["default_origin"])
        if False:' \
  "AssertionError: Narnia" "$ES_PAIS[alta]" "$ES_PAIS[edicion]"
sabotaje casos $M "lo escrito se guarda sin normalizar" '        limpio["default_origin"] = origen
' '' "AssertionError: países  bajos" "$ES_PAIS[alta]" "$ES_PAIS[edicion]"
sabotaje casos $M "lo vacío no pasa por el validador" '    if "default_origin" in limpio:' \
  '    if limpio.get("default_origin"):' "AssertionError" "$ES_PAIS[alta]" "$ES_PAIS[edicion]"
sabotaje casos $M "guardar otro dato borra el origen" '    if "default_origin" in client_data:
'"$EDICION" '    if True:
        client.default_origin = client_data.get("default_origin")' "AssertionError" "$OTRO"

# 3. La ficha muestra la etiqueta, escapada.
sabotaje pantalla $CLI "la etiqueta de arriba muestra lo guardado" \
  "Origen ' + CDI.escapeHtml(CDI.paisesMaria.etiqueta(c.default_origin))" "Origen ' + CDI.escapeHtml(c.default_origin)" \
  "FALLA: la ficha muestra «Origen 101» y «101 · BURKINA FASO»"
sabotaje pantalla $CLI "la etiqueta de arriba muestra HTML" \
  "Origen ' + CDI.escapeHtml(CDI.paisesMaria.etiqueta(c.default_origin))" "Origen ' + CDI.paisesMaria.etiqueta(c.default_origin)" \
  "no «<img src=x"
sabotaje pantalla $CLI "«Origen habitual» muestra lo guardado" \
  "['Origen habitual', CDI.paisesMaria.etiqueta(c.default_origin) || '—']" "['Origen habitual', c.default_origin || '—']" \
  "FALLA: la ficha muestra «Origen 101 · BURKINA FASO» y «101»"

# 4. La etiqueta de arriba: sus letras, un renglón, adentro y con «…» si no entra.
ORIGEN_CSS='.cx-hero-tag.is-origen { text-transform: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }'
TAGS_CSS='.cx-hero-tags { display: inline-flex; flex-wrap: wrap; gap: var(--s-1); max-width: 100%; }'
sabotaje pantalla $CSS "la etiqueta de arriba en mayúsculas" "$ORIGEN_CSS" \
  '.cx-hero-tag.is-origen { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }' \
  "la ficha fuerza las letras del origen"
sabotaje pantalla $CSS "la etiqueta de arriba baja de renglón" "$ORIGEN_CSS" \
  '.cx-hero-tag.is-origen { text-transform: none; overflow: hidden; text-overflow: ellipsis; }' \
  "la etiqueta del origen baja de renglón"
sabotaje pantalla $CSS "lo que no entra se dibuja afuera" "$ORIGEN_CSS" \
  '.cx-hero-tag.is-origen { text-transform: none; white-space: nowrap; text-overflow: ellipsis; }' \
  "lo que no entra en la etiqueta se sale o se corta sin «…»"
sabotaje pantalla $CSS "lo que no entra se corta sin «…»" "$ORIGEN_CSS" \
  '.cx-hero-tag.is-origen { text-transform: none; white-space: nowrap; overflow: hidden; }' \
  "lo que no entra en la etiqueta se sale o se corta sin «…»"
sabotaje pantalla $CSS "las etiquetas de arriba crecen fuera de la ficha" "$TAGS_CSS" \
  '.cx-hero-tags { display: inline-flex; flex-wrap: wrap; gap: var(--s-1); }' \
  "el origen se sale de la ficha"
sabotaje pantalla $CSS "la moneda le quita lugar al origen" "$TAGS_CSS" \
  '.cx-hero-tags { display: inline-flex; gap: var(--s-1); max-width: 100%; }' \
  "no entra entera en la etiqueta"

# 5. El formulario: muestra la etiqueta, ofrece la tabla, deja lo que no se tocó y tiene lugar.
sabotaje pantalla $CLI "el formulario manda el origen aunque no se toque" \
  "        if (origen !== origenVisto) body.default_origin = origen;" "        body.default_origin = origen;" \
  "FALLA: guardar otro dato reescribe «CN» → «310 · CHINA»"
sabotaje pantalla $CLI "el formulario muestra lo guardado" \
  "        if (fOrigen) fOrigen.value = CDI.paisesMaria.etiqueta(c.default_origin);" "        if (fOrigen) fOrigen.value = c.default_origin || '';" \
  "FALLA: el formulario muestra «CN» para «CN»"
sabotaje pantalla $CLI "el formulario compara con lo guardado y no con lo que muestra" \
  "        origenVisto = fOrigen ? fOrigen.value : '';" "        origenVisto = CDI.paisesMaria.etiqueta(c.default_origin);" \
  "FALLA: guardar otro dato con «A↵B» guardado da 400"
sabotaje pantalla $CLI "el formulario no ofrece los países" \
  "        \$('cfOrigenPaises').innerHTML = CDI.paisesMaria.optionMarkup();
" "" "FALLA: el formulario ofrece 0 países"
sabotaje pantalla $HTML "el campo no está unido a la lista" ' list="cfOrigenPaises"' '' \
  "FALLA: el formulario ofrece 0 países"
sabotaje pantalla $HTML "el origen comparte renglón con la moneda" '                        <div class="field">
                            <label class="field-label" for="cfOrigen">' '                        <div class="field-row"><div class="field">
                            <label class="field-label" for="cfOrigen">' \
  "FALLA: «331 · EMIRATOS ARABES,UNID» no entra en el campo de origen a 1280 px"

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
