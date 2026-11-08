# Reproducción ENTORNO-3 (Dev MARIA), 2026-11-08

Sobre `fd545c1` (rama `claude/dev-maria`), base `a9c4f06`. Veredicto:
**aceptada, sin integrar** (la rama lleva debajo piezas en devolución).

| Qué | Resultado |
|---|---|
| `chequeo-6.py a9c4f06 fd545c1` | `producto +11/−10`, arnés `+72/−3`, historia vacío, avisos 0 — igual al informe |
| `tests/test_entorno1.py` | `30 passed` |
| `entorno1.sh fd545c1` | 10 ROJO, sin rojo 0, salida 0 |
| `entorno2.sh fd545c1` | 8 ROJO, sin rojo 0, salida 0 |
| `entorno3.sh fd545c1` | 4 ROJO (link a localhost, ALLOWED_ORIGINS, HSTS, 127.0.0.1), sin rojo 0, salida 0 |

La primera corrida de `entorno3.sh` se cortó por el tope de 10 min de mi
espera (no del script); la segunda, sola, dio lo de la tabla.

Negativos míos, importando la app en un proceso limpio: con `ENVIRONMENT`
vacío, `prod`, `Production` y `staging`, `ALLOWED_ORIGINS` en `*` o en blanco
no arranca (`CORS config error`) y, con orígenes válidos, `get_frontend_url()`
falla sin `FRONTEND_URL`. Control: con `development`, cae a
`http://127.0.0.1:8010` y a los orígenes locales. Cubre los dos que la Dev
deja como riesgo sin caso (`*` y espacios).

Diff de producto leído entero: las cuatro puertas usan `es_desarrollo()` /
`_es_desarrollo()`; no hay regla nueva. No corrí la suite completa: tomo las
dos de la Dev (`5201 passed`), sobre `2b7f09a`, que tiene el mismo producto.
Sin adversario: la pieza es de configuración y sus cuatro puertas tienen
sabotaje.

**Riesgo para publicar:** si en Railway `ENVIRONMENT` no es exactamente
`production` (D99) y falta `ALLOWED_ORIGINS`, antes la app arrancaba y ahora
no arranca. Antes de publicar, mirar en Railway `ENVIRONMENT`,
`ALLOWED_ORIGINS` y `FRONTEND_URL`.
