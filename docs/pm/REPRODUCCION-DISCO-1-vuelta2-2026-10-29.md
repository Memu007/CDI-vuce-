# Reproducción de DISCO-1, segunda vuelta (2026-10-29)

Entrega de la Dev MARIA: informe en `PARA-PM-2.md` («DISCO-1, vuelta de las
20:58: entregada en `5c46e36`»). Sólo pruebas: `5c46e36` toca
`scripts/testing/disco1_postgres.py` y `scripts/testing/sabotajes/disco1.sh`.
El producto es el de `1f5480e` (DESPACHO-1b, vuelta 3), que queda debajo.

## Lo que corrió la PM, sobre `5c46e36`, Postgres 16 descartable

- `disco1_postgres.py`: «fallas: 0» (igual que el informe).
- `disco1.sh` con `PG_URL`: 46 ROJO, «sabotajes sin rojo: 0» (igual que el
  informe).
- La primera corrida de `disco1.sh` dio 7 «ROJO?»: error de la PM, que pasó
  el rol `postgres` en vez del rol dueño de la base. Con el rol correcto, 46
  ROJO. No es de la pieza.

## Mutantes propios de la PM

Distintos de los de la devolución, sobre una copia de `5c46e36`, con
`disco1_postgres.py`:

| Mutante | Resultado |
|---|---|
| m1: la carga toma el bloqueo con otra clave (el nombre del archivo en vez del dueño) | muere: `FALLA \| la carga del archivo de A espera a la importación de A: terminó`, «fallas: 1» |
| m2: la importación toma el bloqueo después del bucle de tandas, no antes | muere: tres `[200, 500]` por deadlock y la carga de A que no espera, «fallas: 4» |

La prueba ve el lugar del bloqueo y su clave, no sólo que exista una
llamada: la causa de la devolución está cubierta.

## No corrido por la PM

La suite completa (no aplica: `5c46e36` no toca producto ni `tests/`),
`tests/test_disco1.py` aparte (corre dentro de la base de `disco1.sh`),
`/code-review` y `/security-review`.

## Veredicto

Aceptada sobre `5c46e36`. No se integra todavía: `5c46e36` está encima de
`1f5480e`, que vuelve con devolución (`REPRODUCCION-DESPACHO-1b-vuelta2-2026-10-29.md`).
Se integra con el commit que acepte la próxima vuelta de DESPACHO-1b,
después de correr de nuevo `disco1.sh` sobre ese SHA; ahí DISCO-1 pasa a ✅
en `ROADMAP.md`.
