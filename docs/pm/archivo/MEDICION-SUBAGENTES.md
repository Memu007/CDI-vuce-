# Medición de subagentes

Una fila por subagente en cada revisión. Se revisa con números para decidir
qué modelo y esfuerzo rinden.

- **Hallazgos:** cuántos devolvió.
- **Reproducidos:** cuántos se confirmaron con evidencia.
- **Nuevos:** cuántos no había visto nadie (ni la Dev, ni sus casos, ni la PM).

| Fecha | Pieza | Quién lo usó | Modelo y esfuerzo | Hallazgos | Reproducidos | Nuevos |
|---|---|---|---|---|---|---|
| 2026-10-06 | AUDITORIA (copia vieja CDI, línea equivocada) | PM | Sonnet medio (ops) | 12 | — (línea equivocada: no se reprodujo; algunos puntos se pasaron como hipótesis al de datos) | — |
| 2026-10-06 | AUDITORIA-VUCE (cobro y sesión) | PM | Opus alto | 12 | 4 por la PM (H2 MARIA sin cortar por impago, H9 admin para cualquiera: corridos; H3 cancelar no cancela en MP: por código; H1 aviso sin firma: por el test G7). El subagente casi no reprodujo nada | 12 |
| 2026-10-06 | AUDITORIA-VUCE (datos y operación) | PM | Sonnet alto | 11 | 6 por el subagente con salida (corte masivo al arrancar, /health 200 con base caída, XFF falsificable, bloqueo del event loop, dev_detail, quotes sin dólar); 0 re-corridos por la PM todavía | 9 |
| 2026-10-06 | AUDITORIA-VUCE (suite y G1) | PM | Haiku | 1 | 0: «G1.5 no corta» era falso (la PM lo corrió: RuntimeError, salida 1). La suite sí: 680 passed, 102 skipped, 0 failed | 0 (1 equivocado) |
| 2026-10-06 | AUDITORIA-VUCE (aislamiento y permisos) | PM | Sonnet alto | 13 | 2 por la PM (admin abierto, corte 402 que no cubre el MARIA: los mismos que el de Opus). El subagente reprodujo con salida casi todo, incluida la fuga de producción con la copia de `a771693` | 9 (fuga en producción confirmada, sesiones que reviven, invitaciones 500 en Postgres, borrar cliente con presupuesto, `/api/ui/event`, carreras de `op_code`, enumeración, correo masivo, XFF) |
| 2026-10-06 | AUDITORIA-VUCE (archivo MARIA y producto) | PM | Sonnet alto | 16 | 1 por la PM (peso por unidad: `QARTKGRNET=2.500` para 10 × 2,5) más `CARTUSO` e `IVAAD1` vistos en el TXT. El subagente reprodujo casi todo con salida | 14 (peso, origen a 2 letras, ítems demo, avisos después de generar, gastos FOB sin cablear, float, inyección, identificadores) |
| 2026-10-06 | Investigación web: `CARTUSO` e IVA adicional | PM | Sonnet alto (general) | 3 | — (son fuentes, no fallas): `CARTUSO` = estado de la mercadería, `IVAAD1` = uso particular, `GANANCIASOP3` sin `NO_VALIDA` desde el 24/08/2026. Todo de resúmenes de buscador; confianza media | 2 (`IVAAD1` exceptúa la percepción; el cambio de `GANANCIASOP3`) |
| 2026-10-06 | Investigación web: banco, proveedor, FOB y procedencia | PM | Sonnet alto (general) | 4 | — : procedencia con cita del Código Aduanero (art. 15) y GTOS con cita de la nota del SIM. El resto, de resúmenes | 2 (procedencia y la regla de GTOS, que dejan de ser preguntas) |
| 2026-10-07 | ROADMAP (lo que la auditoría no miró) | PM | Sonnet alto | 5 (+1 ausencia: sin términos ni privacidad) | 4 por el subagente con salida (`pip-audit`, cuelgue del lector de PDF viejo, 10 pruebas excluidas que hoy pasan, suite sin exclusiones 680/102/0); la PM confirmó leyendo: sin límite en sugerencias de NCM, no hay `deploy.yml`, versiones de las librerías | 6 (X1 a X6) |
| 2026-10-07 | ROADMAP (tamaño y choque de piezas) | PM | Sonnet medio | 8 piezas mal planteadas o incompletas | La PM confirmó leyendo: el origen cortado está en dos copias del lector, el admin se monta sin `require_admin`, el corte por impago está en 2 rutas, las carreras de `op_code` están fuera del webhook | 4 (C6 mal ubicada, contar dos veces el MARIA, DISCO-1 sin los TXT descargados, MARIA-1 en dos piezas) |
| 2026-10-07 | ADMIN-1 (revisión de PM) | PM | Opus alto | 4 (3 puntos ciegos de la prueba, 1 de telemetría) | 3 por el subagente con salida, en copias del código; la PM no los re-corrió | 2 (app montada aparte y ruta cruda escondida, que la prueba no ve) |
| 2026-10-07 | MARIA-2 (revisión de PM) | PM | Sonnet medio | 5 (todos bajos o informativos) | 3 por el subagente con salida | 1 (un archivo enorme se lee entero antes del 413; es de antes) |
| 2026-10-07 | ADMIN-2 (revisión de PM) | PM | Sonnet alto | 3 (2 puntos ciegos de la prueba, 1 latente de `roles`) | 2 por el subagente con salida, en copias del código; la PM no los re-corrió | 2 (WebSocket bajo `/api/admin/` y ruta cruda en `/api/admin` o `/dev` exactos, que la prueba no ve) |
| 2026-10-07 | Candidato del ensayo (`81bcaba`) | PM | Opus alto | 6 (+1 fuera de alcance: el TXT cambia entre versiones) | 5 por el subagente con salida, con Postgres 16 local y una base armada con julio | 4 (la cuenta de Emi pasa a impaga al arrancar y no guarda operaciones nuevas, y volver atrás no lo deshace; `ENVIRONMENT=Production` con mayúscula crea los demo en la base real; `ADMIN_USERNAMES` con un usuario inexistente lo regala al primero que se registre; `ALLOWED_ORIGINS` y JWT exigidos al arrancar) |
| 2026-10-07 | RENDIMIENTO-1 (revisión de PM) | PM | Sonnet alto | 6 | 4 por el subagente con salida (servidor vivo con una cuenta de prueba) | 1 (tiempos en 0 o negativos); confirmó con números la D10 de la Dev (4 PDFs armados dejan sin lectura a todos) |
| 2026-10-07 | MARIA-1a y MARIA-2b (revisión de PM) | PM | Sonnet alto | 7 | 4 por el subagente con salida (unos 300 países, números, D5 hasta el TXT, cuota) | 2 (la pantalla vieja repone 1 y China; «sin productos» que da 503) |
| 2026-10-07 | RENDIMIENTO-1b y MARIA-1c (revisión de PM) | PM | Sonnet medio | 3 | 3 por el subagente con salida (más de 10 PDFs armados sin cuelgue) | 2 (el vendedor con dos columnas sale «BUYER»: devolución; avisos de más en MARIA-1c) |
| 2026-10-07 | MARIA-4 (revisión de PM) | PM | Sonnet alto | 5 | 4 por el subagente con salida (pantalla en Chromium, dos usuarios, los dos archivos reales comparados) | 3 (estado contra origen sin aviso; la pantalla vieja no muestra los supuestos; `origen` contra `pais_origen`): devolución |
| 2026-10-07 | MARIA-3 (revisión de PM) | PM | Sonnet alto | 6 | 5 por el subagente con salida (672 combinaciones de avisos, los dos archivos reales) | 5 (procedencia con 129 países rechazados, año del IEXT sin fecha, fechas raras aceptadas, procedencia rara con 500, gastos sin tope): devolución |
| 2026-10-07 | EXCEL-1 (revisión de PM) | PM | Sonnet alto | 7 | 6 por el subagente con salida (servidor vivo, dos cuentas, Excel de 8 MB) | 5 (el mapeo aprendido pisa «Precio Unitario»: FOB ×10; validación en los hilos compartidos; fila de ejemplo; mapeo doble con 500; la pantalla vieja llama a una ruta borrada): devolución |
| 2026-10-07 | Devoluciones de EXCEL-1 y MARIA-3 | PM | Sonnet medio | 4 (menores) | 4 por el subagente con salida (login real; los 10 puntos devueltos repetidos) | 4 menores (subida chica detrás de las pesadas, aviso de mapeo, procedencia rara de ítem en avisos, siglo del IEXT) |
| 2026-10-07 | MARIA-1d (revisión de PM) | PM | Sonnet medio | 6 (todos ya pasaban antes) | 6 por el subagente con salida (TestClient, Gemini falso, 26 procedencias, los dos archivos reales) | 0 en la pieza; 2 a MARIA-5 («None» escrito en la carátula; descripción distinta en las dos copias), 3 cubiertos por MARIA-1b |
| 2026-10-07 | MARIA-1b (revisión de PM) | PM | Sonnet alto | 9 | 7 por el subagente con salida (TestClient, 12 CUIT reales, 25 casos del archivo real, libro armado de 90 MB) | 4 (NaN e inf llegan al TXT; el escaneo de otras hojas traba la lectura 3 min; dígitos Unicode en el CUIT; monedas sin confirmar): devolución |
| 2026-10-07 | MARIA-5 (revisión de PM) | PM | Sonnet alto | 14 | 11 por el subagente con salida (~11.000 pedidos al azar de centavos, 1500 de regresión, 3000 de subítems, Playwright en la v2) | 6 (peso ×cantidad si el lector o el Excel traen dos pesos; fila que desaparece; peso sin guarda; subítems que dejan de generar; grupo con un producto en 0; validación con otro FOB): devolución |
| 2026-10-07 | Devolución de MARIA-1b | PM | Sonnet medio | 7 | 6 por el subagente con salida (TestClient, libros armados con y sin `<dimension>`, 9 tipos de salto en la exportación, el merge con la Dev 2) | 0 en la pieza; 2 a EXCEL-2 (abrir libros sin `<dimension>`, 500 con `10**400`) |
| 2026-10-07 | Candidato de la segunda publicación (`6ea8ca9`) | PM | Opus alto | 10 | 8 por el subagente con salida (Postgres 16 con base de `5cb03ab`, ida y vuelta, tokens cruzados, imagen sin apt, TXT línea por línea) | 1 (ya en producción: guardar con SIM completa da 500 por `String(10)`) y la lista de lo que cambia para Emi |
| 2026-10-07 | PUNTA-A-PUNTA-1 | PM | — (pieza de pruebas: la PM corrió los 9 sabotajes) | — | — | — |
| 2026-10-07 | Reentrega de MARIA-5 con CATALOGO-NCM-1 | PM | Sonnet alto | 9 | 8 por el subagente con salida (9000 pedidos al azar, 26.000 de subítems, 33.037 SIM, Playwright, copia sin catálogo); 3 repetidos por la PM | 6 (columna de peso desconocida que gana: ×16 en el TXT; bruto «unitario» leído como neto; dos pesos de la línea sin números; pantalla en rojo en el SHA entregado; baja con aviso doble y texto falso; sin catálogo, errores inventados): devolución |
| 2026-10-07 | EXCEL-2 (revisión de PM) | PM | Sonnet alto | 9 | 9 por el subagente con salida (libros armados medidos en tiempo y memoria, 8 y 2 subidas a la vez, combinadas, CSV cp1252); 2 repetidos por la PM | 6 (combinada gigante traba la lectura; combinada con texto duplica el FOB; tope de estilos que no protege; la D26 se saltea con otros libros; CSV que pierde tildes en silencio; fila vacía como «sin leer»): devolución |
| 2026-10-07 | SUBITEMS-1 (revisión de PM) | PM | Sonnet medio | 6 | 5 por el subagente con salida (3600 pedidos al azar contra los dos árboles, Playwright, formas raras) | 0 que rompan; 4 chicos a la reentrega de MARIA-5 (500 con un número, borde de 0,01 pantalla/servidor, suma redondeada, error bajo el campo equivocado) |
| 2026-10-07 | GUARDAR-1 (revisión de PM) | PM | Sonnet alto | 6 y la D32 | 6 por el subagente con salida (Postgres 16 propio, triggers que fallan en el commit y cortan la conexión, 8 guardados a la vez, `ALTER` sobre 3 millones de filas) | 0 en la pieza; 2 ya existentes a COBRO-CORTE-1 (contador y tope con guardados a la vez); la D32 medida: (b) |
| 2026-10-07 | Reentrega completa de MARIA-5, CATALOGO-NCM-1 y SUBITEMS-1 | PM | Sonnet medio | 4 | 4 por el subagente con salida (los scripts viejos de cada hallazgo, 5000 + 1100 pedidos al azar contra tres SHA, Playwright) | 1 media (el bruto «unitario» se divide: MARIA-5d antes de publicar) y 3 bajas |

