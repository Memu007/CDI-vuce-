# Reproducción de DATOS1-DOS-OPERACIONES (2026-11-12)

Entrega de la Técnica: arnés `53bd7df1`, informe `67fef76b`, base `50124c63`.
Sólo tests (producto +0/−0). Revisado por la PM principal en dos worktrees
aparte en `53bd7df1`, con el guion de esa versión, entre las 23:10 y las
23:20 UTC.

## Lo reproducido

| qué | salida |
|---|---|
| `tests/test_datos1.py` (SQLite) | `11 passed, 5 warnings` |
| `datos1.sh 53bd7df1` | 22 `ROJO`; `sabotajes sin rojo: 0`; salida 0 |
| sabotaje nuevo, presupuesto | `ROJO \| sólo se borra el presupuesto de la primera operación` … «AssertionError: presupuesto de la operación 2» «assert 200 == 404» |
| sabotaje nuevo, ítems | `ROJO \| sólo se borran los ítems de la primera operación` … «AssertionError: ítems de la operación 2» «assert 1 == 0» |
| `ROTO`, `VERDE \|` o `ROJO?` en el log | ninguno |
| `chequeo-6.py 50124c63 53bd7df1` | producto +0/−0; arnés +31/−9; historia vacío; avisos: 0 |
| `anclas_perdidas.py 53bd7df1 \| grep datos1` | nada |

Igual al informe, salvo 5 warnings y no 3: los dos de más son `SyntaxWarning`
de `pdf_extractor.py:927` y `:936`, que salen sólo en la primera
compilación de un worktree nuevo (las corridas siguientes dan 3; ya está en
la cola).

## Negativos míos (otros bordes, mismo caso)

| mutación en `delete_cliente` | con el caso nuevo | con el caso de la base |
|---|---|---|
| N1: presupuesto sólo de la última operación (`operaciones[-1]`) | rojo, «presupuesto de la operación 1» | no medido |
| N2: ítems de todas las operaciones de todos (`isnot(None)`) | rojo, «otro cliente», `assert 0 > 0` | **verde** (`1 passed`) |
| N3: ítems de todas menos la primera (`operaciones[1:]`) | rojo, «ítems de la operación 1» | no medido |

N1 cubre el riesgo que ella anotó (si el orden se diera vuelta): el caso
sigue en rojo, nombrando la otra operación. N2 muestra que su supuesto
reversible (comprobar que los ítems ajenos siguen) suma un borde que antes
nadie veía: queda aceptado.

## Lo que no corrí

La suite completa, Postgres, `e2e_maria.sh` y los adversarios: la entrega es
sólo un caso de un archivo y su guion, producto +0/−0, y la tarea no los
pedía.
