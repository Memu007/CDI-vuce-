# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## SUFIJOS-2+SEGURO-1: **entregada** en `ad2d0f8` (2026-11-08)

Base `7c0ac55`. Atiende la devolución de SUFIJOS-2 y el agregado de SEGURO-1.

**SUFIJOS-2.** Hay un solo criterio, y mira lo que sale al TXT: se recorre
carácter por carácter lo escrito contra lo que deja `caracteres_del_maria`.
Cada carácter que pasa a espacio se juzga en su palabra:

- frena si es un dígito que no es ASCII, o si la palabra no se lee igual;
- se leen igual una fecha válida, números con guion (`123-456`) y un código
  con letras sin punto de miles;
- fuera de una palabra, frena el signo de un número (`- 5`, `.5`, `10 %`).

Las fechas `dd/mm/aaaa`, `dd.mm.aaaa` y `dd-mm-aaaa` salen `dd mm aaaa` sin
frenar; la pregunta va como 11 en `PREGUNTAS-DESPACHANTE.md`. Un Z acepta
sólo dígitos ASCII (`[0-9]+`). Cada palabra se evalúa una vez: un sufijo
largo ya no cuesta cuadrático.

**SEGURO-1.** `/generate_maria/avisos` limpia los textos con la misma función
que `/generate_maria` (`_textos_como_van_al_txt`, en `main.py`): un `CIF\x00`
ya no ofrece el 1 % que la generación después rechaza. Una prueba fija la
lista de los cinco incoterms.

| SHA | qué |
|---|---|
| `b9b015c` | fix SUFIJOS-2: un criterio para el número que cambiaría + CHANGELOG |
| `31d6878` | test: la familia de entradas como datos, mutantes, pregunta de fechas |
| `4e4a58b` | fix SEGURO-1: los avisos limpian los textos como la generación + CHANGELOG |
| `1cc64b5` | test: la lista de los cinco fija; el incoterm igual en avisos y generar |
| `429c61a` | fix: un punto de miles pegado a letras y una fecha fuera de rango frenan |
| `c43977e` | test: esos casos, y sabotajes que no daban rojo |
| `cb94154` | fix: cada palabra del sufijo se mira una vez |
| `7271e9f` | test: cada palabra se mira una vez |
| `7944646` | refactor: dos comentarios en dos líneas |
| `46f4028` | refactor: el signo se reconoce sólo por su categoría Unicode |
| `be38774` | test: el ² pegado a un número y el incoterm de los avisos |
| `ad2d0f8` | test: el más suelto antes de un número y el incoterm de generar |

`producto +86/−62`. Suma 24 netas, y estas son las razones:

- la lista de signos se reemplaza por un criterio de palabra y fecha
  (`_SE_LEE_IGUAL`), con su recorrido carácter por carácter;
- se agrega la regla del Z;
- `_textos_como_van_al_txt` sale del cuerpo de `generate_maria` para
  compartirla con los avisos: es una función nueva con firma y docstring,
  y la generación pierde las mismas líneas.

## Decisiones

**D123.** Un `tipo_destinacion` con un carácter invisible adelante
(`"\x00EC01"`) da 200 en avisos y 400 en generar. La causa es que
`_rechazar_exportacion_en_importacion` corre antes de limpiar los textos.
Es preexistente: con la base pasa igual, y lo encontró la autorrevisión.

- (a) mover ese rechazo después de `_textos_como_van_al_txt` en los dos
  endpoints, con su caso;
- (b) dejarlo así.

Recomiendo (a), pero como pieza aparte: la generación ya frena con 400, así
que no sale un TXT malo. Sólo los avisos callan, y la pieza no lo pide. No
lo hice.

Supuesto reversible: los avisos ahora trabajan sobre los textos limpios. Lo
que muestran puede diferir de lo crudo en un salto de línea o un `=`, igual
que el TXT.

## Riesgos

**SUFIJOS-2: pasan sin frenar** (falsos verdes)

- `AJ(1,500)`: la coma es decimal para el MARIA, así que sale `1,500`. Si
  quien escribió quería mil quinientos, cambia de valor y no hay cómo
  distinguirlo.
