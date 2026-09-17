# Estado y prioridades

**Última actualización:** 2026-09-17 (VUCE-2)
**Línea del producto:** `Memu007/CDI-vuce-`, rama `claude/project-deploy-review-4nct96`
**Desplegado:** Railway · `cdi-production.up.railway.app`
**Canal PM/Dev:** vive **acá** (`docs/pm/`) desde VUCE-2. El historial previo está
en `Memu007/CDI`, `docs/pm/` (archivo histórico).
**Plan:** `ROADMAP-MVP.md` (en el archivo histórico de `CDI`) · **Puertas:** `PROPUESTA-G1-G7.md` (íd.)

> Nota de mudanza: `ROADMAP-MVP.md`, `PROPUESTA-G1-G7.md` y `ALCANCE-Y-LIMITES.md`
> quedaron en el repositorio `CDI` y **no** estaban en la lista de archivos a mover
> de VUCE-2. Si la PM los quiere acá, se traen en una entrega aparte.

---

## Dónde estamos

**Cuatro de las siete puertas de deploy están cerradas** (G1, G2, G3 y, con VUCE-1,
G1 pasó a verde). Hay **50 estudios esperando para pagar**. Ya dijeron que sí.

---

## Las siete puertas

| Puerta | Estado | Qué falta | Quién |
|---|---|---|---|
| **G0 · Secretos** | 🟡 | Rotar la `GEMINI_API_KEY` | **Emi**, 10 min |
| **G1 · Configuración** | 🟢 | **Cerrada en VUCE-1: los 5 casos cortan, G1.5 incluido.** G1.6/G1.7 quedan como verificación manual | Hecho |
| **G2 · Imagen real** | 🟢 | Cerrada 2026-09-17: 16/16 en modo Docker | Hecho |
| **G3 · Aislamiento** | 🟢 | 22 bloqueados, 0 fugas. Abierto: no se corrió contra el servicio desplegado | Hecho |
| **G4 · Producto** | 🟡 | Pantallas + 4 preguntas al despachante + 1 bug | Producto |
| **G5 · Pruebas** | 🟡 | `4 failed, 671 passed, 102 skipped`. Los 4 rojos se diagnostican y limpian en VUCE-3 | Deuda acotada |
| **G6 · Rollback** | ⚪ | Railway conserva los deploys: volver atrás es un clic. Queda **demostrarlo y escribir el procedimiento**, no construir | Al deployar |
| **G7 · Cobro** | 🟡 | **7.1/7.2/7.4 demostradas en VUCE-2.** 7.3 decidido (corte por calendario + 7 días de gracia); se implementa en VUCE-3 | Semana 2 |

---

## Pendiente de Emi

1. **Rotar la `GEMINI_API_KEY`.** Cierra G0.
2. **Elegir la ventana para mergear los 14 commits.** Confirmado (2026-09-17):
   Railway deploya de `main` con auto-deploy y «Wait for CI» apagado, así que el
   merge es un **deploy inmediato**. No se mergea hasta que Emi elija la ventana.
3. **Conseguir al despachante.** Cuatro preguntas —`CARTUSO`, `IVAADICIONAL1`,
   código de banco, procedencia—, media hora.
4. **Resolver el permiso de push de la PM a `CDI-vuce-`** (hoy da 403). Mientras
   tanto la PM escribe en `CDI` y la Dev mirrorea.
5. **Decidir el alcance del catálogo NCM** y **confirmar el precio**.

---

## Lo próximo del lado técnico

1. **VUCE-3 (en curso):** cerrar el agujero de cobro (corte de `active` vencido con
   7 días de gracia), averiguar el listado admin por estado de cobro, y limpiar los
   4 rojos de la suite.
2. **G6 · Rollback** (demostrar el clic de Railway y escribir el procedimiento, no
   construir) y el bug de procedencia ≠ origen.
3. **Mergear los 14 commits varados** — es un deploy; espera la ventana de Emi.
4. **Recorrido de producto propio** — el `recorrido.py` de `CDI` no se mudó (era
   específico de aquella línea). Falta un equivalente o apoyarse en
   `scripts/testing/smoke_friccion.sh`.

---

## Lo que no se toca

- `main` de `CDI-vuce-`: no se mergea ni se pushea. Railway deploya de `main`, así
  que hacerlo es un deploy — decisión de Emi.
- `Memu007/CDI` (las dos ramas): ya no es el producto. Es archivo histórico.
- Integraciones AFIP/WSAA y VUCE: excluidas por decisión de producto.
- Carpetas read-only de este repo: `viejo/`, `venv/`, `docs/archive/`.
- Los reportes de estado viejos: no son fuente de verdad. Se verifica contra el
  código y contra una corrida.
