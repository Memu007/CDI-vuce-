# DOS-RELOJES — reproducción de la PM (2026-11-13)

Pieza de la Técnica: que el mensaje de `forzar_orden1.js` no dependa del
empate entre su tope y la espera del producto. Base `eea0eab5`, arreglo
`894bc67a`, merge `4a8652a7`, informe `89d74bbe`. Sólo arnés
(`scripts/testing/forzar_orden1.js`, +9/−6); producto +0/−0.

**Veredicto: aceptada sobre `894bc67a` e integrada (`89d74bbe`).** Sin
devolución.

## Lo que corrí

Worktree en `894bc67a`, `correr_pantallas.sh` con `CASOS=z22 SOLO=orden1` y
`NODE_OPTIONS="--require <preload>"`, venv de la PM, sin red.

| qué | resultado |
|---|---|
| preload nuevo sobre `894bc67a`, 4 corridas | 4 de 4 rc=0, «la consulta del hueco se cortó sin respuesta antes de entrar» y `OK` |
| preload viejo (el de la base) sobre `894bc67a`, 4 corridas | rc=0 las 4; 1 «se cortó…» y 3 «seguía retenida a los 10 s»: el rojo de la Dev se reproduce |
| preload nuevo sobre `74e3cc74` (antes del arreglo de producto) | rc=1, «volvió antes de entrar: 401», `FALLA: … reading 'click'`: la puerta que distingue sigue en rojo |
| mi negativo: `ESPERA_SESION_MS` a 14000 en un commit local | rc=0, «se cortó sin respuesta» (una corrida) |
| mi negativo: `ESPERA_SESION_MS` a 16000 en un commit local | rc=0, «seguía retenida a los 15 s de pedida» (una corrida) |
| `chequeo-6.py eea0eab5 894bc67a` | producto +0/−0, arnés +9/−6, historia vacía, 0 `AVISO`: igual que el informe |

Los dos negativos tocan `app_v2.js` en commits locales del worktree que no
están en ninguna rama. Muestran que el mensaje lo decide qué reloj vence
primero: con la espera del producto por debajo del tope sale «se cortó»; por
encima, «seguía retenida».

## `orden1b.sh`

Sobre `894bc67a` vi sólo la cola: 3 `ROJO`, «sabotajes sin rojo: 0», rc=0.
Los 30 `ROJO` los contó la Dev. No podía moverse con este cambio:
`git grep -l forzar_orden1` da sólo el archivo, `orden1b` no lo carga.

## z22 sin el preload

`pantalla_orden1.js` (z22) no tiene rama «retenida»: ese mensaje lo imprime
sólo el preload. Con el tope en 15 s y la espera del producto en 10 s, sólo
apareció en mi negativo de 16 s. z22 sin preload: no corrido.

## No reproducido por mí

Los 30 `ROJO` de `orden1b.sh` (vi la cola) y las corridas repetidas de la
Dev más allá de las cuatro mías.
