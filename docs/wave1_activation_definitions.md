# Wave 1 — Definiciones de “usuario activado” (para alinear equipo)

Este documento no reemplaza un OK formal de stakeholders: sirve como **lista de opciones**, con la que el equipo elige una definición oficial para reportes hasta la próxima revisión.

Referencia técnica: el backend expone todas las vistas simultáneas en **`GET /api/dev/wave1-kpis`** bajo las claves `activation` y `activation_unique_users_aliases` para la ventana móvil (días parametrizables). La base muestra **`database_window`** cuentas creadas y verificadas en la misma ventana de tiempo (`users.created_at`), independiente del evento frontend.

---

## Opciones típicas (negocio)

| ID | Definición en castellano | Fuente recomendada | Limitación práctica |
|----|--------------------------|--------------------|---------------------|
| **A · Cuenta nueva** | “En el período apareció como usuario nuevo en el sistema”. | Panel: `database_window.new_accounts_in_window` (+ verificados si aplica: `…verified_in_window`) | Cubre alta aun si el usuario **no llegó al dashboard**. No mide uso. |
| **B · Ingresó a la app v2** | “Abrió el dashboard lo suficiente como para disparar `session_start` con sesión”. | Panel: usuarios únicos con acción **`session_start`** | No distingue “miró solo” vs “intentó trabajo”. |
| **C · Ingresó vía landing** | “Completó login o registro con sesión inmediata (telemetría landing)”. | Acciones **`login_completed`**, **`register_completed`** (+ **`register_pending_verify`** si cuenta como iniciado onboarding) | `register_pending_verify` suele ir **sin usuario logueado** (solo cuenta de eventos, no personas únicas). |
| **D · Intención con documento real** | “Intentó cargar PDF en el período”. | Acción **`pdf_uploaded`** usuarios únicos | Incluye fallos después del upload si el paso llegó hasta `pdf_uploaded`. |
| **E · Paso crítico de datos** | “Confirmó revisión”. | **`review_confirmed`** usuarios únicos | Proxie de seriedad antes de NCM/generación. |
| **F · Valor hasta archivo** | “Generó MARIA (TXT) en algún momento del período”. | **`maria_generated`** usuarios únicos | Alineado a **resultado tangible** pero excluye quien llegó muy cerca y abandonó antes. |

---

## Recomendación operativa Wave 1 (borrador para votar/rechazar)

- **North Star provisional:** **F (`maria_generated` únicos con sesión)** como “valor entregado” en demos y pilotos donde el archivo es lo que cuenta.
- **Leading indicator (“empujar producto”)** · **D (`pdf_uploaded` únicos)** — mide funnel más arriba.
- **Crecimiento funnel** · **A** (cuentas DB en ventana) para marketing vs producto sin confundir con uso.

Registrar en Slack/doc la decisión: *desde fecha X usamos definición oficial Y para KPI semanal.*

---

## Cómo reconciliar discrepancias

- **DB cuentas > telemetría login:** esperable si usuarios abandonan después del mail / antes de cargar SPA.
- **Muchos `session_start` pero pocos PDF:** problema de onboarding o audiencia equivocada.
- **`register_pending_verify` alto vs `register_completed` bajo:** flujo está “encallado” en verificación mail.
- Comparar cualitativamente con **[wave1_interview_kit.md](./wave1_interview_kit.md)**.
