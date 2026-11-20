# Reproducción de CONEXIONES-1-NOKEY, 2026-11-20

Dev técnica. Entrega `331bae9f`; vuelta `090609bc` (anclas) y `05e61efa` (`soltar()`), informe
`77556d06`. Veredicto en `PARA-DEV.md`: se acepta e integra junto con CONEXIONES-1-PRODUCTO, sobre
el SHA final de esa pieza, porque la vuelta ya está encima de commits de PRODUCTO
(`git merge-base --is-ancestor 7f4e04d1 090609bc` da verdadero).

## Primera entrega (`331bae9f`)

- Adversarios Opus y Sonnet con Postgres 16, sin red, `GEMINI_API_KEY` vacía: nada que bloquee.
  Preexistentes, iguales en la base: D188, D205, 500 por clave foránea en alta contra borrar cliente.
- Negativo de la PM: sin el arreglo de organizaciones, `conexiones1_pares.py` da «FOR UPDATE | MAL».
- Devolución: `anclas_perdidas.py 298e5fee` daba tres PERDIDA de `cobro_corte1.sh` (430, 434, 438)
  que la base no tenía; y el intermitente «la app no soltó sus conexiones» sin causa.

## Vuelta, corrido por la PM

| qué | sobre | resultado |
|---|---|---|
| `scripts/testing/anclas_perdidas.py` | `05e61efa` | rc=0, ninguna PERDIDA; sólo las SIN ANCLA de `limpieza1.sh` (por diseño) |
| `scripts/testing/conexiones1_nokey.sh` | `05e61efa` | rc=0; los tres BIEN (abajo) |
| carrera forzada, `soltar()` viejo y nuevo | `331bae9f` + espera de 1 s en la tarea de log | ver «El intermitente» |

`conexiones1_nokey.sh`, salida exacta:

```
BIEN  | sin sabotaje: salida 0, dice «_cuenta_bloqueada después del aviso: FOR NO KEY UPDATE OF users | FOR NO KEY UPDATE OF organizations»
BIEN  | sin key_share ni of=: salida 1, dice «FOR UPDATE | FOR UPDATE | MAL DEADLOCK | recarga + guardado DEADLOCK | recarga + maria»
BIEN  | key_share sin of=: salida 1, dice «FOR NO KEY UPDATE | FOR UPDATE | MAL»
rc=0
```

«sin sabotaje: salida 0» depende de `7f4e04d1` (PRODUCTO): sobre un SHA sin él vuelve a 1. Por eso
es puerta de PRODUCTO.

## El intermitente

Causa según la Dev: la tarea de log de `MetricsMiddleware` devuelve su conexión después del
`engine.dispose()` del arnés, cae en el pool descartado y queda idle en «COMMIT;». En el producto
`dispose(` sólo está en `close_db()` (`database/connection.py:161`, al apagar; `git grep` sobre
`05e61efa`). Su evidencia: 11/12 sin el arreglo, 12/12 con él, y el volcado de la réplica que falló.

Intento de la PM de hacerla determinística (`conexiones1_pares.py` en `331bae9f`, `con_pg16.sh`):

| `soltar()` | espera de 1 s | duración | resultado |
|---|---|---|---|
| viejo (`331bae9f`) | antes del `commit` | 44 s | rc=1 (los 3 deadlocks esperados sin PRODUCTO), ningún «la app no soltó» |
| viejo (`331bae9f`) | después del `commit` | 39 s | rc=1, ningún «la app no soltó» |
| nuevo (`conexiones1_rondas.py` de `05e61efa`) | antes del `commit` | 101 s | rc=1, ningún «la app no soltó» |

Ninguna corrida dio «Error logging metrics»: la espera insertada no rompió la tarea. Que el nuevo
tarde más del doble muestra que la tarea de log estaba viva en el dispose, que es la condición de
la causa informada. Aun así el viejo pasa: su `h.hasta` ya repetía dispose + gc para ese camino
(su comentario lo dice). Conclusión: del arnés y no de la app, sí; el mecanismo, incompleto (no
explica la conexión que en el volcado de la Dev sobrevivió 14 s de dispose + gc). Se le pide un
párrafo con evidencia en PRODUCTO; si no, riesgo abierto. 11/12 contra 12/12 no separa el arreglo
de la suerte.

## No corrido por la PM

Sobre `05e61efa`: `cobro_corte1.sh` (~80 min; la Dev informa rc=0, 87 ROJO, «sabotajes con
falla: 0»), la suite completa, `e2e_maria.sh`, adversarios y `/code-review`. Van sobre el SHA final
de PRODUCTO, con la revisión fuerte de esa pieza.
