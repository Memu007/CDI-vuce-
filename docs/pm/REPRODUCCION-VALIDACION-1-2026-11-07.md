# Reproducción de VALIDACION-1 (2026-11-07)

PM principal. Rama `claude/dev-tecnica`, entrega `c24a266`, producto
`0bd4b6c` (base `18f2928`), informe `9bc75e9`.

**Veredicto: en revisión (borrador).** Lo que se muestra, lo que se guarda y lo que
habilita «Generar» salen de la carga que se ve.

## Lo que coincide con el informe

| Qué | Salida |
|---|---|
| `chequeo-6.py 18f2928 0bd4b6c` | 2 `AVISO`, los dos explicados en el informe (`fecha_inic_activ.py` entra por un merge; `finalize.js:9` es la función que envuelve la pantalla) |
| `sabotajes/validacion1.sh c24a266` | `BASE  | en verde`, 7 `ROJO`, `FALLAS=0`, `salida 0` |
| código de `runValidation` | leído: caché sólo con el mismo pedido, turno por validación, error con otro pedido limpia el resultado |

## Mutaciones propias

Mismo guion, con dos sabotajes de la PM:

| Cambio en `finalize.js` | Salida |
|---|---|
| sacar `!force &&` («Volver a validar» reusa el caché) | `VERDE`: la pantalla no lo ve |
| el caché no vence (`< 60000` → `true`) | `VERDE`: la pantalla no lo ve |

Las dos son de la misma carga, no muestran nada de otra: quedan fuera de la
causa de la pieza y van como riesgo, no como devolución.

## Adversario

Sonnet alto, en curso al escribir esto.

## Riesgos que quedan

- Las dos mutaciones de arriba: ninguna prueba cuida «Volver a validar» ni el
  vencimiento de 60 s.
- Riesgo 1 del informe: con el validador caído y sin validación previa, el
  historial guarda 0 (ya pasaba antes). Va a la cola como pieza aparte.

## No corrido por la PM

- Suite completa: la corrió la Dev sobre `0bd4b6c` (`4570 passed`); después
  sólo cambió `scripts/testing/`. El cambio es sólo de la pantalla.
