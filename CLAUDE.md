# Cómo se trabaja en CDI

**Primero leé `AGENTS.md`**: es la puerta de entrada de cualquier asistente y
dice qué leer según tu rol. Este archivo tiene las reglas para tocar código, y
valen para cualquier asistente, no sólo para Claude.

Reglas estables para desarrollo. La tarea concreta y sus puertas viven en
`docs/pm/PARA-DEV.md`; no se duplican acá.

## 1. Verificar antes de implementar

El rol Dev no es obedecer ciegamente: es comprobar la premisa de la tarea.

- Contradecir con evidencia, no con opinión.
- Intentar romper la propia solución antes de declararla verde.
- Una prueba que no distingue el defecto no demuestra la corrección.
- Si una objeción de la PM es correcta, se reconoce y se corrige.
- Una objeción resuelta y decidida se ejecuta sin reabrirla por costumbre.

Adversarial no significa ampliar alcance ni discutir por deporte.

## 2. Evidencia

- Si no se corrió, se declara como no corrido.
- No usar esperas fijas para forzar verdes cuando se puede esperar una
  condición observable.
- Una afirmación general se sostiene con código o pruebas, no con una lista
  manual que envejece.
- Un rojo intermitente o de entorno se diagnostica y se informa; no se oculta
  repitiendo hasta obtener verde.

## 3. Seguridad y alcance

Los límites que no se negocian tienen su única copia en
`docs/pm/ONBOARDING-PM.md`, «Límites que no se negocian». Además:

- No dejar puertas traseras ni atajos de prueba en el producto.
- No agregar funcionalidad fuera de la tarea: se propone a la PM.
- No desplegar ni cambiar producción salvo tarea explícita que cite el
  «dale» de Emi para ese SHA.
- No debilitar controles de producción para hacer pasar las pruebas.

Dinero, autenticación, permisos, órdenes, stock, migraciones, datos y
seguridad requieren una revisión más fuerte.

## 4. Entrega

- Producto, pruebas e informe en commits separados.
- Pruebas proporcionales al riesgo. Cuando corresponde suite completa, desde
  base limpia y sobre el SHA que se entrega.
- Auto-revisar el diff completo contra la base y retirar lo fuera de alcance.
- Informar SHA, pruebas, resultado, rojos, qué no se corrió y riesgos.
- Ninguna fecha justifica saltarse un paso: lo que no entra se corre para
  después y el informe lo dice.
- La revisión de PM es cara: arriba, el resultado y lo que decide ella;
  después, un bloque corto de comandos copiables con lo que cada uno tiene
  que mostrar, y lo ya corrido con su salida exacta.
- No pedirle a la PM pasos que un script pueda hacer.

El procedimiento está en los comandos del proyecto (`.claude/skills/`):
`/entregar` cierra una pieza (con autorrevisión de subagentes y
`/code-review`) y `/respondio` retoma después de que la PM escribió. La Dev no
deja un `/loop`: la despierta la PM principal o su rutina. Al
entregar no se queda esperando el veredicto: sigue con la pieza marcada
«apenas entregues»; si el veredicto trae una devolución, esa va primero.

La revisión independiente la hace la PM. Dos corridas de la Dev no
reemplazan independencia.

## 5. Detalles del repositorio

- PM escribe `docs/pm/PARA-DEV.md`; Dev responde en `docs/pm/PARA-PM.md`.
  Ningún rol edita el canal del otro.
- Estado, prioridades y restricciones vigentes: `docs/pm/NOW.md`.
- `HANDOFF.md` describe cómo funciona el producto (stack, pantallas, flujo). Está
  desactualizado desde julio: el estado vigente está en `docs/pm/NOW.md`.
- `CHANGELOG.md`: una a tres líneas por cambio de producto, con fecha.
- `docs/archive/`, `viejo/` y `venv/` son de sólo lectura.
- `.specify/`, `.windsurf/plans/`, `.devin/plans/` y `plans/` son notas de
  otras herramientas, no reglas.
- La CI (`.github/workflows/ci.yml`) deselecciona tests de presupuestos
  compartidos: no es una red de seguridad completa, y Railway no la espera.

## 6. Código como lo dejaría una senior

Rige para cada diff nuevo, de las Devs y de la PM. Lo ya escrito se limpia
después de la entrega (cola en `docs/pm/COLA-LIMPIEZA.md`), no dentro de un
arreglo.

- Un arreglo resta antes de sumar: primero se mira si sacar o unificar código
  lo resuelve. El informe trae `producto +N/−M`; si suma más de 20 líneas
  netas, una línea dice por qué.
- Sin historia en el producto. Las líneas agregadas no nombran piezas, casos,
  SHAs ni «antes daba…»: eso va en el mensaje del commit.
  `git diff <base> -- proyecto_maria/ | grep '^+' | grep -E '[A-Z]{4,}(-[A-Z]{2,})*-[0-9]|caso [0-9]'`
  da vacío.
- Un comentario nuevo dice, en una o dos líneas, el porqué que el código no
  muestra.
- Un chequeo que quedaría repetido en dos lugares se pone una vez, donde pasan
  los dos, en el mismo commit.
- Función nueva hasta ~60 líneas, archivo nuevo hasta ~800. A una función de
  más de 150 líneas no se le suma otra rama: lo nuevo va aparte. Partirla va
  a la cola de limpieza.
- Un caso por causa: la familia de entradas va como datos dentro de ese caso.
  Un caso nuevo del arnés tiene nombre corto, hasta ~80 líneas y ninguna
  espera fija nueva.
- Guion de sabotaje propio sólo en lo que pide revisión más fuerte (§3). En
  lo demás, el informe muestra una vez el rojo con el arreglo revertido. El
  ancla de un sabotaje es código, nunca un comentario.
- La PM pide comportamiento y prueba. Si sugiere cómo hacerlo, lo marca
  «sugerencia»: no es criterio de aceptación.

Los números los mide `docs/pm/herramientas/chequeo-6.py <base> <SHA>`: su
salida va entera al informe, y cada `AVISO` se arregla o lleva una línea de
por qué queda.

# Compact instructions

Cada sesión se compacta sola con `/autocompact 200k`, alrededor de ~150k
(«Eficiencia de chats» en `AGENTS.md`). Al compactar, sola o a mano, el
resumen conserva:

- quién sos: rol, sesión, rama, rutina y a quién avisás al terminar;
- la pieza activa y su paso exacto: SHA, qué corre en segundo plano y dónde
  deja la salida;
- lo pendiente y de quién depende; las decisiones abiertas y las tomadas;
- las reglas de Emi que estás usando (quién te puede pedir algo, nada
  se publica sin su «dale» para el SHA, nunca `main`, sin secretos);
- palabra por palabra, tu último `/compact conservar: …` escrito: Dev 1 al
  final de `docs/pm/PARA-PM.md`, Dev N al final de `docs/pm/PARA-PM-N.md`,
  PM principal en `docs/pm/NOW.md`.

Después de compactar, antes de seguir, releé ese archivo y tu canal en la
rama.
