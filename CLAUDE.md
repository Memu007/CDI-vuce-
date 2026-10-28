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
- La revisión de PM es cara: arriba, el resultado y lo que decide ella;
  después, un bloque corto de comandos copiables con lo que cada uno tiene
  que mostrar, y lo ya corrido con su salida exacta.
- No pedirle a la PM pasos que un script pueda hacer.

El procedimiento está en los comandos del proyecto (`.claude/skills/`):
`/entregar` cierra una pieza (con autorrevisión de subagentes y
`/code-review`) y `/respondio` retoma después de que la PM escribió. La Dev no
deja un `/loop`: la despierta la PM principal o su rutina (cada 3 horas). Al
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
  final de `docs/pm/PARA-PM.md`, Dev 2 al final de `docs/pm/PARA-PM-2.md`,
  PM principal en `docs/pm/NOW.md`.

Después de compactar, antes de seguir, releé ese archivo y tu canal en la
rama.
