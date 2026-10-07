# Dev 1 → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## MARIA-1b — entregada sobre `21a7a7e`

**Resultado:** los cuatro puntos del alcance están hechos, con D20 (a). Los
dos archivos reales salen idénticos por la ruta `/generate_maria`. Hubo dos
revisores: el primero encontró 11 cosas, el segundo 5. Arreglé lo que
cabía en la pieza; lo demás queda abajo, con lo que propongo.

**Lo que decidís vos:** D22, la ruta de exportación `/generate_maria_export`,
que tampoco limpia los textos. Es fuera de alcance y no frena la entrega.

| | SHA |
|---|---|
| Base (EXCEL-1 aceptada) | `7b119b6` |
| Producto | `dbc745e`, `cc01e5b`, `1041589`, `56c4697`, `bfd51e6` (y `15094d8`, de la devolución de EXCEL-1, ya aceptada) |
| Pruebas y sabotajes | `c8e05dd`, `567b152`, `b3c0e83`, `763d3a9`, `cb0f886`, `29fc395`, `6755655`, `c1ef3a2`, `21a7a7e` |
| CHANGELOG | `03717a8` |

### Qué cambia para el usuario

1. **Controles antes de generar.** `/generate_maria` responde 400 con
   todos los errores juntos. `/api/validate/smart` devuelve lo mismo si
   recibe la cabecera; la pantalla de generar y el semáforo se la mandan,
   así que el botón «Generar» ya queda deshabilitado antes.
   - **Frenan:**
     - moneda vacía, «USD» («en MARIA se escribe DOL») o que no tiene 3
       letras;
     - incoterm vacío o inválido. Se aceptan los del generador, FAS y DAT,
       DAF, DES, DEQ y DDU;
     - CUIT del importador vacío (D20) o con el dígito verificador mal: el
       mismo algoritmo que la pantalla;
     - flete o seguro negativos;
     - NCM que perdió el 0 inicial: «¿Es 01012100000A?»;
     - cantidad, valor o peso vacíos, negativos o en 0, que ya frenaban
       antes.
   - **Avisan:** una moneda poco habitual, y una NCM que no está en el
     nomenclador, porque es el de 2018 (D21, pendiente de Emi).
   - La pantalla de revisión pide el CUIT del importador: ya no dice
     «opcional» y lo cuenta en «Falta: …» antes del clic.
2. **Ningún texto rompe el TXT (M10).**
   - En la cabecera y en los ítems, los saltos de línea (también los de
     Unicode, ` `, ` ` y `\x85`) y los caracteres de control
     pasan a ser un espacio, y el «=» un guion.
   - El sufijo SBT es un código: con «=» o con controles se rechaza, con su
     propio mensaje.
   - El TXT lleva la moneda, el incoterm y el CUIT tal como se controlan:
     en mayúsculas, sin espacios y sin guiones.
3. **Nada inventado.**
   - El servidor ya no pone DOL ni FOB si el pedido no los trae.
   - La pantalla de generar tampoco inventa DOL, FOB ni cantidad 1.
   - Al guardar la operación (`save_client_operation`, la D6 de la Dev 2)
     no se inventan cantidad 1, peso 0,5 ni «XX», ni en el servidor ni en
     la pantalla.
4. **Avisos del Excel (D17 y D18).**
   - Las filas sin leer y las otras hojas con datos van en `operacion` y
     quedan en el semáforo con un botón «Descartar» propio.
   - Siguen ahí después de otra validación, y «Descartar» no cierra el
     semáforo.
   - Mirar las otras hojas es sólo un aviso: como mucho 50 hojas, 60
     columnas, 1000 filas y 10 s. Si falla, la subida sigue sin el aviso.

### Lo que vale la pena saber

- **El CUIT anonimizado del archivo real (`30999999990`) no tiene un
  dígito verificador válido.** Es inventado. La prueba por la ruta usa
  `30999999995` y compara contra el archivo real cambiando sólo esa línea.
  El archivo real no se tocó.
- **Pruebas viejas y herramientas con datos inválidos.** Cinco pruebas de
  `/generate_maria`, la operación simulada de la pantalla y
  `ataque_aislamiento.sh` generaban sin CUIT del importador, sin moneda o
  con un CUIT inválido. Les puse datos válidos. Si no, el ataque se quedaba
  sin el TXT de Ana para robar, y la puerta pasaba por la razón
  equivocada: ahora el TXT se genera y queda bloqueado.
- **Dos pruebas mías no distinguían el defecto, y las corregí.**
  - La de «no inventar cantidad 1 en la validación previa»: `Item` ya
    acepta la cantidad vacía, así que ese 1 era casi inalcanzable. Saqué
    la prueba; el cambio quedó por coherencia.
  - El «=» y la hoja vacía: dos sabotajes daban verde. Las ajusté.

### Rojo antes y verde después

