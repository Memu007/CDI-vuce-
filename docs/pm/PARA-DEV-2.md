# PM → Dev 2

Este archivo es de la PM principal (en CDI no hay PM visual). Vos lo leés y
contestás en `PARA-PM-2.md`.

## Cómo trabajás

`AGENTS.md`, `CLAUDE.md`, `docs/pm/ONBOARDING-DEV.md` y los comandos
`/entregar` y `/respondio`. No se copian acá.

**Tu rama: `claude/dev2-maria`**, creada desde la de la PM
(`claude/practical-shannon-szpwkn`). Antes de cada tarea traés la de la PM con
`merge`. Nunca `main`.

Sos la Dev de la **cola MARIA**: el archivo MARIA.TXT, el lector de facturas
y sus pantallas. La Dev 1 trabaja en `claude/dev1-tecnica` (lectura de PDF, Excel y controles); no
tocás su canal ni su rama.

Herramientas: todas menos el consejero; tu sesión y tus subagentes hasta
esfuerzo alto, nunca Fable (`ONBOARDING-DEV.md`, «Rol»).

**Tu PM es la PM principal.** Ella te despierta con `fire_trigger` de tu
rutina; vos la despertás con el de la suya al entregar o al dejar una D que te
frena (donde `/entregar` dice «PM visual», en CDI es la PM principal). Los ids
están en `NOW.md`, «Quién hace qué».

**Regla del archivo MARIA** (límite que no se negocia): ningún cambio en lo
que sale en el TXT sin prueba (la ley, un archivo real o la respuesta del
despachante). Los dos archivos reales anonimizados
(`tests/fixtures/maria_golden_anon.TXT` y `maria_golden_subitems_anon.TXT`)
tienen que seguir saliendo idénticos, salvo que la tarea diga otra cosa.

## Último veredicto

**MARIA-4 devuelta** (2026-10-07, sobre `6149ef3`). La PM reprodujo el rojo
antes (`30 failed`), la focal con los archivos reales (`127 passed`) y la
suite (`837 passed, 102 skipped`). Su subagente Sonnet alto: lo central se
sostiene (valores raros rechazados, 2025 idéntico byte a byte, 2026 sin
diferencias en los cuatro campos, sin fugas entre usuarios ni clientes).
Detalle en `REPRODUCCION-MARIA-4-2026-10-07.md`.

**Devolución, tres puntos:**
1. **Estado contra origen.** Un estado «argentino» (1, 3, 5) con origen
   extranjero, o «importado» (2, 4, 6) con origen argentino, no se genera:
   400 con un mensaje claro, como el del argentino sin estado. En la pantalla,
   si el origen cambia entre argentino y extranjero, el estado elegido se
   vuelve a pedir (hoy queda `['CN','3']`).
2. **Pantalla vieja:** muestra los `warnings` y `supuestos` que devuelve
   `/generate_maria`, como pedía la tarea («genera con los valores por defecto
   y su aviso»).
3. **`origen` y `pais_origen`:** el generador y los supuestos los leen en el
   mismo orden (hoy uno usa `pais_origen or origen` y el otro al revés).

Rojo antes y verde después en cada punto; suite completa en verde.

**Tu D11: (a).** Tu supuesto del banco propuesto que va al TXT si nadie lo
toca, con el aviso en pantalla: aceptado.

**Antes:** MARIA-1a, 2b y 1c aceptadas. Nada se integra en la rama de PM
hasta después del ensayo.

## Respuestas a tus D (2026-10-07, 05:30 UTC)

- **D5: (a), como MARIA-1c** (abajo), antes de MARIA-4.
- **D6: a la Dev 1, en MARIA-1b.**
- **D7: (a).** Se mide con facturas reales cuando Emi pruebe.
- **D8: (a), dejarlo.** Lo mismo decidió la Dev 1 con su lectura lenta (D11).

## Respuestas a tus D (2026-10-07, 06:10 UTC)

- **D9: (a), hecho por la PM** en `docs/pm/herramientas/levantar.sh`: las
  novedades de ARCA apuntan a un puerto local cerrado.
- **D10:** tenés razón. MARIA-4 queda escrita abajo.

## Tarea activa — MARIA-4: lo que decide el despachante

Asignada el 2026-10-07. Cambia lo que sale en el TXT. Hoy el generador fija
`CARTUSO=3` (`core/maria_generator.py:618`), `IVAADICIONAL1=IVAAD1` (`:650`) y
`ARDIG-CUIT-PSAD=PSAD06` (`:459`), y no emite `BANCOSARGENTINA`.

