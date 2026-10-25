# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## SUFIJOS-1: D22 antes de escribir código (2026-10-25)

**Resultado:** no arranqué el código. La fuente de los sufijos la decidís
vos, y de esa decisión depende todo lo demás.

**Por qué frené.** La tarea dice que los sufijos se traen de VUCE
(`/cice/sufijos/<posición>`).
- En el repositorio no está esa ruta ni la forma de su respuesta.
- No hay ninguna respuesta guardada: ni la del 24/10 ni una sintética.
- Escribir el lector y el simulado sin conocer la forma es inventar.
- La única forma de conocerla es la consulta real, y la tarea me dice que
  eso es una D.

**Lo que sí hay, público y sin red: el arancel de ARCA**
(`docs/pm/datos/arancel_ARCA_07102026.zip`, del 07/10).
- `sufijos_07102026.txt` dice qué sufijos pide cada posición. Van por
  nivel: capítulo, partida y posición SIM, y se suman.
  - Ejemplo: `3@39@AA@IG 11@MARCA` y
    `3@39@AI@IG 11@CODIGO DE PRODUCTO O ARTICULO`.
  - Para una posición de plásticos (capítulo 39) da AA y AI, lo mismo que
    contestó VUCE el 24/10.
- `nomenclador_07102026.txt` trae la unidad estadística de cada posición
  SIM. Ejemplo: `3920.10.10.100F` lleva `01`, kilogramo, también como el
  24/10.
  - 33 243 posiciones SIM; las unidades más comunes son `01` (26 646) y
    `07` (6 431).
- **Contra:** es una foto del 07/10. Si ARCA cambia un sufijo, CDI no se
  entera hasta que alguien suba el archivo nuevo.

**D22. ¿De dónde salen los sufijos y la unidad estadística?**
- **(a) Del arancel de ARCA, en el producto.**
  - Una tabla local, armada con un script desde el zip.
  - Ninguna llamada a terceros. Se puede probar entero con sintéticos.
  - VUCE queda para una pieza aparte, cuando haya una respuesta real
    guardada.
- **(b) De VUCE, como dice la tarea.**
  - Antes alguien (vos o Emi) guarda una respuesta real de
    `/cice/sufijos/<posición>`, sin datos del cliente: es una consulta
    pública por posición.
  - Con eso armo el lector y el simulado con la misma forma.
  - Mientras tanto la pieza queda frenada.
- **(c) ARCA primero y VUCE encima cuando exista.**
  - Hago (a) ahora.
  - Dejo el lugar para que, cuando haya una respuesta real guardada, VUCE
    corrija lo que ARCA tenga viejo.

**Recomiendo (a).**
- Cubre el caso del 24/10 sin depender de una consulta que no puedo hacer.
- No agrega un tercero que se puede caer en medio de una operación.
- Los sufijos cambian poco.
- (c) agrega una segunda fuente que hoy nadie puede probar.

**Mientras decidís** no escribo código. El resto de la pieza depende de
esta respuesta: completar con lo que lee la IA, el `AI` distinto por
renglón y marcar lo que falta.

## SEPARADORES-1b: entregada a revisión (2026-10-25)

**Resultado:** van los dos puntos en `db39de0`.

- **D19 (b).** Si la pantalla no puede leer el flete, el seguro, los
  gastos o un ajuste, el pedido lleva el texto tal cual.
  - El servidor no genera y dice cuál es, por ejemplo «Flete: «1,500» no
    es un importe.». Nunca da 0, ni un 422 crudo, ni un 500.
  - Tampoco toma «3.480» como 3,48 ni «1e3» como 1000.
- **La familia.** «4500.000» o «98765,432»: un separador y tres cifras,
  con cuatro o más cifras adelante.
  - En la factura, con la pista decimal en contra, queda sin leer y se
    avisa. Antes salía por mil.
  - En la pantalla se pregunta: «¿4.500.000 o 4.500,000?».
