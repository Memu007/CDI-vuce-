# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## REGISTRO-GUIONES: todo guion de pantalla que registra una cuenta se corta si el registro no da 2xx

| | SHA |
|---|---|
| Base | `08ae96549c4704b331566ff59bf4d35721472978` |
| Arnés | `b832fc2254ef408b4567da6272c0b223f00d86b9` (`test(pantalla): …`) |
| Informe | el commit `docs:` que trae este archivo |

**Resultado:** el chequeo está una sola vez, en `scripts/testing/_registrar.js`, y los 28 `pantalla_*.js` que registran una cuenta lo usan. Producto +0/−0. Sobre b832fc2 dan verde 24 de los 28 guiones tocados; los otros 4 (`maria3`, `maria4`, `maria5`, `subitems1`) **dan el mismo rojo en la base 08ae9654**: no son de esta pieza (D209). Una puerta no se cumple: `maria4` corre en un guion de sabotaje y su base no da verde.

## Decisiones

**D209. Quién arregla `maria3`, `maria4`, `maria5` y `subitems1`, rojos en la base desde MARIA-7 (`67d56889`, 2026-10-24).**
- (a) **La Dev MARIA** (recomendada). La exigencia del CUIT del despachante es su comportamiento, y es ella quien decide si el guion carga el CUIT en el perfil o elige un estudio en la operación.
- (b) Yo, en una pieza aparte, después de que ella diga cuál de los dos caminos usa el guion.
- Mientras tanto la puerta «base verde de `maria4`» no se puede cumplir: el sabotaje que corre `maria4` no distingue nada hasta que el guion vuelva a verde.

Nada más para decidir. Supuesto reversible: el ayudante devuelve la respuesta del registro (`return r`) aunque hoy ningún guion la usa; si molesta, se saca en una línea.

## Qué cambió

```js
// scripts/testing/_registrar.js
module.exports = async (request, base, opciones) => {
  const r = await request.post(base + '/auth/register', opciones);
  if (!r.ok()) throw new Error('registro: ' + r.status() + ' ' + await r.text());
  return r;
};
```

Cada guion hace `await registrarCuenta(X.request, base, {...})`; el `throw` cae en el `catch` del guion, que termina en `FALLA: registro: <status> <cuerpo>` con rc=1. 29 archivos, +64/−45.

## Medición: antes 13, después 0

Comando (registros con `request.post` directo que no miran `.ok()`/`status()` en las 6 líneas siguientes):

```bash
git grep -n -A6 "request.post(base + '/auth/register'" <SHA> -- 'scripts/testing/pantalla_*.js' \
  | awk '/auth\/register/{if(f)print f; f=$0; next} /\.ok\(\)|status\(\)/{f=""} END{if(f)print f}'
```

- **08ae9654: 13.** `catalogo_ncm1:15`, `destino1:21`, `excel1:15`, `maria1b:20`, `maria1c:16`, `maria3:16`, `maria4:15`, `maria5:17`, `maria7:17`, `maria9:23`, `separadores1:24`, `subitems1:26`, `sufijos1:28`.
- **b832fc2: 0** en `pantalla_*.js`. El único `post` a `/auth/register` de los guiones de pantalla queda en `_registrar.js`.
- **Tus 15** son estos 13 más dos que no son el defecto: `despacho1a` (la llamada ocupa varias líneas y chequea el status cuatro líneas más abajo) y `org1b` (registra por el formulario y espera el 400 a propósito). `despacho1a` igual pasó al ayudante; `org1b` no se tocó.

## Rojo con y sin el chequeo (una vez, `excel1`, con un proxy que contesta 429 a `/auth/register`)

| | rc | Salida |
|---|---|---|
| b832fc2 (con chequeo) | 1 | `FALLA: registro: 429 {"detail":"Demasiados registros desde esta IP (proxy de prueba)"}` |
| b832fc2 con el `throw` neutralizado | 1 | `FALLA: page.waitForSelector: Timeout 30000ms exceeded. … waiting for locator('#uploadFileInput')`, sin mencionar el registro |
| b832fc2 sin proxy | 0 | `OK: pantalla EXCEL-1` |

Sin el chequeo el guion falla 30 s después y lejos de la causa; con el chequeo falla en el registro con el status y el cuerpo.

## Cada guion tocado sobre b832fc2

