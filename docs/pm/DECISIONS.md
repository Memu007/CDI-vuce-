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
| ~~Los dos procesos conviven~~ | 2026-09-17 | **Reemplazada el 2026-10-06** por «Reglas en un solo lugar» (abajo). Texto original en Git |
| ~~`main` es de Emi — excepción permanente al push~~ | 2026-09-17 | **Absorbida el 2026-10-06** por «Reglas en un solo lugar»: ya no es una excepción, es la regla para todos. Railway publica `main` sin esperar CI |
| **G7.3 — corte por calendario, no señal de impago** | 2026-09-17 | Para el MVP se descarta la señal de impago de MP (rama A). Se extiende el corte por vencimiento a los `active` con **7 días de gracia** (0 para `trial`). Motivo: con 50 estudios contratados un corte falso es peor que un mes gratis de más. Implementado en VUCE-3 |
| ~~El canal PM/Dev está partido~~ | 2026-09-17 | **Resuelta el 2026-10-06:** la PM tiene push a `CDI-vuce-`. El canal vive sólo acá |
| **Se cobra sólo con tarjeta, por ahora** | 2026-09-18 | Emi. Los estudios se suscriben por el checkout de Mercado Pago; no hay alta manual ni transferencia. Toda la plata pasa por un flujo que nadie probó de punta a punta: probarlo es parte de la puerta G7 |
| **Forma de trabajo: el método del Second Brain** | 2026-10-06 | Emi. PM principal + Dev 1, con canales, rutinas, subagentes, consejero y «dale» para publicar (`Memu007/ynerasecondbrain`). Se puede sumar una Dev 2 (y una PM visual) cuando haya cola visual: pasos en `NOW.md`, «Sumar una Dev» |
| **Nada sin plan aprobado** | 2026-10-06 | Emi. Ninguna tarea a la Dev ni avance por cuenta propia sin un plan que Emi aprobó. Primero auditoría, después roadmap |
| **Reglas en un solo lugar, congeladas** | 2026-10-06 | Emi: «limpiá las rules de ese proyecto así quedan fijas». `AGENTS.md` es la única fuente; los archivos de cada herramienta sólo apuntan ahí. Resuelve cuatro choques: (1) «push a `main` tras cada cambio» pasa a «siempre a rama; `main` sólo con el «dale» de Emi», para todos los asistentes; (2) «arreglar sin pedir permiso» de `.agent/rules` pierde contra «nada sin plan aprobado»; (3) la alerta de contexto al 70-80 % se reemplaza por compactar al 50 % (Devs) y 60 % (PMs); (4) el equipo virtual de 6 roles queda sólo para chats sueltos con otros asistentes. `NOW.md` es el único documento de estado; `HANDOFF.md` describe el producto. Congeladas hasta el 2026-10-27 salvo que algo se rompa |
| **Límites propios del proyecto** | 2026-10-06 | Decidido por la PM (Emi puede revertirlo): los de `ONBOARDING-PM.md`, «Límites que no se negocian», que juntan los de septiembre (`ALCANCE-Y-LIMITES.md` de `CDI`) con los de la instalación |
| **`Memu007/CDI` queda como archivo** | 2026-10-06 | La instalación del método que se hizo ahí por error (copia de abril) se descarta, incluido el trabajo a medias de CI-PUERTA-1. Su `docs/pm` apunta acá |
| **Fechas y precio de septiembre, vencidos** | 2026-10-06 | Emi: las fechas del plan se rehacen y el precio quedó viejo (no se escribe acá). Producción la usa sólo Emi: no hay estudios reales adentro |
| **Roadmap aprobado** | 2026-10-07 | Emi: «apruebo». Las semanas se cuentan desde el 2026-10-07. El orden lo cambió Emi el mismo día (fila siguiente) |
| **Orden: primero el TXT, después el cobro, la seguridad al final** | 2026-10-07 | Emi: «dale con ese orden, dejamos seguridad para el final, bien exhaustivo así ya está todo terminado, pero prioridad es el PDF». `ROADMAP.md` rehecho: Fase 1 TXT, Fase 2 cobro, Fase 3 seguridad y datos con auditoría final, Fase 4 piloto. Condiciones de la PM, dichas a Emi: la publicación de ensayo sigue (cierra la fuga); Emi revisa los usuarios de prueba y las variables de Railway; **ningún estudio entra antes de cerrar la Fase 3** |
| **Dos Devs** | 2026-10-07 | Emi: «dale 2 devs, lo que haga mejor el proyecto». El reparto de piezas está en `ROADMAP.md`. Sin PM visual: a las dos las revisa la PM principal |
| **Lo que pueden usar las Devs** | 2026-10-07 | Emi: «que las devs tengan acceso a todo menos el advisor, que es tuyo, y subagentes nunca pueden usar fable, y cada dev fijate que max de esfuerzo sea alto». Las Devs: todas las herramientas, sin consejero; su sesión y sus subagentes, hasta esfuerzo alto. **Nadie** lanza un subagente con Fable, tampoco la PM |
| **Compactar antes: 30 % las Devs, 40 % las PMs** | 2026-10-07 | Emi: «dale 30/40» (antes, 50 y 60, sin razón escrita). Cada paso relee toda la memoria del chat y las tres sesiones comparten el plan. Excepción al congelamiento de reglas, por decisión de Emi. Se revisa el 2026-10-27 con lo que usa cada pieza |
| **CDI no usa Google Cloud** | 2026-10-07 | Emi: «no podemos rearmar esas cosas, es un proyecto muy viejo». `cloudbuild.yaml` se borra en LIMPIEZA-1. El sitio es sólo Railway |
| **Producción tiene datos reales** | 2026-10-07 | Emi cargó facturas reales en el sitio publicado. La fuga de MARIA.TXT (S1) pedía sesión iniciada: si en producción no hay cuentas de otras personas, nadie pudo usarla. Lo confirma Emi en Railway antes del ensayo |
| **Publicación de ensayo** | 2026-10-07 | Emi: «dale». Se publica la rama de trabajo más las reglas nuevas. El «dale» final va para el SHA exacto, de día y con los chequeos de Railway hechos |
| **Empresa de digitalización, por operación** | 2026-10-07 | El despachante (2026-10-06, 22:15): «se selecciona en cada operación»; Lakaut = `PSAD01`, Modoc = `PSAD06`, como en los dos archivos reales. Se elige como el banco: en cada operación, con la última usada propuesta. Va en MARIA-4 |
| **La reducción del IVA adicional no va en el TXT** | 2026-10-07 | El despachante (2026-10-06, 22:12): es la ventaja `IVAADREDUCCION` del menú «Ventajas» del Kit, que elige él cuando sabe que corresponde; elegirla mal es una infracción grave. Ningún archivo real trae ventajas. CDI no la pone: avisa que se elige en el Kit. Va en MARIA-4 |

