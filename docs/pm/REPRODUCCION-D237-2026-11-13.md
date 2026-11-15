# D237 (a): reproducción de la PM

Entrega `346a1c9` (informe `73f8db7`, canal `PARA-PM-2.md`). Base `c3eb7cf`.
Veredicto: **aceptada sobre `346a1c9`**. D241 (b), decidida por la PM.

Sólo arnés: `scripts/testing/forzar_avisos_orden1.js` (nuevo, 38 líneas) y
`scripts/testing/pantalla_orden1.js` (+36/−1). Producto sin cambios. La unión con mi
rama (`7104db7f` + `73f8db77`) no difiere de `346a1c9` fuera de `docs/pm`
(`git merge-tree` + `git diff --stat`, vacío).

## Corrido por la PM (2026-11-13, 22:10–22:38 UTC, worktrees descartables)

- `chequeo-6.py c3eb7cf 346a1c9`: igual al informe (producto +0/−0, arnés +73/−1,
  historia vacía, avisos: 0).
- (z22) de `orden1`, sqlite y puerto libre:

| corrida | SHA | rc | lo que muestra |
|---|---|---|---|
| base con su forzador | `c3eb7cf` | 1 | «un pedido de avisos sale 648 ms después de salir»; api.log: `POST /auth/logout 200` → `POST /generate_maria/avisos 401` → `POST /auth/login`; FALLA TypeError del click |
| entrega con su forzador | `346a1c9` | 0 | los 2 avisos y las 2 validaciones con 200 antes del logout; «OK A salió, volvió a entrar y generó enseguida» |
| entrega sin la espera, con su forzador | `776c80f9` (local, `await terminaron(...)` comentado) | 1 | avisos 401 después de salir (884 ms) |
| entrega sin forzador | `346a1c9` | 0 | — |

- `orden1b.sh` sobre `346a1c9`: rc=0, 368 s, 30 ROJO, «sabotajes sin rojo: 0». Los
  dos de z22 («con la sesión cambiada no escribe…», «la comprobación de la sesión
  corta antes…») en ROJO.
- `orden1` entero sobre `346a1c9` con `correr_pantallas.sh`: rc=0, 586 s, 71 OK,
  «resumen: 1 verdes, 0 rojas».

### Mis negativos, no dados a la Dev

Su supuesto 1 dice que la espera cubre también las validaciones de la entrada a
«Validación». Forzador mío igual al suyo pero sobre `**/api/validate/smart`; cada fila es
una corrida (validación demorada / nuevo login demorado):

| demora | base `c3eb7cf` | entrega `346a1c9` |
|---|---|---|
| 1 s / 2 s | rc=0: las dos validaciones terminan antes del logout, **no distingue** | rc=0 |
| 3 s / 5 s | rc=1: `POST /auth/logout 200` → `POST /api/validate/smart 401`, 125 ms después de salir (el mensaje del forzador dice «avisos» porque es copia del suyo; el pedido es la validación) | rc=0: las dos validaciones con 200 antes del logout |

Con 3 s / 5 s distingue: la espera cubre las validaciones.

Su supuesto 4 (z22 ya no escribe el sufijo): el campo `#sbtSufijoValor` lo siguen
escribiendo `generar()` (casos que generan y leen el TXT, con sus `[SBT]`) y
`listaParaGenerar()` (z20, z23).

El caso al revés (lo que hace la pestaña cuando le llega el 401): en la base forzada, después
del 401 la pestaña va al login y no sale ningún `POST /generate_maria`; no escribe.

## No corrido por la PM

pytest, `e2e_maria.sh`, `smoke_friccion.sh`, `ataque_aislamiento.sh` y
`/security-review`: la pieza toca sólo arnés y ninguno de esos lo usa. Las otras
pantallas no cambian. `orden1.sh` no corre z22 (sus casos z son de otras letras).

Las corridas fueron en paralelo con la tanda de sabotajes de `7436c6e5` (4 CPU, carga ~1).
ROADMAP: D237 es arreglo del arnés de ORDEN-1b (fila 2b, ya ✅); no suma fila.
