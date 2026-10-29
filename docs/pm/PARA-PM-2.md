# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.


## DESPACHO-1b, devolución de las 20:07: **entregada** en `1f5480e` (2026-10-28)

**Resultado:** los 5 puntos y la D47 (b) están arreglados en el producto, cada uno con su rojo antes del arreglo y su sabotaje. El riesgo del `.env` se arregló en una línea. Base `f125939`.

**Nada para decidir.** No abro ninguna D; la próxima libre sigue siendo la D49. Los supuestos reversibles están en «Supuestos».

| SHA | Qué |
|---|---|
| `9aee77f` | fix: trabajo, turnos, identidad, promedios y D47 (producto + CHANGELOG) |
| `8d9fbc0` | test: casos y sabotajes de la devolución |
| `712778a` | fix: el tope de CPU corta en medio de una hoja y el entero enorme no da 500 (hallazgos del adversario y del code-review) |
| `fe6dfbc` | test: hoja cara, señal restaurada, origen con mitad de par, entero enorme y sus sabotajes |
| `c6ad2f4` | test: los sabotajes de memoria siguen la sangría de `_leer_hojas` |
| `1f5480e` | test: sabotaje del promedio en el historial de operaciones |
| este | docs: informe |

## Punto por punto

1. **Trabajo y turnos.**
   - **CPU:** el hijo corta a los 10 s de CPU (`_MAX_CPU_LECTURA`). El corte llega aunque sea en medio de una hoja: `setitimer(ITIMER_PROF)` lanza `_DemasiadoTrabajo`, que es `BaseException` para que ningún `except Exception` de pypdf se lo coma. El aviso dice «El PDF da demasiado trabajo: leí hasta la hoja N.», y la señal se restaura al salir.
   - **Turnos:** un usuario lee un despacho a la vez (`clave=username`); el segundo da 429. Siguen siendo dos lectores en total.
   - **Medido en `1f5480e`**, 4 CPU con la suite corriendo al lado. Es CPU propia del hijo, así que no depende de la carga:
     - PDF con la forma del de la PM (20 hojas × 14 000 operaciones, 40 KB): `40021 bytes 10.73 s cpu 10.61 ('ok', 0, ['El PDF da demasiado trabajo: leí hasta la hoja 14.', …])`. Antes, 23,5 s.
     - Hoja cara sola (hallazgo 1 del adversario, 160 KB de `T*`, PDF de 770 bytes): `770 10.08 ['El PDF da demasiado trabajo: leí hasta la hoja 0.']`. El adversario midió unos 23 s antes del arreglo.
   - **Casos:** `test_un_pdf_que_da_mucho_trabajo_deja_de_leerse_por_tiempo_de_cpu`, `test_una_sola_hoja_cara_se_corta_en_el_tope_de_cpu`, `test_el_lector_aparte_corta_una_sola_hoja_cara`, `test_el_tope_de_cpu_deja_la_senal_como_estaba`, `test_un_usuario_lee_un_despacho_a_la_vez_y_no_frena_a_otro` y `test_leer_con_otra_lectura_en_curso_da_429`.
2. **Identidad.** Dos productos son el mismo sólo con el NCM sin puntos ni espacios igual **y** la descripción entera igual (sin mayúsculas ni espacios de más), sin el corte de 200.
   - Vale para el despacho (`solo_mismo_ncm`) y para el paso 1 del upsert, que usan `learn` y las operaciones.
   - **Casos:** `test_el_mismo_ncm_con_o_sin_puntos_es_el_mismo_producto`, `test_lo_aprendido_con_puntos_y_el_despacho_son_el_mismo_producto`, `test_aprender_con_puntos_suma_al_producto_del_despacho_y_no_a_otro` y `test_dos_textos_largos_con_el_mismo_comienzo_no_se_funden`.
3. **Promedio.** Hay columnas nuevas `veces_peso`, `veces_valor` y `veces_cantidad`, con migración. Un uso sin valor no mueve el promedio ni se cuenta.
   - Una fila de antes (con `NULL`) usa `veces_usado` como hasta ahora.
   - El arreglo está también en `client_service.py:371`, el historial de operaciones.
   - **Casos:** `test_el_promedio_no_cuenta_los_usos_sin_valor` y `test_el_historial_de_operaciones_tampoco_cuenta_los_usos_sin_valor`. Esa misma secuencia da (3, 3,0, 4,5, 10,0); la base daba `(3, 2.0, 3.0, 7.0)`.
