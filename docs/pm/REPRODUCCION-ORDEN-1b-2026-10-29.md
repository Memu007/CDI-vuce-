# Reproducción de ORDEN-1b (2026-10-29)

Entrega de la Dev técnica: producto `6c459d2` (rama en `36cbd1d`).

## El arreglo, leído

`api()` frena toda escritura cuya cookie de sesión no sea la del dueño de la
pestaña, salvo que una consulta a `current_user` confirme que es él;
`confirmarSesion` descarta la respuesta si la cookie cambió mientras volvía;
un 401 lleva al login; `marcarAjena` tapa la pestaña con un diálogo que no
se cierra con Escape; `track()` no sale con sesión ajena; `logout()` no
cierra la sesión de otro. Coincide con el informe.

## Lo que corrió la PM

- `orden1b.sh 6c459d2`: 14 «ROJO», «sabotajes sin rojo: 0», sin «ROJO?».
- `orden1.sh 6c459d2`: 76 «ROJO  |», «sabotajes sin rojo: 0», rc=0 (la red de ORDEN-1 sigue entera).
- **El hueco del adversario Opus, reproducido** con su caso E7 (la consulta
  a `current_user` sale como A y su respuesta llega 1,5 s después, cuando B
  ya entró; la pestaña escribe en el medio), sobre `6c459d2` y con el
  mutante que quita la comparación de cookie de `confirmarSesion`
  (`if (sesionAjena || getCsrfToken() !== sesion) return false;` →
  `if (sesionAjena) return false;`):

  ```
  === pm-base
  E7: error: No se pudo comprobar la sesión. Recargá la página. salieron []
  E7 clientes A: [] B: []
  === pm-m1
  E7: status 200 salieron [ 'POST /api/clientes' ]
  E7 clientes A: [] B: [ 'E7-escrito' ]
  ```

  El producto aguanta; sin esa línea, la pestaña de A escribe como B. Según
  el adversario, `pantalla_orden1.js` completa con ese mutante da salida 0 y
  60 OK (su salida queda en `/tmp/cdi-pm/adv-o-orden1b-run/dev-m1-completa.out`;
  la PM corrió sólo E7).
- **El freno sólo se prueba con POST**, como dice el adversario Sonnet:
  con el mutante `method === 'POST' && …` delante del freno, la PM corrió
  `CASOS=z12,z20,…,z28` de `pantalla_orden1.js`: `dev salida 0`, 13 «OK»,
  ningún «FALLA». Con ese mutante, PUT, DELETE y PATCH salen con la sesión
  de B (lo vio el adversario en su `e2.js`).

## Adversario Opus alto (contexto nuevo, sobre `6c459d2`, `CSRF_ENFORCE=true`)

No encontró camino por el que una pestaña escriba como otro usuario, pierda
datos o quede trabada.

1. **Media (pruebas): nada protege la guarda de cookie de
   `confirmarSesion`** (arriba). Causa: `retenerUsuario` usa
   `route.continue()`, y Playwright manda las cookies al continuar; z20, z21
   y z23 reciben siempre a B y nunca prueban «la respuesta dice A y la
   cookie ya es de B».
2. **Baja (pruebas): nada prueba la salida del diálogo `#pestanaAjena`.**
   Sin el botón «Recargar» o sin el `cancel → preventDefault`, z20, z21 y
   z24 siguen en verde. El producto aguanta (Escape no cierra, «Recargar»
   recarga y conserva el borrador).
3. **Baja (pruebas):** sacar `'comprobando'` de lo que limpia
   `confirmarSesion` deja z12 en verde (el aviso quedaría fijo).
4. **Baja (producto):** «Comprobando la sesión…» puede quedar fijo si la
   sesión ya se cerró (`sesionRevisada` igual a la cookie tras un 401);
   forzado en E6, camino natural sólo por lectura. Texto engañoso, no
   bloqueo.
5. **Baja (producto):** una respuesta que ya dice «es B» se descarta por la
   comparación de cookie; la ráfaga da «No se pudo comprobar» y la pestaña
   se tapa recién a los 3 s. No escribe nada.
6. **Baja, por lectura:** en `loadCurrentUser` (rama `else`, tras el
   checkout), `currentUser` y los valores por defecto se pisan con los de B
   aunque `confirmarSesion` dé false.

Contexto, no de esta pieza: `/api/session/state` no está exento de CSRF y
`track()` no manda el header; con `CSRF_ENFORCE=true` la telemetría v2 da
403 (111 de 112 en su corrida). z27 cuenta pedidos que salen, no que se
aceptan.

Aguanta: ráfaga de 5 POST con un 500 en la primera consulta (sin duplicados
ni traba), logout en otra pestaña con B entrando mientras el POST espera,
FormData a `/api/migrations/analyze` con B adentro, base z12 y z20–z28 en
verde, y todas las rutas que hacen entrar cambian la cookie CSRF.

## Adversario Sonnet alto (contexto nuevo, sobre `6c459d2`)

No encontró defecto del producto. El cliente coincide con el servidor
(cookie `csrf_token`, rotada en las cuatro rutas que dan sesión, borrada en
`/auth/logout`; el middleware es double-submit sin atar la cookie al
usuario, así que este freno es el único control). Ningún otro camino de
escritura esquiva `CDI.api`. PUT, DELETE y PATCH con B adentro se frenan.
Corrió también con `ENVIRONMENT=production` (cookies Secure, CSRF por
defecto): igual.

1. **Media (pruebas): nada protege la guarda `sesionAjena` de
   `confirmarSesion`.** Sin ella, una pestaña cuya primera carga quedó
   «ajena» escribe a nombre de B (`status 200`, `cliente quedó en B: true`).
2. **Media (pruebas): el freno sólo se prueba con POST** (arriba,
   reproducido).
3. **Baja (pruebas): «Recargar» y el `cancel` del diálogo sin prueba** (el
   mismo que el 2 de Opus).
4. **Baja, por lectura:** en la escritura, `sesionEsDelDueno` puede esperar
   hasta 10 s sin aviso propio; el «Comprobando…» es sólo de la
   recuperación.
5. **Baja, medido:** una consulta a `current_user` por cada escritura
   simultánea (15 para 15).
6. **Baja, por lectura:** `/logout` de la raíz (v1) no borra `csrf_token`;
   no abre nada.

Mutantes: 6 muertos; vivos M1 y M7 (equivalentes), M2 (cambia el mensaje),
M3 y M4 (punto 3), M5 (punto 1), M15 (la guarda de cookie, el 1 de Opus) y
M21 (punto 2).

## No corrido por la PM

La suite completa con el mutante (lo corrió el adversario), `/code-review`,
cookies vacías o repetidas, dos pestañas que adoptan a la vez.

## Veredicto

Devolución de pruebas sobre `6c459d2`. El producto aguanta lo que se
probó; lo que no aguanta es la red: la comparación de cookie de
`confirmarSesion`, la guarda `sesionAjena`, los verbos que no son POST, la
salida del diálogo y la limpieza de «Comprobando» se pueden sacar sin que
nada se ponga rojo. Se pide una prueba con su sabotaje por cada condición
del freno; el detalle está en `PARA-DEV.md`. Nada se integra en esta vuelta.
