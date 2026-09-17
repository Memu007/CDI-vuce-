# Decisiones tomadas

Lo que está acá está decidido. Se puede discutir con evidencia, pero cambiarlo es
una decisión de Emi, no de la PM ni de la Dev. Lo que no sirve es empezar a
trabajar como si no estuviera decidido.

Mudado a `Memu007/CDI-vuce-` el 2026-09-17 (VUCE-2). Las decisiones específicas de
la línea `CDI` que no aplican acá quedaron en el archivo histórico de aquel
repositorio.

| Decisión | Fecha | En una línea |
|---|---|---|
| **AFIP/WSAA y VUCE quedan simulados** | 2026-09-04 | Excluidos del alcance por decisión de producto. No se auditan ni se trabajan |
| **El proceso PM/Dev es por archivos** | 2026-09-04 | La PM escribe en `PARA-DEV.md`, la Dev en `PARA-PM.md`. Ninguna edita el archivo de la otra. Si el informe no está en el repositorio, la entrega no ocurrió |
| **La PM no escribe código de producto** | 2026-09-04 | Sólo edita `docs/pm/`. Es la única revisión independiente que tiene el proyecto |
| **Aislamiento de datos antes de cobrar** | 2026-09-04 | No se onboardean los 50 estudios hasta que exista separación de datos por cliente. En esta línea ya está hecho (`owner_username`, `test_multitenant.py`) |
| **Verificación contra código, no contra informes** | 2026-09-04 | La documentación afirmaba métricas de calidad falsas. Una afirmación sin salida de comando pegada se trata como no hecha |
| **La revisión de seguridad completa es condición para desplegar** | 2026-09-04 | No se adelanta y no se saltea. Matiz: posponer la auditoría no es posponer un agujero ya encontrado |
| **Los términos comerciales no se versionan** | 2026-09-04 | Montos, márgenes y datos de clientes no entran al repositorio |
| **`CDI-vuce-` es la línea del producto** | 2026-09-16 | `Memu007/CDI` deja de trabajarse. Rama de trabajo: `claude/project-deploy-review-4nct96` |
| **Los dos procesos conviven** | 2026-09-17 | `AGENTS.md` de `CDI-vuce-` sigue siendo la puerta de entrada de cualquier asistente —Cursor, Antigravity, Cascade apuntan ahí—. Se le suma el canal PM/Dev en `docs/pm/` para el trabajo planificado. Ni se archiva su proceso ni se copia el nuestro entero. Ver `AGENTS.md` §2.ter |
| **`main` es de Emi — excepción permanente al push** | 2026-09-17 | Railway deploya de `main` con auto-deploy y «Wait for CI» apagado (verificado por Emi en el dashboard). Un push a `main` es un deploy inmediato. La excepción a la regla «push a `main` tras cada cambio» de `CDI-vuce-` es **permanente**, sin condición de salida. El trabajo del canal va a rama |
| **G7.3 — corte por calendario, no señal de impago** | 2026-09-17 | Para el MVP se descarta la señal de impago de MP (rama A). Se extiende el corte por vencimiento a los `active` con **7 días de gracia** (0 para `trial`). Motivo: con 50 estudios contratados un corte falso es peor que un mes gratis de más. Implementado en VUCE-3 |
| **El canal PM/Dev está partido** | 2026-09-17 | La PM no tiene push a `Memu007/CDI-vuce-` (403 del proxy). Escribe los bloques en `Memu007/CDI` y la Dev los mirrorea acá. Provisorio hasta resolver el permiso |

---

## Pendientes de decisión de Emi

| Tema | Por qué hay que decidirlo | Impacto |
|---|---|---|
| **Ventana para mergear los 14 commits** | Confirmado: Railway deploya de `main` sin esperar CI, así que el merge es un deploy inmediato | Lo elige Emi. La Dev no mergea ni deploya |
| **Rotación de la `GEMINI_API_KEY`** | Cierra G0 | Lo ejecuta Emi; la Dev no puede |
| **Alcance comercial del catálogo NCM** | 22 posiciones de las ~9.500 del Nomenclador Mercosur | Define qué se le promete a los 50 estudios |
| **Las cuatro preguntas del despachante** | `CARTUSO`, `IVAADICIONAL1`, código de banco, procedencia | Cierra parte de G4. Media hora con un despachante |
| **Precio y fecha de arranque de los 50** | El producto está cerca de poder cobrarse con alcance acotado | Comercial |
