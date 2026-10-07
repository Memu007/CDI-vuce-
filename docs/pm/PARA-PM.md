# Dev 1 → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## EXCEL-1 — devolución entregada sobre `29fc395`

**Resultado:** arreglé los cinco puntos, cada uno con rojo antes y verde
después. MARIA-1b sigue en curso en la misma rama: estos SHA también traen
sus commits. Para ver sólo la devolución: `git diff cb0f886 7b119b6`.

**Lo que decidís vos:**
- **D20.** El CUIT del importador vacío, ¿frena la generación o sólo avisa?
  Hoy avisa, porque la pantalla lo deja «opcional».
- **D21.** El nomenclador está desactualizado: es el de 2018.

Ninguna de las dos frena la devolución.

| | SHA |
|---|---|
| Base (lo que revisaste) | `9cc321e` |
| MARIA-1b en curso, antes de la devolución | `dbc745e` … `cb0f886` |
| Devolución: producto | `15094d8` |
| Devolución: pruebas y sabotajes | `2455418`, `7b119b6` |
| MARIA-1b, dos arreglos del revisor que tocan la subida del Excel | `1041589` (producto), `29fc395` (pruebas) |

### Los cinco puntos

1. **El mapeo aprendido no pisa una columna reconocida.** Es el problema
   del FOB que salía ×10. Para cada campo comparo la columna guardada con
   la que reconozco en el archivo:
   - si la guardada es un nombre conocido de menor prioridad, gana la
     reconocida. Así «Valor» o «Peso», aprendidos con la lista vieja, no
     pisan «Precio Unitario» ni «Peso Neto»;
   - si la guardada es un nombre que el sistema no conoce («Precio Unit.
     USD», «Glosa»), es una corrección a mano y sigue mandando.

   Esto concilia tu punto con lo que pidió la segunda revisión, que no se
   pierda la corrección a mano. Las pruebas mandan `cliente_id`, como la
   pantalla.
2. **Validar el Excel tiene su propio grupo de hilos**
   (`EXCEL_VALIDATE_WORKERS`, 2). El tamaño descomprimido ya se mira en ese
   hilo, antes de abrir el libro.
3. **La fila de ejemplo de la plantilla no entra.** La descripción viene de
   una sola constante, la misma que usa la plantilla.
4. **Dos columnas para el mismo campo:**
   - el catálogo no las guarda: responde 400 «Dos columnas para…»;
   - un catálogo viejo que ya las tiene usa la primera y avisa al subir
     (`avisos_mapeo`, en el aviso final);
   - si el archivo trae una columna con el nombre del campo y el mapeo
     elige otra, ya no da 500.
5. **Las rutas borradas.** La pantalla vieja dice «El Excel se sube en la
   pantalla nueva: entrá a /dashboard y elegí «Excel»». En
   `smoke_test.sh`, el test 7 apunta a `/upload_excel_v2/` y sin sesión
   espera 401 o 403.

Rojo en `cb0f886` (el código anterior a la devolución) con las pruebas
nuevas:

```
E   assert (3500.0, 25.0) == (350, 15)                    (mapeo aprendido, con cliente_id)
E   AssertionError: ['asyncio_0']                          (validar usaba los hilos compartidos)
E   assert ['Laptop 14 p...', 'Telefono'] == ['Telefono']   (fila de ejemplo)
E   assert 200 == 400                                      (catálogo con dos columnas)
E   "dev_detail":"... 'DataFrame' object has no attribute 'tolist'" assert 500 == 200   (x2)
E   assert '/upload_excel/public' not in ...               (pantalla vieja)
7 failed → después: verdes
```

Sabotajes nuevos en `excel1.sh`, uno por punto (actualicé además tres
patrones viejos): ver «Corrido».

### Lo de MARIA-1b que entró acá

El revisor de MARIA-1b encontró dos cosas que tocan esta entrega. Las
arreglé ya:
- el incoterm **FAS**, que la pantalla ofrece, no dejaba generar. Tampoco
  DAT ni DDU, que el generador reconoce;
- mirar las otras hojas del libro podía hacer fallar entera una subida que
  se lee bien. Un libro de 104 KB con 220 hojas vacías dio 504 a los 60 s.
  Ahora es sólo un aviso: mira como mucho 50 hojas, 60 columnas y 1000
  filas, tiene 10 s, y si falla o tarda la subida sigue sin el aviso.

Rojo en `7b119b6`: `4 failed` (FAS, DAT, DDU y la otra hoja que falla).

### Corrido, con su salida

```
suite completa, worktree limpio en 29fc395, venv-limpio: 936 passed, 102 skipped, 25 warnings in 97.98s · fin: 0
sabotajes en 29fc395: excel1, rendimiento1, rendimiento1b, admin1, admin2 → «sabotajes con falla: 0»; maria2 → «OK: los 8 sabotajes dan rojo»; maria1b → 1 ROTO (patrón viejo del incoterm), arreglado en 6755655 → «sabotajes con falla: 0»
smoke_friccion.sh (levantar.sh 29fc395)  → ==> OK · telemetría + alias session/state + by-cuit protegido
ataque_aislamiento.sh                    → MARIA.TXT de Ana generado · Bloqueado: 22 · Fugas: 0
pantalla_excel1.js / pantalla_maria1b.js → OK / OK
smoke_test.sh: test 7 → «PASS: Excel upload without session rejected (401)»; total 6/11.
  El de antes (9cc321e) daba 5/11 con el test 7 en FAIL. Los otros 5 FAIL
  (crear cliente, XSS, PDF, email, CUIT) ya fallaban: el script llama sin
  sesión a rutas que la piden. No los toqué: es otra pieza.
```

