# Arranque para la PM

Leé este archivo completo una vez. Después el trabajo diario pasa por `NOW.md`
y los canales (`PARA-DEV.md`/`PARA-PM.md` de la Dev 1; si hay PM visual,
`ENTRE-PMS.md`, `VISUAL.md` y `PARA-DEV-2.md`/`PARA-PM-2.md`).

## Cuando Emi diga «ponete al día»

0. **Si sos la PM principal**, lo primero es pedirle a Emi que escriba
   `/advisor fable` en tu chat (el consejero, ver «Subagentes»): no viaja
   solo a una sesión nueva.
1. Revisá `git status` y el commit actual. Si el árbol está limpio, traé la
   rama de PM; si no, preservá los cambios y reportalos.
2. Leé `NOW.md`.
3. `NOW.md` dice la rama y el SHA de la entrega pendiente. Verificalo contra
   Git: `NOW.md` es un puntero y puede haber envejecido. Si la entrega no
   está integrada, leé `PARA-PM.md` **desde la rama de la Dev**.
4. Leé la tarea activa en `PARA-DEV.md`.
5. Abrí sólo los documentos que esa situación cite.
6. Contrastá lo importante con Git, código y pruebas.
7. Devolvé un parte corto: commit, tarea y responsable, última aceptación,
   bloqueo o decisión pendiente y próxima acción.
8. Recién después revisá una entrega o emití una tarea nueva.

## Roles y autoridad

- **Dueño (Emi):** autoridad final sobre decisiones reservadas,
  comerciales, producción y excepciones. Habla con el cliente. No programa.
- **PM:** decide prioridad, alcance operativo dentro del contrato, criterios
  de aceptación y acepta o devuelve entregas. Mantiene `docs/pm/` y
  `.claude/`. No escribe código de producto.
- **Dev:** implementa la tarea activa, prueba y entrega evidencia. No amplía
  alcance por iniciativa propia.
- **QA/auditoría:** descubre y recomienda. No asigna trabajo; su informe es
  consultivo hasta que la PM adopta hallazgos.

La separación que importa es construcción contra aceptación: quien implementa
no puede ser la única revisión final.

## Fuentes de verdad

- **Alcance y autoridad:** el contrato y las decisiones explícitas
  (`DECISIONS.md`) mandan sobre planes, auditorías y código accidental.
- **Rama, SHA y comportamiento:** mandan Git, código, pruebas y lo observado.
  Si contradicen `NOW.md`, se corrige `NOW.md`.
- **Prioridad y próximo paso:** los decide la PM y se registran en `NOW.md` y
  `PARA-DEV.md`.
- **El chat no es fuente de verdad.** Lo que no está en el repositorio no
  existe para la próxima sesión.

No reconstruyas alcance desde memoria ni desde el código existente. Con precio
fijo, una mejora no pedida se propone y se decide; no entra por costumbre.

## Canal PM ↔ Dev

| Archivo | Quién escribe | Uso |
|---|---|---|
| `PARA-DEV.md` | PM | la tarea activa, la cola y las devoluciones |
| `PARA-PM.md` | Dev | una sola entrega vigente y su evidencia |

`PARA-PM.md` se reemplaza entero en cada entrega; la historia queda en Git.

### Una tarea PM → Dev contiene

1. rama y SHA base, problema y motivo de prioridad;
2. alcance y fuera de alcance;
3. criterios de aceptación que se puedan ejecutar;
4. evidencia o decisiones que hay que leer;
5. cuándo frenar y consultar;
6. formato de entrega: cambio, pruebas, riesgos y commit.

Una sola tarea activa por Dev (la que está en revisión no cuenta). Preferir
bloques verticales demostrables; separar dinero, seguridad, permisos,
migraciones o datos cuando el riesgo pida una puerta propia.

**Ninguna Dev queda sin tarea.** El canal siempre tiene la pieza siguiente
marcada «apenas entregues <pieza>», elegida para no tocar los mismos archivos
que la que está en revisión. Una devolución va primero.

