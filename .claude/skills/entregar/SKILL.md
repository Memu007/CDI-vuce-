---
name: entregar
description: Dev. Cerrar una pieza de la tarea activa - autorrevisión con subagentes, negativos, puertas, commits separados, informe en PARA-PM.md y push. Usalo cuando el código y los casos de la tarea ya están.
---

# /entregar — cerrar una pieza

Qué es una entrega lo dicen `CLAUDE.md` §4 y `docs/pm/ONBOARDING-DEV.md`
(«Calidad mínima de una entrega», «Informe Dev → PM»). Acá va el orden y los
comandos.

## 1. Antes de darla por terminada

- **Auto-revisión:** leé `git diff <base>..HEAD` completo y sacá lo que la
  tarea no pide. Lo que agregaste sin que se pidiera va en el informe como
  supuesto reversible, para que la PM pueda rechazarlo. Para `CLAUDE.md` §6,
  `docs/pm/herramientas/chequeo-6.py <base> HEAD` (lee JS/TS con
  `typescript`: el del proyecto, o uno global por `NODE_PATH`): su salida va
  entera en el informe, y cada `AVISO` se arregla o lleva una línea de por
  qué queda. Lo que no mide (un caso por causa, un chequeo en un solo lugar,
  el porqué de cada comentario) lo mirás vos.
- **Subagentes adversariales:** los que pide la tabla «Modelo y esfuerzo»
  de `docs/pm/ONBOARDING-PM.md` («Subagentes»); en la vuelta de una
  devolución de plata, sesión o permisos, uno solo, Sonnet alto («Cuántos y
  quién los corre»). Lo que encuentren lo reproducís; el informe lleva la tabla de hallazgos con
  modelo y esfuerzo de cada uno.
- **`/code-review`:** corré `/code-review high` sobre lo que cambió
  la rama desde la base. Lo confirmado, de acá o de los subagentes, se
  arregla con su rojo antes si está dentro de la tarea y tiene camino de hoy
  («Código de producto sólo con camino de hoy» en `ONBOARDING-PM.md`). Lo
  demás va al informe como riesgo, con su severidad. Si la pieza toca
  dinero, sesión, permisos, órdenes, stock, migraciones o datos, corré
  también `/security-review`.
- **Negativos:** cada caso nuevo o cambiado muestra su rojo discriminante.
  Guion de sabotaje propio sólo donde lo pide `CLAUDE.md` §6, uno por
  motivo, anclado en código, con lo que el rojo tiene que decir y lo que no;
  en lo demás, el informe muestra el rojo una vez con el arreglo revertido.
  Ningún sabotaje toca datos compartidos de prueba: el caso trabaja sobre lo
  que crea y retira.
- **Sabotajes de piezas anteriores:** al entregar corrés sólo los de tu
  pieza. Los de lo que cambió en la tanda los corre la PM antes de publicar
  («Publicar» en `ONBOARDING-PM.md`); si ahí falla uno que toca lo tuyo,
  vuelve como devolución.

## 2. Commits

- El producto en un commit; los casos, el arnés y los negativos en otro; el
  informe en otro.
- Mensajes en castellano con prefijo (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`). Una a tres líneas en `CHANGELOG.md` por cambio de producto.

## 3. Puertas, sobre el SHA que se entrega

```bash
# desde el worktree que dejó levantar.sh, con su entorno virtual
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov --timeout=120    # base 2026-10-06 en e8344d0: 680 passed, 102 skipped, 0 failed
python -m compileall -q proyecto_maria
BASE_URL=http://127.0.0.1:<puerto> ./scripts/testing/smoke_friccion.sh   # si tocaste backend
PUERTO=<puerto libre> ./scripts/testing/ataque_aislamiento.sh             # si tocaste datos, sesión o permisos
```

- Un rojo se diagnostica; no se repite hasta que pase. Los rojos de entorno
  conocidos se listan acá con su causa.

## 4. Informe en tu canal

`PARA-PM.md` para la Dev 1, `PARA-PM-N.md` para la Dev N. El de las otras no
se toca.

- Reemplazá todo el cuerpo. Conservá el encabezado `# Dev → PM` y «Este
  archivo es mío y vos no lo tocás. Acá te informo.».
- Arriba: tabla de SHAs, el resultado y lo que decide la PM, o «Nada para
  decidir» con los supuestos.
- **Lo que decide la PM va numerado: D1, D2…** Cada decisión con sus
  opciones cerradas, tu recomendación y por qué, en un bloque «Decisiones»
  arriba de todo. La PM contesta en `PARA-DEV.md` con el mismo número, así
  ninguna queda sin respuesta.
- Un bloque corto de comandos copiables, cada uno con lo que tiene que
  mostrar.
- Tabla de puertas con la salida exacta y riesgos.
- Los archivos de producto que tocaste: la PM los anota en `NOW.md`,
  «Quién hace qué» (archivos abiertos), para que la otra Dev no los pise.
- Los textos de cada rojo se copian de la salida, no de memoria. Antes de
  commitear, releé cada número del informe contra su log.

## 5. Subir

```bash
git fetch origin <rama Dev> && git log --oneline HEAD..origin/<rama Dev>
```

- Si la PM escribió mientras tanto (en su rama): integrá con `merge` y releé
  tu canal (`PARA-DEV.md` o `PARA-DEV-N.md`). Puede haber cambiado la tarea
  activa.
- Ningún archivo privado ni secreto en el árbol (`.env`, `.env.afip`, bases locales `*.db`, PDFs, Excel o TXT de clientes reales, `viejo/`, `venv/`). Si aparece, no subas.
- `git push -u origin <rama Dev>`; sólo por fallas de red, reintentá a los
  2, 4, 8 y 16 s.
- **Comprobá que subió:** `git ls-remote origin refs/heads/<rama Dev>` tiene
  que dar lo mismo que `git rev-parse HEAD`. Si no, no entregaste.
- **Avisale a tu PM:** `send_message` a la sesión de tu PM, `priority` `next`
  (en CDI las dos Devs → PM principal, porque no hay PM visual; las sesiones
  están en `NOW.md`, «Quién hace qué»; `fire_trigger` no la despierta), con el
  texto «Dev N: entregué <PIEZA> en <SHA>». Es un timbre: lo que vale es el
  informe en tu canal. Nunca a la otra Dev. En el chat, una línea igual. Lo
  que haya que decidir va como D en el informe.
- Sin `/loop` y sin esperar el veredicto: seguí con la pieza marcada
  «apenas entregues» (`CLAUDE.md` §4).
