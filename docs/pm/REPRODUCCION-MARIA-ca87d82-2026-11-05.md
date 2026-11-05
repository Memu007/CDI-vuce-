# Reproducción de `ca87d82` — 2026-11-05

RENDIMIENTO-1c vuelta 2, DESPACHO-1b vuelta 6 y CATALOGO-LARGO-1, con DISCO-1
(`5c46e36`) adentro. Rama `claude/dev-maria`. Worktree de PM
`/tmp/cdi-pm/wmaria` en `ca87d82`, Postgres 16 descartable.

**Veredicto: las cuatro aceptadas, sin integrar.** `HEAD..ca87d82` trae
además commits de piezas que tienen devolución abierta (SESION-1, ABUSO-1,
OBSERVABILIDAD-1, SUFIJOS-2, ORG-1): se integra cuando esas estén aceptadas,
o antes si Emi lo pide para publicar.

## Lo que corrí yo (salida exacta)

```
chequeo-6 bd46b4e..ca87d82 (RENDIMIENTO-1c): producto +51/−43, avisos: 0
chequeo-6 e099744..7bcb7b9 (CATALOGO-LARGO-1): producto +47/−8, 1 AVISO (39 netas; el informe dice por qué)
rendimiento1c.sh: 17 ROJO, con falla: 0
rendimiento1.sh: 11 ROJO
despacho1b_postgres: 22 OK, fallas 0
catalogo_largo1_postgres: fallas 0
== despacho1b   salida 0 · 138 · sin Postgres, no corridos: 0 · sabotajes sin rojo: 0
== disco1       salida 0 · 46 · sabotajes sin rojo: 0
== catalogolargo1 salida 0 · 12 · fallas: 0
== suite (con Postgres)
4537 passed, 102 skipped, 2 xfailed, 93 warnings in 638.65s, rc=0
```

La suite también avisó «Task was destroyed but it is pending!» (asyncio, al
cerrar); no falla nada.

## Lo que encontraron los adversarios

- RENDIMIENTO-1c (Sonnet): nada que bloquee.
- CATALOGO-LARGO-1 (Opus): ningún defecto del diff. Seis cosas que ya estaban:
  origen de más de 5 y proveedor de más de 200 se pierden con 200, y una
  descripción sólo CJK o emoji (van a CATALOGO-LARGO-2, propuesta a Emi);
  la pantalla se traga el error (DESPACHO-1c y 1d); el 2000 contado de dos
  maneras (CATALOGO-LARGO-2); `_migrate_add_user_cuit_column` sin
  `lock_timeout` y `api_logs.endpoint` de 200 (cola de limpieza).