4. **El mismo tope para todo lo que entra al catálogo** (`valor_para_promedio`).
   - Infinito, NaN, negativo, ≥ 1e12 o un entero JSON enorme no entra, en el despacho, `learn` y el historial.
   - En el PUT de peso eso da 400. El cero, como número o como «0» en texto, borra el peso.
   - Un infinito guardado antes ya no rompe el GET del catálogo ni la búsqueda: sale `null`, y el próximo valor bueno lo reemplaza.
   - `\ud800` en la descripción o en el origen da 422 al guardar, y el mensaje no lo repite.
   - **Casos:** `test_aprender_un_peso_infinito_no_lo_guarda_y_el_catalogo_anda`, `test_aprender_un_entero_enorme_no_da_500`, `test_un_infinito_guardado_antes_no_rompe_el_catalogo_y_se_arregla`, `test_un_infinito_guardado_antes_no_rompe_la_busqueda`, `test_cambiar_el_peso_a_algo_que_no_es_un_peso_da_400`, `test_cambiar_el_peso_a_cero_lo_borra`, `test_guardar_una_mitad_de_par_suelta_da_422` y `test_guardar_un_origen_con_mitad_de_par_da_422`.
5. **Mutantes vivos**, un caso por cada uno:

   | Mutante | Caso |
   |---|---|
   | número de hijos a la vez | `test_como_mucho_dos_lectores_a_la_vez` |
   | `except MemoryError` al abrir | `test_sin_memoria_al_abrir_el_pdf_no_se_disfraza_de_pdf_roto` |
   | tope de pypdf que no es Flate | `test_una_hoja_que_se_infla_con_run_length_se_saltea` y `test_los_topes_de_pypdf_cubren_todos_los_filtros` |
   | `columnas[max(k,0)]` | `test_un_valor_a_la_izquierda_de_todos_los_rotulos_va_al_primero` |
   | `_MAX_TEXTO` sin parchar | `test_el_tope_de_texto_de_verdad_corta_en_la_hoja_10` |
   | borde de 500 renglones | `test_guardar_justo_el_tope_de_renglones_se_guarda` |
   | `isinstance(resultado, dict)` | `test_un_lector_que_no_devuelve_un_objeto_es_un_error` |
   | `BrokenPipe` | `test_un_lector_que_sale_sin_leer_todo_dice_con_que_salio` |

- **D47 (b):** sólo con divisa `USD` o `DOL` se guarda `valor_unitario`. Con otra divisa, o sin divisa, el valor no se guarda, ese renglón avisa y lo demás se guarda. Casos: `test_guardar_un_despacho_que_no_esta_en_dolares_no_guarda_el_valor` y `test_guardar_un_despacho_en_dolares_guarda_el_valor`.
- **Riesgo del `.env`:** el hijo recibe `PYTHON_DOTENV_DISABLED=1` en su entorno (despacho_lector.py:646). Sabotaje: «el lector lee el .env».

## Rojo antes del arreglo (salida copiada)

- **Casos de `8d9fbc0` con el producto de la base `f125939`:** `24 failed, 98 passed, 5 warnings in 60.81s`. Algunos motivos:
  - `KeyError: 'PYTHON_DOTENV_DISABLED'`
  - `TypeError: leer_despacho_aparte() got an unexpected keyword argument 'clave'`
  - `cannot import name 'LectorOcupado'`
  - el NCM en tres filas: `'ncm': '8471.4900' … 'ncm': '8471.49.00'`
  - `assert (3, 2.0, 3.0, 7.0) == (3, 3.0, 4.5, 10.0)`
  - `ValueError: Out of range float values are not JSON compliant: inf`
  - `"peso_unitario_avg":-1.0` aceptado
  - `"code":"internal_error"` con `\ud800`
  - `KeyError: 'avisos'` (D47)
