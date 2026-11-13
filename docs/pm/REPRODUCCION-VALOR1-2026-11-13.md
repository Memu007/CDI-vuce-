# Reproducción de valor1 (2026-11-13)

Entrega de MARIA: trabajo `b1a70d1`, entregado en `03348000` (su merge de mi
rama), informe `a647bee3`, base `a88f62f3`. Sólo arnés: `sabotaje_valor1.sh`
pasa a 29 sabotajes con anclas en código y sale de
`sabotajes-conocidos.txt`. Revisado por la PM principal en worktrees en
`03348000`, con el guion de ese árbol. Veredicto: **aceptada e integrada**.

| qué | salida |
|---|---|
| `chequeo-6.py a88f62f3 b1a70d1` | producto +0/−0, arnés +21/−30, historia vacía, 0 AVISO: igual que el informe |
| `sabotaje_valor1.sh 0334800` (07:18–07:28 UTC) | 29 `ROJO`, 0 `FALLA`, `OK: los 29 sabotajes dan rojo por la razón esperada`, rc=0; `descuento_solo` 2 failed y `respuesta_vieja` 1, como el informe |
| `anclas_perdidas.py 0334800 \| grep -c sabotaje_valor1.sh` | 0 |
| grep de comentarios del informe sobre el guion | vacío |
| negativos de la PM, `tests/test_valor1.py` sobre `03348000`, en otro worktree, a la vez que los primeros casos del guion (07:18–07:19 UTC) | ver abajo |

| negativo de la PM en `finalize.js` | salida |
|---|---|
| sano | `75 passed` |
| `if (seq !== avisosSeq) return;` → `if (seq < avisosSeq - 5) return;` (tolera respuestas un poco viejas) | `1 failed`: `test_una_respuesta_vieja_no_pisa_las_cuentas_nuevas` |
| antes de `if (ofrece) …`, `if (descuento > 0 && !op.ajustes_deducir) op.ajustes_deducir = String(descuento);` (pone el descuento solo sólo si el campo está vacío) | `1 failed`: `test_el_descuento_de_la_planilla_se_ofrece_y_no_se_pone_solo` |

Los dos son distintos del 26 (`if (false)`) y del 10 (pone siempre) de la
Dev, y cada uno lo ve la prueba que corresponde.

El 13 (`ajuste_mal_escrito_vacio`) y el 24 (`mal_escrito_se_borra`) no
están: salieron por D221 (b) y D222 (a), pedidos en el veredicto `0e517939`.

**Supuestos de la Dev, aceptados.** La renumeración y el total del mensaje
(31 → 29), el 26 como cambio de condición y la baja en el mismo commit que el
guion.

**A la cola, no devolución.** Dos cosas del guion. El total del mensaje
final (`los 29 sabotajes`) se escribe a mano, y por eso hubo que renumerar;
contarlo de los `caso` que corrieron lo evita. Y no corre antes una vez sin
sabotear: si el árbol sano ya estuviera rojo en la prueba que nombra un
`caso`, ese `caso` daría `ROJO` igual. Acá el control es mi `75 passed` sano
sobre `03348000`.

No corrido: pytest entero y adversarios (sólo arnés).
