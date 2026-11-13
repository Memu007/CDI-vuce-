# PAIS-NL: reproducción de la PM

Entrega `a2c6dc6` (informe `22e84e5`, canal `PARA-PM-2.md`). Base `6fbfefd`.
Veredicto: **aceptada sobre `a2c6dc6`**. D240 (b), decidida por la PM. D239 y si «Holanda» también es 423 van a Emi.

## Corrido por la PM (2026-11-13, 20:38–20:55 UTC, worktree descartable en `a2c6dc6`)

- `git diff 6fbfefd a2c6dc6 --stat` fuera de `docs/pm`: `maria_generator.py` (sale
  `"NL": 434` de `PAISES_INDEC`; queda `"NL": 423` en la línea 129), `paises_maria.js`
  (`"NL"` y `"NLD"` de 434 a 423 en `ALIASES`), `tests/test_catalogo3.py`, `CHANGELOG.md`.
  Ningún otro `434`, `"NL"` ni `HOLANDA` en `proyecto_maria` fuera de esas tablas (grep).
- `chequeo-6.py 6fbfefd a2c6dc6`: igual al informe (producto +2/−2, arnés +25/−4,
  historia vacía, avisos: 0).
- `pytest tests/test_catalogo3.py`: `108 passed`.
- Rojo: el producto de `6fbfefd` sobre las pruebas de `a2c6dc6`: `2 failed, 106 passed`
  (`test_la_tabla_de_paises_no_tiene_claves_repetidas`, `test_paises_bajos_es_423_y_holanda_434`).
- `e2e_maria.sh` sobre `a2c6dc6`: `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.`
  Mi rama (`6887343`) no cambia producto respecto de `6fbfefd`: la unión es el mismo producto.
- Las 8 pruebas que nombran la tabla de países, los lectores o `CARTPAYORI`
  (`test_catalogo3`, `test_catalogo_largo2`, `test_country_catalog_frontend`,
  `test_generar_maria_txt`, `test_maria1a_lectura_factura`, `test_maria3_antes_de_generar`,
  `test_ncm_batch_frontend`, `test_punta_a_punta1`): `425 passed, 2 xfailed`.
- Suite entera sobre `a2c6dc6` (20:50–21:09 UTC, sqlite, `ENVIRONMENT=test`, dólar local,
  `GEMINI_API_KEY` vacía): `6131 passed, 110 skipped, 3 xfailed`, igual a la de la Dev.

### Mis ejemplos, no dados a la Dev

Por `codigo_de_pais`, catálogo (`origen_para_catalogo` + `get_pais_codigo`), exportación
y los dos lectores, antes (`6fbfefd`) y ahora (`a2c6dc6`):

| escrito | antes | ahora |
|---|---|---|
| «Nl», «nL», « NL », «\xa0nl\xa0», «NLD » | 434 en los cinco caminos | 423 en los cinco |
| «Paises bajos», «PAÍSES BAJOS», «paises  bajos» | 423 (los lectores guardan el texto) | 423 (los lectores guardan «NL») |
| «434», «0434», «434 · HOLANDA» | 434 | 434 (el lector de despachos con «434» o «434 · HOLANDA»: sin origen, D239) |
| «Holland», «Netherlands», «N.L.» | sin reconocer; catálogo lo rechaza | igual (D240) |

La pantalla (`_resolve_de_la_pantalla` de `tests/test_catalogo3.py`, con node) da lo
mismo que el servidor para todas esas formas, antes y ahora.

Generador directo (`_gen`), dos productos en el mismo grupo:

| par | `6fbfefd` | `a2c6dc6` |
|---|---|---|
| «NL» + «HOLANDA», «NL» + «434» | genera 434 | **error** «Grupo g: todos los ítems deben tener el mismo origen» |
| «NL» + «Países Bajos» | error (el mismo) | genera 423 |
| «nld» + «NL» | genera 434 | genera 423 |
| «HOLANDA» + «434» | genera 434 | genera 434 |

Lector de despachos con el formato de las pruebas («NNN NOMBRE»), `origen_iso2`:

| escrito | `6fbfefd` | `a2c6dc6` |
|---|---|---|
| «434 HOLANDA» | «NL» (genera 434 hoy, 423 después de publicar) | «HOLANDA» (434) |
| «423 HOLANDA» | «NL» | `None`, con aviso |
| «434 · HOLANDA» | «NL» | `None`, con aviso |

Es la consecuencia con camino real: **todo renglón ya importado de un despacho
«434 HOLANDA» quedó guardado como «NL» y genera 423 al publicar.** Lo nuevo
que se importe así guarda «HOLANDA» y sigue en 434.

Despachos: las pruebas y los guiones traen el origen como código y nombre
(«310 CHINA», «203 BRASIL», «999 ATLANTIDA»); ninguno trae un código solo. No
encontré un camino de hoy para el «434» solo de D239: se le pregunta a Emi.

## Adversario (Sonnet alto, contexto nuevo, sin red)

Lo lancé porque la pieza cambia qué código queda guardado. Cuatro hallazgos:

1. **Nuevo y reproducido por mí.** El lector de despachos, con un código sin sigla
   de dos letras y un nombre de otro país, guarda el nombre sin avisar.
   `origen_iso2`, antes → ahora: «434 BELGICA» `None` → `BE`, «434 CHINA» `None` →
   `CN`, «434 PAISES BAJOS» `None` → `NL`; «423 BELGICA» `BE` → `None`. El hueco ya
   existía para los 115 códigos sin sigla; la pieza mueve 434 adentro y saca 423.
   Pide un despacho con código y nombre contradictorios: no vi ninguno. Sin camino
   de hoy, es riesgo y va con D239.
2. Lo ya guardado cambia sin tocarlo («NL» de 434 a 423; grupos «NL» + «434»
   frenan): es el punto 5 del informe y la tabla de grupos de arriba.
3. «434 · HOLANDA» en el lector de despachos queda sin origen (antes «NL»): es D239.
4. Las formas en inglés: igual que antes, D240.

No encontró claves repetidas, desfase entre servidor y pantalla ni otro mapa de
países.

Visto de paso, ya estaba antes y no es de la pieza: en la exportación,
`maria_generator_export.get_pais_codigo` da 212 (EE. UU.) para un país que no
reconoce, como dice su docstring; `pais_reconocido()` es el que avisa.

## No corrido por la PM

Las 34 pantallas, los cuatro
rojos por mitades y los dos sabotajes del informe, `smoke_friccion.sh`, `anclas_perdidas.py`.
La tabla de lo que queda guardado, lo que guarda la pantalla escrito a mano y el volcado
de 2.515 formas son medición de la Dev; no los repetí.
Tampoco conté en producción cuántos «NL», «NLD» o «434» hay guardados (no toco producción).