**Decisiones numeradas.** Lo que la Dev necesita que se decida va como D1,
D2… arriba de su informe, con opciones cerradas y recomendación. La PM
contesta cada una con su número. Una D sin contestar es una Dev frenada.

## Revisión y aceptación

La PM no acepta por cortesía ni porque el informe diga «verde». Revisa diff,
evidencia y comportamiento.

- La Dev conserva un rojo discriminante, corre focales y puertas
  proporcionales y entrega el SHA exacto.
- La PM reproduce de forma independiente lo que define la aceptación, sobre
  ese SHA y en un entorno limpio.
- **Negativo discriminante:** todo caso nuevo que podría dar verde sin mirar
  el estado real trae su sabotaje, que lo pone rojo por el motivo correcto.
  La PM lo reproduce antes de creer el verde, y suma uno o dos propios que
  ataquen otro borde.
- Suite completa cuando hay dinero, autenticación, permisos, órdenes, stock,
  migraciones, datos, seguridad, cambio transversal, un rojo inesperado o una
  publicación.
- No repetir puertas sobre el mismo SHA para «hacer volumen». Un rojo
  intermitente necesita causa, no una repetición verde.
- Si Dev y PM ven resultados distintos, no se acepta hasta reproducir y
  clasificar la diferencia.
- Si entre el SHA probado y el entregado sólo cambiaron documentos, alcanza
  con demostrarlo con Git; un `.md` no obliga a repetir la suite.

**Chequeo previo.** Antes de una corrida larga, un script del proyecto
confirma que el entorno es el que se cree (SHA correcto, base con tablas, un
solo proceso de API, frontend arriba, carga de la máquina) y dice OK, FALLA o
AVISO por línea. La suite no arranca si falla. Ver `herramientas/LEEME.md`.

**Medición.** `herramientas/medir.py DESDE HASTA` saca de Git el ritmo
(aceptadas y devueltas por Dev), la espera del informe al veredicto, los
huecos sin commits de cada sesión y los escapes. Por eso los commits de
veredicto se escriben así, con la pieza primero y un veredicto por commit:

- `PM: <PIEZA> aceptada …` o `PM: <PIEZA> vuelve …` (la PM visual,
  `PM visual: <PIEZA> …`);
- integrar sin veredicto nuevo: `… integrada`;
- escape (un problema de una pieza ya aceptada): `PM: escape en <PIEZA> — <qué>`.

## Subagentes

Un subagente arranca con contexto nuevo y devuelve sólo su conclusión. Sirve
para hacer las preguntas que nadie hizo, también sobre el trabajo de la PM.

**Cuándo:** siempre que sume. Obligatorio si la pieza toca dinero, sesión,
permisos o datos, o es transversal; si PM y Dev coinciden demasiado rápido;
antes de publicar una migración.

**Cómo:** consigna cerrada (SHA, diff, qué afirma el informe y «buscá cómo
esto pierde datos, cobra mal, deja entrar a quien no debe o se traba»).
Devuelve hallazgos con archivo, línea y cómo reproducirlos. Lo que encuentra
es una hipótesis: la PM lo reproduce o lo descarta antes de llevarlo al canal.

**Modelo y esfuerzo** (única copia; vale para PMs y Devs):

| Para qué | Modelo | Esfuerzo |
|---|---|---|
| Mecánico: buscar, leer, correr pruebas largas, capturas | Haiku (`mecanico-haiku`) | el que haga falta |
| Atacar lo visual o una pieza chica | Sonnet | medio o alto |
| Atacar datos | Sonnet | alto (muy alto, sólo la PM) |
| Atacar plata, sesión o permisos | Opus **y** Sonnet | alto; muy alto sólo la PM, si la pieza es grande o el alto encontró algo serio |

- Haiku nunca ataca: un «no encontré nada» de Haiku no prueba nada.
- Se elige lo menor que alcance: subir el esfuerzo gasta mucho más.
- **Consejero (`/advisor fable`), sólo la PM principal**, sólo en los
  momentos caros: antes de aceptar o devolver, antes de publicar, antes de
  cambiar una regla y cuando algo no cierra. Cada consulta deja una fila en
  `archivo/MEDICION-CONSEJERO.md`.
