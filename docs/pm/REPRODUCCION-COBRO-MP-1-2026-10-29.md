# Reproducción de COBRO-MP-1 (2026-10-29)

Entrega de la Dev técnica: producto `551de83`; pruebas y sabotajes hasta
`784e793`; informe en `0a8a87a` (rama en `93ade49`).

## Lo que corrió la PM, sobre `784e793`

- Las 7 pruebas del cobro del informe:
  `220 passed, 3 warnings in 71.76s` (igual que el informe).
- `cobro_mp1.sh`: 68 «ROJO  |», «BASE  | la carrera en Postgres, en verde»,
  «BASE  | la pantalla, en verde», «sabotajes con falla: 0», «fin rc=0».
- **Negativo de la PM: dos pagos distintos de la misma cuenta a la vez**, en
  un Postgres 16 descartable (`con_pg16.sh`), con el simulador de Mercado
  Pago de `cobro_mp1_postgres.py`. Los dos avisos registran su pago antes de
  que alguno guarde (la misma técnica que la Dev usa para el mismo pago dos
  veces):

  ```
  recargas: pasaron=['aplicado', 'aplicado'] resp=[(200, None), (200, None)] extra 0 -> 10 filas=[('r1-…', 'aplicado'), ('r2-…', 'aplicado')]
  FALLA | dos recargas pagadas suman 20 (0 -> 10)
  planes: pasaron=['aplicado', 'aplicado'] resp=[(200, None), (200, None)] fin … -> … (30 días) filas=[('p1-…', 'aplicado'), ('p2-…', 'aplicado')]
  FALLA | dos pagos de plan suman 60 días (30)
  ```

  Los dos pagos quedan «aplicado» y la cuenta recibe uno: el cliente paga
  dos veces y se le acredita una, sin aviso. La causa: el aviso lee la
  cuenta (`User` y también `Organization`) sin `with_for_update`, y el
  segundo guardado pisa al primero. Ya pasaba antes de la pieza (en
  `957539d` tampoco se bloquea), pero la pieza es la que promete que cada
  pago se aplica una vez y entero. La ventana natural es de milisegundos
  (entre leer la cuenta y guardar); el arreglo es barato, el mismo candado
  que ya usa el checkout.

## Adversario Opus alto (contexto nuevo, sobre `784e793`)

La PM corrió sus pruebas de sondeo en su worktree (cada una afirma lo que
debería pasar): `8 failed, 1 passed`, los 8 rojos que él informa. Y corrió
`cobro_mp1_postgres.py` en PG16:

```
FALLA | un pago se aplica una vez ({"success":true,"skipped":"pago rechazado: sin fecha de aprobación legible"} / …)
FALLA | los dos avisos pasaron el «¿ya está?» (['rechazado', 'rechazado'])
FALLA | dos a la vez: uno aplicado y otro salteado ([200, 200], [… 'sin fecha de aprobación legible' …])
FALLA | dos a la vez suman una sola recarga (0 → 0)
fallas: 4
```

1. **Media: volver de Mercado Pago antes del aviso y tocar otra vez
   «Activar plan ahora» cancela la suscripción ya cobrada.** Con la cuenta
   en `past_due` (o `canceled` con fin futuro), el 409 del checkout no
   frena: cancela la suscripción «authorized» S1 y crea S2. El pago de S1
   se aplica igual, pero queda sin débito automático mientras
   `/api/billing/me` dice `renueva: True`; si también paga S2, son dos
   cobros (59 días). Choca con D7.2 de COBRO-MP-2 y con
   `test_sin_cuenta_vigente_la_vieja_se_cancela_antes_de_crear`, que lo
   fija a propósito.
2. **Media (de pruebas): la prueba D31 en Postgres quedó muerta.**
   `cobro_mp1_postgres.py` no pone `date_approved`; desde A todo pago se
   rechaza antes de la carrera, y el script de sabotajes corre sólo
   `cobro_mp1d_postgres.py`. No queda prueba en Postgres de que el mismo
   pago dos veces a la vez se aplica una vez. La PM lo sube de baja-media
   a media: es la red de lo que la pieza promete.
3. **Baja: la pantalla vieja (v1) cuenta 2 operaciones por exportación con
   cliente elegido** (guarda `GROUPED_<ts>` y después exporta). Regresión
   de B.
4. **Baja: una exportación con id de 44 a 50 caracteres cuenta doble**
   (`MARIA_EXPORT_{id[:50]}` no entra en `_ARCHIVO_MARIA`).
