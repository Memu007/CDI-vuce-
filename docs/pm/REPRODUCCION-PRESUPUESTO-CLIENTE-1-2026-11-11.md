# PRESUPUESTO-CLIENTE-1, reentrega sobre la unión: `f45243a`

Base `64c39e9` (cabeza de la PM). Dev MARIA, informe `d49a436`
(`PARA-PM-2.md`). Worktree `/tmp/cdi-pm/wt-pc1`, venv de PM, SQLite de las
pruebas y Postgres 16 local (127.0.0.1:55462, rol `cdi`, bases nuevas
`pm_pc1` y `pm_pc1_rev`).

## Lo del informe, reproducido

| Qué | Salida |
|---|---|
| `tests/test_datos1.py` sobre `f45243a` | `11 passed`, exit=0 |
| el mismo archivo con la llamada cambiada por `pass` (receta del informe) | `FAILED …test_pasar_la_operacion_a_otro_cliente_borra_su_presupuesto`, `FAILED …test_borrar_el_cliente_anterior_no_deja_el_link_de_la_operacion_pasada`, `2 failed, 9 passed` |
| `datos1_postgres.py` sobre `f45243a`, base `pm_pc1` | once `OK`, `fallas: 0`, exit=0 |
| el arnés PG con la llamada cambiada por `pass`, base `pm_pc1_rev` | nueve `OK`, `FALLA \| guardada en otro cliente, la operación pierde su link (200)`, `FALLA \| borrar el cliente anterior no la toca ni devuelve el link (200)`, `fallas: 2`, exit=1 |
| chequeo-6 de la pieza sola (receta del informe, sobre `64c39e9`) | `producto +10/−0`, `arnés +200/−24`, historia vacío, `avisos: 1` (`save_client_operation` 152 → 153): igual al informe |
| `scripts/testing/e2e_maria.sh` sobre `f45243a` | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.`, exit=0 |
| `sabotajes/datos1.sh f45243a` | 20 líneas `ROJO`, `sabotajes sin rojo: 0`, exit=0 |

El AVISO queda: la rama nueva vive en su propia función y la función larga
sólo suma la llamada. Partir `save_client_operation` no estaba en la cola de
limpieza; lo sumo yo en este commit.

## Lo que entra con ésta

Comprobado con código y por rango, no con los nombres. «Ancestro de un SHA
aceptado» no alcanza: `e81b961` (CATALOGO-3) y `5dd9a6eb`
(PRUEBA-LIMPIAR-1) son puntas de la rama que ya contienen commits de esta
pieza. Los 32 commits de
`git rev-list 64c39e9..f45243a -- proyecto_maria requirements.txt`, por
rango:

| Commits | Pieza aceptada | Cómo cae |
|---|---|---|
| `3d0083a0`, `1a02fc20`, `e1874661` | RESET-3 | ancestros de `8fda3d2` |
| `ffd1b95e`, `9cfe87c3` | AVISOS-2b | ancestros de `aa115f4` |
| `df597561`, `42dd9a64` | OBSERVABILIDAD-1 | ancestros de `279ef26` |
| `1095f5c4`, `e9e6153e` | ORG-1 | ancestros de `bf9583b` |
| `43ac587c` | D139 | ancestro de `3fde8bb` |
| `a7bc85a6` (bcrypt) | D102 | la primera aceptada que lo tiene es `af924ea` |
| 15, de `6cbd192d` a `1dca33e0` | CATALOGO-3 | en `07504e0..e81b961` (sin `de176b17` ni `db0f25a4`), asuntos de catálogo, origen, memoria y unidades |
| `de176b17`, `db0f25a4`, `4d30e9cc`, `a9fb87fe` | ésta | aceptada sobre `f45243a`; los dos primeros también caen en el rango de CATALOGO-3 |
| `d497551a` | arreglo SIM de MEMORIA-E2E | citado en su acta; `git diff d2f7f9c f45243a` no tiene «posici» |
| `2b59f396` | merge | ver abajo |

Suman 32 (3+2+2+2+1+1+15+4+1+1). Para listarlos con su rango:
`for c in $(git rev-list 64c39e9..f45243a -- proyecto_maria requirements.txt); do git log -1 --format='%h %s' $c; done`.
PRUEBA-LIMPIAR-1 no suma producto: `git diff c033db7 5dd9a6eb -- proyecto_maria`
da vacío.

`git show --remerge-diff` de los 10 merges: sólo `2b59f396` resolvió
conflictos, y las combinaciones son correctas (`_soltar_link_de_otro_cliente`
junto a las funciones nuevas de la unión; la llamada dentro del
`if operation is not None:` del camino por `operacion_id`; el comentario de
`invite_to_organization` con `plan_de_la_cuenta`; `saveCatalogLearn(items,
carga)` en `finalize.js` con un solo llamador). El AVISO de `register`
209 → 210 que da el chequeo-6 de la unión viene de ORG-1+D40 y está en su
acta.

Integrado en mi rama con `merge --no-ff`: `8669b43`.
`git diff f45243a 8669b43 -- . ':!docs/pm' ':!.claude'` da 0 líneas.

## Adversario

Uno, Sonnet esfuerzo alto (tabla: «atacar datos»), sin red, su propio
worktree y su base PG `adv_pc1` (ya borrada). Sin hallazgos atribuibles a la
pieza. Lo que probó y salió bien:

- una operación con dos links pierde los dos al pasar; otra operación del
  mismo cliente y la de otro dueño siguen en 200;
- mismo cliente, o sin cliente (generada por `/generate_maria`) y después
  guardada en uno: el link sigue;
- otro dueño mandando mi `operacion_id`: crea una operación nueva, la mía
  queda intacta; un cliente ajeno como destino da 404 y el link sigue;
- `client_id` en mayúsculas, con espacios o sin guiones: 404 sin tocar nada
  (`_get_owned_client` compara exacto antes de llegar a la función);
- un `commit` que falla, o un 400 por `NaN`: el link sigue (la sesión
  revierte al cerrar);
- dos guardados en paralelo a clientes distintos, 5 rondas: 200/200, sin 500
  ni bloqueo; con `share_quote` en paralelo, 8 rondas: sin 500 (lo que a
  veces queda es D163);
- en `proyecto_maria` el cliente de una operación existente sólo cambia en
  `delete_cliente` y en `save_client_operation`;
- sobre la base `64c39e9` el pase deja el link en 200; sobre `f45243a`, 404.

No probó organizaciones con varios usuarios (`_operacion_del_usuario` filtra
por dueño).

## Mi negativo: un miembro del estudio

Un caso temporal (no va al repo) con un dueño y un miembro de su equipo
(`effective_owner` del miembro = el dueño, `role = member`). El dueño tiene
la operación en su cliente A con un link vivo.

- el miembro guarda esa `operacion_id` en un cliente suyo: 200 con una
  operación **nueva**; la del dueño no cambia;
- el miembro la guarda en el cliente A del dueño: 404;
- el miembro comparte la operación del dueño: 403/404;
- después de todo: el link del dueño sigue en 200, los presupuestos de la
  operación siguen en 1 y su cliente sigue siendo A.

`1 passed`. Los datos de clientes y operaciones son por usuario
(`username`, no `effective_owner`; refactor citado en `main.py:829`), así
que un miembro no llega a soltar ni conservar el link del dueño.

## Lo de la Dev que no corrí

Golden (`115 passed, 2 xfailed`), `ataque_aislamiento`
(`Bloqueado: 47 · Fugas: 0`) y `smoke_friccion` son de la Dev sobre
`f45243a`; no los corrí yo.

## Suite completa, mía

Sobre `f45243a`, en el worktree de la pieza, con `DOLARAPI_BASE` local,
`ENVIRONMENT=testing` y `GEMINI_API_KEY` vacía:
`6077 passed, 110 skipped, 3 xfailed, 102 warnings in 1046.99s (0:17:26)`,
`fin: exit=0`, 0 FAILED.

La Dev, sobre el mismo SHA: `5832 passed, 355 skipped, 3 xfailed`. Mismo
total (6190); la diferencia neta, 245, es `xlwt`: no está en
`requirements.txt` (a propósito, lo dice `tests/test_excel3.py:1148`), mi
venv lo tiene y el de la Dev, por el conteo, no (ella lo confirma al
instalarlo). Con un `xlwt` que no se puede importar
adelante en `PYTHONPATH`, `test_excel3.py` y `test_excel2d.py` dan
`SKIPPED [234] tests/test_excel3.py:1150: could not import 'xlwt'`,
`SKIPPED [11] tests/test_excel2d.py:80: …`, `739 passed, 245 skipped`.
La diferencia vieja (335 contra 101 desde CATALOGO-3, 234) da justo lo de
`test_excel3.py`; no recalculé esas corridas. En mi corrida las 245
corren y pasan.

## Riesgos que quedan

- **D163 (a):** un `share_quote` en vuelo mientras el mismo usuario pasa la
  operación a otro cliente, o borra el cliente (variante 2, reproducida por
  el adversario de la Dev en PG 16), puede dejar un link vivo con los datos
  del cliente anterior. No cruza permisos: lo arma y lo reparte el mismo
  dueño, en dos pestañas a la vez. Si se quiere cerrar, (c).
- **Links ya emitidos en producción** antes de este arreglo, sobre
  operaciones que ya pasaron de cliente: siguen vivos hasta que se publique
  y se borren (no lo hace este arreglo). El GET público no manda
  `Cache-Control`.
- **CR2 (media, de la unión, no de esta pieza):** guardar una operación
  existente con un cuerpo mínimo pisa `source`, `currency`, `total_value` y
  `extra.resumen`. Leído por el `/code-review` de la Dev, no corrido.
- **A2:** `delete_cliente` borrando sólo la primera operación deja
  `test_datos1.py` en verde: hueco de prueba de DATOS-1. A la cola.
- **CR5:** el caso nuevo deja un TXT en `data/descargas`, como otros 45
  archivos de `tests/`. **CR7:** el arnés PG importa `_pedido`. **CR8:**
  tres sabotajes viejos anclan en comentarios: va con D149.

## Decisiones

- **Aceptada sobre `f45243a`, integrada en `8669b43`.** ROADMAP pasa a ✅.
- **D163: (a)**, riesgo bajo sin código, con la variante 2 anotada arriba.
- **D167: decidido por la PM, con el consejero.** No se generaliza: las
  demás sesiones siguen en 200k. A MARIA, los 250k que puso Emi (21:06 UTC)
  le tomaron recién a las 21:36 UTC (umbral 184000). Hasta ahí, con umbral
  144000, compactó a las 21:24, 21:30 y 21:35 UTC: después de cada una
  quedaba en ~150k, ya arriba del umbral. Con 184k el margen es ~33k; si
  vuelve a compactar seguido, la PM se lo pasa a Emi con los números.
- A `COLA-LIMPIEZA.md`: partir `save_client_operation` (AVISO 152 → 153) y
  el caso de A2.