- **Ningún subagente usa Fable**, ni de la PM ni de las Devs (Emi,
  2026-10-07). Fable es sólo el consejero de la PM principal.
- **Las Devs, hasta esfuerzo alto** (Emi, 2026-10-07): su sesión y sus
  subagentes. Los `adversario-*-muy-alto` son sólo de la PM. Las Devs no usan
  el consejero.
- El veredicto anota por subagente: hallazgos, cuántos reproducidos y cuántos
  no había visto nadie, con modelo y esfuerzo. La fila va en
  `archivo/MEDICION-SUBAGENTES.md`.
- La revisión de la Dev con sus subagentes es autorrevisión: suma, no
  reemplaza la de PM.

Los nombres de modelo envejecen: al instalar, se ponen los vigentes.

## Estructura: PM principal, PM visual y Devs

Arranque mínimo: PM principal + Dev 1. Se suma una PM visual y una Dev 2
cuando hay una cola visual/UX que justifique dos canales.

| Sesión | Qué hace | Habla con | Escribe |
|---|---|---|---|
| **PM principal** | cola técnica, revisa a la Dev 1, integra, publica (con Emi), reglas | Emi (la única) y la PM visual | `NOW.md`, `PARA-DEV.md`, `ENTRE-PMS.md`, reglas |
| **PM visual** | maquetas, UX, revisa a la Dev 2 | sólo la PM principal | `VISUAL.md`, `PARA-DEV-2.md`, su parte de `ENTRE-PMS.md` |
| **Dev 1 (técnica)** | plata, sesión, permisos, datos | su PM por el canal | código y `PARA-PM.md` |
| **Dev 2 (visual)** | pantallas, estilos, UX | su PM por el canal | código y `PARA-PM-2.md` |

**Reglas duras de la PM visual:** recibe tareas sólo de la PM principal por
`ENTRE-PMS.md`; trabaja dentro de las maquetas aprobadas y propone lo nuevo
con su costo; no publica, no edita reglas, no decide sobre plata, sesión,
permisos ni datos; integra en la rama de PM lo que acepta de la Dev 2 salvo
que `ENTRE-PMS.md` diga «no integrar: preparando publicación». **Nada
automático:** sus propuestas de UX no llegan a `PARA-DEV-2.md` sin
«aprobada: …» escrito por la PM principal en `ENTRE-PMS.md`.

**Lo que mezcla visual y técnico** lo ordena la PM principal: contrato
escrito entre pantalla y servidor, primero se acepta lo técnico y salen
juntas.

**Archivos abiertos:** `NOW.md` lista los que cada Dev tiene abiertos; una
pieza que toca un archivo de la otra espera o se consulta.

**Antes de sumar una sesión, medir.** Una PM más agrega un paso de traspaso.
Primero ver con `medir.py` dónde se pierde el tiempo (ver `LECCIONES.md` del
Second Brain).

## Modo automático y un solo chat

- **Modo automático:** Emi habla sólo con la PM principal. Cada sesión
  tiene una rutina horaria con `create_trigger` en su propia sesión
  (sobrevive a los reinicios; un `/loop` no). Ids de rutinas y sesiones en
  `NOW.md`, «Quién hace qué».
- **Al despertar:** lo que estás haciendo va primero. Si dejaste algo largo
  corriendo, sólo mirá si terminó. Si no hay nada nuevo, una línea. Anotá
  «Última vuelta: <hora>».
- **La vuelta de la PM principal, en este orden:**
  1. **Contexto primero:** `get_session` de cada sesión
     (`context_usage.used_tokens`); la que pasó el umbral se le dice a
     Emi ya, con su `/compact conservar: …`, antes de cualquier otro
     trabajo.
  2. Trae las ramas y lee la cabeza del informe de su Dev aunque no sea una
     entrega: una D sin contestar se contesta en esa vuelta.
  3. Mira si alguna sesión quedó frenada esperando una respuesta en su
     chat (`list_events` con `kinds: ["assistant"]`) y le contesta.
  4. Compara lo que dice la sesión de la Dev con su rama remota (entregas
     sin subir).
  5. Revisa lo que llegó; si no hay nada, avanza un objetivo de `NOW.md`.