5. **Baja: una importación con id `EXPORT_<x>`** reusa la operación de la
   exportación `<x>` (sólo armando el pedido a mano).
6. **Baja: cancelar mientras llega el primer pago** deja la cuenta
   `active`, sin suscripción y con +30 días (pagó y recibe su mes).
7. **Baja, preexistente:** una recarga revive extras vencidos y el tope de
   100 se come operaciones pagadas (igual en `8b45207`).
8. **Baja, por lectura:** `_pago_un_plan_mp` manda al checkout a una prueba
   cuya única compra fue una recarga (lado conservador).

Mutantes: tres mueren; `aprobado < desde` → `<=` vive, sin caso realista.

## Adversario Sonnet alto (contexto nuevo, sobre `784e793`)

La PM corrió sus pruebas de sondeo en su worktree (`4 failed, 15 passed`;
las que pasan imprimen el defecto en vez de afirmarlo) y leyó el SDK de
Mercado Pago del venv: `http_client.py` devuelve
`{"status": api_result.status_code, "response": …}` sin levantar excepción;
sólo reintenta 429 y 5xx.

```
HTTP 404 -> 200 {"success":true,"skipped":"status=404"}
pago de usuario 'org' -> 400 {"detail":"external_reference desconocida"}
cancel: 200 {"success":true,"billing_status":"canceled",…}
DESPUES me: active renueva False | sub en MP: cancelled | org: active
cancel por el otro miembro: 200 {"success":true,"billing_status":"canceled",…}
{'external_reference': None} -> 500 …   {'payer': None} -> 500 …   {'card': None} -> 500 …
checkout: 200 nueva-1
PUT: ['https://api.mercadopago.com/preapproval/sus-adv_dc_…'] | estado sub vieja en MP: cancelled
topup con 100 extra: 200 {…"type":"topup"…}
```

1. **Alta: si Mercado Pago contesta 401, 403 o 404 al consultar el pago,
   el aviso responde 200 y el pago se pierde sin rastro.** Ni fila, ni
   panel, ni log de aviso; Mercado Pago no reintenta. Con el token vencido
   se pierden todos. Ya era así en `957539d`, pero la pieza endureció las
   otras tres lecturas (503) y dejó ésta: es la misma familia que D9.
2. **Media: el checkout cancela la suscripción recién cobrada** (igual que
   el 1 de Opus).
3. **Media, preexistente: en una organización, «Cancelar plan» actúa sobre
   la fila del usuario.** El dueño cancela en Mercado Pago pero la org
   sigue `active`; un miembro que no pagó «cancela» y la suscripción sigue
   cobrando.
4. **Media-baja, preexistente: una recarga con el tope de 100 se cobra y
   no acredita nada** (con 95, acredita 5), y queda «aplicado». El link se
   arma igual.
5. **Baja: `external_reference`, `payer` o `card` en `null` dan 500** y
   Mercado Pago reintenta sin fin; el informe dice 400.
6. **Baja: el usuario `org` nunca puede pagar** (400).
7. **Baja, por lectura:** el texto del panel de rechazados sólo nombra
   monto y moneda; ahora también rechaza por fecha.
8. **Baja, por lectura:** la regeneración de D4 (b) se extiende a la
   exportación. Es el diseño decidido.

Mutantes vivos (6 de 16): el margen del corte de A no está fijado; **sin
la fila `InicioRegistroPagosMP` el corte se abre** (cambiar el 503 por
seguir de largo da verde; el informe afirma el 503 sin prueba); rechazar
el sobrepago; `past_due` como vigente; el prefijo `org:` del registro; el
orden y tope del panel.

Lo que aguanta, según los dos: la carrera D en Postgres
(`cobro_mp1d_postgres.py`, «fallas: 0»), los formatos de fecha en 3.12,
reenvíos y pagos viejos, montos y moneda, cancelar desde `past_due` sin
ganar acceso, la suscripción de otra cuenta, el panel sin XSS y con
`require_admin`, la demo cerrada fuera de desarrollo.

## No corrido por la PM

La suite completa, `/code-review` y `/security-review` sobre `784e793`
(la Dev los corrió en su vuelta), la pantalla con un navegador fuera del
script de sabotajes, y nada contra Mercado Pago real.

## Veredicto

Devolución sobre `784e793`. Lo que se promete (cada pago se aplica una
vez, entero y a la vista) no aguanta dos pagos distintos a la vez, ni un
error de Mercado Pago al consultar el pago, ni volver al checkout antes del
aviso. El detalle, por causa, está en `PARA-DEV.md`.
