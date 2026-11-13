# Reproducción de ABUSO-2 (2026-11-07)

PM principal. Rama `claude/dev-maria`, pruebas `8ad47ee`, informe `8b14d07`,
base `ccf0f65`.

**Veredicto: devolución sólo de pruebas.** El producto se comporta como dice
el informe, pero dos cambios de `descontar` que perdonan lo que no
corresponde dejan todas las pruebas en verde.

## Lo que coincide con el informe

| Qué | Salida |
|---|---|
| `chequeo-6.py ccf0f65 8ad47ee` | `producto +35/−24`, `avisos: 0` |
| `test_abuso2.py` + `test_abuso1.py` | `83 passed` |
| `sabotajes/abuso2.sh 8ad47ee`, Postgres 55462 | `BASE` en verde, 9 `ROJO`, `fallas: 0` |

## Mutaciones que ninguna prueba ve (reproducidas por la PM)

Árbol aparte en `8ad47ee`, un cambio por vez en
`proyecto_maria/core/limites_auth.py`, `descontar`; pruebas
`test_abuso2.py` y `test_abuso1.py`:

| | Cambio | Salida | Qué deja pasar |
|---|---|---|---|
| M2 | `update(_T).values(...)` sin `where clave == clave` | `83 passed` | un login correcto resta de **todas** las filas: otras IPs, `recuperar:*`, `registro:*`, cuentas ajenas |
| M5 | `select` de la fila propia en vez de `delete … returning` | `83 passed` | cada login correcto repetido vuelve a restar lo mismo y borra fallos ajenos |

Del adversario Sonnet alto, no reproducidas por la PM: olvidar la cuenta a
las 48 h en vez de 24 (M8b), no purgar lo vencido antes de restar (M1) y la
IP con otra ventana que la cuenta (M15) también quedan en verde.

## Adversarios

**Opus alto** (producto): sin perdón de fallos ajenos, sin choque de claves,
SQLite y Postgres iguales, sin enumeración por el cuerpo. Dos bajos:
1. Con cuentas duplicadas por mayúsculas del email (`Dup@` y `dup@`, sólo
   datos viejos), recuperar manda 3 mails por cuenta (6 en vez de 3). Lo trae
   esta pieza (`main.py:1853`). Riesgo.
2. El tope de recuperar es de ventana fija (`limites_auth.py:92-100`). De
   antes. Riesgo.

**Sonnet alto** (mutaciones): 17, 10 en rojo. De las 7 verdes, M2 y M5 son
devolución; M8b, M1 y M15 entran en la misma familia; M7 sólo perdona menos
y M14 es equivalente al código.

## No corrido por la PM

- Suite completa: la corrió la Dev (`5107 passed`). Para una devolución de
  pruebas no hace falta; se corre sobre la vuelta.
- M1, M8b y M15 a mano.

## Vuelta: aceptada sobre `1f79a8e` (sólo pruebas)

| Qué | Resultado PM |
|---|---|
| chequeo-6 `0c4893b..1f79a8e` | producto +0/−0, arnés +86/−9, avisos 0: igual que el informe |
| `test_abuso2.py` + `test_abuso1.py` | `90 passed` |
| `abuso2.sh 1f79a8e` (con `PG_URL`) | 20 ROJO (también el de Postgres), `fallas: 0` |
| Mi ejemplo distinto: `descontar` resta `n − 1` | `7 failed, 83 passed`: lo ve |
| Mi ejemplo distinto: el `delete` de lo propio por prefijo (`like propia%`) | `90 passed`: no lo ve |

La segunda queda como **riesgo**, no devolución: hoy la clave se compara
por igualdad y no hay camino que la vuelva prefijo; un `delete` sin `where`
(lo ancho de verdad) sí cae en `test_un_login_correcto_no_cambia_otras_claves`.
Lo cerraría una clave ajena que empiece igual (`cuenta:{propia}:login:{real}9`).

Primera corrida mía de `abuso2.sh` sin `PY` ni Postgres prendido: base en
rojo y luego Postgres rechazado. Error mío de entorno, no de la pieza.

No corrido por la PM: suite completa (cambio sólo de pruebas; la Dev la
corrió sobre `8ad47ee`).
