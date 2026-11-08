# Reproducción AISLAMIENTO-2 + LIMPIEZA-1 (Dev técnica), 2026-11-08

Sobre `c86f3ff` (informe `ac52d6f`). Veredicto: **las dos aceptadas, sin
integrar** (la rama lleva debajo COBRO-MP-2+3, en devolución).

| Qué | Resultado |
|---|---|
| `chequeo-6.py 335d287 c86f3ff` | `producto +2/−3`, arnés `+229/−72`, historia vacío, avisos 0 — igual al informe |
| `test_roles_texto.py`, `test_admin_solo_admin.py`, `test_limpieza1.py` | `50 passed` |
| `limpieza1.sh c86f3ff` | base VERDE, 37 ROJO, 2 controles VERDE, `sabotajes con falla: 0`, salida 0 |
| `aislamiento2.sh prueba c86f3ff` | 10 ROJO, 2 controles VERDE, `sabotajes con falla: 0`, salida 0 |
| `aislamiento2.sh ataque c86f3ff` | 18 ROJO, `sabotajes con falla: 0`, salida 0 |
| `ataque_aislamiento.sh` sobre `c86f3ff` | `Bloqueado: 47 · Fugas: 0 · Sin probar: 0`, «PUERTA G3 PASADA», rc 0 |

Leí el diff de producto entero: `roles_de` (texto = un rol entero, lista,
tupla o set a lista, lo demás `[]`) en `require_role`, `require_admin` y
`_es_admin`; `ci.yml` queda en `python -m pytest --no-cov`; los borrados de
Google Cloud son archivos de publicación y guías.

No corrí la suite completa: tomo la de la Dev (`4587 passed`, 0 failed) y la
de la CI (`4050 passed`). Sin adversario propio: la Dev pasó Sonnet alto dos
veces, Opus alto, `/code-review` y `/security-review`, y todo lo que cambia
en producto son 2 líneas de una función con 50 casos.

## D116, confirmada en el código

`main.py` ~1388: al arrancar, cada identificador de `ADMIN_USERNAMES` se
busca por `username` **o por `email`**, y esa cuenta recibe el rol admin
guardado. PUT `/api/user/profile` (~1990) cambia el email sin verificarlo:
sólo pide formato y que no lo use otra cuenta. Si `ADMIN_USERNAMES` tiene un
email que ninguna cuenta usa, cualquiera lo toma y es admin desde el próximo
arranque. Decidido por la PM: pieza PERMISOS-1.
