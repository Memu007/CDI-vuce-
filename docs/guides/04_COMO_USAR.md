# 🧮 CÓMO PROBAR LA CALCULADORA DE VALOR EN PLAZA

## 📋 **Requisitos Previos**

1. **Servidor corriendo**:
   ```bash
   cd "/Users/Emi/Documents/despanchte nuevo"
   PYTHONPATH=. uvicorn proyecto_maria.server_funcional:app --reload --port 8001
   ```

2. **Verificar que funciona**:
   ```bash
   curl http://localhost:8001/health
   ```
   Deberías ver: `{"status":"healthy",...}`

---

## 🚀 **OPCIÓN 1: Test Automático (MÁS FÁCIL)**

### Ejecutar todos los tests de una vez:

```bash
bash test_calculator.sh
```

Esto va a probar automáticamente:
- ✅ Cálculo desde China
- ✅ Cálculo desde Brasil (MERCOSUR)
- ✅ Comparación de orígenes
- ✅ Ejemplos pre-configurados
- ✅ Info de MERCOSUR

---

## 🧪 **OPCIÓN 2: Probar Manualmente (Paso a Paso)**

### **Test 1: Calcular valor de Laptop desde China**

```bash
curl -X POST http://localhost:8001/api/calculator/valor-plaza \
  -H "Content-Type: application/json" \
  -d '{
    "ncm": "84713010",
    "origen": "CN",
    "fob_unitario": 500,
    "cantidad": 10
  }'
```

**Resultado esperado:**
```json
{
  "success": true,
  "calculo": {
    "fob_total": 5000.0,
    "derechos_importacion": 2152.0,  // 41% sobre CIF
    "iva": 1501.92,                  // 21%
    "tasa_estadistica": 150.0,       // 3%
    "valor_final": 8953.92,          // ← ESTE ES EL VALOR FINAL
    "valor_unitario_final": 895.39,  // Por unidad
    "tributos_totales": 3803.92,
    "breakdown": {
      "porcentaje_tributos": 76.1,   // Tributos = 76% del FOB 😱
      "incremento_vs_fob": 79.1      // Incremento total 79%
    },
    "es_mercosur": false
  }
}
```

**Interpretación:**
- Comprás 10 laptops a USD 500 c/u = USD 5,000 FOB
- Pagás USD 3,803 de tributos (¡76% del FOB!)
- Valor final: USD 8,954 (casi el doble del FOB)

---

### **Test 2: Calcular valor de Laptop desde Brasil (MERCOSUR)**

```bash
curl -X POST http://localhost:8001/api/calculator/valor-plaza \
  -H "Content-Type: application/json" \
  -d '{
    "ncm": "84713010",
    "origen": "BR",
    "fob_unitario": 500,
    "cantidad": 10
  }'
```

**Resultado esperado:**
```json
{
  "calculo": {
    "derechos_importacion": 0.0,     // ← 0% por MERCOSUR!
    "valor_final": 6751.92,          // Mucho más barato
    "es_mercosur": true,
    "ahorro_mercosur": 1837.5        // Ahorraste USD 1,837!
  }
}
```

**Comparación:**
- China: USD 8,954
- Brasil: USD 6,752
- **Ahorro: USD 2,202 (24.6%)**

---

### **Test 3: Comparar todos los orígenes automáticamente**

```bash
curl -X POST http://localhost:8001/api/calculator/comparar-origenes \
  -H "Content-Type: application/json" \
  -d '{
    "ncm": "84713010",
    "fob_unitario": 500,
    "cantidad": 10
  }'
```

**Resultado esperado:**
```json
{
  "comparacion": {
    "mejor_origen": "BR",
    "peor_origen": "CN",
    "diferencia_maxima": 2202.0,
    "origenes_comparados": [
      {
        "origen": "BR",
        "valor_final": 6751.92,
        "es_mercosur": true,
        "ahorro_vs_mas_caro": 2202.0,
        "ahorro_percent": 24.6
      },
      {
        "origen": "CN",
        "valor_final": 8953.92,
        "es_mercosur": false,
        "ahorro_vs_mas_caro": 0.0,
        "ahorro_percent": 0.0
      }
    ]
  }
}
```

---

### **Test 4: Usar ejemplos pre-configurados**

Ver todos los ejemplos disponibles:
```bash
curl http://localhost:8001/api/calculator/ejemplos
```

Probar un ejemplo específico:
```bash
curl http://localhost:8001/api/calculator/test/laptop_brasil
curl http://localhost:8001/api/calculator/test/celular_vietnam
curl http://localhost:8001/api/calculator/test/neumaticos_brasil
```

---

### **Test 5: Ver tasas de NCM disponibles**

```bash
curl http://localhost:8001/api/calculator/ncm-rates
```

**Resultado esperado:**
```json
{
  "rates": [
    {"ncm": "84713010", "tasa_porcentaje": 41.0},
    {"ncm": "85171200", "tasa_porcentaje": 41.0},
    {"ncm": "40111000", "tasa_porcentaje": 18.0},
    ...
  ]
}
```

---

### **Test 6: Info de MERCOSUR**

```bash
curl http://localhost:8001/api/calculator/mercosur-info
```

