# 📘 Guía de Testing para Usuarios - CDI

**Sistema**: CDI (Carga y Despacho Inteligente) v2.0
**URL**: http://127.0.0.1:8001
**Fecha de testing**: Semana del 2025-10-17
**Participantes**: 6 testers (2 estudios de despachantes, 3 personas c/u)

---

## 🔑 CREDENCIALES

### Plan Básico (3 usuarios)
- **Usuario**: `basico`
- **Password**: `basico123`
- **Funcionalidades**: Manual, Excel upload, Validación, Excel AVG download
- **Limitaciones**: ❌ Sin PDF, ❌ Sin clientes, ❌ Sin historial

### Plan Premium (3 usuarios)
- **Usuario**: `premium`
- **Password**: `premium123`
- **Funcionalidades**: Todo lo de básico + PDF upload, Gestión clientes, Historial, Notas
- **Sin limitaciones**: ✅ Full access

---

## ✅ CHECKLIST DE TESTING

### 📋 Para Usuarios BÁSICO (3 personas)

#### Test 1: Login y Primera Impresión
- [ ] Abrir http://127.0.0.1:8001
- [ ] Click en "Probar el dashboard"
- [ ] Ingresar: usuario `basico`, password `basico123`
- [ ] Click "Iniciar Sesión"
- [ ] **Verificar**: Dashboard carga sin errores
- [ ] **Tiempo esperado**: < 2 segundos

**¿Qué observar?**
- ¿El login fue intuitivo?
- ¿La interfaz se ve profesional?
- ¿Hay algún mensaje de error confuso?

#### Test 2: Subir Excel Simple
- [ ] Click en "Subir Excel" en sidebar
- [ ] Seleccionar archivo: `test_excel_web.xlsx` (provisto)
- [ ] **Verificar**: Archivo se sube sin errores
- [ ] **Verificar**: Tabla muestra items detectados
- [ ] **Tiempo esperado**: < 3 segundos desde upload hasta tabla

**¿Qué observar?**
- ¿El proceso fue claro?
- ¿Los items se muestran correctamente?
- ¿Hubo algún mensaje de error?

#### Test 3: Subir Excel Desordenado (Realista)
- [ ] Click en "Subir Excel"
- [ ] Seleccionar: `FACTURA_DESORDENADA_MEZCLADA_v2.xlsx` (provisto)
- [ ] **Verificar**: Sistema detecta columnas automáticamente
- [ ] **Verificar**: Filtra items inválidos (debe mostrar 5 de 8)
- [ ] **Verificar**: Muestra mensaje de cuántos items válidos/inválidos

**¿Qué observar?**
- ¿El sistema explicó por qué algunos items fueron descartados?
- ¿La detección automática de columnas funcionó?
- ¿Te sentiste confiado con el resultado?

#### Test 4: Generar y Descargar Excel AVG
- [ ] Con items en pantalla, click "Generar Excel AVG"
- [ ] **Verificar**: Descarga inicia automáticamente
- [ ] Abrir el archivo descargado
- [ ] **Verificar**: Tiene 13 columnas exactas
- [ ] **Verificar**: Datos coinciden con lo ingresado
- [ ] **Tiempo esperado**: Descarga inicia < 2 segundos

**¿Qué observar?**
- ¿Fue obvio cómo generar el Excel?
- ¿El archivo descargado es el esperado?
- ¿Confías en usar este archivo para MARIA?

#### Test 5: Verificar Limitaciones del Plan Básico
- [ ] **Verificar**: NO hay opción "Subir PDF" en sidebar
- [ ] **Verificar**: NO hay opción "Gestión Clientes"
- [ ] **Verificar**: NO hay opción "Historial"

**¿Qué observar?**
- ¿Está claro que son funciones premium?
- ¿Hay algún mensaje explicando las limitaciones?

---

### 💎 Para Usuarios PREMIUM (3 personas)

#### Test 1-4: Repetir Tests de Plan Básico
Ejecutar todos los tests 1-4 del plan básico primero.

#### Test 5: Subir y Extraer PDF
- [ ] Click en "Subir PDF" (solo visible en premium)
- [ ] Seleccionar: `test_invoice.pdf` (provisto)
- [ ] **Verificar**: Sistema muestra "Procesando con IA..."
- [ ] **Verificar**: Aparecen items extraídos automáticamente
- [ ] **Verificar**: NCM detectado correctamente (ejemplo: `71490347`)
- [ ] **Tiempo esperado**: Feedback inicial < 3 seg (procesamiento puede ser async)