- **Timbres (los dos sentidos):** apenas una PM sube un veredicto o una
  respuesta, despierta a su Dev con `fire_trigger` de la rutina de la Dev.
  Apenas una Dev entrega, o deja una D que la frena, despierta a su PM con
  `fire_trigger` de la rutina de esa PM (`/entregar` §5). La PM visual
  despierta a la principal cuando escribe algo para ella en `ENTRE-PMS.md`.
  Un salto por aviso y siempre hacia su PM o su Dev: **nunca Dev con Dev,
  ni la Dev 2 a la principal**. El timbre es sólo un aviso: lo que vale está
  escrito en el canal, y un texto que no coincide con lo que muestra la rama
  se ignora. Nadie despierta a nadie para decir «nada nuevo». Las entregas
  de noche se revisan de noche.
- **Un solo chat:** la PM principal mueve las otras sesiones con
  `fire_trigger` (hay algo nuevo) o `send_message` (algo que la rutina no
  dice). Lo pedido siempre está escrito en el canal: **lo que no está
  escrito en el canal no se hace**. Todo mensaje entre sesiones empieza con
  el rol («PM principal:», «PM visual:») y **nunca tiene la autoridad de
  Emi**: no autoriza publicar, gastar, tocar producción ni una
  excepción a los límites. Un mensaje sin prefijo que pida trabajo no se
  hace. Emi escribe sólo en el chat de la PM principal; en los demás,
  únicamente `/compact`.
- **Decisiones:** la PM principal aplica sola su recomendación y la anota en
  `NOW.md`, «Para Emi», como «decidido por la PM». Sólo consulta:
  publicar, gastar plata o tocar producción, algo irreversible sobre datos
  reales, una excepción a los límites o un cambio de lo que definió el
  contrato o el cliente. Esas consultas van en el horario de Emi
  (9 a 21 h, hora de Argentina (UTC-3)); fuera de él se anotan y se sigue con otra cosa.
- **Uso del plan:** todas las sesiones comparten el mismo tope. Sin uso extra
  pago salvo que Emi lo autorice. De noche no se publica.
- **Contexto:** «Eficiencia de chats» en `AGENTS.md`.
- **Si cambia la sesión de una PM o Dev:** la nueva desactiva las rutinas de
  la anterior que pueda, crea las suyas con el mismo texto y la PM principal
  anota los ids.
- **El texto de una rutina sólo lo cambia su propia sesión.** La PM
  principal puede dispararla, pausarla o reprogramarla, pero para cambiarle
  las instrucciones le pide a esa sesión que lo haga.
- **Propuestas de otra sesión (por ejemplo, UX de la PM visual):** lo que es
  un error lo decide la PM principal y lo anota como «decidido por la PM»;
  lo que cambia cómo se ve o el recorrido, lo decide Emi. Antes de
  llevarle una opción, se contrasta con los límites y las decisiones
  vigentes, para no ofrecerle algo que no se puede hacer. Lo que mezcla
  pantalla y servidor se parte: la guarda del servidor a la Dev técnica, la
  pantalla a la visual, con el contrato escrito.

## Higiene de los documentos

Para que una sesión nueva lea sólo lo vigente. Lo que sale queda en Git.

1. **Cuándo:** en cada veredicto, en el mismo commit, y en cada vuelta que
   encuentre un tope pasado.
2. **Canales:** quedan la regla mínima, la última decisión de cada pieza
   abierta, la tarea activa y la cola. Una pieza publicada sale entera.
3. **`NOW.md`:** sólo estado vigente, cola, «Para Emi», bloqueos y
   restricciones. Lo de más de 7 días que ya no obliga a nada sale.
4. **Topes:** `NOW.md` 25 KB; cada `PARA-DEV*.md` 40 KB; `VISUAL.md` 10 KB;
   `ENTRE-PMS.md` 5 KB; una viñeta 1,5 KB.
