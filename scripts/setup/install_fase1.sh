#!/bin/bash

echo "🚀 Instalando MARIA Fase 1 - Escalabilidad"
echo "=========================================="

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no encontrado. Instala Python 3.8+"
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"

# Instalar dependencias de base de datos
echo "📦 Instalando dependencias de base de datos..."
pip install -r requirements-db.txt

# Configurar PostgreSQL
echo "🗄️  Configurando PostgreSQL..."
./setup_postgres.sh

# Configurar Redis
echo "🔄 Configurando Redis..."
./setup_redis.sh

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p logs
mkdir -p data/backups
mkdir -p data/generated

# Verificar instalación
echo "🔍 Verificando instalación..."

# Test PostgreSQL
if psql -h localhost -U maria_user -d maria_db -c "SELECT version();" &>/dev/null; then
    echo "✅ PostgreSQL configurado correctamente"
else
    echo "⚠️  PostgreSQL no conecta. Revisa la configuración"
fi

# Test Redis
if redis-cli ping &>/dev/null; then
    echo "✅ Redis configurado correctamente"
else
    echo "⚠️  Redis no conecta. Revisa la configuración"
fi

# Configurar variables de entorno
echo "⚙️  Configurando variables de entorno..."
echo ""
echo "Agrega estas líneas a tu archivo .env:"
echo "----------------------------------------"
cat env_database.txt
echo ""
cat env_logging.txt
echo "----------------------------------------"

echo ""
echo "🎉 Instalación de Fase 1 completada!"
echo ""
echo "📋 Para activar las nuevas funcionalidades:"
echo "   1. Agrega las variables de entorno a tu .env"
echo "   2. Reinicia el servidor con ./start_server.sh"
echo "   3. Visita http://127.0.0.1:8010/api/monitoring/dashboard"
echo ""
echo "🔧 Endpoints nuevos disponibles:"
echo "   - /api/database/status - Estado de PostgreSQL"
echo "   - /api/cache/status - Estado de Redis"
echo "   - /api/logs/status - Estado del logging"
echo "   - /api/monitoring/dashboard - Dashboard completo"
echo "   - /api/health/detailed - Health check mejorado"