## MARIA-1b — en curso (no es entrega)

Hecho en la rama:
- `/generate_maria` responde 400 con todos los errores juntos, y
  `/api/validate/smart` devuelve lo mismo si recibe la cabecera. La pantalla
  de generar y el semáforo se la mandan. Los controles:
  - frenan: moneda vacía, «USD» (en MARIA es «DOL») o que no tiene 3 letras;
    incoterm vacío o inválido; CUIT del importador mal escrito; flete o
    seguro negativos; NCM que perdió el 0 inicial (propone el código con el
    0); y los montos en 0 o negativos, que ya frenaban antes;
  - avisan: una moneda poco habitual, una NCM que no está en el nomenclador
    y el CUIT del importador vacío.
- Los textos no meten saltos de línea ni «=».
- No se inventan DOL, FOB ni cantidad 1 en la pantalla. Al guardar la
  operación tampoco se inventan cantidad 1, peso 0,5 ni «XX».
- Las filas sin leer y las otras hojas quedan en el semáforo con
  «Descartar» (D17 y D18).
- Sabotajes en `maria1b.sh` y una prueba de pantalla,
  `pantalla_maria1b.js`, que da rojo en el código anterior.

Falta, del revisor (lo hago apenas entregue esta devolución):
- el «=» y el `\x7f` en el sufijo SBT;
- los saltos de línea Unicode (` `, `\u0085`);
- «Descartar» cierra el semáforo;
- el TXT escribe la moneda, el incoterm y el CUIT tal como llegan, no
  normalizados;
- el servidor todavía pone DOL y FOB por defecto si el pedido no los trae;
- la búsqueda en el catálogo recorre todo por cada ítem (5000 ítems tardan
  3 s);
- `finalize.js` todavía manda «XX» al guardar;
- monedas numéricas, a confirmar;
- `/generate_maria_export` tampoco limpia los textos. Sólo la llama la
  pantalla vieja: lo propongo aparte.

## Decisiones

- **D20 — ¿El CUIT del importador vacío frena?** La pantalla de revisión lo
  marca «opcional (extranjeros sin CUIT)», pero en una importación el
  importador es argentino y la declaración lo necesita. Hoy: vacío avisa, y
  mal escrito frena. Opciones: (a) que vacío también frene y la pantalla deje
  de decir «opcional»; (b) dejarlo como aviso.
  **Recomiendo (a).** El TXT sin el CUIT del importador no sirve para
  presentar.
- **D21 — El nomenclador es el de 2018.** `ncm_arca_metadata.json` dice
  `source_file: nomenclador_19122018.txt`. Le falta la enmienda de 2022: por
  ejemplo 8517.13.00 (teléfonos), 8524 (pantallas) y 8549 (desechos
  eléctricos). Por eso «no está en el nomenclador» avisa en vez de frenar:
  si frenara, trabaría operaciones válidas. También afecta al filtro de las
  sugerencias de NCM de la IA, que descarta lo que no está en el catálogo.
  Opciones: (a) pieza para actualizar el catálogo desde ARCA con el
  nomenclador vigente, y después frenar; (b) dejarlo como aviso.
  **Recomiendo (a)**, en la Fase 2 o antes si las sugerencias de NCM fallan
  con teléfonos.

## Qué no corrí

- No pedí revisores independientes para la devolución: son cambios chicos y
  cada uno tiene su prueba y su sabotaje.
- No medí la carga de 12 subidas de un `.xlsx` de 8 MB que mediste vos. Mi
  prueba comprueba que la validación corre en un hilo del grupo propio, no
  el tiempo de la consulta de NCM.

## Sigo con

MARIA-1b: los nueve puntos del revisor de arriba, su revisión y la entrega.

Última vuelta: 2026-10-07
Contexto: ~90 %. Emi: pedile a esta sesión el `/compact` cuando puedas.

`/compact conservar: Dev 1 de CDI, rama claude/dev1-tecnica. EXCEL-1:
devolución entregada sobre 29fc395 (5 puntos de la PM con prueba y sabotaje).
MARIA-1b en curso: controles en proyecto_maria/core/controles_maria.py, usados
en /generate_maria y /api/validate/smart; semáforo con avisos del Excel y
Descartar; tests/test_maria1b_controles.py, scripts/testing/sabotajes/maria1b.sh,
scripts/testing/pantalla_maria1b.js. Falta del revisor: «=» y \x7f en el sufijo
SBT, saltos Unicode, Descartar cierra el semáforo, TXT con valores crudos vs
normalizados, defaults DOL/FOB del servidor, find_by_code lineal, XX en
finalize.js al guardar, monedas numéricas (confirmar), /generate_maria_export
sin limpiar (proponer aparte). D20 (CUIT vacío) y D21 (nomenclador 2018)
abiertas. Entorno: PM_DIR=/tmp/cdi-dev1, levantar.sh <SHA> <puerto>, venv
/tmp/cdi-dev1/venv y venv-limpio; rutina de la PM trig_01TvMmGfSLDfbcJrf66ZZ7YK.`
