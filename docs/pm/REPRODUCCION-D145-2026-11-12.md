# D145 (a) de la Dev MARIA: reproducción de la PM (2026-11-12)

**En curso (PM):** faltan las corridas de `maria9` antes y después y la de
uvicorn sin `proxy_headers`.

Entrega `08edd63` (base `46959d7`), informe `1b87d06` en `claude/dev-maria`.
Sólo arnés: sus cuatro pantallas que registran varias veces contra una
misma base mandan un `X-Forwarded-For` inventado distinto por registro, y la
IP inventada sale de `scripts/testing/_ip_nueva.js`.

## Lo corrido

| qué | resultado | informe de la Dev |
|---|---|---|
| `chequeo-6.py 46959d76 08edd63` | producto +0/−0, arnés +12/−4, historia vacía, 0 avisos | igual |
| `sabotajes/validacion1.sh 08edd63` | BASE en verde, 7 `ROJO  \|`, `FALLAS=0`, rc=0, 122 s | igual (134 s) |
| `sabotajes/org1b.sh 08edd63` | 7 `ROJO`, `sabotajes sin rojo: 0`, rc=0, 21 s | igual (23 s) |
| `sabotaje_separadores1.sh 08edd63` | «OK: los 17 sabotajes dan rojo por la razón esperada», rc=0, 315 s | 17 de 17, rc=0 (377 s) |
| `sabotajes/org1b.sh 46959d76` (antes) | 5 `ROJO`, 2 `ROJO?` por 429, «sabotajes sin rojo: 2», rc=1, 18 s | igual |

Los guiones corrieron desde copias en el scratchpad con el venv de la PM y
`node` 22. No siempre uno por vez: `exp.sh` y `exp2.sh` corrieron a la par
de `sabotaje_separadores1.sh`, que igual dio 17 de 17.

## Negativos de la PM

**El que no distinguía (queda dicho).** `validacion1.sh 08edd63` con
`TRUSTED_PROXY_HOPS=0` dio lo mismo que sin él (7 `ROJO`, rc=0). Causa,
medida: uvicorn, por defecto, toma la IP del cliente de `X-Forwarded-For`
cuando el pedido viene de 127.0.0.1, así que con `TRUSTED_PROXY_HOPS=0` la
IP sigue siendo la inventada (siete corridas de la pantalla nueva contra una
API con `TRUSTED_PROXY_HOPS=0`: siete claves `registro:h:10.x.x.x` con 1
cada una). No es un defecto de la pieza; no sirve como negativo.

**El que distingue.** Una API de `08edd63` (SQLite propia,
`TRUSTED_PROXY_HOPS` por defecto) y siete corridas seguidas de
`pantalla_validacion1.js`:

```
pantalla de 46959d76 (sin header)
corrida 1 a 5: sale 0
corrida 6 sale 1 registrar: 429
corrida 7 sale 1 registrar: 429
[('registro:h:127.0.0.1', 7)]

pantalla de 08edd63
corrida 1 a 7: sale 0
siete claves registro:h:10.x.x.x, una por corrida
```

El guion entero corre la pantalla 8 veces (base y siete sabotajes): sin el
header, del sexto registro en adelante da 429, que son los 3 `ROJO?` que la
Dev contaba antes.

Además, sin pantalla: ocho `POST /auth/register` con `curl` sin header
contra la misma API dan `200 ×5` y `429 ×3`, con `TRUSTED_PROXY_HOPS` 1 y 0.
El límite del producto sigue en pie.

## Lo que la Dev dice y verifiqué leyendo

- **D190:** `pantalla_cliente1.js`, `_despacho1a.js`, `_destino1.js`,
  `_estudio1.js`, `_estudio1b.js` y `_orden1.js` tienen su propia copia de
  la IP inventada (grep).
- **D191:** `usa_el_sufijo_de_la_operacion` hoy recibe sólo `items`
  (`maria_generator.py:463`), y `sabotaje_maria9.sh` busca la firma con
  `iva_adicional`. El guion no se toca desde `9f1e5b52` (2026-10-25).

## No corrido

- `sabotaje_maria9.sh` (roto por D191) y las seis corridas de `maria9` y
  `separadores1` de la Dev contra una sola base: no las repetí; el negativo
  de la PM mide lo mismo sobre `validacion1`.
- Suite y `e2e_maria.sh`: la pieza no toca producto.
