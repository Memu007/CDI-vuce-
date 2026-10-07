# Dev 1 → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## EXCEL-1 — parcial: la parte 2 hecha, la parte 1 frenada en D13–D15

| | SHA |
|---|---|
| Base (RENDIMIENTO-1b aceptada, con tu rama traída) | `ec3606e` |
| Parte 2, producto | `3393c2f` |
| Parte 2, pruebas | `b5ddaf3` |

RENDIMIENTO-1b aceptada: gracias. Su informe está en el commit `ec3606e` de
este archivo.

### Parte 2 (tu D12): leer un Excel no frena el sitio — hecha

Leer un Excel o un CSV pasa a otro hilo, con tiempo máximo
(`EXCEL_READ_TIMEOUT_S`, 60 s), en las cinco rutas que leen uno:
`/upload_excel/`, `/upload_excel_v2/`, `/api/clientes/import`,
`/api/ncm/import-historial` y `/api/migrations/analyze`. Lo mismo la
validación del archivo al subirlo. Al vencerse el tiempo: 504
`{"detail": texto, "code": "lectura_excel_demasiado_larga"}`, y la pantalla
ofrece la carga a mano, como con el PDF.

Rojo antes (`ec3606e`) y verde después (`b5ddaf3`):

```
E   AssertionError: clientes_import: /health tardó 1.58 s mientras se leía un Excel
E   AssertionError: migraciones_analyze: /health tardó 1.52 s mientras se leía un Excel
E   AssertionError: ncm_import_historial: /health tardó 1.52 s mientras se leía un Excel
E   AssertionError: upload_excel: /health tardó 1.52 s mientras se leía un Excel
E   AssertionError: upload_excel_v2: /health tardó 1.52 s mientras se leía un Excel
E   AssertionError: /health tardó 1.51 s mientras se validaba un Excel
E   AssertionError: clientes_import: 200 {...}   assert 200 == 504     (y lo mismo en las otras 4 rutas)
→ después: 11 passed
```

Suite completa sobre `b5ddaf3`, venv nuevo armado sólo desde
`requirements.txt`: `765 passed, 102 skipped, 25 warnings in 97.18s`.
Faltan, para la entrega final: los sabotajes de esta parte, los revisores, y
humo y aislamiento.

Lo midió el auditor antes del arreglo: un .xlsx de 5 KB, con una celda en la
fila 1.048.576, congelaba el sitio 54 s.

### Parte 1: el relevamiento (un subagente Opus alto, con evidencia)

**Caminos y quién los llama:**

| Ruta | ¿La llama una pantalla? | ¿Llega al TXT? |
|---|---|---|
| `/upload_excel_v2/` | sí (v2, `upload.js`) | **sí, el único** |
| `/upload_excel/` | **no**: sólo `static/script.js` de la raíz, que no se sirve | no (devuelve un AVG .xlsx) |
| `/upload_excel/public` | sólo el dashboard viejo (`?v=1`), que muestra «No se detectaron ítems» | no |
| `/api/clientes/import` | **no** | indirecto (crea clientes que prellenan la operación) |
| `/api/migrations/analyze` | sí (v2, `clientes.js`) | indirecto; es el más sólido (valida CUIT y límites) |
| `/api/ncm/import-historial` | sí (v2, `ncm.js`) | indirecto (sugiere NCM) |

**Defectos en `/upload_excel_v2/`, con el TXT que sale** (del más grave al
menos grave):
1. **Filas perdidas sin aviso:** el TXT declara menos FOB. Se descarta
   cualquier fila sin NCM, sin origen o con un número en texto («1.234,56»,
   «10 pcs»), y no se avisa. En el ejemplo, 3 filas → 1 ítem: `MDDTFOB=3500.00`
   de una factura de 6.000. Una factura sin columna NCM da 400 entera, aunque
   v2 tiene un paso para clasificar NCM. Además, sólo lee la primera hoja.
2. **«Valor» (el total) gana sobre «Precio Unitario»:** `MARTUNITAR=3500`,
   `MDDTFOB=35000` en vez de 350 y 3500.
3. **Separador de miles leído como decimal:** «1.500» → cantidad 1,5.
4. **Peso bruto o total tomado como peso unitario neto**, y queda guardado
   en el mapeo del cliente y en su plantilla.
5. **Una fila de subtotal entra como ítem** y suma FOB (`MDDTFOB=38500`, era
   3500).
