#!/bin/bash

# Script para configurar PostgreSQL local para MARIA
echo "🗄️  Configurando PostgreSQL para MARIA..."

# Verificar si PostgreSQL está instalado
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL no está instalado. Instalando con Homebrew..."
    brew install postgresql@15
    brew services start postgresql@15
else
    echo "✅ PostgreSQL encontrado"
fi

# Crear usuario y base de datos
echo "📝 Creando usuario y base de datos..."

# Conectar como superusuario y crear usuario/db
psql postgres -c "CREATE USER maria_user WITH PASSWORD 'maria_pass';" 2>/dev/null || echo "Usuario ya existe"
psql postgres -c "CREATE DATABASE maria_db OWNER maria_user;" 2>/dev/null || echo "Base de datos ya existe"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE maria_db TO maria_user;" 2>/dev/null

echo "✅ PostgreSQL configurado:"
echo "   - Host: localhost:5432"
echo "   - Database: maria_db"
echo "   - User: maria_user"
echo "   - Password: maria_pass"

# Verificar conexión
echo "🔍 Verificando conexión..."
if psql -h localhost -U maria_user -d maria_db -c "SELECT version();" 2>/dev/null; then
    echo "✅ Conexión exitosa a PostgreSQL"
else
    echo "❌ Error conectando a PostgreSQL"
    echo "💡 Asegúrate de que PostgreSQL esté corriendo: brew services start postgresql@15"
fi

echo ""
echo "🚀 Para continuar:"
echo "   1. pip install -r requirements-db.txt"
echo "   2. Actualizar .env con DATABASE_URL"
echo "   3. Ejecutar inicialización desde el servidor"