| 2026-10-19 | Codex PM, retoma | MARIA-5d `d22ff1a` | modelo heredado, esfuerzo heredado (Sonnet/Opus no disponibles) | 1 familia de defecto, 3 variantes HTTP | PM reprodujo las 3; borde nuevo frente a 65 focales verdes | vuelve, no publicación |

| 2026-10-19 | Codex PM, segunda revisión MARIA-5d | b3fd518 → 8b8b789 | modelo y esfuerzo heredados | 1 regresión, 2 columnas por línea en inglés | PM reprodujo por AST las 2; corregidas y cubiertas en 148 focales | candidata; faltan puertas de publicación |

| 2026-10-21 | Codex PM, combinación Fase 1 | candidate_integration, modelo/esfuerzo heredados | 8b19662 | sin conflicto de producto; 186 focales, 15 JS, 14 negativos | PM revisó diff y reprodujo 82 focales | candidato devuelto tras suite limpia |
| 2026-10-21 | Codex PM, entorno limpio | clean_dependencies, modelo/esfuerzo heredados | 8b19662 | 4 fallos, una causa nueva: booleano Form omitido cambia a False con FastAPI nuevo | PM contrastó fuente oficial y reprodujo el rojo discriminante en copia previa | compatibilidad mínima autorizada, 166395f en revisión |
| 2026-10-21 | Codex PM, navegador | candidate_browser, modelo/esfuerzo heredados | 8b19662 | registro y cliente correctos; adjunto bloqueado por permiso de Brave | PM completó en IAB carga Excel, controles, TXT y persistencia sin cambiar permisos | recorrido CUA sintético, no e2e CI ni Gemini real |
| 2026-10-21 | Codex PM, cierre compatibilidad Excel | candidate_integration y clean_dependencies, modelo/esfuerzo heredados | 166395f | corrección mínima y suite limpia 1612 passed | PM reprodujo rojo anterior y 8 focales verdes, revisó diff y cierre del log completo | aceptada técnicamente en candidato local; faltan puertas de publicación |
| 2026-10-22 | Codex PM, revisión final de publicación | candidate_integration, modelo/esfuerzo heredados | 166395f contra a9b03cf | sin bloqueantes nuevos de alcance/config/datos añadidos | PM comprobó diff de producto vacío en15611f5 y main648cd2f; CI tests/e2e aprobados | merge autorizado realizado; Railway pendiente por incidente |
| 2026-10-22 | Codex PM, EXCEL-2 | excel2_next_review, modelo/esfuerzo heredados | c2f8063 | un escape bloqueante XML válido y un CSV menor; 93 focales verdes no bastan | PM reprodujo escape con una celda, 16384 columnas al usar comillas simples | vuelve; Dev corrige aislado, no integrado en publicación |
| 2026-10-22 | Codex PM, devolución XML EXCEL-2 | candidate_integration y clean_dependencies, modelo/esfuerzo heredados | 04e1d0 | 32 focales y checks propios verdes; observación de retención de nodos vacíos medida sin incumplimiento demostrado | PM repitió reproducción anterior en verde y revisó diff; QA midió 3MB XML/38.69MiB pico del parser | guarda verificada; aceptación completa de EXCEL-2 e integración pendientes |
| 2026-10-22 | Codex PM, integración EXCEL-2 | candidate_integration preparó d448033; revisión/medición final PM | d448033 sobre648cd2f | Dev356focales/15JS; PM encontró dos rojos: concurrencia real y origen combinado XML simple | PM reprodujo ambos con harness acotado, nueve normales iguales a base, tiempo2000combinadas0.166s | vuelve; no full ni publicación por rojos conocidos. Agentes interrumpidos por cuota; no se atribuyen sus negativos inconclusos |


