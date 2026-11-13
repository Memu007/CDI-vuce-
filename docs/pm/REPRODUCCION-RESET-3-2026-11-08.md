# Reproducción de RESET-3 (PM principal, 2026-11-08 21:40 UTC)

Pieza de MARIA: tope por cuenta al pedir el reset de contraseña (D132 a).
Base `2fba5c9`, producto y pruebas hasta `8fda3d2`, informe en `dbe2d2c`.
Auth: revisión fuerte (adversario Opus alto, sabotajes en SQLite y Postgres).

## Veredicto

Aceptada sobre `8fda3d2`, sin integrar (D136). Igual al informe.

## Lo que corrí

- `chequeo-6.py 2fba5c9 8fda3d2`: producto +14/−7, arnés +213/−3, historia
  vacía, avisos 0.
- `reset3.sh 8fda3d2` sin PG: `BASE | 74 passed`, 7 ROJO, `sabotajes sin rojo: 0`,
  salida 0.
- `reset3.sh 8fda3d2` con `PG_URL` (mi PG 16, 55462): lo anterior más
  `BASE | Postgres: fallas: 0` y `ROJO | el tope se cuenta con la cuenta
  trabada`, `sabotajes sin rojo: 0`, salida 0. Log `/tmp/cdi-pm/rep-r3pg2.log`.
  La primera corrida con PG dio rojo de base sólo porque el servidor no había
  arrancado (error mío de `-l`); no es de la pieza.
- Mi negativo: la clave por `request.email` en vez de por username →
  `FAILED test_reset_tres_por_hora_por_cuenta_aunque_cambie_la_ip` (el caso
  usa variantes de mayúsculas).

## Adversario (Opus alto, contexto nuevo, sin red)

Nada grave. Probó variantes de email (espacios, mayúsculas, ＠, NBSP,
`​`), 30 pedidos simultáneos en SQLite y 40 en PG 16 con 4 workers
(fila nueva y fila vencida): nunca más de 3 links. Ninguna clave ajena empieza
con `reset-cuenta:`; un username no tiene `:` ni pasa 30 caracteres. La
respuesta topada es idéntica a la de un email inexistente (200, mismo cuerpo);
el tiempo queda más cerca del inexistente que de la cuenta libre. El hint de
desarrollo no se filtra. Reset legítimo y login con la clave nueva, bien.

Dos bajos, misma familia que los riesgos ya anotados de recuperar
(`REPRODUCCION-ABUSO-2-2026-11-07.md`):

1. Ventana fija: 6 links en 3601 s (5 en 2 s en el borde). Promedio 3/h.
   Ya informado por MARIA. Queda como riesgo.
2. Datos viejos con el mismo email en distintas mayúsculas en dos cuentas:
   3 links por cuenta, 6 al buzón. El alta y el perfil ya no dejan crearlos;
   va con el índice sobre `lower(...)` que espera a Emi.

## Decisiones

- D138: (a), decidida por la PM. Quien conoce el email deja a la cuenta sin
  links una hora; igual que recuperar y lo que pidió D132 (a). Un mail de aviso
  (c) sería funcionalidad nueva.
- Supuestos de MARIA aceptados: el tope por cuenta depende de
  `limiter.enabled`; un email inexistente no cuenta en ninguna clave.
