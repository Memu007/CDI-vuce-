# Reproducción de RENDIMIENTO-1d — 2026-11-05

Entrega: rama `claude/dev-maria`, producto hasta `aaed661`, informe `3956cb7`.
Base `f5d227c`. Worktree de PM `/tmp/cdi-pm/wr1d` en `aaed661`.

**Veredicto: devolución corta, por una causa.** Lo que vuelve del proceso
aparte se pierde según cómo se escribe: un carácter que no se puede codificar
hace que el hijo termine con error y la app se queda sin el resultado. Antes
de la pieza, el texto no salía del hilo y no se perdía.

## Lo que corrí yo (salida exacta)

Subida a `/upload_pdf/public` con un PDF de 1 hoja cuyo mapa de caracteres
devuelve un `\ud800` suelto (PDF del adversario, `surr.pdf`), y el mismo
pedido con un PDF normal:

```
# aaed661
normal (200, 'ACME TRADING CO LTD')
surrogate (200, None)
# f5d227c (base)
normal (200, 'ACME TRADING CO LTD')
surrogate (200, 'ACME TRADING CO LTD')
```

La causa está en `despacho_lector.py:810`
(`json.dumps(resultado, ensure_ascii=False)` al `stdout` del hijo): con un
surrogate suelto da `UnicodeEncodeError`, el hijo sale con 1 y la app lo traga.

## Lo que encontró el adversario (Sonnet alto)

Sin hallazgo alto. Además de la causa de arriba (reproducida por mí):

- El tope de 64 K funciona, pero ningún caso lo distingue: la bomba de texto
  del caso corta antes por memoria o CPU. Sacar el recorte o ponerlo en 64 MB
  pasa 12 de 12. Un PDF de 891 bytes con 120 líneas de 1000 «A» devuelve
  65536 con el tope y 120120 sin él.
- Soltar la fila por usuario no lo ve ningún caso: con `finally: pass` pasan
  12 de 12; con dos pedidos del mismo usuario a la vez el segundo da
  `SinLugar` y pierde el vendedor. Sacar `del filas[clave]` tampoco se nota.
- Cancelar, vencer y fallar al lanzar el hijo dejan todo limpio (probado).
- Sin otro camino que lea el PDF en la app (fuera de `fitz`, ya sabido); sin
  ReDoS útil; las fallas del hijo dan 200 con vendedor vacío, nunca 500.
- 9 de las demás mutaciones dan rojo.

## No corrido por mí todavía

- `test_rendimiento1d.py`, los tres sabotajes, chequeo-6 y la suite sobre
  `aaed661`: en cola detrás de la reproducción de `ca87d82`
  (`$S/r1d.sh` → `$S/r1d.txt`). Van con la vuelta.
