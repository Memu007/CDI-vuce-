# Dev 2 → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## MARIA-1c — entregada: lo que no se pudo leer se avisa

| Qué | SHA |
|---|---|
| Base (MARIA-2b aceptada) | `c3bef51` |
| Producto | `73621ed`, `0e56cc5` |
| Pruebas, sabotajes, comprobación de pantalla y captura | `0c07258`, `533ad3f`, `af5f85a`, `448b54d` |
| **SHA que se entrega** | **`448b54d`** |

**Resultado: terminada.**

1. **El lector marca lo que la factura traía y no pudo leer.** Lo guarda en
   `operacion.campos_sin_leer`, en las dos copias. Cubre:
   - el flete y el seguro;
   - también el país del vendedor, porque es otro valor de la operación que
     antes quedaba vacío sin aviso.

   No se marca lo que no estaba en la factura, lo vacío, lo que se leyó ni
   «N/A» en el país.
2. **La pantalla lo nombra:**
   - **Al subir:** aviso «Revisá la factura · No pudimos leer el flete de la
     factura: completalo.». Se muestra al final de la subida, para que otro
     aviso no lo tape.
   - **Antes de generar:** el semáforo, que está a la vista en revisión, NCM y
     validación, lo lista como advertencia.
   - **Cuándo se apaga:** cuando la persona escribe un valor en ese campo, 0
     incluido («flete incluido»). Si lo borra, el aviso vuelve. La lista del
     lector no se toca: la pantalla anota aparte qué completó la persona.
3. **La pantalla vieja (`static/app.js`)** ya no repone cantidad 1, origen
   `CN` ni país del vendedor `CN`; manda lo que hay. Con cantidad y origen
   vacíos, `/generate_maria` responde 400 con «Cantidad inválida» y «Falta
   origen», y la pantalla vieja lo muestra; lo verificó el revisor. El país del
   vendedor va más allá de la línea que citaste, pero es el mismo defecto y
   lo marcó el `/code-review`: lo podés rechazar.

Los dos archivos reales: el generador del TXT no se tocó, y sus pruebas están
dentro de la suite.

## Decisiones

**D9. Levantar la app local llama a ARCA de verdad.** El panel «Novedades
ARCA» del tablero (`core/arca_news.py`) busca en
`servicioscf.afip.gob.ar` cada vez que se abre el tablero. La herramienta
`levantar.sh` no lo apaga. Lo vi en el proxy durante mis comprobaciones de
pantalla, y el proxy rechazó la conexión. Ninguna prueba de pytest lo hace.
Toca el límite de «nada contra terceros desde las pruebas».
- (a) Que `levantar.sh` agregue al `.env`
  `ARCA_NOVEDADES_XML_URL=http://127.0.0.1:9/x` y
  `ARCA_NOVEDADES_WEB_URL=http://127.0.0.1:9/x`. Una línea en tu
  herramienta. **Recomiendo (a).**
- (b) Un modo simulado en `arca_news.py`, como los de VUCE y Tarifar. Sería
  una pieza aparte.

Nada más para decidir. Supuesto que podés rechazar: el país del vendedor (en
el lector y en la pantalla vieja).

## Evidencia

**Rojo antes:** con el producto de `c3bef51`, `13 failed`: 12 por
`KeyError: 'campos_sin_leer'` y 1 porque la pantalla vieja tenía `|| 1`. La
comprobación de pantalla, contra mi primera versión (`0c07258`), falla en
`FALLA: completar el flete con 0 no apaga su aviso`: distingue el defecto que
encontraron los revisores.

| Puerta (sobre `448b54d`, worktree limpio) | Resultado |
|---|---|
| Suite completa | `804 passed, 102 skipped, 24 warnings in 58.43s`, 0 failed |
| `tests/test_maria1c_avisos_lectura.py` | `13 passed` |
| `compileall` | ok |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| `scripts/testing/pantalla_maria1c.js` (Chromium local, subida simulada) | `OK aviso de la subida` / `OK semáforo con flete y seguro` / `OK flete en 0 apaga su aviso; el seguro sigue` / `OK borrar el flete lo vuelve a avisar` / `OK: pantalla MARIA-1c` |
| `sabotaje_maria1c.sh` / `2b` / `2` / `1a` | `OK: los 4 …` / `OK: los 6 …` / `OK: los 8 …` / `OK: los 10 …` |
| Captura | `docs/pm/capturas/maria1c-aviso.png` |

**Autorrevisión** (adversario Sonnet medio, que probó la app local con
Playwright, más `/code-review high`). Arreglados, cada uno con su
comprobación:
- el 0 no apagaba el aviso;
- escribir algo y borrarlo lo apagaba;
- si el semáforo respondía con error o se editaba muy seguido, los avisos
  quedaban viejos;
- el aviso de la subida quedaba tapado y no tenía estilo de advertencia;
- la pantalla vieja reponía el país del vendedor;
- el script de pantalla usaba esperas fijas y no verificaba nada.

Quedan como riesgos bajos, fuera de alcance:
- se marcan flete «N/A», «-» o «incluido», y países escritos de una manera
  que una persona entiende («United States», «Hong Kong»). Se pide completar,
  y ahora 0 apaga el aviso;
- una operación guardada antes de este cambio no trae la marca;
- la pantalla vieja dice «Origen no especificado (se acepta igual)» antes de
  un 400 por falta de origen.

## Para reproducir

```bash
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh 448b54d 8080
<venv>/bin/python -m pytest -q --no-cov tests/test_maria1c_avisos_lectura.py      # 13 passed
BASE_URL=http://127.0.0.1:8080 node scripts/testing/pantalla_maria1c.js <un-pdf> # «OK: pantalla MARIA-1c»
VENV=<venv> scripts/testing/sabotaje_maria1c.sh 448b54d                            # «OK: los 4 …»
```

## No corrido

- Facturas reales con Gemini real (prohibido).
- La pantalla vieja en el navegador: la verificó el revisor por HTTP. La
  prueba es sobre su código.
- `ataque_aislamiento.sh`: la pieza no toca sesión ni permisos.

Sigo con MARIA-4.

Última vuelta: 2026-10-07 06:20 UTC
Contexto: ~62 % (pasado el umbral; compactar cuando Emi pueda)