**Base:** tu rama (con MARIA-1a, 2b y 1c).

**Alcance, campo por campo, con su prueba:**

| Campo | Qué hace CDI | Por defecto | Prueba |
|---|---|---|---|
| `CARTUSO` (estado de la mercadería), por producto | Se elige entre los seis estados, con los nombres del despachante: nuevo sin uso argentino, nuevo sin uso importado, sin uso argentino, sin uso importado, usado argentino (incl. reacondicionado), usado importado (incl. reacondicionado). Códigos 1 a 6 en ese orden | Origen extranjero: 2 (nuevo sin uso importado). Origen argentino: no hay; se pide elegir | Respuesta 1 (21:20); el archivo de 2026 trae 2 con origen China y el de 2025 trae 3 con origen Argentina. El orden → código lo confirma la prueba en su Kit: dejalo en un solo lugar, con esta nota |
| `IVAADICIONAL1`, por operación, con cambio por producto | «Reventa» (`NO_VALIDA`) o «uso particular» (`IVAAD1`) | Reventa (`NO_VALIDA`) | Respuesta 2 (21:34) y el archivo de 2026. Si hay reducción o exclusión: un aviso de que se elige en «Ventajas» del Kit (22:12); **no va en el TXT** |
| `BANCOSARGENTINA`, por operación | El cliente elige el banco en cada operación; CDI propone el último que usó ese cliente. Se carga el código de entidad del BCRA (3 dígitos) | El último del cliente; si no hay, vacío: la línea no se emite (como en el archivo de 2025) y hay aviso | Respuestas 4 (21:35 y 21:40) y el archivo de 2026 (`191`). Si querés mostrar el nombre del banco, sólo con una tabla de fuente oficial citada; si no, sólo el código |
| `ARDIG-CUIT-PSAD`, por operación | Modoc (`PSAD06`) o Lakaut (`PSAD01`); CDI propone la última que usó ese usuario | La última usada; si no hay, Modoc (`PSAD06`, lo de hoy), a la vista en la pantalla | Respuestas 5 (21:42 y 22:15) y los dos archivos reales |

**Pantalla:** en la v2, donde se revisa antes de generar: banco, empresa de
digitalización y reventa o uso particular a nivel operación; estado (y el
cambio de IVA) por producto. Lo que se usó por defecto entra en los
«supuestos» que ya se muestran. La pantalla vieja (v1) sólo tiene que no
romperse: genera con los valores por defecto y su aviso.

**Dónde se guarda:** con la operación. Si hace falta una columna nueva en la
base, dejá una D antes de tocarla.

**Criterios:**
1. **Los dos archivos reales salen idénticos** cargando sus valores: 2025 con
   estado 3, uso particular, sin banco y `PSAD06`; 2026 con estado 2,
   reventa, banco `191` y `PSAD01`.
2. **Con los valores por defecto el TXT cambia a propósito:** `CARTUSO=2` con
   origen extranjero e `IVAADICIONAL1=NO_VALIDA`. Una prueba lo fija y el
   CHANGELOG lo dice.
3. Origen argentino sin estado elegido, o sin banco: aviso antes de generar.
   No se inventa ninguno de los dos.
4. Rojo antes y verde después por campo; sabotajes que devuelvan cada valor
   fijo de hoy. Suite completa en verde. Comprobación de pantalla con captura.

**Fuera de alcance:** procedencia, gastos FOB y avisos (MARIA-3); peso
(MARIA-5); identificadores y sufijos (MARIA-6); las ventajas del Kit.

**Después:** MARIA-3 y MARIA-5, en ese orden; MARIA-6 cuando lleguen los
archivos reales del despachante.

**Datos nuevos del despachante para MARIA-4** (2026-10-06, 22:12 y 22:15;
detalle en `PREGUNTAS-DESPACHANTE.md`):
- **Empresa de digitalización:** se elige en cada operación, como el banco
  (CDI propone la última usada). Modoc = `PSAD06`, Lakaut = `PSAD01`.
- **Reducción o exclusión del IVA adicional:** es una «ventaja» que el
  despachante elige en el Kit (`IVAADREDUCCION`). No va en el TXT (ningún
  archivo real trae ventajas): sólo un aviso de que se elige ahí.
