# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ESTUDIO-1: entregada

**Resultado:** los estudios son de la cuenta. Se cargan en «Mi perfil», «Mis
estudios», y se eligen en la operación, con el último usado o el único ya
puesto. Su CUIT va al CDDTAGR. Sin estudio sigue el CUIT del perfil: no hay
migración ni se copia nada. Otra cuenta no ve, no borra y no usa un estudio
ajeno; si lo intenta da 404 o 400 y no cae al perfil. El error que agregaste
cuando falta el CUIT (`1fa0b6e`) ahora dice que se elige en la operación o
se carga en «Mis estudios».

**Lo que decidís:** D23, abajo. Siguen abiertas D20, D21 y D22 de EXCEL-3d:
están en el informe `470fc48`, que reemplazo acá. El resumen va al final.

### Decisiones

**D23. Generar con el CUIT del perfil no cuenta como «último usado».**
Pasa así: alguien despacha con su perfil, carga un estudio y lo usa una vez.
Desde ahí ese estudio queda puesto en cada operación nueva, aunque después
genere varias veces con el perfil. El selector lo muestra con su CUIT antes
de generar, pero quien no mira sale con el CDDTAGR del estudio. Lo encontró
el adversario Opus alto y lo reproduje: tres TXT con el perfil, y la API
sigue preseleccionando el estudio.
- (a) Dejarlo así. «El último usado» cuenta sólo estudios, como dice la
  tarea al pie de la letra.
- (b) Anotar también cuándo se generó con el perfil, y preseleccionar lo
  último de las dos cosas. No alcanza con una columna nueva en `users`:
  `create_all` no agrega columnas a tablas que ya existen. Va en una tabla
  chica aparte, que sí se crea sola. Es una pieza chica después de
  CLIENTE-1c.
- **Recomiendo (b).** Un CDDTAGR equivocado se descubre recién en la aduana,
  y la preselección existe para que la persona no tenga que mirar.

### SHAs

| Commit | Qué es |
|---|---|
| 609ec52 | producto: tabla `estudios`, API, selector y «Mis estudios» |
| 6d4cc89 | pruebas: casos, pantalla y sabotajes |
| 8bbfbe6 | producto: lo confirmado de la autorrevisión |
| c992715 | pruebas: el rojo de esa autorrevisión y sus sabotajes |
| 7de44b7 | después vino EXCEL-3d; las puertas corrieron sobre este SHA, que ya contiene ESTUDIO-1 |
| 5468581 | merge de tu rama; los sabotajes de ESTUDIO-1 corrieron sobre este SHA |

`git diff --stat 7de44b7 5468581` muestra sólo `CHANGELOG.md`, `NOW.md` y
este archivo. Por eso las puertas sobre 7de44b7 valen para el código que se
entrega.

**Archivos de producto:**
- `proyecto_maria/database/models.py`
- `proyecto_maria/main.py`
- `proyecto_maria/static/v2/screens/estudios.js` (nuevo)
- `proyecto_maria/static/v2/screens/finalize.js`
- `proyecto_maria/templates/dashboard_v2.html`

No toqué `maria_generator.py`, `controles_maria.py` ni `despachante.js`.

### Hallazgos de la autorrevisión

| Quién | Hallazgo | Qué hice |
|---|---|---|
| `/code-review high` y Opus alto | el CUIT del estudio no controlaba el verificador | `cuit_valido` en el alta, con prueba y sabotaje. Los CUIT de prueba son sintéticos y tienen el verificador válido |
| Opus alto (reproducido con Playwright) y `/code-review` | generar antes de que llegue la lista mandaba el CUIT del perfil | generar espera `CDI.estudios.listo()`, con prueba de pantalla y sabotaje |
| `/code-review` | lo elegido en una operación seguía en la siguiente | cada operación vuelve a la preselección, con prueba y sabotaje |
| `/code-review` | un alta o un borrado no refrescaba los avisos | se vuelven a pedir, con prueba y sabotaje |
| `/code-review` | sin perfil, el hint de error prometía el perfil | dice que sin CUIT no se genera, con prueba y sabotaje |
| `/code-review` | `renderPerfil` sin guardia de orden | ahora tiene una secuencia propia |
| `/code-review` | SELECT de duplicado antes del UNIQUE | lo saqué: lo frena el UNIQUE, también con dos altas a la vez |
| Opus alto | un nombre con un surrogate suelto daba 500 en Postgres | ahora es 400, con prueba y sabotaje |
| Opus alto | el perfil no cuenta como «último usado» | **D23** |
| `/code-review` | el rótulo «CUIT de mi perfil» no coincide si la operación trae su propio `cuit_agr` | descartado: ninguna pantalla carga `op.cuit_agr` (grep en `static/`), así que siempre va el del perfil |
| `/code-review` | el texto del error vive en dos constantes y se reemplaza comparando cadenas | se queda: la otra copia está en `maria_generator.py`, que no toco. Si el generador cambia su texto, la comparación deja de coincidir y `test_sin_estudio_ni_perfil_el_error_dice_donde_cargarlo` pasa a rojo (pide «estudio» y «Mi perfil») |
| `/code-review` | la consulta por dueño está repetida y el filtro de caracteres no reutiliza `controles_maria` | se queda: es estilo, y `controles_maria.py` no se toca |
| Opus alto | faltan casos para el `IntegrityError` concurrente, el rollback del uso y el `estudio_id` con espacios | riesgo bajo, abajo. Opus los probó y el código responde bien: 8 altas a la vez en Postgres dieron 200 y siete 409 |
| `/security-review` (sobre 609ec52^..c992715) | nada con confianza alta | todos los endpoints piden `get_current_user` y filtran por `owner_username`; ajeno o inexistente da 404 o 400; los nombres se muestran con `textContent`; `create_all` crea la tabla en Postgres (Opus la creó en un Postgres 16 propio) |

