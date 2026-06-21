# Fix NCM Assistant Paywall

## Diagnóstico

1. **Bug de cálculo de días de trial** (`app_v2.js:620`): `daysLeft` tiene un `* 60` extra → trial de 14 días muestra "1 día" y después desaparece el banner hasta que vence.
2. **Modal de pago con texto incorrecto** (`app_v2.js:42-58`): handler de 402 pasa `confirmText` e `icon` pero `confirmDialog` espera `acceptText` y `kind`.
3. **Botón "Asistente" no responde**: no reproducible en test. Probablemente el modal de pago (dialog nativo con `showModal()`) bloqueó la página después de un 402 previo.

## Plan

### Paso 1: Fix cálculo daysLeft en `app_v2.js`
- Línea 620: cambiar `1000 * 60 * 60 * 60 * 24` → `1000 * 60 * 60 * 24`

### Paso 2: Fix opciones del modal 402 en `app_v2.js`
- Líneas 42-58: cambiar `confirmText` → `acceptText`, `icon` → `kind: 'warning'`

### Paso 3: Verificación
- `node --check` en `app_v2.js`
- Commit + push

### Paso 4: Pedir al usuario que valide en producción
