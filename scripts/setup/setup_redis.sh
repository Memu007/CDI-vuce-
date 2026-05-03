#!/bin/bash

# Script para configurar Redis local para MARIA
echo "🔄 Configurando Redis para MARIA..."

# Verificar si Redis está instalado
if ! command -v redis-server &> /dev/null; then
    echo "❌ Redis no está instalado. Instalando con Homebrew..."
    brew install redis
else
    echo "✅ Redis encontrado"
fi

# Iniciar Redis
echo "🚀 Iniciando Redis..."
brew services start redis

# Verificar que Redis esté corriendo
echo "🔍 Verificando conexión..."
if redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis corriendo correctamente"
    
    # Configurar memoria máxima (opcional)
    redis-cli config set maxmemory 256mb
    redis-cli config set maxmemory-policy allkeys-lru
    
    echo "📊 Estado de Redis:"
    redis-cli info server | grep redis_version
    redis-cli info memory | grep used_memory_human
    
else
    echo "❌ Redis no responde"
    echo "💡 Intenta: brew services restart redis"
fi

echo ""
echo "🚀 Redis configurado:"
echo "   - Host: localhost:6379"
echo "   - Database: 0"
echo "   - Política de memoria: LRU (256MB)"
echo ""
echo "🔧 Para continuar:"
echo "   1. pip install redis"
echo "   2. Agregar ENABLE_REDIS=true al .env"
echo "   3. Reiniciar el servidor"
