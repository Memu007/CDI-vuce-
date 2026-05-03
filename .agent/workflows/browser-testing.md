---
description: Preferencia de uso del browser interno para testing
---

# Regla: Browser Interno para Testing

**SIEMPRE** usar el browser subagent interno de Antigravity para testing visual.

## Beneficios:
- No abre ventanas externas en la máquina del usuario
- Las acciones quedan grabadas automáticamente como .webp
- Se pueden embeber las grabaciones en walkthroughs

## Cómo usar:
```
browser_subagent(
    TaskName="...",
    Task="...",
    RecordingName="nombre_descriptivo"
)
```

## NO hacer:
- No abrir Chrome/Safari manualmente
- No pedir al usuario que abra ventanas
- No usar URLs externas para screenshots
