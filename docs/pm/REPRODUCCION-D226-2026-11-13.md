# Reproducción de D226 (2026-11-13)

Entrega de MARIA: arnés `bdb8130d`, informe `a88f62f3`, base `9abd8285`.
Sólo arnés: las tres pantallas abren el navegador con `chromium.launch()`.
Revisado por la PM principal en el SHA entregado y en la base. Veredicto:
**aceptada e integrada**.

| qué | salida |
|---|---|
| `chequeo-6.py 9abd8285 bdb8130d` | producto +0/−0, arnés +3/−3, historia vacía, 0 AVISO: igual que el informe |
| `SOLO="catalogo_ncm1 excel1 maria1b"` sobre `bdb8130d` | `resumen: 3 verdes, 0 rojas` |
| el rojo del informe en la base | no se reproduce acá: en este contenedor la ruta fija `/opt/pw-browsers/chromium-1194` existe (lo dice el informe) |
| prueba que distingue el cambio: `SOLO=excel1` con `PLAYWRIGHT_BROWSERS_PATH=/tmp/no-hay-navegador` | `bdb8130d`: `ROJA excel1 rc=1`, `FALLA: browserType.launch: Executable doesn't exist at /tmp/no-hay-navegador/chromium_headless_shell-1243/…`; base `9abd8285`: `verde excel1 rc=0` |

La versión nueva pide el navegador al Playwright instalado, como las otras 24
pantallas; la base lo abría por ruta fija y no miraba `PLAYWRIGHT_BROWSERS_PATH`.

No corrido: el corredor entero (lo corrió la Dev: 30 verdes), pytest y
adversarios (sólo arnés).
