# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## COBRO-CORTE-1, entregada en `75c6476` (informe en el commit de arriba)

Es la primera entrega de la pieza: el informe la cubre entera.

| SHA | qué |
|---|---|
| `a3e7e0c`, `0cf721a` | pruebas: cuándo se cuenta una operación y dónde se corta; la cancelada conserva `TRIAL_EXPIRED` |
| `10a1a9d` | producto: la operación se cuenta al generar su MARIA y se corta por la razón real |
| `704df60` | producto: la pantalla dice la razón del 402 y regenerar sin factura usa el mismo id |
| `76e9fd2` | pruebas: la pantalla y dos pedidos a la vez contra Postgres |
| `b2e4bcb`, `1d86c60`, `ec4699a`, `5e73f6b`, `427b08c` | pruebas: regenerar o guardar sin estar al día, guardar dos veces, estudio vencido, el conteo vence la cuenta, sin gastar el usuario compartido |
| `8b47d12` | CHANGELOG |
| `27e4594`, `3f3234d` | pruebas: `cobro_corte1.sh` y la pantalla espera el arranque |
| `4ae523c`, `4dd2d25` | producto: comentarios y docstrings sin historia, de una o dos líneas |
| `298db6c` | pruebas: regenerar lo ya contado también en la exportación |
| `3ac4dfa` | producto: guardar en otro cliente no le saca la operación al primero |
| `2afc90f` | pruebas: la misma factura en dos clientes; la cancelada con el tope |
| `1a7ee26` | producto: docstrings del guardado (sin cambio de comportamiento) |
| `75c6476` | pruebas: CUIT válido y nombre corto en el caso de dos clientes |

Base: `f54d8a9` (COBRO-MP-1). Las piezas de en medio (CSRF-1 a 3, COBRO-MP-1
vueltas 4 y 5) entraron por los merges y no son de esta entrega.

**Resultado.** Arregla C1, C5 y C6 de `AUDITORIA-2026-10-06.md` con D4 b, D5 a
y D6 a.

- **Corte por estado (C1, D5 a).** `require_billing_vigente` da 402 si la
  cuenta no está al día, antes de que la ruta llame a Gemini o escriba nada.
  Está en `process_operation`,
  `upload_pdf_public`, `generate_maria`, `generate_maria_export`,
  `migraciones/analizar` y `confirmar`, el guardado en cliente y
  `ncm/sugerir`. No mira el tope.
- **Se cuenta al generar (C5, D4 b).** Se cuenta la primera generación de cada
  `generated_file`. Regenerar el mismo id no cuenta y anota la huella del
  contenido; a la 11.ª huella distinta, 409 `MARIA_REGENERACIONES_AGOTADAS`.
  `finalize.js` regenera y guarda con ese id. Guardar en el cliente completa
  la operación ya contada si no tiene cliente o es de ese cliente; si no, se
  cuenta y se crea otra.
- **Con lock (C6, D6 a).** El conteo hace `FOR UPDATE` de usuario y
  organización, en ese orden, y un solo commit. Sin migración.
- **El tope, sólo donde se cuenta.** Con el tope lleno se valida y se baja lo
  ya contado; una operación nueva da 402.
- **El 402 dice la razón real**, con los `code` que ya lee la pantalla: impaga
  con MP, prueba vencida, cancelada, sin suscripción o tope. La pantalla
  muestra ese texto.
- Producto `+356/−147` (neto +209). Más de 20 netas porque el corte por
  estado, el conteo con lock y el 402 con su razón son lógica que no existía:
  no había nada que sacar o unificar.

### Decisiones

**D61. Guardar por error en el cliente equivocado cuesta una operación.**
Generar y guardar en A, y después guardar en B, cuenta dos (A conserva la
suya). Si después se corrige y se vuelve a guardar en A, no cuenta otra.

- (a) **Dejarlo así.** Guardar en otro cliente es otra operación para otro
  importador; no hay forma, sin más datos, de distinguir el error de la
  segunda operación de verdad.
- (b) Mover la operación a B si A no la modificó, o sumar un camino para
  reasignar o borrar que devuelva el conteo.

Recomiendo **(a)**: (b) agrega un camino que devuelve cupo, y eso se puede
usar para no pagar operaciones. Si hace falta, va en una pieza aparte con su
revisión de plata.

Supuestos reversibles:
- `SUBSCRIPTION_INACTIVE` es un código nuevo, para la cuenta sin suscripción
  (antes salía `PLAN_LIMIT_EXCEEDED`, que habla del tope). La v2 lo muestra
  con el título genérico.
- `TRIAL_EXPIRED` vale también para la suscripción vencida y la cancelada ya
  sin período; cambia el mensaje, no el código, porque la pantalla y las
  pruebas de prelaunch ya leen ese código.
- El atajo de testing (`ENVIRONMENT=testing` con ciertos usuarios), que ya
  salteaba el tope, ahora también saltea el conteo. En producción no aplica.
- `tests/conftest.py` (`427b08c`): al terminar, cada prueba le devuelve el
  cupo a `test_user` y retira las operaciones MARIA que creó. Sin eso, como
  generar ahora cuenta, otras pruebas daban 409 de regeneraciones agotadas y
  402 del tope.

### Puertas

| puerta | resultado |
|---|---|
| suite completa sobre `75c6476` | `4455 passed, 121 skipped, 3 xfailed`, 0 failed |
| `tests/test_cobro_corte1.py` sobre `75c6476` | 65 passed |
| sabotajes `cobro_corte1.sh` sobre `75c6476`, con Postgres 16 local | 44 ROJO (31 de pytest, 10 de la pantalla, 3 del lock), ninguno VERDE, ROTO ni ROJO?; «sabotajes con falla: 0», sale con 0 |
| concurrencia (`cobro_corte1_postgres.py`, Postgres 16 local) | sin sabotaje, «BASE  \| el lock en verde» (ninguna línea FALLA); con cada uno de los 3 sabotajes del lock, ROJO |
| `/code-review high` (Opus, alto) y adversario Sonnet alto, sobre `2afc90f` | 2 arreglados; el resto, en la tabla |
| `/security-review` (Sonnet, alto), sobre `298db6c..75c6476` | ninguno con confianza ≥ 8 |
| chequeo-6 | 1 aviso que queda, con su porqué (abajo) |

`smoke_friccion.sh` y `ataque_aislamiento.sh`: no corridos. La pieza no toca
permisos de clientes ni descargas; el primero queda para tu corrida antes de
publicar.

### Rojo antes

- **Pruebas de `75c6476` sobre el producto de la base** (`0cf721a`, igual a
  `f54d8a9` en producto): `60 failed, 5 passed`. Fallan todas las familias de
  estado × ruta (`assert 200 == 402`), conteo, tope, org, exportación,
  guardar dos veces, id largo y EXPORT. Pasan en la base:
  `test_la_suscripcion_dentro_de_la_gracia_genera`,
  `test_la_cancelada_genera_hasta_el_fin_del_periodo`,
  `test_guardar_sin_haber_generado_cuenta_una`,
  `test_guardar_una_operacion_nueva_con_el_tope_lleno_da_402` y
  `test_guardar_con_un_id_que_no_es_un_maria_no_lo_toma_como_archivo`: piden
  lo que la base ya hacía. Los cubren los sabotajes.
- Guardar en otro cliente: la prueba de `2afc90f` sobre el producto de
  `298db6c` daba `1 failed, 10 passed`.

### Sabotajes de `cobro_corte1.sh`, uno por regla

```
BASE  | en verde
ROJO  | process_operation no corta por estado: dice «FAILED tests/test_cobro_corte1.py::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[impaga-process_operation]»
ROJO  | upload_pdf no corta por estado: dice «FAILED tests/test_cobro_corte1.py::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[impaga-upload_pdf]»
ROJO  | generate_maria no corta por estado: dice «FAILED tests/test_cobro_corte1.py::test_regenerar_lo_ya_contado_con_la_cuenta_que_no_esta_al_dia_da_402[impaga-importacion]»
ROJO  | generate_maria_export no corta por estado: dice «FAILED tests/test_cobro_corte1.py::test_regenerar_lo_ya_contado_con_la_cuenta_que_no_esta_al_dia_da_402[impaga-exportacion]»
ROJO  | migraciones_analizar no corta por estado: dice «FAILED tests/test_cobro_corte1.py::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[impaga-migraciones_analizar]»
ROJO  | migraciones_confirmar no corta por estado: dice «FAILED tests/test_cobro_corte1.py::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[impaga-migraciones_confirmar]»
ROJO  | guardar en el cliente no corta por estado: dice «FAILED tests/test_cobro_corte1.py::test_guardar_lo_ya_generado_con_la_cuenta_que_no_esta_al_dia_da_402[impaga]»
ROJO  | ncm_sugerir no corta por estado: dice «FAILED tests/test_cobro_corte1.py::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[impaga-ncm_sugerir]»
ROJO  | la dependencia deja pasar la impaga: dice «FAILED tests/test_cobro_corte1.py::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[impaga-ncm_sugerir]»
ROJO  | el trial vencido no vence: dice «FAILED tests/test_cobro_corte1.py::test_el_estudio_con_la_prueba_vencida_no_genera_ni_gasta_gemini»
ROJO  | la suscripción vence sin gracia: dice «FAILED tests/test_cobro_corte1.py::test_la_suscripcion_dentro_de_la_gracia_genera»
ROJO  | la fecha sin zona no se toma como UTC: dice «FAILED tests/test_cobro_corte1.py::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[suscripcion_vencida-ncm_sugerir]»
ROJO  | el impago se avisa como vencido: dice «FAILED tests/test_cobro_corte1.py::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[impaga-ncm_sugerir]»
ROJO  | la prueba vencida se avisa como suscripción: dice «FAILED tests/test_cobro_corte1.py::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[prueba_vencida-ncm_sugerir]»
ROJO  | la cancelada no dice que canceló: dice «FAILED tests/test_cobro_corte1.py::test_una_cuenta_que_no_esta_al_dia_no_genera_ni_gasta_gemini[cancelada-ncm_sugerir]»
ROJO  | la cuenta sin suscripción se avisa como tope: dice «FAILED tests/test_cobro_corte1.py::test_el_aviso_de_la_cuenta_sin_suscripcion_no_habla_del_tope»
ROJO  | cada generación crea y cuenta otra operación: dice «FAILED tests/test_cobro_corte1.py::test_generar_cuenta_una_vez_por_id_y_crea_la_operacion»
ROJO  | generar no suma al contador: dice «FAILED tests/test_cobro_corte1.py::test_generar_cuenta_una_vez_por_id_y_crea_la_operacion»
ROJO  | regenerar el mismo contenido gasta una de las 10: dice «FAILED tests/test_cobro_corte1.py::test_el_mismo_id_no_pasa_de_10_contenidos_distintos»
ROJO  | el mismo id pasa de 10 contenidos: dice «FAILED tests/test_cobro_corte1.py::test_el_mismo_id_no_pasa_de_10_contenidos_distintos»
ROJO  | se escribe el archivo antes de contar: dice «FAILED tests/test_cobro_corte1.py::test_con_el_tope_lleno_se_valida_y_se_baja_lo_ya_contado»
ROJO  | la fecha de las recargas sin zona no se toma como UTC: dice «FAILED tests/test_cobro_corte1.py::test_con_el_tope_lleno_el_extra_paga_la_operacion_nueva»
ROJO  | cuenta el usuario y no su organización: dice «FAILED tests/test_cobro_corte1.py::test_la_organizacion_es_la_que_cuenta»
ROJO  | guardar no busca la operación generada: dice «FAILED tests/test_cobro_corte1.py::test_guardar_despues_de_generar_no_cuenta_dos_veces»
ROJO  | guardar toma la operación generada de otra cuenta: dice «FAILED tests/test_cobro_corte1.py::test_guardar_con_el_archivo_de_otra_cuenta_no_toca_su_operacion»
ROJO  | guardar le saca la operación a otro cliente: dice «FAILED tests/test_cobro_corte1.py::test_guardar_en_otro_cliente_no_le_saca_la_operacion»
ROJO  | guardar no reusa la operación generada sin cliente: dice «FAILED tests/test_cobro_corte1.py::test_guardar_despues_de_generar_no_cuenta_dos_veces»
ROJO  | guardar sin haber generado no cuenta: dice «FAILED tests/test_cobro_corte1.py::test_guardar_sin_haber_generado_cuenta_una»
ROJO  | guardar toma cualquier id como archivo MARIA: dice «FAILED tests/test_cobro_corte1.py::test_guardar_con_un_id_que_no_es_un_maria_no_lo_toma_como_archivo»
ROJO  | guardar dos veces suma los ítems: dice «FAILED tests/test_cobro_corte1.py::test_guardar_dos_veces_lo_generado_reemplaza_los_items»
ROJO  | el conteo no vence la cuenta: dice «FAILED tests/test_cobro_corte1.py::test_el_conteo_vence_la_cuenta_que_vencio_despues_del_corte»
BASE  | la pantalla en verde
ROJO  | el id sin factura sale de la hora de generar: dice «FALLA: el id sin factura no sale de cuándo se cargó»
ROJO  | el id sin factura corta en segundos: dice «FALLA: el id sin factura no sale de cuándo se cargó»
ROJO  | el tope tiene otro título: dice «FALLA: tope: el modal se titula»
ROJO  | el impago se titula como tope: dice «FALLA: impago: el modal se titula»
ROJO  | la cancelada se titula como vencida: dice «FALLA: cancelada: el modal se titula»
ROJO  | la cancelada con el tope se titula como cancelada: dice «FALLA: cancelada con el tope: el modal se titula»
ROJO  | el modal no muestra el mensaje del servidor: dice «FALLA: tope: el modal dice»
ROJO  | el 402 no le pasa su razón a la generación: dice «FALLA: tope: el error de la generación dice»
ROJO  | la generación no muestra la razón del 402: dice «FALLA: tope: el error de la generación dice»
ROJO  | el 409 no muestra su mensaje: dice «FALLA: 409: el error de la generación dice»
BASE  | el lock en verde
ROJO  | no se bloquea la fila del usuario: dice «FALLA | tope»
ROJO  | no se bloquea la fila de la organización: dice «FALLA | estudio»
ROJO  | se cuenta con el usuario leído antes del lock: dice «FALLA | tope»
sabotajes con falla: 0
```