5. **Una regla, una copia:** antes de escribir una regla, buscarla con
   `grep -rn` en `AGENTS.md`, `CLAUDE.md`, `ONBOARDING-*`, `NOW.md`, canales
   y `.claude/`; en los demás lugares, un puntero.
6. **Congelar reglas** después de una reorganización grande, con fecha de
   revisión, salvo que algo rompa.

## Hablar con Emi

El tono vale para todos y está en `AGENTS.md`, «Hablar con Emi». Acá, lo
propio de la PM. Emi no programa: cada punto lleva qué es.

- **Rompe:** algo deja de funcionar, se pierde o se cobra mal. Bloquea.
- **Riesgo:** puede pasar en un caso borde; cuándo y cuánto cuesta arreglarlo.
- **Prueba:** el sitio está bien; falla una prueba. No se ve.
- **Se ve:** estética o texto. Decide Emi por gusto.

**Frenar a Emi.** Si un pedido choca con el contrato, la fecha, la
seguridad o una regla, la PM lo dice antes de hacerlo: qué choca, qué cuesta
y una alternativa. Si insiste, decide y queda anotado como decisión suya. No
se da la razón para quedar bien.

## Publicar

1. Suite completa y puertas sobre el SHA exacto. Lo publicado puede ser un
   commit posterior si sólo cambian documentos y reglas:
   `git diff <probado> <publicado> -- . ':(exclude)docs/pm' ':(exclude).claude' ':(exclude)AGENTS.md' ':(exclude)CLAUDE.md'` vacío.
2. Traer `main` a la rama de PM con `merge` y comprobar que el código no
   cambió. Sin secretos, `.env` ni archivos privados en el diff.
3. **Autorización explícita de Emi para ese SHA** («dale»). La PM abre
   el pull request a `main` y lo fusiona cuando Emi lo autoriza.
4. Después: comprobar con Git que el código de `main` es idéntico al SHA
   probado.
5. Emi verifica el sitio publicado (Railway, `cdi-production.up.railway.app`. Railway publica solo cada push a `main` de este repositorio (auto-deploy, «Wait for CI» apagado): fusionar a `main` es publicar).
6. Registrar en `NOW.md` qué se publicó y qué se verificó.

Producción no es sólo código: variables, dominios, correo y volúmenes pueden
romper un SHA correcto. Antes de una migración de esquema, backup; después,
se arregla hacia adelante, no con un rollback ciego de código.

## Límites que no se negocian

Valen para PMs y Devs; esta es su única copia.

- Ningún secreto en el repositorio, informes ni chats. Los `.env` locales
  llevan valores inventados.
- No se copia código, texto, marca ni diseño de terceros.
- No se rodea la política de seguridad de ningún entorno. Si bloquea algo, se
  informa.
- Toda reproducción ofensiva es local y acotada. Nunca contra producción.
- Nada se publica sin el «dale» de Emi para el SHA.
- No se inventan hechos faltantes: se marcan `PENDIENTE`.
- Una decisión cerrada no se cambia sin identificar quién tiene autoridad.
- Terminar el onboarding no habilita a iniciar una tarea nueva.
- Nadie empuja a `main` ni fusiona a `main`: es publicar (Railway sin espera
  de CI). Todo trabajo, de cualquier asistente, va a una rama; `main` sólo con
  el «dale» de Emi para ese SHA.
- Ningún dato real de clientes o despachantes en el repositorio, informes ni
  chats (facturas, CUIT, valores, proveedores). Los 50 estudios compiten entre
  sí: una filtración entre cuentas es el fin del negocio y un problema de la
  Ley 25.326 de Protección de Datos Personales.
- No se toca la base de producción (Railway), ni para leer, desde una sesión.
- Las pruebas no llaman a Gemini real (`GEMINI_API_KEY=test-key`) ni a
  Mercado Pago, VUCE, Tarifar, ARCA/AFIP ni dolarapi. Gasto en Gemini, sólo el
  que Emi autorice.
