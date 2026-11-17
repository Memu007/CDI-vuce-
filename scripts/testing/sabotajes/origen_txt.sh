#!/usr/bin/env bash
# Negativos del origen que se valida y sale en el TXT: cada sabotaje deshace una
# parte de `origen_de` o de quien la usa, y el caso de tests/test_generar_maria_txt.py
# tiene que fallar.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/origen_txt.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y sin terceros.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo donde debe.
T=tests/test_generar_maria_txt.py
PANTALLA=
source "$(dirname "$0")/_casos_y_pantalla.sh"
G=proyecto_maria/core/maria_generator.py
CASO=test_generate_maria_valida_el_origen_que_sale_en_el_txt

sabotaje casos $G "la validación vuelve a leer sólo origen" \
  "        origen = origen_de(item)
        if not origen:" \
  "        origen = item.get('origen')
        if not origen:" \
  "('4340', 'CN')" $CASO
sabotaje casos $G "origen manda sobre pais_origen" \
  '("pais_origen", "origen")' '("origen", "pais_origen")' \
  "('4340', 'CN')" $CASO
sabotaje casos $G "un origen en blanco tapa al otro" \
  'return _primero_escrito(item, ("pais_origen", "origen"))' \
  'return str(item.get("pais_origen") or item.get("origen") or "")' \
  "('  ', 'BR')" $CASO
sabotaje casos $G "el TXT vuelve a escribir su propio origen" \
  "        pais = origen_de(item)
        pais_codigo = get_pais_codigo(pais)
        # Procedencia" \
  "        pais = item.get('pais_origen') or item.get('origen', 'CN')
        pais_codigo = get_pais_codigo(pais)
        # Procedencia" \
  "('  ', 'BR')" $CASO

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
