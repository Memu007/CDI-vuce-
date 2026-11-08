# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## SMOKE-1 (D137 a): **entregada** en `00df4de` (2026-11-08), base `dbe2d2c`

| SHA | qué |
|---|---|
| `87d5734` | test: el smoke espera el rechazo sin sesión en `/api/ui/event` y en `/api/session/state` |
| `00df4de` | test: si curl no conecta, el smoke dice qué pedido falló (hallazgo de la autorrevisión) |
| este commit | docs: el informe |

**Producto +0/−0. Arnés +12/−10** (sólo `scripts/testing/smoke_friccion.sh`).

Qué hace: los dos POST sin sesión pasan por `rechaza_sin_sesion`, que exige
`"ok":false,"detail":"Evento sin sesión no admitido"` en el cuerpo. Si no
está, el smoke da rojo y muestra lo que obtuvo. Después sigue con by-cuit
(401), sin cambios.

**Nada para decidir.** Supuestos reversibles:

1. Se busca la cadena exacta, con el orden de las claves. Así distingue el
   rechazo del `{"ok":false}` que el producto contesta cuando salta una
   excepción. Si alguien reescribe el mensaje, el smoke da rojo.
2. Saqué el `"dry":true` de los cuerpos: el producto no lo lee.
3. Si curl no conecta, el smoke dice qué pedido falló, en vez de salir con
   el código de curl y sin `[FAIL]`.

Siguen abiertas **D131** (de EMAIL-1, va a Emi), **D136** (vigente: no traigo
tu rama hasta que INTEGRAR-1 esté aceptada) y **D138** (de RESET-3: quien
conoce el email de una cuenta la deja sin links; recomiendo (a)). La próxima
D libre es la D139.

## Comandos

```bash
# con el producto levantado en <puerto> (ENVIRONMENT=test): «==> OK · telemetría y alias session/state rechazan sin sesión + by-cuit protegido», salida 0
BASE_URL=http://127.0.0.1:<puerto> ./scripts/testing/smoke_friccion.sh; echo "salida $?"
# rojo: en main.py, sacar de _ui_event las dos líneas de «if accion not in _UI_EVENT_SIN_SESION: return {...}»,
# reiniciar y volver a correr: «[FAIL] POST /api/ui/event sin sesión debería rechazarse, obtuvo: {"ok":true}», salida 1
# rojo del alias: que session_state devuelva {"ok": True} sin pasar por _ui_event:
# «[FAIL] POST /api/session/state sin sesión debería rechazarse, obtuvo: {"ok":true}», salida 1
```

## Puertas

Todas contra el producto de `00df4de`, levantado con uvicorn en un worktree
aparte y `ENVIRONMENT=test`.

| corrida | salida exacta |
|---|---|
| smoke de `dbe2d2c`, producto sin tocar (rojo antes) | `[FAIL] POST /api/ui/event`, salida 1 |
| smoke de `00df4de`, producto sin tocar | `==> OK · telemetría y alias session/state rechazan sin sesión + by-cuit protegido`, salida 0 |
| smoke de `00df4de`, `_ui_event` acepta sin sesión | `[FAIL] POST /api/ui/event sin sesión debería rechazarse, obtuvo: {"ok":true}`, salida 1 |
| smoke de `00df4de`, el alias acepta sin sesión | `[FAIL] POST /api/session/state sin sesión debería rechazarse, obtuvo: {"ok":true}`, salida 1 |
| `rechaza_sin_sesion` de `87d5734` contra el puerto 9 (rojo antes) | sin `[FAIL]`, salida 7 |
| `rechaza_sin_sesion` de `00df4de` contra el puerto 9 | `curl: (7) Failed to connect to 127.0.0.1 port 9 after 0 ms: Couldn't connect to server` y `[FAIL] POST /api/ui/event: curl no pudo completar el pedido`, salida 1 |

**No corrido**, porque la pieza no toca el producto: la suite, `compileall`,
`/security-review` y `ataque_aislamiento.sh`.

## Hallazgos de la autorrevisión

| quién | hallazgo | qué hice |
|---|---|---|
| `adversario-sonnet-medio` (Sonnet, medio) | Sin falsos verdes. Probó la tilde en UTF-8, `LC_ALL=C`, `local` con `set -e` y cuerpos vacíos o inválidos | — |
| `adversario-sonnet-medio` (Sonnet, medio) | Baja: verde aunque el producto rechace también las acciones admitidas | Riesgo 1 |
| `adversario-sonnet-medio` (Sonnet, medio) | Baja: con la red caída sale sin mensaje | Arreglado en `00df4de`, con su rojo antes |
| `adversario-sonnet-medio` (Sonnet, medio) | Muy baja, del producto: `action` lista o dict contesta `{"ok":false}` sin detail | Riesgo 2 |
| `adversario-sonnet-medio` (Sonnet, medio) | Del entorno: un 429 da rojo con el producto bien | Riesgo 3 |
| `/code-review high` | Falta el caso del camino aceptado | Riesgo 1 |
| `/code-review high` | curl bajo `set -e` corta sin mensaje | Arreglado en `00df4de` |
| `/code-review high` | La cadena exacta y el texto copiado del producto | Supuesto 1 |
| `/code-review high` | El `"dry":true` no lo lee el producto | Sacado en `00df4de` |

## Riesgos

1. **Baja.** No hay caso para una acción admitida sin sesión (por ejemplo,
   `hero_cta_clicked`). Si el producto rechazara todo, el smoke seguiría en
   verde. No lo sumé: está fuera de D137 y escribiría telemetría.
2. **Muy baja, del producto.** Un `action` que no es texto da TypeError y
   contesta `{"ok":false}` sin detail. No guarda nada. La pieza era sólo el
   script.
3. **Del entorno.** Con más de 120 pedidos por minuto, un 429 da rojo con el
   producto bien. El mensaje muestra el cuerpo, así que se reconoce.

## chequeo-6

```
chequeo-6 dbe2d2c..HEAD: avisos para mirar, no un veredicto
producto +0/−0
arnés +12/−10
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Archivos de producto

Ninguno.

## Lo que sigue

OBSERVABILIDAD-1.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (send_message next, «Dev MARIA: …»), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. SMOKE-1 entregada en 00df4de (informe en este archivo, base dbe2d2c). RESET-3 entregada en 8fda3d2 (informe dbe2d2c, base 2fba5c9); AVISOS-2b aceptada sobre aa115f4 sin integrar. Abiertas: D131 (de EMAIL-1, va a Emi), D136 (decidida: no traigo tu rama hasta que INTEGRAR-1 esté aceptada), D138 (DoS del tope por cuenta). La próxima D libre es la D139. Sigue OBSERVABILIDAD-1, después ORG-1+D40 y D102. Nunca main, nada se publica sin el «dale» de Emi para el SHA, sin secretos, sólo datos inventados.
