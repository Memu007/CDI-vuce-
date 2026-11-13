# Reproducción de AUTOREMOVE-PG (2026-11-12)

Entrega de la Dev técnica: código `6d370864`, informe `ed78ad48`, base `24788cf0`.
Sólo arnés (`scripts/testing/org1_postgres.py` +26, `org1.sh` +1/−1). Revisado
por la PM principal en un worktree aparte, sobre `6d370864`.

## Lo reproducido

| qué | salida |
|---|---|
| `chequeo-6.py 24788cf0 6d370864` | producto +0/−0, arnés +27/−1, historia vacía, avisos: 0 (igual al informe) |
| `anclas_perdidas.py 6d370864 \| grep -c org1` | `0` |
| lo que trae el merge, fuera de `docs/pm` | sólo esos dos archivos |
| `org1.sh 6d370864` entero con `PG=` (Postgres 16 local) | BASE verde en SQLite y en Postgres; 40 ROJO (28 en SQLite, 12 en Postgres); ninguna línea VERDE ni `ROJO?`; `sabotajes sin rojo: 0`; `salida 0`; de 20:34:15 a 21:01:13 UTC. «el dueño se saca a sí mismo» da ROJO en las dos bases |

Mercado Pago no se llama de verdad: el dueño recibe un `mp_preapproval_id`
puesto por el guion y `_leer_suscripcion_mp` y `_cancelar_suscripcion_mp` se
reemplazan por funciones que anotan; se restauran en un `finally`. Después de
ese bloque `org1_postgres.py` sólo registra usuarios: el id de mentira del dueño
no llega a ninguna llamada real.

## Mis mutaciones, en una copia de `org1_postgres.py`, base nueva cada una

| mutación de `remove_member` | rc | lo que ve el caso | otras FALLA |
|---|---|---|---|
| ninguna | 0 | OK: 400 exacto, variantes 404, base igual, lista vacía | 0 |
| guarda después del `commit` | 1 | variantes 400 «No pertenecés a un estudio», base distinta, leer y cancelar | 0 |
| guarda después de Mercado Pago | 1 | respuestas y base iguales; sólo la lista (leer, cancelar) lo ve | 0 |
| búsqueda con `lower()` | 1 | la variante en mayúsculas da 200, base distinta, Mercado Pago llamado | 0 |
| búsqueda con `strip()` | 1 | la variante con espacio adelante da 200, base distinta, Mercado Pago llamado | 0 |

La de Mercado Pago es la que justifica la lista de llamadas: sin ella, el caso
quedaba verde.

## Corrección de mi acta anterior

`REPRODUCCION-AUTOREMOVE-2026-11-12.md` y el veredicto decían «39 ROJO (29 en
SQLite, 10 en Postgres)». Lo correcto es **28 en SQLite y 11 en Postgres**.
Conté la línea BASE como un rojo, y «la regla 2 despierta a las marcadas
vencidas» no tiene rojo en SQLite a propósito. La Dev lo marcó en su informe;
tenía razón. Corregido en esa acta.

## No corrí

- Los otros tres sabotajes del dueño (guarda después de Mercado Pago, `lower`,
  `trim`) siguen sin tercer argumento en `org1.sh`: corren sólo en SQLite. En
  Postgres los vi rojos a mano (tabla de arriba), no por el guion. Riesgo bajo,
  no devolución: la tarea pedía uno.
- La suite entera: producto +0/−0.
- Adversarios: sólo arnés.

## Escape

El conteo 29/10 de la revisión anterior (arriba). Lo marcó la Dev, no yo.
