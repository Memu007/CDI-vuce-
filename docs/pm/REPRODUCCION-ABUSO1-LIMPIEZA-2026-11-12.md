# Reproducción de ABUSO1-LIMPIEZA (2026-11-12)

Entrega de la Técnica: arnés `c193af5d`, informe `99b549ec`, base `00ac6b29`.
Sólo tests (producto +0/−0). Revisado por la PM principal en dos worktrees
aparte en `c193af5d`, con los guiones de esa versión, entre las 22:25 y las
22:58 UTC.

## Lo reproducido

| qué | salida |
|---|---|
| `test_abuso1.py -k tres_por_hora` | `2 passed, 72 deselected` |
| su mutación literal, reset (`return mensaje` → `pass`) | `FAILED …[reset]` «el cuarto pedido de la hora mandó el mail»; `1 failed, 1 passed` |
| su mutación literal, recuperar | `FAILED …[recuperar]`, mismo texto; `1 failed, 1 passed` |
| `reset3.sh c193af5d` con `PG_URL` (Postgres 16) | `BASE \| 74 passed`; `BASE \| Postgres: fallas: 0`; 8 `ROJO`; `sabotajes sin rojo: 0`; rc 0 |
| `abuso1.sh c193af5d` | 34 `ROJO`; `sabotajes sin rojo: 0`; rc 0 |
| `abuso2.sh c193af5d` con `PG_URL` | `BASE \| en verde`; 20 `ROJO`; `fallas: 0`; rc 0 |
| `ROTO`, `VERDE \|` o `ROJO?` en los tres logs | ninguno |
| el chequeo de links, aislado | `reset3.sh`: `ROJO \| el tope corta después de crear el link: … [reset] … «el cuarto pedido de la hora creó un link»` |
| `chequeo-6.py 00ac6b29 c193af5d` | producto +0/−0; arnés +27/−41; historia vacío; avisos: 0 |
| `anclas_perdidas.py` en `c193af5d` y en la unión, filtrado por `abuso\|reset3` | nada |
| nombres viejos de los dos casos fuera de las actas y los canales | ninguno |

**Diferencias con el informe, explicadas.** `reset3.sh` dio 8 `ROJO` y no
7 + `SALTO`, y `abuso2.sh` dio 20 y no 19 + `SIN PG`. Las dos diferencias
vienen de que corrí con `PG_URL`: los sabotajes de Postgres que ella no
midió también dan rojo («el tope de recuperar va por el texto en minúsculas
de Python»).

## Negativos míos (otros bordes, mismo caso)

| mutación en `main.py` | rojo |
|---|---|
| N1: la clave de reset va por el texto del email (`reset-cuenta:{request.email}`) | `[reset]` «el cuarto pedido de la hora mandó el mail» |
| N2: lo mismo en recuperar | `[recuperar]`, mismo texto |
| N3: ventana de 3000 s en `_tope_por_cuenta` | los dos: «a los 59 minutos ya mandó otro» |
| N4: tope `> 4` en `_tope_por_cuenta` | los dos: «el cuarto pedido de la hora mandó el mail» |

N1 y N2 los ve sólo el caso nuevo con variantes. El caso de reset de antes
mandaba 4 pedidos que no eran todos iguales, pero no comprobaba los 3 mails
antes del cuarto. Su supuesto reversible de que la rama de reset ahora
controla más queda aceptado: el control es más estricto, no más flojo.

## La premisa de la tarea siguiente (`test_datos1.py`, dos operaciones)

En `delete_cliente`, cambié los dos `.in_([o.id for o in operaciones])` (el
presupuesto público y los ítems) por `[:1]`, sólo la primera operación.
`tests/test_datos1.py` da `11 passed`: hoy nada ve que se borre sólo lo de
la primera. La línea de la cola está vigente.

## Lo que no corrí

La suite completa, `e2e_maria.sh` y los adversarios: la entrega es sólo
tests de un archivo, producto +0/−0, y la tarea no los pedía.
