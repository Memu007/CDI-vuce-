# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

**COBRO-MP-2+3 (vuelta 3), PERMISOS-1 y BACKUP-1a:** el producto y las pruebas están en `ca84c5f`, y los sabotajes de permisos y de la copia ya dieron rojo. Los de cobro todavía corren en este contenedor: el informe entero va en el próximo commit, apenas terminen. Mientras tanto entrego EXCEL-2c, que ya está completa.

## EXCEL-2c, entregada en `c2b84f1` (informe en el commit de arriba)

Base: `a87b4f7`. Encima hay un merge de tu rama (`985e1e2`, trae `0bc9a62`, sólo `docs/pm`).

### Resultado

- **Qué cambia:** antes de leer un `.xlsx` liviano, se mide la forma del libro. Si pasa un tope, va al carril pesado. No se rechaza por eso.
- **Qué se mide:**
  - la fila y la columna máximas de la primera hoja: por el `r` de las celdas y de las filas, contando también las filas y celdas sin `r`, y por la `<dimension>`;
  - los elementos de `styles.xml`;
  - los elementos del `sst`.
- **Topes por defecto:**
  - `EXCEL_LIVIANO_FILAS` 20000;
  - `EXCEL_LIVIANO_COLUMNAS` 64;
  - `EXCEL_LIVIANO_ESTILOS` 5000;
  - `EXCEL_LIVIANO_TEXTOS` 40000.
- **Topes que no sirven:** un tope que no sirve (`0`, `-3`, `0.5`, `inf`, `nan`, `x`…) vale el de defecto.
- **Lo que no se lee:** una referencia que no se lee (`r="x"`, `r="inf"`, `1A`) manda el libro al carril pesado, y la lectura dice si sirve.
- **El rechazo de más de 256 columnas** ahora cuenta también las celdas sin `r`. Una `<dimension>` A1:XFD1048576 no rechaza: va al carril pesado.
- **Costo:** medir un libro de 10.1 MB tarda 1.27 s, contra 1.14 s antes.
- **Archivos de producto:**
  - `proyecto_maria/security/file_security.py`;
  - `CHANGELOG.md`.

**producto +53/−29**. Suma 24 netas: la medida nueva de la hoja (`_medida_hoja`) no sale restando código. El conteo reusa `_mas_elementos_que` y `tope_de_entorno`.

### Decisiones

