# 🤖 Script de Cambio de AI: Claude vs Z.AI GLM-4.6

## 📋 Descripción
Script simple para cambiar entre Claude (Anthropic) y Z.AI GLM-4.6 en Cursor/Claude Code con un solo comando.

## 🚀 Uso Rápido

### Opción 1: Comandos directos
```bash
cd "/Users/Emi/Documents/despanchte nuevo"

# Cambiar a Claude (Anthropic)
./cambiar_ai.sh claude

# Cambiar a Z.AI GLM-4.6
./cambiar_ai.sh zai

# Ver estado actual
./cambiar_ai.sh status
```

### Opción 2: Alias (Recomendado)
```bash
# Recargar shell (o cerrar y abrir terminal)
source ~/.zshrc

# Cambiar a Claude
aiclaude

# Cambiar a Z.AI GLM-4.6
aiglm

# Ver estado actual
aistatus
```

## ⚙️ Configuraciones

### Claude (Anthropic)
- **API Key**: `sk-ant-api03-***` (Suscripción $20USD)
- **Base URL**: `https://openrouter.ai/api/v1`
- **Modelo**: `claude-4.5-sonnet`

### Z.AI GLM-4.6
- **API Key**: `1b27eb1a61af4e4283aef0a105bce088.B8yJfnwGDeP96qOh`
- **Base URL**: `https://open.bigmodel.cn/api/paas/v4`
- **Modelo**: `glm-4.6`

## 🔧 ¿Qué cambia el script?

El script modifica 3 parámetros en:
`~/Library/Application Support/Cursor/User/settings.json`

1. `cursor.general.openaiApiKey` - La API key
2. `cursor.general.openaiBaseUrl` - La URL del endpoint
3. `claude-code.selectedModel` - El modelo seleccionado

## 🛡️ Seguridad

✅ **Backups automáticos**: Antes de cada cambio, crea un backup con timestamp
- Ubicación: `settings.json.backup.YYYYMMDD_HHMMSS`
- Siempre puedes revertir manualmente si es necesario

## 📋 Pasos para usar

1. **Ejecutar el comando** (ya sea `aiclaude` o `aiglm`)
2. **Verificar el cambio** con `aistatus`
3. **REINICIAR CURSOR completamente**:
   - Cmd + Q (Mac) o cerrar todas las ventanas
   - Volver a abrir Cursor
4. **Verificar en la UI** que el modelo cambió

## 🎯 Verificación

Después de reiniciar Cursor:
- Abre el panel de Claude Code
- En "Select a model" deberías ver el modelo correspondiente:
  - Claude: `claude-4.5-sonnet` o similar
  - Z.AI: `glm-4.6`

## 🔍 Troubleshooting

### Si no funciona:
1. Verifica que el comando se ejecutó sin errores
2. Revisa el archivo de configuración directamente
3. Asegúrate de reiniciar Cursor completamente
4. Revisa los backups si necesitas revertir

### Verificar manualmente:
```bash
# Ver API key actual
grep "cursor.general.openaiApiKey" ~/Library/Application\ Support/Cursor/User/settings.json

# Ver modelo actual
grep "claude-code.selectedModel" ~/Library/Application\ Support/Cursor/User/settings.json
```

## 📁 Archivos creados

- `cambiar_ai.sh` - Script principal
- `INSTRUCCIONES_CAMBIO_AI.md` - Este archivo
- Alias en `~/.zshrc` - Para acceso rápido
- Backups automáticos en `~/Library/Application Support/Cursor/User/`

---
🎉 **¡Listo!** Ahora puedes cambiar entre Claude y Z.AI GLM-4.6 con un solo comando.