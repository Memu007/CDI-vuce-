# Wave 1 — Kit de entrevistas (3–5 conversaciones cortas)

Objetivo: validar hipótesis de producto (**importador + PDF**) y pegar etiquetas cualitativas a lo que muestra **`/api/dev/wave1-kpis`** (y el bloque Wave 1 en `/dev/dashboard`).

---

## Antes del llamado

1. Abrí la consola de desarrollo (`/dev/dashboard`) estando logueado (misma cuenta que usás para soporte si aplica) y anotá el bloque Wave 1 en pantalla o el JSON de `/api/dev/wave1-kpis`: **AUTO-DETECT OK**, **AUTO-DETECT SIN MATCH**, **DEMO VS PDF**, y la sección **Activación** cuando esté cargada.
2. Fecha del piloto y ventana (**14 días** por defecto). Si ves pocos **EVENTOS**, los números son ruidosos; priorizá notas verbatim sobre fricción.

---

## Contraste cualitativo ↔ panel

| Feedback típico | Qué mirar en el panel / API |
|-----------------|----------------------------|
| “No encontré dónde subir PDF” | Bajo **`pdf_uploaded`** vs **`upload_simulated`** alto (demo vs real); preguntás por **screen_start**/`session_start` sólo indirectamente. |
| “Me cambió el cliente y no quería” | Deberías ver más **`importador_pdf_matches_other_kept_activo`** (no auto-swap post Wave1). Si igual se quejan, registrar bug o copy. |
| “Me confundió el importador nuevo” | Picos en **`importador_no_match`**; si usaron el banner, **`importador_quick_create_clicked`** vs **`…_ok`** (ratio clic → éxito). |
| “Me quedé en crear cuenta” | **`register_pending_verify`** vs **`register_completed`**; DB **`new_accounts_in_window`**. |

---

## Guion corto (10–15 min)

1. Contexto sin jerga: “Estamos mejorando cargar MARIA desde PDF”.
2. Tarea dirigida **una sola vez**: cargar PDF que traigan **o** simular solo si tienen tema de seguridad — anotás cuál hicieron.
3. Pensar en voz alta: donde frene 3 seg., pedí ‘¿Qué esperabas?’
4. Cierre sobre confianza: “¿Harías uno urgente esta semana sí/más o menos/no?”.

Usá las **cinco preguntas** de checklist en **[wave1_invitation.md](./wave1_invitation.md)** al final como encuesta rápida (sí/medio/no).

---

## Plantilla de notas (copiar/pegar)

- Participante rol:
- PDF real / simular:
- ¿Encontró subir archivo? sí/medio/no
- ¿Entendió importador nuevo si apareció? sí/medio/no
- ¿Llegó hasta revisión/generación? hasta dónde
- Fricción verbatim (una frase):
- vs panel antes/después fecha X: AUTO-DETECT OK __ SIN MATCH __ DEMO% __ MARIA_USERS __ PDF_USERS __ 

---

## Criterio de “listo esta tanda”

Cerradas **3 sesiones grabadas/notas**, y **actualizado snapshot** Wave 1 al mismo día (para correlación fecha).
