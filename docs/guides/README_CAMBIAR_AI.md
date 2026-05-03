# 🤖 Script para Cambiar entre Claude y GLM en Cursor

Script simple para alternar entre Claude (Anthropic) y GLM-4.6 (Z.AI) en Cursor/Claude Code.

## 📋 Uso

### Ver estado actual
```bash
./cambiar_modelo_ai.sh status
```

### Cambiar a Claude (Anthropic)
```bash
./cambiar_modelo_ai.sh claude
```

### Cambiar a GLM-4.6 (Z.AI)
```bash
./cambiar_modelo_ai.sh glm
```

## ⚠️ Importante

1. **Reinicia Cursor** después de ejecutar el script para que los cambios surtan efecto.
2. El script crea un **backup automático** antes de cada cambio en:
   ```
   ~/Library/Application Support/Cursor/User/settings.json.backup.YYYYMMDD_HHMMSS
   ```

## 🔧 Qué hace el script

### Cambio a Claude:
- Cambia `claude-code.selectedModel` a `"claude-4.5-sonnet"`
- Mantiene la URL de OpenRouter (que soporta ambos modelos)

### Cambio a GLM:
- Cambia `claude-code.selectedModel` a `"glm-4.6"`
- Asegura que usa la URL de OpenRouter

## 📁 Archivo modificado

El script modifica:
```
~/Library/Application Support/Cursor/User/settings.json
```

## 🆘 Recuperación

Si algo sale mal, puedes restaurar desde el backup:
```bash
cp "$HOME/Library/Application Support/Cursor/User/settings.json.backup.FECHA" \
   "$HOME/Library/Application Support/Cursor/User/settings.json"
```

## 💡 Alternativas

También puedes cambiar manualmente desde la UI de Cursor:
1. Abre el panel de Claude Code
2. Haz clic en "Select a model"
3. Elige el modelo deseado


