# Medición de subagentes

Una fila por subagente en cada revisión. Se revisa con números para decidir
qué modelo y esfuerzo rinden.

- **Hallazgos:** cuántos devolvió.
- **Reproducidos:** cuántos se confirmaron con evidencia.
- **Nuevos:** cuántos no había visto nadie (ni la Dev, ni sus casos, ni la PM).

| Fecha | Pieza | Quién lo usó | Modelo y esfuerzo | Hallazgos | Reproducidos | Nuevos |
|---|---|---|---|---|---|---|
| 2026-10-06 | AUDITORIA (copia vieja CDI, línea equivocada) | PM | Sonnet medio (ops) | 12 | — (línea equivocada: no se reprodujo; algunos puntos se pasaron como hipótesis al de datos) | — |
| 2026-10-06 | AUDITORIA-VUCE (cobro y sesión) | PM | Opus alto | 12 | 4 por la PM (H2 MARIA sin cortar por impago, H9 admin para cualquiera: corridos; H3 cancelar no cancela en MP: por código; H1 aviso sin firma: por el test G7). El subagente casi no reprodujo nada | 12 |
| 2026-10-06 | AUDITORIA-VUCE (datos y operación) | PM | Sonnet alto | 11 | 6 por el subagente con salida (corte masivo al arrancar, /health 200 con base caída, XFF falsificable, bloqueo del event loop, dev_detail, quotes sin dólar); 0 re-corridos por la PM todavía | 9 |
| 2026-10-06 | AUDITORIA-VUCE (suite y G1) | PM | Haiku | 1 | 0: «G1.5 no corta» era falso (la PM lo corrió: RuntimeError, salida 1). La suite sí: 680 passed, 102 skipped, 0 failed | 0 (1 equivocado) |
