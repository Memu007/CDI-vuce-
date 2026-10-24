# Cierre de retoma — 2026-10-24

## Publicación autorizada completada

Main648cd2f (producto166395f) está activo en Railway. Despliegue
4bb8b534-04e2-4d94-bfd8-7e101defbe94, solicitado una vez con sesión autorizada
en Brave el23Oct17:11ARG. La creación de contenedores demoró unos11min;
startup completo17:22:50ARG. Verificado24Oct10:00ARG: UIActive, enlace al
commit648, salud200 API/baseok y upload.js idéntico al local de main648.
SHA256 b20509580b9bf92271604caac0d77b86211fe0626b62a334d1b37f78592dd38d.
Captura local outputs/CDI-publicado-2026-10-24.png. No hubo nuevos cambios
de main, variables, permisos, credenciales ni acceso directo a DB.

Se abrió CDI para Emi y quedó el formulario de ingreso listo; no se solicitó
ni introdujo contraseña. No se subieron documentos privados ni se llamó a
Gemini/MP/VUCE/ARCA reales como prueba. Publicación completada no significa
MVP cerrado: sigue pendiente la prueba real en Kit y el cierre de Fase1.

## EXCEL-2: veredicto PM

**Aceptada en el alcance de lectura y validación sobre HEADdddcf6d**, producto
be17e1b. PR#5 está lista para revisión, fuera de borrador, sin fusionar ni publicar. Los seis criterios de devolución
están cubiertos por revisión de fuente, focales, ejemplos independientes y
puertas finales; no se exige que un marcador de sabotaje obsoleto se cuente
como resultado. Quedan explícitas cuatro limitaciones del corpus histórico.
No se afirma cobertura universal de memoria, formatos o archivos reales.

- Suite local completa, venv limpio requirements Python3.12.8, preflightOK:
  1731passed,102skipped,2xfailed,23warnings,250.01s,exit0, sin deselecciones.
- CI40017165638, HEADdddcf6d: tests120632090501 success (1721passed,
  102skipped,10deselected históricas,2xfailed); e2e-maria120633984525 success,
  «E2E MARIA OK». Sin cambios de configuración para ocultar fallos.
- Corrección origen XML: ambas comillas conservan CN/CN. 2000 combinadas
  0.132s. Ocho XML10282491bytes (<10MiB) entran antes de normal:200 en23.29s.
  Nueve ejemplos sintéticos propios devuelven JSON idéntico a648; no son el
  corpus histórico no recuperado ni validación de facturas reales.
- Falla inicial de cuatro mensajes subítems corregida enbe17e1b:51focales
  verdes y negativo restaura los cuatro fallos. Doc1/pesos/Form/dueño intactos.
- QA independiente12checks y3mutaciones nuevas; Dev2negativos nuevos más
  negativo de subítems; no se suman a las42históricas.
- Históricas: baseline37casos verdes;38mutaciones con fallo por causa correcta,
  cero sobrevivientes entre las terminadas,2timeout30s (#21,#27) no evaluadas,
  2recetas sin coincidencia (#9,#26) obsoletas. No es42/42. PM leyó causas
  de origen, codificación y duplicación de cantidad/precio. Informe y detalle
  en outputs/EXCEL2-mutaciones-2026-10-23.md, reviewed-results.json en
  /private/tmp/cdi-excel2-mutations-4_a14kvy. No repetir sólo para obtener100%.
- Medición adicional para cerrar el borde de estilos:499990etiquetas añadidas
  más las originales superaron el tope y se rechazaron400 antes de abrir;
  no cuenta como libro admitido.499900xf añadidos sí entran:200 en9.182s,
  RSS familiar460140544bytes, sin corte900MB/90s. Registro en
  /private/tmp/cdi-excel2-maxstyles-20261023/measurements/dddcf6d-styles_xf.*.
  Es una muestra cerca del tope, no prueba universal de memoria.

La suite instrumentada066 fue roja (5fallos,52.67%cobertura); el caso de
tiempo también falla aislado con cobertura31.5s y pasa sin ella. Decisión
operativa registrada enDECISIONS: medir tiempo sin instrumentación comoCI,
sin excluir casos ni elevar timeout. La suite completa final confirmó verde.
El primer intento final se interrumpió al7% durante la pausa; no se acredita.

## Qué sigue

1. Para fusionar/publicar PR#5, autorización de Emi para dddcf6d. El permiso
   anterior ya se consumó en main648 y no cubre producto nuevo (AGENTS§1).
2. GUARDAR-2 separado, candidato2d930c5/base1cdfe49: preferencia SIMproveedor
   cuando coincide NCM8 y descripción normalizada. Mantener D32(b), sin
   migración. Faltan negativos explícitos por dueño en ambos endpoints,
   Postgres descartable y puertas de integración sobre base aceptada.
   Lectura Dev:5archivos; producto sólo main.py. Binarios Postgres ausentes,
   DockerCLI disponible pero daemon sin conexión; no se instaló/inició nada.
3. Factura real revisada por Emi/despachante y prueba de TXT en Kit para cerrar
   Fase1. EC02 continúa bloqueado, no se implementó exportación completa.

## Observación operativa fuera de esta pieza

El log del despliegue muestra error al registrar métricas de /robots.txt:
falta la columna api_logs.owner_username. El modelo y middleware no cambian
entre a9b03cf y648; no se atribuye al fix nuevo. Salud pública da200, pero
eso no acredita persistencia de métricas. Registrar para clasificar en la
cola de observabilidad/esquema; sin migraciones a ciegas ni DBproducción.
No se copian parámetros, clientes, identificadores ni secretos del log.
