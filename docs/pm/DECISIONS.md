# Decisiones tomadas

Lo que está acá está decidido. Se puede discutir con evidencia, pero cambiarlo es
una decisión de Emi, no de la PM ni de la Dev. Lo que no sirve es empezar a
trabajar como si no estuviera decidido.

Mudado a `Memu007/CDI-vuce-` el 2026-09-17 (VUCE-2). Las decisiones específicas de
la línea `CDI` que no aplican acá quedaron en el archivo histórico de aquel
repositorio.

| Decisión | Fecha | En una línea |
|---|---|---|
| **EMAIL-1 y CONEXIONES-1 entran al roadmap** | 2026-10-28 | Emi: «1 sí, 2 sí». EMAIL-1: el email se busca y se controla sin distinguir mayúsculas; los pares que ya haya en producción no se tocan hasta que Emi los cuente. CONEXIONES-1: medir si quedan conexiones a la base tomadas y arreglar sólo si pasa. Las dos de la Dev MARIA, Fase 3, después de ABUSO-1 |
| **DESPACHO-1 entra al roadmap** | 2026-10-28 | Emi: «Sí, hay que sumarlo»: subir despachos ya oficializados para armar y editar el catálogo de cada cliente y poder bajarlo. Pieza de la Dev MARIA en la Fase 1c, después de ORG-1; espera un despacho de ejemplo del despachante. No arma TXT ni operación |
| **Emi autoriza guardar las tres ramas de esta retoma en GitHub** | 2026-10-20 | Ante la pregunta explícita de guardar las ramas del resumen sin modificar el sitio, Emi respondió «dale. y. anotalo asi. la prox. pm sabe». Abarca `codex/pm-retoma-txt` (incluida esta nota y el cierre PM), `codex/maria5d-unit-kg` (`254531b`) y `codex/doc1-block-invalid-pdf` (`fe0a101`) en `Memu007/CDI-vuce-`, y sus borradores de revisión. No volver a pedir permiso para este guardado ya autorizado. No autoriza fusionar a main, desplegar en Railway ni aceptar precisión del lector real. |
| **DOC-1: bloquear el TXT incorrecto; no sumar exportación completa** | 2026-10-19 | Emi eligió «Primero bloquear el TXT incorrecto» al decidir sobre EC02. Reconocer/rechazar documentos no admitidos y frenar destinaciones EC* en el flujo de importación. Sin generar exportaciones, inventar factura ni cambiar campos del formato MARIA. |
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
| **Compactar: 60 % las Devs, 50 % las PMs, y las tres antes de dormir** | 2026-10-07 (tarde) | Emi, con lo medido hoy: una pieza de Dev gasta 26 a 33 puntos (con 30 % se compactaba después de cada pieza); la PM sube ~7 puntos por hora. El corte de la cuenta de anoche pasó sin nadie que compactara, con las Devs cerca del 40 %; ahora Emi compacta las tres antes de dormir (la PM le pasa los textos a eso de las 20:30). Nadie se frena esperando el `/compact`, y vale el porcentaje de `get_session`. Si la cuenta vuelve a llegar a su límite, ese día se vuelve a 30 y 40 (pasó el 2026-10-07 a las ~18:34 UTC: ese día, 30/40). Antes: 30/40 (2026-10-07, mañana) y 50/60 | Se revisa el 2026-10-27 |
| **CDI no usa Google Cloud** | 2026-10-07 | Emi: «no podemos rearmar esas cosas, es un proyecto muy viejo». `cloudbuild.yaml` se borra en LIMPIEZA-1. El sitio es sólo Railway |
| **Producción tiene datos reales** | 2026-10-07 | Emi cargó facturas reales en el sitio publicado. La fuga de MARIA.TXT (S1) pedía sesión iniciada: si en producción no hay cuentas de otras personas, nadie pudo usarla. Lo confirma Emi en Railway antes del ensayo |
| **Publicación de ensayo** | 2026-10-07 | Emi: «dale». Se publica la rama de trabajo más las reglas nuevas. El «dale» final va para el SHA exacto, de día y con los chequeos de Railway hechos |
| **GUARDAR-1 entra** | 2026-10-07, ~15:27 ARG | Emi, «dale a todo» a la lista de la PM. Pieza de la Dev 1, antes que COBRO-MP-1, que queda en pausa en `83b4ec1` |
| **El caso habitual de Emi es reventa** | 2026-10-07, ~15:27 ARG | Emi, ídem. El IVA adicional por defecto, `NO_VALIDA` (MARIA-4), es el que corresponde; se cambia por operación o por producto |
| **Subítems en la pantalla (D24)** | 2026-10-07, ~15:27 ARG | Emi, ídem: sus facturas traen subítems. Entra SUBITEMS-1 (Dev 2), después de CATALOGO-NCM-1 y antes de MARIA-6 |
| **La suscripción de Mercado Pago está configurada** | 2026-10-07, ~15:27 ARG | Emi: las variables `MP_PREAPPROVAL_PLAN_ID_*` están en Railway. Las renovaciones de COBRO-MP-1 corren en producción |
| **Los subítems no se guardan con la operación, por ahora** | 2026-10-07 | La PM, por la D27 de la Dev 2: hoy la v2 no reabre operaciones del historial, así que no se pierde nada a la vista. Si entra «reabrir una operación», esa pieza lleva la columna y la migración (también para el estado de MARIA-4) |
| **D32 de la Dev 1: (b), sin migración** | 2026-10-07 | La PM, con lo medido contra Postgres. Agrandar la columna no reescribe la tabla, pero necesita `lock_timeout`, da `InvalidCachedStatementError` en el solapamiento del despliegue y no alcanza solo (el upsert no actualiza el `ncm`). Gana la SIM del proveedor si empieza con los 8 dígitos del cliente: GUARDAR-2 |
| **Empresa de digitalización, por operación** | 2026-10-07 | El despachante (2026-10-06, 22:15): «se selecciona en cada operación»; Lakaut = `PSAD01`, Modoc = `PSAD06`, como en los dos archivos reales. Se elige como el banco: en cada operación, con la última usada propuesta. Va en MARIA-4 |
| **La reducción del IVA adicional no va en el TXT** | 2026-10-07 | El despachante (2026-10-06, 22:12): es la ventaja `IVAADREDUCCION` del menú «Ventajas» del Kit, que elige él cuando sabe que corresponde; elegirla mal es una infracción grave. Ningún archivo real trae ventajas. CDI no la pone: avisa que se elige en el Kit. Va en MARIA-4 |

---

## Compatibilidad necesaria de Excel — decidido por PM, 2026-10-21