Cada uno con su servidor uvicorn y una base sqlite nueva (el límite de `/auth/register` es 5 por hora por IP, `main.py:3420`).

| Resultado | Guiones |
|---|---|
| rc=0 (24) | `borrador1`, `catalogo_ncm1`, `cliente1`, `cobro_corte1`, `cobro_mp1`, `cobro_mp1_v2`, `csrf1`*, `csrf2`, `csrf3`, `despacho1a`, `despacho1b`, `destino1`, `estudio1`, `estudio1b`, `excel1`, `maria1b`, `maria1c`, `maria7`, `maria9`, `orden1`, `separadores1`, `sesion1`, `sufijos1`, `validacion1` |
| rc=1, igual en 08ae9654 | `maria3`, `maria4`, `maria5`, `subitems1` |

\* `csrf1` necesita `CSRF_ENFORCE=true`, como dice su cabecera: con `ENVIRONMENT=development` el token no se exige (`main.py:2049-2052`). Con la variable da rc=0 en la base y en b832fc2.

Los rojos de la base, de a uno, en 08ae9654:

| Guion | Salida |
|---|---|
| `maria5`, `subitems1` | `FALLA: no se generó el TXT: {"detail":"Falta el CUIT del despachante (CDDTAGR): elegí el estudio en la operación o cargá uno en «Mi perfil», «Mis estudios». Sin él no se genera el TXT."}` |
| `maria3` | último OK «al cargar el banco el aviso se actualiza»; después `TimeoutError` esperando `POST /generate_maria`. El log del servidor no tiene ningún `POST /generate_maria`. |
| `maria4` | `element is not enabled` al hacer click en «Generar» |

Causa: los cuatro también dan rojo en `273c153e` (antes de ESTUDIO-1); en ese SHA `maria5` dice «Falta el CUIT del despachante (CDDTAGR): cargalo en «Mi perfil», campo «Mi CUIT (despachante)»…», el texto de MARIA-7. Para `maria3` y `maria4` **no está confirmado** que el botón deshabilitado venga del CUIT: `finalize.js:606` deshabilita «Generar» cuando la validación trae errores, y no verifiqué qué error trae en ese guion.

**Base de los guiones que corre un sabotaje**, en 08ae9654: `maria1c` (con `tests/test_factura.pdf`), `maria7` y `maria9` rc=0; `maria4` rc=1 (arriba).

## chequeo-6

```
chequeo-6 08ae9654..b832fc2: avisos para mirar, no un veredicto
producto +0/−0
arnés +64/−45
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Lo que no se corrió y ajustes del entorno

- **No corrí** los guiones de sabotaje (`maria1c`, `4`, `7`, `9`) sobre b832fc2: la tarea pide la base de sus guiones en verde, no el sabotaje. Tampoco la suite pytest: no cambió producto ni tests de pytest.
- **Sin adversarios**, como dice la tarea. Sin `/code-review`.
- **Chromium:** los guiones apuntan a `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`; en este contenedor el binario está en `/opt/pw-browsers/chromium`, así que agregué un enlace fuera del repo. No toqué los guiones por eso.
- `tests/test_conexiones1.py` sigue sin seguimiento a propósito (su copia está en `scripts/testing/conexiones1_tests.diff`).

## Archivos tocados

Sólo arnés: `scripts/testing/_registrar.js` (nuevo) y 28 `scripts/testing/pantalla_*.js`. Ningún archivo de producto.

## Para reproducir

```bash
git diff --stat 08ae9654 b832fc2                         # 29 files changed, 64 insertions(+), 45 deletions(-)
python3 docs/pm/herramientas/chequeo-6.py 08ae9654 b832fc2  # producto +0/−0, avisos: 0
git grep -n "auth/register" b832fc2 -- 'scripts/testing/pantalla_*.js'   # sólo org1b (formulario, espera 400)
# un guion: servidor uvicorn local con base sqlite nueva, después
BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_excel1.js <xlsx>   # OK: pantalla EXCEL-1
```

/compact conservar: Dev 1 técnica, rama claude/dev-tecnica; entregué REGISTRO-GUIONES (b832fc2 + informe); D209 (rojos de maria3/4/5 y subitems1 desde MARIA-7, recomiendo Dev MARIA); tests/test_conexiones1.py sin seguimiento (su copia está en el parche); espero veredicto.
