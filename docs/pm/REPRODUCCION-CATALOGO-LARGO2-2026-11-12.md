# Reproducción de la vuelta D216/D217 y del re-anclaje de `catalogo_largo2.sh` (2026-11-12)

Entrega de MARIA: arnés `204c638`, informe `0609e14`, base `e115e50`. Sólo
arnés (producto +0/−0). Revisado por la PM principal en un worktree aparte en
`204c638`, con los guiones de esa versión.

## Mi primera corrida no vale

A las 21:08 corrí los dos guiones desde mi rama, no desde `204c638`: el SHA
iba bien, pero los guiones eran los viejos (30 sabotajes en `sabotaje_maria3`,
8 `ROTO` en `catalogo_largo2` por las anclas que ella cambió). Se corrigió
corriéndolos desde el worktree de `204c638`. Regla para mí: el guion que se
reproduce es el del SHA entregado, no el de la rama de PM.

## Lo reproducido (21:24–21:44 UTC, guiones de `204c638`)

| qué | salida |
|---|---|
| `sabotaje_maria3.sh 204c638` | `VERDE sin sabotaje: 136 passed`; 32 `ROJO`; «OK: los 32 sabotajes dan rojo por la razón esperada»; salida 0 (igual al informe) |
| `catalogo_largo2.sh 204c638` con Postgres 16 | 37 `ROJO`; `VERDE \| la clave junta ﬁ con fi: la prueba no lo vio`; ningún `ROTO`; `fallas: 1`; salida 1 (igual: es D199) |
| `chequeo-6` por tramo | `e115e50..0baa07b` +6/−2; `8c4a434..ac58fb0` +18/−34; `dd89d03..a538124` +6/−2; `0baa07b..204c638` +3/−3; producto +0/−0 y 0 avisos en todos |
| `anclas_perdidas.py 204c638 \| grep -cE "catalogo_largo2\|sabotaje_maria3"` | `0` |
| `anclas_perdidas.py` sobre la unión con mi rama | los vencidos de `sabotajes-conocidos.txt` (maria1d, maria5, maria7, maria8, valor1, valor1b, guardar2); `e2e_rerun.sh` y `foco_cliente1.sh` «NO MEDIDO» y `limpieza1.sh` «SIN ANCLA», que no son anclas perdidas; `catalogo_largo2` ya no aparece |
| diff de `204c638..0609e14` fuera de `docs/pm` | sólo `org1`, que viene de mi rama (merge `829f2d1`) |

## Las decisiones, medidas

**D199: el sabotaje no es equivalente.** Comparé `clave_de_producto("a"+c+"b")`
con `NFD` y con `NFKD` en `_normalize`, para todos los caracteres de U+0080 a
U+2FFFF: cambian 5, justo los que `_compatible` deja sin NFKC: `ª º № ℠ ™`
(«Nº 5» pasa de `n 5` a `no 5`; «Bolt™» de `bolt` a `bolttm`). Con el
reemplazo literal del guion en `204c638`, `tests/test_catalogo3.py` pasa de
104 passed a 5 failed, 99 passed, entre ellos
`test_lo_que_se_lee_igual_se_encuentra[Tornillo Nº 8-Tornillo N° 8-exact]`
y `test_un_proveedor_latino_conserva_su_id[Industrias García Nº1-…]` (el id
guardado de un proveedor cambiaría). La protección existe y la ve
`test_catalogo3.py`, pero `catalogo_largo2.sh` sólo corre
`test_catalogo_largo2.py`. No se retira: se muda a `catalogo3.sh`, que corre
`test_catalogo3.py`.

**D218: confirmado.** Sin la tupla de `operation_items` en
`_migrate_catalogo_sin_tope`, `catalogo3_postgres.py` da
`FALLA | operation_items.origen pasa a text y la fila vieja queda igual`,
salida 1.

**D219.** Leído, no corrido: `_migrate_catalogo_claves` vuelve a armar al
arrancar los `vendor_id` de 60 o más caracteres desde `vendor_nombre`, así
que un cambio del esquema de corte se repara solo en las filas con nombre;
las que no lo tienen quedan huérfanas. El dato fijo sigue valiendo.

**D220: confirmado, y no es limpieza.** `_normalize('Arandela ﬁna')` da
`arandela na`; `_word_set` da `['arandela']`; `client_memory._norm_desc` da
`arandela na`. Cambiar `_norm_desc` cambia `descripcion_normalizada` ya
guardada: es producto y datos, con migración, y no hay camino medido hoy
(nadie midió facturas reales con ligaduras).

## Lo que no corrí

La suite completa, `e2e_maria.sh` (sobre el SHA y sobre la unión) y los
adversarios: la entrega es sólo arnés, producto +0/−0, y no toca el recorrido.
