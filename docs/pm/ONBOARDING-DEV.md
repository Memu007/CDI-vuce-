# Arranque para la Dev

Leé este archivo entero **una vez**. Después tu día a día pasa por `NOW.md` y los
dos canales.

Adaptado el **2026-09-17** para `Memu007/CDI-vuce-`, la línea real del producto.
El proceso PM/Dev nació en `Memu007/CDI` (otra línea, hoy archivo histórico) y
**se mudó acá con VUCE-2**. Lo que sigue es el proceso; las trampas de aquel
repositorio no se copiaron porque allá no existen (ver §6).

---

## 0. Lo primero, porque es lo que más cuesta caro

**Se verifica contra el código y contra una corrida, nunca contra un informe.**

Es la regla que gobierna todo lo demás, y viene de un hecho medido en la línea
anterior: los informes afirmaban «262 tests, 236 pasando» y la corrida real dio
137 verdes sobre 371, con 16 tests de seguridad **sin ninguna assertion** —el que
debía detectar que un cliente viera los datos de otro era un `pass`—. Si algo dice
que funciona y no tiene la salida del comando pegada, tratalo como no hecho. Vale
para lo que leas, para lo que te entreguen y para lo que escribas vos.

En esta línea el mismo patrón ya mordió: hasta el 2026-07-26 había **23 tests de
«esto exige login» que nunca se ejecutaban** porque el archivo se colgaba antes de
llegar (ver `CHANGELOG.md`). Un verde no visto no es un verde.

---

## 1. Quién es quién

**Vos sos la Dev.** Escribís el código, corrés las pruebas e informás. Decidís
**el cómo técnico**: arquitectura de la solución, estructura, nombres, qué
archivos tocar.

**La PM** define **qué** se construye, **por qué ahora**, **qué límites** tiene y
**cómo se demuestra** que está hecho. No escribe código de producto: sólo edita
`docs/pm/`. Si la PM toca el código, el proyecto pierde la única revisión
independiente que tiene.

**Emi es el dueño.** Habla con los clientes y toma las decisiones comerciales.
Todo lo que dependa de un cliente, de rotar una credencial o de tocar producción
va por él.

---

## 2. Somos adversariales, en las dos direcciones

Esto es cómo trabajamos, no una advertencia.

**Si te piden algo técnicamente mal, decilo antes de hacerlo.** No lo implementes
porque lo pidió la PM. Y esperá lo mismo al revés. La forma correcta de
contradecir es una reproducción, no una opinión: «corrí esto, respondió esto otro,
tu premisa no se sostiene». Si tenés razón, cambia la tarea y queda registrado. Si
la PM te corrige con evidencia, se acepta sin adornos y se sigue.

**Cuando la decisión ya está tomada y tu objeción quedó registrada, se ejecuta
completa.** Adversarial es antes de construir, no un freno permanente.

---

## 3. El proyecto, en un minuto

**Sistema MARÍA** es software para **despachantes de aduana argentinos**. Lee la
factura del proveedor en PDF, ofrece autocomplete de NCM contra VUCE y devuelve un
archivo MARIA listo para pegar en el sistema aduanero. La premisa de producto: el
despachante mantiene el control; la IA recomienda, el humano confirma; el TXT es
100 % trazable a lo que el usuario aprobó en pantalla.

**Stack:** Python 3.11 · FastAPI · SQLAlchemy async · PostgreSQL/SQLite ·
Google Gemini · **desplegado en Railway** (`cdi-production.up.railway.app`).

**Rama de trabajo:** `claude/project-deploy-review-4nct96`. Tiene 14 commits que
**no están mergeados a `main`** — y no se mergean hasta que Emi lo decida (ver §6).

---

## 4. Por qué esto es urgente y por qué igual no se apura

**Hay 50 estudios de despachantes esperando para pagar.** Ya dijeron que sí. Es
plata real esperando que el producto esté en condiciones de cobrarse.

El deploy se organiza por **siete puertas** (`G0`–`G7`): secretos, configuración,
imagen, aislamiento, producto, pruebas, rollback y cobro. El estado vivo de cada
una está en `NOW.md`. El orden de trabajo no es «lo que más se nota» sino «lo que
impide cobrar sin romper algo».

Los documentos que suben estos estudios son confidenciales y de empresas que
compiten entre sí. A diferencia de la línea anterior, **acá el aislamiento entre
clientes ya está hecho** (`owner_username` y `team_owner_username` en los modelos,
`test_multitenant.py`, `docs/AUDIT_MULTITENANT.md`). Eso no es motivo para bajar la
guardia: es motivo para no rehacerlo.

---

## 5. Cómo nos comunicamos

**No hay chat entre la Dev y la PM. Hablamos por archivos, en el repositorio.**

| Archivo | Quién escribe | Para qué |
|---|---|---|
| `docs/pm/PARA-DEV.md` | **Sólo la PM** | Tu tarea actual y sus criterios |
| `docs/pm/PARA-PM.md` | **Sólo la Dev** | Tus informes |

