#!/bin/bash

# Script para cambiar entre Claude (Anthropic) y GLM-4.6 (Z.AI) en Cursor
# Uso: ./cambiar_modelo_ai.sh [claude|glm|status]

SETTINGS_FILE="$HOME/Library/Application Support/Cursor/User/settings.json"

# Configuraciones
# Ambos modelos usan OpenRouter, solo cambiamos el selectedModel
CLAUDE_MODEL="opus"  # Modelo Opus de Claude (aparece en el menú de Cursor)
GLM_MODEL="glm-4.6"  # Modelo GLM en OpenRouter
OPENROUTER_URL="https://openrouter.ai/api/v1"

# Función para mostrar el estado actual
mostrar_estado() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 Estado actual de Cursor:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if grep -q '"claude-code.selectedModel": "glm-4.6"' "$SETTINGS_FILE"; then
        echo "✅ Modelo actual: GLM-4.6 (Z.AI)"
    elif grep -q '"claude-code.selectedModel": "opus"' "$SETTINGS_FILE"; then
        echo "✅ Modelo actual: Opus (Claude - Anthropic)"
    elif grep -q '"claude-code.selectedModel": "haiku"' "$SETTINGS_FILE"; then
        echo "✅ Modelo actual: Haiku (Claude - Anthropic)"
    elif grep -q '"claude-code.selectedModel": "claude' "$SETTINGS_FILE"; then
        echo "✅ Modelo actual: Claude (Anthropic)"
    else
        MODELO_ACTUAL=$(grep '"claude-code.selectedModel"' "$SETTINGS_FILE" | sed 's/.*": "//;s/".*//')
        echo "✅ Modelo actual: $MODELO_ACTUAL"
    fi
    
    echo ""
    grep '"cursor.general.openaiBaseUrl"' "$SETTINGS_FILE" | sed 's/^[[:space:]]*//' || echo "URL no configurada"
    grep '"claude-code.selectedModel"' "$SETTINGS_FILE" | sed 's/^[[:space:]]*//' || echo "Modelo no configurado"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Función para cambiar a Claude (Anthropic)
cambiar_a_claude() {
    echo "🔄 Cambiando a Claude (Anthropic)..."
    
    # Backup
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Cambiar modelo a Claude (mantener OpenRouter URL)
    sed -i '' 's|"claude-code.selectedModel": "[^"]*"|"claude-code.selectedModel": "'"$CLAUDE_MODEL"'"|' "$SETTINGS_FILE"
    
    # Asegurar que la URL sea OpenRouter
    sed -i '' 's|"cursor.general.openaiBaseUrl": "[^"]*"|"cursor.general.openaiBaseUrl": "'"$OPENROUTER_URL"'"|' "$SETTINGS_FILE"
    
    echo "✅ Cambiado a Claude (Anthropic)"
    echo "⚠️  Reinicia Cursor para aplicar los cambios"
}

# Función para cambiar a GLM (Z.AI)
cambiar_a_glm() {
    echo "🔄 Cambiando a GLM-4.6 (Z.AI)..."
    
    # Backup
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Cambiar modelo a GLM (mantener OpenRouter URL)
    sed -i '' 's|"claude-code.selectedModel": "[^"]*"|"claude-code.selectedModel": "'"$GLM_MODEL"'"|' "$SETTINGS_FILE"
    
    # Asegurar que la URL sea OpenRouter
    sed -i '' 's|"cursor.general.openaiBaseUrl": "[^"]*"|"cursor.general.openaiBaseUrl": "'"$OPENROUTER_URL"'"|' "$SETTINGS_FILE"
    
    echo "✅ Cambiado a GLM-4.6 (Z.AI)"
    echo "⚠️  Reinicia Cursor para aplicar los cambios"
}

# Menú principal
case "$1" in
    claude)
        cambiar_a_claude
        echo ""
        mostrar_estado
        ;;
    glm)
        cambiar_a_glm
        echo ""
        mostrar_estado
        ;;
    status)
        mostrar_estado
        ;;
    *)
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🤖 Script de Cambio de Modelo AI - Cursor"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Uso: $0 [claude|glm|status]"
        echo ""
        echo "Opciones:"
        echo "  claude  - Cambiar a Claude (Anthropic)"
        echo "  glm     - Cambiar a GLM-4.6 (Z.AI)"
        echo "  status  - Ver configuración actual"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        mostrar_estado
        ;;
esac


