# E2E del flujo MARIA

Ejecutar desde la raíz del repositorio:

```bash
./scripts/testing/e2e_maria.sh
```

El comando instala Puppeteer la primera vez, levanta CDI con SQLite y datos en
un directorio temporal, crea una planilla XLSX determinística y elimina el
entorno al terminar. No usa Gemini, VUCE CI, Tarifar, MercadoPago ni internet
durante el escenario (la instalación inicial del navegador sí descarga sus
dependencias).

El escenario registra un usuario de prueba, crea y selecciona un cliente,
sube la planilla, revisa carátula e ítems, exige SIM de 11 dígitos + DC, agrupa
dos ítems, prueba un error bloqueante y una advertencia no bloqueante, exige
SBT, descarga MARIA.TXT y confirma operación y memoria NCM/origen. En la
consulta que representa la próxima factura verifica explícitamente que el peso
no se ofrece ni se autocompleta: cada peso requiere confirmación humana.

Ante un fallo conserva screenshot, traza de Chromium, HTML y detalle fuera del
repositorio; el runner informa la ruta. En GitHub Actions esos archivos se
publican como artefacto del job `e2e-maria`, que corre después de las pruebas
críticas.
