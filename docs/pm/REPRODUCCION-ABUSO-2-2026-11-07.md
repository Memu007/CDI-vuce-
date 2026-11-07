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