**D122. Un `formatCode` de `numFmt` con muchos «[» traba un hilo.** Es de antes de EXCEL-2c y está fuera de la tarea.
- openpyxl revisa si el formato es de fecha. Esa revisión es cuadrática y retiene el GIL.
- Lo que medí yo:

| «[» | Tiempo |
|---|---|
| 5000 | 0.015 s |
| 20000 | 0.23 s |
| 40000 | 0.955 s |

- Lo que midió el adversario:
  - 120 000 «[» en un zip de 5223 B dan 200 a los 8.97 s;
  - otro hilo queda parado 8.92 s.
- Opciones:
  - (a) Una pieza nueva que ponga tope al largo de `formatCode` antes de abrir; si lo pasa, rechazar o mandar al carril pesado.
  - (b) Dejarlo como riesgo.
- Recomiendo (a). El carril pesado no alcanza solo, porque el GIL frena a todos los hilos.

### Sabotajes

Corrieron sobre `2009d41`. Entre `2009d41` y `c2b84f1` sólo cambia un docstring (`git diff 2009d41 c2b84f1 --stat` da `file_security.py | 3 ++-`).

| Script | ROJO | Fallas | Salida |
|---|---|---|---|
| `excel2c.sh` | 16 de 16 | `sabotajes con falla: 0` | `salida excel2c 0` |
| `excel2.sh` | 41 | `sabotajes con falla: 1` | `salida excel2 1` |
| `excel2b.sh` | 37 | `sabotajes sin rojo: 0` | `salida excel2b 0` |

**La falla de `excel2.sh` no es de esta pieza:**

```
ROTO  | una combinada vuelve a recorrerse hasta su última fila (la función de 3e6e63e): el sabotaje no encontró su patrón
```

- El patrón es el bucle de `_rellenar_combinadas` en `proyecto_maria/main.py`.
- `522e082` (EXCEL-3b, 2026-10-25) le agregó líneas en el medio, y ese commit ya está en la base `a87b4f7`.
- Esta pieza no toca `main.py`.
- No lo corrí sobre `a87b4f7`; lo digo por código.
- No lo arreglo: es el script de otra pieza.

Los 16 de `excel2c.sh`:

```
ROJO  | una fila lejana vuelve a quedar en el carril liviano: dice «FAILED tests/test_excel2c.py::test_la_forma_del_libro_decide_el_carril[fila con r]» (2 s)
ROJO  | el tope de filas vuelve a no leerse del entorno: dice «FAILED tests/test_excel2c.py::test_el_tope_se_lee_del_entorno[EXCEL_LIVIANO_FILAS]» (2 s)
ROJO  | muchas columnas vuelven a quedar en el carril liviano: dice «FAILED tests/test_excel2c.py::test_la_forma_del_libro_decide_el_carril[columna con r]» (3 s)
ROJO  | muchos estilos vuelven a quedar en el carril liviano: dice «FAILED tests/test_excel2c.py::test_muchos_estilos_van_al_carril_pesado» (2 s)
ROJO  | muchos textos vuelven a quedar en el carril liviano: dice «FAILED tests/test_excel2c.py::test_muchos_textos_van_al_carril_pesado» (2 s)
ROJO  | un libro caro vuelve a leerse en los hilos livianos: dice «FAILED tests/test_excel2c.py::test_la_subida_con_una_fila_lejana_lee_en_los_hilos_pesados» (2 s)
ROJO  | las filas sin r vuelven a no contar: dice «FAILED tests/test_excel2c.py::test_la_forma_del_libro_decide_el_carril[filas sin r]» (3 s)
ROJO  | la fila de una celda con r vuelve a no contar: dice «FAILED tests/test_excel2c.py::test_la_forma_del_libro_decide_el_carril[celda con r en una fila sin r]» (2 s)
ROJO  | las celdas sin r vuelven a no contar: dice «FAILED tests/test_excel2c.py::test_la_forma_del_libro_decide_el_carril[celdas sin r]» (2 s)
ROJO  | las celdas sin r vuelven a seguir la cuenta de la fila anterior: dice «FAILED tests/test_excel2c.py::test_la_forma_del_libro_decide_el_carril[celdas sin r]» (2 s)
ROJO  | la dimension vuelve a no contar las filas: dice «FAILED tests/test_excel2c.py::test_la_forma_del_libro_decide_el_carril[dimension alta]» (3 s)
ROJO  | la dimension vuelve a no contar las columnas: dice «FAILED tests/test_excel2c.py::test_la_forma_del_libro_decide_el_carril[dimension ancha]» (2 s)
ROJO  | la dimension ancha vuelve a rechazar el libro: dice «FAILED tests/test_excel2c.py::test_la_dimension_ancha_no_rechaza_el_libro» (2 s)
ROJO  | una referencia que no se lee vuelve a quedar en el carril liviano: dice «FAILED tests/test_excel2c.py::test_una_referencia_que_no_se_lee_va_al_carril_pesado[fila]» (2 s)
ROJO  | una fila infinita vuelve a cortar la validación: dice «FAILED tests/test_excel2c.py::test_una_referencia_que_no_se_lee_va_al_carril_pesado[fila infinita]» (2 s)
ROJO  | una fila que no se lee vuelve a seguir la cuenta de columnas de la anterior: dice «FAILED tests/test_excel2c.py::test_una_referencia_que_no_se_lee_va_al_carril_pesado[fila que no se lee empieza en la columna 1]» (2 s)
```

### Pruebas

- **`tests/test_excel2c.py`** sobre `c2b84f1`: `54 passed in 1.03s`.
- **Suites de Excel y de rendimiento** sobre el árbol de `2009d41`: `1429 passed in 119.81s`.
- La suite completa no corrió.

### chequeo-6

```
chequeo-6 a87b4f7..c2b84f1: avisos para mirar, no un veredicto
producto +53/−29
  AVISO producto suma 24 líneas netas: el informe dice por qué (§6: más de 20)
arnés +323/−20
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/security/file_security.py: 691 → 715
avisos: 1
```

El AVISO tiene su porqué arriba, en «Resultado».

### Revisiones

**Adversario: `adversario-opus-alto` (Opus, esfuerzo alto).**

| # | Hallazgo | Severidad | Qué pasó |
|---|---|---|---|
| 1 | `numFmt` con muchos «[»: cuadrático y con GIL | Alta, de antes | Lo reproduje. Va como D122 |
| 2 | `mergeCells` en 4998 filas: 10.95 s, contra 0.80 s sin combinadas | Media, de antes | Riesgo |
| 3 | `sqref` de 640 000 rangos en formato condicional: 3.68 s en el carril liviano | Media, de antes | Riesgo |
| 4 | Una `<dimension>` A1:XFD1048576 va al carril pesado aunque se lee en 0.01 s | Baja | La tarea pide medirla. Supuesto |
| 5 | `r="inf"` daba `OverflowError` y un 400 | Baja, mía | Arreglado en `fc4cac6`. Rojo: `E   OverflowError: cannot convert float infinity to integer` / `1 failed, 3 passed, 49 deselected` |

**`/code-review high`** (Opus 5.5, esfuerzo alto): 10 hallazgos; el agente reprodujo sólo el 1.

| # | Hallazgo | Qué pasó |
|---|---|---|
| 1 | Una fila que no se lee no ponía la columna en 0 | Arreglado en `5bd4347`, con su rojo |
| 2 | La prueba del tope que no sirve usaba el mismo libro para cada variable | Arreglado: un libro por tope |
| 3 | iterparse: 1.7 M de `<row/>` en ~10 MB usan ~197 MB de memoria | Riesgo |
| 4 | Un `.xls` no se mide | Riesgo |
| 5 | `styles.xml` se cuenta dos veces, contra topes distintos | Queda: la segunda pasada corta en 5000 |
| 6 | La `<dimension>` cuenta aunque leerla sea barato | Supuesto (el 4 del adversario) |
| 7 | La prueba de punta a punta no miraba el status | Arreglado: pide 200 |
| 8 | Docstrings que no decían que se devuelve el carril | Arreglado, el último en `c2b84f1` |
| 9 | Faltaban paréntesis en la expresión de `caro` | Arreglado |
| 10 | `import math` repetido | Arreglado |

**Seguridad: `adversario-sonnet-alto` (Sonnet, esfuerzo alto).** Ningún hallazgo con confianza de 8 o más.
- **XXE:** `_sin_dtd` corre antes de medir, con el mismo ElementTree.
- **Nombres de partes:** sólo se usan como claves del zip.
- **Rechazo de más de 256 columnas:** cubre más que antes.
- **Excepciones:** se atrapan.
- **Topes:** salen de `tope_de_entorno`.
- **Qué no hizo:** no corrió el flujo HTTP entero ni miró el mensaje al cliente ante un `ParseError`.

### Riesgos y supuestos

- **Riesgos:**
  - el 3 del code-review (la memoria de iterparse);
  - el 4 (`.xls`);
  - `mergeCells`;
  - `sqref`.
- **Supuestos que se pueden revertir:**
  - las celdas sin `r` cuentan para las 256 columnas;
  - una referencia que no se lee va al carril pesado;
  - la `<dimension>` cuenta.

### Para reproducir

```bash
scripts/testing/sabotajes/excel2c.sh c2b84f1   # 16 ROJO, «sabotajes con falla: 0»
DATABASE_URL=sqlite+aiosqlite:///./rep.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
  python -m pytest -q --no-cov tests/test_excel2c.py    # «54 passed»
docs/pm/herramientas/chequeo-6.py a87b4f7 c2b84f1       # «producto +53/−29», «avisos: 1»
```

/compact conservar: Dev 1, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM) con send_message priority next. EXCEL-2c entregada en c2b84f1 (D122 abierta: tope a formatCode). Falta el informe de COBRO-MP-2+3, PERMISOS-1 y BACKUP-1a en ca84c5f: esperan los sabotajes de cobro_mp2.sh y cobro_mp3.sh. Abiertas D119 (b), D120 (b), D121 (a). Frenar 2026-11-08 15:50 UTC. Reglas de Emi: sólo la PM y Emi me piden, nada se publica sin su «dale» para el SHA, nunca main, sin secretos.
