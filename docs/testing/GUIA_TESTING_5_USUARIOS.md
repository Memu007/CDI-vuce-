# 🧪 Guía de Testing - CDI Sistema MARÍA
## Pre-Testing con 5 Usuarios

**Fecha**: 2025-10-20
**Versión**: CDI v2.0
**Objetivo**: Validar funcionalidad core con 5 testers reales antes del lanzamiento
**Duración estimada**: 20-30 minutos por persona

---

## 🎯 INFORMACIÓN PARA TESTERS

### Credenciales de Acceso

**URL del sistema**: http://127.0.0.1:8001

**Usuarios disponibles**:

| Usuario | Contraseña | Plan | Características |
|---------|-----------|------|----------------|
| `basico` | `basico123` | Básico | Upload Excel, generar AVG |
| `premium` | `premium123` | Premium | Todo lo básico + PDF, Clientes, Calculadora |

### Archivos de Prueba

Los siguientes archivos están disponibles en la carpeta `samples/`:

- `test_excel_web.xlsx` - Excel válido con items correctos
- `test_invoice.pdf` - Factura PDF para extracción con IA
- `FACTURA_DESORDENADA_MEZCLADA_v2.xlsx` - Excel con errores (para probar validación)

---

## ✅ CASOS DE PRUEBA

### 📋 PARA USUARIO BÁSICO (basico/basico123)

#### Caso 1: Upload Excel y Generar AVG (CRÍTICO)
**Objetivo**: Verificar flujo principal end-to-end

**Pasos**:
1. Login con `basico` / `basico123`
2. En el dashboard, buscar la zona de upload/drag&drop
3. Subir archivo: `test_excel_web.xlsx`
4. **Verificar**: Los items aparecen en la tabla
5. **Verificar**: Los campos NCM, descripción, cantidad, etc. están poblados
6. Click en botón "Generar Excel" o "Generar AVG"
7. **Verificar**: Se muestra spinner "Generando Excel AVG..."
8. **Verificar**: Se descarga el archivo automáticamente
9. Abrir el archivo descargado en Excel
10. **Verificar**: Tiene 13 columnas y los datos coinciden

**Resultado esperado**: ✅ Excel AVG generado correctamente
**Tiempo estimado**: 3-5 minutos

---

#### Caso 2: Excel con Errores - Validación Automática
**Objetivo**: Verificar que el sistema filtra items inválidos

**Pasos**:
1. Login con `basico` / `basico123`
2. Subir archivo: `FACTURA_DESORDENADA_MEZCLADA_v2.xlsx`
3. **Verificar**: Aparece mensaje indicando items con errores
4. **Verificar**: Solo se procesan los items válidos (5 de 8)
5. Revisar el panel de validaciones (semáforo 🟢🟡🔴)
6. **Verificar**: Muestra 3 items filtrados por errores
7. Intentar generar Excel
8. **Verificar**: El Excel solo contiene los 5 items válidos

**Resultado esperado**: ✅ Filtrado automático funciona correctamente
**Tiempo estimado**: 4-6 minutos

---

#### Caso 3: Restricción de Features Premium
**Objetivo**: Verificar que plan básico no accede a features premium

**Pasos**:
1. Login con `basico` / `basico123`
2. Buscar en la interfaz las siguientes opciones:
   - "Subir PDF" o "Upload PDF"
   - "Gestión de Clientes" o "Clientes"
   - "Calculadora de Tributos"
3. **Verificar**: Estas opciones NO están visibles o están deshabilitadas
4. Intentar acceder directamente (si hay URL):
   - `/clientes`
   - `/calculadora`
5. **Verificar**: Redirige o muestra error de permisos

**Resultado esperado**: ✅ Plan básico correctamente restringido
**Tiempo estimado**: 2-3 minutos

---

### 💎 PARA USUARIO PREMIUM (premium/premium123)

#### Caso 4: PDF Extraction con IA (CRÍTICO)
**Objetivo**: Verificar extracción inteligente de datos desde PDF

