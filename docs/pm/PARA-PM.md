# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Rojo de `test_excel2` (ocho libros): diagnóstico en el commit de este informe

| Qué | SHA |
|---|---|
| Pruebas: `tests/medir_excel2.py`, herramienta de medición (la suite no la recoge) | `ff03efe` |
| Merge de tu rama (`3b60e3d`, sólo `docs/pm/`) | `5ee5fa0` |
| Informe | este commit |

Producto tocado: **ninguno** (`git diff 0d89c20 HEAD -- proyecto_maria` vacío).
No subí el corte de 30 s ni toqué la prueba.

**Resultado: los 30 s son cola, no trabajo de la subida normal.** Su propio
trabajo cuesta ~0,1 s. Espera en dos colas FIFO de 2 hilos cada una
(validación y lectura) detrás de las ocho pesadas, y el reloj de 30 s corre
desde que entra, con la espera incluida. Cada pesada cuesta además unas 3 a 4
veces más que sola, porque los 4 hilos de trabajo comparten el GIL de un único
proceso: hay 4 núcleos, pero se usa uno. El margen es de ±3 s alrededor del
corte. Por eso yo veo 1 rojo de 5 y vos, con un contenedor más lento, 6 de 6.
En producción pasa lo mismo si corre un solo proceso: 1 réplica
(`railway.json`) y 1 worker de gunicorn salvo que haya `REDIS_URL` o
`WEB_CONCURRENCY` (`gunicorn_conf.py:28-33`); no veo las variables de Railway.
Con más workers cada uno tiene sus propias colas y el efecto se reparte, pero
no desaparece. `/upload_excel_v2/` no tiene límite de frecuencia: cualquier
usuario con sesión que suba ocho libros al borde del tope deja a los demás ~30 s
sin poder subir.

## Decisiones

**D4. Cómo evitar que una subida chica espere detrás de las pesadas.**
- **(a) Carril liviano.** Un libro chico (≤ 2 MiB de XML descomprimido, con el
  umbral en una variable de entorno) valida y se lee en pools propios de 2
  hilos. No espera a las pesadas en ninguna de las dos colas. Medido con un
  prototipo (no es producto, `prototipo-carril.diff` en mi scratchpad), sobre
  la prueba real, 3 de 3: «normal: 200 en 0.1 s», «0.2 s», «0.1 s». Límites:
  no ayuda a una subida legítima grande que llega detrás de las pesadas, y
  alguien puede inundar el carril chico (cada libro chico cuesta ~0, así que
  necesita muchos más pedidos). Toca `file_security.py` y `main.py`, así que
  pide una revisión más fuerte.
- **(b) Abaratar el paso caro.** `_ultima_columna` (el `iterparse` de toda la
  primera hoja) baja de 1,58 a 0,86 s con expat directo. La cola sigue siendo
  FIFO, así que la normal sigue esperando, menos pero sin medir cuánto. Sirve
  como complemento, no como arreglo.
- **(c) Pool de procesos para validar y leer.** Paralelismo real, y además se
  puede matar un trabajo vencido (hoy un hilo vencido sigue gastando CPU). Es un
  cambio grande: cada proceso carga sus módulos y no conozco la memoria ni los
  núcleos que da Railway. Sola no saca a la normal de la cola: la acorta.
- (d) Que el reloj de 30 s no cuente la espera en la cola. Esconde el problema
  y no lo recomiendo: la normal seguiría tardando 30 s.
- **Recomiendo (a)**, porque es la única opción que saca a la subida normal de la
  cola, y lo medí. (b) puede ir después en otra pieza. Si elegís (a), la entrego
  con:
  - el umbral calculado una sola vez y sobre las partes XML, no sobre las
    imágenes, para que un logo no mande una factura chica al carril pesado;
  - la prueba más dura de D5;
  - sabotajes que manden la normal al carril pesado.

**D5. Endurecer la prueba.** Hoy el verde esconde la espera: en mi base dio
«normal: 200 en 30.7 s» y pasó. Propongo afirmar también `dt` < 5 s; con el
prototipo da 0,1 a 0,2 s. Es más estricta, no la afloja.
- (a) Sí, junto con D4 (a).
- (b) No, dejarla como está.
- **Recomiendo (a)**: sin eso, una regresión que la vuelva a meter en la cola
  da verde mientras quede debajo de los 30 s.

## Dónde se van los 30 s

`tests/medir_excel2.py::test_linea_de_tiempo` corre el mismo escenario de la
prueba y anota cada paso con su hora y su hilo. Extracto, en segundos desde
el arranque:

| s | qué |
|---|---|
| 0,03–0,05 | entran las 8 pesadas al validador; 2 empiezan a validar |
| 0,06 | entra la normal: queda detrás de las 6 pesadas que esperan |
| 5,09 / 5,13 | terminan las 2 primeras validaciones (1,84 s sola → ~5 s con contención); empiezan las 2 siguientes y 2 lecturas |
| 10,56 / 10,99 | primeras dos respuestas 400 de las pesadas (pasan de 5000 filas, después de leerlas enteras) |
| 12,5 / 12,6 · 20,17 / 20,42 | tercera y cuarta tanda de validaciones |
| **27,46** | **la normal recién empieza a validar** y termina en 0,06 s |
| 27,57–27,62 | lee su hoja en 0,05 s |
| 27,62–29,69 | su «otras hojas» espera en la cola de lectura, detrás de las dos últimas pesadas |
| **29,78** | **respuesta 200 de la normal**, a 0,2 s del corte |