- En AK, AI y AW, `15.3` sale `15,3`. Es el mismo número, pero con otra
  forma.
- `AJ(1.5.5kg)` y `AJ(1-500kg)` pasan: son palabras con letras y sin punto
  de miles de tres dígitos.
- `1-2` pasa, porque se lee como números con guion, y `V1.2.3` pasa.

**SUFIJOS-2: frenan sin necesidad** (falsos rojos, la dirección segura)

- Por un signo junto a un dígito: `ZA( 10 )`, `AI(123/ABC)`, `AB(A4+)`,
  `AA(25 °C)`, `8E-5`, `12:30`, `V1.234` y un `=` suelto.
- Por dígitos o símbolos que no son ASCII: `ø5`, `M3²` y `MODELO Ⅳ` con
  espacio.
- Por la coma sin espacio después: `AA(TALLE 5,AZUL)` frena;
  `AA(TALLE 5, AZUL)` pasa.
- `AB(ABC12_XL)`: el `_` después de un dígito.
- `1 - 2`, con el guion suelto entre dos números.

**SUFIJOS-2: se toman como fecha**

- `1.2.33` y `10.10.10` salen `1 2 33` y `10 10 10`. Si eran una versión
  o un código, el MARIA los recibe con espacios; no cambia ningún número.

**SEGURO-1**, los tres que pediste:

- el 1 % sin `seguro_calculado` lo cubre SEGURO-2;
- el seguro mayor al FOB es preexistente, no lo toqué;
- «no los sumes dos veces» contra «cargá el de la factura» queda como
  texto de pantalla; no lo cambié.

**Otros**

- La normalización del incoterm está en dos lugares:
  `_textos_como_van_al_txt` (`main.py`) y `seguro_en_el_precio`
  (`maria_generator.py`). Los dos hacen `.strip().upper()`, y una prueba
  falla si generar deja de normalizar (sabotaje 3 de `seguro1.sh`).
- Una procedencia `"C\nN"` muestra el salto de línea crudo en el texto del
  400. No llega al TXT.
- Para la cola de limpieza: que `caracteres_del_maria` devuelva sus spans.
  Así `_numero_que_cambiaria` no tendría que depender de que
  `sin_tildes(x)` y `caracteres_del_maria(x)` midan lo mismo; hoy un caso
  lo fija.

## Hallazgos de la autorrevisión

| quién | modelo y esfuerzo | hallazgo | qué hice |
|---|---|---|---|
| adversario | Sonnet alto | `2.500KG` y `AB-1.500` pasaban: punto de miles pegado a letras | `429c61a` + caso + sabotaje |
| adversario | Sonnet alto | `12.50.2026` y `32/12/2026` pasaban como fecha | `429c61a` + caso + sabotaje |
| adversario | Sonnet alto | costo cuadrático: `"a."*4000` 0.86–0.91 s, `"a1-"*3000` 0.75–0.80 s | `cb94154`: 0.019 s y 0.017 s; caso que cuenta las evaluaciones |
| adversario | Sonnet alto | `AJ(1.5.5kg)-`, `AJ(1-500kg)-` pasan | riesgo, arriba |
| `/code-review` | high | `ZA( 10 )` frena | riesgo (falso rojo), arriba |
| `/code-review` | high | falsos rojos `AI(123/ABC)`, `AB(ABC12_XL)`, `AB(A4+)`, `AA(TALLE 5,AZUL)`, `AA(25 °C)`, `MODELO Ⅳ` | riesgo, arriba |
| `/code-review` | high | `1.2.33` se toma como fecha | riesgo, arriba |
| `/code-review` | high | que `caracteres_del_maria` devuelva sus spans | propuesta para la cola, arriba |
| yo | — | el mutante 4 (signo sin `Sm`) sobrevivía en `be38774` | `ad2d0f8`: casos `AF(+ 5)-` y `AF(− 5)-` |
| yo | — | un sabotaje de `seguro1.sh` no daba rojo (generar sin normalizar) | `ad2d0f8`: apunta a `main.py`, rojo en `[cif ]` |
| yo | — | `"\x00EC01"`: 200 en avisos, 400 en generar | D123 |

