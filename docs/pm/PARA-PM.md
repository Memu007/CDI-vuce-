# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ORDEN-1, vuelta de tu devolución del 2026-10-28 16:45 UTC sobre `0d89c20`

### Decisiones

- **D1. Con la consulta del usuario caída al abrir, el mismo usuario vuelve
  a entrar en otra pestaña: esta pestaña deja de autoguardar hasta
  recargarla.** Mientras no se sabe quién abrió la pestaña, el único indicio
  de que la sesión cambió es el token CSRF, y un login nuevo lo cambia aunque
  sea la misma persona. Lo encontró el adversario Sonnet (hallazgo 1).
  - (a) Queda así: es el lado seguro. Lo cargado no se guarda a nombre de
    otro. La pestaña sigue andando y puede generar; sólo pierde el
    autoguardado, y lo cargado se pierde si se cierra sin terminar.
  - (b) Si el usuario que vuelve es el mismo que tenía la pestaña cuando se
    abrió, seguir guardando. No se puede saber: al abrir no hubo usuario.
    Habría que guardar el usuario de la última sesión en sessionStorage, y
    eso es otro dato que hay que mantener.
  - **Recomiendo (a).** Pasa sólo si el servidor está caído al abrir y la
    persona vuelve a entrar en ese rato. (b) agrega un estado nuevo para un
    caso raro. Con (a), corrijo la línea del `CHANGELOG` que dice «la
    operación se sigue guardando» en la próxima entrega que toque ese archivo.

Lo demás de la devolución: lo hice como lo pediste. Los supuestos van abajo.

| Qué | SHA |
|---|---|
| Pruebas: dueño, edad y pestaña viva; rojo antes de cada regla | `0fa30bf` |
| **Producto:** el sobre guarda el usuario, vence a los 7 días y la duplicada no toma la operación de la viva | `36aba87` |
| Sabotajes de dueño, edad, pestaña viva y los dos mutantes | `6da850e` |
| Pruebas: con la consulta del usuario caída al abrir, la operación se guarda igual (rojo del adversario) | `699c3eb` |
| **Producto:** sin usuario al abrir, la pestaña lo vuelve a pedir y sigue autoguardando | `29c1999` |
| Pruebas: el sobre de hoy sin dueño se borra; sabotajes que faltaban | `aa174e1` |
| Pruebas: si otro usuario entra mientras la pestaña reintenta, la operación no queda a su nombre (caso k, rojo) | `6fd3de7` |
| **Producto:** la pestaña sin usuario no guarda lo cargado a nombre de quien entra después | `1de46b4` |
| Pruebas: el caso j mira el reintento de la pestaña; los sabotajes de j y k apuntan bien | `973a1ed` |
| Informe | este commit |

Entre esos commits van también los de COBRO-MP-1 (A, B, C, D y E) y el merge
de tu rama hasta `d0ef0a1` (`eebd3c9`). COBRO no entra en esta entrega: la
informo aparte. Ver «COBRO-MP-1, en curso».

Archivo de producto tocado en esta vuelta: `proyecto_maria/static/v2/app_v2.js`
(y `CHANGELOG.md`).

### Qué hace ahora

- **Dueño.** El sobre del borrador guarda el usuario. Al abrir, sólo se
  recupera el del mismo usuario. Un sobre sin dueño se borra, sea la clave
  vieja sin pestaña o un sobre de hoy sin `user`.
- **Edad.** Un sobre de más de 7 días no se recupera y se borra al barrer.
  Uno de casi 7 días, sí.
- **Pestaña viva.** Cada pestaña retiene un lock con su clave. La duplicada
  no toma la operación de una pestaña viva. La recarga y la restauración
  recuperan la suya. Una pestaña que murió sin `pagehide` se da por muerta a
  los 3 minutos (`BORRADOR_HUERFANO_MS`).
- **Sin usuario al abrir.** Si `/auth/current_user` falla al abrir, la
  pestaña lo vuelve a pedir. Espera de 1 a 30 segundos entre pedidos, hasta
  tenerlo. Mientras tanto no recupera ni guarda. Cuando llega el usuario,
  guarda lo cargado a su nombre.
- **Otra sesión en el medio.** Si cambió el token CSRF desde que abrió la
  pestaña, o si llega un usuario distinto del dueño, la pestaña deja de
  recuperar y de guardar hasta recargarla. Lo mismo después de un 401.

### Supuestos (reversibles)

1. **Sin usuario al abrir, se reintenta.** No lo pediste. Lo agregué porque
   el adversario mostró que tu regla de dueño rompía algo que andaba: con
   `/auth/current_user` caído al abrir, la pestaña no autoguardaba nunca.
   Antes de ORDEN-1 guardaba igual.
2. **Sesión ajena.** Es consecuencia del punto 1. Mientras se reintenta, si
   otro usuario entra en el mismo navegador, lo cargado quedaba a su nombre
   (caso k, rojo en `6fd3de7`).
3. **Tope de 30 s entre reintentos.** Sin tope, la espera crecía sin fin;
   con 1 s fijo, la pestaña martillaba al servidor caído. Hay un sabotaje
   para cada lado.

### Puertas

| Puerta | SHA | Resultado |
|---|---|---|
| Sabotajes (`scripts/testing/sabotajes/orden1.sh`) | `973a1ed` | 31 en ROJO, «sabotajes sin rojo: 0», «salida 0» |
| Pantalla completa (`scripts/testing/pantalla_orden1.js`) | `d316db2` | «OK: ORDEN-1 en el navegador», «salida 0» |
| Suite completa | `d316db2` | «4199 passed, 121 skipped, 3 xfailed in 590.02s», «salida 0» |
| `/code-review high` y `/security-review` | — | **no corridos en esta vuelta**: corrió sólo el adversario Sonnet alto, como dice «Cuántos y quién los corre» para una vuelta |