### Retoma 2026-10-23 — EXCEL-2 integrada

- candidate_integration (modelo/esfuerzo heredados): producto3906130 y
be17e1b, pruebasb073ba4/0666881, entrega dddcf6d.362focales, test8durable,
51focales adicionales y negativos nuevos; PM reprodujo lectura/origen,
concurrencia y suitefinal1731. No hubo Fable ni medición de tokens exacta.
- excel2_next_review (heredados):12checks, seis propios;3mutaciones
con fallo correcto. Cero bloqueantes nuevos reproducidos; preservación de
DOC1/pesos/Form/dueño confirmada por fuente. PM comprobó gatesindependientes.
- clean_dependencies (heredados): descubrió patrón#9obsoleto y debilidad de
harnessgrepFAILED; PM adoptó selección exacta/JUnit/motivo y cortesrecursos.
EjecutorQAexterno concleanupfinally, sin producto. Grupoall300s en curso;
no acreditar resultados aún. Primer sandbox no llegó a tests por psutil;
se conservó evidencia y se aprobó escalación local, sin ocultar testrojo.


Cierre24Oct: clean_dependencies ejecutó grupoall sobredddcf6d. Baseline37verdes;
38detectadas por motivo (36matcher+2manual),2timeouts no evaluadas y2patrones
obsoletos con count0. PM verificó motivos14/23/28 directamente.0sobrevivientes
entre terminadas; no42/42. Modelo/esfuerzo heredados; uso tokens no disponible.
PMmidió además499900xf admitidos460MB/9.18s, no límite universal. CI/e2everdes.