**Pasos**:
1. Login con `premium` / `premium123`
2. Buscar la opción "Subir PDF" en el dashboard
3. Subir archivo: `test_invoice.pdf`
4. **Verificar**: Aparece barra de progreso con etapas:
   - 📤 Subiendo archivo
   - 🌐 Enviando al servidor
   - 🔍 Procesando PDF
   - ✨ Enriqueciendo datos
5. **Verificar**: Los items se extraen automáticamente
6. **Verificar**: NCM detectado (ej: 71490347 o similar)
7. **Verificar**: Descripción, cantidad, valores poblados
8. Revisar la tabla de items
9. Click "Generar Excel"
10. **Verificar**: Descarga correcta del AVG

**Resultado esperado**: ✅ IA extrae datos correctamente del PDF
**Tiempo estimado**: 5-7 minutos
**Nota**: La extracción puede tardar 2-3 segundos

---

#### Caso 5: Gestión de Clientes (CRUD)
**Objetivo**: Verificar creación y gestión de clientes

**Pasos**:
1. Login con `premium` / `premium123`
2. Navegar a sección "Clientes" en sidebar
3. Click "Nuevo Cliente" o "Agregar Cliente"
4. Llenar el formulario:
   - Nombre: "Estudio Test ABC"
   - CUIT: "20123456789"
   - Email: "test@estudio.com" (opcional)
   - Teléfono: "1234567890" (opcional)
5. Click "Guardar"
6. **Verificar**: Cliente aparece en la lista
7. **Verificar**: Muestra nombre, CUIT, y acciones (editar/eliminar)
8. Click en el cliente para ver detalles
9. Editar el cliente (cambiar nombre)
10. **Verificar**: Los cambios se guardan
11. Volver al dashboard y crear una operación
12. Asignar la operación al cliente "Estudio Test ABC"
13. Volver a "Clientes" y ver el historial del cliente
14. **Verificar**: La operación aparece en el historial

**Resultado esperado**: ✅ CRUD de clientes funciona completamente
**Tiempo estimado**: 6-8 minutos

---

#### Caso 6: Sistema de Notas en Operaciones
**Objetivo**: Verificar persistencia de notas

**Pasos**:
1. Login con `premium` / `premium123`
2. Crear o abrir una operación existente
3. Buscar botón "Agregar Nota" o campo de notas
4. Escribir: "Producto requiere certificado SENASA"
5. Guardar la nota
6. **Verificar**: Nota se muestra en la interfaz
7. Refrescar la página (F5)
8. **Verificar**: La nota persiste después del refresh
9. Editar la nota
10. **Verificar**: Los cambios se guardan

**Resultado esperado**: ✅ Notas se guardan y persisten correctamente
**Tiempo estimado**: 3-5 minutos

---

### 🚨 ESCENARIOS DE ERROR (Ambos Usuarios)

#### Caso 7: Archivo Inválido
**Objetivo**: Verificar manejo graceful de errores

**Pasos**:
1. Login con cualquier usuario
2. Intentar subir un archivo `.txt` o `.jpg` (no Excel ni PDF)
3. **Verificar**: Sistema muestra error claro:
   - "Formato no soportado"
   - "Solo se aceptan .xlsx o .pdf"
4. **Verificar**: Sistema NO crashea
5. **Verificar**: Puedo seguir usando el sistema

**Resultado esperado**: ✅ Error manejado sin crash
**Tiempo estimado**: 2 minutos

---

#### Caso 8: Excel Corrupto
**Objetivo**: Verificar robustez ante archivos corruptos

**Pasos**:
1. Login con cualquier usuario
2. Crear un archivo `.xlsx` vacío o corrupto
3. Intentar subirlo al sistema
4. **Verificar**: Error claro: "No se pudo procesar el archivo"
5. **Verificar**: Sistema sigue funcionando
6. Intentar subir un Excel válido después
7. **Verificar**: Funciona correctamente

**Resultado esperado**: ✅ Sistema se recupera de errores
**Tiempo estimado**: 3 minutos

---

## 📝 PLANTILLA DE REPORTE DE BUGS

Si encontrás un problema, reportalo usando este formato:

