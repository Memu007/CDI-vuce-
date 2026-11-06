# Reproducción de ORDEN-1, segunda vuelta (2026-10-29)

Entrega de la Dev técnica: producto `ad87f78`; pruebas y sabotajes hasta
`86c9d84`. Es la vuelta de la devolución del 2026-10-28 20:08 UTC.

## Lo que corrió la PM, sobre `86c9d84`

- `orden1.sh`: 64 ROJO, «sabotajes sin rojo: 0», «fin rc=0» (igual que el
  informe).
- **H1, la sesión que cambia durante la espera del candado**, con el guion
  del adversario (`r1_candado.js`) contra una API local en SQLite:
  A deja una operación cerrada a medias (`OP-DE-A`) y tiene otra pestaña
  abierta; se duplica esa pestaña, que espera el candado 1,5 s, y en esa
  espera entra B.

  ```
  == DEMORA 900
  entró B a los 1135 ms
  P2 (sesión de B): {"pantalla":"review","factura":"OP-DE-A","items":1,"aviso":"Entró otro usuario en este navegador: esta pestaña ya no guarda la operación. Recargá la página.", ...}
  después: [..."OP-P1"...},{"clave":"cdi_v2_state:b2779944-b5","user":null,"closed":false,"factura":"OP-DE-A"}]
  P3 de B: {"pantalla":"upload","items":0, ...}
  tras P3 de B: [{... "user":"adva_…","closed":false,"factura":"OP-P1"}]
  P4 de A: {"pantalla":"upload","items":0, ...}
  == DEMORA 300
  entró B a los 542 ms
  (el mismo resultado: sobre con "user":null, barrido por la pestaña de B; A no lo recupera)
  ```

  La operación de A queda en un sobre sin usuario, la primera pestaña nueva
  la barre y A, al volver a entrar, no la encuentra: se pierde sin vuelta.
  Mientras tanto, la pestaña duplicada le muestra a B la operación de A en
  review, con el aviso de otro usuario.

## Adversarios (Opus alto y Sonnet alto, contexto nuevo, sobre `86c9d84`)

Los dos reprodujeron H1 por su cuenta, también en la recuperación tardía
(`CDI.borrador.buscar()` y `adoptar(b)`). La PM reprodujo H1 en el
arranque (arriba); lo demás es de los adversarios.

1. **Alta, PM: H1** (arriba). La causa: `buscarBorrador` toma el usuario,
   espera `pestanaViva` y después `adoptarBorrador` escribe con
   `usuarioActual()` y borra el sobre original. El informe lo tenía como A9,
   baja.
2. **Media: pestaña tocada sólo por `pointerdown`, `keydown` y `drop`.** Un
   `click()` sin `pointerdown` no la marca; la recuperación tardía la lleva
   a review y lo que se elige después pisa la operación de antes sin aviso.
   Quitar `keydown` o `drop` no lo ve ningún caso.
3. **Media: sabotajes que faltan, medidos por el adversario:**

   | Mutante | Consecuencia |
   |---|---|
   | sin `sesionRevisada = sesion;` | con 401, las consultas en 20 s pasan de 1 a 8 |
   | sin el freno de 10 s de `revisarDesde` | con la red cortada, de 2 a 8 |
   | el aviso de otro usuario deja de ser pegajoso | pasa a «No se pudo comprobar la sesión» |
   | sin `sesionRevisada = null` en el `catch` | por lectura: tras un error de red no vuelve a preguntar |

4. **Baja: `ESPERA_SESION_MS` 10 s.** Con una sesión que tarda 12 s la
   pestaña no guarda y avisa. Lado seguro; la PM acepta el supuesto.
5. **Baja: A2.** El mismo usuario que sale y vuelve a entrar con la primera
   consulta en camino ve «Entró otro usuario»: no guarda y avisa.
6. Informativo: `/logout` no rota el CSRF; el bfcache de las pruebas es
   simulado; `subiendo--` y el aviso `lleno` sin prueba.

Lo que aguanta, según los adversarios: la sesión se mira antes de guardar,
la recarga lenta recupera o avisa, el corte se ve en `#avisoBorrador`, y
sin usuario a tiempo la pestaña avisa que no guarda.

## No corrido por la PM

La suite completa, `/code-review` y `/security-review` (tampoco los corrió
la Dev en esta vuelta, por la pausa de Emi), y un bfcache real del
navegador.

## Veredicto

Devolución sobre `86c9d84`. La vuelta arregla lo pedido, pero la
recuperación sigue decidiendo con el usuario de antes de una espera, y eso
pierde la operación de otro usuario sin vuelta. El detalle está en
`PARA-DEV.md`.
