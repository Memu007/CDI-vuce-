#!/bin/bash

# Script para cambiar entre Claude Code y Z.AI GLM-4.6
# Autor: Claude Code Assistant
# Funciona cambiando la configuración de Cursor/Claude Code

# Colores para mejor visualización
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Archivo de configuración
SETTINGS_FILE="$HOME/Library/Application Support/Cursor/User/settings.json"

# Funciones de utilidad
crear_backup() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.backup.$timestamp"
    echo -e "${GREEN}✅ Backup creado: $SETTINGS_FILE.backup.$timestamp${NC}"
}

mostrar_estado() {
    if [[ ! -f "$SETTINGS_FILE" ]]; then
        echo -e "${RED}❌ Error: No se encuentra el archivo de configuración${NC}"
        echo "   Ubicación esperada: $SETTINGS_FILE"
        exit 1
    fi

    local api_key=$(grep '"cursor.general.openaiApiKey"' "$SETTINGS_FILE" | cut -d'"' -f4)
    local base_url=$(grep '"cursor.general.openaiBaseUrl"' "$SETTINGS_FILE" | cut -d'"' -f4)
    local model=$(grep '"claude-code.selectedModel"' "$SETTINGS_FILE" | cut -d'"' -f4)

    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📊 ESTADO ACTUAL DE CONFIGURACIÓN:${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if [[ "$api_key" == *"sk-ant-api"* ]]; then
        echo -e "${GREEN}✅ Proveedor: Claude (Anthropic)${NC}"
        echo -e "   API Key: ${api_key:0:20}..."
    elif [[ "$api_key" == "1b27eb1a61af4e4283aef0a105bce088"* ]]; then
        echo -e "${YELLOW}🟡 Proveedor: Z.AI (GLM)${NC}"
        echo -e "   API Key: ${api_key:0:20}..."
    else
        echo -e "${RED}❌ Proveedor: Desconocido${NC}"
        echo -e "   API Key: ${api_key:0:20}..."
    fi

    echo -e "   Base URL: $base_url"
    echo -e "   Modelo: $model"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

usar_claude() {
    echo -e "${BLUE}🔄 Cambiando a Claude (Anthropic)...${NC}"

    crear_backup

    # Cambiar API key de Anthropic
    sed -i '' 's/"cursor.general.openaiApiKey": "[^"]*"/"cursor.general.openaiApiKey": "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"/' "$SETTINGS_FILE"

    # Cambiar a OpenRouter (que funciona con Claude)
    sed -i '' 's|"cursor.general.openaiBaseUrl": "[^"]*"|"cursor.general.openaiBaseUrl": "https://openrouter.ai/api/v1"|' "$SETTINGS_FILE"

    # Cambiar modelo a Claude
    sed -i '' 's/"claude-code.selectedModel": "[^"]*"/"claude-code.selectedModel": "claude-4.5-sonnet"/' "$SETTINGS_FILE"

    echo -e "${GREEN}✅ Configurado para Claude (Anthropic)${NC}"
    echo -e "${YELLOW}⚠️  REINICIA CURSOR para aplicar los cambios${NC}"
}

usar_zai_glm() {
    echo -e "${YELLOW}🔄 Cambiando a Z.AI GLM-4.6...${NC}"

    crear_backup

    # Cambiar API key de Z.AI
    sed -i '' 's/"cursor.general.openaiApiKey": "[^"]*"/"cursor.general.openaiApiKey": "1b27eb1a61af4e4283aef0a105bce088.B8yJfnwGDeP96qOh"/' "$SETTINGS_FILE"

    # Cambiar a URL de Zhipu AI (probable para GLM-4.6)
    sed -i '' 's|"cursor.general.openaiBaseUrl": "[^"]*"|"cursor.general.openaiBaseUrl": "https://open.bigmodel.cn/api/paas/v4"|' "$SETTINGS_FILE"

    # Cambiar modelo a GLM-4.6
    sed -i '' 's/"claude-code.selectedModel": "[^"]*"/"claude-code.selectedModel": "glm-4.6"/' "$SETTINGS_FILE"

    echo -e "${GREEN}✅ Configurado para Z.AI GLM-4.6${NC}"
    echo -e "${YELLOW}⚠️  REINICIA CURSOR para aplicar los cambios${NC}"
}

# Función de ayuda
mostrar_ayuda() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🤖 SCRIPT DE CAMBIO DE AI - CLAUDE CODE / Z.AI${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo
    echo -e "${GREEN}USO:${NC}"
    echo -e "  $0              ${CYAN}→ Muestra estado actual${NC}"
    echo -e "  $0 claude       ${CYAN}→ Cambia a Claude (Anthropic)${NC}"
    echo -e "  $0 zai          ${CYAN}→ Cambia a Z.AI GLM-4.6${NC}"
    echo -e "  $0 status       ${CYAN}→ Muestra estado actual${NC}"
    echo -e "  $0 help         ${CYAN}→ Muestra esta ayuda${NC}"
    echo
    echo -e "${YELLOW}ALIAS RECOMENDADOS:${NC}"
    echo -e "  alias aiclaude='bash $0 claude'"
    echo -e "  alias aiglm='bash $0 zai'"
    echo
    echo -e "${RED}IMPORTANTE:${NC}"
    echo -e "  Siempre reinicia Cursor después de cambiar"
    echo
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Lógica principal
case "${1:-status}" in
    "claude"|"anthropic"|"c")
        usar_claude
        mostrar_estado
        ;;
    "zai"|"glm"|"z")
        usar_zai_glm
        mostrar_estado
        ;;
    "status"|"estado"|"s"|"")
        mostrar_estado
        ;;
    "help"|"ayuda"|"h"|"-h"|"--help")
        mostrar_ayuda
        ;;
    *)
        echo -e "${RED}❌ Opción desconocida: $1${NC}"
        echo
        mostrar_ayuda
        exit 1
        ;;
esac