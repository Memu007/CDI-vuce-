# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Entrega D263: sobre `9e5960d2` (10:16 UTC)

**Resultado.** Los cuatro criterios se cumplen en `9e5960d2` (base `d363fb38`). La validación y el TXT
leen el origen con una sola función, `origen_de(item)`: el primero escrito entre `pais_origen` y `origen`,
con `strip`, igual que `procedencia_de`. Hoy (`d363fb38`) «4340» en `pais_origen` con `origen` «CN» sale
`CARTPAYORI=4340`; «ATLANTIDA» o «  » en `pais_origen` con `origen` «BR» salen 310 (China) sin aviso;
`pais_origen` «BR» sin `origen` frena. Con el arreglo, los dos primeros frenan nombrando el ítem y el
valor, y los otros salen 203. La pantalla manda sólo `origen`: sigue igual. `producto +19/−13`.

**Lo que decidís vos:**
- **D268. El generador no se defiende solo.** `generate_maria_txt` llamado sin validar escribe 310 con un
  origen vacío o no reconocido (lo reprodujo un adversario llamando a la función). Por HTTP no se llega:
  la única llamada (`main.py` ~5188) va después de `validate_items_for_maria`. El agrupado ya se defiende
  («Defensa en profundidad»). Propongo una pieza chica: que el generador tire `ValueError` si
  `pais_reconocido(origen_de(item))` es falso. No lo hice: es fuera de la tarea.

**El arreglo (`521d5fda`).** `_primero_escrito(item, claves)` sale del cuerpo de `procedencia_de`; sobre
ella, `procedencia_de` y `origen_de`. `origen_de` la usan la validación, la clave de posición, el agrupado,
el generador y los dos supuestos (sin procedencia, sin estado). Se fueron los dos `'CN'` de respaldo: con
un origen vacío daban lo mismo que `get_pais_codigo("")`, y la validación ya frena antes.

### Criterio 1: el caso

`test_generate_maria_valida_el_origen_que_sale_en_el_txt` (`tests/test_generar_maria_txt.py`). Once
pares `(pais_origen, origen)` como datos, por `/generate_maria`; cada uno da el `CARTPAYORI` del ítem o
los errores exactos con que frena:
- no reconocido con válido al lado: `("4340","CN")`, `("ATLANTIDA","BR")` → «Item 2: Origen no reconocido
  '4340'…»;
- válido sin el otro, o con el otro inválido: `("BR",None)`, `("BR","")`, `("BR","ATLANTIDA")` → 203;
- ninguno: `(None,None)`, `("","")`, `("  ","  ")` → «Item 2: Falta origen/país de origen» (nunca 310);
- vacío o en blanco con válido: `("","BR")`, `("  ","BR")`, `(None,"BR")` → 203. `(None,"BR")` es lo
  que manda la pantalla (criterio 2).

`("BR","ATLANTIDA")` lo sumé por un adversario: distingue la validación que revisa los dos campos de la
que revisa el que sale. Con esa mutación, rojo.

### Criterio 3: el rojo con el arreglo revertido

Producto de `d363fb38`, pruebas de `9e5960d2`:
```
  Differing items:
  {('4340', 'CN'): ['4340']} != {('4340', 'CN'): ["Item 2: Origen no reconocido '4340'. Debe indicar un país válido."]}
  {('ATLANTIDA', 'BR'): ['310']} != {('ATLANTIDA', 'BR'): ["Item 2: Origen no reconocido 'ATLANTIDA'. Debe indicar un país válido."]}
  {('BR', None): ['Item 2: Falta origen/país de origen']} != {('BR', None): ['203']}
  {('BR', 'ATLANTIDA'): ["Item 2: Origen no reconocido 'ATLANTIDA'. Debe indicar un país válido."]} != {('BR', 'ATLANTIDA'): ['203']}
  {('  ', '  '): ["Item 2: Origen no reconocido '  '. Debe indicar un país válido."]} != {('  ', '  '): ['Item 2: Falta origen/país de origen']}
  {('BR', ''): ['Item 2: Falta origen/país de origen']} != {('BR', ''): ['203']}
  {('  ', 'BR'): ['310']} != {('  ', 'BR'): ['203']}
================= 1 failed, 60 deselected, 6 warnings in 3.10s =================
```