- **No cambian:** `_numero_factura` y las ocho guardas de la tarea.
- **El TXT** cambia sólo en esto: un importe que antes salía mal leído
  (por mil o como 3,48), o como 0, ahora no sale.
- **Puertas sobre `db39de0`:** compileall, 12 sabotajes, smoke y e2e en
  verde. La suite dio un rojo de Excel que no es de la pieza: está en la
  base igual (ver «Rojos»).

**Lo que decidís vos:** nada que frene la entrega.
- **D20:** recomiendo dejarlo como está.
- **D21:** es de antes; recomiendo una pieza aparte.
- Abajo van los supuestos reversibles.

| Pieza | SHA |
|---|---|
| Base: SEPARADORES-1 y VALOR-1c | `a2fdabd` |
| Producto: D19 (b) y la familia | `8eaa0a3` |
| Casos y sabotajes | `2b71c71` |
| Producto: «4 500.000» con espacio de miles (adversario) | `9e24ae0` |
| Casos: espacios y seguro calculado (`/code-review`) | `5a6b6d0` |
| Producto: la pregunta no traba la pantalla (seguridad) | `3e67a0a` |
| Casos y sabotaje 3b | `1d12e3b` |
| Docstring de las pruebas | `db39de0` |
| **SHA probado:** suite, compileall, sabotajes, smoke y e2e | **`db39de0`** |

## Decisiones

**D20. Con el seguro calculado, un ajuste ilegible frena el TXT.**
- **Qué pasa.** Con el seguro calculado por el sistema, un ajuste que no
  se lee («1,500») hace que `/generate_maria` dé 400: «…no se puede
  comprobar: Ajustes a deducir: «1,500» no es un importe.».
- **Antes.** La pantalla mandaba ese ajuste como nada y el control lo
  comparaba sin él.
- **Sin el seguro calculado, no frena:** el ajuste se dice en las cuentas,
  como en VALOR-1b.
- **La salida:** «Dejar el seguro como está» o corregir el ajuste.
- **Las pruebas:** las dos ramas, `test_con_el_seguro_calculado_un_ajuste_ilegible_frena_hasta_que_se_elija`
  y `test_un_ajuste_ilegible_se_dice_en_las_cuentas_y_sin_seguro_calculado_no_frena_el_txt`.

Opciones:
- (a) Dejarlo así.
- (b) Que el control del seguro ignore los ajustes ilegibles.

**Recomiendo (a).** Con un ajuste que no se lee, el sistema no puede
comprobar que el seguro que calculó sigue valiendo. Dejarlo pasar es
volver al 0 silencioso que D19 saca.

**D21. En la factura, un cero adelante o varios separadores mal armados
siguen saliendo por mil.**
- **Es de antes:** la base da lo mismo.
- **Es la familia de esta pieza fuera de su letra:** la regla nueva exige
  que el número empiece con 1-9.
- **Lo reprodujo el adversario**, con `_monto_factura`:

| Texto | Pista | Da |
|---|---|---|
| «04500.000» | «,» | 4500000.0 |
| «0500.000» | «,» | 500000.0 |
| «01,500» | «.» | 1500.0 |
| «4500.000.000» | ninguna | 4500000000.0 |
| «4500,000,000» | «.» | 4500000000.0 |
| «4500.000,00» | «,» o «.» | 4500000.0 |

- **«01,500» con «.» contradice tu tarea.** La tarea dice que «01,500» con
  el cero adelante no puede ser miles, y con la pista «.» la factura lo lee
  1500.
- **La guarda que pediste** es «01,500» con «,», que da 1,5, y sigue así.
- **En la pantalla** el cero adelante se lee decimal: «04500.000» da 4500.
  «4500.000,00» da «Los puntos y comas no cierran».

Opciones:
- (a) Dejarlo.
- (b) Una pieza aparte: en `_monto_factura`, el cero adelante y los grupos
  mal armados (el primero de más de tres cifras) quedan sin leer, como la
  familia.

**Recomiendo (b).** Es plata por mil sin aviso. No lo toqué porque la
tarea dice «siguen como hoy» y son casos que no nombra.

## Lo que se hizo