```
TÍTULO: [Breve descripción del problema]

QUÉ INTENTÉ HACER:
- Paso 1
- Paso 2
- Paso 3

QUÉ ESPERABA QUE PASARA:
[Descripción del comportamiento esperado]

QUÉ PASÓ REALMENTE:
[Descripción del comportamiento actual]

USUARIO: basico / premium

SCREENSHOT: [Si es posible, adjuntar captura]

SEVERIDAD: CRÍTICO / ALTO / MEDIO / BAJO
```

**Ejemplos de severidad**:
- **CRÍTICO**: Sistema crashea, no puedo usar nada
- **ALTO**: Funcionalidad core no funciona (ej: no genera Excel)
- **MEDIO**: Feature secundaria no funciona (ej: notas no se guardan)
- **BAJO**: UI confusa, texto mal escrito, lentitud menor

---

## 🎯 MÉTRICAS DE ÉXITO

El testing será considerado exitoso si:

- ✅ 8/8 casos de prueba pasan (100%)
- ✅ 0 bugs CRÍTICOS encontrados
- ✅ < 3 bugs ALTOS encontrados
- ✅ Todos los testers pueden completar el flujo principal (Caso 1 y 4)
- ✅ Tiempo promedio por operación: < 5 minutos

---

## 🔧 TROUBLESHOOTING

### "No puedo acceder al sistema"
- Verificar que el servidor está corriendo en puerto 8001
- Abrir navegador en: http://127.0.0.1:8001
- Verificar credenciales correctas

### "El upload no funciona"
- Verificar tamaño del archivo (< 10MB)
- Verificar formato (.xlsx o .pdf solamente)
- Revisar consola del navegador (F12 → Console)

### "La descarga no inicia"
- Verificar que el navegador no bloqueó pop-ups
- Revisar carpeta de Descargas
- Verificar que el Excel se generó correctamente en el servidor

### "Aparece error 500"
- Reportar inmediatamente (bug CRÍTICO)
- Adjuntar screenshot del error
- Indicar qué estabas haciendo cuando ocurrió

---

## 📊 CHECKLIST FINAL PARA CADA TESTER

Antes de finalizar el testing, verificar que completaste:

**Usuario Básico**:
- [ ] Caso 1: Upload Excel y generar AVG ✅
- [ ] Caso 2: Excel con errores - Validación ✅
- [ ] Caso 3: Restricción features premium ✅
- [ ] Caso 7: Archivo inválido ✅
- [ ] Caso 8: Excel corrupto ✅

**Usuario Premium**:
- [ ] Caso 4: PDF Extraction con IA ✅
- [ ] Caso 5: Gestión de clientes ✅
- [ ] Caso 6: Sistema de notas ✅
- [ ] Caso 7: Archivo inválido ✅
- [ ] Caso 8: Excel corrupto ✅

**Feedback adicional**:
- [ ] ¿La interfaz fue clara y fácil de usar?
- [ ] ¿Hubo algo confuso o poco intuitivo?
- [ ] ¿Qué mejorarías?
- [ ] ¿Usarías este sistema en tu trabajo diario?

---

## 🚀 PRÓXIMOS PASOS

Después del testing:

1. **Recopilar feedback** de los 5 testers
2. **Priorizar bugs** encontrados (CRÍTICO > ALTO > MEDIO > BAJO)
3. **Fixear bugs críticos** antes del lanzamiento
4. **Implementar mejoras** de UX sugeridas
5. **Re-testing** de bugs corregidos
6. **Lanzamiento** a producción 🎉

---

## 💬 CONTACTO

Si tenés dudas o problemas durante el testing:

- **Email**: [AGREGAR_EMAIL_CONTACTO]
- **Slack/Teams**: [AGREGAR_CANAL]
- **Horario de soporte**: Lunes a Viernes 9-18hs

---

**¡Gracias por ayudar a mejorar CDI!** 🙏

Tu feedback es fundamental para lanzar un producto de calidad que realmente ayude a despachantes de aduana en su trabajo diario.

---

**Última actualización**: 2025-10-20
**Versión de la guía**: 1.0
**Generado por**: Claude Code Auditoría Pre-Testing
