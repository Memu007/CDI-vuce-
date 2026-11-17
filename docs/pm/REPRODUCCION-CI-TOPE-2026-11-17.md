# Reproducción CI-TOPE (2026-11-17 00:49 UTC)

Pieza de la Técnica: el job `tests` de `.github/workflows/ci.yml` corta a los 30 minutos en vez de 20
(sí de Emi al punto 14, 17/11 00:41 UTC). Base `a0091a94`, pieza `c721f7fc`, informe `a0299443`.

## Corrido por la PM

| Qué | Resultado |
|---|---|
| `git log a0091a94..origin/claude/dev-tecnica` | dos commits: `c721f7fc` (ci.yml) y `a0299443` (informe) |
| `git diff a0091a94 c721f7fc -- . ':!docs/pm'` | una línea: `timeout-minutes: 20` → `30` en `tests` |
| `yaml.safe_load` de `ci.yml` en `c721f7fc` | `{'tests': 30, 'e2e-maria': 10}` |
| `grep -n -i -E 'timeout\|--max\|pytest'` en `ci.yml` | sólo las líneas 15 (`30`), 49 (`python -m pytest --no-cov`) y 54 (`10`): ningún paso trae otro tope |
| Informe | declara la CI como no corrida; lo cerrado que sale es la vuelta anterior; el `/compact conservar` está al día |

## No corrido

- La CI. Corre sólo en un push o una PR a `main`; los 30 minutos se prueban recién en la próxima PR de
  publicación.

## Veredicto

Aceptada sobre `c721f7fc` e integrada (fast-forward a `a0299443`). No es pieza del roadmap.
Riesgo que queda, el del informe: si la suite pasara los 30 minutos, el corte vuelve sin rojo antes;
hoy tarda unos 23.