6. **NCM numérica mal leída:** con una fila vacía en el medio sale
   «84713000.0». En el historial NCM y en clientes se pierde el 0 de
   «01012100».
7. **El país se corta a 3 letras** (`models/operations.py:60`): «China» y
   «Chile» dan «CHI», «Argentina» da «ARG». El TXT lo frena con «Origen no
   reconocido».
8. **«.XLSX» en mayúsculas da 500.**
9. **Valores inventados en la operación:** la moneda queda «USD» si el
   cliente no tiene otra (`main.py`, `upload_excel_v2`); la fecha de
   emisión sale como la de hoy (`maria_generator.py:392`, también con PDF),
   sin aviso.
10. **Un mapeo guardado del cliente deja afuera encabezados nuevos**; tampoco
    se reconocen «Cant.», «Precio Unitario (USD)», «Peso Neto (kg)» ni
    «Posición Arancelaria».
11. Menores: el manejador global muestra `dev_detail` (rutas del servidor,
    SQL); `upload.js` acepta 15 MB y el servidor, 10 MB.

En `/api/clientes/import`, que no tiene llamador: inventa «Cliente
<CUIT>» cuando falta la razón social y acepta CUIT sin dígito verificador.

### Avance desde el primer parcial (sin esperar las D)

Arreglado en `/upload_excel_v2/` (producto `7e804e5`, pruebas `1df55b0`,
sabotajes en `scripts/testing/sabotajes/excel1.sh`):
- el precio unitario gana sobre «Valor» (defecto 2);
- peso neto o unitario; sin uno de ellos, el peso queda vacío en vez de
  tomar el bruto o el total, y el TXT lo frena con «Peso inválido» hasta
  que se complete (defecto 4);
- las filas de total o subtotal no entran (defecto 5);
- «.XLSX» en mayúsculas (defecto 8);
- encabezados con la unidad entre paréntesis, y el mapeo guardado del
  cliente se completa con los encabezados nuevos (defecto 10);
- la respuesta trae `filas_descartadas` y sus números de fila, y la pantalla
  avisa «N fila(s) del Excel no se pudieron leer (filas …). Revisalas y
  cargalas a mano» (el aviso del defecto 1; leer esas filas espera D14).

Rojo antes y verde después:

```
E   assert 3500.0 == 350                       (unitario sobre total)
E   assert 25.0 == 15                          (neto sobre bruto)
E   assert 25.0 in (0, None)                   (bruto o total como unitario)
E   ['Laptop 14 pulgadas', 'Subtotal 8471.30.00']   (subtotal como ítem)
E   assert 500 == 200  ... "Excel xlsx file; not supported"   (.XLSX)
E   assert 400 == 200  ... "No se pudieron extraer items"     (paréntesis; mapeo guardado)
E   assert None == 2                           (filas descartadas sin aviso)
→ después: 8 passed
```

Sabotajes de `excel1.sh`: 10 en ROJO, `sabotajes con falla: 0`. Uno de la
parte 2 primero daba verde porque mi prueba medía mal: la segunda lectura
lenta pisaba la hora de inicio de la primera. Ya está arreglada.

**La moneda «USD» inventada (defecto 9) no se arregla en el Excel:** sale
de `Client.preferred_currency`, que vale «USD» por defecto en el modelo.
No hay forma de distinguir «el cliente eligió USD» de «nadie eligió». Va
como D16.

## Decisiones

- **D13 — Rutas sin llamador vivo (tu punto 3).** `/upload_excel/` no la
  llama nada que se sirva. `/upload_excel/public` sólo la llama el dashboard
  viejo, y ahí no anda. `/api/clientes/import` no tiene llamador e inventa
  nombres de cliente.
  Opciones: (a) borrarlas en esta pieza; (b) no arreglarlas y borrarlas en
  una pieza de limpieza; (c) arreglarlas igual.
  **Recomiendo (a) para `/upload_excel/` y su alias `public`, y para
  `/api/clientes/import`.** Ninguna llega al TXT desde una pantalla, y
  borrarlas saca superficie. Así arreglo sólo `/upload_excel_v2/`. La parte
  2 ya las dejó sin frenar el sitio, por si preferís (b).
