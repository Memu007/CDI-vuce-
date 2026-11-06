# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

> **PYPDF-1** ya la aceptaste (974263e, D89 a / D90 a); gracias. RESET-2 va
> encima. Traje tu rama con merge (`3d5451c`): veredicto y limpieza tanda 3,
> todo docs.

## RESET-2: **entregada**. Producto `249cfd4`, pruebas+sabotaje `99d3f69`, informe en el commit siguiente. SHA entregado `99d3f69` (2026-11-06)

**Resultado.** El token de reset y el nombre de usuario se devolvían en la
respuesta (comodidad sin SMTP) siempre que `ENVIRONMENT` no fuera
«production». Con `ENVIRONMENT` sin poner —ni producción ni prueba— el token
de reset se filtraba en la respuesta HTTP. Ahora un único helper
(`_pista_dev_habilitada`) los devuelve sólo en el entorno de prueba
(`IS_TESTING`, es decir `ENVIRONMENT=="testing"`), nunca cuando falta. Vale
para los dos lugares (reset y recuperar usuario); el chequeo repetido queda en
uno (§6). El marcador del repo es `testing` (lo pone `conftest.py`), no el
literal «test»: gaté sobre el `IS_TESTING` que ya usa el resto de `main.py`.

## Decisiones

- **D91 (seguridad, ALTA — fuera de RESET-2, te lo propongo como pieza):** la
  misma raíz `not IS_PRODUCTION` deja dos agujeros en el **login** cuando
  `ENVIRONMENT` falta (`main.py:3181` y el alta de usuarios demo en el
  `lifespan`, `main.py:1608`):
  1. `demo/demo123` entra como **admin** por el camino normal (sin
     prerrequisito).
  2. El fallback de contraseña plana compara `stored_password == password`:
     quien conozca el **hash** de una cuenta entra presentándolo como
     contraseña, y encima la «migra» (rehashea el hash y la clave real queda
     inválida).
  El adversario lo reprodujo con `ENVIRONMENT` sin poner (200) vs
  `production` (401). **Recomiendo una pieza chica que gate esto en el entorno
  de prueba (o saque el fallback plano y los demo de producción), como hicimos
  en reset.** No lo toqué: es login, fuera de RESET-2.

- **D92 (seguridad, media — fuera de RESET-2):** mismo patrón
  `not IS_PRODUCTION` en otros dos lugares: la validación de firma del webhook
  de Mercado Pago (`main.py:11294`, acepta cualquier firma si falta
  `MP_WEBHOOK_SECRET` y `ENVIRONMENT`) y el `send_email` sin SMTP, que imprime
  el link de reset entero en stdout (queda en los logs con `ENVIRONMENT` sin
  poner; no llega al cliente). **Recomiendo barrerlos en la misma pieza que
  D91.**

- **D93 (reversible, baja):** el script manual `scripts/test_reset_flow.py`
  dependía de la pista bajo `ENVIRONMENT=development`; ahora necesita
  `ENVIRONMENT=testing` (el token sigue en stdout). No lo toqué (es script
  manual, no de la suite). **Recomiendo (a): dejarlo y que el script use
  `testing`.** Opción (b): que lo arregle una limpieza.

Próxima D libre: **D94**.

## Rojo antes del arreglo

Con `ENVIRONMENT` ausente (`IS_PRODUCTION=False`, `IS_TESTING=False`), sobre el
código viejo (`not IS_PRODUCTION`): `test_la_pista_de_dev_solo_en_el_entorno_de_prueba`
daba `2 failed` (el token y el usuario volvían igual). Con el arreglo, `2 passed`.

## Autorrevisión

- **Adversario Sonnet alto:** confirmó que RESET-2 cierra la fuga y que no
  queda ningún camino de vuelta del token al cliente fuera de prueba.
  Encontró D91/D92/D93 (la misma raíz en login/webhook/stdout), reproducidos.
- **`/code-review high`:** sin bug en el diff; marcó dos AVISO de §6 en mi
  helper (nombre de pieza e historia en el comentario, y 4 líneas) →
  **corregidos** (comentario de 2 líneas sin historia; rehíce los dos commits
  locales sobre `7417fe8`). También señaló D91/D92 como preexistentes.
- **`/security-review`:** sin vulnerabilidad nueva en el diff; el gate
  `IS_TESTING` es un subconjunto estricto de `not IS_PRODUCTION`, así que no
  amplía la exposición en ningún entorno.

## Riesgos / límites

- La prueba parchea las constantes `IS_PRODUCTION`/`IS_TESTING` (congeladas al
  importar), no la variable de entorno. Si un refactor futuro leyera
  `os.getenv` directo, la prueba no vería la regresión. Es el modo que usa el
  resto de las pruebas de estas rutas.
- Si un despliegue real quedara en `ENVIRONMENT=testing` por error, la pista
  se filtra igual que antes: igual de malo, no peor (no se puede atar a
  `PYTEST_CURRENT_TEST` porque los motores usan un server real con `testing`).
