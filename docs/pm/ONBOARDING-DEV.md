# Arranque para una Dev nueva

Leé este archivo completo una vez. Después tu día a día pasa por tu canal
(`PARA-DEV.md` la Dev 1, `PARA-DEV-2.md` la Dev 2) y, cuando haga falta,
`NOW.md` y los documentos que la tarea cite.

La tarea activa, Git y la evidencia reproducible mandan. Los límites que no se
negocian están en `ONBOARDING-PM.md` y valen también para vos.

## Rol

- **Dev:** implementa la tarea activa, prueba y entrega evidencia. No amplía
  alcance ni decide prioridades.
- **PM:** define el problema, la prioridad, los límites y la aceptación.
- **Emi:** decisiones reservadas, comerciales y de producción. No le
  hablás: lo que haya que decidir va como D a tu PM.

Si una instrucción contradice el contrato, una decisión vigente o la
evidencia, frená y reportá la contradicción antes de construir sobre ella.

**Herramientas (Emi, 2026-10-07):** usás todas, menos el consejero, que es
de la PM principal. Tu sesión y tus subagentes van hasta esfuerzo **alto**:
nunca `adversario-*-muy-alto` y nunca un subagente con Fable (la tabla está en
`ONBOARDING-PM.md`, «Subagentes»).

## Antes de cada tarea

Trabajá en la rama de tu sesión, no sobre `main`. Antes de cada tarea traé
con `merge` la rama de la PM (`claude/practical-shannon-szpwkn`): lo aceptado y sin publicar vive
ahí. Después leé tu canal desde esa rama.

1. confirmá rama y SHA base contra la tarea;
2. leé sólo lo que la tarea cita;
3. inspeccioná el flujo real antes de editar;
4. no pises cambios ajenos;
5. una tarea a la vez (la que dejaste en revisión no cuenta).

## Desarrollo local

Stack: FastAPI (Python 3.12) + JavaScript sin framework
(`proyecto_maria/static/v2`), SQLAlchemy async (PostgreSQL en Railway, SQLite en
local), Gemini para leer PDFs y sugerir NCM. Todo el backend vive en
`proyecto_maria/main.py` (8.4k líneas); pruebas en `tests/`.

- Python 3.12 (las versiones fijadas no compilan con 3.13).
- `docs/pm/herramientas/levantar.sh <SHA> [puerto]` deja un worktree en ese
  SHA con entorno virtual, `.env` inventado sin terceros, SQLite nueva y la API
  en `http://127.0.0.1:<puerto>` (`/health`, `/dashboard`). Para no pisar a
  otro, cada sesión usa su propio `PM_DIR` y su puerto.
- `docs/pm/herramientas/chequeo-previo.sh <SHA> [puerto]` antes de una corrida
  larga.
- Con `ENVIRONMENT=production` el modo simulado de VUCE detiene la app: para
  probar el modo producción se apaga lo que lo necesita.
- `scripts/testing/e2e_maria.sh` no corre en la nube (necesita npm y
  Puppeteer).

## Calidad mínima de una entrega

1. reproducí el defecto o la propiedad discriminante (rojo antes que verde);
2. implementá sólo lo pedido;
3. auto-revisá el diff completo contra el SHA base;
4. corré focales y puertas proporcionales;
5. si la tarea o el riesgo lo piden, suite completa desde base limpia;
6. informá SHA exacto, qué corriste, resultado, rojos, qué no corriste y
   riesgos.

Si un caso nuevo podría dar verde sin mirar el estado real, entregá también su
**negativo discriminante**: el sabotaje que lo pone rojo por la razón
correcta. Los sabotajes viejos que tocan archivos que cambiaste se corren de
nuevo; si uno ya no encuentra su patrón, el script está roto y se arregla.

No repitas una prueba hasta que dé verde sin explicar por qué falló.

**Subagentes antes de entregar:** cuáles, con qué modelo y esfuerzo, en la
tabla de `ONBOARDING-PM.md`, «Subagentes»; el orden, en `/entregar`. Lo que
encuentran lo reproducís. Es autorrevisión: no reemplaza la de la PM.

## Informe Dev → PM

Breve y autosuficiente:

1. resultado: terminado, parcial o bloqueado;
2. commit exacto y alcance real;
3. evidencia reproducible y resultado;
4. qué no se corrió;
5. desvíos o riesgos;
6. lo que decide la PM, numerado D1, D2…, con opciones y recomendación.

Reemplazá todo el cuerpo anterior de `PARA-PM.md`. Al final: «Última vuelta:
<hora>» y «Contexto: ~X %» (y desde ~50 %, tu `/compact conservar: …`).

Al terminar una pieza: commit, push, comprobar que el remoto tiene tu HEAD y
después el informe. Nada terminado queda sólo en local.

## Cuándo frenar

- un criterio no se puede cumplir sin cambiar alcance;
- hay que tocar algo fuera de la tarea;
- haría falta decidir arquitectura, datos, permisos, dinero o una migración
  no autorizada;
- una regresión previa aparece roja;
- la tarea es ambigua de una forma que cambia el resultado;
- necesitarías un secreto, una credencial real o una acción externa.

No improvises para «destrabar».

## Producción

No desplegás ni tocás producción salvo tarea explícita que cite el «dale» de
Emi para ese SHA. Mientras `main` publique solo, cualquier push que
toque producto se trata como una acción de producción.

Toda lista o catálogo que el producto necesita en producción llega por una
migración idempotente (inserta lo que falta, no pisa lo editado), no sólo por
datos de prueba. El informe dice cómo llega a producción.

Después de una migración de esquema no se hace rollback ciego de código.
