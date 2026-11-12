# Reproducción de AUTOREMOVE (2026-11-12)

Entrega de la Dev técnica: código `1368dff8`, informe `77101b83`, base `265a9cd6`.
Sólo tests y arnés (`tests/test_org1.py` +31, `org1.sh` +17). Revisado por la PM
principal en un worktree aparte, sobre `1368dff8`.

## Lo reproducido

| qué | salida |
|---|---|
| el caso nuevo, sin mutar | `1 passed` |
| `tests/test_org1.py` entero | `87 passed, 5 warnings in 48.75s`, rc=0 |
| `chequeo-6.py 265a9cd6 1368dff8` | producto +0/−0, arnés +69/−28, historia vacía, avisos: 0 (igual al informe) |
| `anclas_perdidas.py 1368dff8 \| grep -c org1` | `0` |
| `org1.sh 1368dff8` entero, la copia entregada, con `PG=` (Postgres 16 local) | 29 sabotajes, 39 ROJO (29 en SQLite, 10 en Postgres), `sabotajes sin rojo: 0`, `salida 0`; de 19:25:39 a 19:52:46 UTC. Los cuatro del dueño corrieron sólo en SQLite: no tienen tercer argumento |
| lo que trae el merge (`git diff --stat HEAD origin/claude/dev-tecnica`, fuera de `docs/pm`) | sólo `org1.sh` +17 y `tests/test_org1.py` +31. El +69/−28 de `chequeo-6` suma además `sabotaje_maria3.sh` y `test_maria3_antes_de_generar.py`, que vienen de MARIA por mi rama (`e3d6be57`, ya aceptados) |

## Las mutaciones, una por una, contra el caso solo

| mutación de `remove_member` | resultado | por qué es rojo |
|---|---|---|
| guarda borrada (su B) | `1 failed` | 200 «fue removido del estudio» |
| guarda movida después de Mercado Pago (su sabotaje 2) | `1 failed` | el 400 sale, pero la lista de llamadas a Mercado Pago no queda vacía (leer y cancelar) |
| búsqueda con `lower()` (su sabotaje 3) | `1 failed` | con el nombre en mayúsculas, 200 «fue removido» |
| búsqueda con `trim()` (su sabotaje 4) | `1 failed` | con espacio adelante, 200 «fue removido» |
| **mía:** guarda movida después del `commit` | `1 failed` | el 400 sale igual, y el caso lo ve en la base: el dueño ya no es miembro y su suscripción quedó en `None`. Es la puerta «que mire el estado», sola |
| **mía:** guarda sólo con plan `premium` (el riesgo del Sonnet) | `1 passed` | el estudio del caso nace premium |
| **mía:** guarda sólo en prueba gratis (`billing_status == "trial"`) | `1 passed` | el estudio del caso nace en prueba |

Las dos verdes confirman el riesgo que la Dev leyó en el código y no corrió: una
guarda que se achica a un plan o un estado de cobro no la ve el caso. Hoy no hay
camino que la achique. Queda como riesgo, no como devolución.

Corridas descartadas, por transparencia: dos mutaciones con la condición al
revés (`plan == "free"`, `billing_status != "trial"`) dan rojo porque la guarda
nunca dispara en ese estudio; no prueban lo que quería. Y una corrida que llamé
«sabotaje 2» sólo borraba la guarda: repetía la primera. La de arriba es la buena.

## Lo que decidió la PM

- **Los supuestos reversibles quedan.** Los dos adversarios encontraron un hueco
  real del caso (espacios). Los cuatro sabotajes van en un guion que ya existía,
  y `remove_member` toca permisos y la suscripción de Mercado Pago: es de lo que
  pide revisión más fuerte (`CLAUDE.md` §3 y §6).
- **Riesgo, no devolución:** la guarda con condición de plan o de cobro.
- **Riesgo media, va de pieza siguiente:** el caso del dueño no está en
  `scripts/testing/org1_postgres.py`.

## No corrí

- El caso del dueño en Postgres: `org1_postgres.py` no lo tiene y sus cuatro
  sabotajes no llevan tercer argumento. Es la pieza siguiente.
- La suite entera: sólo tests y arnés, producto +0/−0.
- El rojo con una suscripción `authorized` (el 409 frenaría antes): lo dice el
  código, como en su informe.

## Escape

Ninguno.
