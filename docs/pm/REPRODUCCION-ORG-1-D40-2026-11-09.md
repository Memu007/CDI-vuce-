# Reproducción ORG-1 + D40, vuelta sobre `bf9583b` (2026-11-09, PM)

Base `db9f11f`. Worktree en `bf9583b6`, Postgres 16 local en el 55462.

| Qué | Informe | PM |
|---|---|---|
| `chequeo-6.py db9f11f bf9583b` | +8/−3, 1 aviso (`register` 218 → 219) | igual |
| `sabotajes/org1.sh bf9583b6` con PG | BASE verde, 35 ROJO, sin rojo 0 | `BASE \| verde … (SQLite y Postgres)`, 35 `ROJO`, `sabotajes sin rojo: 0`, `salida 0` |
| `tests/test_org1.py` | 86 passed | 86 passed (corrida del adversario) |
| `org1_postgres.py` en una base nueva | `fallas: 0` | `fallas: 0` (adversario, base `adv_a`, borrada) |
| negativo PM: invitada en mayúsculas + cuenta en minúsculas; invitar al dueño de otro estudio en mayúsculas | — | `2 passed` sobre `bf9583b`; con `main.py` de `db9f11f`: `1 failed, 1 passed` (el de mayúsculas) |

## Adversario (Sonnet, alto, contexto nuevo)

- Media-baja, reproducida en SQLite: con tope 3, X pendiente se registra sin
  link, el dueño invita a Y, X cambia el email del perfil y entra con el link
  viejo con otro usuario, Z entra; Y recibe 400 «El estudio ya tiene los 3
  usuarios de su plan» y no hay cómo revocar. El tope no se supera. Riesgo,
  a Emi con R3 (email del perfil sin verificar) y revocar invitaciones.
- Sin hallazgo: zona horaria (columna con zona, `nullable=False`), vencidas
  por estado y por fecha, mayúsculas y espacios, concurrencia del arnés de PG.
- Fuera del diff: una invitación a un email mal escrito ocupa lugar 7 días.

Veredicto: aceptada. D151 (a). Partir `register` a `COLA-LIMPIEZA.md`.