- D91/D92 siguen abiertos hasta que decidas la pieza.

## chequeo-6 (`7417fe8` → `99d3f69`)

```
chequeo-6 7417fe8..99d3f69: avisos para mirar, no un veredicto
producto +8/−2
arnés +22/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11944 → 11950
avisos: 0
```

## Puertas (SHA entregado `99d3f69`)

| Puerta | Resultado |
|---|---|
| suite completa | `4991 passed, 335 skipped, 3 xfailed, 95 warnings in 886.49s`, salida=0 (2 nuevas de RESET-2) |
| `compileall proyecto_maria` | `compileall=0` |
| sabotaje de la pieza | `email1.sh`: el sabotaje «la pista de dev vuelve con ENVIRONMENT que falta» da ROJO (verificado directo: `2 failed` en `test_la_pista_de_dev_solo_en_el_entorno_de_prueba`). El `email1.sh` entero es puerta tuya antes de publicar. |
| `/code-review high`, `/security-review`, adversario Sonnet alto | Ver «Autorrevisión». |

## Comandos copiables

```bash
# 1) el gate: sólo el entorno de prueba
git -C /home/user/CDI-vuce- show 249cfd4 -- proyecto_maria/main.py
# 2) rojo del caso con el gate viejo (en un worktree descartable)
#    (sacar IS_TESTING y poner not IS_PRODUCTION → 2 failed)
# 3) la D91 (login), para que la veas:
sed -n '3178,3183p' /home/user/CDI-vuce-/proyecto_maria/main.py
```

## Archivos de producto tocados

- `proyecto_maria/core`/… no; sólo `proyecto_maria/main.py` (helper + los dos
  lugares) y `CHANGELOG.md`.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP, aviso a la PM session_01B7FVQspcEHF7PqNv797wNM priority next. RESET-2 ENTREGADA: producto 249cfd4 (helper _pista_dev_habilitada: token/usuario de reset vuelven en la respuesta sólo con IS_TESTING, nunca con ENVIRONMENT ausente), pruebas+sabotaje 99d3f69, informe en el commit siguiente, SHA 99d3f69. Antes entregué PYPDF-1 (f3bd528, informe 7417fe8) sin integrar. Decisiones abiertas para la PM: D91 (ALTA, fuera de alcance: login con ENVIRONMENT ausente deja entrar demo/demo123 como admin y entrar con el hash como contraseña — main.py:3181 y demo en lifespan 1608; recomiendo pieza chica que gate en prueba), D92 (webhook MP main.py:11294 y link de reset en stdout, misma raíz), D93 (test_reset_flow.py manual ahora necesita ENVIRONMENT=testing). Próxima D libre D94. Sigue: ABUSO-1 (orden del roadmap tras RESET-2). Reglas de Emi: nada se publica sin su «dale» para el SHA (no propongo SHA; la rama lleva e0b8626 no aceptada), nunca main, nunca force/amend de lo ya pusheado (rehíce 249cfd4/99d3f69 porque eran locales, sobre el pusheado 7417fe8), sin secretos ni datos reales, subagentes hasta alto sin Fable, no uso advisor, Postgres local 55432. conftest pisa ENVIRONMENT a 'testing'.

---

## ABUSO-1 (en pausa por el corte, sin commitear nada)

Arranqué la investigación; **no toqué producto ni pruebas** (sólo leí código y
reproduje en un PG descartable local). Dónde quedó cada punto de la devolución
sobre `43916a7`, contra HEAD actual:

- **D44 (2ª conexión del login):** ya está arreglado por `ce7cd9d` (SESION-1
  v2: `limites_auth` usa la conexión del pedido). Falta: una prueba de
  concurrencia en PG que lo pruebe (verde en HEAD) y un sabotaje que devuelva
  la 2ª conexión.
- **Punto 1 (duración de bloqueos):** abierto. Las pruebas mueven el reloj
  justo pasado el tope, así que el mutante `bloqueo=60` sobrevive. Falta:
  casos «a los 14 min sigue 429, a los 16 pasa» (bloqueo de 15 min) y el
  equivalente para la ventana de recuperar (3600 s), con la fixture `reloj`.
- **Punto 2 (claves 121-300 en PG):** por confirmar el mecanismo exacto;
  `hash_password` usa `bcrypt.hashpw`, que en bcrypt moderno **levanta** con
  >72 bytes → probable 500 en registro/reset/cambio. Falta reproducir y topear
  el largo antes de la base + matar el mutante `len(clave) <= 300`.
- **Punto 3 (surrogate 500 en recover-username):** abierto. `main.py:1791`
  `request.email...encode()` levanta `UnicodeEncodeError` con un surrogate
  suelto → 500. Falta hacerlo a prueba de surrogates + caso.

Retomo con `/respondio` cuando se levante el corte. Próxima D: D94.
