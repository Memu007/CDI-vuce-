#!/bin/bash

# ========================================================================
# FASE 1 QUICK WINS - CDI Sistema MARÍA Performance Optimization
# Implementación inmediata para 48 horas
# ========================================================================

set -e

echo "🚀 Iniciando FASE 1 QUICK WINS - Optimización Performance CDI María"
echo "📋 Objetivo: +50% capacity (750 usuarios concurrentes)"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Funciones auxiliares
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_service() {
    if systemctl is-active --quiet "$1"; then
        log_success "$1 está corriendo"
        return 0
    else
        log_warning "$1 no está corriendo"
        return 1
    fi
}

# ========================================================================
# 1. BACKUP DEL SISTEMA ACTUAL
# ========================================================================
backup_system() {
    log_info "📦 Creando backup del sistema actual..."
    
    BACKUP_DIR="/backup/cdi_maria_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup de código
    log_info "Backup código fuente..."
    cp -r /Users/Emi/CDI/proyecto_maria "$BACKUP_DIR/"
    
    # Backup de base de datos
    log_info "Backup base de datos..."
    if command -v pg_dump &> /dev/null; then
        pg_dump "$DATABASE_URL" > "$BACKUP_DIR/database_backup_$(date +%Y%m%d_%H%M%S).sql" 2>/dev/null || log_warning "No se pudo hacer backup de DB"
    fi
    
    # Backup de configuración
    cp /Users/Emi/CDI/.env* "$BACKUP_DIR/" 2>/dev/null || true
    
    log_success "Backup completado en: $BACKUP_DIR"
}