### Hallazgos de la autorrevisión

Dos rondas. La primera, sobre `3f3234d`: adversario Opus alto y adversario
Sonnet alto. La segunda, sobre `2afc90f`: `/code-review high` (Opus, alto) y
el adversario Sonnet alto.

**Primera ronda**:

| modelo | hallazgo | qué se hizo |
|---|---|---|
| Opus | `process_operation` y el Excel con el tope lleno dan 200 | riesgo: D5 a pone el tope sólo donde se cuenta |
| Opus y Sonnet | el id `FAC_<factura>` en dos clientes: la segunda guardada le mueve la operación al otro cliente | confirmado con rojo antes (`1 failed, 10 passed` sobre `298db6c`); arreglado en `3ac4dfa` |
| Opus y Sonnet | ids con símbolos o de más de 50 caracteres chocan en el mismo archivo | casos de id largo (43, 44, 50, 60) y de importación con id EXPORT; el choque de símbolos es la clave que ya usaba el archivo: riesgo |
| Sonnet | regenerar una exportación ya contada con la cuenta impaga daba 200 en la prueba (el sabotaje quedaba verde) | `298db6c`: la familia corre también en la exportación |
| Sonnet | el modal titulaba «Cancelaste» a la cancelada en período que llegó al tope | arreglado en `3ac4dfa` |
| Opus | prueba gratis con top-up vencido dice «pago pendiente»; `vencio` sólo en el pedido que vence | riesgo (textos) |
| Sonnet | el alta manual cuenta y generar ese id vuelve a contar; id vacío `OP_<segundo>`; v1 manda `Date.now()`; v1 muestra «[object Object]» | riesgo: v1 legado y ruta manual |
| Opus | en SQLite `FOR UPDATE` no protege | por eso la concurrencia se mide en Postgres |

**Segunda ronda:**

| hallazgo | qué se hizo |
|---|---|
| docstrings del guardado desactualizados | arreglado en `1a7ee26` |
| CUIT inválido y nombre largo en la prueba nueva | arreglado en `75c6476` |
| corregir un guardado en el cliente equivocado cuesta una operación | D61 |
| la huella y el tope de 10 quedan en la operación más vieja con ese archivo; si se borra, el tope se reinicia | riesgo bajo: borrar no devuelve el conteo |
| falta el caso de guardar en otro cliente con el tope lleno, y que A conserve sus ítems | riesgo |
| no hay `code` propio para la cancelada | fuera de alcance: los `code` los leen los tests de G7 |
| `generated_file` ya no identifica una sola operación | riesgo: `_operacion_maria` toma la más vieja que corresponde |

Preexistentes que encontró el adversario, no tocados: borrar un cliente no
devuelve el conteo; al reclamar una operación sin cliente, `source` pasa a
«manual»; en el tope, el modal igual dice «Ir a pagar».

### Riesgos

- Excel y `process_operation` con el tope lleno dan 200: el tope sólo se mira
  donde se cuenta (D5 a).
- Un mismo id para operaciones distintas cuenta como regeneración (D4 b).
- v1 legado: cada generación cuenta (`Date.now()` en el id); el alta manual
  cuenta y generar vuelve a contar; un 402 se ve como «[object Object]».
