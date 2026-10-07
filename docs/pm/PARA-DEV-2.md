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

**MARIA-1a aceptada sobre `0a1775f` y MARIA-2b aceptada sobre `c3bef51`**
(2026-10-07). La PM reprodujo los rojos antes (`59 failed` y `12 failed`,
`assert 400 == 503`), las focales (`143 passed` con los archivos reales;
`84 passed`) y las suites (`777 passed, 102 skipped` y `791 passed, 102
skipped`). Su subagente Sonnet alto probó unos 300 países y los números
difíciles: ningún código ni valor equivocado; los dos archivos reales salen
idénticos. Confirmó tu D5 hasta el TXT (`MDDTFLE=0.00`, `MDDTASS=0.00`) y
encontró que la pantalla vieja (`static/app.js:3289`, `/dashboard?v=1`) repone
`cantidad || 1` y `origen || 'CN'`. Detalle en
`REPRODUCCION-MARIA-1a-2b-2026-10-07.md`.

**Todavía no se integran en la rama de PM:** el ensayo de mañana publica
exactamente lo que se atacó. Se integran después, y MARIA-1a no se publica sin
MARIA-1c. Seguí en tu rama.

## Respuestas a tus D (2026-10-07, 05:30 UTC)

- **D5: (a), como MARIA-1c** (abajo), antes de MARIA-4.
- **D6: a la Dev 1, en MARIA-1b.**
- **D7: (a).** Se mide con facturas reales cuando Emi pruebe.
- **D8: (a), dejarlo.** Lo mismo decidió la Dev 1 con su lectura lenta (D11).

## Tarea activa — MARIA-1c: lo que no se pudo leer se avisa

Asignada el 2026-10-07. Sale de tu D5 y de la revisión de la PM. Es chica.

**Base:** tu rama (con MARIA-1a y MARIA-2b).

**Alcance:**
1. Si el lector encontró un flete, un seguro u otro valor de la operación
   pero no lo pudo leer, lo marca, y la pantalla de subida lo nombra
   («No pudimos leer el flete: completalo»). Antes de generar, el aviso
   sigue a la vista. Un dato que no estaba en la factura no se marca.
2. La pantalla vieja (`static/app.js`, ~línea 3289) no repone cantidad 1 ni
   origen China: manda lo que hay, y el control de `/generate_maria` avisa.

**Fuera de alcance:** guardar la operación (D6, Dev 1) y los controles antes
de generar (MARIA-1b, Dev 1).

**Criterios:** rojo antes y verde después con flete `"1,500"` sin pista y
seguro `"350 USD/kg"` (hoy salen 0 sin aviso concreto) y con la pantalla vieja
mandando cantidad y origen vacíos. Los dos archivos reales salen idénticos.
Suite completa en verde.

## Respuestas a tus D (2026-10-07, 06:10 UTC)

- **MARIA-1c:** en revisión de la PM. Mientras, arrancá MARIA-4 (abajo).
- **D9: (a), hecho por la PM** en `docs/pm/herramientas/levantar.sh`: las
  novedades de ARCA apuntan a un puerto local cerrado.
- **D10:** tenés razón. MARIA-4 queda escrita abajo.

## Siguiente — MARIA-4: lo que decide el despachante

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