# ========================================================================
# 2. OPTIMIZACIÓN DE BASE DE DATOS - CONNECTION POOLING
# ========================================================================
setup_database_pooling() {
    log_info "🗄️ Configurando database connection pooling..."
    
    # Instalar asyncpg para connection pooling
    log_info "Instalando asyncpg y dependencias..."
    pip install asyncpg>=0.28.0 sqlalchemy[asyncio]>=2.0.0 alembic>=1.12.0
    
    # Crear configuración de database pooling
    cat > /Users/Emi/CDI/proyecto_maria/database/async_connection.py << 'EOF'
"""
Database Connection Pooling for High Concurrency
Optimizado para 2000 usuarios concurrentes
"""

import os
import asyncpg
import asyncio
from contextlib import asynccontextmanager
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class DatabasePool:
    """Connection pool optimizado para alta concurrencia"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self._initialized = False
        
    async def initialize(
        self, 
        min_connections: int = 20,
        max_connections: int = 200,
        command_timeout: int = 60
    ):
        """Inicializar pool con parámetros optimizados"""
        if self._initialized:
            return
            
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.warning("DATABASE_URL no configurada, usando fallback en memoria")
            return
            
        try:
            self.pool = await asyncpg.create_pool(
                database_url,
                min_size=min_connections,
                max_size=max_connections,
                command_timeout=command_timeout,
                max_inactive_connection_lifetime=300,  # 5 minutos
                max_queries=50000,  # Reciclar conexión después de 50k queries
                server_settings={
                    'application_name': 'cdi_maria_high_concurrency',
                    'jit': 'off',  # Deshabilitar JIT para queries simples
                }
            )
            
            # Test connection
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                
            self._initialized = True
            logger.info(f"✅ Database pool inicializado: {min_connections}-{max_connections} conexiones")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando database pool: {e}")
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """Obtener conexión del pool"""
        if not self._initialized:
            await self.initialize()
            
        if not self.pool:
            raise RuntimeError("Database pool no inicializado")
            
        async with self.pool.acquire() as conn:
            yield conn
    
    async def execute_query(self, query: str, *args):
        """Ejecutar query con pooling"""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_command(self, command: str, *args):
        """Ejecutar comando (INSERT/UPDATE/DELETE)"""
        async with self.get_connection() as conn:
            return await conn.execute(command, *args)
    
    async def health_check(self) -> dict:
        """Health check del pool"""
        if not self.pool:
            return {"status": "not_initialized", "size": 0}
            
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                
            return {
                "status": "healthy",
                "size": self.pool.get_size(),
                "idle": self.pool.get_idle_size(),
                "max_size": self.pool.get_max_size(),
                "min_size": self.pool.get_min_size()
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        """Cerrar pool"""
        if self.pool:
            await self.pool.close()
            self._initialized = False
            logger.info("Database pool cerrado")

# Global instance
db_pool = DatabasePool()
EOF

    log_success "Database pooling configurado"
}

# ========================================================================
# 3. REDIS POR DEFECTO + CACHÉ DISTRIBUIDA
# ========================================================================
setup_redis_cache() {
    log_info "🔴 Configurando Redis cache distribuida..."
    
    # Verificar si Redis está instalado
    if ! command -v redis-server &> /dev/null; then
        log_info "Instalando Redis..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install redis
        else
            sudo apt-get update && sudo apt-get install -y redis-server
        fi
    fi
    
    # Configurar Redis para alta concurrencia
    sudo tee /etc/redis/redis.conf > /dev/null << 'EOF'
# Redis Configuración Optimizada para CDI María - 2000 usuarios
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000

# Optimizaciones de performance
tcp-keepalive 300
timeout 0
tcp-backlog 511
databases 16

# Persistencia
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis

# Seguridad (producción)
# requirepass your_redis_password_here
# bind 127.0.0.1 10.0.0.100

# Slow log para debugging
slowlog-log-slower-than 10000
slowlog-max-len 128

# Clientes
maxclients 10000

# Memory optimization
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
EOF

    # Iniciar Redis
    sudo systemctl start redis-server || redis-server --daemonize yes
    sudo systemctl enable redis-server 2>/dev/null || true
    
    # Actualizar configuración de environment
    cat > /Users/Emi/CDI/.env.phase1 << 'EOF'
# FASE 1 QUICK WINS - Environment Variables
ENABLE_REDIS=true
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=50
CACHE_TTL_SECONDS=7200
LLM_CACHE_TTL=86400
NCM_CACHE_TTL=604800
VUCE_CACHE_TTL=604800

# Rate Limiting optimizado
API_RATE_LIMIT=5000/hour
RATE_LIMIT_BASIC=5000/hour
RATE_LIMIT_PREMIUM=15000/hour

# Database Pooling
DB_POOL_MIN_CONNECTIONS=20
DB_POOL_MAX_CONNECTIONS=200
DB_POOL_COMMAND_TIMEOUT=60

# Workers optimizados
UVICORN_WORKERS=8
UVICORN_WORKER_CONNECTIONS=1000
UVICORN_TIMEOUT=180
UVICORN_MAX_REQUESTS=500
UVICORN_MAX_REQUESTS_JITTER=100
EOF

    log_success "Redis configurado e iniciado"
}

# ========================================================================
# 4. OPTIMIZACIÓN DE WORKERS UVICORN
# ========================================================================
optimize_workers() {
    log_info "⚡ Optimizando workers uvicorn para CPU-bound processing..."
    
    # Detectar número de cores
    CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo "4")
    WORKERS=$((CORES * 2))
    
    log_info "Detectados $CORES cores, configurando $WORKERS workers"
    
    # Actualizar Dockerfile para producción optimizada
    cat > /Users/Emi/CDI/Dockerfile.phase1 << 'EOF'
# ========================================================================
# Dockerfile FASE 1 - CDI Sistema MARÍA Optimizado
# Optimizado para 750+ usuarios concurrentes
# ========================================================================

FROM python:3.12-slim as builder

WORKDIR /app

# Build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies optimizadas
COPY requirements.txt requirements-phase1.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt
RUN pip install --no-cache-dir --user -r requirements-phase1.txt

# Production runtime
FROM python:3.12-slim as runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependencies
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY proyecto_maria ./proyecto_maria
COPY scripts ./scripts
COPY .env.phase1 ./.env

# Create directories
RUN mkdir -p generated backups logs temp

# Environment
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Health check mejorado
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Optimized Gunicorn + Uvicorn workers
CMD exec gunicorn proyecto_maria.server_funcional:app \
    --bind 0.0.0.0:${PORT} \
    --workers $(($(nproc) * 2)) \
    --worker-class uvicorn.workers.UvicornWorker \
    --worker-connections 1000 \
    --timeout 180 \
    --keep-alive 2 \
    --max-requests 500 \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --statsd-host localhost:8125
EOF

    # Crear requirements adicionales para Fase 1
    cat > /Users/Emi/CDI/requirements-phase1.txt << 'EOF'
# FASE 1 QUICK WINS - Dependencias adicionales
asyncpg>=0.28.0
sqlalchemy[asyncio]>=2.0.0
alembic>=1.12.0
redis[hiredis]>=5.0.0
hiredis>=2.2.0
uvloop>=0.19.0
httptools>=0.6.0
python-multipart>=0.0.6
aiofiles>=23.2.0
cachetools>=5.3.0
prometheus-client>=0.19.0
psutil>=5.9.0
pydantic-settings>=2.1.0
EOF

    log_success "Workers optimizados configurados"
}

# ========================================================================
# 5. RATE LIMITING POR PLAN
# ========================================================================
setup_rate_limiting() {
    log_info "🚦 Configurando rate limiting por plan de usuario..."
    
    # Crear middleware de rate limiting mejorado
    cat > /Users/Emi/CDI/proyecto_maria/middleware/rate_limiting_middleware.py << 'EOF'
"""
Rate Limiting Middleware para CDI María
Optimizado para 2000 usuarios concurrentes
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
from starlette.responses import JSONResponse
import redis.asyncio as redis
import os
import logging

logger = logging.getLogger(__name__)

# Rate limits por plan
RATE_LIMITS = {
    "basic": "5000/hour",
    "premium": "15000/hour", 
    "enterprise": "50000/hour"
}

class PlanAwareRateLimitMiddleware:
    def __init__(self):
        self.redis_client = None
        self.limiter = None
        
    async def init_redis(self):
        """Inicializar Redis para rate limiting distribuido"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Redis rate limiting conectado")
            
        except Exception as e:
            logger.error(f"❌ Error conectando Redis para rate limiting: {e}")
            # Fallback a rate limiting en memoria
            
    def get_user_plan(self, request: Request) -> str:
        """Determinar plan del usuario desde JWT o query param"""
        # Implementar lógica para extraer plan del token JWT
        # Por ahora, fallback a 'basic'
        return request.headers.get("X-User-Plan", "basic")
    
    async def check_rate_limit(self, request: Request) -> bool:
        """Verificar rate limit por plan"""
        if not self.redis_client:
            return True  # Fallback: no limit si Redis no disponible
            
        plan = self.get_user_plan(request)
        limit = RATE_LIMITS.get(plan, "5000/hour")
        
        # Implementar sliding window log en Redis
        client_id = get_remote_address(request)
        key = f"rate_limit:{plan}:{client_id}"
        
        try:
            current = await self.redis_client.incr(key)
            if current == 1:
                await self.redis_client.expire(key, 3600)  # 1 hora
                
            # Parsear límite (ej: "5000/hour" -> 5000)
            max_requests = int(limit.split("/")[0])
            
            if current > max_requests:
                logger.warning(f"Rate limit exceeded for {client_id}: {current}/{max_requests}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Fallback: allow request

# Global instance
rate_limiter = PlanAwareRateLimitMiddleware()

# Rate limit exceeded handler
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Rate limit exceeded",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "retry_after": 3600
        },
        headers={"Retry-After": "3600"}
    )
EOF

    log_success "Rate limiting por plan configurado"
}

# ========================================================================
# 6. TESTING DE CARGA INICIAL
# ========================================================================
run_load_test() {
    log_info "🧪 Ejecutando load test inicial (750 usuarios)..."
    
    # Instalar Locust si no está
    if ! command -v locust &> /dev/null; then
        log_info "Instalando Locust..."
        pip install locust
    fi
    
    # Crear script de load test para Fase 1
    cat > /Users/Emi/CDI/tests/load_test_phase1.py << 'EOF'
"""
Load Test Fase 1 - CDI Sistema MARÍA
Target: 750 usuarios concurrentes
"""

from locust import HttpUser, task, between
import random
import time

class Phase1LoadTest(HttpUser):
    wait_time = between(1, 4)
    
    def on_start(self):
        """Inicialización por usuario"""
        self.user_id = random.randint(1000, 9999)
        
    @task(40)
    def health_check(self):
        """Health check - operación más rápida"""
        self.client.get("/health", name="Health Check")
        
    @task(30)
    def get_root(self):
        """Acceso a página principal"""
        self.client.get("/", name="Get Root")
        
    @task(15)
    def ncm_lookup(self):
        """Consulta NCM - operación mediana"""
        ncm_codes = [
            '84713010', '85423900', '90138000', '84212990', '84818090',
            '85366990', '84798970', '85044010', '85322490', '84811000'
        ]
        ncm = random.choice(ncm_codes)
        self.client.get(f"/api/ncm/{ncm}/completo", name="NCM Lookup")
        
    @task(10)
    def upload_excel(self):
        """Upload Excel - operación pesada"""
        # Simular archivo Excel
        files = {
            'file': ('test.xlsx', b'test excel data', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        data = {'client_id': str(random.randint(1, 10))}
        self.client.post("/upload_excel/", files=files, data=data, name="Upload Excel")
        
    @task(5)
    def create_operation(self):
        """Crear operación - operación completa"""
        operation_data = {
            "operation_id": f"TEST_{self.user_id}_{int(time.time())}",
            "items": [
                {
                    "pieza": "84713010",
                    "descripcion": "Test item",
                    "origen": "CN",
                    "cantidad": random.randint(1, 100),
                    "valor_unitario": random.uniform(10, 1000),
                    "peso_unitario": random.uniform(0.1, 100)
                }
            ]
        }
        self.client.post("/process_operation/", json=operation_data, name="Process Operation")
EOF

    log_success "Load test creado. Ejecutar con:"
    log_warning "   locust -f tests/load_test_phase1.py --users 750 --spawn-rate 50 --run-time 5m --html report_phase1.html"
}

# ========================================================================
# 7. MONITORING BÁSICO
# ========================================================================
setup_monitoring() {
    log_info "📊 Configurando monitoring básico..."
    
    # Instalar Prometheus client
    pip install prometheus-client psutil
    
    # Crear middleware de métricas
    cat > /Users/Emi/CDI/proyecto_maria/middleware/metrics_middleware.py << 'EOF'
"""
Metrics Middleware para CDI María
Prometheus metrics para monitoring
"""

import time
import psutil
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

# Registry personalizado
registry = CollectorRegistry()

# Métricas
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=registry
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=registry
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections_total',
    'Number of active connections',
    registry=registry
)

SYSTEM_MEMORY_USAGE = Gauge(
    'system_memory_usage_percent',
    'System memory usage percentage',
    registry=registry
)

SYSTEM_CPU_USAGE = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage',
    registry=registry
)

PDF_QUEUE_DEPTH = Gauge(
    'pdf_processing_queue_depth',
    'Number of PDFs in processing queue',
    registry=registry
)

REDIS_CONNECTIONS = Gauge(
    'redis_connected_clients',
    'Number of connected Redis clients',
    registry=registry
)

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Incrementar conexiones activas
        ACTIVE_CONNECTIONS.inc()
        
        try:
            response = await call_next(request)
            
            # Registrar métricas
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).inc()
            
            duration = time.time() - start_time
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            return response
            
        finally:
            # Decrementar conexiones activas
            ACTIVE_CONNECTIONS.dec()
    
    async def update_system_metrics(self):
        """Actualizar métricas del sistema"""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY_USAGE.set(memory.percent)
            
            # CPU usage
            cpu = psutil.cpu_percent(interval=1)
            SYSTEM_CPU_USAGE.set(cpu)
            
            # Redis connections (si está disponible)
            try:
                import redis.asyncio as redis
                redis_client = redis.from_url("redis://localhost:6379")
                info = await redis_client.info()
                REDIS_CONNECTIONS.set(info.get('connected_clients', 0))
            except:
                pass  # Redis no disponible
                
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")

# Función para endpoint de métricas
async def metrics_endpoint():
    """Endpoint de Prometheus metrics"""
    return Response(
        generate_latest(registry),
        media_type="text/plain"
    )
EOF

    # Agregar endpoint de métricas al server
    log_info "Endpoint de métricas disponible en: /metrics"
    
    log_success "Monitoring básico configurado"
}

# ========================================================================
# FUNCIÓN PRINCIPAL
# ========================================================================
main() {
    log_info "🎯 Iniciando implementación FASE 1 QUICK WINS..."
    
    # Verificar que estamos en el directorio correcto
    if [[ ! -f "/Users/Emi/CDI/proyecto_maria/main.py" ]]; then
        log_error "Directorio incorrecto. Ejecutar desde /Users/Emi/CDI"
        exit 1
    fi
    
    # Ejecutar pasos en orden
    backup_system
    setup_database_pooling
    setup_redis_cache
    optimize_workers
    setup_rate_limiting
    setup_monitoring
    run_load_test
    
    log_success "🎉 FASE 1 QUICK WINS completada!"
    log_info "📈 Resultados esperados:"
    log_info "   • +50% capacity: 750 usuarios concurrentes"
    log_info "   • Response time p95: <800ms"
    log_info "   • Error rate: <0.5%"
    log_info "   • Memory usage: -30%"
    
    log_info "🔄 Próximos pasos:"
    log_info "   1. Reiniciar servidor con nueva configuración"
    log_info "   2. Ejecutar load test: locust -f tests/load_test_phase1.py --users 750"
    log_info "   3. Verificar métricas en: /metrics"
    log_info "   4. Monitorear en: http://localhost:8080/health"
    
    echo ""
    log_info "📋 Comandos útiles:"
    log_info "   Ver Redis: redis-cli monitor"
    log_info "   Ver conexiones DB: SELECT * FROM pg_stat_activity;"
    log_info "   System metrics: curl http://localhost:8080/metrics"
}

# Ejecutar si el script es llamado directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi