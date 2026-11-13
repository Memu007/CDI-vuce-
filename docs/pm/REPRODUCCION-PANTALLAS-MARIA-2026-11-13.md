# Reproducción de PANTALLAS-MARIA (2026-11-13)

Entrega de MARIA: guiones `0ec63435`, `3e195de4` y `7ac0b4ea`; su rama
integrada hasta `90b66c5e` en `e0d2770f`; informe `8f848862`. Base del
informe anterior `166c46c`. Sólo arnés (producto +0/−0). Revisado por la PM
principal en worktrees en `e0d2770f`, con el `correr_pantallas.sh` del mismo
SHA y, para una pantalla sola, un servidor y una base nuevos por corrida.

## Lo medido

| qué | salida |
|---|---|
| `git diff 7ac0b4e e0d2770 -- <sus cinco archivos>` | vacío |
| `chequeo-6.py 166c46c 7ac0b4e` | producto +0/−0, arnés +23/−8, historia vacía, 1 aviso (`subitems1` 180 → 181: la línea sumada es la llamada al ayudante; lo nuevo está en `_cuit_perfil.js`). Igual que el informe; el aviso queda explicado |
| antes: mi corredor sobre `907e1edb` (acta de CORREDOR-PANTALLAS) | `26 verdes, 4 rojas: maria3 maria4 maria5 subitems1` |
| corredor entero sobre `e0d2770f` | `resumen: 28 verdes, 2 rojas: maria1c orden1`. `maria3`, `maria4`, `maria5` y `subitems1` verdes |
| D226 en mi contenedor: `catalogo_ncm1`, `excel1`, `maria1b` | verdes en ese mismo corredor: `/opt/pw-browsers/chromium-1194` existe acá; el rojo es de su contenedor |
| `maria1c` | de la Técnica (INTERMITENTES): verde con su arreglo `d1f82fe2` |
| `orden1` en ese corredor | roja: 52 `OK` y `FALLA: page.evaluate: TypeError: Cannot read properties of null (reading 'click')` (no aparece `#validatingGenerate` después de «entró otro usuario y la pestaña de A guardó un cliente») |
| `orden1` sola, servidor y base nuevos, `CSRF_ENFORCE=true` (su única cabecera `// corredor`), dos veces en la base `90b66c5e` y dos en `e0d2770f` | las cuatro `rc=0`, 71 `OK`, `OK: ORDEN-1 en el navegador`. **No reproducido; causa sin diagnosticar.** Lo que la saca de esta pieza: `orden1` sólo requiere `_ip_nueva` y `_registrar`, ninguno de sus cinco archivos. En mi corredor sobre `907e1edb` había salido verde. Va a la Técnica |
| negativo: `maria4` sin el CUIT del comprador en el armado | `rc=1`, `FALLA: page.click: Timeout 30000ms exceeded`: el guion distingue la causa 1 |
| negativo: `maria5` y `subitems1` con `CSRF_ENFORCE=true` (el ayudante manda el token) | `rc=0`, 9 y 10 `OK` |
| D225 en vivo: `PUT /api/user/profile` con `cuit` `20999999998` (dígito verificador malo) | 200, y queda guardado |

## D225

`PUT /api/user/profile` (`main.py:2428-2439`) guarda el CUIT sin
`cuit_valido`. Confirmado en vivo arriba. Es producto y toca datos: pieza
chica propia, después de AJUSTE-BORRADOR, que además dice qué pasa con los
perfiles que ya tengan un CUIT inválido guardado (sin mutar datos).
