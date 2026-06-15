# Vulnerabilidades de dependencias pendientes

> Última actualización: 2026-06-14
> Detectadas por auditoría automática (`reports/audit_proyecto.json`, `reports/audit_main.json`).
> NO son vulnerabilidades propias del negocio; son actualizaciones de librerías de terceros.
> Prioridad: media. Se sugiere atacar en una ventana de mantenimiento tranquila, separada de olas de producto.

---

## Estado actual

### Resueltas (en `requirements.txt`)

| Paquete | Vulnerabilidad | Fix aplicado |
|---------|----------------|--------------|
| `requests` | GHSA-9hjg-9r4m-mvj7 / CVE-2024-47081 | `requests>=2.32.4` |
| `pdfminer.six` | GHSA-wf5f-4jwr-ppcp | `pdfminer.six>=20251107` |
| `starlette` | GHSA-f96h-pmfr-66vw / CVE-2024-47874, GHSA-2c2j-9gv5-cj73 / CVE-2025-54121 | `starlette>=0.47.2`, `fastapi>=0.115.0` |

### Pendiente (dev-only)

| Paquete | Vulnerabilidad | Fix disponible | Notas |
|---------|----------------|----------------|-------|
| `pytest` | GHSA-6w46-j5rx-g56g | `pytest>=9.0.3` | Solo afecta entornos de desarrollo/test. Queda pendiente porque el proyecto tiene conflictos preexistentes con `pytest-asyncio` que pueden agravarse al subir de pytest 8.x a 9.x. |

---

## 1. `requests` — filtrado de credenciales `.netrc` ✅ RESUELTO

- **ID:** GHSA-9hjg-9r4m-mvj7 / CVE-2024-47081
- **Fix aplicado:** `requests>=2.32.4` en `requirements.txt`
- **Impacto:** Podría filtrar credenciales `.netrc` a terceros si se procesan URLs maliciosamente construidas.
- **Riesgo para CDI:** Bajo. No usamos `.netrc` ni armamos URLs con input no sanitizado de usuarios.

---

## 2. `pdfminer.six` — ejecución de código arbitrario ✅ RESUELTO

- **ID:** GHSA-wf5f-4jwr-ppcp
- **Fix aplicado:** `pdfminer.six>=20251107` en `requirements.txt`
- **Impacto:** Un PDF malicioso podría ejecutar código arbitrario via pickle deserializado.
- **Riesgo para CDI:** Medio. Procesamos PDFs de clientes; aunque el flujo pasa por Gemini Vision, pdfminer es parte de la cadena de extracción.
- **Verificación:** Smoke de upload PDF/Excel sigue funcionando; suite completa **250 passed**.

---

## 3. `starlette` — DoS multipart y bloqueo de event loop ✅ RESUELTO

- **IDs:** GHSA-f96h-pmfr-66vw / CVE-2024-47874, GHSA-2c2j-9gv5-cj73 / CVE-2025-54121
- **Fix aplicado:** `starlette>=0.47.2`, `fastapi>=0.115.0` en `requirements.txt`
- **Impacto:**
  - DoS por subida de campos multipart muy grandes sin `filename`.
  - Bloqueo del event loop al escribir archivos grandes a disco.
- **Riesgo para CDI:** Medio. Tenemos endpoints de upload PDF/Excel públicos y autenticados.
- **Verificación:** Tests de upload y smokes de login/dashboard pasan.

---

## Plan de ataque sugerido

1. ✅ Actualizar `requests`, `pdfminer.six`, `starlette`/`fastapi` en `requirements.txt` + tests.
2. ✅ Correr smoke completo (upload, login, dashboard, generación MARIA) antes de mergear.
3. ⏳ Pendiente: evaluar upgrade de `pytest` a `>=9.0.3` en entorno de test, dado el conflicto preexistente con `pytest-asyncio`.
4. Staging 24h antes de producción.

---

## Referencias

- `requirements.txt`
- `reports/audit_proyecto.json`
- `reports/audit_main.json`
- Archivo generado por auditoría de dependencias del entorno.
