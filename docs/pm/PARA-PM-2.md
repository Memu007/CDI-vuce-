# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ENTRADAS-2 (D101, D104): **entregada** en `b8aa9bd` (2026-11-08)

| Qué | SHAs |
|---|---|
| Base | `b727ed3` (el arnés de PG `3447b10` es el primer commit de la pieza; chequeo-6 mide desde `28c72f8^` = `3447b10`, el producto es el mismo) |
| Producto y CHANGELOG | `28c72f8`, `a91c7b8`, `c9343e0`, `7a439b8` |
| Pruebas, sabotajes y arnés de PG | `3447b10`, `2a5848d`, `e8174db`, `ecd0923`, `b38dea4`, `0809112`, `b8aa9bd` |
| Merge de tu rama (sólo `docs/pm/NOW.md`) | `fbe9a7e` |
| Informe | el `docs:` que sigue a `b8aa9bd` |

**Resultado.** En Postgres, ningún texto ni número de afuera da 500 en estas entradas:
- **Operación manual** (`POST /api/operations/manual`):
  - un cuerpo o un ítem que no es objeto da 400;
  - un número no finito (`NaN`, `1e999`, `-Infinity`) o de texto da 400;
  - un total que desborda da 400;
  - un NUL o un surrogate en descripción o pieza se cambia por «�»;
  - la pieza se corta a su columna (20);
  - un `grupo_id` fuera de `int32` se guarda como sin grupo.
- **Clientes, alta y edición:** los textos se limpian campo por campo, también con un campo muy anidado al lado. El email repetido en la edición da 409 y no cambia nada.
- **Guardar al cliente** (`POST /api/clientes/{id}/operaciones`): da 400 y no guarda nada con:
  - un JSON roto, vacío o muy hondo;
  - `NaN` o infinito en cualquier lugar del cuerpo;
  - un entero de más de 32 bits;
  - `resumen.items` o la cantidad de un ítem de texto.

  `resumen.items` en null cuenta los ítems.
- **Ruta:** un NUL en la ruta da 404 antes de llegar a la ruta.
- **Agrupar:**
  - más de 10000 ids da 422;
  - si el número de grupo más alto del usuario ya es el último de `int32`, da 409 y no cambia nada.
- **Clave (D104):** el alta de estudio pide la misma política que el registro: 8 caracteres y un número o símbolo. Hay un solo chequeo, `_exigir_politica_de_clave`.

## Decisiones

**D109. Las entradas que ENTRADAS-2 no cubre.** Estas tres siguen pudiendo dar 500 o perder el registro:
- otras rutas llaman a `tiene_medio_par` sobre el cuerpo crudo, fuera de un `try`, y un cuerpo muy hondo daría `RecursionError` 500: `main.py` ~8734 y ~8889 (no lo reproduje);
- un NUL en el query string;
- un NUL en la ruta: hoy da 404 bien, pero el log de métricas (`api_logs`) falla al guardarlo con `CharacterNotInRepertoireError`. Se ve en el arnés de PG, y ese pedido queda sin registro.

Opciones:
- (a) **Recomendada.** Pieza ENTRADAS-3 con las tres. Son del mismo tipo y el arnés de PG ya está.
- (b) Dejarlas. El de las métricas no da 500 a la persona, sólo pierde el registro.

**D110. Un campo del cliente que no es texto** (lista u objeto en `nombre`, `cuit`…) hoy se guarda como su `repr` de Python.
- (a) **Recomendada.** Rechazar con 400. La pantalla nunca manda eso.
- (b) Dejarlo. No da 500 y no rompe nada.

Próxima D libre: D111.

**Supuestos reversibles.**
- El tope de agrupar es 10000 ids (422 por encima). La pantalla agrupa de a decenas.
- El texto «Body JSON inválido» se usa también para un cuerpo muy hondo o un entero enorme (cosmético, ver riesgos).

## Archivos de producto que toqué

- `proyecto_maria/main.py` (+115/−49):
  - `_exigir_politica_de_clave` (:341);
  - el middleware `_RutaSinNul` (:433);
  - `_textos_de_arriba_guardables` (:7364);
  - `_numero_de_afuera`, `_entero_de_afuera`, `_no_finito`, `_float_finito` y `_json_guardable` (:7974);
  - el tope de agrupar (:8183) y su 409 (:8255).
- `CHANGELOG.md`: una entrada de tres líneas.

`producto +115/−49`. Suma 66 líneas netas porque son cuatro puertas de entrada, cada una con su ayudante: el cuerpo de la manual, los textos del cliente, el lector de JSON con números finitos y el middleware de NUL en la ruta. Además están el tope y el 409 de agrupar, y la política de clave unificada. Dos ayudantes reemplazan chequeos que estaban repetidos: los números y la clave.

### chequeo-6, salida entera

```
chequeo-6 28c72f8^..b8aa9bd: avisos para mirar, no un veredicto
producto +115/−49
  AVISO producto suma 66 líneas netas: el informe dice por qué (§6: más de 20)
arnés +383/−5
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11981 → 12047
avisos: 1
```

