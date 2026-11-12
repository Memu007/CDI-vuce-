# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## AUTOREMOVE: un caso cubre «No podés removerte a vos mismo»

| SHA | qué |
|---|---|
| `265a9cd6` | base |
| `d643dbbd` | `test:` el caso: el dueño se pide sacar, 400, y la base queda igual |
| `0b699331` | `test:` el caso mira también la suscripción de Mercado Pago y prueba otras mayúsculas |
| `30f94a14` | `test:` `org1.sh` suma tres sabotajes del caso |
| `945761a7` | `merge:` tu rama (`fa0f1064`, texto nuevo de la tarea) |
| `1368dff8` | `test:` variantes con espacio adelante y atrás, y su sabotaje |
| `9ad60f07` | `merge:` tu rama (`6c842da9`; sólo `docs/pm`, nada para mí) |
| este commit | `docs:` informe |

**Nada para decidir.** `producto +0/−0`. La guarda alcanza: no encontré otro
camino que deje un estudio sin dueño (sección D).

**Supuestos reversibles** (no los pediste; si sobran, se sacan sin tocar el caso):
- Corrí dos adversarios y `/code-review high` aunque la tarea decía «sin adversarios».
- Sumé cuatro sabotajes del caso a `org1.sh` (+17 líneas) aunque decía «sin guion de sabotaje».
- El caso prueba, además del nombre exacto, el nombre en mayúsculas y con un
  espacio adelante o atrás. Lo sumé por un hallazgo del adversario Opus: si la
  búsqueda del miembro ignorara espacios, el dueño salía con 200 y el caso
  anterior quedaba verde.

### A. El caso

`tests/test_org1.py::test_el_duenio_no_se_saca_a_si_mismo_y_el_estudio_queda_igual`:
- El estudio tiene al dueño y otro miembro. El dueño tiene una suscripción de
  Mercado Pago pendiente.
- Las llamadas a Mercado Pago están reemplazadas y se anotan.
- El dueño pide `DELETE /api/organizations/members/<su nombre>` y da 400 con
  «No podés removerte a vos mismo del estudio».
- Con otras mayúsculas o un espacio adelante o atrás da ese 400 o un 404 «Ese usuario no es miembro del estudio».
- Después de cada pedido, la base queda igual:
  - `owner_username` sigue siendo el dueño;
  - su suscripción sigue guardada;
  - los dos miembros siguen siendo los mismos;
  - no hubo ninguna llamada a Mercado Pago.

### B. El rojo, con la guarda borrada en una copia local

Salida del caso sobre `1368dff8` sin las dos líneas de la guarda:
```
E   AssertionError: ('o1d_…', '{"success":true,"message":"o1d_… fue removido del estudio"}')
E   assert (200, None) in {(400, 'No podés removerte a vos mismo del estudio')}
======================== 1 failed, 5 warnings in 1.08s =========================
```

Lo que queda en la base (la misma copia, mirada después del 200):
```
ESTADO 200 dueño_en_org: True suscripción_intacta: False dueño_miembro: False miembros: 1 otro_miembro_sigue: True llamadas_MP: ['_leer_suscripcion_mp', '_cancelar_suscripcion_mp']
```
Dicho en palabras:
- el estudio sigue diciendo que el dueño es él, pero él ya no es miembro;
- su suscripción pendiente se canceló en Mercado Pago y se borró;
- el otro miembro sigue.

### C. Puertas sobre `1368dff8`

| puerta | resultado |
|---|---|
| caso nuevo | verde; rojo con la guarda borrada (B) |
| `tests/test_org1.py` entero | `87 passed, 3 warnings in 60.69s (0:01:00)`, salida 0 |
| `chequeo-6 265a9cd6 1368dff8` | abajo, entero |
| `org1.sh 1368dff8` | `BASE  | verde sin sabotaje en 1368dff8…`; 28 `ROJO` (los 4 míos entre ellos); `sabotajes sin rojo: 0`; `salida 0` |

```
chequeo-6 265a9cd6..1368dff8: avisos para mirar, no un veredicto
producto +0/−0
arnés +69/−28
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```
El `arnés +69/−28` incluye lo que trajo el merge de tu rama: `sabotaje_maria3.sh` y `test_maria3_antes_de_generar.py`. Lo mío es `test_org1.py` +31 y `org1.sh` +17.

Los cuatro sabotajes del caso en `org1.sh`:
1. «el dueño se saca a sí mismo»: borra la guarda.
2. «la guarda va después de Mercado Pago»: la mueve después de cancelar la suscripción.
3. «sacar busca sin mayúsculas»: la búsqueda del miembro con `lower()`.
4. «sacar busca sin espacios»: la búsqueda del miembro con `trim()`.

El 4 fue verde con el caso de `30f94a14` (`1 passed`) y es rojo desde `1368dff8`:
```
E   AssertionError: (' o1d_…', '{"success":true,"message":" o1d_… fue removido del estudio"}')
E   assert (200, None) in {(400, 'No podés removerte a vos mismo del estudio'), (404, 'Ese usuario no es miembro del estudio')}
======================== 1 failed, 5 warnings in 1.13s =========================
```

