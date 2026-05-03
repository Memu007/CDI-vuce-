# Optimizador para MARIA

Un proyecto para validar, enriquecer y generar archivos Excel en formato AVG para el sistema MARIA de despachantes de aduana.

## Características

- ✅ **Validación de datos**: Verifica que todos los campos requeridos estén presentes y sean válidos
- ✅ **Generación de Excel AVG**: Crea archivos Excel con el formato exacto requerido por MARIA
- ✅ **Interfaz web intuitiva**: Formulario web simple para ingresar datos y descargar archivos
- ✅ **Subida de archivos Excel**: Procesa archivos Excel existentes y los convierte a formato AVG
- ✅ **Detección automática de columnas**: Reconoce diferentes formatos de Excel automáticamente
- ✅ **API REST**: Endpoint para integraciones automáticas
- ✅ **Cálculos automáticos**: TOTAL = cantidad × valor_unitario
- ✅ **Campos opcionales**: Soporte para marca, modelo, versión, otros, separador, ventaja

## Instalación

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Variables de entorno

### AFIP (homologación)
```bash
# Copiar a .env y completar rutas reales
AFIP_SERVICE=wscdc
AFIP_CERT_PATH=/ruta/al/certificado/afip_cert.pem
AFIP_KEY_PATH=/ruta/a/la/clave/afip_key.key
AFIP_WSAA_URL=https://wsaahomo.afip.gov.ar/ws/services/LoginCms
```
```bash
# Para producción cambiar la URL
AFIP_WSAA_URL=https://wsaa.afip.gov.ar/ws/services/LoginCms
```
```bash
python - <<'PY'
from afip_client import AFIPSettings, WSAAClient
settings = AFIPSettings.from_env()
print('Configurado?', settings.is_configured())
if settings.is_configured():
    print(WSAAClient(settings).authenticate())
PY
```

## Uso

### Interfaz Web (Recomendado)

1. Iniciar el servidor:
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

2. Abrir en el navegador: `http://127.0.0.1:8000`

3. Elegir modo de trabajo:
   - **Ingreso Manual**: Completar el formulario con datos individuales
   - **Subir Archivo Excel**: Cargar un archivo Excel existente

### Modo Manual
4. Completar el formulario:
   - **Código de Operación**: Identificador único (ej: `25DI00241`)
   - **Items**: Agregar uno o más items con sus datos

5. Hacer clic en "Generar Excel AVG"

6. Descargar el archivo generado

### Modo Subida de Archivo
4. Seleccionar archivo Excel (.xlsx o .xls)

5. El sistema detectará automáticamente las columnas con datos de piezas

6. Hacer clic en "Procesar Excel"

7. Descargar el archivo convertido a formato AVG

#### Formatos de Excel Soportados
El sistema reconoce automáticamente diferentes formatos de columnas:
- `pieza`, `Pieza`, `pieza`, `ncm`, `NCM`, `codigo`, `Código`
- `descripcion`, `Descripcion`, `descripción`, `Descripción`, `desc`, `Desc`
- `origen`, `Origen`, `pais`, `País`, `country`, `Country`
- `peso_unitario`, `Peso Unitario`, `peso`, `Peso`, `weight`, `Weight`
- `cantidad`, `Cantidad`, `qty`, `Qty`, `quantity`, `Quantity`
- `valor_unitario`, `Valor Unitario`, `valor`, `Valor`, `price`, `Price`, `unit_price`

### API REST

La API está disponible en `http://127.0.0.1:8000/docs` con documentación automática.

#### Endpoint principal:

```http
POST /process_operation/
Content-Type: application/json

{
  "operation_id": "25DI00241",
  "items": [
    {
      "pieza": "84713010",
      "descripcion": "Computadora portátil",
      "origen": "CN",
      "peso_unitario": 2.5,
      "cantidad": 10,
      "valor_unitario": 1500.00,
      "marca": "Apple",
      "modelo": "MacBook Pro",
      "version": "14.2"
    }
  ]
}
```

#### Respuesta exitosa:
```json
{
  "message": "Operación procesada y Excel generado exitosamente.",
  "filename": "AVG_25DI00241_20241201_143022.xlsx",
  "validated_items_count": 1
}
```

## Formato Excel AVG

El archivo generado incluye exactamente estas columnas en orden:

1. **Pieza** (NCM)
2. **Descripcion**
3. **Origen** (código de país)
4. **Peso Unitario** (kg)
5. **Cantidad**
6. **Valor Unitario** (USD)
7. **Marca** (opcional)
8. **Modelo** (opcional)
9. **Version** (opcional)
10. **otros** (opcional)
11. **separador** (opcional)
12. **ventaja** (opcional)
13. **TOTAL** (calculado automáticamente)

## Validaciones

- **Pieza**: Obligatoria, no puede estar vacía
- **Descripción**: Obligatoria
- **Origen**: Obligatorio (código de 2 letras)
- **Peso Unitario**: > 0
- **Cantidad**: > 0
- **Valor Unitario**: > 0

## Desarrollo

### Estructura del proyecto
```
proyecto_maria/
├── static/                 # Archivos web
│   ├── index.html         # Interfaz principal
│   ├── style.css          # Estilos
│   └── script.js          # JavaScript
├── core/                  # Lógica de negocio
│   ├── validations.py     # Validaciones
│   ├── excel_generator.py # Generador de Excel
│   └── vuce_connector.py  # API VUCE (futuro)
├── models/                # Modelos de datos
│   └── operations.py      # Pydantic models
├── tests/                 # Tests
├── main.py               # FastAPI app
├── requirements.txt      # Dependencias
└── README.md            # Esta documentación
```

### Tests

Ejecutar todos los tests:
```bash
pytest
```

Con cobertura:
```bash
pytest --cov=.
```

## Próximas mejoras (Fase 2)

- 🔄 **Enriquecimiento con API VUCE**: Obtener datos adicionales de códigos NCM
- 💾 **Base de datos**: Persistencia de operaciones
- 🐳 **Docker**: Containerización
- 📊 **Dashboard**: Estadísticas y reportes

## Licencia

Este proyecto es para uso interno de despachantes de aduana.