1. **D19 (b).**
   - **La pantalla.** `montoDelPedido` y `ajusteDelPedido` (`finalize.js`)
     mandan el texto que no pudieron leer, recortado.
   - **El pedido.** Acepta texto en el flete, el seguro y los dos gastos
     (`MariaRequest`). `importe_valido` (`maria_generator.py`) acepta sólo
     `-?cifras` con hasta dos decimales y punto. Si no, da ««texto» no es
     un importe.».
   - **`/generate_maria`.** Pasa los cuatro importes a número antes de
     generar (`_importes_como_numeros`, `main.py`). Si uno no se lee, da
     400.
   - **`/avisos`.** Hace lo mismo y lo dice como aviso.
   - **Un ajuste ilegible** va como `valor.error` en las cuentas: «Ajustes
     a deducir: «1,500» no es un importe.». Frena sólo con el seguro
     calculado (D20).
2. **La familia, en la factura.** Regla `sin_grupo` en `_monto_factura`
   (`pdf_extractor.py`):
   - Cuatro o más cifras (de 1 a 9 la primera), un separador y tres cifras,
     con la pista decimal en contra: queda sin leer.
   - Saca antes los espacios, apóstrofos y espacios finos de miles. Así
     «4 500.000» también queda sin leer; lo encontró el adversario de la
     primera vuelta.
   - Con la pista a favor o sin pista, sigue como hoy.
3. **La familia, en la pantalla.** `montos_ar.js` pregunta «¿4.500.000 o
   4.500,000? Escribilo con puntos de miles (4.500.000) o como 4.500,000.».
   Las dos respuestas se leen sin dudas.
   - **El arreglo de seguridad.** La revisión de seguridad encontró que la
     regex que armaba los grupos de la pregunta crecía con el cuadrado del
     largo: 199 998 cifras pegadas tardaban 31 s. Los armo con un recorrido
     lineal, con el rojo antes (31 818 ms).

**Pruebas:** `tests/test_separadores1b.py`, con los dos lados y las
guardas de la tarea.
- **Ejemplos de la familia:** «4500.000», «98765,432», «2500.125» y
  «12345,250». No son los de la tarea.
- **Casos viejos que afirmaban el 0 o el 422, puestos al día:**
  - `test_separadores1.py`: «1,500» viaja como «1,500»;
  - `test_valor1.py:570`: los ajustes ilegibles viajan como texto.

## Puertas, sobre `db39de0`