## Sabotajes (§3)

`scripts/testing/sabotajes/origen_txt.sh` (nuevo, sobre el arnés `_casos_y_pantalla.sh`, que ahora corre
sin pantalla si no se la nombra): la validación que lee sólo `origen`, el orden de los campos, el blanco que
tapa al otro (sólo en `origen_de`) y el generador con su propio origen. Dos anclas se movieron y las seguí:
`sabotaje_maria4.sh:98` (los supuestos leen el origen como el generador) y `catalogo3.sh:297` (el agrupado
compara el país, no la forma). `sabotaje_maria3.sh:206` sigue anclando el `strip`, que ahora está en
`_primero_escrito`. `anclas_perdidas.py 9e5960d2`: sólo la de siempre (`limpieza1.sh:135`).

| guion | SHA | resultado |
|---|---|---|
| `origen_txt.sh` | `9e5960d2` | 4 ROJO, «sabotajes sin rojo: 0» |
| `sabotaje_maria3.sh` | `9e5960d2` | «OK: los 32 sabotajes dan rojo por la razón esperada» |
| `sabotaje_maria8.sh` | `9e5960d2` | «OK: los 70 sabotajes dan rojo por la razón esperada» |
| `sabotaje_maria4.sh` | `df2f3aac` | «OK: los 8 sabotajes dan rojo por la razón esperada» |
| `catalogo3.sh` | `df2f3aac` | «fallas: 0» |
| `holanda423.sh` | `df2f3aac` | «sabotajes sin rojo: 0» (usa el arnés con pantalla) |

Los tres de `df2f3aac`: lo que vino después sólo toca el caso nuevo y `origen_txt.sh`.

## Revisión

- `/code-review high` y dos adversarios (Opus y Sonnet, alto), sin mi conclusión. Ninguno encontró
  una entrada por `/generate_maria` que saque un origen distinto del validado o 310 en silencio.
  Probaron tipos raros (0, `false`, listas, dicts, números), invisibles, grupos, renglones que se
  juntan, procedencia de la operación y origen argentino.
- Atendido: el caso aceptaba cualquier error «de origen» (ahora compara el error exacto, `71c7833f`);
  faltaba `("BR","ATLANTIDA")` (`3dbbcf53`); el sabotaje del `strip` compartía línea con la procedencia y
  una `PANTALLA` exportada se colaba como base (`9e5960d2`).
- No atendido, va a riesgos o a D268: el generador sin defensa propia; el agrupado y el aviso «sin
  procedencia» no tienen caso con `pais_origen` y `origen` distintos; `/generate_maria/avisos` no
  anticipa un origen no reconocido (ya era así); la unidad tiene la misma cadena con `or`.
- Descartado: «guion de sabotaje propio fuera de §3» (la tarea lo pide: cambia lo que sale en el TXT).

## Puertas

Todas sobre `9e5960d2`, en un worktree limpio (`/tmp/cdi-dev2/wt-d263`, sólo el enlace a `config/node_modules`):
```
=== 6200 passed, 110 skipped, 3 xfailed, 108 warnings in 1184.62s (0:19:44) ====
E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.
```
Los sabotajes, arriba. No corrí `despacho1b.sh` ni `catalogo_largo2.sh` (Postgres): no anclan nada de lo tocado.

## Comandos

```bash
VENV=/ruta/al/venv   # el tuyo
PT="env -u DATABASE_URL -u ENVIRONMENT GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=. $VENV/bin/python -B -m pytest -q --no-cov -p no:cacheprovider"
# 1. el rojo: producto de d363fb38, pruebas de 9e5960d2
R=/tmp/rojo263; git worktree add -f -q --detach $R 9e5960d2 && cd $R && git checkout d363fb38 -- proyecto_maria
$PT tests/test_generar_maria_txt.py -k origen_que_sale | grep -E "4340|failed"   # «('4340', 'CN'): ['4340']» y «1 failed»
cd - >/dev/null; git worktree remove -f $R
# 2. el caso, verde en 9e5960d2
$PT tests/test_generar_maria_txt.py -k origen_que_sale | tail -1                  # «1 passed»
# 3. sabotajes y §6
PATH=$VENV/bin:$PATH PY=$VENV/bin/python bash scripts/testing/sabotajes/origen_txt.sh 9e5960d2 | tail -1   # «sabotajes sin rojo: 0»
python3.12 docs/pm/herramientas/chequeo-6.py d363fb38 9e5960d2     # «producto +19/−13», «avisos: 0»
```

