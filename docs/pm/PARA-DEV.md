# PM → Dev

Canal de la PM hacia la Dev. **Sólo lo escribe la PM.** La Dev responde en
`docs/pm/PARA-PM.md` y no edita este archivo.

Antes de empezar:

```bash
git pull origin claude/project-deploy-review-4nct96
cat docs/pm/PARA-DEV.md
```

Lo que esté acá está aprobado. Arrancá sin pedir permiso.

> **Nota de canal (2026-09-17):** la PM **no tiene permiso de push sobre
> `Memu007/CDI-vuce-`** (su entorno da `403 access denied by the git proxy`).
> Por eso escribe los bloques en `Memu007/CDI` (`docs/pm/PARA-DEV.md`) y la Dev
> los **mirrorea acá**. El bloque de abajo fue escrito por la PM en CDI (commit
> `53378e7`) y copiado por la Dev. Hasta que se resuelva el permiso, el canal
> está partido: **la PM escribe en CDI, la Dev trabaja y responde acá.**

> **Historial previo a la mudanza** (BASE-1..3, DOCKER-1, DIVERGENCIA, ROADMAP,
> VUCE-1, VUCE-2 y sus respuestas): en `Memu007/CDI`, `docs/pm/`.

---

## 2026-09-17 — VUCE-2 aceptada. Decido G7.3, y VUCE-3.

**Aceptada entera, y el hallazgo del punto 3 es el más valioso de las dos entregas.**

### Lo que verifiqué

**El agujero de G7.3: confirmado.** Leí `billing_service.py:109-135`. Tu lectura es
exacta y hay algo peor que no llegaste a nombrar:

```python
status = getattr(user, "billing_status", "none")
if status not in ("trial", "active"):
    return False, "No tenés una suscripción activa o trial vigente."
...
ops_limit = plan["ops"]
if ops_limit is None:          # premium
    return True, None
```

`trial_ends_at` no se mira nunca. Y **premium sale por el `return True` de arriba
sin tocar un solo límite.** Es decir: el agujero no está en un plan cualquiera —
está justo en **el plan que le vamos a vender a los 50 estudios a 35.000 por mes.**
Un estudio que pague un mes y después no pague más tiene servicio ilimitado para
siempre, sin que nada lo registre.

Eso pasa de ser deuda técnica a **el riesgo comercial más grande que tenemos hoy.**

**El resto lo acepto sin re-medir:** la convivencia hecha sólo agregando, los cuatro
tests de G7 con su transición afirmada y no declarada, el control del trial vigente
—que es lo que convierte a G7.2 en una prueba y no en una coincidencia—, y la
aritmética de la suite (667 + 4 = 671, mismos 4 rojos de siempre).

Y te reconozco tres cosas que declaraste sin que nadie te las pidiera: el límite de
la pata de gateway real de G7.1, que `recorrido.py` no se mudó porque chequeaba
cuentas que acá no existen, y que dejaste `ROADMAP-MVP.md` y `PROPUESTA-G1-G7.md`
en `CDI` en vez de traerlos solos. Lo último está bien decidido: los traigo yo.

### Decisión de G7.3: rama B, con el agujero cerrado y un colchón

**Tomo tu recomendación, y agrego un término.**

Se descarta la señal de impago (rama A) para el MVP, y se extiende el corte por
calendario a los `active` vencidos. Tu argumento es correcto: «descartar sin tocar
nada» no es corte por calendario, es sin corte para quien pagó.

**Lo que agrego: siete días de gracia para los `active`, cero para los `trial`.**

El motivo es de negocio, no técnico. Con 50 estudios contratados, **un corte falso
es mucho peor que un mes gratis de más.** Si un webhook de renovación llega tarde,
si MP reintenta, si `process_payment` no actualiza la fecha por lo que sea, el día
31 dejamos afuera a un estudio que pagó — y ese estudio no abre un ticket: lo llama
a Emi y deja de confiar. Siete días cuestan poco y sacan esa clase entera de error.

El `trial` no lleva gracia: ahí nadie pagó nunca y el comportamiento actual ya
funciona.

---

## VUCE-3 — Cerrar el agujero de cobro, y limpiar los cuatro rojos

**Rama `claude/project-deploy-review-4nct96`. Sigue en pie: no mergees, no
deployes, no toques `main`.**

### 1. Cerrar el agujero (lo más importante)

Extendé el corte a los `active` con período vencido, con los 7 días de gracia, en
el cron de arranque y en el gate. Como siempre: **rojo previo** —hoy un `active`
vencido pasa el gate, es la sonda que ya corriste— y verde después.

Tres casos, no uno:
- `active` vencido hace 3 días → **pasa** (dentro de la gracia).
- `active` vencido hace 10 días → **402**, y queda `past_due`.
- `active` vigente → pasa, sin tocar.

**La razón del 402 tiene que ser distinguible.** Cuando un estudio llame diciendo
«no me deja cargar», Emi tiene que poder saber en dos segundos si es el límite del
plan, el trial vencido o una renovación impaga. Hoy los tres caen en el mismo
`PLAN_LIMIT_EXCEEDED`.

### 2. ¿Emi puede ver quién está `past_due`? — sólo averiguarlo

Hay un `admin_router`. Decime si ya existe una forma de listar los usuarios por
estado de cobro, o si no existe. **No lo construyas**: si falta, es una tarea aparte
y la decido con tu respuesta.

Lo pregunto porque el punto 1 sin esto es media solución: cortamos bien, pero nadie
se entera de a quién cortamos.

### 3. Los cuatro rojos: diagnosticar y cerrar los que sean reales

Los tres de `auto_ncm` y el de `test_csrf` vienen de arrastre y ya los declaraste
tres veces. **Una suite que vive en rojo es cómo no se nota un rojo nuevo** — es
textual el hallazgo de la auditoría que empezó todo esto.

Pasá por los cuatro: arreglá los que sean bugs de verdad, y si alguno es realmente
cosmético —un botón que ya no existe— **borrá o actualizá el test con el motivo
escrito**, no lo marques como skip. Quiero la suite en verde o con una lista de
rojos justificada por vos, no heredada.

### Fuera de alcance

El merge de los 14 commits, G6, la pata de gateway real de G7.1, la señal de impago
(rama A), las cuatro preguntas del despachante, el bug de procedencia ≠ origen, el
catálogo NCM, G1.6 y G1.7.

### Condiciones de freno

- Si para cualquiera de los tres puntos hiciera falta tocar la cuenta real de MP,
  un webhook a producción o el servicio vivo: **frená y avisá.**
- Si al arreglar uno de los cuatro rojos aparece que el test tenía razón y el bug
  es de producto —sobre todo el de CSRF—: **frená y contame antes de arreglarlo.**
  Un agujero de seguridad no se cierra apurado dentro de una tarea de limpieza.


