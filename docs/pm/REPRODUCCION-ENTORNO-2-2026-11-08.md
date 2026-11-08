# ENTORNO-2: reproducción de la PM (2026-11-08)

Entrega `bf92bf9`, base `1e1f60d`, rama `claude/dev-maria` (`19b7764`). Producto
`c8afa6f` y `fb91f5c`; pruebas `cac8924`, `65a689d`, `1b44897`, `633551d`.

## Corrido por la PM

- `chequeo-6.py 1e1f60d bf92bf9`: producto `+24/−26`, arnés `+166/−80`, historia vacía, `avisos: 0` (igual al informe).
- `tests/test_entorno1.py` en `bf92bf9`: `22 passed`.
- `entorno1.sh bf92bf9`: 10 ROJO, `sabotajes sin rojo: 0`. `entorno2.sh bf92bf9`: 8 ROJO, `sabotajes sin rojo: 0` (igual al informe).
- Negativos míos, con la misma sonda en proceso aparte: `ENVIRONMENT` = `"development\n"`, `"test "`, `"dev"`, `"local"`: las 11 puertas `cerrada`.
- Ni el front ni los scripts usan `/openapi.json`, `/docs` ni el cobro simulado. Nadie importaba `connection.IS_PRODUCTION`.

## Adversario (Opus, esfuerzo alto, contexto nuevo)

Ninguna puerta abierta ni regresión con camino de hoy.
- Sólo `docs_url`/`redoc_url`/`openapi_url` y el corte de `DATABASE_URL` se evalúan al importar; CSRF, cookies, VUCE y cobro leen en cada llamada.
- Sin importaciones circulares (ocho módulos importados por separado).
- Un sabotaje propio, distinto de los del arnés (VUCE y cookie cerrados sólo si `ENVIRONMENT` existe): `3 failed, 19 passed`.
- Suite completa en `bf92bf9`: `5124 passed, 335 skipped, 3 xfailed in 818.04s` (igual al informe).
- Menor, de pruebas: quedan monkeypatches de `main_mod.IS_PRODUCTION` en tests viejos (email1, prelaunch_block2/3, cobro_mp1/2) que ya no controlan lo que dicen. Va a la cola de limpieza.

## Riesgo para publicar

Si Railway no tiene `ENVIRONMENT=production` exacto (D99, pendiente de Emi), después de desplegar el CSRF bloquea y, sin `VUCE_MODE`, la consulta NCM con modo `fake` por defecto da `SourceUnavailableError`. Es el comportamiento buscado; hay que confirmar las variables de Railway antes de publicar.

## Veredicto

Aceptada sobre `bf92bf9`, sin integrar (la rama lleva debajo piezas en devolución). D107: (a), ENTORNO-3, decidido por la PM.

No corrido por la PM: la suite completa (la corrió el adversario).