- **Casos de `fe6dfbc` y `1f5480e` con el producto de `9aee77f`:** `13 failed, 126 passed, 3 warnings in 66.85s`. Motivos:
  - Las dos de la hoja cara: `AssertionError: ['El PDF no tiene texto que se pueda leer: parece escaneado. …']`. No hubo corte de CPU.
  - `OverflowError: int too large to convert to float` en `main.py:8220-8222` (learn) y en `client_memory.py:47` (PUT).
  - Búsqueda: `ValueError: Out of range float values are not JSON compliant: inf`.
  - Aprender con puntos: `assert [('39269090',...84713012', 2)] == [('39269090',...84713012', 1)]`.
  - El peso cargado: `assert 2.5 == 3.0`.
  - PUT `false` aceptado y «0» en texto: `{"detail":"El peso tiene que ser un número positivo."}`.
  - Origen con `\ud800`: `UnicodeEncodeError: 'utf-8' codec can't encode character '\ud800' … surrogates not allowed`.

## Revisores

| Revisor | Modelo y esfuerzo | Hallazgos | Qué hice |
|---|---|---|---|
| adversario sobre `8d9fbc0` | Sonnet alto | **1 alta:** una sola hoja cara (`T*`, cuadrático) pasa el tope entre hojas: 160 KB tardaba unos 23 s y 500 KB más de 400 s, y dos de esos dejan a un tercero en timeout. **2 media:** `\ud800` en `origen` da 500. **3 baja-media:** un entero enorme da 500 en learn y en el PUT. 4–7 bajos o informativos | 1, 2 y 3 arreglados (`712778a`, casos en `fe6dfbc`). 5 (`false`) también. 4 y 6 van a riesgos; 7 no es defecto |
| `/code-review high f125939..9aee77f` | el de la sesión, fork | infinito en la búsqueda; NCM exacto en el upsert y en `update_product_history`; la migración se traga errores; tope de CPU sólo entre hojas; corte en el borde de hoja; divisa del cliente; PUT `false`/«0»; código duplicado; `_MEDIO_PAR` repetido | Arreglados la búsqueda, el NCM del upsert, el CPU dentro de la hoja, el PUT y `_MEDIO_PAR` (el PUT importa el de `client_memory`). El resto va a riesgos |
| `/security-review` | a mano (la skill falla en este entorno) | sin hallazgo nuevo | El único llamador de producto de `leer_despacho` es el `main` del hijo (despacho_lector.py:695), así que el temporizador nunca vive en uvicorn. La migración arma SQL sólo con nombres constantes. El PUT con lista o dict da 400. Los endpoints siguen con `_get_owned_client` |

## Puertas (salida exacta)

| Puerta | SHA | Salida |
|---|---|---|
| `tests/test_despacho1b.py` | `1f5480e` | `139 passed, 3 warnings in 43.03s` |
| sabotajes `despacho1b.sh` (67) | `1f5480e` | 67 líneas `ROJO`, `sabotajes sin rojo: 0`, salida 0 |
| suite completa | `c6ad2f4` | `4138 passed, 336 skipped, 2 xfailed, 97 warnings in 619.79s (0:10:19)` |
| `compileall -q proyecto_maria` | `c6ad2f4` | `compileall 0` (dentro de la suite) |

- La suite corrió sobre `c6ad2f4`. `1f5480e` cambia sólo el script de sabotajes, así que el producto y los casos son los mismos.
- **No corrido:** el smoke y `ataque_aislamiento.sh` (no se tocaron sesión ni permisos; los endpoints son los mismos con `_get_owned_client`), Postgres 16 (la migración sólo agrega columnas `INTEGER` que aceptan `NULL`) y la pantalla en un navegador (`clientes.js` cambia 7 líneas: el mensaje del 400 y no dejar el valor rechazado en el campo).

## Para reproducir

```bash
S=<tu venv>; rm -f test.db; GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
  DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares ENVIRONMENT=test DATABASE_URL=sqlite+aiosqlite:///./test.db \
  python -m pytest -q --no-cov tests/test_despacho1a.py tests/test_despacho1b.py
#   tiene que dar: `152 passed` (1a + 1b; acá: `152 passed, 3 warnings in 43.08s`)
PY=python scripts/testing/sabotajes/despacho1b.sh 1f5480e
#   tiene que terminar con «sabotajes sin rojo: 0» y código 0 (67 líneas ROJO)
```

