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
M=proyecto_maria/main.py
CASO=test_generate_maria_valida_el_origen_que_sale_en_el_txt
AVISOS=test_los_avisos_no_toman_un_origen_que_falta_como_china
LUGARES=test_cada_lugar_lee_el_origen_que_sale_en_el_txt

sabotaje casos $G "la validación vuelve a leer sólo origen" \
  "        origen = origen_de(item)
        if not origen:" \
  "        origen = item.get('origen')
        if not origen:" \
  "('4340', 'CN')" $CASO $AVISOS
sabotaje casos $G "origen manda sobre pais_origen" \
  '("pais_origen", "origen")' '("origen", "pais_origen")' \
  "('4340', 'CN')" $CASO $AVISOS
sabotaje casos $G "un origen en blanco tapa al otro" \
  'return _primero_escrito(item, ("pais_origen", "origen"))' \
  'return str(item.get("pais_origen") or item.get("origen") or "")' \
  "('  ', '  ')" $CASO $LUGARES $AVISOS
sabotaje casos $G "el TXT vuelve a escribir su propio origen" \
  "        pais = origen_de(item)
        pais_codigo = get_pais_codigo(pais)
        # Procedencia" \
  "        pais = item.get('pais_origen') or item.get('origen', 'CN')
        pais_codigo = get_pais_codigo(pais)
        # Procedencia" \
  "('  ', 'BR')" $CASO $LUGARES

CRUDO="(item.get('pais_origen') or item.get('origen') or '')"

# Cada lugar que lee el origen, con `pais_origen or origen` en vez de origen_de.
sabotaje casos $G "la clave de posición lee pais_origen or origen" \
  "    pais = origen_de(item)
    pais_codigo = get_pais_codigo(pais)
    unidad" \
  "    pais = $CRUDO
    pais_codigo = get_pais_codigo(pais)
    unidad" \
  "'clave de posición'" $LUGARES
sabotaje casos $G "lo que se junta lee pais_origen or origen" \
  "or not pais_reconocido(origen_de(item)):" "or not pais_reconocido($CRUDO):" \
  "'clave de posición'" $LUGARES
sabotaje casos $G "la defensa del grupo lee pais_origen or origen" \
  "origenes = {clave_de_origen(origen_de(it)) for it in grupo_items}" \
  "origenes = {clave_de_origen(it.get('pais_origen') or it.get('origen') or '') for it in grupo_items}" \
  "'defensa del grupo'" $LUGARES
sabotaje casos $G "el supuesto de procedencia lee pais_origen or origen" \
  "if pais_reconocido(origen_de(item)) and not procedencia_de(item):" \
  "if pais_reconocido($CRUDO) and not procedencia_de(item):" \
  "'sin procedencia'" $LUGARES
sabotaje casos $G "el supuesto de estado lee pais_origen or origen" \
  "codigo_de_pais(origen_de(item)) not in (None, PAIS_ARGENTINA)" \
  "codigo_de_pais($CRUDO) not in (None, PAIS_ARGENTINA)" \
  "'sin estado'" $LUGARES

# Un origen que falta o no se reconoce, tomado como China antes de generar.
sabotaje casos $G "se junta con China" \
  " or not pais_reconocido(origen_de(item)):" ":" \
  "juntos 1 y 2" $AVISOS
sabotaje casos $G "lleva la procedencia por defecto" \
  "if pais_reconocido(origen_de(item)) and not procedencia_de(item):" \
  "if origen_de(item) and not procedencia_de(item):" \
  "procedencia 1, 2" $AVISOS
sabotaje casos $G "lleva el estado de importado" \
  "codigo_de_pais(origen_de(item)) not in (None, PAIS_ARGENTINA)" \
  "get_pais_codigo(origen_de(item)) != PAIS_ARGENTINA" \
  "estado 1, 2" $AVISOS
sabotaje casos $M "los avisos no dicen el origen" \
  '"avisos": errores_de_pais(items) + ' \
  '"avisos": [e for e in errores_de_pais(items) if "rigen" not in e] + ' \
  "['procedencia 1', 'estado 1']" $AVISOS

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
