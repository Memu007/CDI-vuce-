#!/bin/bash
set -e

# Add current directory to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Export environment variables from .env
if [ -f .env ]; then
    echo "📦 Cargando variables de entorno desde .env..."
    set -a  # Automatically export all variables
    source .env
    set +a
    echo "✅ Variables cargadas"
fi

echo "🚀 Starting Gunicorn..."

# Iniciar Gunicorn usando el mismo entorno que python3
python3 -m gunicorn -c gunicorn_conf.py proyecto_maria.main:app
