# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CLIENTE-1c: entregada

| Qué | SHA |
|---|---|
| Entrega (código, pruebas y puertas) | `4452b22` |
| Merge de tu rama (`adfe707`), sólo `docs/pm/` y CHANGELOG | `df07dda` |
| Informe | este commit |

Tu diff de revisión: `git diff c820c74..4452b22`. El merge `df07dda` no cambia
código: `git diff --stat 4452b22 df07dda` toca sólo `docs/pm/`. En CHANGELOG
dejé mi lado; tu entrada de SEPARADORES-1b ya estaba en él, una sola vez.

**Resultado:**
- **D15 (b):** la operación copia a la ficha vacía sólo una fecha que pasa
  la regla del alta, guardada AAAA-MM-DD. La que no sirve, incluida la fecha
  con hora, no se copia, y la operación se guarda igual.
- **D16 (b):** la importación deja vacía la fecha que no sirve, y la vista
  previa avisa la fila («Fila N: la fecha de inicio «…» no es válida y no se
  importa»). El año sale siempre con cuatro cifras.
- **Dígito de ancho completo:** la ficha ya no tiene una regla propia. El
  servidor manda `fecha_inic_activ_sirve` con el criterio del generador
  (`fecha_inicio_actividad`), así que la pantalla y el TXT no se contradicen.
- **`--base` sin la clave:** el error del script nombra sólo host, puerto y
  base. También tapa lo que esté antes del último «@», partido en «:», «;» y
  «@», y los valores de la consulta (`?password=`), en crudo y codificados.
- **Tus dos condiciones:**
  - `test_guardar1::test_datos_largos_de_la_operacion_no_impiden_guardarla`
    pasa. La suite sobre `4452b22` da 0 failed.
  - Los 12 rojos de 402 tenían una causa propia: las 10 operaciones de
    `tests/test_cliente1c.py` gastaban el cupo de 15 de `test_user`. Lo
    arreglé en `2ff3262`, en las pruebas: `_contador` guarda y restaura
    `ops_used_this_period`. No deseleccioné nada ni toqué el tope.
  - **La CI de tu `ci.yml` no la vi correr**: corre cuando suba. La suite
    local completa, sin deseleccionar nada, dio 0 failed.

## Decisiones

**D25. La importación no sigue la regla del alta para el formato.**
«15/03/15» se guarda como 2015 y «01/01/50» como 2050. También pasan los
dígitos de ancho completo y DD-MM-AAAA. Son fechas válidas, pero el alta las
rechazaría.
- (a) Queda así: lo que el lector de la importación entiende se guarda.
- (b) La importación usa la regla del alta: el año de dos cifras y los
  formatos que el alta no acepta quedan vacíos, con el aviso de la fila.

Recomiendo **(b)**: hoy hay tres reglas de fecha distintas (alta, importación
y generador), y «01/01/50» da 2050 sin aviso. Es chico y va con su sabotaje.

## Supuesto reversible

- `test_guardar1`: la prueba que mandaba la fecha con hora ahora espera la
  ficha vacía, que es lo que dice D15 (b). Antes esperaba la fecha cortada.

## Hallazgos propios

| Hallazgo | Quién | Qué pasó |
|---|---|---|
| El chequeo de pantalla «sin fechas malas no hay aviso» no distinguía | yo | arreglado en `9a3cc75`, con el sabotaje «el aviso de las fechas aparece siempre» en `cliente1.sh` |
| Las operaciones de `test_cliente1c` gastaban el cupo compartido (los 12 rojos) | yo, tras tu corrección | arreglado en `2ff3262` |
| La clave con «@», «;» o en `?password=` salía en el error, y la clave «1» tapaba el host | adversario Opus, alto | rojo en `db1a18a`, arreglo en `1f698d2`, sabotajes en `4452b22` |

**Revisión:**
- Corrieron el adversario Opus alto y `/code-review high`.
- `/security-review` con subagentes **no se completó**: el subagente se cortó
  por el límite mensual de gasto de la API (429). Lo hice yo, inline, sobre
  `c820c74..4452b22`, y no encontré nada:
  - el aviso de la vista previa usa `textContent`, así que no hay XSS;
  - `save_client_operation` sigue buscando la ficha con
    `_get_owned_client(db, client_id, username)`;
  - la clave del script la cubren los casos de `test_cliente1b_script.py` y
    sus sabotajes.

  No es una revisión independiente.

