# Candidato Fase 1 — verificación del 2026-10-21

## Identidad y alcance

Primera combinación local `8b19662257dc35245ae382b002ac374db03e91e8`, rama
`codex/phase1-candidate-local`, preservada también en el repositorio de trabajo.
Combina PM `261d6cb`, pesos `254531b` y DOC-1 `fe0a101`. Los conflictos fueron
sólo documentales; no hubo edición manual del producto. No está publicado.
El candidato corregido vigente es `166395f`, detallado más abajo.

El 2026-10-20 se confirmaron las tres cabezas remotas y `main` en `a9b03cf`;
los PR #1, #2 y #3 seguían abiertos y en borrador. El permiso de guardarlos
no equivale a permiso para publicar el candidato.

## Evidencia de integración

- Dev: 186 focales Python y 15 escenarios JS aprobados.
- PM: 82 focales reproducidos independientemente sobre este candidato.
- Negativos en copias aisladas: 11/11 de pesos y 3/3 documentales detectaron
  el defecto esperado. No se alteró el checkout usado por las otras pruebas.
- Informe de integración local: `/private/tmp/cdi-phase1-integration-report.md`.

## Instalación limpia

Venv nuevo sin paquetes del sistema:
`/private/tmp/cdi-clean-requirements-20261020`. Instalación del requirements
sin modificarlo y `pip check` satisfactorios. En esta Mac, cryptography 50
intentaba compilar sin OpenSSL disponible; `--only-binary=cryptography`
permitió resolver cryptography 48.0.1 y pyOpenSSL 26.2.0 dentro de los rangos
declarados. Esto prueba instalación local, no la imagen Linux de Railway.

Evidencias y versiones resueltas en `/private/tmp/cdi-phase1-clean-suite/`.
El primer chequeo previo no arrancó la suite: ventana de arranque insuficiente,
bind local bloqueado por sandbox y luego comparación del PID wrapper/hijo.
Se corrigió el harness externo; no el producto. El chequeo válido verificó
SHA, árbol limpio, entorno aislado, servicios simulados, URLs loopback,
un solo listener, API, frontend, tablas SQLite y carga de máquina.

Resultado de suite completa con chequeo previo satisfactorio: **ROJA**,
1604 passed, 4 failed, 102 skipped, 2 xfailed, 23 warnings; cobertura 50.63 %,
338.30 s, salida 1. Fallan cuatro casos de `tests/test_excel1_lectura.py`
relacionados con el mapeo guardado/corregido. No aceptar ni publicar este SHA.
La investigación debe distinguir regresión de integración, entorno y estado
de pruebas; no repetir la suite para buscar un verde sin explicar la causa.

## Navegador real mediante CUA

Servidor local real sobre el candidato, SQLite descartable y datos sintéticos.
Sin Gemini real ni conexión a producción. El subagente verificó alta,
bienvenida y creación de cliente; Brave no permitió adjuntar archivos sin
ampliar permisos de la extensión. No se cambiaron esos permisos.

PM continuó en el navegador integrado y verificó:

1. Excel sintético: dos productos y cliente correcto; revisión de fecha e incoterm.
2. NCM de ocho dígitos bloquea avanzar; completar SIM/DC y agrupar habilita avance.
3. Grupo rechaza peso cero; producto individual con cero bloquea generación.
4. Corregir peso y volver a validar elimina ese error. Se mantuvieron advertencias.
5. SBT vacío bloquea; al completarlo se genera y descarga el TXT.
6. Descarga leída desde disco: un DDT, ocho CPL, un DVD, un ART y un SBT;
   peso neto total 2.000 para cuatro unidades de 0.5 kg. No es referencia aduanera.
7. Operación persistida visible con dos ítems y total sintético; catálogo muestra
   NCM y origen confirmados. Una segunda carga conserva sus cantidades, valores,
   origen y peso del Excel; no copia los valores editados de la operación previa.

Evidencia visual en `outputs/candidato-txt-sintetico.jpg` del workspace.
No se ejecutó `e2e_maria.sh` (automatiza Puppeteer); esta reproducción CUA
no se cuenta como ejecución de ese script ni cubre todas sus aserciones HTTP
de memoria/sugerencias. El PDF A→B rechazado tiene evidencia sintética anterior
en DOC-1 y pruebas combinadas; no demuestra precisión del clasificador real.

## Corrección de compatibilidad en revisión

Nuevo candidato local `166395f99c0011aa46f55f82afa3734c97576150`, rama
`codex/phase1-form-default-compat`, preservada también en el repo de trabajo.
Sólo agrega la guarda de campo ausente en el endpoint Excel, cuatro casos
parametrizados y changelog. Conserva el booleano validado por FastAPI y no
agrega dependencias ni cambia requisitos.

Dev reprodujo antes 1 fallo/3 verdes y después 57 Excel verdes en limpio,
8 focales verdes en heredado. PM revisó el diff y reprodujo independientemente:
8 focales verdes en limpio; con las pruebas nuevas copiadas a `8b19662`,
1 fallo/3 verdes por la cantidad incorrecta esperada. No se debilitó la prueba.
Una búsqueda de bool Form con default True encontró sólo esta opción.

La segunda suite completa con chequeo previo sobre el SHA nuevo terminó
**VERDE: 1612 passed, 102 skipped, 2 xfailed, 23 warnings**, cobertura 50.75 %,
311.92 s, salida 0. PM comprobó el cierre del log y el SHA; checkout limpio.
API temporal cerrada. Evidencia separada en
`/private/tmp/cdi-phase1-clean-suite-fixed/`. No se sobrescribió la corrida
roja ni se cuenta como un reintento del mismo código.

Veredicto PM: corrección de compatibilidad aceptada técnicamente dentro del
candidato local. No equivale a aceptación aduanera ni autorización de deploy.

## Qué sigue después de la corrección

Completar la puerta oficial de CI; recibir EXCEL-2 y GUARDAR-2
por separado, sin adelantar cobro. Para cerrar Fase 1 faltan facturas reales
revisadas por Emi y un TXT aceptado sin correcciones en el Kit del despachante.
MARIA-6 espera evidencia; no inventar identificadores ni sufijos. No generar
exportaciones EC02: la decisión vigente es bloquear el TXT incorrecto.

No fusionar a main ni desplegar sin autorización de Emi para el SHA final.
