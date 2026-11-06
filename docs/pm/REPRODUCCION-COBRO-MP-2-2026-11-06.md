# COBRO-MP-2: reproducción de la PM, 2026-11-06

Producto `4f1822f`, informe `6b18c47`, rama `claude/dev-tecnica`. Base del
chequeo-6 `6f79edf`. Entorno: venv Python 3.12, SQLite para pytest, Postgres
16 local descartable. MP simulado, sin red, `GEMINI_API_KEY` vacía.

**Veredicto: devolución.** Lo de una sola cuenta aguanta: ni Opus ni Sonnet
lograron un cobro doble, servicio sin cobro ni días pagados perdidos. Lo que
vuelve está en el estudio: quién puede tocar la suscripción que paga se decide
distinto en cada ruta, y lo que la pantalla muestra sale de quien mira y no de
la cuenta que paga.

## Lo que coincide con el informe

| Puerta | Resultado |
|---|---|
| `tests/test_cobro_mp2.py` en `4f1822f` | `55 passed` (Opus y Sonnet, cada uno en su worktree) |
| `scripts/testing/cobro_mp2_postgres.py` (Opus, base propia) | 8 OK, 0 fallas |
| suite, sabotajes, chequeo-6 | no los corrí: la pieza vuelve; se corren sobre la vuelta |

## Hallazgos de los adversarios (contexto nuevo, Opus y Sonnet alto)

Los cuatro primeros los volví a correr yo (`advrun/test_adv_mp2.py` de Opus,
`4 passed`, salidas abajo).

1. **Media, nuevo. Reactivar no pide permiso** (`main.py:2160-2207`), los dos.
   `dueña cancela: 200 canceled` → `miembro cancela: 403` → `miembro reactiva:
   200 {'billing_status': 'trial'}`: un miembro deshace la cancelación de la
   dueña. Sonnet forzó en Postgres un pago que llega en medio de reactivar
   (sin candado): la cuenta pagada queda en `trial` (ventana de milisegundos).
2. **Media, nuevo (D62). El checkout cancela la pausada que paga**
   (`main.py:10983-10999` contra `2114-2121`), Opus. El miembro recibe 403 al
   cancelar, pero su checkout cancela la pausada de quien la abrió:
   `{'sus-…abrio': 'cancelled', 'nueva-1': 'pending'}`.
3. **Media, nuevo. Sacar a quien dejó un checkout sin pagar exige cancelar el
   plan** (`main.py:10092-10096`), los dos. `sacar: 409 «… abrió la
   suscripción del estudio …, primero cancelá el plan»`; con una autorizada de
   otro, el checkout de la dueña también da 409, así que la única salida
   cancela la suscripción que sí paga. Riesgo declarado; no lo acepto.
4. **Baja-media, nuevo. «Próximo cobro» y «Cancelar plan» salen de quien
   mira** (`main.py:3269-3273`), los dos. En un estudio con la de otro miembro
   autorizada: `dueña: renueva False, suscripcion_abierta False`, `abrio:
   renueva True`. La dueña ve «Activo hasta» y MP le va a cobrar al estudio.
5. **Baja-media, nuevo. El estudio entero espera mientras se habla con MP**
   (`_cuenta_con_suscripciones`, `main.py:10877`), los dos. Con MP a 4 s por
   llamada, el aviso de pago de la org esperó 11,5 s y otro miembro que genera,
   también. Las llamadas por httpx tienen `timeout=10`; la creación por el SDK
   usa el suyo por defecto (Opus: 60 s), así que con MP caído la espera supera
   los «unos 20 s» del informe y el aviso de pago puede pasar del tiempo con el
   que MP lo reintenta.
6. **Baja, nuevo. Texto del 409** (`main.py:10921-10922`), Sonnet. Con el
   estudio en `past_due` dice «Se renueva sola», y dice que sólo la cancela
   quien la abrió, cuando también puede la dueña.

## A la cola (decidido por la PM)

- Un estado de MP que la lista no conoce (p. ej. `expired`) deja cancelar y
  pagar en 503 para siempre, con «probá en unos minutos». Cae en el supuesto
  aceptado sobre los estados de MP.
- «Próximo cobro» con una suscripción que se canceló desde MP o que nunca se
  autorizó: cae en el riesgo ya aceptado.
- Textos de antes: `SUBSCRIPTION_PAST_DUE` dice «pago pendiente» a quien
  canceló y dejó vencer (`main.py:1800`, `:2192`); «Tu período pagado ya
  terminó» a una prueba; `app_v2.js:769` dice «Tu prueba gratis terminó» a
  quien pagaba; `main.py:1812` le dice «Cancelaste tu suscripción» a un miembro
  cuya dueña canceló.

## Lo que aguantó

Cancelar con PUT fallido, sin conexión o con estado distinto de `cancelled`:
503 sin tocar nada. Un 404 de MP no traba la cuenta. Un aviso de pago después
de cancelar suma desde el fin del período. Pagos repetidos o fuera de orden no
se aplican dos veces. Sin token y fuera de desarrollo o pruebas no hay demo ni
dice «activada». Orden de candados sin ciclos. Ningún miembro abre una segunda
suscripción con una autorizada de otro.