**¿Qué observar?**
- ¿Fue claro que el sistema estaba procesando?
- ¿Los datos extraídos son correctos?
- ¿Hubo tiempo de espera frustrante?

#### Test 6: Gestión de Clientes
- [ ] Click en "Clientes" en sidebar
- [ ] Click "Nuevo Cliente"
- [ ] Ingresar:
  - Nombre: "Estudio Test ABC"
  - CUIT: "20-12345678-9"
  - Email: "test@abc.com" (opcional)
- [ ] Click "Guardar"
- [ ] **Verificar**: Cliente aparece en lista
- [ ] **Verificar**: Mensaje "Cliente creado exitosamente"

**¿Qué observar?**
- ¿El formulario fue intuitivo?
- ¿Los campos requeridos estaban claros?
- ¿El flujo fue natural?

#### Test 7: Asignar Operación a Cliente
- [ ] Subir Excel (test 2 o 3)
- [ ] Antes de generar AVG, seleccionar cliente creado
- [ ] Generar Excel AVG
- [ ] **Verificar**: Operación queda registrada
- [ ] Ir a "Historial"
- [ ] **Verificar**: Operación aparece en historial del cliente

**¿Qué observar?**
- ¿Fue obvio cómo asignar a un cliente?
- ¿El historial es útil?
- ¿Qué información te gustaría ver que no está?

#### Test 8: Sistema de Notas
- [ ] En una operación del historial, click "Agregar Nota"
- [ ] Escribir: "Factura verificada, todo OK"
- [ ] Guardar nota
- [ ] **Verificar**: Nota aparece asociada a la operación
- [ ] Cerrar y reabrir operación
- [ ] **Verificar**: Nota persiste

**¿Qué observar?**
- ¿Las notas son fáciles de agregar/leer?
- ¿Te ayudarían en tu trabajo diario?
- ¿Qué más necesitarías en las notas?

---

## 🐛 CÓMO REPORTAR BUGS

Si encuentras algo que no funciona bien, por favor reportá:

### Información Requerida
1. **¿Qué estabas intentando hacer?**
   - Ejemplo: "Subir un Excel con 20 items"

2. **¿Qué esperabas que pasara?**
   - Ejemplo: "Que se procesen todos los items"

3. **¿Qué pasó realmente?**
   - Ejemplo: "Solo se procesaron 10, los otros desaparecieron"

4. **Screenshot (si es posible)**
   - Presionar `Cmd+Shift+4` (Mac) o `Win+Shift+S` (Windows)
   - Capturar pantalla del error

5. **Plan usado**
   - Básico o Premium

6. **Hora aproximada**
   - Para revisar logs del servidor

### Severidad de Issues

**🔴 CRÍTICO** (reportar inmediatamente)
- Sistema crashea/no responde
- Datos se pierden
- Excel generado no sirve para MARIA
- Credenciales expuestas

**🟠 ALTO** (reportar al final del día)
- Función no funciona pero hay workaround
- Mensajes de error confusos
- Operación toma > 10 segundos

**🟡 MEDIO** (reportar al final de testing)
- UX confusa pero funcional
- Texto mal redactado
- Diseño raro pero no bloquea

**🟢 BAJO** (feedback general)
- Sugerencias de mejora
- "Sería bueno si..."
- Preferencias personales

---

## ⏱️ ESCENARIOS DE TESTING REALISTAS

### Escenario 1: Despachante Básico - Primera Operación del Día
**Tiempo estimado**: 10 minutos

1. Login con plan básico
2. Recibir Excel de cliente por email
3. Subir Excel al sistema
4. Revisar que items sean correctos
5. Generar Excel AVG
6. Enviar a MARIA

**Objetivo**: Verificar flujo completo más común

### Escenario 2: Despachante Premium - Cliente Recurrente
**Tiempo estimado**: 15 minutos

1. Login con plan premium
2. Recibir PDF de factura internacional
3. Subir PDF al sistema
4. Verificar extracción automática de datos
5. Seleccionar cliente recurrente de la lista
6. Agregar nota: "Factura Q4 2024"
7. Generar Excel AVG
8. Revisar historial del cliente

**Objetivo**: Verificar flujo premium completo

