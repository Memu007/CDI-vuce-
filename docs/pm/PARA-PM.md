# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## NAVEGADOR: las 31 pantallas abren el navegador con `chromium.launch()`

| qué | SHA |
|---|---|
| base (informe de EXCEL2D-RELOJ, todavía en tu revisión) | `25e13c44` |
| arnés | `740eac45` |
| informe | el commit `docs:` que trae este archivo |

**Resultado.** Las tres puertas en verde. No toqué producto (`producto +0/−0`)
ni nada de MARIA.

**Forma elegida: `chromium.launch()`, sin argumentos.** Es la que ya usaban
28 de las 31 pantallas, y toma el Chromium que trae el Playwright instalado.
`borrador1`, `cliente1` y `destino1` pasan a usarla. Como ya ninguna pantalla
lee `CHROMIUM`, lo saqué de `correr_pantallas.sh`: del comentario de `:10`,
de `:24` y de `:56`. También lo saqué del uso documentado en
`sabotajes/cliente1.sh:5`, que nombraba la variable pero no la leía.

**Nada para decidir.** Un supuesto reversible: quien tenga otro Playwright
que no encuentre su navegador ya no puede apuntarlo con `CHROMIUM`. Es lo
mismo que ya pasaba con las otras 28 pantallas.

D229 (fuga de hilos del arnés, informe de EXCEL2D-RELOJ en `25e13c44`) sigue
abierta.

### Comandos para reproducir

1. **Una sola forma.** Tiene que dar `31 chromium.launch()`, en una sola
   línea:
   ```bash
   grep -ho 'chromium.launch([^;]*' scripts/testing/*.js | sort | uniq -c
   ```
2. **Nadie lee `CHROMIUM`.** Tiene que dar vacío:
   ```bash
   grep -rn CHROMIUM scripts/
   ```
3. **Las tres pantallas.** Tiene que dar `resumen: 3 verdes, 0 rojas`:
   ```bash
   SOLO="borrador1 cliente1 destino1" PY=<python del venv> scripts/testing/correr_pantallas.sh 740eac45
   ```
4. **Los sabotajes de `cliente1`.** Tiene que dar `sabotajes sin rojo: 0`:
   ```bash
   PY=<python del venv> scripts/testing/sabotajes/cliente1.sh 740eac45 | tail -1
   ```

### Puertas (corridas sobre `740eac45`)

| puerta | salida |
|---|---|
| `grep` en la base `25e13c44` | `28 chromium.launch()` · `1 chromium.launch({ executablePath: '/opt/pw-browsers/chromium' })` · `2 chromium.launch({ executablePath: process.env.CHROMIUM \|\| '/opt/pw-browsers/chromium' })` |
| `grep` en `740eac45` | `31 chromium.launch()` |
| `git grep -n CHROMIUM 740eac45 -- scripts/` | 0 líneas |
| `correr_pantallas.sh` con las tres | `verde borrador1 rc=0 … ok: el arranque no saca de Clientes y recupera si no fue a ninguna pantalla` · `verde cliente1 rc=0 … PANTALLA CLIENTE-1 OK (con CLIENTE-1b y 1c)` · `verde destino1 rc=0 … OK: pantalla DESTINO-1` · `resumen: 3 verdes, 0 rojas` · rc=0 |
| `sabotajes/cliente1.sh 740eac45` | 34 `ROJO` · `sabotajes sin rojo: 0` · rc=0 (11:02:53 → 11:06:58) |

`chequeo-6 25e13c44 740eac45` (rc=0, entero):
```
chequeo-6 25e13c44..740eac45: avisos para mirar, no un veredicto
producto +0/−0
arnés +6/−7
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

### No corrido

- Adversarios y `/code-review`, porque sigue vigente «sin adversarios».
- Las otras 28 pantallas: no las toqué.
- `pytest`: el cambio es sólo en JS y bash de pantallas, que pytest no
  ejecuta.

### Archivos de producto tocados

Ninguno.

/compact conservar: Dev 1 técnica, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica (nunca main); PM session_01B7FVQspcEHF7PqNv797wNM. Entregué EXCEL2D-RELOJ (25e13c44, D229 abierta) y NAVEGADOR (arnés 740eac45). No hay pieza siguiente marcada. Próxima D: D230. Sin adversarios. Nada se publica sin el «dale» de Emi para el SHA. Sin secretos.
