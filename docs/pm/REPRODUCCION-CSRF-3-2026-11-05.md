# Reproducción de CSRF-3 — 2026-11-05

Entrega: rama `claude/dev-tecnica`, producto y pruebas hasta `9fe55d4`, informe
`9c80525`. Base `d21e16d`. Worktree de PM `/tmp/cdi-pm/wcsrf3` en `9fe55d4`.

**Veredicto: aceptada.**

## Lo que corrí yo (salida exacta, recortada)

```
== test_csrf (test_csrf.py + test_auth_invalid_plan.py)
39 passed, 7 warnings in 12.22s
== test_csrf enforce=0
38 passed, 3 warnings in 12.16s
== test_csrf enforce=1
38 passed, 3 warnings in 12.30s
== chequeo6
chequeo-6 d21e16d..9fe55d4: avisos para mirar, no un veredicto
producto +14/−2
arnés +163/−8
historia (grep de §6, sin líneas movidas): vacío
avisos: 0
== csrf3   salida 0, 8 ROJO, sabotajes con falla: 0
== csrf2   salida 0, 10 ROJO, sabotajes con falla: 0
== csrf1   salida 0, 8 ROJO, sabotajes con falla: 0
== suite (SQLite, ENVIRONMENT=test)
4450 passed, 121 skipped, 3 xfailed, 98 warnings in 596.82s, rc=0
```

Coincide con el informe: 4450 passed, 8 sabotajes propios, csrf1 y csrf2
siguen en rojo.

## Adversarios (Opus alto y Sonnet alto, sobre `9fe55d4`)

Sin hallazgo que bloquee: la emisión sólo ocurre con sesión verificada, nunca
reemplaza un token que ya está y no se emite con sesión vencida o revocada.
Van a la cola de limpieza, no a esta pieza:
- `GET /dashboard` consulta la base: si la base no responde, la página da 500
  en vez de servirse (riesgo que la Dev ya declaró).
- Carrera del token al abrir la v2 con dos respuestas en vuelo: el navegador
  se queda con el último `Set-Cookie`; no reproducida como fuga.

## Notas

- El merge de `9fe55d4` trae también `4dd2d25`, `4ae523c` y `3f3234d`:
  comentarios y arnés de COBRO-CORTE-1, que ya estaba en la rama sin aceptar
  desde `e0b8626`. La suite de arriba corrió con ellos.

## No corrido por mí

- Playwright de `pantalla_csrf3.js` fuera del sabotaje `csrf3.sh` (que sí lo corre).
- Suite con el entorno de la CI.
