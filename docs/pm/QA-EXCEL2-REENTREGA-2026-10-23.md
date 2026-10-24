# EXCEL-2 — reentrega y revisión PM, 2026-10-23

Estado: dos bloqueantes anteriores corregidos y reproducidos verdes;
**aceptación completa pendiente de suite/CI/e2e**. No publicar esta pieza
con el permiso del producto anterior. Base main `648cd2f`, integración
rechazada `d448033`, producto nuevo `3906130`, pruebas `b073ba4` y `0666881`.

## Qué cambió y qué se conservó

El lector de la primera hoja usa Expat de stdlib para atributos XML válidos:
comillas simples/dobles, espacios, entidades y namespace principal. Esa
misma pasada anticipa el límite existente sólo cuando más de MAX+31 filas
contienen números efectivos. No baja D27=10 MiB, no usa nrows ni trunca.
Las filas ambiguas siguen al límite final previo. No demuestra que todo
libro admitido consuma poco: la guarda numérica es conservadora.

Dev corrigió también el test de ocho libros: comprueba el tamaño XML real
del miembro ZIP y espera ocho entradas al validador, sin sleep ni estimación
que rechace los archivos por estar fuera del tope.

QA comparó contratos contra648: DOC-1, pesos, formulario omitido=True y dueño
se conservan; sin GUARDAR-2, cobro, credenciales ni documentos privados.

## Comprobaciones PM sobre producto exacto

Clone limpio propio `/private/tmp/cdi-excel2-pm-final-20261023`, primero
`b073ba468bd8fbbcacfbd8076dfbfa2318636001`. `0666881` cambia sólo el test
antes descrito; producto idéntico confirmado por diff.

| Caso | Resultado PM | Pico RSS familia |
|---|---|---|
| Ocho primeras hojas XML10282491 bytes y normal después de ocho entradas | normal200 en23.292s; ocho400 por límite de filas |254394368bytes|
| Origen combinado con ambas comillas |200 CN/CN en ambos|152670208bytes|
|2000 combinadas gigantes|200 en0.132s, CN/CN|153174016bytes|
|Nueve facturas sintéticas propias|nueve200, JSON idénticos a base648|152961024bytes|

Mediciones en `/private/tmp/cdi-excel2-independent/measurements/b073ba4-*`,
wrapper y worker del informe anterior. Corte900MB/90s; sin cortes activados.
Log b073 se reutilizó para la repetición PM: los valores anteriores informados
por Dev (normal25.138s/RSS243855360) no son otra medición PM. No afirmar
fluidez: la normal aún tarda23s bajo estrés y conserva margen limitado frente
al timeout30s. RSS incluye proceso/hijos, imports y fixtures; no prueba
un límite universal1GB. Los nueve libros propios no son el corpus histórico
cuya lista no se recuperó. Tres comprobaciones pequeñas finales se lanzaron
cerca entre sí; el estrés de ocho ya había terminado.

## Revisión independiente y discriminantes

QA (`excel2_next_review`, modelo/esfuerzo heredados; no Fable) en clone propio
b073:12checks verdes0.96s, seis propios+seis Dev. Cubren5002filas físicas
vacías entre productos,30notas numéricas antes del encabezado, fórmulas sin
cache/NaN, cero/False y prefijo del namespace principal. Tres mutaciones en
memoria dieron rojo correcto: quitar guarda1fallo, quitar filtro namespace1,
omitir merge3fallos. Sin producto editado ni repetir estrés8.
Informe `outputs/EXCEL-2-revision-fix-2026-10-23.md` del workspace.

Dev informó362focales verdes39.93s sobreb073. El test8 durable0666881 dio
1passed23.21s, normal20022.6s, mismoXML10282491bytes. No son resultados PM.
Negativos42/43históricos siguen pendientes/no recuperados; no inventarlos.

## Puertas en curso

Suite completa iniciada sobre0666881, venv limpio requirements Python3.12.8,
sin system-site-packages. Preflight/APIloopback19006/SQLite temporal/externales
fake y test-key; logs `/private/tmp/cdi-excel2-clean-suite-20261023`.
No se accede a DB/servicios de producción ni se ejecuta Gemini real.
Registrar resultado real al terminar y luego CI/e2e del SHA final.


