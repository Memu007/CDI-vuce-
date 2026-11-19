#!/usr/bin/env bash
# Negativos del desempate del catálogo del proveedor: cada sabotaje deshace una
# parte de la regla (lo más parecido primero, después el último confirmado y, a
# la misma hora, la clave de la fila) y tests/test_catalogo4.py tiene que fallar.
# En Postgres lo mide scripts/testing/catalogo4_postgres.py.
#
# uso: PY=/ruta/al/venv/bin/python scripts/testing/sabotajes/catalogo4.sh [SHA]
# Trabaja en un worktree descartable con su propia SQLite y sin terceros.
# Sale con error si un sabotaje no encuentra su patrón o no pone rojo.
T=tests/test_catalogo4.py
source "$(dirname "$0")/_casos_y_pantalla.sh"
C=proyecto_maria/core/catalog_service.py
CASO=test_un_empate_de_parecido_no_depende_del_orden_de_las_filas
EMPATADAS="(f for p, f in puntajes if p == mejor), key=desempate"
ULTIMA="return row.ultima_vez is not None, row.ultima_vez, row.product_key"

sabotaje casos $C "el empate lo decide el orden de las filas" "$EMPATADAS" \
  "(f for p, f in puntajes if p == mejor), key=lambda f: 0" "AssertionError" $CASO
sabotaje casos $C "el último confirmado le gana a lo más parecido" "$EMPATADAS" \
  "(f for p, f in puntajes if p >= FUZZY_THRESHOLD), key=desempate" "AssertionError" $CASO
sabotaje casos $C "a la misma hora decide el orden de las filas" "$ULTIMA" \
  "return row.ultima_vez is not None, row.ultima_vez" "AssertionError" $CASO
sabotaje casos $C "una fila sin fecha le gana a una fechada" "$ULTIMA" \
  "return row.ultima_vez is None, row.ultima_vez, row.product_key" "AssertionError" $CASO
sabotaje casos $C "un producto nuevo toma la hora de la base, al segundo en SQLite" \
  $'                ultima_vez=ahora,\n' "" "AssertionError" $CASO
sabotaje casos $C "cada producto nuevo del lote con su hora" "ultima_vez=ahora," \
  "ultima_vez=datetime.now(timezone.utc)," "AssertionError" $CASO
sabotaje casos $C "cada producto del lote que ya estaba con su hora" "existing.ultima_vez = ahora" \
  "existing.ultima_vez = datetime.now(timezone.utc)" "AssertionError" $CASO

git checkout -q -- proyecto_maria/
echo "sabotajes sin rojo: $FALLAS"
[ "$FALLAS" -eq 0 ]
