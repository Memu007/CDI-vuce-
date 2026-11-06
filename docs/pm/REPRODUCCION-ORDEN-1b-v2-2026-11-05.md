# ORDEN-1b vuelta 2: reproducción de la PM (2026-11-05)

Producto `8b087fd`, informe `54dabb7`, base `7ebfc50`. Revisión con
subagente adversarial (Opus, alto) y confirmación de la PM.

## Lo que se sostiene

- `orden1b.sh 8b087fd`: 24 ROJO, «sabotajes sin rojo: 0», salida 0.
- `orden1.sh 8b087fd`: 76 ROJO, 0 VERDE, 0 ROJO?, 0 ROTO, «sabotajes sin rojo: 0», salida 0.
- `chequeo-6.py 7ebfc50 8b087fd`: igual al informe.

```
producto +6/−11
arnés +233/−10
historia (grep de §6, sin líneas movidas): vacío
  AVISO creció una función de más de 150: proyecto_maria/static/v2/app_v2.js:7 <anónima> 1198 → 1193, 1 en su propio cuerpo
  AVISO creció una función de más de 150: scripts/testing/pantalla_orden1.js:280 <anónima> 1343 → 1520, 103 en su propio cuerpo
avisos: 2
```

- Negativos del revisor sobre `8b087fd`, todos OK:
  - dos pestañas de A y una de B: las de A se tapan y no mandan POST ni PUT; B escribe;
  - entra B, sale B y A escribe: no sale el pedido, va al login;
  - relectura del pago retenida con la cookie de A, entra B, se suelta: el
    cliente no queda en ninguna cuenta.
- Grep de escrituras en `static/v2`: todas pasan por `CDI.api`. Los `fetch`
  directos son GET o tienen guarda.
- Las cuatro rutas que setean `access_token` en `main.py` también rotan
  `csrf_token`.

## El hueco (confirmado por la PM)

Mutante M3: en `loadCurrentUser`, mover `const sesionAntes = getCsrfToken();`
(app_v2.js:381) abajo del `try/finally`, antes de `if (duenoPestana === null)`.

- Arnés completo (`pantalla_orden1.js`) con M3: 67 OK, 0 FALLA, salida 0
  (revisor).
- Negativo n1 (relectura de `/dashboard?billing=success` retenida con
  `route.fetch()`, que manda la cookie de A; se registra B; se suelta la
  respuesta; se guarda un cliente), corrido por la PM:
  - sobre `8b087fd`: `OK n1: … no queda en ninguna cuenta (error: Entró otro usuario en este navegador. Recargá la página.)`, salida 0;
  - sobre `8b087fd` + M3: `FALLA: n1: la relectura del pago contestó A, entró B antes de leerla y la pestaña guardó un cliente y el cliente quedó en la cuenta de B`, salida 1.

El negativo vive en el scratchpad de la PM (`o1b/neg/casos.js`), no en el repo.

## Observación aparte (estaba en la base)

Las lecturas GET no pasan por el freno: con B adentro, la pestaña de A
muestra clientes y perfil de B sin taparse hasta que intenta escribir. Queda
fuera del criterio de ORDEN-1b («ninguna escritura…»).

## No corrido

- «B entra con una escritura de A en vuelo»: `route.continue()` repega las
  cookies; no se armó una variante que lo ejercite.
