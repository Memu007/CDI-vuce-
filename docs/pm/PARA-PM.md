# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ORDEN-1, vuelta 3: entregada en `f7fbb72` (informe en el commit de arriba)

**Resultado.** Está todo lo que pidió tu devolución del 2026-10-29 01:00
UTC. Cada caso tiene su rojo antes y su sabotaje:

- la familia «la sesión cambia en la espera» (z9 a z12);
- los cuatro sabotajes que faltaban (z17, z18 dos veces y z19);
- la pestaña tocada sin puntero (z13 a z16);
- la línea del `CHANGELOG` sobre los 10 s.

Corrieron las puertas que pediste para esta vuelta, todas en verde:
`/code-review high`, `/security-review`, la suite completa, la pantalla, el
smoke y el ataque de aislamiento, sobre `92bbaa2`. La pantalla completa y
los 76 sabotajes corrieron también sobre `f7fbb72`, el SHA que entrego. Los
commits que siguen a `92bbaa2` no tocan el producto: `7b20882` sólo cambia
el `CHANGELOG`, y `f7fbb72`, la pantalla y `orden1.sh`. El producto que
entrego es el de `92bbaa2`.

**Un rojo intermitente, diagnosticado.** En la corrida completa sobre
`92bbaa2`, el sabotaje de z8 dio rojo, pero por el aviso y no por el
guardado a nombre del otro (`ROJO?`, «sabotajes sin rojo: 1»). Lo corrí
aislado tres veces sobre `92bbaa2`: las tres dieron el rojo esperado. La
causa era una espera fija de 3 s en z8. Con ese sabotaje, guardar a nombre
del otro lleva un guardado periódico más la consulta de la sesión nueva, y
a veces no entraba. `f7fbb72` cambia esa espera por la de una condición:
que aparezca el aviso o que haya un guardado a nombre del otro, con tope de
10 s. Sobre `f7fbb72` dio el rojo esperado tres de tres veces aislado, y en
la corrida completa.

Tu devolución de COBRO-MP-1 (causas a a g) llegó: la hago después de esta
vuelta, como pediste. Este informe reemplaza el cuerpo del de COBRO-MP-1
(`0a8a87a`).

### Decisiones

Sigo tu numeración: D8 a D10 fueron de COBRO-MP-1. Tu devolución de
COBRO-MP-1 nombra una D11 posible para la c; si hace falta, va como D13.

- **D11. La duplicada queda en la pantalla de carga si A vuelve a entrar
  mientras ella espera.** Es el caso z12. La pestaña duplicada no adopta
  nada, porque la sesión cambió, y se queda en upload sin reintentar ni
  avisar. La operación de A sigue guardada a su nombre: otra pestaña o una
  recarga la recuperan (lo comprueba z12). Pasa sólo si A vuelve a entrar
  dentro de los 1,5 s en que la duplicada mira si la original vive.
  - (a) Riesgo aceptado, sin cambio.
  - (b) Que la duplicada vuelva a buscar cuando confirma la sesión, en esta
    pieza.
  - (c) Lo mismo que (b), como pieza aparte.

  Recomiendo (a): no se pierde nada y la ventana es chica. (b) agrega otro
  camino de recuperación tardía, que es justo donde estuvieron los defectos
  de las tres vueltas.
  Salió de `/code-review high` (hallazgos 1 y 2).
- **D12. Con «Entró otro usuario», la pestaña de A sigue mostrando la
  operación de A.** `sesionAjena` deja de guardar y avisa, pero no limpia
  `CDI.state` (`app_v2.js:339`, `:966-968`). Si B entra en otra pestaña y
  vuelve a la de A, ve los ítems de A, y lo que haga desde ahí sale con la
  cookie de B. Es anterior a esta vuelta, lo encontró el adversario Sonnet
  alto por lectura y no lo reproduje.
  - (a) Pieza aparte, después de esta tanda: con `sesionAjena`, la pestaña
    tapa la operación y ofrece recargar.
  - (b) Dentro de ORDEN-1 ahora.
  - (c) Riesgo aceptado.

  Recomiendo (a): el servidor ya filtra por usuario, así que B no lee nada
  de A que no esté en esa pantalla. Lo que queda es qué muestra el
  navegador, y eso merece su propio caso y su sabotaje, no un agregado a
  una vuelta que ya va por la tercera.

### SHAs (sobre `40e5a63`)

| SHA | Qué es |
|---|---|
| `2dc1bd8` | test: casos z9 a z19 |
| `90afdaf` | test: z9 a z12 preparan bien la operación de A y esperan el tablero |
| `e4ddcd5` | fix: la duplicada no adopta si la sesión cambió; `'click'` cuenta como tocar; `CHANGELOG` |
| `76947b4` | test: la duplicada retiene su lock; z12 espera la sesión confirmada |
| `4389f89` | refactor: `adoptarBorrador` mira sólo si hay usuario confirmado |
| `92bbaa2` | test: sabotajes de z9 a z19 |
| `7b20882` | docs: la línea del `CHANGELOG` sobre los 10 s |
| `f7fbb72` | test: z8 espera una condición en vez de 3 s fijos; sabotaje de z12 |
| (arriba) | docs: este informe |