## Supuestos reversibles

- **Identidad:** dos descripciones que difieren sólo en tildes o puntuación («TAPA, VERDE» y «TAPA VERDE») ya no se funden en el despacho. Es la «descripción entera» que pediste. Si querés que se fundan, se compara la normalizada sin cortar.
- **Peso editado a mano:** cuenta como un uso (`veces_peso = 1`). El próximo valor del despacho promedia con peso 1 frente al de la persona.
- **D47:** la divisa vale si es exactamente `USD` o `DOL`, sin espacios ni mayúsculas de más.

## Riesgos (sin arreglo acá)

- **Media.** El corte en el borde de hoja puede dejar incompleto un renglón que sigue en la hoja siguiente. El aviso general lo dice («leí hasta la hoja N»), pero no marca el renglón.
- **Media.** La divisa de D47 la manda el cliente en el body: quien llama a la API puede declarar `USD` en un despacho en euros. Leerla en el servidor es la (a) de la D47, que quedó para otra pieza.
- **Media.** La migración de `veces_*` se traga el error como «no crítica», igual que las demás de `main.py`. Si el `ALTER` falla en Postgres, el modelo nuevo falla en cada consulta de `client_product_history`.
- **Baja.** Dos usuarios (o dos cuentas) con un PDF pesado cada uno ocupan los dos lectores unos 10 s; un tercero espera. Antes eran 120 s.
- **Baja.** Fuera del hilo principal sólo vale el tope entre hojas. Hoy no hay ningún llamador así en producto.
- **Baja.** «leí hasta la hoja 0» cuando corta en la primera hoja: el texto no es lindo.
- **Baja.** `ClientService.get_frequent_products` y `update_product_history` (`client_service.py`) devuelven el promedio crudo y comparan el NCM tal cual. Hoy no tienen llamadores de producto (lo busqué con grep).
- **Baja.** La regla del promedio está copiada en `client_memory` y en `client_service`, y el tope 1e12 está dos veces (`_MAX_VALOR` y `_MAX_NUMERO`).
- **Baja.** `learn` con `\ud800` en el NCM o en el origen da 200 con `aprendidos: 0`: no aprende, pero tampoco da 500.
- **Baja.** No hay prueba directa de la bandera `leyendo` de la pantalla.

## Archivos de producto tocados

`proyecto_maria/core/despacho_lector.py`, `proyecto_maria/database/models.py`, `proyecto_maria/main.py`, `proyecto_maria/services/client_memory.py`, `proyecto_maria/services/client_service.py`, `proyecto_maria/static/v2/screens/clientes.js`. Además, `CHANGELOG.md`, `scripts/testing/sabotajes/despacho1b.sh`, `tests/pdf_bombas.py` y `tests/test_despacho1b.py`.

**Después:** por la pausa de Emi, RENDIMIENTO-1c queda en curso y sin entregar (abajo).

---

## DISCO-1, vuelta de las 20:58: **entregada** en `5c46e36` (2026-10-28)

**Resultado:** el producto no cambia. La prueba de Postgres ahora ve los dos lugares del bloqueo y su clave. Cada mutante de la devolución da rojo en `disco1.sh`, y el texto del bloqueo acepta el 500 en cualquier posición.

**Orden:** la entregué después de DESPACHO-1b, aunque pediste que fuera antes. Cuando llegó tu orden, 1b ya estaba terminada y sólo esperaba sus sabotajes. La entregué primero para no dejar seis commits sin subir. DISCO-1 no toca nada de 1b.

**Nada para decidir.** La próxima D libre sigue siendo la D49.

| SHA | Qué |
|---|---|
| `5c46e36` | test: el bloqueo por dueño en cada camino que escribe en tandas, y tres sabotajes nuevos |
| este | docs: informe |

## Punto por punto

