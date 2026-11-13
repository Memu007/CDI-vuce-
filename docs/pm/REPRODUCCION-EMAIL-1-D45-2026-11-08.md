# Reproducción EMAIL-1 (D45 (1)), 2026-11-08 (PM principal)

Pruebas en `40423be` (rama `claude/dev-maria`), base `3af69c0`. Sin producto.

| qué | resultado |
|---|---|
| `chequeo-6.py 3af69c0 40423be` | producto +0/−0, arnés +48/−6, historia vacío, avisos 0 |
| `email1.sh 40423be` | 15 ROJO, «sabotajes sin rojo: 0», rc=0 |
| PG 16.15 descartable, `C.UTF-8`: `email1_minusculas_pg.py` | default 1 (U+0130), und-x-icu 0, ucs_basic 1407; rc=0 |
| `abuso2_postgres.py` | 6 OK, «fallas: 0», rc=0 (cinco variantes con İ: 3 mandados) |
| `abuso2.sh` con `PG_URL` | 20 ROJO, «fallas: 0», rc=0 |
| leído en el código | `_email_valido` (main.py:331) acepta sólo ASCII; el reset (1783) tiene tope sólo `reset:{ip}` |

Primera corrida, en una base mía en `C`/`SQL_ASCII` (sin querer): `email1_minusculas_pg.py`
cae porque no hay `und-x-icu` en SQL_ASCII, `default` da 1407 y `abuso2_postgres.py`
da fallas 1, porque las cinco variantes con İ mandan 1 mail y no 3. La causa es
la collation de la base, no el código. Por eso D131 va a Emi.

No corridos: suite completa y adversarios, porque el diff es sólo de pruebas.