## Riesgos (no los arreglé: fuera de la tarea)

| Riesgo | Severidad |
|---|---|
| Con una fecha mala ya guardada, la vista previa dice `fill_empty` y la confirmación da `skipped` | baja |
| `fechaDdMmAaaa` en la pantalla muestra «30/02/2015» tal cual | baja |
| Se acepta el año 0001 | baja |
| En el script, un error después del commit sale con rc 2, aunque ya guardó | baja |
| Con una fecha de puros espacios, el aviso dice «no es válida» | baja |
| Hay tres reglas de fecha distintas (ver D25) | media |
| Con la clave «1», el error de red muestra `[Errno ***]` | baja |
| El usuario de la base queda tapado en los errores del driver | baja (es a propósito) |

## Puertas sobre `4452b22`

| Puerta | Salida |
|---|---|
| Suite completa | `3135 passed, 102 skipped, 2 xfailed, 92 warnings in 373.22s (0:06:13)`, exit 0 |
| `python -m compileall -q proyecto_maria` | exit 0 |
| `cliente1c.sh` | 25 ROJO, «sabotajes sin rojo: 0», exit 0 |
| `cliente1.sh` (PUERTO=8852) | «sabotajes sin rojo: 0», exit 0 |
| `cliente1b.sh` | «sabotajes sin rojo: 0», exit 0 |
| `smoke_friccion.sh` (puerto 8861) | «==> OK · telemetría + alias session/state + by-cuit protegido», exit 0 |
| `ataque_aislamiento.sh` (PUERTO=8862) | «✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.», exit 0 |
| Las cuatro de clientes sobre `df07dda` | `104 passed in 13.68s` |

**No corrido:** la CI de GitHub (corre al subir) y `/security-review` con
subagentes (ver arriba).

## Archivos de producto

- `proyecto_maria/main.py`
- `proyecto_maria/services/migration_service.py`
- `proyecto_maria/static/v2/screens/clientes.js`
- `scripts/datos/clientes_fecha_inic_activ.py`
- `CHANGELOG.md`

## Para reproducir

```bash
git diff c820c74..4452b22 --stat     # la pieza
python -m pytest -q --no-cov tests/test_cliente1c.py tests/test_cliente1b_script.py tests/test_cliente1b.py tests/test_guardar1.py
                                      # 104 passed
bash scripts/testing/sabotajes/cliente1c.sh 4452b22
                                      # 25 ROJO, «sabotajes sin rojo: 0»
python -m pytest -q --no-cov --timeout=120
                                      # 0 failed, sin los 402
```

## Sigo con

ESTUDIO-1b. Después vienen EXCEL-3f y GUARDAR-2.

/compact conservar: Soy la Dev técnica (Dev 1) de CDI, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica (nunca main), rutina trig_011UpBfwEu9TUzoNUrviqoP5 min 15; aviso a la PM principal session_01B7FVQspcEHF7PqNv797wNM con send_message priority next empezando «Dev técnica:». CLIENTE-1c entregada en 4452b22 (base c820c74, merge de la PM df07dda), abierta D25 (importación con la regla del alta; recomiendo b). Próxima D: D26. Sigo con ESTUDIO-1b (D23 b tabla aparte, 400 para estudio_id "null"/"None"/"N/A"/espacios, nombre sin U+200B–200F/202A–202E/2066–2069 ni vacío; riesgos cuit_valido 00000000000 y estudio borrado durante la generación), EXCEL-3f (D21 b, D22 b, H4 con aviso, H5 opcional, más H1 descripción repetida a mano y H3 texto de contenedor como medida, de PARA-DEV.md) y GUARDAR-2 (desde 2d930c5 en claude/dev1-tecnica + punto 2 de «Qué sigue» de CIERRE-RETOMA-2026-10-24.md). Reglas de Emi: sólo me piden la PM o Emi; nada se publica sin su «dale» para el SHA; nunca main; sin secretos ni datos reales (la proforma del 24/10 no entra); no tocar maria_generator.py, controles_maria.py, despachante.js ni el canal/rama de la Dev MARIA; subagentes hasta alto, sin Fable.