chequeo-6, entero:
```
chequeo-6 d363fb38..9e5960d2: avisos para mirar, no un veredicto
producto +19/−13
arnés +77/−5
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/maria_generator.py: 2394 → 2400
avisos: 0
```

| commit | qué |
|---|---|
| `521d5fda` fix | `origen_de` en la validación y en todo lo que lee el origen del TXT; CHANGELOG |
| `47862198` test | el caso |
| `df2f3aac` test | `origen_txt.sh`; las anclas de maria4 y catalogo3 |
| `71c7833f` test | el caso compara el error exacto |
| `3dbbcf53` test | `("BR","ATLANTIDA")` |
| `9e5960d2` test | el sabotaje del blanco sólo en `origen_de`; `PANTALLA=`. **Lo que se entrega** |
| informe | el commit siguiente |

## Riesgos

- **D268** (arriba): `generate_maria_txt` sin validar antes escribe 310 en silencio.
- **Sin caso propio**: el agrupado (`grupo_id`) y el aviso «sin procedencia» con `pais_origen` y
  `origen` distintos. Usan `origen_de`, y la clave de posición sí queda cubierta por
  `test_supuestos_leen_el_origen_como_el_generador`.
- **La misma cadena en la unidad**: `unidad="  "` con `unidad_medida="KG"` sale 07. Lo propongo para la
  cola de limpieza; no lo toqué.
- **Sub-ítems**: el origen de un sub-ítem se ignora sin aviso (ya pasaba; la pantalla no lo manda).
- **Cambia para quien llame a la API a mano**: `pais_origen` válido sin `origen` ahora genera;
  `pais_origen` no reconocido o adivinado por prefijo con `origen` válido ahora da 400.
- Lo de producción no se midió; la CI deselecciona y Railway no la espera.

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5, rama `claude/dev-maria`, rutina trig_01Ukttby1fc4sGVQfSn1jC9U; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `d363fb38`). Aceptadas: las de antes (CUIT-GENERAR `29327d2` … D257 (b) `3c7eb14`), D244 (a) y Holanda→423 sobre `b3a3bf69`, D239 (a) sobre `01c28e83`. En revisión: D263 (la validación y el TXT leen el origen con `origen_de`), entregada sobre `9e5960d2` (base `d363fb38`), informe en el commit siguiente; puertas en «Puertas» de este archivo. Abierta para la PM: D268 (el generador sin validar escribe 310 en silencio). D266 y D267 quedaron como riesgo escrito de D239 (a). Sin pieza marcada «apenas entregues»: si al despertar no hay nada nuevo, termino la vuelta. Si la PM avisa un «sin rojo» en su `despacho1b.sh` de D239 (a), esa va primero. D262 (a) está en la cola de limpieza; D261 la lleva la PM. Próxima D: D269. Lecciones (además de las de antes, que siguen en el historial de este archivo): una tarea en segundo plano muere a las 2 h: puertas largas con `setsid nohup` y un vigía que espera una línea en un archivo; `despacho1b.sh` tarda unas 2 h y sin PG_DSN sale 1: Postgres 16 está en /usr/lib/postgresql/16 (initdb y pg_ctl como postgres, en /tmp/cdi-dev2/pg16, puerto 55472); no editar un guion de sabotaje mientras corre; medir `anclas_perdidas.py` y correr el guion del ancla antes de entregar; `/security-review` necesita `origin/HEAD`: ref local temporal y borrarlo; horas, sólo de `date -u`. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica; subagentes hasta esfuerzo alto, sin consejero, nunca Fable; detener los subagentes después de su informe.