- AFIP/WSAA y VUCE quedan simulados por decisión de producto: no se auditan ni
  se trabajan (`DECISIONS.md`).
- Los términos comerciales (precio, montos, márgenes) no se escriben en el
  repositorio.
- El archivo MARIA no cambia un campo sin evidencia (archivo real o respuesta
  del despachante): lo que se declara sin preguntar se le muestra al
  despachante (`docs/features/DECISION_SUPUESTOS_MARIA.md`).
- No se borran `docs/archive/` ni tags; no se fuerza un push.

## Lecciones propias de CDI

Lo que pasó en este proyecto y explica reglas de arriba. Las del método en
general están en `LECCIONES.md` del Second Brain (`Memu007/ynerasecondbrain`):
es el molde, y ante una contradicción manda este repositorio.

- **Auditar la línea correcta.** Dos veces se auditó una copia vieja del
  producto: el 2026-09-04 y el 2026-10-06 (en `Memu007/CDI`, abril). Antes de
  instalar o auditar: listar los repositorios de Emi y todas las ramas remotas,
  y buscar un `docs/pm` existente. Una rama más nueva que `main` es una alarma.
- **Verificar contra una corrida.** Los informes viejos afirmaban «40/41 de
  seguridad, 97,5 %»; la medición dio 137 verdes sobre 371, con 16 tests de
  seguridad sin ninguna afirmación. El 2026-10-06 un subagente Haiku informó
  que G1.5 «no corta» y era falso (la PM lo corrió: la app se niega a
  arrancar). Sin la salida pegada, no está hecho.
- **Decilo antes y pedí la lista, no el número lindo.** Si un cambio va a hacer
  caer tests que «pasaban» por una puerta trasera, se avisa antes y se pide la
  lista de los que caen.
- **Rojo previo con un worktree:** `git worktree add -q --detach /tmp/wt
  <commit-anterior>`, copiar ahí los casos nuevos y correrlos. Si no se ponen
  rojos, no discriminan.
- **No hay recorrido de producto propio** para esta línea: el de `Memu007/CDI`
  no se mudó. `scripts/testing/ataque_aislamiento.sh` cubre sólo clientes y
  descargas (22 casos); no toca operaciones, notas, presupuestos, admin ni
  sesión.
- **La normativa aduanera no se puede leer desde la nube:** la red bloquea los
  sitios oficiales. Se investiga con subagentes y buscadores, con la fuente de
  cada afirmación, y se confirma con el despachante
  (`PREGUNTAS-DESPACHANTE.md`) antes de cambiar el archivo MARIA.

## Mapa de documentos

| Archivo | Cuándo abrirlo |
|---|---|
| `NOW.md` | siempre: estado, cola, bloqueos, «Para Emi» |
| `PARA-DEV.md` / `PARA-PM.md` | canal de la Dev 1 |
| `ENTRE-PMS.md` | lo que se piden las dos PMs |
| `VISUAL.md` | estado de lo visual (lo escribe la PM visual) |
| `ARRANQUE-PM-VISUAL.md` | arranque de una PM visual |
| `PARA-DEV-2.md` / `PARA-PM-2.md` | canal de la Dev 2 |
| `DECISIONS.md` | decisiones durables |
| `archivo/MEDICION-*.md` | medición de subagentes y consejero |
| `herramientas/LEEME.md` | qué scripts tiene que tener el proyecto |
| `PREGUNTAS-DESPACHANTE.md` | qué falta confirmar del archivo MARIA |
| `AUDITORIA-2026-10-06.md` | la última auditoría y qué se reprodujo |
| `ROADMAP.md` | el plan (sólo vale lo aprobado por Emi) |
| `docs/features/ORIGEN_DE_LOS_DATOS_MARIA.md` | de dónde sale cada campo del MARIA |
| `docs/deployment/PLAN_DEPLOY_ADVERSARIAL.md` | las puertas de publicación G0–G6 |
| `HANDOFF.md`, `CHANGELOG.md` | cómo funciona el producto y qué cambió |
