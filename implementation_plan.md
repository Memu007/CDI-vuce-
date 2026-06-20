# Plan de Implementación Técnico (Versión V3 - M&A Audited)

> [!CAUTION]
> **Atención M&A / Auditores:** Este plan ha sido reescrito íntegramente tras la auditoría técnica de Due Diligence. Se descartó el roadmap fantasioso de 30 días, se eliminaron los riesgos de seguridad detectados (como el split-brain auth y dependencias circulares) y se robusteció la capa de seguridad del nuevo endpoint público.

## User Review Required

**Revisión del Plan V3:**
Por favor revisen las mitigaciones técnicas (especialmente la mudanza de la auth a `dependencies.py` y la estructura criptográfica de la Fase 2). ¿Damos el OK definitivo para empezar a codear?

---

## FASE 0: Extracción de Métricas de Tracción (Pre-Pitch)
Antes de escribir una línea de código del Pilar B, necesitamos validar el "Product-Market Fit" real para la narrativa M&A.
- **Acción:** Correr una query SQL en producción para calcular el **Cohort Retention** de los 5 usuarios activos. Necesitamos saber qué porcentaje sigue activo mes a mes y su frecuencia de uso real. 
- *(Esto es trabajo de análisis de datos, no de desarrollo, pero es bloqueante para el Pitch de $50k).*

---

## FASE 1: Mitigaciones Críticas de Due Diligence (Quick Wins)

### 1.1. Sanitización de Endpoints y Swagger Público
- **En `main.py`:** Condicionar `docs_url=None`, `redoc_url=None`, y **`openapi_url=None`** si la app corre en producción.
- **Dead Code:** Eliminar **toda la carpeta** `proyecto_maria/routers/_deprecated/` (los 7 archivos) para no dejar huellas en escáneres estáticos de seguridad.

### 1.2. Unificación de Auth Segura (Evitando Circular Imports)
- **El Problema:** El `get_current_user` robusto vive en `main.py`. Si lo movemos a `jwt_utils.py`, generamos importaciones circulares en el middleware.
- **La Solución:** Crear un nuevo módulo agnóstico `proyecto_maria/auth/dependencies.py`.
- **Refactor:** Mover el `get_current_user` robusto a este nuevo archivo. Hacer que `main.py`, `plan_middleware.py`, y `roles.py` importen desde allí. Auditar dependencias previas de `TestingHTTPBearer`.

### 1.3. Fallback de Datos Aduaneros (No más "Fake Data" en Prod)
- **Riesgo:** Si el scraper cae, servir datos mockeados en producción genera riesgo legal por multas.
- **Acción:** Si falla Tarifar o VUCE oficial, verificamos el caché (`ncm_cache`). Si hay caché, devolvemos HTTP 503 con la data marcada estrictamente como **stale** y se renderiza un banner explícito. **Si no hay caché (NCM nuevo), se devuelve HTTP 503 puro sin body de datos, deteniendo la operación.** Se prohíbe el uso de datos `fake` en el entorno de producción.

### 1.4. Transferencia de Conocimiento de Dominio
- **Acción:** Crear la estructura y template base de `docs/DOMINIO_ADUANERO.md`. 
- **Nota Importante:** La IA solo estructurará el documento basándose en el historial. El usuario (Owner/Especialista de Dominio) deberá completarlo manualmente, ya que inventar reglas aduaneras destruiría la credibilidad en Due Diligence.

---

## FASE 2: Ejecución del Pilar B (Efecto Red B2B2B - Presupuestos Públicos)

### 2.1. Capa de Datos Segura (`proyecto_maria/models/quote.py`)
Creación del modelo `PublicQuote` en SQLAlchemy:
- `hash_id` (String primary_key): ID generado criptográficamente.
- **`owner_username` (String, ForeignKey("users.username"))**: Respetando la convención de FKs del repo.
- `snapshot_data` (JSON): Tipo de cambio, alícuotas, costo total.
- `created_at` (DateTime).
- **`expires_at` (DateTime):** Los presupuestos vivirán por 30 días para no exponer data obsoleta y controlar el crecimiento de la tabla. Habrá **lazy cleanup** (si un GET accede a un hash vencido, retorna 404 y borra el registro) y limpieza por script periódico.

### 2.2. Capa API y Seguridad Crítica (`routes/quote_router.py`)
- **`POST /api/quotes/share` (Autenticado):** Recibe el payload del presupuesto, genera un ID robusto usando **`secrets.token_urlsafe(16)`** (~128 bits, resistente a brute-force) y persiste en DB.
- **`GET /api/quotes/public/{hash}` (Sin Auth):** Retorna el JSON. **Requisito excluyente:** Estará protegido por un **Rate Limit estricto** (ej. 10 req/min por IP) usando la librería `slowapi` ya instalada en el proyecto para evitar escaneos masivos.

### 2.3. Capa Frontend y Efecto Moat (`templates/public_quote.html`)
- UI mobile-first para el Importador.
- Mostrará el cálculo de aranceles.
- **Branding V1:** Extraeremos el `company_name` (o el nombre del usuario) para mostrar: *"Presupuesto estimado generado por [Nombre de Agencia]"*. (El soporte para logos de imagen subidos se anotará en el backlog de la Fase 3, pero el branding de texto entra ahora para asegurar el efecto red).