```
en c0bae0e (antes de MARIA-1b): 22 failed, 7 passed
  (moneda, incoterm, CUIT, flete/seguro, NCM sin 0, textos x5, validación previa,
   guardado sin inventar, filas y hojas del Excel; las 7 que pasan: archivo
   idéntico, montos que ya frenaban, libro de una hoja)
en 7b119b6: 4 failed (FAS, DAT, DDU; otras hojas que fallan)
en fcd2fb7: 10 failed (CUIT vacío, saltos Unicode x4, sufijo SBT x2, DOL/FOB
  inventados, TXT sin normalizar, 5000 ítems en más de 0,5 s)
pantalla_maria1b.js: c0bae0e → FALLA: el semáforo no muestra las filas sin leer
                     fcd2fb7 → FALLA: «Descartar» cerró el semáforo
                     21a7a7e → OK: pantalla MARIA-1b
```

### Corrido, con su salida

```
suite completa, worktree limpio en 21a7a7e, venv-limpio: 941 passed, 102 skipped, 25 warnings in 100.17s · fin: 0
sabotajes en 21a7a7e (excel1, maria1b, rendimiento1, 1b, admin1, admin2, maria2): corriendo; actualizo esta línea al terminar
smoke_friccion.sh (levantar.sh 21a7a7e)          → ==> OK · telemetría + alias session/state + by-cuit protegido
pantalla_excel1.js / pantalla_maria1b.js / pantalla_maria1c.js (con un PDF) → OK / OK / OK
ataque_aislamiento.sh                            → MARIA.TXT de Ana generado · Bloqueado: 22 · Fugas: 0
```

### Comandos para vos

```bash
git fetch origin claude/dev1-tecnica && git checkout 21a7a7e
# 1) pruebas de la pieza: todas pasan
<venv>/bin/python -m pytest -q --no-cov tests/test_maria1b_controles.py tests/test_generar_maria_txt.py tests/test_maria_subitems.py tests/test_excel1_lectura.py
# 2) sabotajes: «sabotajes con falla: 0»
PY=<venv>/bin/python scripts/testing/sabotajes/maria1b.sh 21a7a7e
# 3) semáforo en el navegador: «OK: pantalla MARIA-1b» (en c0bae0e y en fcd2fb7, FALLA)
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh 21a7a7e 8080
BASE_URL=http://127.0.0.1:8080 node scripts/testing/pantalla_maria1b.js <cualquier .xlsx>
```

## Decisiones

- **D22 — `/generate_maria_export` tampoco limpia los textos.** Por
  ejemplo, `exportador_nombre="ACME\r\nCDDTINCOTE=EXW"` mete una segunda
  línea. Sólo la llama la pantalla vieja (`static/app.js:3328`).
  Opciones: (a) aplicarle la misma limpieza en una pieza chica; (b)
  borrarla junto con la pantalla vieja.
  **Recomiendo (a)** si la exportación está en el roadmap; si no, (b).

## Qué no corrí y riesgos

- **Monedas en código numérico** («060» para el euro en la tabla de AFIP):
  hoy frenan, porque piden 3 letras. No pude confirmar si MARIA las usa. La
  pantalla ofrece sólo códigos de letras.
- Al generar, la pantalla todavía manda «XX» cuando falta el origen. Sigue
  frenando, pero el error dice «Origen no reconocido 'XX'» en vez de «Falta
  el origen». Es cosmético.
- Un CUIT que se tipea en la revisión no vuelve a la ficha del cliente: hay
  que tipearlo en cada operación de un cliente guardado sin CUIT.
- La pantalla vieja (`app.js`) no manda el sufijo SBT, así que ya daba 400
  siempre. Sigue igual.

## Sigo con

PUNTA-A-PUNTA-1 apenas esté en el canal.

Última vuelta: 2026-10-07
Contexto: ~95 %. Emi: hace falta el `/compact` de esta sesión antes de la
próxima pieza.

`/compact conservar: Dev 1 de CDI, rama claude/dev1-tecnica. EXCEL-1
aceptada (7b119b6). MARIA-1b entregada sobre 21a7a7e: controles en
proyecto_maria/core/controles_maria.py (usados en /generate_maria y
/api/validate/smart), semáforo con avisos del Excel y Descartar,
tests/test_maria1b_controles.py, scripts/testing/sabotajes/maria1b.sh,
scripts/testing/pantalla_maria1b.js. D21 (nomenclador 2018) espera a Emi; D22
(/generate_maria_export sin limpiar) abierta. Sigue PUNTA-A-PUNTA-1. Entorno:
PM_DIR=/tmp/cdi-dev1, levantar.sh <SHA> <puerto>, venv /tmp/cdi-dev1/venv y
venv-limpio; rutina de la PM trig_01TvMmGfSLDfbcJrf66ZZ7YK.`
