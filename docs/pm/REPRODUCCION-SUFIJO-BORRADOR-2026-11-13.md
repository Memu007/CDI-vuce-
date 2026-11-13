# Reproducción de SUFIJO-BORRADOR (2026-11-13)

Entrega de MARIA: base `9ed8b9a`, entregado en `ee2ee3c`, informe `765db40`.
Producto: `finalize.js` pinta en el campo el sufijo guardado al entrar a
«Validación» y lo guarda al escribirlo. Revisado por la PM principal en
worktrees en `ee2ee3c`. Veredicto: **devolución por la causa** (abajo).

| qué | salida |
|---|---|
| `chequeo-6.py 9ed8b9a ee2ee3c` | producto +14/−4, arnés +173/−135, historia vacía, 1 AVISO (la envoltura anónima de `finalize.js:9`, 1476 → 1486): igual que el informe; la explicación alcanza |
| `pantalla_sufijo_borrador1.js` con el `finalize.js` de `9ed8b9a` (commit descartable `ed8b57ce`; es el único archivo de producto que cambia) | rojo: las 3 `FALLA` del informe, idénticas |
| la misma pantalla sobre `ee2ee3c` | 3 OK y `PANTALLA SUFIJO-BORRADOR OK` |
| `e2e_maria.sh` sobre `ee2ee3c` y sobre la unión `76193061` (mi rama `64106289` + `ee2ee3c`, merge limpio) | `E2E MARIA OK…`, rc=0 en las dos |
| `sabotaje_valor1.sh ee2ee3c`, con el guion del árbol de `ee2ee3c` | `OK: los 32 sabotajes dan rojo por la razón esperada`, rc=0. La primera corrida, la del «17 de 32» que figuraba acá, usó por error el guion de mi rama, que tiene 29 (`OK: los 29…`); no cuenta. Entre `b35d3cb8` y `ee2ee3c` cambian sólo dos guiones: este y `pantalla_sufijo_borrador1.js`, que corrió desde el árbol de la entrega |
| pytest entero sobre la unión `76193061` | `6126 passed, 110 skipped, 3 xfailed, 109 warnings in 1190.02s`, rc=0; 0 «dejó» |

**Negativos de la PM** (guiones propios fuera del repositorio, datos
inventados). A = operación con `AA(000123)` escrito en el campo; después
«Nueva operación» y B (`OTRA-0002`, sin sufijo). B se carga con
`CDI.state.operacion = …` y `goTo`, como el guion de MARIA: no hay botón de
simular en la plantilla.

| recorrido | base (`ed8b57ce`) | entrega (`ee2ee3c`) |
|---|---|---|
| recargar, recuperar A, B | A: campo «», B: campo «» | A: campo `AA(000123)`; **B: campo `AA(000123)`, operación «»** |
| sin recargar, B, «Generar» (mismo perfil) | **ya pasaba:** B muestra `AA(000123)` y el TXT de `OTRA-0002` sale con `CSBTSVL=AA(000123)` (D236) | igual |
| recargar, recuperar A, B, «Generar» (perfil con CUIT `20111111112`) | frena: «Ingresá el sufijo de valor SBT. Es obligatorio.»; sólo sale `/generate_maria/avisos` con `""` | **`/generate_maria` 200, `MARIA_FAC_OTRA-0002_….TXT` con `CSBTSVL=AA(000123)`**; los avisos se pidieron con `""` |

Sin CUIT en el perfil la misma corrida da 400 por el CUIT del despachante:
el sufijo de A ya había pasado el control de la pantalla.
Nada en `static/` vacía `#sbtSufijoValor` (`grep -rn sbtSufijoValor` y
`sbtInput`: sólo lo leen `finalize.js:681` y `despachante.js:256`), así que
la subida real deja el campo igual que el atajo.

**Lo que esto cambia.** El defecto ya existía sin recargar y MARIA lo
declaró como D236. Con la entrega se suma un camino: recuperar un borrador con sufijo y empezar otra operación genera el
TXT de la nueva con el sufijo de la anterior, sin que nadie lo escriba, y
los avisos de esa pantalla se calcularon con otro valor. Es la causa de
D236: `pintarSufijo` sólo pinta cuando la operación tiene sufijo («Sin uno
guardado queda lo que tiene»). La herencia no está escrita en `CHANGELOG`,
`PREGUNTAS-DESPACHANTE` ni `DECISIONS`: es accidental.

**D237** (carrera de z22 en `orden1`): leída la causa y su forzado sobre la
base en el informe; no lo reproduje. `pantalla_orden1.js` es de MARIA
(«Archivos abiertos» de `NOW.md`).

No corrido: `smoke_friccion`, `ataque_aislamiento`, Firefox y WebKit,
Postgres, adversarios (pieza sin dinero, sesión ni permisos).
