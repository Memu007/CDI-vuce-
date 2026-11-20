# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CI-TOPE: el job `tests` de la CI corta a los 30 minutos

| | SHA |
|---|---|
| base (tu rama, traída por fast-forward) | `a0091a94` |
| `ci.yml`: `tests` 20 → 30 | `c721f7fc` |
| informe | el commit `docs:` que trae este archivo |

**Nada para decidir.** No hay supuestos.

### Comandos

```bash
git diff a0091a94 c721f7fc -- . ':!docs/pm'
# tiene que mostrar una sola línea cambiada: timeout-minutes 20 → 30 en el job tests
python -c "import yaml;d=yaml.safe_load(open('.github/workflows/ci.yml'));print({k:v.get('timeout-minutes') for k,v in d['jobs'].items()})"
# tiene que mostrar {'tests': 30, 'e2e-maria': 10}
```

### Lo que ya corrí

- `git diff a0091a94 c721f7fc -- . ':!docs/pm'`:

```
diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
index 18128e36..22bc5305 100644
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -12,7 +12,7 @@ permissions:
 jobs:
   tests:
     runs-on: ubuntu-latest
-    timeout-minutes: 20
+    timeout-minutes: 30
 
     steps:
       - name: Checkout
```

  `--numstat`: `1	1	.github/workflows/ci.yml`.
- Carga del YAML con `yaml.safe_load`:
  - sobre `c721f7fc`: `{'tests': 30, 'e2e-maria': 10}`;
  - sobre la base `a0091a94`: `{'tests': 20, 'e2e-maria': 10}`.
- `ci.yml` no tiene otro `timeout`: el `grep -i timeout` da sólo las líneas 15 y 54.

### Qué no se corrió

- **La CI.** Corre sólo en un push o una PR a `main`. Se ve en la próxima PR de publicación.
- Como pide la tarea, tampoco corrí sabotaje, `CHANGELOG`, `chequeo-6`, adversarios ni pytest.
  `ci.yml` no es producto ni prueba.

### Riesgo

Si la suite pasara los 30 minutos, el corte volvería a llegar sin ningún rojo antes.
Hoy tarda unos 23 minutos: el margen es de unos 7.

Ahora sigo esperando a Emi (D182, D206). No arranco otra cosa. **Próxima D: D231.**

/compact conservar: Dev 1 técnica, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica, base 3874a1d2 (rama PM traída con merge). Tarea activa CONEXIONES-1 en dos piezas: primero CONEXIONES-1-NOKEY (D206 a) sola; apenas la entregue, CONEXIONES-1-PRODUCTO (D182, D183, D188) sobre ella. D205 no entra. Revisión fuerte: /security-review, adversarios con Postgres 16 sin red y GEMINI_API_KEY vacía, suite completa, e2e_maria.sh, sabotaje propio. Próxima D: D231. Sin advisor, nunca main, sin secretos, test_conexiones1.py no se sube.
