# Dev 2 → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## MARIA-4 — entregada: lo que decide el despachante sale en el TXT

| Qué | SHA |
|---|---|
| Base (MARIA-1c aceptada) | `448b54d` |
| Producto | `893f6bd` (generador y `/generate_maria`), `30aa414` (pantalla y listados), `8b6edb9` (arreglos de la revisión), `9cf109e` (CHANGELOG) |
| Pruebas, sabotajes, pantalla y captura | `5500f6e`, `e3b7b84`, `9cf109e`, `41a623e`, `b3ec171`, `6149ef3` |
| **SHA que se entrega** | **`6149ef3`** |

**Resultado: terminada.** Cambia lo que sale en el TXT, campo por campo y con
la prueba que fijaste:

| Campo | Ahora | Por defecto |
|---|---|---|
| `CARTUSO`, por producto | Se elige entre los seis estados, con los nombres del despachante (1 a 6). La tabla está en un solo lugar, `ESTADOS_MERCADERIA`, con tu nota | Origen extranjero: 2. Origen argentino: no hay. Si falta, el servidor responde 400 «Ítem N (descripción): el origen es argentino; elegí el estado…» y la pantalla no deja generar |
| `IVAADICIONAL1` | Por operación, con cambio por producto: reventa (`NO_VALIDA`) o uso particular (`IVAAD1`) | Reventa |
| `BANCOSARGENTINA` | Código BCRA de 3 dígitos, por operación. Va antes de `ARDIG-SETI-OPC`, como en el archivo de 2026 | El último banco del cliente. Si no hay, la línea no sale y hay aviso |
| `ARDIG-CUIT-PSAD` | Modoc (`PSAD06`) o Lakaut (`PSAD01`) | La última empresa del usuario. Si no hay, Modoc |

- **Supuestos:** lo que se usó por defecto entra en `supuestos_declarados`:
  el estado de cada producto, el IVA, el banco ausente y la empresa. Se suma
  el aviso de que la reducción o exclusión del IVA se elige en «Ventajas» del
  Kit. El aviso fijo «se declaró 3, siempre» se fue.
- **Pantalla v2:** en validación, antes de generar, aparece la tarjeta «Lo
  que decide el despachante»:
  - banco, empresa e IVA de la operación;
  - una tabla por producto con el estado y el cambio de IVA.

  Solo se guarda lo que la persona elige. El valor por defecto sigue al
  origen: si al volver a NCM el origen pasa a argentino, el estado se vuelve
  a pedir. La propuesta de banco y empresa es del cliente activo.
- **Dónde se guarda, sin columnas nuevas:** en la operación, dentro de
  `extra.resumen.maria`. Incluye el estado y el IVA de cada producto. Los
  listados `GET /api/clientes/{id}/operaciones` y `GET /api/operations`
  devuelven `maria`, recortado a 12 caracteres, y de ahí sale la propuesta.
  Respetan el dueño de las operaciones: el revisor lo probó con dos usuarios.

**Los dos archivos reales:**
- **2025:** sale idéntico entero, cargando estado 3, uso particular, sin banco
  y `PSAD06`.
- **2026:** salen igual que el real los cuatro campos (`2`, `NO_VALIDA`,
  `191`, `PSAD01`) y el orden banco → `ARDIG-SETI-OPC` → `ARDIG-CUIT-PSAD`.
  Los bloques de productos también salen idénticos. El resto del archivo de
  2026 nunca se comparó entero: el real viene sin el relleno de espacios.

## Decisiones

**D11. En la pantalla vieja (v1), un producto de origen argentino ya no se
puede generar.** Esa pantalla no tiene dónde elegir el estado. Recibe el 400
con el mensaje claro y no se rompe, pero no genera. Con otros orígenes genera
con los valores por defecto (2 y reventa). Tampoco muestra los supuestos.
- (a) Aceptarlo: la v1 está de salida, y el criterio 3 prohíbe inventar el
  estado. **Recomiendo (a).**
- (b) Agregar un selector de estado en la v1: una pieza aparte.

Supuesto que podés rechazar: si el banco viene propuesto (el último del
cliente) y la persona no lo toca, va al TXT y la pantalla lo dice («Banco
191: el último que usó este cliente»).

## Evidencia

