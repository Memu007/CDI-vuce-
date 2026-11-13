# Reproducción de DESPACHO-1b + D41, vuelta (2026-10-28)

Entrega de MARIA: informe en `PARA-PM-2.md` («DESPACHO-1b + D41
(devolución): entregada en 09e16f3»). Producto `5508317`, `aabf3e5`,
`bf9f3d8`; pruebas `bcd2eaf`, `6357d25`, `09e16f3`. Es la vuelta de la
devolución sobre `e59e1a8`.

La PM corrió con pypdf 6.21.2 (el venv tenía 6.19.0; la entrega exige
`pypdf>=6.21.2`).

## Lo que corrió la PM

- `despacho1b.sh` sobre `09e16f3`: 30 ROJO, «sabotajes sin rojo: 0», salida 0
  (igual que el informe).
- PDFs armados por la PM (texto chico que se multiplica al decodificar), por
  `leer_despacho_aparte`:

  | PDF | Pico del hijo | Resultado |
  |---|---|---|
  | b10x70, 716 KB | 55 MB | páginas salteadas con aviso |
  | b2x70 | 53 MB | páginas salteadas con aviso |
  | b200x7, 1,48 MB | 230 MB | `PdfDemasiadoPesado` a los 0,9 s |

  El proceso de la app no crece: el hijo tiene tope de 256 MB y se corta.
  El pico de b200x7 se acumula en la caché de decodificación de pypdf
  dentro del hijo; queda debajo del tope y la app no lo paga.
- Punto 2 de la devolución: el lector ya no usa el pool de hilos
  compartido; leer un despacho no frena las facturas.
- Punto 4: `_incr_avg` con el promedio anterior vacío toma el valor nuevo.
- Punto 5: dos NCM distintos ya no se fusionan (`solo_mismo_ncm=True` en el
  guardado del despacho).

## D48, reproducida por la PM (preexistente, no es de esta pieza)

`validate_file_upload` abre cada PDF dentro del proceso de la app, sin tope
de memoria (`_abrir_pdf`, `file_security.py`; en `main` 8b45207 por
`asyncio.to_thread`). Una página pesada repetida en `/Kids`:

| Repeticiones | Tamaño | Tiempo | Pico |
|---|---|---|---|
| 10 | 956 KB | 1,0 s | 136 MB |
| 100 | 956 KB | 3,2 s | 586 MB |
| 200 | 957 KB | 8,6 s | 1086 MB |

Está en producción desde RENDIMIENTO-1 (`989c175`) y la alcanzan las
llamadas de `validate_file_upload` en `main.py` (8b45207) 3970, 5948, 7495
y 8580.

## Adversario (Sonnet alto, contexto nuevo)

Lo marcado «PM» lo corrió la PM con los scripts del adversario sobre una
copia de `09e16f3` (pypdf 6.21.2); lo demás es del adversario.

1. **Alta = D48, confirmada.** Diez bombas en paralelo por el endpoint
   (`main.py:8212` valida antes del lector topeado): la app llegó a 5446 MB
   y una subida normal pasó de 0,51 s a 9,08 s.
2. **Media, PM: un PDF de 49 KB ocupa un lugar del lector 23,5 s.** 20 hojas
   que comparten un contenido de 500 KB con unas 14 000 operaciones de texto:

   ```
   rc 0 seg 23.5 maxrss_MB 76 out_bytes 161
   ops_compartidos [20, 500] pdf_bytes 49231
   ```

   Con `_HIJOS_A_LA_VEZ = 2`, dos de esos pedidos y uno normal de otro
   usuario (tope 5 s):

   ```
   A,B,C -> ['TimeoutError', 'TimeoutError', 'TimeoutError'] 10.0s
   hijos vivos tras timeouts: []
   ```

   El tope mide bytes por hoja, no trabajo. El adversario extrapola unos
   240 s para 200 hojas (no corrido). El límite de pedidos es 3000 por
   minuto (`config.py:28`).
3. **Media, PM: el mismo NCM con texto largo igual se funde.** `_norm_desc`
   corta en 200 caracteres (`client_memory.py:36`): dos renglones con el
   mismo comienzo de 275 caracteres quedan en una fila, `veces_usado` 2,
   peso 25,5 (mezcla de 1 y 50).
4. **Media, PM, preexistente: `learn` guarda `inf`.** Después, el GET del
   catálogo da 500 (`ValueError: Out of range float values are not JSON
   compliant: inf`) y la fila queda así.
5. **Baja-media, PM: el promedio cuenta los usos sin valor.** Sin valor,
   después (2, 3), después (4, 6): queda `veces_usado` 3, peso 2,67 y valor
   4,0, en vez de 3 y 4,5. `client_service.py:371` tiene la misma cuenta.
6. **Baja, PM: el NCM con puntos no se une.** «8471.49.00», «84714900» y
   «8471.4900» quedan en tres filas. Es regresión de `solo_mismo_ncm`.
7. **Baja, PM: un `\ud800` suelto en el JSON de guardar da 500** (`main.py`,
   «no se guardó ninguno»).
8. Informativo: el hijo carga `.env` por `pdf_extractor.py:16-18`.

Mutantes del adversario: 22 muertos, 17 vivos. Los que importan: el número
de hijos a la vez, el `except MemoryError` al abrir, los topes de pypdf
fuera de Flate, `columnas[max(k,0)]`, `_MAX_TEXTO` (la prueba lo parcha), el
borde de 500 renglones, `isinstance(resultado, dict)` y `BrokenPipe`.

No corrido por la PM: la suite completa (MARIA informa 4067 passed, 336
skipped, 2 xfailed sobre `09e16f3`), Postgres.

## Veredicto

Devolución sobre `09e16f3`. Los siete puntos de la devolución anterior
cambiaron el código, pero la causa de tres sigue: los topes acotan bytes y
memoria, no trabajo ni turnos (punto 2 del adversario); la identidad del
producto sigue dependiendo de un texto cortado y de un NCM sin normalizar
(3 y 6); y el promedio sigue contando usos sin valor (5). El detalle, la
D47 y la D48 están en `PARA-DEV-2.md`.
