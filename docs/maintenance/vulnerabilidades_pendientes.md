# Vulnerabilidades de dependencias pendientes

> Última actualización: 2026-06-14
> Detectadas por auditoría automática (`reports/audit_proyecto.json`, `reports/audit_main.json`).
> NO son vulnerabilidades propias del negocio; son actualizaciones de librerías de terceros.
> Prioridad: media. Se sugiere atacar en una ventana de mantenimiento tranquila, separada de olas de producto.

---

## 1. `requests` — filtrado de credenciales `.netrc`

- **ID:** GHSA-9hjg-9r4m-mvj7 / CVE-2024-47081
- **Versión actual:** < 2.32.4
- **Fix:** `requests>=2.32.4`
- **Impacto:** Podría filtrar credenciales `.netrc` a terceros si se procesan URLs maliciosamente construidas.
- **Riesgo para CDI:** Bajo. No usamos `.netrc` ni armamos URLs con input no sanitizado de usuarios.
- **Esfuerzo:** Bajo (requirements.txt + tests).

---

## 2. `pdfminer.six` — ejecución de código arbitrario

- **ID:** GHSA-wf5f-4jwr-ppcp
- **Versión actual:** < 20251107
- **Fix:** `pdfminer.six>=20251107`
- **Impacto:** Un PDF malicioso podría ejecutar código arbitrario via pickle deserializado.
- **Riesgo para CDI:** Medio. Procesamos PDFs de clientes; aunque el flujo pasa por Gemini Vision, pdfminer es parte de la cadena de extracción.
- **Esfuerzo:** Medio. Requiere validar que `pdf_extractor.py` siga funcionando después del upgrade.

---

## 3. `starlette` — DoS multipart y bloqueo de event loop

- **IDs:** GHSA-f96h-pmfr-66vw / CVE-2024-47874, GHSA-2c2j-9gv5-cj73 / CVE-2025-54121
- **Versión actual:** < 0.40.0 / < 0.47.2
- **Fix:** `starlette>=0.47.2` (requiere actualizar FastAPI y sus deps)
- **Impacto:**
  - DoS por subida de campos multipart muy grandes sin `filename`.
  - Bloqueo del event loop al escribir archivos grandes a disco.
- **Riesgo para CDI:** Medio. Tenemos endpoints de upload PDF/Excel públicos y autenticados.
- **Esfuerzo:** Medio-Alto. FastAPI se mueve junto con Starlette; puede haber breaking changes en middlewares/tests.

---

## Plan de ataque sugerido

1. Actualizar `requests` y `pdfminer.six` en un primer commit + tests.
2. Actualizar FastAPI/Starlette en un segundo commit + tests de upload y auth.
3. Correr smoke completo (upload, login, dashboard, generación MARIA) antes de mergear.
4. Staging 24h antes de producción.

---

## Referencias

- `reports/audit_proyecto.json`
- `reports/audit_main.json`
- Archivo generado por auditoría de dependencias del entorno.