Los dos mutantes que pediste, con lo que dice el rojo:

- `BORRADOR_HUERFANO_MS` enorme: «FALLA: no se recupera la operación de una
  pestaña que murió sin avisar».
- Quitar el `selectedRows.add` de `reorderItems`: «FALLA: al arrastrar, la
  selección no sigue a los productos».

La suite y la pantalla corren sobre `d316db2`, que es `973a1ed` más COBRO.
COBRO no toca `app_v2.js`.

### Adversario (Sonnet, esfuerzo alto, sobre `973a1ed`)

| # | Severidad | Hallazgo | Qué hice |
|---|---|---|---|
| 1 | MEDIA | Con la consulta caída al abrir, el mismo usuario vuelve a entrar en otra pestaña: la pestaña deja de autoguardar (falso positivo del CSRF, `app_v2.js:343-345`). Ninguna prueba lo cubre | **D1** |
| 2 | BAJA | Una consulta del usuario que tarda más de 4 s, con un login en el medio, deja la pestaña como sesión ajena | riesgo |
| 3 | MEDIA | La pestaña ajena sigue mostrando la operación de A, pero `CDI.currentUser` pasa a ser B, y `finalize.js:790` usa el CUIT de B al generar | riesgo, con propuesta |
| 4 | MEDIA (cobertura) | Ninguna prueba cubre la rama `user.username !== duenoPestana` ni el corte por 401 (`sinSesion`) | riesgo, con propuesta |
| 5 | — | Los casos j y k distinguen el defecto | — |
| 6 | BAJA | Una carrera en `adoptarBorrador` deja `user: null`. No la reprodujo | riesgo |

Antes, en esta misma vuelta, el adversario encontró el rojo de `699c3eb`
(supuesto 1).

### Riesgos

Los que pediste, sin arreglar:

- **Pestaña congelada más de 3 minutos.** Su operación la puede tomar otra
  pestaña.
- **MARIA-8.** Dos filas del mismo renglón se funden en un ítem del TXT.
  Queda como está.
- **`draggable` colgado.** Queda así si se suelta fuera de la tabla.
- **El borrador de A sigue en localStorage después de su salida.** B ya no
  lo ve.

Del adversario:

- **Hallazgo 2.** Una consulta lenta deja la pestaña sin autoguardado hasta
  recargarla. Es el lado seguro.
- **Hallazgo 3.** Propuesta: cuando la sesión es ajena, la pestaña avisa y
  no deja generar hasta recargarla. Toca `finalize.js`, que no está en esta
  pieza.
- **Hallazgo 4.** Propuesta: un caso de pantalla para cada rama y su
  sabotaje. No los hice por tiempo. Hoy cada rama es una línea que lee un
  dato del servidor.
- **Hallazgo 6.** Sin reproducción.

### Errores míos en esta vuelta

- En medio de la vuelta, mi copia quedó con el HEAD separado en `6da850e`.
  Ni yo ni `orden1.sh` hicimos ese checkout; probablemente fue el
  adversario. Volví la rama a su lugar con fast-forward, sin perder commits,
  y le pedí al adversario que trabajara sólo en su worktree.
- El primer caso j era débil: la caída de 2 s por reloj podía verla sólo
  `tour.js`, no la pestaña. Lo rehice en `973a1ed`. Ahora mira que la
  pestaña vuelve a pedir el usuario.
- El sabotaje «el reintento da por cargado al usuario aunque falló» apuntaba
  a otro `return`. Ahora cambia `if (!res.ok) return;` por
  `if (!res.ok) return true;` (`973a1ed`).

### COBRO-MP-1, en curso (no se entrega acá)

Commiteado, sin informe:

- A: `d7edcfe`, `292eca1` y `b44c25e`; sabotajes en `8ca00f7`.
- B: `c3a05a7` y `85a32e6`.
- C y E: rojo en `86687fa`, producto en `4b3ebbd`.
- D, backend: rojo de la carrera en Postgres 16 en `aaa20f0`, producto en
  `d316db2`.
- C y D en el perfil: pantalla en rojo en `3b38dc2`, `profile.js` en
  `12ec020`.
- Sabotajes de B, C, D y E: `c73a286`.

`3b38dc2`, `12ec020` y `c73a286` quedan fuera de la suite y la pantalla de
esta entrega: tocan `profile.js` y scripts de prueba, no `app_v2.js`.

Antes de entregar COBRO me falta correr los sabotajes, los adversarios, las
revisiones y escribir el informe.

### Comandos

```bash
git fetch origin claude/dev-tecnica && git checkout --detach 973a1ed
PY=<venv>/bin/python scripts/testing/sabotajes/orden1.sh 973a1ed
#   tiene que terminar en «sabotajes sin rojo: 0» y «salida 0»
#   (31 líneas «ROJO  |», entre ellas las de los dos mutantes de arriba)
```

/compact conservar: Dev 1 (técnica), sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica, rutina trig_011UpBfwEu9TUzoNUrviqoP5, aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM). ORDEN-1 (vuelta) entregada (D1 abierta). Sigue, en orden: la devolución de EXCEL-2b del 28/10 19:20 (topes en cero, guardas sin caso, caso de sugerir y el informe), COBRO-MP-1 (A–E commiteadas; faltan adversarios, revisiones e informe), COBRO-CORTE-1, COBRO-MP-2, AISLAMIENTO-2, LIMPIEZA-1, BACKUP-1a (7 puntos). Informes en el scratchpad (informe_*.md); push y aviso por cada uno.