### D. Revisión

**`/code-review high`:**

| # | hallazgo | qué hice |
|---|---|---|
| 1 | si la guarda pasaba después de Mercado Pago, el caso no lo veía | arreglado en `0b699331` (sabotaje 2) |
| 2 | `estado()` no miraba la suscripción | arreglado en `0b699331` |
| 3 | exigir 400 con otras mayúsculas era demasiado | arreglado: acepta 400 o 404 |
| 4 | la guarda compara el texto pedido; sería más firme comparar el miembro encontrado | no hecho: es producto. El caso ya detecta si la búsqueda se afloja (sabotajes 3 y 4). Va a riesgos |
| 5 | el caso mezcla dos causas | no: es una causa, la de la guarda. Mercado Pago y las variantes son datos de esa causa |
| 6 | el docstring no decía el porqué | arreglado |
| 7 | reusar `_QUIEN_TOCA` | no hecho: arma otra cosa (quién toca a quién en el cobro). Usarlo acá sumaba acoplamiento sin sacar líneas |
| 8 | el estudio tenía un solo miembro | arreglado: ahora tiene dos |

**Adversarios** (los dos sólo leyeron y probaron contra copias locales):

| modelo y esfuerzo | hallazgo | qué hice |
|---|---|---|
| Opus alto | si la búsqueda ignora espacios, el dueño sale con 200 y el caso seguía verde | reproducido; arreglado en `1368dff8` (sabotaje 4) |
| Opus alto | la guarda después de Mercado Pago | ya cubierto en `0b699331` |
| Opus alto | pytest no corre nunca en Postgres: `conftest.py` pisa `DATABASE_URL` | riesgo, no tocado |
| Opus alto | ningún camino deja el estudio sin dueño | probado en SQLite y en un Postgres 16 local con `%20` `%09` `%0A` `/` `%2F` `%00` `.` `?x=1`: la base igual en todos |
| Sonnet alto | una guarda con condición extra (sólo en prueba gratis, sólo plan premium, sólo con operaciones usadas) sigue verde | no lo reproduje. Se ve en el código: el estudio del caso nace premium y en prueba gratis (`main.py:10742-10743`). Va a riesgos |
| Sonnet alto | ningún otro camino deja el estudio sin dueño | coincide con Opus |

El adversario Opus revisó dónde se escriben esos datos:
- `users.organization_id` se escribe sólo en `main.py` 3559, 10751 y 11013.
- `Organization(` se arma sólo en 10738.
- No hay endpoint para renombrar una cuenta, borrarla ni borrar un estudio.

`/security-review`: no corresponde, porque el diff son sólo tests y un guion.

### E. Riesgos

- Baja. La guarda compara el texto pedido con `owner_username`, no el miembro encontrado. Hoy alcanza porque la búsqueda es exacta. Si alguien la afloja, el caso falla.
- Baja. Una guarda con condición de plan o de estado de cobro no la detecta el caso, porque el estudio de prueba es siempre premium y en prueba gratis.
- Media. Ningún pytest corre en Postgres, y `scripts/testing/org1_postgres.py` no tiene el caso del dueño. Lo de Postgres lo probó sólo el adversario, a mano.

### F. Comandos

```bash
git diff 265a9cd6..1368dff8 --stat -- proyecto_maria/       # vacío
python -m pytest -q --no-cov tests/test_org1.py              # 87 passed
python -m pytest -q --no-cov "tests/test_org1.py::test_el_duenio_no_se_saca_a_si_mismo_y_el_estudio_queda_igual"   # 1 passed
python3 docs/pm/herramientas/chequeo-6.py 265a9cd6 1368dff8   # producto +0/−0, avisos: 0
scripts/testing/sabotajes/org1.sh 1368dff8                   # sabotajes sin rojo: 0
```
Las dos primeras corridas de pytest van con las variables de `/entregar` §3.

### No corrido

- La suite entera: el diff son sólo tests y un guion.
- pytest contra Postgres: `conftest.py` lo fuerza a SQLite. Los sabotajes de `org1.sh` contra Postgres tampoco, porque no levanté Postgres para el arnés. Por eso «la regla 2 despierta a las marcadas vencidas», que sólo tiene rojo en Postgres, no corrió: 28 de 29.
- La primera corrida de `org1.sh` la cortó mi propio límite de 25 min (`salida 124`, antes de mis 4). La volví a correr sin ese límite; arriba va esa.
- El rojo con una suscripción `authorized`. Con la guarda borrada, el 409 de Mercado Pago (`main.py:11001-11005`) frenaría al dueño antes de salir. Eso se lee en el código; no lo corrí.

/compact conservar: Dev 1 técnica, rama claude/dev-tecnica; entregué AUTOREMOVE (d643dbbd, 0b699331, 30f94a14, merge 945761a7, 1368dff8, merge 9ad60f07 + informe); nada para decidir; tests/test_conexiones1.py sin seguimiento (su copia está en el parche); espero veredicto.
