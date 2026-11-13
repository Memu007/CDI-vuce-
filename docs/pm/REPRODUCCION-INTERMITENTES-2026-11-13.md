# Reproducción de INTERMITENTES (2026-11-13)

Entrega de la Técnica: arnés `aa002538` y `2d76e419`; informe `d1f82fe2`;
base `90b66c5e`. Sólo arnés (producto +0/−0). Revisado por la PM principal en
un worktree en `d1f82fe2`, con el `correr_pantallas.sh` y el
`forzar_arranque.js` del SHA entregado.

## Lo medido

| qué | salida |
|---|---|
| `chequeo-6.py 90b66c5e d1f82fe2` | producto +0/−0, arnés +75/−9, historia vacía, 0 avisos |
| ¿`forzar_arranque.js` parchea el playwright de las dos pantallas? (`maria1c` lo pide por ruta fija, `maria7` por nombre) | desde `scripts/testing`, `require.resolve('playwright')` = `/opt/node-tools/node_modules/playwright/index.js`: el mismo módulo. Cada log dice `forzar_arranque: terminada` (maria1c) y `en_vuelo` (maria7) |
| carrera forzada sobre la base `90b66c5e`, dos veces | `0 verdes, 2 rojas: maria1c maria7` las dos; maria1c `- waiting 500ms` (click vencido), maria7 `FALLA: la pregunta por la fecha no aparece al subir` |
| carrera forzada sobre `d1f82fe2`, dos veces | `2 verdes, 0 rojas` las dos |
| sin forzar, sobre `d1f82fe2`, dos veces | `2 verdes, 0 rojas` las dos |
| `sesion1` con su cabecera: entorno del uvicorn leído en `/proc/<pid>/environ` mientras corre | `ENVIRONMENT=testing` en el servidor de `sesion1` (los demás uvicorn de la máquina, `development`); resumen `1 verdes, 0 rojas` |
| `kill -TERM` al PID del corredor de `d1f82fe2` a mitad de `orden1` | el corredor sale; vivos de esa corrida (uvicorn, `timeout`, node): 0; su worktree, borrado |
| lo mismo con el corredor de la base, a mitad de `borrador1` | quedan 3 huérfanos con PPID 1: uvicorn, `timeout 600 node` y node. Los maté por PID. El worktree, en mi corrida, sí se borró (el informe dice que quedaba: diferencia menor, no cambia el veredicto) |

La puerta es determinista: la misma condición forzada da rojo en la base y
verde con el arreglo, en las dos pantallas.

## D211, leída en el código

El informe dice que una usuaria real con la red lenta puede subir antes de la
primera pantalla. En `d1f82fe2`:

- Todas las secciones son `.screen` y `.screen{display:none}`; sólo la
  `.is-active` se ve (`app_v2.css:810-811`). Ninguna trae `is-active` en el
  HTML (`dashboard_v2.html:88` y siguientes).
- El arranque elige la primera pantalla recién con el usuario o a los 4 s
  (`app_v2.js`, `Promise.race([usuarioListo, espera])`). Hasta ahí la zona de
  carga y su botón están ocultos y `#uploadFileInput` es `sr-only` con
  `tabindex="-1"`.
- Soltar un archivo en la ventana sólo hace `preventDefault`
  (`screens/upload.js:155`).
- Lo único visible es «Nueva operación» de la barra (`data-action="go-upload"`):
  pasa por `goTo('upload')`, que fija `currentScreen`, y el arranque después
  hace `if (currentScreen && !parsed) return;`: no repite `goTo('upload')`, no
  sube el ticket. Además `orden1` ya cubre tocar la pestaña antes de que
  llegue el usuario («no la cambia y avisa»), verde en mi corredor.

Sólo `setInputFiles` de Playwright sobre el input oculto llega antes de la
primera pantalla. Queda un camino angosto, leído y no corrido: con un
borrador guardado, ella toca «Nueva operación» y sube en los segundos antes de
que llegue el usuario; al llegar, como está en `upload`, el arranque adopta el
borrador (`app_v2.js:921-922`) y hace `goTo` igual (`:927-932`), y una subida
todavía en vuelo se descarta. El comentario del código justifica recuperar
el borrador cuando a la carga la llevó el tour, no cuando ella está subiendo.
No lo corrí: va a la cola como riesgo «no corrido», y no es pieza ahora.

## D212

`orden1` tardó 581 s sola en su máquina contra el tope de 600. En la mía,
cuatro corridas sueltas seguidas (servidor y base nuevos cada una) llevaron
39 min por reloj (03:15:05 → 03:54:06): unos 585 s cada una, aproximado.
Subirlo a 900 es una línea del arnés y el tope sigue existiendo: (a).