---

## Pendientes de decisión de Emi

| Tema | Por qué hay que decidirlo | Impacto |
|---|---|---|
| **Rotar las claves de Gemini** | Una estuvo en un repositorio público. Cierra G0 | Lo hace Emi en Google AI Studio y Railway |
| **«Dale» para el SHA de la publicación de ensayo** | Hecho: Emi, 2026-10-07 09:52 ARG, «dale 5cb03ab»; publicado 12:53 UTC como avance directo de `main` | Falta la verificación de Emi (`NOW.md`, «Para Emi» 1) |
| **Prender «Wait for CI» en Railway** | Hoy Railway publica aunque las pruebas fallen | Es un ajuste de Railway; no cuesta nada |
| **Qué se promete del catálogo NCM** | Hoy hay 10.226 posiciones (cargadas en julio de 2026 desde el nomenclador de ARCA del 19/12/2018: le falta la enmienda de 2022; D21 de la Dev 1), no 22 | Cambia el discurso comercial de septiembre |
| **Actualizar el catálogo NCM al nomenclador vigente** | El de CDI es de 2018 (sin la enmienda de 2022: 8517.13.00, 8524, 8549). Por eso «no está en el catálogo» avisa en vez de frenar | Emi, 2026-10-07 09:35 ARG: lo baja la PM. Desde acá la red bloquea `www.arca.gob.ar`, `www.afip.gob.ar` y `www.mercosur.int` (también para WebFetch). Ojo: el catálogo de julio ya salió del `arancel.zip` oficial (`ncm_arca_metadata.json`) y adentro venía `nomenclador_19122018.txt`, así que el ZIP de ARCA puede seguir siendo el viejo. Se le ofreció a Emi habilitar `www.arca.gob.ar` en el entorno o adjuntar el archivo. La PM compara el SHA-256 con `d14605c9…` y el nombre de adentro: si es el mismo, la fuente es otra (lista del Mercosur) y hace falta un lector nuevo. Falta que Emi diga si entra como pieza (propuesta: Dev 1, después de MARIA-1b). La PM no corre `import_arancel_nomenclador.py`: lo importa la Dev con prueba |
| **Los dos favores del despachante** | Respondió las seis preguntas y las dos cortas el 2026-10-06 (`PREGUNTAS-DESPACHANTE.md`). Faltan sus archivos reales y, al cerrar la Fase 1, la prueba en su Kit | MARIA-6 y la prueba en el Kit, que cierra G4 |
| **Precio y fecha de arranque** | Vencidos | Comercial; no se escriben acá |