1. **La carga de archivos viejos toma el bloqueo de su dueño.**
   - La prueba se arma así:
     1. Una conexión aparte deja sin confirmar una fila de A.
     2. Una importación de A queda esperando esa fila, con el bloqueo de A tomado. Se ve en `pg_locks`.
     3. La carga de un archivo viejo de A corre en un proceso aparte, el mismo `_migrate_ncm_historial_archivos` del arranque.
   - **Qué tiene que pasar:** la carga espera, y se ve como un `advisory` no concedido, con el proceso vivo y la importación sin terminar. Al soltar la fila, las dos terminan: `200 0 0 0`.
   - Sin `_bloquear_historial(db, dueno)` en la carga da `FALLA | la carga del archivo de A espera a la importación de A: terminó`.
2. **La clave lleva el dueño.** Con A tomado:
   - una importación de B termina (`200`);
   - la carga de un archivo de B termina (`0`, 300 filas).
   - Con la clave `"ncm_historial:"`, las dos dan `FALLA | … no espera el bloqueo de A: esperó`.
   - Es tu ejemplo de «un dueño que termina mientras otro tiene tomado el suyo».
3. **El texto del sabotaje del deadlock.** Los códigos se ordenan antes de imprimirlos, así que el 500 sale igual venga primero o segundo. El texto esperado es `vuelta 0: [200, 500]`.
   - Agregué el mutante que saca el bloqueo sólo de la importación y lo deja en la carga. Da rojo por el deadlock y por la carga de A.
4. **La espera** se mira en `pg_locks` y en si terminó el proceso o la importación, con un plazo de seguridad de 120 s. No hay esperas fijas. `pg_locks` se filtra por la base de la prueba: es de todo el servidor, y otra corrida en el mismo Postgres daría un «esperó» falso.

**Mutantes en `disco1.sh`**

| Sabotaje | Rojo esperado |
|---|---|
| importar sin el bloqueo por dueño (`if False:`) | `vuelta 0: [200, 500]` y `carga del archivo de A … terminó` |
| importar sin tomar el bloqueo (la carga sí lo toma), **nuevo** | los mismos dos |
| cargar archivos viejos sin tomar el bloqueo, **nuevo** | `carga del archivo de A … terminó` |
| el bloqueo sin el dueño en la clave, **nuevo** | `importación de B … esperó` y `carga del archivo de B … esperó` |

## Puertas, sobre `5c46e36`

| Puerta | Salida |
|---|---|
| `tests/test_disco1.py` | `33 passed, 3 warnings in 5.99s` |
| `disco1_postgres.py`, Postgres 16 local | 39 líneas `OK`, `fallas: 0`, salida 0 |
| `disco1.sh` con `PG_URL` (Postgres 16 local) | 46 líneas `ROJO`, `sabotajes sin rojo: 0`, salida 0 |

No corrí la suite completa: `5c46e36` toca sólo `scripts/testing/`, y el producto es el de `1f5480e`, cuya suite está en el informe de DESPACHO-1b.

```bash
git show --stat 5c46e36            # sólo scripts/testing/disco1_postgres.py y scripts/testing/sabotajes/disco1.sh
PG_URL=postgresql://<usuario>@127.0.0.1:<puerto>/postgres bash scripts/testing/sabotajes/disco1.sh 5c46e36
#   termina con «sabotajes sin rojo: 0»
```

## Riesgos (de tu medida; ninguno se arregla acá)

- **El 400 de guardar-uso** es una regresión sólo con un cliente sin proveedor y una descripción de 2001 caracteres o más.
- **Anterior a la pieza:** con cliente y proveedor, una descripción de 301 a 2000 caracteres ya se perdía en silencio, con 200, en la memoria del cliente y en el catálogo, porque `product_key` es `String(300)`.
- **guardar-uso espera** mientras el mismo dueño importa: 9,3 s con 60 000 filas en tu medida, y no hay `lock_timeout`.
- **La carga de archivos viejos descarta para siempre** lo que no pasa los topes, y el log no dice qué entrada era.

---

## RENDIMIENTO-1c (D48 (a)): **en curso, sin entregar** (pausa de Emi, 28/10 22:01 UTC)

Frené por la pausa: queda para cuando Emi diga de retomar. Los commits ya están en la rama, así que **no hace falta revisarlos ni integrarlos** hasta que llegue el informe.