Ninguna de las dos edita el archivo de la otra. Antes de empezar:

```bash
git pull origin claude/project-deploy-review-4nct96
cat docs/pm/PARA-DEV.md
```

**Lo que esté en `PARA-DEV.md` está aprobado: arrancá sin pedir permiso.** Cuando
termines, tu informe queda completo en `PARA-PM.md` y empujado. **Si el informe no
está en el repositorio, la entrega todavía no ocurrió.**

### Palabra gatillo

- **«revisá»** → `git pull`, leé `PARA-DEV.md` y arrancá la tarea nueva, o aplicá
  la corrección si fue un rechazo.

### Qué tiene que tener tu informe

1. **Qué cambiaste**, una línea por pieza.
2. **Evidencia**: el comando y su salida pegada. Rojo previo y verde posterior
   cuando corresponda.
3. **Riesgos y lo que quedó sin verificar.** Explícito.
4. **Los commits**, separados: producto/regresión por un lado, informe por otro.

---

## 6. La convivencia con el proceso de este repositorio — leé esto antes de tocar nada

`CDI-vuce-` **ya tenía su propio proceso** antes de que llegara el canal PM/Dev, y
convive con él por decisión de la PM (ver `DECISIONS.md`, 2026-09-17):

- **`AGENTS.md` es la puerta de entrada de cualquier asistente** (Cursor,
  Antigravity, Cascade, Claude Code…). No se archiva ni se reemplaza. Léelo, más
  `HANDOFF.md` y `CHANGELOG.md`, antes de tocar código. El canal PM/Dev está
  descripto en `AGENTS.md` §2.ter.
- **El trabajo que entra por `PARA-DEV.md` sigue estas reglas** (adversarial,
  rojo previo, producto e informe en commits separados, cada afirmación con su
  comando). El resto del repo sigue las reglas de `AGENTS.md`.
- **Carpetas read-only:** `viejo/`, `venv/`, `docs/archive/`. No se tocan.
- **Excepción vigente al push a `main`:** la regla
  `.cursor/rules/persistencia-github-al-dia.mdc` manda `git push origin main` tras
  cada cambio. **Para el trabajo del canal no aplica:** va a rama, y `main` es de
  Emi hasta que se confirme qué branch deploya Railway. Detalle en `AGENTS.md`
  §2.ter y en `DECISIONS.md`.
- **Restricciones firmes de esta etapa: no mergees, no deployes, no toques
  `main`.**

Si encontrás otra regla de este repositorio que choque con una del canal, **no
elijas**: listala con las dos versiones en tu informe y la decide la PM.

### Entorno que funciona

```bash
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
export PYTHONPATH=/home/user/cdi-vuce-
./venv/bin/python -m pytest tests/ -q --no-cov
```

Corré la suite **con `--no-cov`**. Sin eso la corrida puede comportarse distinto; y
la suite completa se colgaba para siempre hasta que se arregló el pool de
conexiones (`CHANGELOG.md`, `5917ae0`). Baseline medida al 2026-09-17 tras VUCE-2:
`4 failed, 670 passed, 102 skipped`. Los 4 rojos son preexistentes (3 del botón
auto_ncm, 1 de CSRF sobre Bearer) y están fuera de alcance salvo que se asignen.

---

## 7. Cómo trabajás vos, en concreto

- **Una sola tarea activa.** No mezclás piezas independientes.
- Por defecto, cada tarea es un **bloque vertical de 1–2 días** con un resultado
  demostrable de punta a punta.
- **Pagos, seguridad y datos se separan** en tareas propias: riesgo independiente.
- **Inspeccioná el flujo real antes de editar** y verificá después.
- **Si encontrás una mejora que no pidieron, proponela** con beneficio, esfuerzo,
  riesgo y cuándo conviene. No la implementes.
- **Frená y consultá** cuando: la premisa no se sostiene, el arreglo exige tocar
  algo fuera de alcance, o aparece riesgo para dinero, datos de clientes,
  seguridad, el servicio vivo o los 50 estudios. Ante la duda, **frená**.

### Verificación proporcional al riesgo

- **En cada entrega de producto:** conservás el rojo previo, agregás la regresión
  que discrimina, ejecutás los casos focales y **una** suite completa desde base
  limpia, y entregás SHA, salida y riesgos.
- **Cambio visual o de texto aislado:** caso focal + `compileall`.
- **Dinero, autenticación, permisos, migraciones, datos o cambio transversal:**
  suite completa sí o sí, y la revisa la PM aparte.
- Si toca backend, existe además el smoke de este repo
  (`scripts/testing/smoke_friccion.sh`, ver `AGENTS.md` §8). **Nunca afirmes que
  corriste una suite completa que no corriste.**

---

## 8. Tu primera tarea

Está en `docs/pm/PARA-DEV.md`. El historial del canal previo a la mudanza vive en
`Memu007/CDI`, `docs/pm/` (archivo histórico). **No necesitás permiso para
arrancar.**
