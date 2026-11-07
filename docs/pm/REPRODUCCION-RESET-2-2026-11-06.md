# Reproducción RESET-2 (Dev MARIA) — 2026-11-06

Entregado: `99d3f69` (producto `249cfd4`, pruebas y sabotaje `99d3f69`;
informe `3362d25`). Base de la pieza: `7417fe8`.
Entorno de la PM: venv, sin red, `GEMINI_API_KEY` vacía, `ENVIRONMENT=testing`.

## Puertas

| Puerta | Informe | PM |
|---|---|---|
| producto | `+8/−2`, un ayudante `_pista_dev_habilitada` usado en reset y recuperar usuario | igual |
| `tests/test_email1.py` + `tests/test_reset1.py` | verdes | `32 passed in 23.49s` |
| rojo con la puerta vieja (`not IS_PRODUCTION`) | 2 failed | `2 failed, 24 deselected` en `-k pista_de_dev` |
| suite completa | `4991 passed` | no corrida por la PM: el producto cambia una condición, y las dos suites que la usan están verdes |
| `email1.sh` entero | rojo el sabotaje nuevo | no corrido entero: queda como puerta de la PM antes de publicar |

## Negativo de la PM (proceso nuevo, la bandera se calcula al importar)

`_pista_dev_habilitada(email_sent)` con cada valor de `ENVIRONMENT`:

| `ENVIRONMENT` | sin SMTP | con SMTP |
|---|---|---|
| ausente | False | False |
| `development` | False | False |
| `test` | False | False |
| `Testing` | False | False |
| `testing` (las suites) | True (las pruebas de email1 leen la pista) | — |
| `production` | la app no arranca sin `DATABASE_URL` | — |

El caso de la prueba de la Dev cambia las banderas con `monkeypatch`; el
negativo de arriba confirma lo mismo calculando las banderas desde el entorno.

## Lo que encontró la Dev fuera de la pieza

D91 y D92: con `ENVIRONMENT` ausente o mal escrito, la app abre puertas de
desarrollo (contraseña guardada aceptada tal cual en el login, usuarios demo
con admin, webhook de MP sin firma, link de reset por stdout). La PM lo
verificó en `main.py` de `claude/dev-maria` (líneas 3179, 1606–1627 y 11292).
Pasa a la pieza ENTORNO-1.