### Puertas

| Puerta | SHA | Salida |
|---|---|---|
| Suite completa | 7de44b7 | `2469 passed, 102 skipped, 2 xfailed, 25 warnings in 288.41s (0:04:48)`, rc=0 |
| compileall | 7de44b7 | rc=0 |
| smoke | 7de44b7 | «==> OK · telemetría + alias session/state + by-cuit protegido», rc=0 |
| ataque | 7de44b7 | «✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.», `Bloqueado: 22 · Fugas: 0` |
| `tests/test_estudio1.py` | 5468581 | `26 passed, 3 warnings in 21.94s` |
| `sabotajes/estudio1.sh` | 5468581 | 37 ROJO, «sabotajes sin rojo: 0», salida 0. Antes de sabotear, la API y la pantalla pasaron en verde |

### Lo que no se corrió

- `ataque_aislamiento.sh` no cubre estudios: sólo cubre clientes y
  descargas. El aislamiento de estudios lo prueba
  `test_otro_usuario_no_ve_ni_borra_ni_usa_los_estudios_ajenos`.
- Postgres: lo probó sólo el adversario Opus, sobre 6d4cc89, no sobre el SHA
  final.
- La e2e completa con un TXT real no se corrió. Las pruebas usan CUIT
  sintéticos.

### Riesgos

- **D23:** el CDDTAGR por defecto puede ser un estudio cuando la persona
  despacha con el perfil.
- **Bajo:** sin prueba para el 409 de dos altas simultáneas, el rollback si
  falla anotar el uso y el `estudio_id` con espacios.

### Comandos

```bash
git fetch origin claude/dev-tecnica && git checkout <sha>   # 5468581 o el SHA que subo con este informe
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov --timeout=120 tests/test_estudio1.py   # 26 passed
PY=$(command -v python) PUERTO=8873 scripts/testing/sabotajes/estudio1.sh   # 37 ROJO, «sabotajes sin rojo: 0»
```

## Pendiente de EXCEL-3d (informe completo en `470fc48`)

- **D20:** la cabecera de descuento sin precio, con copias que sí tienen
  precio. Recomiendo (a), dejarlo.
- **D21:** los plurales «Fletes», «Seguros» y «Bank fee». Recomiendo (b),
  una pieza chica aparte.
- **D22:** la fila con origen propio que empieza como un cargo. Recomiendo
  (b), un aviso, junto con D21.

## Sigo con

CLIENTE-1c: D15 (b) y D16 (b) con `_fecha_inic_activ_de_api`, el error de
`--base` sin la clave y el dígito de ancho completo. Después, GUARDAR-2.

/compact conservar: Soy la Dev técnica (Dev 1) de CDI, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica (nunca main), rutina trig_011UpBfwEu9TUzoNUrviqoP5 min 15; aviso a la PM principal session_01B7FVQspcEHF7PqNv797wNM con send_message priority next empezando «Dev técnica:». EXCEL-3d entregada (informe 470fc48) y ESTUDIO-1 entregada (producto 609ec52+8bbfbe6, pruebas 6d4cc89+c992715, puertas sobre 7de44b7, sabotajes 37 ROJO sobre 5468581). Abiertas para la PM: D20 (a), D21 (b), D22 (b), D23 (perfil como último usado, recomiendo b con tabla aparte). Próxima D: D24. Sigo con CLIENTE-1c (D15 b y D16 b con _fecha_inic_activ_de_api en main.py ~6934 y ~6303, error de --base sin la clave, dígito de ancho completo, sabotaje por lugar) y después GUARDAR-2 (desde 2d930c5 en claude/dev1-tecnica + punto 2 de «Qué sigue» de CIERRE-RETOMA-2026-10-24.md). Reglas de Emi: sólo me piden la PM o Emi; nada se publica sin su «dale» para el SHA; nunca main; sin secretos ni datos reales (la proforma del 24/10 no entra); no tocar maria_generator.py, controles_maria.py, despachante.js ni el canal/rama de la Dev MARIA; subagentes hasta alto, sin Fable.
