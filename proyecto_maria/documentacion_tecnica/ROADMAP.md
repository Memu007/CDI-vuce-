# Roadmap CACA - Optimizador MARIA (2025)

Este roadmap guía la evolución del sistema priorizando simplicidad, velocidad y valor para el usuario. Se organiza en fases cortas con criterios de aceptación claros. Integra el plan avanzado (idea_claude-md) en etapas posteriores, sin complejizar el prototipo actual.


## Principios
- Simplicidad primero: FastAPI + HTML/CSS/JS plano. Persistencia ligera (JSON/SQLite). Nada extra si no es necesario.
- Iterar con entregas verificables: cada hito debe correrse y probarse con `pytest` o `curl`.
- Compatibilidad con formato AVG y flujo del despachante: la UI asiste, el profesional decide.
- Debt consciente: lo que no suma valor inmediato, se documenta para después.


## Estado actual (evaluado con reglas y revisor)

- Contrato API: OK (JSON estándar con `success`, `/health` extendido, `/validate_items/`, `/generated/`, descargas). Validaciones de negocio devuelven `success=false` cuando aplica.
- Tests: OK (suite verde + smoke.sh). Casos robustos para decimales con coma y `origen` largos cubiertos.
- Deploy/operación: OK (`dev.sh`, `test.sh`, `prod.sh`, backups). `.env.example` creado. Guía Nginx+systemd documentada. Rotación de logs simple.
- UI/UX: panel de validación con conteo y lista, auto-validar, atajos Enter/Esc, autosave + indicador, “Descargar último”, barra de métricas `/health`, mapeo por cliente con “Restablecer/Borrar”.
 - Avance por fase: F0 100%, F1 100%, F2 100%, F3 100%, F4 100%, F5 80%.


## Fase 0 — Consolidación actual (semana 1)
Objetivo: una única app estable con tests verdes y UI coherente.

- Unificar servidor: usar `proyecto_maria/server_funcional.py` como base única.
- Alinear endpoints UI: `/process_operation/`, `/upload_excel/`, `/upload_pdf/`, `/download/{file}`.
- Fix mínimos:
  - Eliminar duplicado `@app.post('/logout')` en `server_nuevo.py` o deprecarlo.
  - Importar `RedirectResponse` donde se use.
  - En UI, asegurar rutas relativas correctas y mensajes de error amigables.
- Tests: adaptar `tests/` al modelo español (`pieza`, `descripcion`, etc.) o agregar traductor interno de payload.
- Criterios de aceptación:
  - `pytest` pasa en local (`run_tests.py` OK).
  - Subida Excel/PDF → agrupación → generación AVG funcional.
  - Revisión técnica (rol revisor) aprobada.
  
Estado: Completada.


## Fase 1 — Agrupación y Productividad (semana 2)
Objetivo: flujo de agrupación estable y rápido para 100 ítems.

- Backend: mantener lógica de extracción robusta y validar con `core/validations.py`.
- Frontend: mejorar agrupación (ya implementado), asegurar:
  - Reordenamiento estable por NCM (4 dígitos) y edición inline confiable.
  - Notas por NCM visibles (badge) y CRUD estable.
- Historial por cliente (persistencia JSON/SQLite vía `database.py`).
- Criterios de aceptación:
  - 100 ítems se editan y agrupan sin lag relevante en laptop media.
  - Guardado en historial si toggle activo.
  - Revisión técnica (rol revisor) aprobada.


## Fase 2 — Importación/Exportación de datos (semana 3)
Objetivo: interoperabilidad básica sin depender de integraciones externas.

- Export CSV por cliente (ya implementado) — revisar columnas y encabezados.
- Importación rápida desde planillas conocidas (mapas de columnas guardados por cliente).
- Descargar plantilla del cliente (Excel vacío con encabezados mapeados) y plantilla AVG “en blanco”.
- Criterios de aceptación:
  - Importar/Exportar funcionan en 3 clics; documentación breve en la UI.
  - Revisión técnica (rol revisor) aprobada.


## Fase 3 — Validaciones y calidad (semana 4)
Objetivo: reducir errores comunes antes de María.

- Validaciones adicionales opcionables en `core/validations.py` (switch en UI):
  - Chequeo de NCM: longitud 6–8 dígitos y prefijos válidos.
  - Reglas de negocio simples (peso total > 0, valores razonables).
