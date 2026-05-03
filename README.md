# 🚀 CDI - Sistema MARÍA (Optimizador de Carga)

**Sistema integral para la validación, enriquecimiento y generación de archivos de carga (AVG) para el sistema MARIA.**

## 🌟 Resumen y Objetivo

Este sistema fue desarrollado para modernizar y asegurar el flujo de trabajo de los despachantes de aduana. El objetivo principal es **eliminar errores humanos** en la carga de datos y **automatizar la generación de archivos AVG**, garantizando la integridad y seguridad de la información sensible.

| Característica    | Detalle                                                       |
| :---------------- | :------------------------------------------------------------ |
| **Arquitectura**  | Monolito Modular (FastAPI + Vanilla JS)                       |
| **Base de Datos** | PostgreSQL (Async con SQLAlchemy)                             |
| **Seguridad**     | **Nivel Bancario** (Rate Limiting, CSRF Strict, JWT HttpOnly) |
| **IA Integrada**  | Google Gemini 2.0 (Extracción de datos de PDFs)               |
| **Validación**    | Pydantic (Backend) + Validación en Tiempo Real (Frontend)     |
| **Despliegue**    | Docker Ready / VPS (Ubuntu)                                   |

## ⚙️ Arquitectura y Seguridad

El sistema no es solo un generador de Excel; es una plataforma robusta diseñada para ser expuesta a internet de forma segura.

### 1. Núcleo de Seguridad (Hardening)

Implementamos una estrategia de defensa en profundidad para proteger el acceso y los datos:

- **Rate Limiting (Anti-Brute Force):** Bloqueo automático de IPs tras 5 intentos fallidos de login (ban de 15 minutos). Implementado en memoria para máxima velocidad.
- **Protección CSRF:** Cookies de sesión con `SameSite=Strict`, impidiendo que sitios maliciosos ejecuten acciones en nombre del usuario.
- **Sanitización XSS:** Todo input y output es sanitizado para prevenir inyección de código en el navegador.
- **Manejo de Sesiones:** JWT (JSON Web Tokens) almacenados exclusivamente en Cookies `HttpOnly`, inaccesibles via JavaScript.

### 2. Lógica de Negocio (Core)

El sistema procesa archivos complejos (Excel/PDF) y los normaliza:

- **Validación Básica:** Reglas estrictas de negocio antes de procesar cualquier dato.
- **Validación Inteligente (Premium):** Detecta errores comunes ANTES de oficializar:
  - NCM inválido o sospechoso
  - Peso/valor fuera de rango típico para el producto
  - Descripciones cortas que AFIP puede rechazar
  - Certificados requeridos (ANMAT, INTI, etc.)
- **Generación AVG:** Motor dedicado (`core/excel_generator.py`) que construye el formato binario exacto requerido por el Sistema MARIA.
- **IA Fallback:** Si el parser tradicional falla con un PDF, Google Gemini entra en acción para estructurar la data desordenada.

## 🛠️ Despliegue y Configuración

El proyecto está diseñado para ser "Plug & Play". Incluye scripts de automatización para el setup inicial.

### Archivos Clave

| Archivo                  | Función                                                                   |
| :----------------------- | :------------------------------------------------------------------------ |
| `setup.sh`               | **Script Mágico.** Crea entorno virtual, instala deps y configura la BD.  |
| `start_server.sh`        | Inicia el servidor de producción (Gunicorn) con la configuración óptima.  |
| `proyecto_maria/main.py` | Punto de entrada de la aplicación FastAPI.                                |
| `requirements.txt`       | Lista de dependencias optimizada (incluye `bcrypt`, `fastapi`, `pandas`). |

### 🚀 Instalación Rápida (VPS / Local)

```bash
# 1. Clonar y preparar entorno
git clone https://github.com/Memu007/CDI.git
cd CDI
./setup.sh

# 2. Configurar secretos
nano .env  # (Agregar GEMINI_API_KEY y credenciales DB)

# 3. Iniciar
./start_server.sh
```

## 🔒 Variables de Entorno

La configuración sensible se maneja exclusivamente via variables de entorno (`.env`).

| Variable          | Propósito                                                      |
| :---------------- | :------------------------------------------------------------- |
| `GEMINI_API_KEY`  | Llave para el motor de IA de Google.                           |
| `DATABASE_URL`    | String de conexión a PostgreSQL (o SQLite por defecto).        |
| `JWT_SECRET_KEY`  | Semilla para la firma criptográfica de tokens.                 |
| `MP_ACCESS_TOKEN` | (Opcional) Token de MercadoPago para pagos. Sin él, usa modo demo. |
| `SMTP_SERVER`     | (Opcional) Configuración para envío de emails transaccionales. |

## 🤝 Contribuciones

Este es un proyecto privado para uso profesional.

---

**Estado del Proyecto:** ✅ LISTO PARA PRODUCCIÓN (v2.1 - Ene 2026)

## 🚂 Deploy Rápido en Railway (Recomendado)

El proyecto está 100% pre-configurado para un despliegue automático en [Railway.app](https://railway.app/) gracias a los archivos `Dockerfile` y `railway.json`.

**Pasos para el despliegue:**
1. Crear una cuenta en [Railway](https://railway.app/).
2. Crear un nuevo proyecto y seleccionar **"Deploy from GitHub repo"**.
3. Conectar tu cuenta de GitHub y seleccionar este repositorio (`CDI`).
4. Añadir un plugin de base de datos **PostgreSQL** dentro del mismo proyecto de Railway.
5. Ir a la pestaña **Variables** del servicio de la aplicación y configurar:
   - `GEMINI_API_KEY`: Tu API Key de Google Gemini.
   - `JWT_SECRET_KEY`: Una cadena segura generada aleatoriamente.
   - `DATABASE_URL`: Referenciar a la variable de base de datos de Railway (ej. `${{Postgres.DATABASE_URL}}`).
6. El despliegue comenzará automáticamente. Railway detectará el `Dockerfile` y expondrá la aplicación en la web.

## 🚀 Deploy Alternativo (Google Cloud)

**[Ver DEPLOY.md](./DEPLOY.md)** - Guía de 3 pasos para deploy manual en GCP Cloud Run.

### 📋 Últimos Cambios (Marzo 2026)

- ✅ Preparación para Railway deployment con `railway.json`
- ✅ Security Pentest: Fixed IDOR + JWT vulnerabilities, Middlewares actualizados
- ✅ Rate Limiting robusto implementado (`core/rate_limit.py`)
- ✅ Database Stress Test y optimizaciones
- ✅ Pruebas Unitarias para Validaciones y Uploads mejoradas