| Puerta | Salida |
|---|---|
| Suite completa (`pytest -q --no-cov --timeout=120`) | `1 failed, 2384 passed, 102 skipped, 2 xfailed, 93 warnings in 322.50s (0:05:22)`, exit 1. El rojo es `test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope…`, de borde y presente en la base (ver «Rojos») |
| `compileall -q proyecto_maria` | exit 0, sin salida |
| Sabotajes `scripts/testing/sabotaje_separadores1b.sh` | `OK: los 12 sabotajes dan rojo por la razón esperada`, exit 0 |
| Smoke (`smoke_friccion.sh`, puerto 8772) | `==> OK · telemetría + alias session/state + by-cuit protegido`, exit 0 |
| e2e (`e2e_maria.sh`) | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.`, exit 0 |

**Sabotajes, uno por motivo.** Cada uno vuelve a la lectura de hoy y tiene
que dar rojo en el caso que nombra:
- **Factura (1-2b):** multiplica; ignora la pista; los grupos con espacio
  se saltean la regla.
- **Pantalla (3-3b):** no pregunta; se traba con una cifra larga.
- **Pedido (4-5):** el monto viaja como 0; el ajuste no viaja.
- **Servidor (6-10):**
  - lee como Python;
  - el flete vuelve a ser sólo número (422);
  - generar no normaliza;
  - los avisos no miran;
  - el blanco deja de contar como cero.

**No corrí:**
- `ataque_aislamiento.sh`: la pieza no toca sesión, permisos ni datos de
  clientes.
- Los sabotajes de piezas anteriores, que se corren al publicar.
- `/security-review`: falla en este clon porque no existe `origin/HEAD`.
  Lo reemplacé por un subagente de seguridad, Sonnet alto, sobre
  `a2fdabd..HEAD`.

## Rojos

- **Primer rojo de la prueba de la cifra larga.** Falló por la cadena
  esperada, que armé mal: 200 000 cifras no arman grupos de tres desde la
  izquierda. La corregí a 199 998 cifras. Ahí el rojo fue por el motivo:
  `{'ms': 31818, 'pregunta': '¿111.111.'}`.
- **Dos sabotajes daban FALLA sobre `2b71c71`.** Daban rojo, pero el texto
  esperado no aparecía en el resumen corto de pytest. Los cambié para que
  esperen el nombre completo del caso con `FAILED`. Sobre `5a6b6d0`, los
  11 de ese momento dieron `OK: los 11 sabotajes dan rojo por la razón
  esperada`.
- **Suite sobre `db39de0`: un rojo de Excel que no es de la pieza.**
  - Cayó `tests/test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal`
    con «la subida normal dio 400 a los 30.0 s: {"detail":"No pudimos
    abrir el Excel: tardó demasiado. Probá con otro archivo."}».
  - El diff `a2fdabd..db39de0` no toca Excel ni `file_security`.
  - Sola, con la máquina tranquila, falló otra vez sobre `db39de0` y pasó
    sobre `a2fdabd`. Por eso la medí: dos corridas por SHA, alternadas,
    con `-s`. Las cuatro pasaron y la subida normal tardó:

    | SHA | 1.ª | 2.ª |
    |---|---|---|
    | `a2fdabd` (base) | 31,1 s | 31,6 s |
    | `db39de0` | 30,3 s | 32,4 s |

  - **Causa:** en esta máquina (4 CPU) la subida normal tarda lo mismo
    que el tope de lectura de 30 s, en los dos SHAs. Pasa o falla según de
    qué lado caiga. Es de la pieza que escribió la prueba, no de esta.
  - **Riesgo:** en la vida real, ocho Excel pesados al mismo tiempo dejan
    a una subida normal a la par del tope. No lo toqué: está fuera de la
    tarea. Si querés, es una pieza.
  - Salidas en el scratchpad de la sesión: `suite_db39.txt`,
    `excel_db39_sola.txt`, `excel_base_sola.txt`, `excel_alt.txt`.
- **La suite sobre `5a6b6d0`** había dado `2384 passed, 102 skipped, 2
  xfailed`, exit 0.

## Hallazgos de la autorrevisión

| # | Quién (modelo, esfuerzo) | Hallazgo | Qué hice |
|---|---|---|---|
| 1 | Adversario (Opus, alto), 1.ª vuelta | «4 500.000» con «,» daba 4500000 | Arreglado en `9e24ae0`, con el rojo antes (5 failed) |
| 2 | `/code-review high` | Con el seguro calculado, un ajuste ilegible da 400 | D20 |
| 3 | `/code-review high` | La prueba sólo cubría el caso sin seguro calculado | Prueba nueva en `5a6b6d0` |
| 4 | `/code-review high` | Mensaje doble con un ajuste ilegible: la pregunta y ««1,500» no es un importe.»; además desaparecen la tabla de cuentas y el botón de calcular | Riesgo bajo |
| 5 | `/code-review high` | `/avisos` con un monto ilegible devuelve 400 y la lista queda en ese único mensaje: los otros avisos no se ven hasta corregirlo | Riesgo bajo |
| 6 | `/code-review high` | Se normaliza a mitad del endpoint, no en el modelo; los gastos se validan dos veces en `/avisos`; los nombres de los gastos en los mensajes no coinciden (es de antes) | Menor, no se tocó |
| 7 | `/code-review high` y adversario (Opus, alto) | Cero adelante y separadores mal armados, por mil en la factura | D21 |
| 8 | Seguridad (Sonnet, alto) | La regex de grupos de la pregunta es cuadrática: cuelga la pestaña de quien pega una cifra enorme | Arreglado en `3e67a0a`, con el rojo antes |
| 9 | Seguridad (Sonnet, alto) | `_MONEDA_O_CUENTA_ATRAS` (`pdf_extractor.py`) es cuadrática con espacios: «1» + 8000 espacios + «x» tarda 8 s. Es de SEPARADORES-1; sólo se llega por lo que lee Gemini | Riesgo bajo, de antes |
| 10 | Adversario (Opus, alto) | `/generate_maria_export` (`MariaExportRequest`) sigue leyendo «3.480» como 3,48 si un cliente de API lo manda como texto | Fuera de la pieza (v1 manda números); riesgo bajo |
| 11 | Adversario (Opus, alto) | El docstring de las pruebas decía que el servidor rechaza un ajuste ilegible | Corregido en `db39de0`. `DECISIONS.md` D19 dice lo mismo: si querés, alinealo vos |

**Lo que los dos revisores probaron y no se rompió:**
- más de 500 pedidos raros a los dos endpoints, sin ningún 500;
- el TXT, igual a la base salvo en los casos buscados;
- sin inyección de líneas en el TXT;
- los mensajes con el texto devuelto se pintan escapados;
- los endpoints siguen pidiendo autenticación.

## Supuestos reversibles

- **Un cliente de API** que manda un importe como texto con tres o más
  decimales («1234.567», «0.005»), o con «+5» o «.5», ahora recibe 400.
  Antes se redondeaba. La v1 (`app.js`) y la v2 mandan números, salvo lo
  que la pantalla no pudo leer.
- **Un importe en blanco** («», «  ») cuenta como 0, como ya hacía la
  pantalla. Para otro cliente es un 0 sin aviso; antes daba 422.
- **`gastos_fob` y `gastos_anteriores_fob`** aceptan texto, con la misma
  regla.
- **La pregunta pierde el signo «-»:** «-4500.000» pregunta «¿4.500.000 o
  4.500,000?». Igual frena, porque el negativo se rechaza después.
- **`importe_valido(True)` da 1**, como antes. `true` en el JSON sigue
  siendo 1.
- **El 422 de Pydantic** con `null` o una lista sigue crudo; es de antes.

**Riesgos que la tarea dejó anotados, sin tocar:**
- lo que la factura deja sin leer sigue terminando en flete 0, con el
  aviso que no frena;
- un `pais_origen` desconocido sale `CARTPAYORI=310`.

## Archivos de producto que toqué

- `proyecto_maria/core/maria_generator.py`
- `proyecto_maria/main.py`
- `proyecto_maria/pdf_extractor.py`
- `proyecto_maria/static/v2/montos_ar.js`
- `proyecto_maria/static/v2/screens/finalize.js`
- `CHANGELOG.md`

## Para reproducir

```bash
git fetch origin claude/dev-maria && git checkout db39de0
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov tests/test_separadores1b.py   # 105 passed
bash scripts/testing/sabotaje_separadores1b.sh db39de0 <venv>
#   última línea: «OK: los 12 sabotajes dan rojo por la razón esperada»
```

**Apenas entregada:** SUFIJOS-1, frenada en D22 (arriba).

Última vuelta: 2026-10-25 07:59 UTC

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM, rutina horaria minuto 35. Entregada SEPARADORES-1b en db39de0 (compileall, 12 sabotajes, smoke y e2e verdes sobre db39de0; suite con 1 rojo de borde en test_excel2 ocho_libros, también en la base a2fdabd); D20 (recomiendo a) y D21 (recomiendo b, pieza aparte) abiertas en PARA-PM-2.md. SUFIJOS-1 (ROADMAP.md, Fase 1c, orden 1) frenada en D22 (fuente: ARCA local o VUCE /cice/sufijos; recomiendo a, ARCA); sin código hasta la respuesta. Nunca main, sin push --force, sin datos reales del 24/10, nada se publica sin el «dale» de Emi para el SHA, sin Gemini en pruebas, subagentes hasta esfuerzo alto, sin advisor.
