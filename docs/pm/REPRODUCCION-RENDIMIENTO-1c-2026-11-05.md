# RENDIMIENTO-1c: reproducción de la PM (2026-11-05)

Producto `3f0ed57`. Commits de la pieza: ccf5d8c, 033cb11, 843cc08, 7dd008f,
9fd6bd0, a341966, a4d2310, 5819029 y 3f0ed57. Base `ccf5d8c^`, que ya incluye
DESPACHO-1b vuelta 4. Revisión con subagente adversarial (Opus, alto) y
confirmación de la PM.

## Lo que se sostiene

- Rojo antes: `-k infla` con el producto de `ccf5d8c^` da `la app creció 1031 MB`.
  Con `3f0ed57`, `'crecio_mb': 0`, y las dos bombas dan
  `[400, 'El PDF es demasiado pesado…']`.
- `rendimiento1c.sh 3f0ed57`: 13 ROJO, «sabotajes con falla: 0», `SALIDA r1c 0`.
- `rendimiento1.sh 3f0ed57`: 11 ROJO, «sabotajes con falla: 0», `SALIDA r1 0`.
- Suite con el comando y el env de `ci.yml`, worktree limpio en `3f0ed57`:
  `4510 passed, 102 skipped, 10 deselected, 2 xfailed, 93 warnings in 702.81s`,
  sale con 0.
- `chequeo-6.py ccf5d8c^ 3f0ed57`: igual al informe, 9 avisos. 6 son de
  DESPACHO-1b y 3 de esta pieza (73 líneas netas propias y dos docstrings de
  `despacho_lector.py:683` y `:764`).
- Tiempo vencido y cancelación dejan el cupo de vuelta, sin hijo vivo ni
  zombi. Si el cliente corta la conexión, el lugar queda ocupado hasta que el
  hijo termina (≤ 30 s) y después se libera.
- Las dos subidas de PDF (`main.py:4325`, `:8378`) pasan `clave=`; ninguna
  abre el PDF antes de validar.

## La causa de la devolución (confirmada por la PM)

`validar_pdf_aparte` le da al hijo sólo el tiempo que sobró de la espera
(`max(hasta - loop.time(), 0.0)`), y `_leer_aparte` marca `lanzado = True`
apenas consigue el lugar. Si la espera se comió casi todo el tiempo, el hijo
corre con unos milisegundos, vence y sale un `TimeoutError` común: 400 «tardó
demasiado. Probá con otro archivo.». Es justamente lo que `5819029` decía
haber sacado.

Sonda `scratchpad/r1c/probes/borde.py`: dos usuarios ocupan los dos lugares
con validaciones que terminan 80 ms antes del tope; después C sube un PDF
normal. Corrida por la PM sobre `3f0ed57`, con tope de 2 s:

```
ocupantes: [{'encriptado': False, 'paginas': 1}, {'encriptado': False, 'paginas': 1}]
C: (400, 'No pudimos abrir el PDF: tardó demasiado. Probá con otro archivo.')
```

El revisor lo vio también con el tope de 30 s (30,6 s) y en 3 de 3 corridas
con 2 s.

## D50: la premisa de (a) no se sostiene

No hay límite por cuenta antes de validar:
- `rate_limit.py:68` limita por IP;
- `config.py:28` pone 3000 pedidos por minuto;
- `enforce_pdf_quota` (`main.py:4336`) corre después de validar.

Producción corre con 1 worker y 1 réplica. Por eso los 2 lugares son de todo
el sitio.

## D49 medido (sobre la función, sin Gemini)

| PDF | Validación aparte | `extraer_texto_pdf_seguro` en la app |
|---|---|---|
| hojas repetidas ×20 | 20 páginas | +130 MB, 0,8 s |
| hojas repetidas ×30 | 30 páginas | +180 MB, 1,0 s |
| Form XObject, 20 000 `Do` (1 KB) | 1 página | 111 s, 47 MB de texto, +119 MB |

El tiempo máximo del vendedor (15 s) suelta el pedido, pero el hilo sigue
ocupando uno de los 4 lugares de `_pool_lectura_pdf`.

## No corrido

- el endpoint de factura con Gemini real;
- la imagen Docker;
- SIGKILL al worker;
- la carga sostenida de D50 con dos cuentas.