### Qué pidió la devolución y cómo queda

**La familia de la sesión que cambia en la espera.** `adoptarBorrador` toma
`usuarioActual()` justo antes de escribir. Si la sesión cambió desde que se
buscó el borrador, eso da `null` hasta que `/auth/current_user` la confirme,
y entonces no escribe ni borra nada. Nunca escribe un sobre sin usuario.

| Caso | Qué pasa en la espera | Qué comprueba |
|---|---|---|
| z9 | entra B, al abrir | B no ve la operación de A, y la de A sigue a su nombre |
| z10 | entra B, con el usuario tarde | lo mismo, por la recuperación tardía |
| z11 | se cierra la sesión | la operación de A sigue guardada con su dueño |
| z12 | A vuelve a entrar con otra sesión | no se pierde: la toma la duplicada o la recupera otra pestaña |

**Sabotajes que faltaban.**

| Caso | Sabotaje | Rojo |
|---|---|---|
| z17 | sin `sesionRevisada = sesion;` | «FALLA: con la sesión cerrada la pestaña pregunta quién es en cada guardado» |
| z18 | sin el freno de `revisarDesde` | «FALLA: con la red cortada la pestaña pregunta quién es en cada guardado» |
| z18 | sin `sesionRevisada = null;` en el `catch` | «FALLA: la red volvió y en 15 s la pestaña no vuelve a guardar» |
| z19 | sin la línea que no deja pisar el aviso `'ajena'` | «FALLA: entró otro usuario antes de la primera consulta y la pestaña avisa otra cosa» |

**Pestaña tocada.** Agregué `'click'` a los eventos. z13 a z16 tocan la
pestaña de cuatro formas distintas antes de que llegue el usuario: un
`click()` programático, Tab, soltar un archivo y `mouse.down`. Cada
sabotaje saca un solo evento y da su propio rojo.

**Supuestos aceptados.** «Cualquier toque desactiva la recuperación
tardía», `ESPERA_USUARIO_MS` de 4 s y `ESPERA_SESION_MS` de 10 s. No cambié
ninguno.

**`CHANGELOG`.** Tiene la línea nueva: «Si la consulta de quién es el
usuario tarda más de 10 s, la pestaña no guarda la operación y lo avisa;
vuelve a guardar cuando la consulta contesta.» Lo cumple el código:
`revisarSesion` corta a los 10 s; el `catch` deja `sesionRevisada = null`,
espera 10 s antes de volver a preguntar y avisa; `confirmarSesion` saca ese
aviso y la pestaña vuelve a guardar. Lo prueban z18 y sus dos sabotajes.

### Cómo se vio en rojo

Los textos están copiados de los mensajes de commit.

Sobre `40e5a63`, según `2dc1bd8`:

- z9 a z12: «…quedó con otro dueño o se borró: []». **Ese rojo no servía.**
  Venía de la preparación, no del producto: la pestaña abierta tomaba
  OP-DE-A ya cerrada y la pisaba. Lo corrige `90afdaf`.
- z13: «FALLA: se tocó la pestaña (un clic sin puntero) antes de que llegara
  el usuario y la recuperación tardía la cambió a review».

Sobre `2dc1bd8`, con la preparación corregida y el producto sin arreglo,
según `90afdaf`:

- z9: «FALLA: entró otro usuario mientras la duplicada miraba si la original
  vive, al abrir y la pestaña le muestra a ord1z9b_… la operación de A:
  OP-DE-A». z10 da lo mismo «con el usuario tarde».
- z11: «FALLA: se cerró la sesión mientras la duplicada miraba si la
  original vive y la operación que A dejó guardada quedó con otro dueño o se
  borró: [null]».
- z13: el mismo rojo de arriba.
- z12 pasa sobre la base: guarda la operación sin dueño y, al confirmar la
  sesión, otra vez a nombre de A. Queda como caso de regresión, con su
  sabotaje en `f7fbb72`.

Hubo además un defecto del arnés que tapaba el rojo de z11: el 401 de los
conectores del tablero mandaba la pestaña al login antes de que terminara
de mirar. Ahora la sesión cambia recién cuando la duplicada recibió esos
conectores.

Sobre `e4ddcd5`, según `76947b4`: «FALLA: la pestaña duplicada no retiene el
lock de su propio id». Era el arnés: el reemplazo de `navigator.locks.request`
pasaba un argumento de más y Chromium rechazaba la llamada.

### Puertas