**Resultado esperado:**
```json
{
  "mercosur": {
    "paises": ["BR", "PY", "UY"],
    "descuento_derechos": "100%",
    "beneficio": "Derechos de importación reducidos a 0%"
  }
}
```

---

## 🐍 **OPCIÓN 3: Probar desde Python (sin servidor)**

Si querés probar la calculadora directamente sin levantar el servidor:

```bash
python3 -c "from proyecto_maria.core.calculator import test_calculadora; test_calculadora()"
```

Esto va a imprimir un test completo con ejemplos formateados.

---

## 🌐 **OPCIÓN 4: Probar desde el Navegador (Swagger UI)**

1. Abrí en tu navegador: http://localhost:8001/docs

2. Buscá la sección **"calculator"**

3. Probá los endpoints clickeando "Try it out":
   - `POST /api/calculator/valor-plaza`
   - `POST /api/calculator/comparar-origenes`
   - `GET /api/calculator/test/{ejemplo_key}`

---

## 📊 **Casos de Uso Reales**

### **Caso 1: Despachante necesita justificar valor ante Aduana**

Cliente importó laptops a USD 500 c/u, Aduana dice "muy barato".

```bash
curl -X POST http://localhost:8001/api/calculator/valor-plaza \
  -H "Content-Type: application/json" \
  -d '{"ncm": "84713010", "origen": "CN", "fob_unitario": 500, "cantidad": 10}'
```

**Respuesta para mostrar a Aduana:**
- FOB: USD 5,000
- Tributos: USD 3,804 (76%)
- **Valor en plaza: USD 8,954**
- "El producto no es barato, tiene 76% de impuestos encima"

---

### **Caso 2: Cliente pregunta "¿De dónde me conviene importar?"**

```bash
curl -X POST http://localhost:8001/api/calculator/comparar-origenes \
  -H "Content-Type: application/json" \
  -d '{"ncm": "84713010", "fob_unitario": 500, "cantidad": 10}'
```

**Respuesta:**
- Brasil: USD 6,752 (mejor opción)
- Vietnam: USD 8,954
- China: USD 8,954
- **Recomendación: Importar de Brasil ahorra USD 2,202**

---

### **Caso 3: Calcular impacto de cantidad**

```bash
# 10 unidades
curl -X POST http://localhost:8001/api/calculator/valor-plaza \
  -H "Content-Type: application/json" \
  -d '{"ncm": "84713010", "origen": "CN", "fob_unitario": 500, "cantidad": 10}'

# 100 unidades (10x más)
curl -X POST http://localhost:8001/api/calculator/valor-plaza \
  -H "Content-Type: application/json" \
  -d '{"ncm": "84713010", "origen": "CN", "fob_unitario": 500, "cantidad": 100}'
```

Ver cómo escalan los tributos linealmente.

---

## ❌ **Solución de Problemas**

### Error: "Connection refused"
- ✅ Asegurate que el servidor esté corriendo en puerto 8001
- ✅ Verificá con: `curl http://localhost:8001/health`

### Error: "404 Not Found"
- ✅ Verificá que el calculator router esté cargado
- ✅ Mirá los logs del servidor al iniciar, debería decir: "Calculator router loaded successfully"

### Error: "500 Internal Server Error"
- ✅ Mirá los logs del servidor para ver el error específico
- ✅ Verificá que el archivo `proyecto_maria/core/calculator.py` exista

### Los números no tienen sentido
- ✅ Verificá que estés pasando `fob_unitario` (no total)
- ✅ Verificá que `cantidad` sea > 0
- ✅ Verificá que el NCM exista en el catálogo (o usará 35% default)

---

## 📚 **Documentación de Endpoints**

### `POST /api/calculator/valor-plaza`
Calcula valor en plaza de un producto.

**Body:**
```json
{
  "ncm": "84713010",
  "origen": "CN",
  "fob_unitario": 500.0,
  "cantidad": 10,
  "flete_percent": 0.04,    // opcional
  "seguro_percent": 0.01    // opcional
}
```

### `POST /api/calculator/comparar-origenes`
Compara costos desde diferentes países.

**Body:**
```json
{
  "ncm": "84713010",
  "fob_unitario": 500.0,
  "cantidad": 10,
  "origenes": ["CN", "BR", "US"]  // opcional
}
```

### `GET /api/calculator/ejemplos`
Lista todos los ejemplos disponibles.

### `GET /api/calculator/test/{ejemplo_key}`
Ejecuta un ejemplo específico.
Ejemplos: `laptop_china`, `laptop_brasil`, `celular_vietnam`, etc.

### `GET /api/calculator/ncm-rates`
Lista todas las tasas de NCM configuradas.

### `GET /api/calculator/mercosur-info`
Info sobre preferencias MERCOSUR.

---

## 🎯 **Próximos Pasos**

1. **Probá los endpoints** con los comandos de arriba
2. **Agregá más NCM** en `calculator.py` si necesitás
3. **Integrá con frontend** cuando esté listo
4. **Conectá con API de Tarifar** para tasas reales (futuro)

---

**¿Problemas? ¿Dudas?**
Revisá los logs del servidor o preguntame!