La suite limpia del candidato `8b19662` encontró cuatro fallos de mapeo:
FastAPI 0.155 interpreta un booleano Form omitido como False aunque su
default sea True (cambio documentado desde 0.147 en sus
[notas oficiales](https://fastapi.tiangolo.com/release-notes/)). Por eso el
endpoint ignoraba las columnas guardadas del cliente. Mismos casos pasan en
entorno heredado y fallan en limpio; no es contaminación de orden.

Dentro del cierre de Fase 1, se autoriza la corrección mínima para conservar
el contrato de `/upload_excel_v2/`: omitido usa el mapeo, False explícito lo
omite, valores válidos conservan su semántica e inválidos dan 422. No se
cambian requisitos, otras rutas ni política comercial. Debe traer negativos,
revisión PM y suite completa en limpio sobre el SHA corregido. No autoriza
publicación; el candidato anterior queda rechazado para publicar.

## Pendientes de decisión de Emi

### Publicación de la candidata Fase 1 autorizada — 2026-10-21

Emi: «publica. y contonua», en respuesta al cierre de la candidata
`166395f99c0011aa46f55f82afa3734c97576150` (1612 pruebas aprobadas).
Autoriza subir la candidata, abrir su PR a main y publicarla después de las
puertas pendientes. No volver a pedir permiso para ese mismo producto.
Se permiten los commits posteriores de documentación según ONBOARDING-PM,
demostrando diff de producto vacío. Si una puerta falla, corregir y verificar
antes de fusionar; no dar por verde la prueba automática de navegador.
La continuación sigue en Fase 1 con revisión separada de EXCEL-2/GUARDAR-2.

| Tema | Por qué hay que decidirlo | Impacto |
|---|---|---|
| **Rotar las claves de Gemini** | Una estuvo en un repositorio público. Cierra G0 | Lo hace Emi en Google AI Studio y Railway |
| **«Dale» para el SHA de la publicación de ensayo** | Hecho: Emi, 2026-10-07 09:52 ARG, «dale 5cb03ab»; publicado 12:53 UTC como avance directo de `main` | Verificado por Emi: «Billing cron» 0 y una operación guardada |
| **Prender «Wait for CI» en Railway** | Hoy Railway publica aunque las pruebas fallen | Es un ajuste de Railway; no cuesta nada |
| **Qué se promete del catálogo NCM** | Hoy hay 10.226 posiciones (cargadas en julio de 2026 desde el nomenclador de ARCA del 19/12/2018: le falta la enmienda de 2022; D21 de la Dev 1), no 22 | Cambia el discurso comercial de septiembre |
| **Actualizar el catálogo NCM al nomenclador vigente** | Hecho el pedido: Emi trajo el `arancel.zip` de ARCA el 2026-10-07 (`nomenclador_07102026.txt`, 10.504 NCM, con la enmienda de 2022; en `docs/pm/datos/`). Entra como CATALOGO-NCM-1 (Dev 2, después de MARIA-5): la PM lo tomó como aprobado por Emi al traer el archivo | Si Emi no quería la pieza, la saca del ROADMAP |
| **Los dos favores del despachante** | Respondió las seis preguntas y las dos cortas el 2026-10-06 (`PREGUNTAS-DESPACHANTE.md`). Faltan sus archivos reales y, al cerrar la Fase 1, la prueba en su Kit | MARIA-6 y la prueba en el Kit, que cierra G4 |
| **La pantalla vieja (v1) y `/generate_maria_export`** | Desde MARIA-5, el TXT de la v2 calcula el peso por línea y los centavos con decimales exactos; la v1 manda el total en float (un centavo de diferencia) y la exportación (`core/maria_generator_export.py`, sólo la llama la v1) sigue con el reparto en float y el peso de una unidad. MARIA-1b (D22 a) sólo le suma la limpieza de textos | Emi decide más adelante si la v1 y la exportación se borran (no está en el roadmap). Mientras, el camino es la v2 |
| **«Dale» para el SHA de la segunda publicación (`6ea8ca9`)** | Hecho: Emi, 2026-10-07 ~16:58 ARG, «dale 6ea8ca9»; publicado 19:58 UTC como avance directo de `main`. Antes, su «dale a todo» lo frenó el sistema de permisos de la sesión | Emi: un TXT real «se ve bien», generado un minuto después del push; falta confirmar que era la versión nueva |
| **«Dale» para el SHA de la tercera publicación (`a9b03cf`)** | Hecho: Emi, 2026-10-07 ~18:35 ARG, «dale a9b03cf» (GUARDAR-1); publicado 21:35 UTC como avance directo de `main` | Falta que Emi guarde una operación con la SIM completa |
| **Precio y fecha de arranque** | Vencidos | Comercial; no se escriben acá |


## 2026-10-23 — Medición de tiempo EXCEL-2 y cobertura (PM)

No se cambia el test ni el timeout30s del producto. La suite con cobertura
sobre0666881 dio5fallos:4regresiones de subítems corregidas enbe17e1b y el
test8concurrente (40031.4s). Repetir sólo ese test instrumentado, aislado,
reprodujo40031.5s. El mismo test sin instrumentación dio20022.6s y pasó en
CI, que ya usa--no-cov. La cobertura global de la corrida roja fue52.67%,
supera38%; no es un resultado funcional aprobado.

Se ejecuta la suite completa final sin instrumentación comoCI, sin excluir
casos ni modificarpytest.ini. El nuevo producto obliga a repetir la puerta;
no se trata de repetir hasta verde el mismoSHA. Si el caso falla también
sin cobertura, se devuelve por concurrencia; no se eleva timeout. Registrar
ambos resultados y el margen limitado, no afirmar fluidez universal.

## 2026-10-24 — Método al día con el secondbrain (Emi)

Emi: «Leé CAMBIOS.md del secondbrain y aplicá lo que falte». Se aplican las
entradas del 2026-10-06 al 2026-10-21. **Reemplaza la fila de compactar del
2026-10-07 (tarde):** cada sesión se compacta sola con `/autocompact 200k`
(Emi lo escribe una vez en cada chat); salen el umbral 60/50 %, la ronda de
las 23:55 UTC y el «Contexto: ~X %». Timbres por `send_message`, no por
`fire_trigger`. No se aplican, por decisiones anteriores de Emi: el consejero
para las Devs, Fable como subagente y el «muy alto» para las Devs.


## 2026-10-24 — Reunión de prueba con el despachante (Emi)

El TXT de una factura real entró al MARIA después de doce correcciones a
mano (detalle en `PARA-DEV-2.md`). Acuerdos de la reunión (notas de la
reunión, sin datos del cliente):

- Ajustes a incluir, ajustes a deducir y FOB casillero: campos que carga el
  usuario; el sistema hace las cuentas, no decide qué se descuenta (Emi). El
  reparto detallado ítem por ítem va en una segunda etapa (PRORRATEO-1).
  PM (2026-10-24, D1 de EXCEL-3): el Excel devuelve `operacion.descuento`
  positivo (lo que se deduce), sólo leído y avisado; VALOR-1 lo ofrece como
  ajuste a deducir.
- Botón para calcular el seguro (1 % de FOB + flete) cuando la factura no lo
  trae.
- Montos con punto o con coma.
- Cliente: sólo lo que pide el MARIA (CUIT, razón social, domicilio, fecha
  de inicio de actividades).
  PM (2026-10-24, D2 de CLIENTE-1): esos cuatro van a la vista y con aviso
  si faltan, no obligatorios al guardar; el TXT los controla al generarse.
  PM (2026-10-24, D3 de CLIENTE-1): editar un cliente no borra una fecha de
  inicio guardada en otro formato; la pantalla no la manda si el campo
  quedó vacío. La fecha va al TXT en DD/MM/AAAA (MARIA-7, punto 9).
- CUIT del despachante por estudio, cargado una vez y elegido en la
  operación.
- «NCM» pasa a «Posición arancelaria (PA SIM)» en pantallas.
- Sufijos y unidad estadística desde VUCE según la posición SIM; lo que la
  IA encuentra en la factura (marca, modelo, código, medidas, color) los
  completa; lo que falta queda marcado para el despachante. Cada renglón
  de la factura es un subítem con su código de artículo propio. En el TXT,
  sólo letras, números y espacios dentro de los sufijos.
- Tres destinos: comercialización en el mercado interno, bien de uso de la
  empresa, bien de uso particular.
- Reordenar los productos arrastrando.
- Peso neto desde el packing list (lo manda el despachante).
- Dos semanas de desarrollo y pruebas con el despachante cada 15 días.
- Fuera de CDI por ahora: el bot de turnos portuarios.

Emi (2026-10-24): Codex deja de trabajar en CDI; la PM principal arma dos
Devs nuevas en Claude: Dev MARIA en esfuerzo alto y Dev técnica en medio.
Roadmap nuevo a tres meses en `ROADMAP.md`: **aprobado por Emi el 2026-10-24** («Dale. Comenzá»). Emi (2026-10-24): la lectura de fechas año/mes/día entra en MARIA-7 (punto 8).

## 2026-10-25 — Base del seguro sugerido (PM, D13 de VALOR-1)

Decidido por la PM: hasta PRORRATEO-1, el botón «Calcular seguro» calcula
el 1 % sobre el FOB de la factura más el flete, no sobre el FOB casillero.
Así el TXT no lleva un FOB sin ajustes con un seguro calculado con ajustes.
Se revierte con una constante (`BASE_SEGURO_SUGERIDO`) cuando el casillero
vaya al TXT. Pregunta 3 al despachante en `PREGUNTAS-DESPACHANTE.md`.

## 2026-10-25 — Fechas de inicio y la prueba de aislamiento (PM, D15–D17 de CLIENTE-1b)

Decidido por la PM:
- D15 (b) y D16 (b): la fecha de inicio que se copia desde la operación y la de
  la importación masiva se validan con la misma función que el alta y la
  edición. Una que no sirve no se copia o queda vacía, y el informe de la
  importación lo dice. Va como pieza chica, CLIENTE-1c. No se usa un
  `@validates` en el modelo.
- D17 (a): la Dev técnica arregla `ataque_aislamiento.sh` (el sufijo «01» que
  la API rechaza desde MARIA-7), en un commit aparte.

## 2026-10-25 — El sufijo general que nadie usa (PM, D18 de MARIA-9)

Decidido por la PM: D18 (b). Si ningún sub-ítem ni renglón toma el sufijo
de valor de la operación, no se valida nada de él (tampoco `=`, caracteres
de control ni el largo) y `/generate_maria/avisos` no avisa por él. Es
seguro porque el general sólo se escribe en `CSBTSVL` y siempre pasa por
`limpiar_sufijo`. Cuando alguno lo toma, los controles siguen igual. Va en
VALOR-1c.

## 2026-10-25 — Un monto ilegible no viaja como 0 (PM, D19 de SEPARADORES-1)

Decidido por la PM: D19 (b). Si la pantalla no puede leer el flete, el
seguro o un ajuste, el pedido lleva el texto tal cual y el servidor lo
rechaza con un mensaje claro; nunca un 0 silencioso. Es la segunda red: la
pantalla ya no deja generar con un monto ilegible. Va en SEPARADORES-1b,
junto con la familia «separador y tres dígitos sin miles bien formados»,
que pasa a ser ambigua en la factura y en la pantalla (no en los precios).

## 2026-10-25 — Los sufijos salen del arancel de ARCA (PM, D22 de SUFIJOS-1)

Decidido por la PM: D22 (a). En el repositorio no hay ruta ni respuesta
guardada de VUCE `/cice/sufijos`; escribir el lector sería inventar la
forma. SUFIJOS-1 toma los sufijos y la unidad estadística del arancel de
ARCA del 07/10/2026 (`docs/pm/datos/`), en una tabla local con su fecha a
la vista; lo que no está se marca para el despachante. VUCE va en una pieza
aparte cuando Emi guarde una respuesta real. Se le cuenta a Emi; se puede
revertir.

## 2026-10-25 — Un ajuste ilegible frena el seguro calculado; ceros adelante, aparte (PM, D20 y D21 de SEPARADORES-1b)

Decidido por la PM. D20 (a): con el seguro calculado por el sistema, un
ajuste que no se lee da 400 hasta corregirlo o elegir «Dejar el seguro como
está»; sin el seguro calculado, se dice en las cuentas y no frena. D21 (b):
el cero adelante y los grupos de miles mal formados en la factura, el
«en blanco» distinto entre pantalla y servidor y la pregunta que sugiere
tres decimales van en SEPARADORES-1c, después de SUFIJOS-1. Son de antes o
piden saltearse la revisión.

## 2026-10-27 — Gana el sufijo que escribió la persona; aviso del sufijo vacío (PM, H5 y D23 de SUFIJOS-1)

Decidido por la PM. H5: la propuesta del arancel no pisa un AA, AB o AI que
el despachante escribió en el sufijo de la operación; sólo agrega los
códigos que faltan y, si propone otro valor, lo avisa en la fila. D23 (c):
si todos los productos tienen sufijo propio, el de la operación vacío no
frena, pero se avisa junto al botón. Las dos van en la vuelta de SUFIJOS-1.

## 2026-10-28 — D28 a D34 de la Dev MARIA (PM)

Decidido por la PM; el texto entero está en `git show 02d28b1:docs/pm/PARA-DEV-2.md`.
D28 (a): el golden de 2025 no se toca; las pruebas comparan todo salvo el
`MCPL` de `GANANCIASOP3`, que dice `USOPAR` (se reabre si la pregunta 7 dice
otra cosa). D29 (a): `PIDE_NUMERO = ("Z",)`; los decimales de los `Z` van en
la pregunta 10. D30 (a): SEGURO-1 avisa y no frena; frenar es SEGURO-2, para
Emi. D31 (a): el catálogo guarda sólo lo que ya tiene columna. D32 (a):
borrar un cliente borra sus presupuestos compartidos, en la misma
transacción. D33 (a): el cargador de `ncm_historial_*.json` no cambia; si se
rescatan los de producción lo decide Emi al publicar DISCO-1. D34 (a):
OBSERVABILIDAD-1 sólo crea la columna y su índice.

## 2026-10-28 — D35 a D37 de la Dev MARIA (PM)

Decidido por la PM; el texto entero está en `git show 1f648c3:docs/pm/PARA-DEV-2.md`.
D35 (1) en las cinco, para ABUSO-1: (a) un solo helper de IP para
`login_attempts`, `reset_attempts` y slowapi, la última de X-Forwarded-For y
log obligatorio en el 429 del login; (b) los números de la Dev; (c) los
mensajes quedan y la enumeración figura mitigada, no cerrada; (d) sin sesión
sólo tres acciones en lista explícita; (e) los contadores de login y
recuperación van a una tabla con incremento atómico, tamaño acotado y
migración `_migrate_*` en commit propio. D36 y D37 (2) por ahora; sus (1)
son EMAIL-1 y CONEXIONES-1, que Emi aprobó.

## 2026-10-28 — OBSERVABILIDAD-1: la métrica guarda el molde de la ruta (PM)

Decidido por la PM, amplía la D34 (a). Al volver a grabar la métrica, la
pieza dejaba en `api_logs` (y en `/api/dev/stats`) el camino crudo, con
tokens de invitación, hashes de presupuestos públicos y CUIT. Se guarda el
molde de la ruta, y `<sin ruta>` si no coincide ninguna. Sin eso,
OBSERVABILIDAD-1 no se publica. Evidencia en
`REPRODUCCION-OBSERVABILIDAD-1-2026-10-28.md`.

## 2026-10-28 — ORG-1: la pendiente de un email con cuenta no ocupa lugar (PM)

Decidido por la PM, generaliza la D40. Una invitación pendiente cuyo email
ya tiene cuenta en CDI (en cualquier estudio o en ninguno) no se puede usar
y no cuenta para el tope de usuarios del estudio. Evidencia en
`REPRODUCCION-ORG-1-D40-2026-10-28.md`.

## 2026-10-28 — EXCEL-2b: el historial liviano de sugerir es del despachante; D32 (b) como EXCEL-2c (PM)

`/api/ncm/sugerir` muestra el historial liviano (`load_ncm_historial`) del
despachante a cualquiera de sus clientes, con `source: historial`. Queda
así: es el historial del propio usuario, ya existía y el NCM depende del
producto. Lo que es de un cliente (`scope: cliente`) no se le muestra a
otro. D32: (b), libros chicos pero caros al carril pesado por una medida
previa a leer, como pieza aparte EXCEL-2c al final de la cola de la Dev
técnica. Topes de entorno: un valor que no da un tope usable (no finito,
no positivo o 0 en bytes) usa el defecto.

## 2026-10-28 — Rutinas de las Devs cada 3 horas (Emi)

Emi, 28/10 («Dale»): las rutinas de la Dev MARIA y de la Dev técnica pasan
de cada hora a cada 3 horas (minutos 35 y 15). La de la PM principal sigue
cada hora. El canal principal son los avisos entre sesiones (la Dev avisa
al entregar; la PM la despierta con el veredicto); la vuelta horaria de la
PM es la red que despierta a una Dev parada. Se vuelve atrás con
`update_trigger`.

## 2026-10-28 — Pausa hasta el sábado 31/10 (Emi)

Emi, 28/10: «frenemos todo hasta el sábado (si están haciendo algo que lo
terminen)», por el uso y una entrega de otro proyecto. Las rutinas de la PM
principal y de las dos Devs quedan apagadas. Cada Dev termina la pieza en
curso, sube el informe y frena; la PM no revisa hasta retomar. Se retoma
cuando Emi lo diga, prendiendo las rutinas con `update_trigger`.

## 2026-10-28 — Se levanta la pausa (Emi)

Emi, 28/10 a la noche: «volver a trabajar tranqui», porque su entrega del
otro proyecto pasó al martes. Se prenden de nuevo las tres rutinas con la
misma frecuencia (PM cada hora, Devs cada 3 horas).

## 2026-10-28 — Sin apurar: calidad antes que velocidad (Emi)

Emi preguntó si el plan de tres meses podía hacerse en un mes y medio. La PM
(con el advisor) contestó que el código puede adelantarse pero el calendario
depende del despachante, de Emi y de los estudios, y que apurar baja la
calidad y sube el uso. Emi: «seguimos así… que no se adelanten, que vamos
tranqui. Si se estira un poquito más, no hay problema… pero que no se salten
nada. Prioridad es tener un código que se sienta hecho por un senior».
Queda escrito arriba de `PARA-DEV.md` y `PARA-DEV-2.md` («Ritmo y calidad»).
Las fechas se re-estiman después de la primera sesión con el despachante.

## 2026-10-29 — Pausa hasta el domingo 1/11 (Emi)

Emi, 29/10 a la mañana: «frenamos hasta el domingo con el proyecto». Las
rutinas de la PM principal y de las dos Devs quedan apagadas. Cada Dev frena
ya: corta lo que corre en segundo plano y sube lo que tenga a medias como
trabajo en curso, sin entregar. La PM no revisa hasta retomar. Se retoma
cuando Emi lo diga, prendiendo las rutinas con `update_trigger`.

## 2026-11-04 — Se retoma por 3 días, con corte por uso (Emi)

Emi, 04/11 a las 18:36 de Argentina: «Continua por 3 días … revisa el
secondbrain que cambiamos cosas, actualizate vos y a las devs y arranca. Si
ves que en 2 días o menos llega al 50% de uso del límite semanal corta». Se
trabaja hasta el **sábado 07/11, ~18:30 de Argentina**. Si el uso semanal
llega al 50 % antes del viernes 06/11 a las ~18:30, la PM corta todo:
apaga las tres rutinas, frena a las Devs y le avisa a Emi. La PM no ve un
porcentaje exacto: mira en cada vuelta el estado del límite de cada sesión
(`get_session`) y le pide a Emi que avise si su pantalla marca 50 %.

## 2026-11-04 — Método al día con el secondbrain hasta 2026-10-31 (PM)

Se aplican las entradas de `CAMBIOS.md` del 2026-10-22 al 2026-10-31, como
el 2026-10-24 (mismo pedido de Emi: «actualizate»). Entra `CLAUDE.md` §6
(código como lo dejaría una senior) con `herramientas/chequeo-6.py`
(producto `proyecto_maria/`; arnés `scripts/testing/` y `tests/`), el camino
de hoy para sumar código, los sabotajes vencidos, `COLA-LIMPIEZA.md` y un
canal por Dev; sale la medición a mano de subagentes y consejero. **Reemplaza
la fila «Rutinas de las Devs cada 3 horas» del 2026-10-28:** las tres
rutinas pasan a cada 2 horas de 8 a 22 y a las 2 y a las 5 de Argentina (PM
minuto 55, técnica 15, MARIA 35); son menos vueltas que antes en total (la
PM bajaba de 24 a 10 por día). Siguen sin aplicarse el consejero para las
Devs, Fable como subagente y el «muy alto» para las Devs.

## 2026-11-04 — Respuestas de Emi a lo pendiente (Emi)

Emi, 04/11 ~19:10 de Argentina. **Claves:** las cambia ella más adelante,
«ahora está en prueba»; sigue pendiente. **`8b45207`** (publicada el 24/10):
la probó y funciona bien. **Seguridad del cobro:** «si vamos a cobrar por
Mercado Pago, sí; hay que hacer los webhooks y todo lo que haga falta»:
entra COBRO-MP-3 (técnica, después de COBRO-MP-2). **Arreglos chicos de
seguridad:** sí: CSRF-1 (técnica: telemetría v2 con CSRF y el logout, D16
b). **Pieza por la descripción larga que se pierde:** sí: CATALOGO-LARGO-1
(MARIA, después de RENDIMIENTO-1c). **SEGURO-2:** sí (D30 b; MARIA, después
de SUFIJOS-2 y SEGURO-1). **Re-estimar fechas:** sí: dos semanas más, el
piloto cierra el 07/02 (`ROADMAP.md`). Orden de las colas: decidido por la
PM.

**2026-11-05 21:41 UTC, Emi en el chat de la PM principal:** «CATALOGO-LARGO-2
sí, dale». Entra en la cola de MARIA después de SESION-1, como estaba
propuesta.

## 2026-10-28 — D38 y D39 de la Dev MARIA (PM)

Decidido por la PM; el texto entero está en `git show d79a8b8:docs/pm/PARA-DEV-2.md`.
D38 (1): con email exacto, esa cuenta; con varias y ninguna exacta, ninguna,
con la misma respuesta que si no existe. El índice sobre `lower(email)` espera
el conteo de Emi en producción. D39 (1): los números de 40 logins malos a la
vez van a riesgos de CONEXIONES-1; la medición de 60 a 100 se propone a Emi.

## 2026-11-06 — CATALOGO-LARGO-2: devolución y D76 a D81 (PM)

Vuelve por tres causas nuevas de la pieza: un NUL o medio par rompe el lote
entero en PG, una fila vieja queda duplicada y sin editar, y la migración puede
trabarse con `guardar-uso` y loguea antes del commit. D79 (a) en la vuelta.
D76, D77, D78 y D80 van a Emi como pieza CATALOGO-3, recomendada. D81 queda:
escapar el `value` va a la cola de limpieza.

## 2026-11-06 — RESET-1 aceptada, D82 y D83, RESET-2 y la limpieza integrada (PM)

RESET-1 aceptada sobre `02a21e7`, sin integrar. D82 (a): pedir un link nuevo
no mata los anteriores. D83 (a): `_archived_test_email` no barre links. RESET-2
sumada por la PM («a cero»): el link vuelve en la respuesta sólo en el entorno
de prueba. La limpieza del repositorio (`07e7b5f`) se integra en `dd052d4`
tras suite y sabotajes de CSRF-2 y COBRO-MP-1 en verde sobre `27b19d9`;
cierra D60 (se retira la v1).

### 2026-11-06 11:20 UTC (PM)

COBRO-CORTE-1 aceptada sobre `ca50916`, sin integrar (debajo hay piezas
técnicas sin aceptar desde `e0b8626`). Cuatro bajas a la cola de limpieza.
La validación de 60 s que cruza cargas (`finalize.js:103-108`, de antes) se
propone a Emi como pieza nueva.

### 2026-11-06 11:40 UTC (PM)

COBRO-MP-2 con devolución sobre `4f1822f`. D62 (a): una pausada de otro
miembro frena el checkout con 409, como una autorizada; la lista de estados
que pagan va en un solo lugar. Sacar del estudio sólo se frena por la que paga.


### 2026-11-06 12:06 UTC (Emi)

Sí a la pieza nueva VALIDACION-1 (Dev técnica, después de COBRO-MP-2): la
validación de una carga nunca muestra ni guarda lo de otra.

### 2026-11-06 12:35 UTC (PM principal)

CATALOGO-LARGO-2 aceptada sobre `d5bc7c1` (pruebas `b0bbd8c`), sin integrar por `e0b8626`. D84 a D87 (a); el aviso de qué producto no se aprendió va a CATALOGO-3. Acta: `REPRODUCCION-CATALOGO-LARGO-2-v2-2026-11-06.md`.

### 2026-11-06 14:40 UTC (PM principal)

PYPDF-1 aceptada sobre `974263e`, sin integrar por `e0b8626`: pypdf 6.21.4 como mínimo, sin fijar una versión vieja. D89 (a) y D90 (a). Acta: `REPRODUCCION-PYPDF-1-2026-11-06.md`.

### 2026-11-06 15:00 UTC (PM principal)

RESET-2 aceptada sobre `99d3f69`, sin integrar por `e0b8626`. D93 (a). D91/D92, decidido por la PM bajo «arreglos chicos de seguridad a cero» (Emi): pieza ENTORNO-1 para MARIA después de ABUSO-1; con `ENVIRONMENT` ausente o desconocido no se abre ninguna puerta de desarrollo. A Emi: confirmar que Railway tiene `ENVIRONMENT=production` exacto. Acta: `REPRODUCCION-RESET-2-2026-11-06.md`.

### 2026-11-06 15:57 UTC (PM principal)

Corte por la regla de Emi del 04/11: las tres sesiones muestran el límite semanal en `allowed_warning` antes del 06/11 21:30 UTC. Rutinas de la PM, MARIA y técnica apagadas (`enabled false`); las dos Devs frenadas con un mensaje; el control de las 21:30 también apagado. Retomar sólo con Emi.

### 2026-11-07 15:50 UTC (PM principal)

Emi: «Podés trabajar con el team por 24hs … 24 y cortar (si hay algo haciéndose se termina)». Rutinas de PM, MARIA y técnica prendidas otra vez; Devs despertadas en su orden. Corte el 2026-11-08 15:50 UTC (`trig_01QwEeyuXBFBx6LErxqapwRh`): rutinas apagadas, cada Dev termina el paso en curso, sube y anota dónde quedó. `allowed_warning` ya no corta (Emi decidió seguir sabiéndolo).

### 2026-11-07 18:15 UTC (PM principal)

ABUSO-1 aceptada sobre `55bf408`, sin integrar por `e0b8626`; supuestos 1 a 3 de MARIA aceptados. D94 (a), D95 (a), D96 (a), decididas por la PM. Piezas nuevas bajo «arreglos chicos de seguridad a cero» (Emi): ENTRADAS-1 (ningún texto de afuera da 500: surrogate/NUL en claves y registro, claves de más de 72 bytes, cuerpo no UTF-8, `NaN` en el 422) y ABUSO-2 (un login bueno en otra cuenta no borra el contador de la IP; el tope de recuperar usuario cuenta como PG). Orden de MARIA: ENTORNO-1 → ENTRADAS-1 → ABUSO-2. Rojo intermitente de `test_despacho1b` a la cola. Acta: `REPRODUCCION-ABUSO-1-2026-11-07.md`.

### 2026-11-07 19:20 UTC (PM principal)

ENTORNO-1 aceptada sobre `83085e4`, sin integrar por `e0b8626`; supuestos S1 a S4 aceptados. D97 (a) y D98 (a), decididas por la PM: pieza nueva ENTORNO-2 (MARIA, después de ABUSO-2) bajo «arreglos chicos de seguridad a cero» (Emi). D99 a Emi: si producción arrancó alguna vez sin `ENVIRONMENT=production`, pueden existir `demo`/`premium`/`basico`; ver usuarios. Acta: `REPRODUCCION-ENTORNO-1-2026-11-07.md`.

### 2026-11-07 20:45 UTC (PM principal)

ENTRADAS-1: devolución sólo de pruebas sobre `589fd0b`; producto sin cambios, supuestos S1 a S6 aceptados. Decididas por la PM: D100 (a) pieza FRONT-422; D101 (a) dentro de ENTRADAS-2; D102 (a) chore de fijar `bcrypt`; D103 (a) cola de limpieza; D104 (a) pieza nueva ENTRADAS-2 (operación manual, clientes, NUL en parámetros de ruta, agrupar con más ítems que el driver), bajo «arreglos chicos de seguridad a cero».

### 2026-11-07 22:10 UTC (PM principal)

COBRO-MP-2 vuelta + COBRO-MP-3: devolución de pruebas sobre `cb740f3` (firma, quién toca a quién, plazo único) y un texto falso al cancelar con el PUT abandonado. D64 (a): antes de publicar, Emi configura Webhooks con secreto en MP y carga `MP_WEBHOOK_SECRET` en Railway, y prueba en sandbox. D66 (a): el límite de avisos queda por `get_client_ip`; cambiar `core/rate_limit.py` sería pieza aparte. Acta: `REPRODUCCION-COBRO-MP-2-3-2026-11-07.md`.

### 2026-11-07 22:40 UTC (PM principal)

ABUSO-2: devolución sólo de pruebas sobre `8ad47ee`; producto sin cambios. D105 (a), decidida por la PM: el tope de recuperar por cuenta queda así y va como riesgo (un mail menos por hora para quien pidió; contar también por IP reabre el salto con muchas IPs).

### 2026-11-07 22:55 UTC (PM principal)

Rojo de `despacho1b` aceptado sobre `d69233c` (sólo prueba, sin integrar). D106 (a), decidida por la PM: el resto del tope para entender el texto queda sin mínimo propio; riesgo, con el tope de producción son 2 s en un proceso con poca memoria.

### 2026-11-07 23:15 UTC (PM principal)

ENTRADAS-1 aceptada sobre `c839197` (vuelta sólo de pruebas), sin integrar porque la rama lleva debajo piezas en devolución.

### 2026-11-08 00:10 UTC (PM principal)

ABUSO-2 aceptada sobre `1f79a8e` (vuelta sólo de pruebas; producto `8ad47ee`), sin integrar porque la rama lleva debajo piezas en devolución. Riesgo decidido por la PM: el `delete` de lo propio por prefijo no tiene prueba; hoy no tiene camino.

### 2026-11-08 01:12 UTC (PM principal)

ENTORNO-2 aceptada sobre `bf92bf9`, sin integrar. D107 decidida por la PM: (a), pieza ENTORNO-3 de MARIA después de ENTRADAS-2 (FRONTEND_URL, ALLOWED_ORIGINS, HSTS y el pase de rate limit de 127.0.0.1 con la regla de `es_desarrollo()`), dentro de «arreglos chicos de seguridad a cero» (Emi). Riesgo para publicar: Railway necesita `ENVIRONMENT=production` exacto (D99).

### 2026-11-08 01:54 UTC (PM principal)

FRONT-422 aceptada sobre `4dbdb0b`, sin integrar. D108 decidida por la PM: (a), el 422 se traduce en el front (`static/errores.js`); el contrato de la API no cambia.

### 2026-11-08 03:55 UTC (PM principal)

ENTRADAS-2 aceptada sobre `b8aa9bd`, sin integrar. D109 (a) y D110 (a), decididas por la PM: pieza ENTRADAS-3 de MARIA después de ENTORNO-3 (lo que quedó afuera de ENTRADAS-2 más el `1e308` que se guarda y rompe la suma de clientes y métricas), dentro de «arreglos chicos de seguridad a cero» (Emi). Acta: `REPRODUCCION-ENTRADAS-2-2026-11-08.md`.

### 2026-11-08 05:00 UTC (PM principal)

ENTORNO-3 aceptada sobre `fd545c1`, sin integrar. Decididas por la PM: D111 (a), el limitador por ruta sin montar va a la cola de limpieza; D112 (c) y D113 (b), pieza ENTORNO-4 de MARIA tras ENTRADAS-3 (sin `FRONTEND_URL` no arranca fuera de desarrollo; `billing_service.py` usa la misma URL). La D112 de la Dev técnica (COBRO-MP-2+3) se registra como D114. Riesgo para publicar: mirar en Railway `ENVIRONMENT`, `ALLOWED_ORIGINS` y `FRONTEND_URL` (D99).

### 2026-11-08 05:35 UTC (PM principal)

COBRO-MP-2+3 vuelta 2 (`71e15df`): devolución. Camino real: quien abrió la suscripción queda trabada tras un 503 de cancelar en el que MP sí canceló (el permiso se decide con el estado de MP posterior). D112 de la Dev técnica registrada como D114: el reintento concilia para quien recibió el 503, dentro de esta pieza (no hace falta COBRO-MP-4). Más casos de firma (cada posición, dos `v1=`), textos de 503, plazo único con varias suscripciones y reactivar con sid que no paga. Numeración única de D: MARIA D115, técnica D116.

### 2026-11-08 05:45 UTC (PM principal)

AISLAMIENTO-2 y LIMPIEZA-1 aceptadas sobre `c86f3ff`, sin integrar. D116 (b), decidido por la PM dentro de «arreglos chicos de seguridad» de Emi: pieza PERMISOS-1 de la Dev técnica (el arranque da admin por email de `ADMIN_USERNAMES` y el email se cambia sin verificar). El registro con invitación sin comparar email ya es ORG-1. Próxima D libre: D117 (MARIA ya tiene D115 reservada).

### 2026-11-08 05:56 UTC (PM principal)

ENTRADAS-3 aceptada sobre `cf5309a`, sin integrar. D115 (a), decidido por la PM: el tope frena lo nuevo; una fila vieja enorme se limpia a mano si aparece, pasando por Emi (dato de producción). D117 (a), decidido por la PM: pieza ENTRADAS-4 (NUL en campos `Form`), después de ENTORNO-4. La D117 de MARIA queda; la técnica toma la próxima libre (D118 en adelante).

### 2026-11-08 07:11 UTC (PM principal)

ENTORNO-4 aceptada sobre `44b9759`, sin integrar. Publicarla pide `FRONTEND_URL` en Railway antes (sin ella no arranca): va a la lista de Emi junto con `ENVIRONMENT=production` y `ALLOWED_ORIGINS`.

### 2026-11-08 07:52 UTC (PM principal)

ENTRADAS-4 aceptada sobre `6baddb5`, sin integrar. Supuesto de la Dev aceptado: un `cliente_id` con NUL se trata como cliente inexistente (200 sin mapeo), no 422.

### 2026-11-08 08:59 UTC (PM principal)

EXCEL-2c aceptada sobre `c2b84f1`, sin integrar. D122 (a), decidido por la PM bajo «arreglos chicos de seguridad» (Emi): pieza EXCEL-2d, tope al `formatCode` antes de abrir; lleva también el sabotaje de `excel2.sh` que dejó sin patrón EXCEL-3b (`522e082`). Próxima D libre: D123.

### 2026-11-08 10:10 UTC (PM principal)

SUFIJOS-2+SEGURO-1 aceptada sobre `ad2d0f8`, sin integrar. Decidida por la PM: D123 (a), pieza chica AVISOS-1 de MARIA después de SEGURO-2 (el rechazo de exportación después de limpiar los textos, en avisos y en generar). Riesgos sin tocar: `31/02/2026` pasa como fecha; `٥` frena con el mensaje de «vacío». Próxima D libre: D124.

### 2026-11-08 11:55 UTC (PM principal)

Decididas por la PM sobre el informe de `ca84c5f` (técnica): D119 (b) → pieza COBRO-MP-4 (anotar quién recibió el 503 de cancelar; migración); D120 (b) → pieza PERMISOS-2 después (sólo roles guardados dan admin; el registro rechaza nombres de `ADMIN_USERNAMES`; la cuenta de Emi sigue admin tras reiniciar); D121 (a) → cola de limpieza, y Emi revisa los roles admin guardados en producción. El veredicto de `ca84c5f` espera sus sabotajes.

### 2026-11-08 12:05 UTC (PM principal)

EXCEL-2d aceptada sobre `84fd9f2`, sin integrar. D124 (a), decidida por la PM: la CI instala `xlwt` para las pruebas (sin `xlwt` los casos `.xls` se saltean sin rojo), en un commit aparte de la entrega de COBRO-MP-4. Próxima D libre: D125.

### 2026-11-08 12:30 UTC (PM principal)

COBRO-MP-2+3 (vuelta 3), PERMISOS-1 y BACKUP-1a aceptadas sobre `ca84c5f`, sin integrar. Cuatro guiones de sabotaje con falla 0; `cobro_mp2.sh` entero sobre `ca84c5f`. Riesgo para confiar la copia de producción: la verificación del backup no compara índices, FK, objetos grandes ni secuencias.

### 2026-11-08 13:30 UTC (PM principal)

COBRO-MP-4 (con D124) aceptada sobre `0fb991c`, sin integrar (`REPRODUCCION-COBRO-MP-4-2026-11-08.md`). Decidido por la PM: el hueco de prueba del orden de cancelar (mutación del desempate verde) va como primer paso de PERMISOS-2, en un commit de pruebas aparte.

### 2026-11-08 13:40 UTC (PM principal)

SEGURO-2 aceptada sobre `d160738`, sin integrar (`REPRODUCCION-SEGURO-2-2026-11-08.md`). Decididas por la PM: D125 (a), D126 (a); AVISOS-1 suma el texto falso de «no pudimos leerlo» tras calcular y pasar a CIF, y el motivo del 400 que no se ve en la revisión.

### 2026-11-08 14:10 UTC (PM principal)

PERMISOS-2 aceptada sobre `a1db966`, sin integrar (`REPRODUCCION-PERMISOS-2-2026-11-08.md`). Decidido por la PM: PERMISOS-3 (el `\n` final y las mayúsculas que esquivan la reserva de `ADMIN_USERNAMES`) sigue en la técnica. La cuenta demo admin fuera de `ENVIRONMENT=production` refuerza la D99 para Emi.

### 2026-11-08 14:45 UTC (PM principal)

PERMISOS-3 aceptada sobre `9428e00`, sin integrar (`REPRODUCCION-PERMISOS-3-2026-11-08.md`). Decidido por la PM: D127 (b), nombres únicos sin mayúsculas para todas las cuentas como pieza aparte, propuesta a Emi después de mirar producción. La técnica sigue con el arnés `separadores1b.sh` de la cola de limpieza hasta el corte.

### 2026-11-08 15:12 UTC (PM principal)

AVISOS-1 aceptada sobre `0aed334` y SEPARADORES-1b-ARNÉS sobre `1063b32`, sin integrar (sus `REPRODUCCION-…-2026-11-08.md`). Decididas por la PM: D129 (a), predicado único antes de limpiar; D130 (a), pieza AVISOS-2 de MARIA después de EMAIL-1, con tres bajas del adversario (texto enorme, texto del 400 en FOB, exportación con destinación de importación).

### 2026-11-08 15:50 UTC (PM principal)

Corte de las 24 h que dio Emi el 07/11 a las 15:50 UTC. Apagadas las rutinas de PM, MARIA y técnica (`enabled=false`). Las dos Devs frenaron con commit y push: técnica en `65af1d3`, MARIA en `cf68314` con EMAIL-1 entregada y sin revisar. Al retomar: revisar EMAIL-1, contestar D131 y D132 y volver a prender las tres rutinas.

### 2026-11-08 17:05 UTC (PM principal, con Emi)

Emi: «Trabaja 12 horas mas». Vuelven las tres rutinas; corte el 2026-11-09 a las 05:00 UTC (trig_01QwEeyuXBFBx6LErxqapwRh, mismo procedimiento). La técnica no tenía piezas en la lista; Emi eligió NOMBRES-1 (D127 b): nombres únicos sin mayúsculas para todas las cuentas, sin tocar las que ya existen, así que no hace falta mirar producción.

### 2026-11-08 17:40 UTC (PM principal)

EMAIL-1 (D45) aceptada sin producto. D132 (a), decidida por la PM bajo «arreglos chicos de seguridad»: RESET-3, tope por cuenta al pedir el reset, después de AVISOS-2. D131 (a) va a Emi: mirar la collation de la base de producción, una consulta de sólo lectura.

### 2026-11-08 18:40 UTC (PM principal)

NOMBRES-1 aceptada sobre `1960a9a` (producto `ccded98`, +4/−2). Escape de la PM en la vuelta 1: el acta decía «PG 16» y corrió en SQLite porque `tests/conftest.py` pisa `DATABASE_URL`; corregido, y el riesgo va a la cola de limpieza. La carrera de altas simultáneas queda como límite conocido; el índice sobre `lower(username)` va con Emi. CONEXIONES-1 pasa de MARIA a la técnica, decidido por la PM (pieza de base y servidor; MARIA tiene cuatro por delante).

### 2026-11-08 19:35 UTC (PM principal)

AVISOS-2 aceptada sobre `4db641b`, sin integrar. D133 (a) y D135 (a) → AVISOS-2b de MARIA antes de RESET-3, con el hueco `IC_4` de mi negativo. D136: la rama de MARIA y la mía (con la técnica) chocan en 5 archivos de producto con conductas aceptadas distintas; la integración es la pieza INTEGRAR-1 de la técnica, antes de CONEXIONES-1, con cada choque de fondo como D para la PM. MARIA no trae mi rama hasta que INTEGRAR-1 esté aceptada.

### 2026-11-08 20:58 UTC (PM principal)

AVISOS-2b aceptada sobre `aa115f4`, sin integrar (D136). D137 (a): el smoke quedó viejo desde ABUSO-1; se ajusta el script a que los eventos sin sesión se rechazan (pieza chica SMOKE-1 de MARIA, después de RESET-3). Escape mío: le mandé a MARIA por mensaje un orden distinto del canal; manda el canal.

### 2026-11-08 21:40 UTC (PM principal)

RESET-3 aceptada sobre `8fda3d2`, sin integrar (D136). D138 (a), decidida por la PM: el tope por cuenta puede dejar a la cuenta sin links una hora, igual que recuperar. Riesgos bajos del adversario (ventana fija, emails viejos repetidos en mayúsculas) quedan anotados en el acta. MARIA ya entregó SMOKE-1.

### 2026-11-08 21:55 UTC (PM principal)

SMOKE-1 aceptada sobre `00df4de`, sin integrar (D136): el smoke espera el rechazo sin sesión; sabotajes en rojo. MARIA sigue OBSERVABILIDAD-1. Numeración: MARIA D139, técnica D140 en adelante.

### 2026-11-09 05:00 UTC (PM principal)

Corte de las 12 h extra que dio Emi el 08/11. Rutinas apagadas. INTEGRAR-1
recibida en `19036a2`, sin aceptar: D140 (a) la cambia la técnica; D141 (a) y
D143 (a) se proponen a Emi como piezas nuevas. D102 aceptada sobre `af924ea`
(D153 a la cola, D154 a). Para retomar: revisar INTEGRAR-1 y prender rutinas.

### 2026-11-09 19:59 UTC (Emi)

«Continua trabajando sin límite». La PM lo lee así: sin hora de corte y
vuelven los adversarios Opus; un rechazo real por límite sigue cortando.
Publicar, roadmap y esfuerzo de las Devs, sin cambios. Rutina de MARIA
apagada hasta que tenga pieza (su cola espera a Emi o al despachante).

### 2026-11-09 20:10 UTC (Emi)

- Sí a **CATALOGO-3** (MARIA, ya; D76, D77, D78, D80 con D84-D86).
- **D141 (a)**: sí, como pieza PRESUPUESTO-CLIENTE-1 (MARIA, tras CATALOGO-3).
- **D143 (a)**: sí, como pieza BORRADOR-1 (técnica, tras INTEGRAR-1).
- «Fusioná» quería decir **publicar**. Nada se publica sin «dale <SHA>»: la
  PM le pasa el SHA cuando INTEGRAR-1 esté aceptada y lo previo a publicar
  esté hecho (D64, FRONTEND_URL y ALLOWED_ORIGINS en Railway, riesgo de D102).

### 2026-11-09 20:20 UTC (PM, modo automático)

- **D155 (a)** en CATALOGO-3: origen válido = lo que reconoce
  `pais_reconocido` (nombre o código), guardado tal cual, en despacho,
  catálogo y extractor. Con (b) quedaban sin origen 143, 402, 403, 408 y 423.

### 2026-11-09 20:55 UTC (Emi: «fijate online»; la PM busca)

- En CATALOGO-3, Países Bajos lleva el código María **423**: así lo dicen
  las tablas de AFIP (Códigos María, la guía de factura de exportación). El
  434 viene del formulario F. 2672, que usa cuatro dígitos. Los sitios de
  AFIP e infoleg no se abren desde la sesión: el dato sale del resumen del
  buscador, sin haber abierto el documento.

### 2026-11-09 20:43 UTC (Emi)

- «Usalo más seguido al advisor por favor sos la pm usalo, esto es rule para
  vos». Los momentos en que se lo consulta quedan escritos en
  `ONBOARDING-PM.md`, «Subagentes».

### 2026-11-09 21:00 UTC (PM; corrige la entrada de las 20:55)

- Retiro «Países Bajos = 423». El consejero lo objetó y volví a buscar: las
  tablas oficiales y `paises_maria.js` traen dos entradas, 423 PAISES BAJOS
  y 434 HOLANDA. Ningún código de país cambia de valor. «NL» sigue en 434
  hasta que Emi confirme cuál lleva un despacho real; va a la lista de antes
  de publicar.

## 2026-11-09 20:53 UTC (PM, con el consejero)

- D157 (a): el `vendor_id` de un proveedor mixto suma el hash de sus letras no
  latinas, con la función de D77.
- D156 (a): `operation_items.origen` pasa a `Text` y sale el recorte a 3. Medido
  en Postgres 16.15: `varchar(3)` → `text` no reescribe la tabla (mismo
  filenode); sólo toma un lock exclusivo. (b), guardar el código de 3 dígitos,
  no tenía respuesta para un texto que no se reconoce.

## 2026-11-10 02:34 UTC — CATALOGO-3: devolución, D158 (a), D159 (a) (PM, con el consejero)

- Devolución sobre `f4ade80` por tres causas (acta
  `REPRODUCCION-CATALOGO-3-2026-11-10.md`): un origen no reconocido hace
  perder la confirmación entera en guardar-uso; textos iguales bajo NFKC
  dan claves distintas y «Screw M8» deja de encontrar a «Screw M8 螺丝»;
  el lookup es ~10 veces más lento.
- D158 (a): «123» es LIBIA en `PAISES_INDEC` y se acepta. Pedir rechazarlo
  fue un error de la PM.
- D159 (a): el origen en clientes (`clientes.js`, `clients.default_origin`
  VARCHAR(3), los `[:3]` de `main.py:7479/7557` y el de `/api/ncm/calcular`) va como pieza aparte, ORIGEN-2, a
  proponer a Emi. Extractor, guardar-uso, PUT del catálogo y
  `catalogo.js` entran en la devolución.
- A la lista de antes de publicar, junto a D156: el primer arranque puede
  frenarse si otra sesión tiene una transacción abierta sobre
  `operation_items`.

## 2026-11-10 10:40 UTC — CATALOGO-3 aceptada, D160-D162 (a) (PM, con el consejero)

- Aceptada la vuelta sobre `ec0092a`, en el rango `1345ca7..ec0092a`; el
  acta está en `REPRODUCCION-CATALOGO-3-2026-11-10.md`, sección «Vuelta».
  No se integra la rama: la integra INTEGRAR-1.
- D160 (a): las formas de país que no están en la tabla quedan sin origen y
  con aviso.
- D161 (a): se mantiene la excepción a NFKC para «ºª№™℠».
- D162 (a): los 22 alias que no son países quedan fuera de la lectura del
  país.
- A la lista de antes de publicar: si el primer arranque dice que N filas
  quedan por un choque y N > 0, se frena antes de que alguien confirme. Con
  un choque, el texto exacto lee la otra fila y pisa su NCM, su origen y su
  descripción.
- Se le propone a Emi MEMORIA-ORDEN-1, con la recomendación de hacerla. Al
  empatar, la memoria del cliente devuelve la primera fila. Ya pasaba antes
  de CATALOGO-3: al reclasificar un producto, sigue sugiriendo el NCM
  viejo.

## 2026-11-10 10:45 UTC — CATALOGO-3 vuelve sobre `ec0092a`; queda sin efecto la aceptación de las 10:40 (PM, con el consejero)

- Escape de la PM: se aceptó llamando preexistente a H1 sin correr la base.
  En la base, ²/2 y el ancho completo aciertan; en la vuelta empatan, porque
  NFKC (pedido por la PM en la causa 2) iguala esos textos.
- Causa de la devolución: ante un empate, la memoria del cliente se queda
  con la fila que la base devuelva primero, y confirmar no lo corrige.
  Camino de hoy: la misma factura leída del PDF y tipeada a mano. Pedido,
  en orden: gana el texto idéntico al guardado; entre iguales o empatadas,
  la última confirmada; el mismo resultado en cada corrida, en SQLite y PG.
- MEMORIA-ORDEN-1 se retira: entra en esta devolución.
- Siguen D160-D162 (a), la condición de publicar sobre los choques de la
  migración, los riesgos menores y la corrección de SUR.

## 2026-11-10 13:15 UTC — CATALOGO-3 aceptada sobre `e81b961`, sin integrar (PM, con el consejero)

- Acta: `REPRODUCCION-CATALOGO-3-2026-11-10.md`, «Vuelta sobre `e81b961`».
  Ejemplos propios, distintos de los de la devolución: 72 OK en SQLite y en
  PG; la base sin el arreglo da 33 y 43 FALLA. Sabotajes 50 de 50.
  Adversario: sin defectos.
- Decidido por la PM: el mismo desempate en el catálogo del proveedor
  (`catalog_service.py:381-402`) queda fuera de CATALOGO-3. Se le propone a
  Emi como pieza aparte. El caso de `ultima_vez` nula va a la cola de
  limpieza.

## 2026-11-10 13:45 UTC — INTEGRAR-1 aceptada sobre `4555f7c4` e integrada (PM, con el consejero)

- Acta: `REPRODUCCION-INTEGRAR-1-2026-11-10.md`. No es un SHA para publicar.
- Decidido por la PM: D145 (a), cada sabotaje con su `X-Forwarded-For`
  (MARIA; `abuso1` sigue con una sola IP); D146 (b), a la cola; D147 (a), el
  tope de avisos de MP es por worker sin `REDIS_URL`; D148, confirmada;
  D149 (a), cada dueña pone al día sus patrones.
- Antes de publicar, además: PRESUPUESTO-CLIENTE-1 sobre la unión (el pase
  por `operacion_id`), el arnés de pantalla del 402 al día y el lock de
  `_migrate_catalogo_sin_tope` probado con una conexión abierta.
- Retiro de la PM: el rojo de «`descontar` con su propia conexión» que le
  pasé a MARIA era `database is locked` en la preparación, no la condición.

## 2026-11-10 13:48 UTC — PRUEBA-LIMPIAR-1 aceptada sobre `5dd9a6eb`, sin integrar (PM, con el consejero)

- Acta: `REPRODUCCION-PRUEBA-LIMPIAR-1-2026-11-10.md`. D164 (a). Reproducida
  en `c033db7` y sobre la unión. Entra con la reentrega de
  PRESUPUESTO-CLIENTE-1.
- Corrección de la PM: el rojo que pedí («`limpiar` con su propia conexión»)
  no se podía dar. Riesgo aceptado: otra conexión sin tener la del pedido no
  se ve; no traba el pool.
- Decidido por la PM: `estudio1`, `estudio1b` y `orden1` (D149 y D145) y
  D145 en las puertas de BORRADOR-1 (`cliente1`, `foco_cliente1`,
  `destino1`, `despacho1a`) son de la Técnica, con D173 (a). Una dueña por
  archivo.
- BORRADOR-1 (`22163cec`), decidido por la PM: D170 (b) a la cola con la
  excepción de la pestaña muerta sin `pagehide`; D172 a la cola; D171 y la
  subida en curso que pisa el borrador en la carga van juntas a Emi como
  pieza nueva (misma causa, ya pasaba en `4555f7c4`).
- Escape de revisión (2026-11-10, decidido por la PM): desde DESPACHO-1b
  (`e035fc98`) acepté piezas de MARIA sin correr `scripts/testing/e2e_maria.sh`,
  y la e2e quedó roja (la memoria no aprende la posición «8471.30.00.900 R»
  que manda la pantalla). Desde ahora, cada pieza que toca el recorrido MARIA
  trae esa e2e verde sobre su SHA y la PM la reproduce; «e2e-maria verde» va
  en «Antes de publicar».

## 2026-11-11 18:41 UTC — Corte por límite semanal de la cuenta (PM)

- Las dos Devs dieron rechazo `seven_day` («weekly limit»): MARIA al menos
  desde el 10/11 19:36 UTC, la Técnica al menos desde el 11/11 11:16 UTC
  (no busqué más atrás). Último commit de las Devs: 10/11 14:04 UTC. El
  límite se renovó el 11/11 18:00 UTC.
- Por la regla de Emi («un rechazo real por límite sigue cortando»): las tres
  rutinas apagadas a las 18:39-18:40 UTC y las dos Devs avisadas de frenar
  (subir lo que tengan a medias como trabajo en curso, sin entregar).
- No se perdió ni se publicó nada. La PR Memu007/CDI-vuce-#6 sigue con
  e2e-maria roja hasta la devolución de la memoria de MARIA.
- Se retoma sólo cuando Emi lo diga: prender las tres rutinas con
  `update_trigger` y seguir la cola de `NOW.md`.
- El rojo de `tests` sobre `a0e66929` fue la aserción de tiempo de
  `test_excel2d.py::test_la_subida_cara_no_frena_a_nadie` (0,66 s contra
  0,5 s); hasta `0ffa73a0` sólo cambió `docs/pm` y ahí dio verde. Va a
  `COLA-LIMPIEZA.md`.

## 2026-11-11 18:43 UTC — Corrección a la entrada del corte (PM, con el consejero)

- «No se perdió nada» vale para lo subido: `main` sigue en `8b45207` y las
  ramas de las Devs no retrocedieron. El último commit de MARIA fue el 10/11
  14:21 UTC (no 14:04). MARIA subió a las 18:42 UTC su MEMORIA-E2E a medias
  (`195af11`, e2e_maria.sh OK, sin puertas ni informe: no es entrega). La
  Técnica no subió nada nuevo (`f6e84dac`); lo que tenga sin subir se sabe
  cuando conteste.

## 2026-11-11 18:44 UTC — Se retoma después del corte (Emi)

- Emi: «Continua», sobre la pregunta de retomar con la recomendación de hacerlo
  al ritmo de siempre. Tres rutinas prendidas otra vez con `update_trigger`
  y Devs avisadas. Si vuelve un rechazo por límite, se corta igual que antes.

## 2026-11-11 18:54 UTC — MARIA pasa a Fable (Emi)

- Emi: «Si, maria», sobre la recomendación de la PM de probar Fable en una
  sola Dev, la de la carga más delicada. El cambio lo hace Emi con `/model`
  en el chat de MARIA al borde de pieza: después de entregar MEMORIA-E2E,
  antes de PRESUPUESTO-CLIENTE-1. Esfuerzo sigue en alto.
- Cambia la regla del 2026-10-07 sólo para MARIA: los revisores de su
  `/code-review` heredan Fable. Los `adversario-*` y `mecanico-haiku`
  siguen con su modelo fijo; ningún otro subagente en Fable.
- Vuelta atrás que propone la PM: si aparece el aviso de límite antes de lo
  habitual, MARIA vuelve al modelo de antes. Que el uso de Fable se recupera
  aparte es dicho de Emi; la PM no lo pudo comprobar.

## 2026-11-11 21:59 UTC — PRESUPUESTO-CLIENTE-1 aceptada e integrada; D163 y D167 (PM, con el consejero)

- Aceptada sobre `f45243a`, integrada en `8669b43`. Entra con ella todo lo
  aceptado sin integrar de MARIA: cada commit de producto cae en el rango de
  una pieza aceptada, clasificados por rango en el acta
  `REPRODUCCION-PRESUPUESTO-CLIENTE-1-2026-11-11.md` (ser ancestro de una
  punta aceptada no alcanza: CATALOGO-3 ya contenía commits de ésta).
- D163 (a): el `share_quote` en vuelo durante un pase o un borrado queda como
  riesgo bajo, sin código. Lo hace el mismo dueño en dos pestañas; no cruza
  permisos. Si se quiere cerrar, (c).
- D167: no se generaliza; las sesiones siguen con `/autocompact 200k`. MARIA
  queda en los 250k que le puso Emi (umbral 184000 desde las 21:36 UTC). Con
  el umbral viejo (144000) compactaba cada ~5 minutos, porque después de
  compactar quedaba en ~150k. Para la rutina de la PM, la alarma de MARIA es
  que compacte seguido, no el tamaño.

## 2026-11-12 01:08 UTC — CONEXIONES-1 B aceptada como medición; D180 (a) y D181 (b) (PM, con el consejero)

- Aceptada sobre `c57b645e` e integrada (merge exacto, sin producto). Acta
  `REPRODUCCION-CONEXIONES-1-2026-11-12.md`. No se cierra CONEXIONES-1.
- D180 (a), con criterio propio: no es «los 500 de PDF» sino que una cuenta
  sola no le haga fallar ni esperar a otra. `/api/ncm/sugerir` no tiene tope y
  un solo token toma 50 de 50 conexiones (la misma cuenta espera 30 s).
  CONEXIONES-1 C a la Técnica, **sólo arnés**: medir a otra cuenta (subida
  pública y sugerir), separar pool lleno de fuga, corrida con la cuota de
  producción, y el arreglo propuesto sin commitear (como D134). El arreglo de
  producto es **propuesta a Emi**: la fila del roadmap dice «arreglar sólo si
  las deja» y no quedan. El login queda afuera: no da rojo.
- D181 (b): a la cola, con el caso de la misma IP en simultáneo.


## 2026-11-12: D145 (a) de MARIA aceptada sobre `08edd63`

- Sus cuatro pantallas que registran varias veces contra una base mandan una IP inventada por registro (`_ip_nueva.js`). Acta `REPRODUCCION-D145-2026-11-12.md`.
- D190 (a), por la PM: las seis copias de la Técnica, a la cola.
- D191 (a), por la PM: `sabotaje_maria9.sh` no corre entero desde `fe95a49b` (SUFIJOS-1 cambió la firma de `usa_el_sufijo_de_la_operacion`); lo reancla MARIA, sólo arnés, 30 de 30 en rojo.
- Escape de la PM: VALOR-1c (`3df999c8`, anclas 24, 27 y 28) y después SUFIJOS-1 (la firma) se aceptaron sin correr `sabotaje_maria9.sh`, que anclaba lo que cambiaron (acta de D191). `sabotaje_maria9.sh` entero entra en «Antes de publicar».
- D194 aceptada sobre `f507763`; D195 (a), decidido por la PM: los 10 guiones vencidos van a `herramientas/sabotajes-conocidos.txt` con dueña MARIA y salida «reescribirlo»; uno por pieza de arnés, empezando por `sabotaje_maria3.sh`; un sabotaje sin protección que atacar vuelve como D para retirarlo. Antes de publicar, `anclas_perdidas.py` sobre el SHA candidato.
