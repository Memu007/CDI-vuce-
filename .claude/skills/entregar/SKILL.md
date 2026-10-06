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
  supuesto reversible, para que la PM pueda rechazarlo.
- **Subagentes adversariales:** los que pide la tabla «Modelo y esfuerzo»
  de `docs/pm/ONBOARDING-PM.md` («Subagentes»). Lo que
  encuentren lo reproducís; el informe lleva la tabla de hallazgos con
  modelo y esfuerzo de cada uno.
- **`/code-review`:** corré `/code-review high` sobre lo que cambió
  la rama desde la base. Lo confirmado dentro de la tarea se arregla, con su
  rojo antes. Lo que quede afuera va al informe como riesgo, con su
  severidad. Si la pieza toca dinero, sesión, permisos, órdenes, stock,
  migraciones o datos, corré también `/security-review`.
- **Negativos:** cada caso nuevo o cambiado tiene su sabotaje discriminante
  (un script por pieza, uno por motivo), con lo que el rojo tiene que decir y
  lo que no. Ningún sabotaje toca datos compartidos de prueba: el caso
  trabaja sobre lo que crea y retira.
- **Sabotajes vigentes:** corré enteros, sobre el SHA que entregás, los
  sabotajes de piezas anteriores que tocan archivos que cambiaste. Un patrón
  que ya no se encuentra es una falla del script, no un salto: arreglalo, y
  el script tiene que salir con error si no lo encuentra.

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
PUERTO=<puerto libre> ./scripts/testing/ataque_aislamiento.sh             # si tocaste datos, sesión o permisos (cubre sólo clientes y descargas)
```

- Un rojo se diagnostica; no se repite hasta que pase. Los rojos de entorno
  conocidos se listan acá con su causa.

## 4. Informe en tu canal

`PARA-PM.md` para la Dev 1, `PARA-PM-2.md` para la Dev 2. El de la otra no
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
  tu canal (`PARA-DEV.md` o `PARA-DEV-2.md`). Puede haber cambiado la tarea
  activa.
- Ningún archivo privado ni secreto en el árbol (`.env`, `.env.afip`, bases locales `*.db`, PDFs, Excel o TXT de clientes reales, `viejo/`, `venv/`). Si aparece, no subas.
- `git push -u origin <rama Dev>`; sólo por fallas de red, reintentá a los
  2, 4, 8 y 16 s.
- **Comprobá que subió:** `git ls-remote origin refs/heads/<rama Dev>` tiene
  que dar lo mismo que `git rev-parse HEAD`. Si no, no entregaste.
- **Avisale a tu PM:** `fire_trigger` de su rutina (Dev 1 → PM principal;
  Dev 2 → PM visual; los ids están en `NOW.md`, «Quién hace qué»), con el
  texto «Dev N: entregué <PIEZA> en <SHA>». Es un timbre: lo que vale es el
  informe en tu canal. Nunca a la otra Dev. En el chat, una línea igual. Lo
  que haya que decidir va como D en el informe.
- Sin `/loop` y sin esperar el veredicto: seguí con la pieza marcada
  «apenas entregues» (`CLAUDE.md` §4).