**Rojo antes:** las pruebas nuevas contra el producto de `448b54d` dan
`30 failed, 2 passed`. Por ejemplo, `TypeError: generate_maria_txt() got an
unexpected keyword argument 'banco_bcra'` y `assert 200 == 400` (origen
argentino sin estado). La comprobación de pantalla contra la primera versión
(`9cf109e`) falla con `FALLA: estados: ["2","3"]`: el 2 por defecto quedaba
guardado como elegido.

| Puerta (sobre `6149ef3`, worktree limpio) | Resultado |
|---|---|
| Suite completa | `837 passed, 102 skipped, 24 warnings in 60.13s`, 0 failed |
| MARIA-4 + archivos reales + supuestos + sub-ítems | `113 passed` |
| `compileall` | ok |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| `scripts/testing/pantalla_maria4.js` | `OK estado 2 por defecto en el importado; el argentino sin estado; banco 191 propuesto` / `OK sin estado en el argentino no se genera` / `OK el pedido lleva banco 191, Lakaut, uso particular, el estado 3 elegido y el importado sin elegir` / `OK al volver y pasar a origen argentino se vuelve a pedir el estado` / `OK otro cliente: se propone su banco (014)` / `OK: pantalla MARIA-4` |
| `pantalla_maria1c.js` | `OK: pantalla MARIA-1c` |
| `sabotaje_maria4.sh` (CARTUSO 3 fijo, IVAAD1 fijo, PSAD06 fijo, sin banco, estado argentino inventado, listados sin `maria`) | `OK: los 6 sabotajes dan rojo por la razón esperada` |
| `sabotaje_maria1c` / `2b` / `2` / `1a` | `OK: los 4 …` / `OK: los 6 …` / `OK: los 8 …` / `OK: los 10 …` |
| Captura | `docs/pm/capturas/maria4-despachante.png` |

**Autorrevisión** (adversario Sonnet alto, que probó la pantalla en una API
propia, más `/code-review high`). Arreglados, cada uno con su prueba o su
paso en la comprobación de pantalla:
- el estado por defecto quedaba guardado como elegido, y al pasar el origen a
  argentino salía `CARTUSO=2`. Es el defecto que esta pieza tenía que evitar;
- el banco o la empresa propuestos de un cliente quedaban pegados al cambiar
  de cliente;
- lo elegido se perdía al volver a NCM;
- se guardaba el valor por defecto como elegido, y por eso los supuestos no
  lo avisaban;
- la propuesta se pedía de a una consulta y podía pisar lo que se escribía
  mientras tanto;
- el estado y el IVA por producto no se guardaban con la operación;
- un grupo con el mismo valor escrito de dos maneras se rechazaba;
- el mensaje de error apuntaba a la fila equivocada en los grupos; ahora
  nombra el producto;
- un banco con dígitos no latinos pasaba;
- el listado crecía sin tope con un valor sembrado;
- la pantalla trataba «ARG» como Argentina y el servidor no.

Quedan como riesgos o fuera de alcance:
- la v1 (D11);
- la tabla de estados está copiada en `despachante.js`, con una nota en el
  archivo. Unificarla pide un endpoint;
- la v2 todavía no muestra los supuestos antes de generar: eso es MARIA-3.

## Para reproducir

```bash
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh 6149ef3 8080
<venv>/bin/python -m pytest -q --no-cov tests/test_maria4_despachante.py tests/test_generar_maria_txt.py tests/test_maria_subitems.py tests/test_maria_supuestos.py   # 113 passed
BASE_URL=http://127.0.0.1:8080 node scripts/testing/pantalla_maria4.js          # «OK: pantalla MARIA-4»
VENV=<venv> scripts/testing/sabotaje_maria4.sh 6149ef3                           # «OK: los 6 …»
```

## No corrido

- La prueba en el Kit del orden de los estados: la tabla tiene la nota.
- La pantalla v1 en el navegador: el revisor la probó por HTTP.
- `ataque_aislamiento.sh`: los listados nuevos filtran por dueño. El revisor
  probó con dos usuarios: el que no es dueño recibe 404 y la lista vacía.

Sigo con MARIA-3.

Última vuelta: 2026-10-07 06:50 UTC
Contexto: ~82 % (muy pasado el umbral; compactar)
