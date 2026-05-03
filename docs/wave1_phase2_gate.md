# Wave 2 (preparación) — Puerta de entrada para decisión PM

Este documento fija **qué debe pasar antes de financiar trabajo extra** mencionado en la visión PM: eventos previos al dashboard más ricos + mejor UX post‑`importador_no_match`.

No es fecha fija universal: usar **ventana con tráfico real** suficiente (orientativo **2 semanas piloto**, o hasta **≥ N sesiones/semana** donde N lo define el equipo según tamaño).

---

## Checklist A — datos mínimos

- [ ] `telemetry_rows_sampled` en **`/api/dev/wave1-kpis`** suficientemente alto para mirar proporciones sin saltar día a día (regla práctica interna ej. **≥ 150 eventos / ventana**, ajustá).
- [ ] Comparaste **usuarios únicos** `pdf_uploaded` vs `maria_generated` y documentaste gaps.
- [ ] Revisás ratio **`importador_no_match`** vs **`importador_auto_detected`** y si **`importador_quick_create_ok`** converge con feedback cualitativo (ver **[wave1_interview_kit](./wave1_interview_kit.md)**).

---

## Checklist B — feedback cualitativo mínimo

- [ ] Al menos **3** notas tipo entrevista (o soporte etiquetado) sobre importador nuevo / banner / cliente activo.

---

## Decisión sí/no Fase 2 (registrar fecha + responsable)

| Decisión si se cumplen A+B | Ejemplo siguiente build |
|---------------------------|-------------------------|
| **Sí**: extender onboarding pre‑dashboard (`register_completed` ya en landing como base; pueden faltar pasos intermedios más finos). | Lista de nuevos **nombres de evento únicos**, doc en PR. |
| **Sí**: iterar UX post‑sin‑match si “no encontré siguiente paso” o **clic rápido sin `…_ok`**. | Banner, tooltips, segundo CTA desde Clientes. |
| **No**: seguir recolectando; no abrir proyecto grande con números inestables. | — |

**Registro rápido (una línea al decidir):**  
[Fecha] [Nombre] Opción elegida · razón corta · link a snapshot KPI CSV/pantalla si hay.