- Reporte de inconsistencias descargable (CSV).
- Criterios de aceptación:
  - Errores se muestran en UI como lista accionable; exportable.
  - Smokes específicos en tests para casos de decimales y origen largo.
  - Revisión técnica (rol revisor) aprobada.


## Fase 4 — Integraciones avanzadas (post-MVP, Q4)
Objetivo: preparar el terreno para AFIP/María sin bloquear al usuario actual.

- Autenticación AFIP WSAA y WSCDC (mock) — prototipo aislado.
- NCM asistido (parser + validación externa):
  - Experimento con `siscomex-ncm` cacheado.
  - Sugerencias no vinculantes en UI (el despachante decide).
- RPA/Scraping controlado para portales (SeleniumBase) — sólo PoC en entorno separado.
- Criterios de aceptación:
  - PoC mock corre en la app principal sin romper endpoints.
  - Revisión técnica (rol revisor) aprobada.


## Fase 5 — Operación y despliegue (continuo)
Objetivo: facilitar uso diario y soporte.

- Scripts de arranque simples (uvicorn) y README actualizado.
- Backups automáticos de `data/` (historial/notas) — cron local.
- Observabilidad mínima: logs limpios; conteo de operaciones/errores.
 - Revisión técnica (rol revisor) aprobada.


## Roadmap de integraciones (derivado de idea_claude-md)
- AFIP WSAA/WSCDC
  - Artefactos: manejo de certificados (homologación), rotación y cache de TA.
  - API interna: `/afip/auth/test`, `/afip/cdc/constatar` (mock primero).
- NCM asistido
  - Servicio pequeño `ncm_suggest` con cache 7 días; UI con “Sugerir NCM”.
- RPA María
  - Caso de uso puntual (login y verificación). Guardar video/logs, sin producción.

## Decisiones sobre claude_2.md (adoptar / backlog / descartar)

- Adoptar ahora (en curso):
  - Validaciones ampliables (toggle en UI) y reporte CSV de errores.
  - Plantillas: “en blanco” y “del cliente” con encabezados mapeados.

- Backlog cercano (post Fase 2–3):
  - Sugerir NCM desde descripción (regex simple primero; luego `siscomex-ncm` con cache 7 días) como ayuda no vinculante.
  - Auto-mapeo sugerido de columnas (usar heurísticas/regex y mostrar propuesta editable en el modal).
  - Endpoints mock para AFIP (`/afip/*`) y prueba de flujo WSAA/WSCDC aislado.
  - BCRA cotización (opcional en métricas; no bloqueante del flujo AVG).

- Descartado por ahora (por simplicidad/alcance):
  - Microservicios/GraphQL/Docker Compose completo; mantenemos FastAPI único + scripts.
  - PWA/React/Next.js/Shadcn en este MVP; seguimos con HTML/CSS/JS plano.
  - RPA productivo y scraping de portales/terminales; sólo PoC controlado más adelante.
  - Integraciones terminales portuarias y SIMI/SEDI en producción.

## Preguntas clave para decidir siguiente sprint

1) Plantilla del cliente: ¿querés incluir ejemplos de filas o solo encabezados?
2) Auto-validación: ¿activada por defecto para todos los usuarios o recordamos última preferencia?
3) Validaciones extra: ¿dejamos pre‑tildadas NCM 6–8 dígitos y “valores razonables” o que el usuario las active?
4) Mapeo por cliente: ¿hay 2–3 clientes prioritarios para pre-cargar mapeos comunes?
5) ¿Te sirve ver cotización BCRA en la barra de métricas o lo dejamos en backlog?
6) Deploy: ¿vamos a Ubuntu + Nginx ya en el host final? (puerto/domino y logs esperados)


## Métricas de éxito
- Tiempo de carga y agrupación < 2 s con 100 ítems.
- 0 crashes en generación AVG en 50 ejecuciones consecutivas.
- 90% de operaciones con historial guardado cuando el toggle está activo.


## Próximos pasos (operativos)
1) Crear `.env.example` y documentar variables (incl. `DATA_DIR`).
2) Guía de deploy con Nginx + systemd (servicio, logs/rotación simple).
3) Smokes `/validate_items/` (decimales coma, origen largo) y UX: atajos Enter/Esc + “Limpiar borrador”.


## Anexos
- Referencia de endpoints y archivos clave en `documentacion_tecnica/README.md`.
- Rol y checklist de revisión en `.cursor/rules/rol-revisor.mdc`.
- Plan avanzado completo en `idea_claude-md` (pendiente de integración por fases).