- Un id vacío se vuelve `OP_<segundo>`.
- Textos: una prueba gratis con top-up vencido dice «pago pendiente»;
  `vencio` sólo vale en el pedido que vence; «actualizá a Premium» aparece
  aunque sea el único plan.
- Sin lock: `_vencer_y_guardar` contra el webhook, y `_expire_extra_ops`.
- Dos miembros de una org con el mismo id cuentan dos veces.
- `/api/ncm/calcular` no tiene corte.
- En SQLite `FOR UPDATE` no protege: la concurrencia sólo se mide con
  Postgres.
- Media. Si falla la escritura del archivo después de contar, la operación
  queda contada sin TXT: el conteo hace commit (y suelta el lock) antes de
  escribir. Reintentar con el mismo id no cuenta otra vez.
- Media. C10 sigue: al publicar, el primer arranque pasa a `past_due` a todo
  `active` vencido hace más de 7 días; con esta pieza esas cuentas quedan sin
  generar, sin PDF y sin NCM.
- Baja. Sin factura, el id de la v2 es `OP_` y la hora de carga en
  milisegundos: dos cargas en el mismo milisegundo comparten id.
- Baja. Un `FAC_<número>` lo comparten dos proveedores con el mismo número de
  factura: el segundo se toma como regeneración y no cuenta.
- Baja. La operación creada al generar no tiene cliente hasta que se guarda:
  en el cockpit sale sin cliente.
- Baja. El Excel de carga (`/upload_excel_v2/`) no tiene corte: no gasta
  Gemini ni genera el TXT (D5 a).
- Baja. La ruta manual mira el tope dos veces, sin lock (`billing_service`) y
  con lock al contar; vale la segunda.

### chequeo-6

El rango `f54d8a9..75c6476` mezcla las piezas que entraron por los merges, así
que se corrió por commit de la pieza. Lo que dijo:

- `10a1a9d`: 15 avisos (217 netas, 6 de historia, 7 comentarios largos, la
  función de más de 150). `4ae523c` y `4dd2d25` sacan la historia y dejan los
  comentarios en una o dos líneas; `git grep` de historia sobre
  `proyecto_maria/` en `75c6476` da vacío (salida 1).
- `704df60`: 3 avisos (21 netas y 2 de historia), resueltos en `4ae523c`.
- `76e9fd2`: la pantalla tiene un cuerpo principal de 92 líneas. Es arnés y
  recorre los estados en orden; partirlo va a la cola de limpieza.
- **Queda un aviso:** `generate_maria_endpoint` pasa de 258 a 264 líneas. Son
  la llamada a `_contar_maria` y su comentario, sin rama nueva; la lógica
  está en `_contar_maria`. Partir la función va a la cola de limpieza.
- El resto de los commits: 0 avisos.

La última vuelta, salida entera:

```
chequeo-6 298db6c..75c6476: avisos para mirar, no un veredicto
producto +17/−11
arnés +35/−6
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11279 → 11284
  proyecto_maria/static/v2/app_v2.js: 1202 → 1203
avisos: 0
```

### Para reproducir

```bash
git checkout 75c6476
# 1. 65 passed
DATABASE_URL=sqlite+aiosqlite:///./t.db GEMINI_API_KEY=test-key ENVIRONMENT=test python -m pytest -q --no-cov tests/test_cobro_corte1.py
# 2. todo ROJO, «sabotajes con falla: 0»; sin PG, la parte del lock dice «NO CORRIDO»
PY=$(which python) PG=postgresql://<usuario>@127.0.0.1:<puerto> scripts/testing/sabotajes/cobro_corte1.sh 75c6476
# 3. 0 avisos en la última vuelta
python docs/pm/herramientas/chequeo-6.py 298db6c 75c6476
```

### Archivos de producto tocados

`proyecto_maria/main.py` (corte, conteo, 402 y guardado),
`proyecto_maria/services/billing_service.py`,
`proyecto_maria/static/v2/app_v2.js`,
`proyecto_maria/static/v2/screens/finalize.js` y `CHANGELOG.md`.

---

/compact conservar: Dev 1, rama claude/dev-tecnica. COBRO-CORTE-1 entregada en
75c6476 (informe en el commit de arriba), con D61. Sigue COBRO-MP-2, en tu
orden. Nada se publica sin el «dale» de Emi; nunca main.