El AVISO es el de las 66 líneas, explicado arriba.

## Casos

`tests/test_entradas2.py`, en SQLite. Doce casos, uno por causa, con la familia de entradas como datos:
- `test_manual_con_numero_no_valido_da_400_y_no_guarda`;
- `test_manual_con_algo_que_no_es_objeto_da_400`;
- `test_manual_guarda_lo_de_afuera_en_la_forma_que_entra_en_su_columna`;
- `test_texto_del_cliente_que_no_se_puede_guardar_queda_con_reemplazo`;
- `test_cliente_con_un_campo_muy_anidado_se_guarda`;
- `test_editar_cliente_con_el_email_de_otro_da_409_y_no_cambia_nada`;
- `test_guardar_al_cliente_con_cuerpo_no_valido_da_400_y_no_guarda`;
- `test_guardar_al_cliente_con_resumen_items_null_cuenta_los_items`;
- `test_nul_en_la_ruta_da_404_antes_de_llegar_a_la_ruta`;
- `test_agrupar_con_mas_ids_de_los_que_acepta_da_422`;
- `test_agrupar_sin_numeros_de_grupo_libres_da_409_y_no_cambia_nada`;
- `test_alta_de_estudio_pide_la_misma_clave_que_el_registro`.

Corridos sobre el producto viejo (`3447b10`), dieron 9 failed: el rojo antes del verde.

`scripts/testing/entradas2_postgres.py` hace lo mismo contra Postgres de verdad, donde el NUL y el `int32` sí dan 500. Con el producto saboteado dio 3 FALLA, las tres con 500.

## Hallazgos de la autorrevisión

| Quién | Hallazgo | Qué hice |
|---|---|---|
| Opus alto | F1: un cliente con un campo muy anidado daba 500 en alta y edición | Arreglado en `c9343e0` |
| Opus alto | F2: `grupo_id` 2147483647 y después agrupar daba 500 en PG | Arreglado en `c9343e0` (409) |
| Opus alto | F3: un cuerpo roto, vacío, de 5000 dígitos o hondo a guardar al cliente daba 500 | Arreglado en `c9343e0` |
| Opus alto | F5b: `resumen.items` null no contaba los ítems | Arreglado en `c9343e0` |
| Sonnet alto | F2 confirmado. F3, más `tiene_medio_par` fuera del `try` (`RecursionError`) | Arreglado en `c9343e0`: lo moví adentro |
| Sonnet alto | NUL en el query string, el log de métricas, diferencias de política | D109 y riesgos |
| `/code-review high` 1 | El 409 de agrupar mira el máximo global del usuario: un ítem con 2147483647 bloquea agrupar en todas sus operaciones | Riesgo bajo: sólo se llega por la API y es contra sí mismo |
| `/code-review high` 2 | El límite de hondura depende de `RecursionError`, un umbral frágil | Riesgo de las pruebas. Medí: 50–450 niveles guardan 200 y 500 o más dan 400. No encontré camino a 500 |
| `/code-review high` 3 | El arnés de PG aceptaba cualquier código menor que 500 en agrupar | Arreglado en `b8aa9bd`: exige 409 |
| `/code-review high` 4 | El cuerpo se recorre tres veces | Riesgo de rendimiento, bajo |
| `/code-review high` 5 | Estilo de `_no_finito` | Queda como está |
| `/code-review high` 6 | Limpiador duplicado | `_guardable_en_pg` es de la Dev 1: lo reusé sin cambiarlo |
| `/code-review high` 7 | Un campo anidado del cliente se guarda como `repr` | D110 |
| `/code-review high` 8 | «Body JSON inválido» también para hondo o entero enorme | Riesgo cosmético |
| `/code-review high` 9 | Redacción del CHANGELOG | Arreglado en `7a439b8` |

`/security-review` corrió sobre la rama en `ecd0923`. El tramo `c9343e0..b8aa9bd` lo revisó sólo `/code-review high`.

## Puertas sobre `b8aa9bd`

| Puerta | Salida exacta |
|---|---|
| Sabotajes (`scripts/testing/sabotajes/entradas2.sh`) | `BASE  \| en verde`, 24 `ROJO`, `sabotajes con falla: 0`, `SALIDA sab 0` |
| Arnés PG 16 (`entradas2_postgres.py`, puerto 55432) | 33 `OK`, `fallas: 0`, `SALIDA pg 0` |
| `compileall proyecto_maria` | `compileall 0` |
| Suite completa, mi entorno (`ENVIRONMENT=test`, SQLite) | `5193 passed, 335 skipped, 3 xfailed, 99 warnings in 998.12s (0:16:38)`, `SALIDA suite_mia 0` |
| Suite completa, entorno de la CI (`ENVIRONMENT=testing`, sin `DATABASE_URL`) | `5193 passed, 335 skipped, 3 xfailed, 96 warnings in 948.07s (0:15:48)`, `SALIDA suite_ci 0` |