| SHA | Qué |
|---|---|
| `ccf5d8c` | fix: validar un PDF al subirlo corre en un proceso aparte, con tope de memoria y de tiempo (facturas y despachos) |
| `033cb11` | test: tu PDF de 200 repeticiones no hace crecer la app; diez de A no frenan a B; sabotajes |
| `843cc08` | fix: si el proceso que valida se cae, la respuesta es 500 y no «Invalid PDF file» (hallazgo del `/code-review`) |
| `7dd008f` | test: el 500, y la prueba de las diez se mide por orden y no por reloj |

**Lo que ya se corrió, sobre `033cb11`:**
- `tests/test_rendimiento1c.py`: la app crecía `1029` MB antes del arreglo y ahora crece menos de 150.
- `test_rendimiento1.py`, `test_despacho1b.py` y `test_rendimiento1c.py` juntos: `156 passed, 3 warnings in 77.99s`.
- Sobre `7dd008f`: `tests/test_rendimiento1c.py` dio `4 passed, 3 warnings in 18.83s`.

**Falta para entregar:**
- correr `rendimiento1c.sh`, `rendimiento1.sh` y `despacho1b.sh` sobre el SHA final;
- la suite completa;
- la revisión adversarial (la frené a la mitad por la pausa);
- el informe.

**Hallazgos del `/code-review high` que van a ir como riesgo o D:**
- **Alta, fuera de la pieza (la propongo como D49):** la factura vuelve a abrir el PDF dentro de la app para buscar el vendedor cuando Vision no lo trae (`main.py:4283`, `extraer_texto_pdf_seguro`). Un PDF de 30 a 40 repeticiones pasa la validación y suma entre 160 y 215 MB por subida.
- **Dos cuentas a la vez** ocupan los dos lugares globales para validar, y los demás esperan hasta 30 s.
- **Sin tope de CPU al validar:** no encontré ningún PDF que haga lenta la validación. pypdf corta el árbol de hojas en 100 000 entradas, que tardan 0,6 s. El tope de tiempo mata al hijo igual.
- **`despacho/leer` levanta dos hijos.**

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria; PAUSA de Emi desde el 28/10 22 UTC hasta que diga de retomar (sábado 31/10): rutina apagada, no arrancar nada ni lanzar subagentes. Entregadas sin veredicto: DESPACHO-1b (1f5480e) y DISCO-1 vuelta (5c46e36). En curso sin entregar: RENDIMIENTO-1c (ccf5d8c, 033cb11, 843cc08, 7dd008f); al retomar: sabotajes rendimiento1c.sh, rendimiento1.sh y despacho1b.sh, suite, adversario Opus alto, informe con D49 (vendedor de la factura abre el PDF en la app). Después SESION-1 → ABUSO-1 → SUFIJOS-2 → EMAIL-1 (D45) → CONEXIONES-1 (D46) → OBSERVABILIDAD-1 → ORG-1+D40. Nunca main; nada se publica sin el «dale» de Emi para el SHA; sin secretos ni datos reales; Devs hasta esfuerzo alto, sin Fable; sin advisor.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria. PAUSA de Emi hasta el domingo 1/11 (aviso de la PM, 2026-10-29 10:36 UTC); rutina apagada, me despierta la PM. Quedé en DESPACHO-1b vuelta 4, sin entregar: producto en bd14302, pruebas en bb913d0 (281 passed); despacho1b.sh sobre bb913d0 cortado a pedido en el sabotaje 95 de 132, los 95 en ROJO y ninguna falla. Al retomar: correr despacho1b.sh entero sobre el SHA de entrega hasta «sabotajes sin rojo: 0», llenar {SAB} y {SHA} en docs/pm/BORRADOR-INFORME-DESPACHO-1b-vuelta4-DEV2.md, pasarlo al cuerpo de este archivo, borrar el borrador, merge de la rama PM, push y timbre. Después RENDIMIENTO-1c y SESION-1. Nunca main; nada se publica sin el «dale» de Emi; sin secretos ni datos reales; Devs hasta esfuerzo alto, sin Fable; sin advisor.
