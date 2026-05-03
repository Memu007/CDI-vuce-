#!/bin/bash

# Script de instalación de herramientas MCP para desarrollo web
# Ejecutar con: bash install_mcp_tools.sh

set -e  # Salir si hay errores

echo "🚀 Instalando herramientas MCP para desarrollo web..."
echo "=================================================="

# Verificar si Node.js está instalado
if ! command -v node &> /dev/null; then
    echo "❌ Node.js no está instalado. Instalando..."
    # Instalar Node.js usando Homebrew (macOS)
    if command -v brew &> /dev/null; then
        brew install node
    else
        echo "❌ Homebrew no está instalado. Por favor instala Node.js manualmente desde https://nodejs.org/"
        exit 1
    fi
fi

echo "✅ Node.js versión: $(node --version)"
echo "✅ npm versión: $(npm --version)"

# Crear directorio para herramientas MCP
mkdir -p mcp_tools
cd mcp_tools

echo ""
echo "📦 1. Instalando Chrome DevTools MCP..."
echo "======================================"
if [ ! -d "chrome-devtools-mcp" ]; then
    git clone https://github.com/ChromeDevTools/chrome-devtools-mcp.git
    cd chrome-devtools-mcp
    npm install
    echo "✅ Chrome DevTools MCP instalado"
    cd ..
else
    echo "✅ Chrome DevTools MCP ya existe"
fi

echo ""
echo "📦 2. Instalando Browser Tools MCP..."
echo "===================================="
npm install -g @agentdeskai/browser-tools-mcp@1.2.0
npm install -g @agentdeskai/browser-tools-server@1.2.0
echo "✅ Browser Tools MCP instalado"

echo ""
echo "📦 3. Instalando Puppeteer MCP..."
echo "================================="
npm install -g @modelcontextprotocol/server-puppeteer
echo "✅ Puppeteer MCP instalado"

echo ""
echo "📦 4. Instalando Playwright MCP..."
echo "=================================="
npm install -g @modelcontextprotocol/server-playwright
echo "✅ Playwright MCP instalado"

echo ""
echo "📦 5. Instalando dependencias del navegador para Playwright..."
echo "============================================================="
npx playwright install chromium
echo "✅ Dependencias de Playwright instaladas"

echo ""
echo "📦 6. Instalando MCP Code Editor..."
echo "==================================="
# MCP Code Editor se instala como extensión, pero podemos preparar el entorno
echo "✅ MCP Code Editor preparado (se instala como extensión)"

echo ""
echo "📦 7. Instalando Gooey..."
echo "========================"
# Gooey es una aplicación de escritorio, verificar si está disponible
if command -v brew &> /dev/null; then
    echo "Instalando Gooey via Homebrew..."
    brew install --cask gooey 2>/dev/null || echo "⚠️  Gooey no disponible via Homebrew, instalar manualmente"
else
    echo "⚠️  Instala Gooey manualmente desde: https://github.com/GooeyAI/Gooey"
fi

echo ""
echo "🎉 ¡Instalación completada!"
echo "=========================="
echo ""
echo "📋 Próximos pasos:"
echo "1. Configura Claude Desktop para usar estos MCPs"
echo "2. Reinicia Claude Desktop"
echo "3. Prueba las herramientas con comandos como:"
echo "   - 'Lanza un navegador y navega a google.com'"
echo "   - 'Inspecciona el elemento X en la página'"
echo ""
echo "📁 Herramientas instaladas en: $(pwd)"
echo "🔧 Para configurar Claude Desktop, edita el archivo de configuración MCP"

