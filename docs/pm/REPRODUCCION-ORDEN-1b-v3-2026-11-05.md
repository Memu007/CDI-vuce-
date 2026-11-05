# Reproducción de ORDEN-1b vuelta 3 (2026-11-05, PM principal)

Sobre `f22f48b` (informe `e7d1642`). Sólo pruebas: `producto +0/−0`.

## Resultado

Devolución corta, sólo de pruebas. El caso `z35` no siempre mide la relectura
de la vuelta del pago: retiene «la primera `/auth/current_user` con
`CDI.currentUser` puesto», y esa no es siempre la relectura.

## Lo que corrí

| Qué | Resultado |
|---|---|
| `orden1b.sh f22f48b` (con otra revisión corriendo en paralelo) | 25 ROJO y `VERDE \| la sesión de la respuesta se lee cuando ya llegó (topup_success): la prueba no lo vio`, «sabotajes sin rojo: 1», SALIDA 1 |
| sabotaje M3 a mano + `CASOS=z35`, 6 veces sin carga (topup, success, topup, topup, success, topup) | 6 de 6 rojo con el mensaje esperado |
| lo mismo con 6 procesos de CPU al 100 %, 4 veces | 4 de 4 rojo |
| lo mismo con la consulta del tour atrasada 1 s (sólo en una copia de diagnóstico del arnés) | **topup_success y success: salida 0, verde**, «no queda en ninguna cuenta y avisa que entró otro» |

## Causa

Hay dos llamadas a `/auth/current_user` al abrir: `checkDemoForceTour`
(`static/v2/screens/tour.js:243`, `fetch` directo) y `loadCurrentUser`.
Con instrumentación en una copia (`console.log` de cada pedido con su pila):

- Corrida normal: pedido 1 es el tour (t≈200 ms, sin usuario), pedido 2 es
  la carga, pedido 3 es la relectura (t≈2200 ms topup, ≈4500 ms success) y
  es la retenida. El sabotaje da rojo.
- Con el tour atrasado 1 s: pedido 2 es el tour (t≈1150 ms, ya con usuario)
  y **es el que se retiene**. B entra, se suelta, y la escritura sale a
  t≈1600 ms (`sesionEsDelDueno`), **antes** de la relectura del pago
  (t≈2150 ms). Nunca pasa por la línea saboteada: verde.

Dos huecos del caso, los dos del arnés:

1. El handler no distingue la relectura del pago de otra consulta de quién
   es que llegue con la pestaña ya cargada.
2. `waitForFunction(__leidas >= __pedidas)` se cumple aunque la relectura
   todavía no se haya pedido: el caso escribe sin haber medido nada.

El verde de `orden1b.sh` es este camino: no lo forcé en esa corrida, pero es
el único verde que reproduje, y el mensaje de la pantalla (no queda en
ninguna cuenta, avisa) es el mismo que da con el tour retenido.

## D55

(a). Coincido: con la pestaña sin dueño el freno es `sesionAlAbrir`, y esas
filas no distinguen este sabotaje.

## No corrido

- `orden1.sh` y la suite completa sobre `f22f48b`: el diff es sólo del arnés
  de `z34`/`z35` y la vuelta 2 ya los tenía verdes.
- No repetí `orden1b.sh` entero: la causa se reprodujo de forma determinista.

Scripts del diagnóstico (fuera del repo):
`/tmp/claude-0/-home-user/eb961cf0-672f-50aa-9215-aa9e8513acf1/scratchpad/o1b3diag/run.sh` y `carga.sh`.
