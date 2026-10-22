# EXCEL-2 — revisión independiente, 2026-10-22

## 1. Resultado

Devolver a Dev; no integrar `c2f8063` todavía. El control de ancho se evade usando comillas simples, que son XML válido. Una sola celda XFD1 pasa el validador y openpyxl abre una fila de 16.384 columnas, frente al límite previsto de 256. La reproducción usa una celda, sin generar carga masiva ni probar memoria extrema.

## 2. Commit y alcance

Revisado `c2f8063`, base `1cdfe49`: 31 commits, 10 archivos, 1.712 inserciones y 65 eliminaciones. Clone aislado: `/private/tmp/cdi-excel2-review-20261021`. Contiene lectura XLSX/CSV, combinadas/encabezados/mapeos, topes previos a openpyxl, montos fuera de rango y CUIT del despachante/vendedor; pruebas, sabotajes y changelog. No se integró GUARDAR-2 ni la punta general de Dev1. No se editó producto ni se hizo push/deploy.

El `docs/pm/PARA-PM.md` leído desde esa rama está obsoleto: entrega PUNTA-A-PUNTA-1 y MARIA-1b, y dice que EXCEL-2 todavía no tiene alcance. No es un informe de aceptación de este SHA.

## 3. Evidencia reproducida

Entorno `/private/tmp/cdi-clean-requirements-20261020`, Python3.12.8, `include-system-site-packages=false`; falsos conectores, `test-key`, endpoints loopback y SQLite temporal del conftest. Sin documentos reales, terceros ni producción.

`python -m pytest -q --no-cov tests/test_excel2.py tests/test_excel1_rendimiento.py`: **93 passed, 3 warnings, 32.79s, exit0**. Warnings de obsolescencia y SECRET_KEY local; no secretos reales.

Los seis criterios de devolución tienen pruebas verdes en ese conjunto:

1. Combinadas gigantes repetidas: prueba verde; el test permite hasta5s frente al criterio original menor a1s. No medirlo como evidencia de ese umbral original.
2. Combinadas cantidad/precio/peso: verde, incluidos textos y mapeo del cliente.
3. Estilos: rechaza millones de xf/font/dxf antes de abrir. No se midió pico RSS independiente; pasar estos ejemplos no demuestra el límite universal de1GB.
4. Hojas con relación rara y primera hoja27MB: verde; prueba de ocho subidas al borde también verde. El nuevo escape del ancho deja incumplida la protección de recursos de forma general.
5. CSV cp1252 con pares que parecen UTF8 y aviso de mezcla: verde. Hallazgo menor adicional abajo.
6. Fila realmente vacía dentro de combinada: verde.

Sabotajes: se inició el script completo y se interrumpió voluntariamente para no repetir estrés por cada mutación. Después se ejecutó una copia temporal que preservaba mutaciones/patrones y corría sólo el test correspondiente por mutación. Se observaron cuatro negativos rojos correctos: OverflowError con entero enorme; lista sin control de monto; generación que ignora monto inválido; exportación sin control previo. La sesión restante no pudo recuperarse después de la retoma: **no se declara que todos los sabotajes pasaron**.

## 4. No corrido

Suite completa y e2e sobre c2f8063; navegador del flujo CSV; medición RSS; comparación independiente de los nueve libros normales contra la base; Kit/despachante o lectura realGemini. El focal incluye libros sintéticos normales, pero no reemplaza esas puertas. No se ejecutaron scripts de navegador desde shell.

## 5. Hallazgos y reproducción

**Bloqueante:** `proyecto_maria/security/file_security.py`, `_ultima_columna`, línea314 (regex dentro de la función). Sólo reconoce referencias con comillas dobles. XML `r='XFD1'` evade el tope. Repro independiente en `/private/tmp/excel2_comillas_repro.py`.

```sh
rtk proxy env PYTHONPATH=/private/tmp/cdi-excel2-review-20261021 /private/tmp/cdi-clean-requirements-20261020/bin/python /private/tmp/excel2_comillas_repro.py
```

Salida esperada actual: dobles `admitted=False`; simples `admitted=True`; openpyxl `columns=16384 last=synthetic`; AssertionError final con mensaje DEFECTO. El script importa sólo el módulo de validación y openpyxl; no necesita credenciales, DB o servidor. Genera todo en memoria y abre una fila de una celda.

**Menor:** `_leer_tabla`, `main.py:3756`, clasifica secuencias UTF8 con regex que permite sobrelongitudes/surrogados y luego hace `seq.decode('utf-8')` sin protección. Bytes sintéticos `b'descripcion;ncm\nDemo\xe0\x80\x80;0901.21.00\n'` reproducen UnicodeDecodeError. La ruta captura el error y devuelve400, no500; el riesgo es rechazar CSV Windows1252 que podría leerse, sin el aviso legible de codificación. Anotar sin ampliar esta corrección automáticamente.

## 6. Decisión solicitada a PM

D1: devolver escape XML de comillas a Dev en EXCEL-2 y mantener fuera de la publicación actual. Recomendado. Dev debe cubrir variantes XML válidas y demostrar rojo/verde con la reproducción pequeña; no necesita libro peligroso.

D2: al reentregar, reemplazar PARA-PM con SHA/base y puertas realmente ejecutadas, medir o declarar pendientes las condiciones de memoria/tiempo, ejecutar suite y e2e de ese SHA. El hallazgo CSV menor queda anotado para decisión de alcance.

Contexto: ~35%; estimado, no lectura de get_session. Herramienta de medición de sesiones históricas no disponible en este agente.
