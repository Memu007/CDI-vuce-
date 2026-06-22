# ========================================================================
# Dockerfile - CDI Sistema MARÍA
# Optimizado para Google Cloud Run (Producción)
# ========================================================================

# Stage 1: Build stage
FROM python:3.12-slim as builder

WORKDIR /app

# Instalar dependencias del sistema para build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Instalar gunicorn para producción (multi-worker)
RUN pip install --no-cache-dir --user gunicorn uvicorn[standard]

# ========================================================================
# Stage 2: Runtime stage (imagen final liviana)
# ========================================================================
FROM python:3.12-slim as runtime

# Instalar dependencias del sistema para runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar dependencias Python del builder
COPY --from=builder /root/.local /root/.local

# Copiar código del proyecto
COPY proyecto_maria ./proyecto_maria
COPY gunicorn_conf.py .

# Crear directorios necesarios
RUN mkdir -p data generated backups logs

# Asegurar que Python packages estén en PATH
ENV PATH=/root/.local/bin:$PATH

# Variables de entorno para Cloud Run
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080
ENV GEMINI_MODEL=gemini-3.1-flash-lite-preview

# Cloud Run usa la variable PORT (por defecto 8080)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Comando de inicio con Gunicorn + 1 Uvicorn worker (rate limiting con MemoryStorage requiere 1 solo proceso)
# Usa la variable PORT de Cloud Run
CMD exec gunicorn proyecto_maria.main:app \
    --bind 0.0.0.0:${PORT} \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
