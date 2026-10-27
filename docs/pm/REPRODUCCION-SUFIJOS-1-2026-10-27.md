# Reproducción de SUFIJOS-1 — 2026-10-27

Sobre `97cd2fa` (informe en `PARA-PM-2.md` de `claude/dev-maria`; base de
comparación `adfe707`). La PM corrió la suite, el sabotaje, negativos propios
y una comparación byte a byte en worktrees limpios (`/tmp/cdi-pm/wt-97cd2fa`,
`/tmp/cdi-pm/wt-adfe707`). Un revisor adversarial con contexto nuevo (Opus
alto) trabajó con base y servidor propios (`/tmp/cdi-pm/advsuf`, fuera del
repositorio). Todo local, con sintéticos, sin Gemini.

**Veredicto:** SUFIJOS-1, **con devolución**. El generador está bien: sin
sufijo propio el TXT sale idéntico al de la base, y los errores son
explícitos. Falla la pantalla: lo que viaja al TXT por producto (sufijo y
unidad estadística) no sale de lo mismo que se pinta en la celda. Con el
arancel caído en la carga, el TXT lleva sufijos y kilos que nadie vio.

## Lo que corrió la PM

| Qué | Resultado |
|---|---|
| `tests/test_sufijos1.py` sobre `97cd2fa` | `50 passed` |
| `scripts/testing/sabotaje_sufijos1.sh 97cd2fa <venv>` | «OK: los 34 sabotajes dan rojo por la razón esperada», rc=0 |
| Suite completa sobre `97cd2fa`, desde base limpia | `12 failed, 3164 passed, 102 skipped, 2 xfailed, 92 warnings in 327.89s`, rc=1 |

Los 12 rojos son los conocidos (el de `test_guardar1` y los 11 del tope de
15 operaciones): `97cd2fa` sale de `adfe707`, que no trae `2ff3262`. Ninguno
nuevo.

### Byte a byte, sin sufijo propio

El mismo pedido en `adfe707` y `97cd2fa`, SHA-1 del TXT: idénticos en los
siete casos (lona, cuatro lonas, todas las lonas, grupo sin sufijo propio,
sub-ítems, dos posiciones, y el sufijo de la operación vacío, que da el mismo
error «Falta el sufijo» en los dos).

### Negativos propios (generador, sufijo de la operación «AA(OP)-»)

| Sufijo propio | Resultado |
|---|---|
| « - » | `AA(OP)-` |
| en minúsculas | sale tal cual; el de la operación en minúsculas también, igual que en la base |
| «AA(SIN» | error «Sufijo de valor del ítem 1: … no se puede separar» |
| propio, el de la operación vacío | `AA(P)-` |
| dos enteros, uno sin propio | `AA(P)-`, `AA(OP)-` |
| grupo con sufijos distintos, o uno sin | error «Grupo 1: todos los ítems deben llevar el mismo sufijo…» |
| 122 caracteres | error «…122 caracteres…» |
| `None`, o con espacios alrededor | el de la operación; recortado |
| grupo «AA(A)-» y «AA(A)» | `AA(A)-` |

### Reproducido por la PM en Chromium (scripts del revisor)

```
=== falla1
llamadas al arancel antes de generar: 1
celdas en pantalla: [{"valor":"","nota":""},{"valor":"","nota":""},{"valor":"","nota":""}]
llamadas al arancel después de generar: 2
generado: {..."csbtsvl":["CSBTSVL=CA00-AA(Marca Demo)-AI(620G GRIS)-","CSBTSVL=CA00-AA(Marca Demo)-AI(620G NEGRA)-","CSBTSVL=CA00-"],"qsbtuntest":["QSBTUNTEST=465.00","QSBTUNTEST=10.00"]}
celdas después de generar: [{"valor":"","nota":""},{"valor":"","nota":""},{"valor":"","nota":""}]
=== congela
celdas con op CA01: [{"valor":"CA01-AA(Marca Demo)-AI(620G GRIS)-",…},{"valor":"AA(Marca Demo)-CA00-AI(620G NEGRA 2)-",…},…]
generado: {..."csbtsvl":["CSBTSVL=CA01-AA(Marca Demo)-AI(620G GRIS)-","CSBTSVL=AA(Marca Demo)-CA00-AI(620G NEGRA 2)-","CSBTSVL=CA01-"],...}
```

El script del revisor espera 1500 ms fijos al entrar a la pantalla: sirve
para diagnosticar, no para declarar verde.

## Lo que probó el revisor (Opus alto)

- **Sin hallazgo:** `/api/sufijos/propuesta` pide sesión (401), limita a 500
  ítems y rechaza anidados (400), aguanta 500 ítems de 60 KB en 0,31 s, y
  sanea marcas con «=», saltos de línea, surrogates y dígitos raros.
  `supuestos_declarados` con valores raros: 360 de 360 sin excepción. El
  historial no guarda sufijos ni se regenera. No encontró un camino para que
  un producto tome la propuesta de otro.
- **Sólo lectura o node, sin impacto visto en el TXT:** `combinar` duplica
  códigos repetidos en el de la operación («AA(X)-AA(Y)-» da dos AA), toma
  «AA00» por AA y siempre agrega «-»; el BOM separa en JS y no en Python;
  un producto de 0,001 a 0,004 kg con unidad en kilos no genera, con error
  correcto.

## Hallazgos

| # | Qué | Gravedad | Qué se hace |
|---|---|---|---|
| H1 | **El TXT lleva lo que la pantalla no mostró.** Si `/api/sufijos/propuesta` falla al entrar, las celdas quedan vacías y sin nota; «Generar» vuelve a pedir y manda la propuesta y la unidad en kilos sin pintarlas (`QSBTUNTEST=465.00` en vez de 750 unidades). Lo mismo, sin aviso, con más de 500 productos. Reproducido por la PM. | plata, alta | devolución |
| H2 | **Una celda tocada congela el sufijo viejo de la operación.** Al escribir, la celda guarda el texto entero; si después cambia el de la operación, esa fila sigue con CA00 y las otras pasan a CA01, sin aviso. Reproducido por la PM. | plata, media | devolución |
| H3 | **Un sufijo escrito antes de agrupar traba el TXT** (400 «Grupo g1: todos los ítems deben llevar el mismo sufijo…») y la celda del grupo no deja corregirlo. Del revisor. | media | devolución |
| H4 | **Un sufijo que ya no se ve** (el producto pasó a sub-ítems) sigue viajando y `main.py` lo rechaza. Del revisor. | baja | devolución |
| H5 | **La propuesta reemplaza el AA/AB/AI que el despachante escribió** en el sufijo de la operación («AA(1)-CA00-» → «AA(Marca Demo)-CA00-…»), sin aviso. Está en el informe como diseño. | plata, media | decidido por la PM: gana lo escrito por la persona |
| H6 | `combinar` con códigos repetidos o «AA00», el «-» final y el BOM. | baja | se anota |

H1 a H4 tienen la misma causa: el valor que se manda por producto
(`sufijoDe`, `unidadesDe`) sale de un estado (`it.sufijo`, la clave de la
propuesta) que no es lo que la celda muestra en ese momento.

## Limpieza

Sin `uvicorn` ni `chromium` de la revisión andando al terminar. Los
ayudantes del revisor quedaron en `/tmp/cdi-pm/advsuf`, fuera del
repositorio.