### Escenario 3: Múltiples Operaciones en Paralelo
**Tiempo estimado**: 20 minutos

1. Procesar 3 Excel diferentes uno tras otro
2. Generar 3 AVG files
3. Verificar que no se mezclen datos
4. Verificar que cada descarga sea correcta

**Objetivo**: Testing de concurrencia básica

### Escenario 4: Manejo de Errores
**Tiempo estimado**: 10 minutos

1. Intentar subir archivo .txt (no es Excel)
2. Intentar subir Excel corrupto
3. Intentar subir archivo > 10MB
4. Verificar mensajes de error son claros

**Objetivo**: Verificar error handling

---

## 📊 FEEDBACK QUE NOS INTERESA

### Sobre Usabilidad
- ¿Fue intuitivo el sistema sin tutorial?
- ¿Qué fue confuso o frustrante?
- ¿Qué te gustaría que fuera más rápido?
- ¿El diseño se ve profesional?

### Sobre Funcionalidad
- ¿El sistema resuelve un problema real tuyo?
- ¿Usarías esto en tu trabajo diario?
- ¿Qué funcionalidad crítica falta?
- ¿Qué funcionalidad es innecesaria?

### Sobre Confianza
- ¿Confías en los archivos generados?
- ¿Te sentís seguro usando el sistema?
- ¿Hay algo que te genera duda?

### Sobre Performance
- ¿Alguna operación se sintió lenta?
- ¿Hubo momentos de frustración esperando?
- ¿El sistema se sintió "trabado" en algún momento?

---

## 🎯 OBJETIVOS DE ESTE TESTING

**NO estamos buscando**:
- Que digas que todo está perfecto
- Feedback solo positivo
- Que uses el sistema "como es"

**SÍ estamos buscando**:
- Honestidad brutal sobre qué no funciona
- Ideas de cómo mejorar
- Bugs y errores que encontrés
- Feedback de si realmente lo usarías

**Tu opinión honesta es MÁS valiosa que decir que todo está bien** ✅

---

## 📁 ARCHIVOS DE PRUEBA PROVISTOS

### Para Plan Básico
- `test_excel_web.xlsx` - Excel simple, 10 items limpios
- `FACTURA_DESORDENADA_MEZCLADA_v2.xlsx` - Excel realista, columnas mal nombradas, 8 items (5 válidos)

### Para Plan Premium
- Todo lo de básico +
- `test_invoice.pdf` - Factura internacional en inglés
- `factura_china.pdf` - Factura en formato chino
- Otros PDFs en carpeta `samples/` para testing avanzado

---

## 🆘 SOPORTE DURANTE TESTING

### Si algo no funciona:
1. **Recargar página**: `Cmd+R` / `Ctrl+R`
2. **Limpiar caché**: `Cmd+Shift+R` / `Ctrl+Shift+R`
3. **Verificar servidor activo**: URL debe responder
4. **Consultar con equipo técnico**: Si persiste el problema

### Logs útiles para debugging:
- Abrir Chrome DevTools: `F12`
- Tab "Console": Ver errores JavaScript
- Tab "Network": Ver requests fallidas

---

## 📅 CRONOGRAMA SUGERIDO

### Día 1 (2 horas por persona)
- Setup y familiarización
- Tests básicos 1-4
- Feedback inicial

### Día 2 (1.5 horas por persona)
- Tests avanzados (5-8 para premium)
- Escenarios realistas
- Reporte de bugs encontrados

### Día 3 (1 hora por persona)
- Re-testing de issues reportados
- Feedback final
- Sugerencias de mejora

**Total por persona**: ~4.5 horas
**Total para 6 personas**: ~27 horas de testing

---

## ✅ AL FINALIZAR TESTING

Por favor completá:

### Cuestionario Final
1. **De 1-10, ¿qué tan probable es que uses este sistema?**
2. **¿Qué es lo MEJOR del sistema?**
3. **¿Qué es lo PEOR del sistema?**
4. **Si pudieras cambiar UNA cosa, ¿cuál sería?**
5. **¿Pagarías por la versión premium? ¿Por qué?**

---

**¡Gracias por tu tiempo y feedback!** 🙏

Tu input es crucial para hacer de CDI una herramienta realmente útil para despachantes.

---

*Guía generada: 2025-10-17 | Contacto: equipo técnico CDI*
