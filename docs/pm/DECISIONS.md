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
| **`main` es de Emi hasta que se sepa qué deploya** | 2026-09-17 | Excepción escrita a la regla «push a `main` tras cada cambio» de `CDI-vuce-`: se escribió cuando no había un servicio vivo atrás. El trabajo va a rama. Sale de vigencia cuando se confirme el branch de deploy en Railway |

---

## Pendientes de decisión de Emi

| Tema | Por qué hay que decidirlo | Impacto |
|---|---|---|
| **¿Qué branch deploya Railway?** | Si es `main`, mergear los 14 commits varados es un deploy | Destraba el merge y la excepción del push. Dato del dashboard de Railway, no del repo |
| **Rotación de la `GEMINI_API_KEY`** | Cierra G0 | Lo ejecuta Emi; la Dev no puede |
| **Alcance comercial del catálogo NCM** | 22 posiciones de las ~9.500 del Nomenclador Mercosur | Define qué se le promete a los 50 estudios |
| **Las cuatro preguntas del despachante** | `CARTUSO`, `IVAADICIONAL1`, código de banco, procedencia | Cierra parte de G4. Media hora con un despachante |
| **Precio y fecha de arranque de los 50** | El producto está cerca de poder cobrarse con alcance acotado | Comercial |
| **G7.3 — señal de impago** | El corte hoy es por calendario, no por señal de MP | Se decide con el costo que estima la Dev (VUCE-2). Descartarla es válido; dejarla sin decidir no |
