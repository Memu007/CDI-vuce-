# Reproducción de ORG-1 + D40 (2026-10-28)

Entrega de MARIA en `b358827` (informe `5396d1e`; producto `3c2693b`,
pruebas `1ef1d38` y `b358827`, encima de `b9881fb`). Pedido: la D40 y los
cuatro «Sumá» de la aceptación de ORG-1.

## Lo que corrió la PM

- `tests/test_org1.py` + `tests/test_email1.py` sobre `b358827`, SQLite:
  `92 passed`.
- Mutantes de la PM, cada uno restaurado después (`git status` limpio):
  - A: el control de dueño al invitar (`main.py` cerca de la 10089) pasa a
    `if False`, cualquiera invita: `81 passed` en las pruebas de ORG-1.
    Sobrevive.
  - B: sin el filtro por estudio al sacar un miembro (cerca de la 10213):
    `81 passed`. Sobrevive.
  - M2 (del revisor Sonnet): sin `Invitation.status == "pending"` en el
    `UPDATE` del registro (3119), una invitación vencida del mismo email
    pasa a usada: `92 passed`. Sobrevive.
- El lugar muerto (del revisor Opus), dos recorridos sobre la app real con
  `/tmp/cdi-pm/adv-org1d40-o/src/tests/test_adv_d40.py`, `4 passed`:

  A, el invitado se registra sin el link y la invitación queda pendiente:

  ```
  perfil -> 200
  registro del invitado -> 400 Email ya registrado…
  reinvitar -> 400 Ese email ya tiene una cuenta…
  pendientes de p: 1 pending
  cuarto lugar -> 400 El estudio ya ocupa los 3 usuarios…
  registro tras soltar -> 200
  ```

  B, el email ya tiene cuenta y la invitación vieja sigue ocupando lugar:

  ```
  registro con token -> 400 Email ya registrado…
  estado: pending
  reinvitar -> 400 …
  tercer lugar libre? -> 400 …
  ```

  La pendiente de un email que ya tiene cuenta no se puede usar nunca y
  ocupa lugar hasta que el dueño la borra.

## Revisores (contexto nuevo)

- **Opus alto**, Postgres 16 propio, copia limpia con `git archive`:
  confirmó la normalización del email, la carrera en Postgres (0
  pendientes, 1 cuenta), el tope firme en el registro y que el sacado no
  vuelve a entrar (`org1_postgres.py`, `fallas: 0`). Encontró el lugar
  muerto, reproducido por la PM arriba.
- **Sonnet alto**, mutantes:
  - M2 sobrevive (reproducido por la PM arriba).
  - M5 (el `UPDATE` después del commit) sólo lo mata la prueba de carrera.
  - M6 (el `UPDATE` antes del control de tope) sobrevive; es equivalente
    porque el rollback lo deshace.
  - M11 (el control de cuenta después del de tope) sobrevive: con el
    estudio lleno nadie fija qué mensaje sale.
  - `org1.sh`: 7 de 7 en rojo.
  - Caso C: X tiene pendientes en los estudios A y B, se registra con el
    token de A, y la de B sigue pendiente y ocupando lugar (la misma causa
    que el lugar muerto).
  - Menor: invitar dice si un email tiene cuenta, sin límite de pedidos
    (el registro ya lo dice).

## Lo que no se entregó

El «Sumá» 4 de la aceptación de ORG-1 (un caso por guarda, rojo con su
sabotaje): los mutantes A y B lo muestran.

## Veredicto

Devolución sobre `b358827`. Causa: las reglas de la D40 tienen filtros que
ninguna prueba distingue, y el «Sumá» 4 no llegó. El detalle está en
`PARA-DEV-2.md`.