- Las dos suites corrieron desde un worktree limpio en `b8aa9bd`, una después de la otra.
- No corrí `smoke_friccion.sh` ni `ataque_aislamiento.sh`. La pieza no cambia sesión ni permisos, y los casos y el arnés de PG cubren el backend tocado.
- Corrí `/security-review` sólo hasta `ecd0923`.

Los 24 rojos, copiados de la salida:
- **Operación manual:**
  - un número no finito pasa;
  - el total no se revisa;
  - un cuerpo que no es objeto pasa;
  - un ítem que no es objeto pasa;
  - la descripción no se limpia;
  - la pieza no se limpia;
  - la pieza no se corta;
  - el grupo fuera de rango se guarda.
- **Clientes:**
  - el alta no limpia los textos;
  - la edición no limpia los textos;
  - el cliente se limpia entero y no campo por campo;
  - el email repetido en la edición no da 409.
- **Guardar al cliente:**
  - un NaN fuera de los números leídos pasa;
  - un infinito fuera de los números leídos pasa;
  - un JSON roto da 500;
  - lo muy hondo se revisa fuera del try;
  - un entero de más pasa;
  - resumen.items de texto no se revisa;
  - resumen.items en null no cuenta los ítems;
  - la cantidad de un ítem no se revisa.
- **Ruta, agrupar y clave:**
  - el NUL en la ruta llega a la ruta;
  - agrupar pasa el último número de grupo;
  - agrupar no tiene tope;
  - el alta de estudio no pide número o símbolo.

## Comandos para reproducir

```bash
git fetch origin claude/dev-maria && git checkout b8aa9bd
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov tests/test_entradas2.py           # → 36 passed
PY=python scripts/testing/sabotajes/entradas2.sh               # → 24 ROJO, «sabotajes con falla: 0»
python scripts/testing/entradas2_postgres.py postgresql://cdi@127.0.0.1:55432/postgres   # → «fallas: 0»
git checkout 3447b10 -- proyecto_maria/main.py && python -m pytest -q --no-cov tests/test_entradas2.py; git checkout b8aa9bd -- proyecto_maria/main.py   # → 9 failed (el rojo)
docs/pm/herramientas/chequeo-6.py 28c72f8^ b8aa9bd             # → la salida de arriba, «avisos: 1»
```

## Riesgos

- **Políticas de NUL distintas.** La ruta da 404. Los textos de la manual y del cliente se cambian por «�». Guardar al cliente da 400 «Hay un carácter que no se puede guardar.».
- **El 409 de agrupar mira el máximo global del usuario** (`/code-review` 1). Bajo: sólo se llega mandando el número por la API.
- **La hondura depende de `RecursionError`** (`/code-review` 2). Si cambia el límite de pila, cambia dónde está el umbral, pero sigue en 400 y no en 500.
- **Datos que pasan con una forma rara** (no dan 500, pero se guardan así):
  - un `null` en un texto del cliente se guarda como `"None"`;
  - `inf` o `nan` escritos como texto en cuit o teléfono se guardan como texto;
  - `"1_000"` lo acepta `float()`;
  - un username con `\n` al final.
- **Cosas que sigue haciendo el código viejo:**
  - la moneda se trunca sin aviso;
  - la pieza se corta a 20 sin aviso;
  - `profile.js:293` muestra el mensaje de clave del front, no el del backend.
- **Cookie o Bearer:** no probé las dos formas de sesión en cada ruta.
- **Números finitos enormes** (`1e308`) pasan como número. En la manual, el total que desborda da 400 (caso `total_que_desborda`); en guardar al cliente no lo probé.
- **Orden de mensajes:** con dos errores en el cuerpo se ve el primero que se encuentra.
- **Rendimiento:** el cuerpo de guardar al cliente se recorre tres veces (`/code-review` 4).
- **D109:** sigue abierto lo del query string, las otras rutas con `tiene_medio_par` y el log de métricas.

Sigo con ENTORNO-3 (D107 a).

/compact conservar: Dev MARIA (session_01C8gCBjvn36wnYC6qG2Sixi), rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM session_01B7FVQspcEHF7PqNv797wNM con send_message next. ENTRADAS-2 (D101, D104) entregada en b8aa9bd (base b727ed3), D109 y D110 abiertas (recomendé a en las dos), próxima D libre D111. FRONT-422 aceptada en 4dbdb0b, D108 decidida (a). Sigue ENTORNO-3 (D107 a: FRONTEND_URL, ALLOWED_ORIGINS, HSTS y el paso de 127.0.0.1 del rate limit con es_desarrollo(); sabotajes en el arnés de test_entorno1; los monkeypatch de IS_PRODUCTION viejos a la cola) y después D102 (fijar bcrypt). Corte de rutinas 2026-11-08 15:50 UTC. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; TXT y proforma reales nunca en el repo.
