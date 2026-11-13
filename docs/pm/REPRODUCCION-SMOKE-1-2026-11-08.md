# Reproducción de SMOKE-1 (PM principal, 2026-11-08 21:55 UTC)

Pieza de MARIA (D137 a): el smoke espera el rechazo sin sesión en
`/api/ui/event` y en `/api/session/state`. Base `dbe2d2c`, entrega `00df4de`,
informe `0231eee`. Sólo `scripts/testing/smoke_friccion.sh` (+12/−10);
producto +0/−0.

## Veredicto

Aceptada sobre `00df4de`, sin integrar (D136). Igual al informe.

## Lo que corrí (producto de `00df4de` con `levantar.sh`, puerto 8093)

- Producto sin tocar: `==> OK · telemetría y alias session/state rechazan sin
  sesión + by-cuit protegido`, salida 0.
- Sabotaje de MARIA (sin las dos líneas del rechazo en `_ui_event`):
  `[FAIL] POST /api/ui/event sin sesión debería rechazarse, obtuvo: {"ok":true}`,
  salida 1.
- Mi negativo (la acción del smoke en `_UI_EVENT_SIN_SESION`): mismo `[FAIL]`,
  salida 1.
- Restaurado: verde de nuevo.

Supuestos aceptados: la cadena exacta distingue el rechazo del `{"ok":false}`
de una excepción; sin `"dry"`; aviso cuando curl no conecta.
