# 🚀 Uso Rápido - Cambiar AI en Cursor

## Comandos Simples

```bash
# Ver qué modelo está activo ahora
./cambiar_modelo_ai.sh status

# Cambiar a Claude (Anthropic) - Más preciso pero más caro
./cambiar_modelo_ai.sh claude

# Cambiar a GLM-4.6 (Z.AI) - Más rápido y económico
./cambiar_modelo_ai.sh glm
```

## ⚠️ IMPORTANTE: Reiniciar Cursor

Después de ejecutar el script, **DEBES REINICIAR CURSOR** completamente:
1. Cmd + Q para salir de Cursor
2. Volver a abrir Cursor
3. El nuevo modelo estará activo

## 🎯 Diferencias entre los modelos

### Claude 4.5 Sonnet (Anthropic)
- ✅ Más preciso y detallado
- ✅ Mejor para tareas complejas
- ❌ Más costoso por token
- ❌ Puede ser más lento

### GLM-4.6 (Z.AI)
- ✅ Más rápido
- ✅ Más económico
- ✅ Bueno para tareas simples
- ❌ Menos preciso en tareas complejas

## 📁 Ubicación del script

```
/Users/Emi/Documents/despanchte nuevo/cambiar_modelo_ai.sh
```

## 🛡️ Seguridad

El script crea backups automáticos en:
```
~/Library/Application Support/Cursor/User/settings.json.backup.FECHA
```

Si algo sale mal, restaura el backup más reciente.

## 💡 Tip

Puedes crear un alias en tu `.zshrc`:
```bash
alias aiglm='cd "/Users/Emi/Documents/despanchte nuevo" && ./cambiar_modelo_ai.sh glm'
alias aiclaude='cd "/Users/Emi/Documents/despanchte nuevo" && ./cambiar_modelo_ai.sh claude'
alias aistatus='cd "/Users/Emi/Documents/despanchte nuevo" && ./cambiar_modelo_ai.sh status'
```

Después de añadir los alias:
```bash
source ~/.zshrc
```

Y luego puedes usar desde cualquier directorio:
```bash
aistatus    # Ver modelo actual
aiclaude    # Cambiar a Claude
aiglm       # Cambiar a GLM
```