## Rojos antes del arreglo

Cada caso nuevo, corrido sobre el producto de antes y con las pruebas de
ahora:

| qué | salida |
|---|---|
| la familia de SUFIJOS-2, sobre `7c0ac55` | `25 failed, 70 passed, 5 warnings in 4.81s` |
| miles pegado a letras y fecha fuera de rango, antes de `429c61a` | `8 failed, 96 passed, 3 warnings in 4.69s` |
| el incoterm en los avisos, antes de `4e4a58b` | `2 failed, 50 passed, 3 warnings in 14.62s` (`[nul]`, `[control_adelante]`) |
| cada palabra una vez, antes de `cb94154` | `3 failed, 104 deselected, 3 warnings in 0.58s` (`assert 1999 <= 1`) |

## Mutantes

Los siete que pediste, más el 7b. Cada uno, sobre `ad2d0f8`, con la prueba
que lo mata (copiado de `mut7_ad2d0f8.log`):

| mutante | rojo |
|---|---|
| BASE | `172 passed, 5 warnings in 9.80s` |
| 1 sin el dígito siguiente en el vecino de un dígito no ASCII | `[AJ(M\xb25)-]` |
| 2 `len(decimales) == 3` → `>= 3` | `[AJ(1.5000)--AJ(1,5000)-]` |
| 3 `entero.lstrip("0") != ""` → `entero != "0"` | `[AJ(00.500)--AJ(00,500)-]` |
| 4 el signo sin `Sm` (`+`) | `[AF(+ 5)-]`, `[AF(− 5)-]` |
| 5 lo que cierra un número sin `,` | `[AA(TALLE 5, AZUL)--AA(TALLE 5  AZUL)-]` |
| 6 Z sin `upper()` | `[za(2.5)-]` |
| 7 lo que cierra un número sin `-` | `test_cada_palabra_se_mira_una_vez[guiones]` |
| 7b el signo sin `Pd` (`-`) | `[AF(- 5)-]` |

## Puertas

Todas sobre `ad2d0f8`, desde worktree limpio y una a la vez; los logs están
en el scratchpad.

| puerta | salida exacta |
|---|---|
| `compileall -q proyecto_maria` | `compileall 0` |
| suite, SQLite (`ENVIRONMENT=test`, `--timeout=300`) | `5269 passed, 335 skipped, 3 xfailed, 99 warnings in 1007.44s (0:16:47)`, `SALIDA suite_mia 0` |
| suite como la CI (`ENVIRONMENT=testing`, sin `DATABASE_URL`) | `5269 passed, 335 skipped, 3 xfailed, 95 warnings in 1034.83s (0:17:14)`, `SALIDA suite_ci 0` |
| `test_sufijos2` + `test_sufijos1` + `test_seguro1` | `224 passed, 5 warnings in 23.20s` |
| sabotajes `sufijos2.sh` | `BASE \| 110 passed, 5 warnings in 4.40s`, 32 `ROJO`, `sabotajes sin rojo: 0` |
| sabotajes `seguro1.sh` | `BASE \| 52 passed, 5 warnings in 15.23s`, 12 `ROJO`, `sabotajes sin rojo: 0` |
| grep de historia de §6 | vacío |

`seguro1.sh`, entero:

```
BASE  | ======================= 52 passed, 5 warnings in 15.23s ========================
ROJO  | DPU fuera de la lista: «test_con_los_cinco_no_hay_sugerencia[DPU]» «test_los_avisos_traen_la_regla_del_servidor[DPU]»
ROJO  | el incoterm sin normalizar: «test_mayusculas_minusculas_y_espacios_dan_lo_mismo»
ROJO  | generar no normaliza el incoterm antes del TXT: «test_una_operacion_cif_lleva_su_seguro_en_el_txt[cif ]»
ROJO  | el servidor no le pasa el incoterm a las cuentas: «test_los_avisos_traen_la_regla_del_servidor[CIF]»
ROJO  | la pantalla decide por su cuenta con el incoterm: «test_la_pantalla_sigue_al_servidor_y_no_al_incoterm»
ROJO  | el botón calcula igual con CIF: «test_con_cif_el_boton_no_pone_nada»
ROJO  | el calculado sobrevive en la pantalla: «test_el_calculado_se_borra_al_pasar_a_cif_y_queda_para_completar[con_cuentas]» «test_el_calculado_que_se_borra_sin_lista_de_sin_leer_la_arma»
ROJO  | el calculado sobrevive en el servidor: «test_un_seguro_calculado_con_cif_no_genera» «test_el_cambio_de_incoterm_con_el_seguro_calculado[cfr_a_cif]»
ROJO  | se borra también el escrito: «test_el_seguro_escrito_no_se_toca_al_pasar_a_cif»
ROJO  | se borra con cuentas de otro pedido: «test_con_cuentas_de_otro_pedido_no_se_borra»
ROJO  | el borrado deja el seguro como completado: «test_el_calculado_se_borra_al_pasar_a_cif_y_queda_para_completar[con_cuentas]»
ROJO  | sin respuesta de los avisos se ofrece dejarlo: «test_sin_respuesta_de_los_avisos_no_se_ofrece_dejarlo[CIF]»
sabotajes sin rojo: 0
```

`sufijos2.sh` son 32 líneas de `ROJO`, una por motivo, y terminan en
`sabotajes sin rojo: 0`. Las últimas tres:

```
ROJO  | cada carácter que cambia vuelve a mirar la palabra entera: «test_cada_palabra_se_mira_una_vez[puntos]» «test_cada_palabra_se_mira_una_vez[guiones]»
ROJO  | los miles se toman como decimales: «test_un_numero_que_cambiaria_no_se_genera[AJ(ROLLO 1.500 M)-]»
ROJO  | un cero adelante también se toma como miles: «test_lo_que_no_cambia_un_numero_sale_como_antes[AJ(0.750)--AJ(0,750)-]»
```

No corrí `smoke_friccion.sh` ni `ataque_aislamiento.sh`. La pieza cambia
cómo se limpian los sufijos y el incoterm antes del TXT, y eso lo miden los
casos y los sabotajes. No toca sesión, permisos ni datos de otro usuario.

chequeo-6, entero:

```
chequeo-6 7c0ac55..ad2d0f8: avisos para mirar, no un veredicto
producto +86/−62
  AVISO producto suma 24 líneas netas: el informe dice por qué (§6: más de 20)
arnés +158/−38
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/maria_generator.py: 2305 → 2321
  proyecto_maria/core/sufijos_arca.py: 236 → 241
  proyecto_maria/main.py: 12060 → 12063
avisos: 1
```

El `AVISO` está explicado arriba, junto a la tabla de SHAs.

## Comandos

```bash
git fetch origin claude/dev-maria && git checkout ad2d0f8
<venv>/bin/python -m pytest -q --no-cov tests/test_sufijos2.py tests/test_sufijos1.py tests/test_seguro1.py   # 224 passed
PY=<venv>/bin/python bash scripts/testing/sabotajes/sufijos2.sh ad2d0f8   # 32 ROJO, «sabotajes sin rojo: 0»
PY=<venv>/bin/python bash scripts/testing/sabotajes/seguro1.sh ad2d0f8    # 12 ROJO, «sabotajes sin rojo: 0»
```

## Archivos de producto tocados

- `proyecto_maria/core/maria_generator.py`
- `proyecto_maria/core/sufijos_arca.py`
- `proyecto_maria/main.py`
- `CHANGELOG.md`

Además, `docs/pm/PREGUNTAS-DESPACHANTE.md` (la pregunta 11).

Sigo con SEGURO-2.

/compact conservar: Dev MARIA (session_01C8gCBjvn36wnYC6qG2Sixi), rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM session_01B7FVQspcEHF7PqNv797wNM con send_message next. SUFIJOS-2+SEGURO-1 entregada en ad2d0f8 (base 7c0ac55). Próxima D libre D124. Sigue SEGURO-2, después EMAIL-1, CONEXIONES-1, OBSERVABILIDAD-1, ORG-1+D40 y D102. Corte de rutinas 2026-11-08 15:50 UTC. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; TXT y proforma reales nunca en el repo.
