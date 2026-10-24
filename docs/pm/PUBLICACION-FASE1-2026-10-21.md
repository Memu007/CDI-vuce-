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

Seguimiento de la tarde, 2026-10-22: salud pública ok a las 16:11 ARG y JS
upload aún distinto del probado. La interfaz, recargada al cierre, sigue
mostrando ACTIVE GUARDAR-1. El estado oficial de las 19:06 UTC informa
operación normal de Pro/Enterprise, otros planes aún pendientes; no se
asume el plan de este workspace. Se intentó una sola vez el comando visible
«Deploy latest commit» para la versión ya autorizada. No apareció un nuevo
despliegue ni confirmación; no afirmar que quedó en cola ni repetirlo a ciegas.
Captura local `outputs/railway-seguimiento-2026-10-22.jpg` del workspace.

Continuación EXCEL-2: integración `d448033` devuelta con dos rojos nuevos de
concurrencia y origen combinado. Ver `REVISION-EXCEL2-INTEGRADA-2026-10-22.md`;
no publicar esa pieza ni atribuirle suite completa. Las comprobaciones PM
se completaron aunque los agentes de implementación se interrumpieron por
límite de uso. No hay corrección entregada de esos dos fallos todavía.

## Retoma 2026-10-22, 20:34 ARG

El estado oficial de 22:49 UTC habilita builds y despliegues para los cinco
planes, a velocidad aproximadamente normal. La comprobación pública de
23:34:01 UTC responde salud ok; SHA256 de upload.js remoto
`322135ba7530e230b517f2507d22140f0f075c1ba4948d4a705e1218b0e1e7d8`, frente
al local de main648
`b20509580b9bf92271604caac0d77b86211fe0626b62a334d1b37f78592dd38d`.
Sigue ACTIVE el mismo despliegue antiguo. Tras la recuperación del proveedor,
un nuevo intento del comando visible Deploy latest commit no cambió el estado.

La revisión de acceso aclara el bloqueo: la UI dice proyecto PUBLIC, muchos
controles están deshabilitados y Members devuelve «You are not authorized to
view the contents of this section». Navegar a inicio muestra Sign in;
Continue with GitHub lleva al formulario de ingreso, sin sesión existente.
Por tanto no atribuir toda la demora actual al incidente ni afirmar que hay
un despliegue en cola. La pestaña de ingreso se conserva para Emi. No se
leyeron credenciales, no se modificaron permisos y no se accedió a la base.
La autorización del mismo producto sigue vigente; se necesita completar el
ingreso en el navegador para poder ejecutar/verificar la acción.


Seguimiento23Oct07:58ARG: salud pública ok; upload.js remoto conserva SHA256
322135ba7530e230b517f2507d22140f0f075c1ba4948d4a705e1218b0e1e7d8,
distinto de main648. Estado oficial09:34UTC: despliegues normales y posible
necesidad de reconectar GitHub; no es evidencia de que esta cuenta lo requiera.
Sin sesión autorizada en IAB no se puede comprobar/ejecutar esa reparación.
No se usó el otro proyecto Railway visible en Brave ni se cambiaron permisos.
La corrección nueva EXCEL-2 se guarda en PR#5 borrador, con CI roja y e2e
omitida; no mezclarla con esta publicación anterior ya autorizada.


23Oct17:13ARG: el selector de navegador para URL deCDI eligióBrave, que tiene
sesión autorizada. Se creó pestaña propia; ningún cambio en el otro proyecto.
Main remoto confirmado648cd2f porls-remote. Un único Deploy latest commit
autorizado registra despliegue4bb8b534-04e2-4d94-bfd8-7e101defbe94 BUILDING,
con mensaje de commit «Publicar Fase1». No afirmar en vivo hasta verificar.
Se resuelve el bloqueo de acceso anterior, no se cambiaron credenciales.


## Publicación completada, comprobación 2026-10-24

Despliegue4bb8b534 ACTIVE/Deployment successful, enlace al commit648cd2f.
Startup completo23Oct17:22:50ARG. Salud pública200 API/baseok24Oct12:59:33UTC;
upload.js servido coincide byte a byte conmain648 (SHA256b20509580b9bf92271604caac0d77b86211fe0626b62a334d1b37f78592dd38d).
Captura outputs/CDI-publicado-2026-10-24.png. Se cierra el despliegue autorizado;
no repetirlo ni pedir otropermiso para eseproducto. PR5 EXCEL2 sigue aparte,
requiere autorización nueva deSHA antesdemain. CierreCIERRE-RETOMA-2026-10-24.md.