- **D14 — Las reglas de lectura de MARIA-1a están en la rama de la Dev 2.**
  Los defectos 1, 3, 6 y 7 piden su regla: el número con coma o con punto
  de miles, el país por nombre, el dato vacío con aviso. Según el auditor,
  en `claude/dev2-maria` el camino del Excel sigue con `upper()[:3]` y
  `float(...)`, así que MARIA-1a no lo cubre. Pero sus funciones existen, y
  no están en mi rama: no se integra nada hasta después del ensayo.
  Opciones: (a) traer MARIA-1a a mi rama con `merge` desde la tuya, cuando
  la integres, y usar sus funciones; (b) escribir las mías para el Excel
  (dos reglas que pueden divergir); (c) que la Dev 2 haga esos cuatro, ya que
  son de lectura.
  **Recomiendo (a).** Mientras tanto avanzo con los que no dependen de ella:
  2 (unitario sobre total), 4 (neto sobre bruto), 5 (subtotales), 8
  (mayúsculas), 10 (encabezados y mapeo), la moneda inventada del 9 y el
  aviso de filas descartadas del 1.
- **D15 — La fecha de emisión de hoy (`maria_generator.py:392`).** Afecta
  también al PDF y es del generador del TXT, que es zona de la Dev 2.
  **Recomiendo** que vaya a MARIA-1b o a la pieza de la Dev 2 que toque el
  generador. No la toco.

- **D16 — Moneda por defecto del cliente.** `Client.preferred_currency`
  vale «USD» por defecto (`models.py:141`), así que una operación por Excel
  con cliente sale siempre con moneda USD aunque nadie la haya elegido.
  Opciones: (a) migración que deje la columna sin valor por defecto, y que
  la pantalla del cliente pida la moneda; (b) dejarlo así: USD es lo común y
  el usuario la ve en la revisión.
  **Recomiendo (b) por ahora** y anotarlo para PUNTA-A-PUNTA-1: cambiarlo
  pide una migración, y la moneda se ve en pantalla antes del TXT.

Lo de `dev_detail` (el manejador global muestra detalles internos) es de
seguridad: **recomiendo** la Fase 3, junto con ABUSO-1.

## Qué no corrí

- Todavía no: sabotajes de la parte 2, revisores, humo y aislamiento. Van
  con la entrega final.
- El auditor no probó la pantalla en un navegador, ni Railway con varios
  procesos.

## Archivos de producto que toqué

`proyecto_maria/main.py` (las cinco rutas de Excel), 
`proyecto_maria/services/migration_service.py`
(`analyze_migration_file_async`), `proyecto_maria/security/file_security.py`
(validación del Excel), `proyecto_maria/static/v2/screens/upload.js` (una
condición), `CHANGELOG.md`.

## Sigo con

Espero D13, D14 y D16. Sin D14 no puedo leer las filas que hoy se descartan
(defectos 1, 3, 6 y 7). La prueba del TXT (Excel contra PDF con los datos
de los dos archivos reales) también depende de ella. Con las respuestas:
eso, la suite final, los revisores, humo y aislamiento, y la entrega.

Última vuelta: 2026-10-07 08:10 UTC
Contexto: ~60 %

`/compact conservar: Dev 1 de CDI en la rama claude/dev1-tecnica.
RENDIMIENTO-1b aceptada (ec3d793). EXCEL-1 en curso: parte 2 (leer Excel en
otro hilo con EXCEL_READ_TIMEOUT_S, 504 lectura_excel_demasiado_larga) hecha
en 3393c2f + pruebas b5ddaf3 (tests/test_excel1_rendimiento.py), suite 765
passed; faltan sabotajes (scripts/testing/sabotajes/excel1.sh), revisores,
humo y aislamiento. Parte 1: el relevamiento del auditor está en PARA-PM.md
(10 defectos en /upload_excel_v2/). D13 (borrar /upload_excel/, su alias
public y /api/clientes/import), D14 (reglas de MARIA-1a de la Dev 2) y D15
(fecha de hoy en maria_generator) abiertas. Hechos además (7e804e5, 1df55b0, excel1.sh): defectos 2, 4, 5,
8, 10 y el aviso de filas descartadas; D16 (moneda USD por defecto del
cliente) abierta. Faltan, después de D13/D14: defectos 1, 3, 6, 7, la
prueba del TXT contra el PDF, la suite final, los revisores, humo y aislamiento. Después:
MARIA-1b (con la D6 de la Dev 2) y PUNTA-A-PUNTA-1. Entorno: PM_DIR=/tmp/cdi-dev1,
levantar.sh <SHA> 8811, venv /tmp/cdi-dev1/venv y venv-limpio; sabotajes en
scripts/testing/sabotajes/. Rutina de la PM: trig_01TvMmGfSLDfbcJrf66ZZ7YK.`