| Puerta | SHA | Salida |
|---|---|---|
| Suite completa | `92bbaa2` | «4283 passed, 121 skipped, 3 xfailed, 102 warnings in 608.21s (0:10:08)», rc=0 |
| `compileall` | `92bbaa2` | rc=0 |
| `node --check app_v2.js` | `92bbaa2` | sin salida, rc=0 |
| Pantalla completa (`pantalla_orden1.js`) | `92bbaa2` | 49 líneas `OK`, la última «OK: ORDEN-1 en el navegador», rc=0 |
| Smoke | `92bbaa2` | «==> OK · telemetría + alias session/state + by-cuit protegido», rc=0 |
| Ataque de aislamiento | `92bbaa2` | «Bloqueado: 47 · Fugas: 0 · Sin probar: 0», «PUERTA G3 PASADA», rc=0 |
| Sabotajes (`orden1.sh`, 75) | `92bbaa2` | 74 `ROJO`; z8 `ROJO?` («…y la pestaña no avisa: «»»); «sabotajes sin rojo: 1», rc=1. Diagnóstico arriba |
| z8 aislado, 3 veces | `92bbaa2` | 3 `ROJO` con «…lo cargado se guardó a nombre de él» |
| Pantalla completa | `f7fbb72` | 49 líneas `OK`, la última «OK: ORDEN-1 en el navegador», rc=0 |
| z8 aislado 3 veces y z12 | `f7fbb72` | 4 `ROJO` con su texto; z12: «FALLA: A volvió a entrar (otra sesión) mientras la duplicada miraba si la original vive y la duplicada no confirma la sesión nueva en 15 s» |
| Sabotajes (`orden1.sh`, 76) | `f7fbb72` | 76 líneas `ROJO  |`, ninguna VERDE, ROTO ni `ROJO?`; z8: «…lo cargado se guardó a nombre de él»; «sabotajes sin rojo: 0», rc=0 |

La suite deja el aviso «Task was destroyed but it is pending …
async_generator_athrow», que es anterior a esta pieza.

### Revisiones

| Revisión | Modelo y esfuerzo | Hallazgo | Qué hice |
|---|---|---|---|
| `/security-review` | el de la sesión | sin hallazgos | — |
| `/code-review high` | el de la sesión | 1 y 2: z12 queda en upload sin reintento ni aviso | D11 |
| `/code-review high` | el de la sesión | 5: limpieza del arnés (`enTablero`, código duplicado, `waitForTimeout` viejos) | riesgo bajo |
| Adversario | Sonnet, alto | media, anterior: `CDI.state` no se limpia con `sesionAjena` | D12 |
| Adversario | Sonnet, alto | baja: z12 no tenía sabotaje | agregado en `f7fbb72` |
| Adversario | Sonnet, alto | baja: la adopción con la original muerta no se prueba junto con el cambio de sesión | riesgo |

El adversario corrió z9 a z12 sobre `92bbaa2` (OK) y los 11 sabotajes
nuevos (11 ROJO). Midió los tiempos de z10: «SEGUIR 10439», «TABLERO
10453», «ADOPT 11514». La adopción defectuosa llega 1 s después del
usuario, y el caso espera 5 s desde que la pestaña muestra algo, así que el
margen alcanza.

### Riesgos

- **D11** (z12 en upload) y **D12** (`CDI.state` con `sesionAjena`).
- **La adopción con la original muerta** no se prueba junto con el cambio de
  sesión: en z9 a z12 la original sigue viva. Las dos ramas llaman al mismo
  `adoptarBorrador`. Baja.
- **A2:** si el mismo usuario sale y vuelve a entrar con la primera consulta
  en camino, ve «Entró otro usuario». No guarda y avisa, del lado seguro.
- **`/logout` no rota el CSRF.**
- **El bfcache está simulado** en la prueba.
- **`subiendo--`** y **el aviso `lleno`**, que se va sin prueba.
- **Limpieza del arnés** (`/code-review` 5): `enTablero`, código repetido
  entre casos y algunos `waitForTimeout` de vueltas anteriores. Baja: no
  cambia qué distingue cada caso.

### Archivos de producto

`proyecto_maria/static/v2/app_v2.js` y `CHANGELOG.md`.

### Comandos

```bash
git fetch origin claude/dev-tecnica && git checkout f7fbb72
git diff 40e5a63..92bbaa2 -- proyecto_maria/
#   sólo app_v2.js: 'click' en pestanaTocada y usuarioActual() antes de escribir en adoptarBorrador
git diff 92bbaa2..f7fbb72 --stat -- . ':!docs/pm'
#   sólo CHANGELOG.md, scripts/testing/pantalla_orden1.js y scripts/testing/sabotajes/orden1.sh
PY=$PM_DIR/venv/bin/python PUERTO=8871 bash scripts/testing/sabotajes/orden1.sh f7fbb72
#   76 líneas «ROJO  |», ninguna VERDE, ROTO ni ROJO?; al final «sabotajes sin rojo: 0»
```

/compact conservar: Dev 1, rama claude/dev-tecnica. ORDEN-1 vuelta 3
entregada (producto 92bbaa2, pruebas f7fbb72), espera veredicto con D11 y
D12. Sigue COBRO-MP-1 vuelta 2 (devolución en PARA-DEV.md, causas a a g);
después CORTE-1, MP-2 (suma la cancelación de organizaciones), AIS2, LIM,
BACKUP-1a y EXCEL-2c. Nada se publica sin el «dale» de Emi; nunca main.