Entrega final guardada en GitHub: `0389f0c6fc925eeef8fc9093721121261d01e8f5`,
[PR #5 en borrador](https://github.com/Memu007/CDI-vuce-/pull/5).
Diff0666881..0389f0c sólo CHANGELOG y PARA-PM; no producto/pruebas nuevas.
[CI run39943030809](https://github.com/Memu007/CDI-vuce-/actions/runs/39943030809)
iniciada sobre esa entrega. La rama se empujó sin tocar main y el PR se
adjuntó a este chat. No fusionar por el permiso previo de main648.


## Devolución adicional encontrada por puertas completas

CI run39943030809 falló: 4 failed,1717passed,102skipped,10deselected,2xfailed.
Los cuatro tests de subítems no-lista en tests/test_subitems1.py esperaban
mensaje específico («Item1», «sub-ítems») y recibieron «no tiene la forma de
un producto». Dev localizó la guarda nueva combinada en main.py; corregir
la distinción de estructura, sin debilitar tests ni ampliar alcance.
E2E skipped por fallo de tests; no hay recorrido verde de esta entrega.

La suite local con cobertura muestra además un fallo en test_excel2 pendiente
de traceback final. CI pasó ese archivo, incluido el test8 corregido. La
hipótesis de coste de cobertura sigue sin confirmar; no subir timeout del
producto ni ocultar fallo con repeticiones. Se detuvo la ejecución de los
negativos históricos hasta tener baseline verde. Plan externo preparado en
/private/tmp/cdi-excel2-independent/plan-42-mutaciones.md:41patronesvigentes,
#9obsoleto; cero resultados ejecutados/acreditados.


## Reentrega final y nueva puerta, 17:13 ARG

Producto be17e1b separa el mensaje de producto inválido del mensaje de
subítems no-lista; PM revisó el diff mínimo en main.py. Dev51focalesverdes,
negativo temporal restaura texto genérico y reproduce4falloscorrectos.
HEADdddcf6d sólo añade informe/changelog. Subido a PR#5 tras superar la cuota
de auto-review; no se eludió el rechazo anterior ni cambió main. NuevaCI
run40017165638 en curso, suite local completa--no-cov reanudada con preflight
nuevo. El intento previo final terminó interrumpido al7%; no hay salida ni
resultado acreditado. Se comprobó ausencia de procesos propios antes de
reiniciar; logs originales conservados.

El caso de tiempo instrumentado aislado dio40031.5s, exit1,53.05stotal.
También reporta17.15% por correr un solo caso: ese umbral parcial no es el
motivo de clasificar la regresión; se leyó la aserción status400. La corrida
completa instrumentada previa sí superó38% con52.67%, pero fue roja. PM
registra puerta sin instrumentar comoCI enDECISIONS, sin tocarpytest.ini,
sin omitir pruebas ni subir timeout. La suite final verificará misma secuencia.


## Puerta local final: VERDE

Sobre dddcf6d0f51024b50ae569218b3b6dbbf1e53b97, preflight completoOK y
suite--no-cov sin deselecciones: **1731passed,102skipped,2xfailed,23warnings,
250.01s,exit0**. API propia cerrada al terminar. Log en
/private/tmp/cdi-excel2-clean-suite-final-retry-20261023/suite.log.
Pasa el caso8 dentro de la secuencia completa sin instrumentación y los4
mensajes subítems. No se cambió ni excluyó ningún test, ni timeout delproducto.
Esto confirma diferencia de coste de instrumentación frente al rojo anterior;
conservar el margen limitado observado, no prometerfluidez universal.
CI run40017165638: tests success; e2e-maria todavía en curso al registrar.
PM habilitó QAexterno groupall con corte global300s, no contar resultados
hasta entrega/revisión de motivos. #9obsoleta no se declara ejecutada.


## CI/e2e final: VERDE

Run40017165638 sobre HEADdddcf6d: jobtests120632090501 success,
**1721passed,102skipped,10deselected,2xfailed** (las10deselecciones son las
históricas de CI, no se añadió ninguna). Jobe2e-maria120633984525 success;
log20:16:54UTC: «E2E MARIA OK». Recorrido de carga, revisión y salida
simulado enCI, no contra facturas reales/Kit/serviciospagos.
Local1731 incluye las10queCIomite y pasó sin deselecciones. No repetir
suite sobre mismo producto ya verde, salvo nuevo cambio/fallo justificado.

Siguiente GUARDAR-2, sólo preparación porDev: candidato2d930c5 sobre1cdfe49,
5archivos, producto sólo main.py (2helpers/2callers). Coincide NCM8 y
referencia de descripción normalizada para preferir SIMproveedor; filtros
owner+client_id/owner+vendor_id conservados. Faltan negativos explícitos
entre dueños, Postgres descartable y puertas de integración exacta. No se
escribió código ni corrieron pruebas de esa pieza en esta preparación.
BinariosPostgres ausentes y daemonDocker no conecta; no se arrancó ni instaló.
No reabrirD32(b), no migraciones ni cobro. Mantener pieza separada dePR5.


## Veredicto final PM, 2026-10-24

Aceptada en su alcance funcional sobredddcf6d/productobe17e1b, sin publicar.
Suite/CI/e2e verdes;38mutaciones históricas detectadas,2timeout no evaluadas,
2recetas obsoletas. Los pendientes son límites explícitos de la evidencia;
no se acreditan42/42. Cierre y razonamiento enCIERRE-RETOMA-2026-10-24.md.
Borde admitido de estilos499900xf:200/9.182s/RSS460140544bytes. Sin cortes;
no garantía universal. No repetir suite salvo cambio nuevo o fallo justificado.
