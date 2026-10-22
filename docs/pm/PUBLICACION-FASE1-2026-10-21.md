# Publicación Fase 1 — 2026-10-21

Emi autorizó «publica. y contonua» en respuesta al cierre de pruebas de
`166395f99c0011aa46f55f82afa3734c97576150`. La autorización y su alcance están
en DECISIONS.md; no hace falta pedirla de nuevo para ese producto.

## Candidata y puertas

- Producto probado: `166395f`, suite local limpia 1612 passed, 102 skipped,
  2 xfailed, cobertura 50.75 %, salida 0; detalles en
  `VERIFICACION-CANDIDATO-2026-10-21.md`.
- Rama de publicación: `codex/release-phase1`, cabeza
  `15611f5106e019a9ab2d44ae007b194f571e1f16`. Sólo documentación añadida sobre
  el producto probado, comprobado con diff excluyendo documentos/reglas.
- Main remoto traído a la revisión: `a9b03cf`. Ya es ancestro de la candidata;
  merge indica actualizado, sin cambios adicionales de producto.
- Revisión final independiente: sin bloqueantes nuevos en alcance,
  configuración ni datos añadidos; no sustituye la CI ni el Kit.
- [PR #4](https://github.com/Memu007/CDI-vuce-/pull/4) abierto inicialmente
  en borrador hacia main para ejecutar las puertas antes de publicar.
- [CI de revisión](https://github.com/Memu007/CDI-vuce-/actions/runs/39685117915):
  tests y e2e-maria **success**, comprobado el 2026-10-22 antes de fusionar.

## Resultado de publicación

PR #4 fusionado el 2026-10-22: main
`648cd2f0c3103f466e7fd7b7022985907e08cd06`. Git remoto traído y diff de
producto contra `166395f` vacío. No se mezcló EXCEL-2 ni GUARDAR-2.

**Railway pendiente, no afirmar publicación en vivo completada.** A las
08:56 ARG, el endpoint público `/health` respondió ok y API/base ok; el
JavaScript upload servido aún no coincidía con la candidata. CUA muestra
como ACTIVE el despliegue de GUARDAR-1 de hace 14 días; fuente correcta
Memu007/CDI-vuce-, main, autodeploy habilitado y Wait for CI deshabilitado.
No se cambiaron variables, permisos ni configuración.

Railway muestra incidente de plataforma; su
[estado oficial](https://status.railway.com/incident/QH8L8B3E) informa colas
de despliegue y disponibilidad limitada por plan. No lanzar despliegues
duplicados. No se accedió directamente a la base de producción ni se cargaron
facturas privadas. La consulta de estado de commit del conector GitHub devolvió
403; no se eludió. La revisión del estado se hizo en la interfaz Railway
accesible y mediante salud/assets públicos.

No requiere nuevo permiso de Emi para completar el mismo despliegue cuando
Railway lo permita. Su aviso oficial también incluye recomendaciones tras un
incidente de seguridad: cualquier rotación de credenciales queda a cargo de
Emi; no leer ni copiar secretos al chat o al repo.

## Continuación

EXCEL-2 se revisa por separado desde `c2f8063` sobre `1cdfe49`; su informe de
Dev sigue antiguo y sus focales verdes no equivalen a aceptación. GUARDAR-2
continúa separado, D32 (b) sin migración sigue vigente. La Fase 1 todavía
necesita facturas reales revisadas por Emi y aceptación del despachante en Kit.

EXCEL-2 devuelta: 93 focales verdes pero el control de ancho acepta una celda
`r='XFD1'` con XML de comillas simples y openpyxl expande 16384 columnas;
el mismo documento con comillas dobles se rechaza. PM reprodujo con una sola
celda sintética, sin estrés. Dev corrige en copia aislada; no integrar antes
de nueva revisión. No contar los 43 negativos como corridos: sólo cuatro
resultados se recuperaron. CSV cp1252 malformado queda anotado como menor.

Devolución XML local `04e1d003fce518a754909e8de5cf56ee22365ae2` lista en
`codex/excel2-xml-quotes`, preservada en repo de trabajo sin publicación.
Parser incremental de stdlib normaliza atributos, reconoce comillas/espacios/
entidades y corta al superar 256 columnas. PM repitió la reproducción segura:
ambas variantes rechazan. QA independiente: 32 focales verdes y comprobaciones
propias de bordes/entidades/namespaces/salida temprana/cierre. Ver
`QA-EXCEL2-XML-2026-10-22.md`.

Precisión de evidencia: clear conserva nodos vacíos hasta cerrar su padre;
no afirmar que nunca retiene árbol. Con XML de 3 MB y 500000 filas, el parser
midió 38.69 MiB pico y 2.13 s; no se midió el máximo ni flujo concurrente.
No demuestra el límite global 1 GB. La guarda concreta está verificada;
EXCEL-2 completa sigue pendiente de integración aislada, suite/CI y las
mediciones históricas. El permiso de publicar la candidata anterior no
autoriza publicar automáticamente esta entrega posterior.

Última comprobación pública a las 09:00 ARG del 22: salud ok y JS servido
todavía anterior. Railway nuevo no confirmado; no registrar como completado.
