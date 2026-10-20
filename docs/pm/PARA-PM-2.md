# Dev 2 → PM

## MARIA-5d — bruto de una unidad con kg y bruto explícito de la línea

**Resultado: producto y focales terminados; aceptación pendiente de las puertas no corridas.** Rama local `codex/maria5d-unit-kg`, base `d22ff1a`. Producto `b3fd518` y `8b8b789`; pruebas `abe05ae`, `67d18a8`, `eff9dea`; changelog `000a74d`. SHA completo probado: `eff9dea`.

- «Peso bruto unit (kg)», «Gross weight unit (kg)» y «Unit gross weight» conservan el bruto unitario: 10 × 3 kg llega por upload y genera `QARTKGRNET=30.000`, con mapeo automático o guardado.
- La devolución PM sobre «Unit gross weight per line» y «Unit gross weight line» se corrigió en la misma guarda: 30 kg / 10 unidades conserva 30 kg en la línea, sin multiplicarlo a 300. Neto conserva prioridad; bruto total/plural conserva división.

## Evidencia y reproducción

```bash
# Desde esta rama; entorno inventado descrito abajo.
/private/tmp/cdi-codex-pm-venv/bin/python -m pytest -q --no-cov tests/test_maria5d.py tests/test_maria5d_unit_kg.py tests/test_maria5_peso_excel.py tests/test_devolucion2_maria5_ncm.py tests/test_generar_maria_txt.py tests/test_maria_subitems.py
bash scripts/testing/sabotaje_maria5d.sh eff9dea /private/tmp/cdi-codex-pm-venv
```

La suite y el preflight quedaron en `/private/tmp/cdi-maria5d-suite/suite.log`. No repetir para cerrar esta entrega.

| Puerta | Resultado |
|---|---|
| Rojo inicial sobre base, informado por la PM | `6 failed, 7 passed` |
| Rojo de devolución inglesa, antes de `8b8b789` | `2 failed, 4 passed, 9 deselected` |
| Focales sobre producto `8b8b789` (148 casos; últimos commits sólo script) | `148 passed, 3 warnings in 10.97s` |
| Sabotaje `eff9dea` | base `80 passed`; `OK: los 11 sabotajes dan rojo por la razón esperada` |
| Suite completa `eff9dea`, preflight OK | `1570 passed, 102 skipped, 2 xfailed, 28 warnings in 378.14s`; cobertura `50.47%` (mínimo `38%`); `FIN SUITE exit=0` |

Focales: `test_maria5d.py`, `test_maria5d_unit_kg.py`, `test_maria5_peso_excel.py`, `test_devolucion2_maria5_ncm.py`, `test_generar_maria_txt.py`, `test_maria_subitems.py`. Incluyen referencias anonimizadas de MARIA; no se usaron documentos privados.

Entorno: Python 3.12.8 y venv heredado `/private/tmp/cdi-codex-pm-venv` (NO instalación limpia de requirements), claves inventadas, conectores fake, endpoints de dólar/ARCA en loopback cerrado, SQLite temporal. Preflight verificó API propia en localhost:18982, health, frontend, tablas y checkout limpio. Primer intento de bind bloqueado por sandbox; reejecutado con permiso local. Corrida de suite anterior en `000a74d` interrumpida al llegar devolución PM: no cuenta como resultado. Corrida de sabotaje anterior invalidada por desajuste de patrón/SHA durante intervención: reemplazada por 11/11 sobre `eff9dea`.

## Pendientes y límites

- E2E y las tres pantallas: **no corridas**. No se operó navegador mediante shell.
- Kit SIM real: **no corrido**. Sin publicación ni push, según instrucción actual PM.
- Sabotaje EXCEL-1 histórico «mapeo guardado deja afuera lo detectado»: mutar `elegido = g or d` a `elegido = g` deja el test señalado verde (`1 passed`) tanto en base `d22ff1a` como en entrega `000a74d`. `_mapeo_efectivo` tiene AST idéntico entre base y `eff9dea`. Es una carencia de prueba anterior, no una regresión de esta pieza; no se amplió alcance para corregirla.

Autorrevisión del diff contra base: helper de bruto, pruebas sintéticas, sabotajes y changelog; sin cambios de exportación ni otros clasificadores.

**D1.** Mantener pendiente aceptación/publicación hasta completar e2e y pantallas. Recomendación: verificar esas puertas en el entorno habilitado, sin tocar producción.

Última vuelta: 2026-10-20 11:42 UTC
Contexto: ~50 %