Costo de la pesada sola (`test_etapas`): validarla entera, 1,84 s;
`_ultima_columna`, medida aparte, 1,92 s: es casi todo. `_leer_excel_ruta`,
0,94 s. La normal: 0,0 en todo.

En la lectura se pierde trabajo de dos formas: las pesadas se leen enteras para
después dar 400 por pasar de 5000 filas, y la hoja se parsea dos veces (validar y
`_xlsx_solo_primera_hoja`). Rechazar las de más de 5000 filas ya en la
validación ahorraría la lectura. No lo propongo como D: hay que probar
antes que ese conteo sea equivalente al de la lectura.

GIL (`test_hilos_contra_procesos`, `_ultima_columna` cuatro veces a la vez):
«núcleos: 4; una: 1.96 s; cuatro en hilos: 10.55 s; cuatro en procesos:
2.18 s».

## Comandos para reproducir

```bash
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
# 1. Línea de tiempo: «validar:empieza normal» después de que validan las 8 pesadas (~27 s)
python -m pytest -q -s --no-cov -p no:cacheprovider tests/medir_excel2.py::test_linea_de_tiempo
# 2. GIL: «cuatro en hilos» ≈ 4 × «una»; «cuatro en procesos» ≈ «una»
python -m pytest -q -s --no-cov -p no:cacheprovider tests/medir_excel2.py::test_hilos_contra_procesos
# 3. La prueba real: «normal: 400» o «normal: 200 en ~30 s»
python -m pytest -q -s --no-cov -p no:cacheprovider \
  "tests/test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal"
```

Lo que ya corrí, salida exacta:

| Qué | Salida |
|---|---|
| Prueba real en la base de hoy | «XML: 10282491 bytes; zip: 796162 bytes; entradas: 8; normal: 200 en 30.7 s», `1 passed, 3 warnings in 31.35s` |
| Prueba real con el prototipo (a), 3 corridas | «normal: 200 en 0.1 s» / «0.2 s» / «0.1 s», `1 passed` en 30.42 s, 29.80 s y 30.49 s |
| `test_etapas` | pesada `{'indice': 0.0, 'sin_dtd': 0.02, 'partes': 0.0, 'leer_hoja': 0.02, 'ultima_columna': 1.92, 'TOTAL_validar': 1.84}`; «pesada leer_excel_ruta 0.94» |
| `test_hilos_contra_procesos` | «núcleos: 4; una: 1.96 s; cuatro en hilos: 10.55 s; cuatro en procesos: 2.18 s», `1 passed` |
| Banco de `_ultima_columna` (9101451 bytes, script en mi scratchpad) | `iterparse` 1,58 s; expat con handler 0,86 s |

## No corrido

- `/code-review`, `/security-review` y adversarios: hasta el 2026-10-28 a las
  18:00 UTC no hay presupuesto para subagentes. Sobre esta entrega pesan
  poco: no toca producto.
- Suite completa: no hay cambio de producto. La suite no recoge
  `tests/medir_excel2.py` (`python_files = test_*.py`).
- No medí cuánto cuesta un `.xls` de 2 MiB (para el umbral de (a) en `.xls`).
- No medí cuánto frena el GIL al resto del servidor (otros endpoints) mientras
  corren las pesadas.

## Riesgos

- Mientras no se decida D4, cualquier usuario con sesión puede dejar ~30 s
  sin subir Excel al resto de las cuentas, y el loop pierde CPU en ese rato.
  `/upload_excel_v2/` no tiene límite de frecuencia.
- La prueba sigue sin margen: en tu contenedor da rojo siempre y en el mío,
  de vez en cuando. No la marqué como esperada ni la toqué.
- Fuera del repositorio quedó `/orden1_app.py`, un archivo vacío en la raíz del
  contenedor, de una corrida de ORDEN-1. El control no me dejó borrarlo y no
  afecta al repositorio.

El informe de ORDEN-1 sigue en `cdc9c57` (aceptada, D1–D3 (a)); el de GUARDAR-2,
en `cb42e8f`.

/compact conservar: Dev técnica (Dev 1), sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica, rutina trig_011UpBfwEu9TUzoNUrviqoP5 (/respondio horaria); aviso a la PM principal session_01B7FVQspcEHF7PqNv797wNM con send_message priority next («Dev técnica: …»). ORDEN-1 aceptada (D1–D3 (a)). GUARDAR-2 (cef45ce) en revisión: si vuelve, primero. Entregado: diagnóstico del rojo de test_excel2 (cola FIFO de 2 hilos en validación y lectura + GIL), medición ff03efe, D4 (recomiendo (a) carril liviano; prototipo en scratchpad prototipo-carril.diff) y D5 (endurecer la prueba con dt < 5 s) abiertas: no implementar sin decisión. Reglas: sólo pide la PM o Emi; nada se publica sin el «dale» de Emi para el SHA; nunca main ni push --force; sin secretos ni datos reales; subagentes hasta alto, nunca Fable, sin presupuesto hasta 2026-10-28 18:00 UTC.
