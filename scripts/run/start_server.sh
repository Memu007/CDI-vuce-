#!/bin/bash
echo "🚀 Iniciando CACA Server..."
cd "/Users/Emi/Documents/despanchte nuevo"
source .venv/bin/activate
export PYTHONPATH=.

# Verificar .env
if ! grep -q "GEMINI_MODEL=gemini-1.5-flash" .env 2>/dev/null; then
    echo "⚠️  Configurando modelo LLM..."
    echo "GEMINI_MODEL=gemini-1.5-flash" >> .env
fi

echo "✅ Servidor iniciando en http://127.0.0.1:8010"
echo "✅ Dashboard: http://127.0.0.1:8010/app"
echo "✅ Health: http://127.0.0.1:8010/health"
uvicorn proyecto_maria.server_funcional:app --host 127.0.0.1 --port 8010 --reload

