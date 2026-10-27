# PM → Dev MARIA (Dev 2)

Este archivo es de la PM principal (en CDI no hay PM visual). Vos lo leés y
contestás en `PARA-PM-2.md`. La historia de este canal está en Git.

## Cómo trabajás

`AGENTS.md`, `CLAUDE.md`, `docs/pm/ONBOARDING-DEV.md` y los comandos
`/entregar` y `/respondio`. No se copian acá.

**Tu rama: `claude/dev-maria`**, creada desde la de la PM
(`claude/practical-shannon-szpwkn`). Antes de cada tarea traés la de la PM
con `merge`. Nunca `main`. Las ramas viejas `claude/dev2-maria` y
`codex/*` son historia: lo aceptado ya está en la de la PM.

Sos la Dev de la **cola MARIA**: el MARIA.TXT, el lector de facturas y sus
pantallas. La Dev técnica trabaja en `claude/dev-tecnica`; no tocás su
canal ni su rama.

Esfuerzo alto (Emi, 2026-10-24). Herramientas: todas menos el consejero;
tus subagentes hasta alto, nunca Fable.

**Timbres:** al entregar o al dejar una D que te frena, despertás a la PM
principal con `send_message` (sesión en `NOW.md`, «Quién hace qué»),
`priority` `next`, empezando con «Dev MARIA:». Ella te despierta igual.

**Regla del archivo MARIA** (límite que no se negocia): ningún cambio en lo
que sale en el TXT sin prueba (la ley, un archivo real, la respuesta del
despachante o lo que el MARIA aceptó o rechazó). **Los TXT y la proforma de
la reunión del 2026-10-24 tienen datos reales de un cliente: no entran al
repositorio.** Las pruebas usan sintéticos con la misma forma.

## Veredicto (2026-10-27): SEPARADORES-1d aceptada

Sobre `140c122` (probado en `1240c08`, sabotajes en `36f54a3`). Suite mía
sobre `140c122`: 3478 passed, 102 skipped, 2 xfailed, 0 rojos. Tus 5
sabotajes y los 10 de 1c en rojo por la razón esperada. Integré tu rama por
avance rápido: mi rama está en `140c122` más este veredicto. Detalle en
`REPRODUCCION-SEPARADORES-1d-2026-10-27.md`.

- **D24:** 19 textos míos contra la base `91be665`; la única diferencia es
  `01.234` con pista `,` (antes 1234, ahora sin leer). Lo bien formado no
  cambió.
- **D25:** `alCentavoDelTxt` contra el redondeo del generador, 20012 montos
  al azar, 0 distintos.
- **Se acepta** que `1234.567` con pista `,` quede sin leer: es el lado
  seguro.
- **Se anota, no es tarea:** el aviso no cubre gastos ni ajustes. Los
  ajustes esperan la pregunta 5 al despachante (`PREGUNTAS-DESPACHANTE.md`).

## ORG-1 — tarea activa

Invitaciones al estudio (`ROADMAP.md`, Fase 2; C7 de
`AUDITORIA-2026-10-06.md`). **Toca permisos: revisión fuerte.** Diff de
revisión desde la punta de mi rama. Trae mi rama antes de arrancar.

**Alcance:** las invitaciones funcionan sin 500, quedan atadas al email
invitado y respetan el tope de usuarios del plan. **No entra** lo demás de
la fila 7 de `REPRODUCCION-ARGON-2026-10-24.md` (miembros que no ven los
clientes del estudio, cancelar sobre el usuario, cobros del miembro raso,
el trial al sacar un miembro, vaciar el email): espera la decisión de Emi.
Si para que ORG-1 funcione hace falta algo de eso, es una D.

El código: `invite_to_organization` y `validate_invitation` en
`proyecto_maria/main.py` (~9480 y ~9540), el registro con `invite_token`
(~2898-2921), `Invitation` en `database/models.py` y el plan en
`services/billing_service.py`.

1. **Premisa primero.** Reproducí el 500 en Postgres antes de arreglar.
   Mi sospecha, sin correr: `expires_at` es `DateTime(timezone=True)` y se
   compara con `datetime.utcnow()`, sin zona; en Postgres vuelve con zona y
   la comparación revienta, en SQLite no. Hay Postgres 16 instalado en el
   contenedor (`/usr/lib/postgresql/16`). Si es otra cosa, decímelo con la
   salida.
2. **Sin 500 en las dos bases.** Validar, registrarse con invitación y una
   invitación vencida dan la respuesta de hoy en SQLite y en Postgres. Los
   registros viejos de SQLite vienen sin zona: también. Una prueba que sólo
   corre en SQLite no distingue este defecto: corré contra un Postgres
   local, o inyectá un `expires_at` con zona.
3. **Atada al email.** Al registrarse con `invite_token`, el email del
   registro (con `strip().lower()`, como lo guarda la invitación) tiene que
   ser el invitado. Si no coincide o falta: 400 y la invitación **no** se
   gasta. Una cuenta que ya existe y se suma por invitación no entra: hoy
   sólo existe el camino del registro.
4. **Tope del plan.** Sale de `billing_service.get_plan(org.plan or
   "premium")["users"]`, nunca un 3 escrito a mano. Cuentan los usuarios con
   el `organization_id` del estudio (el dueño también). Al invitar: 400 si
   miembros más invitaciones pendientes sin vencer llegan al tope. Al
   registrarse: 400 si los miembros ya llegaron, sin gastar la invitación.
   Sacar un miembro libera el lugar (ya lo hace).
5. **Un solo uso, de verdad.** Hoy el usuario y el «accepted» se guardan en
   dos commits: dos registros a la vez con el mismo token pasan los dos. La
   invitación se gasta en la misma transacción que el alta, con una
   actualización condicionada a `status = 'pending'`, y se comprueba que
   tocó una fila. Contame qué deja una carrera de dos registros a la vez; si
   en SQLite no se puede provocar, decilo.

**Pruebas:** por punto, casos de la familia y no un solo ejemplo; las
guardas (una invitación válida del email correcto con lugar entra igual que
hoy); un sabotaje por punto que vuelva a lo de hoy; corré
`scripts/testing/ataque_aislamiento.sh`. Suite completa sobre el SHA que
entregás.

**No se toca:** el alta sin invitación, el cobro y los planes, lo que ve
cada miembro.

**Tu cupo:** hasta el 28/10 a las 18:00 UTC no tenés subagentes ni
`/code-review`. Programá, armá casos y sabotajes ya; `/entregar` espera a
que vuelva el cupo. Yo sumo un adversario de permisos en mi revisión.

**Puede pausarse:** le pregunto a Emi si tres errores del TXT de la
auditoría (8.1, 9.2 y 8.2) van antes. Si dice que sí, te aviso acá y ORG-1
queda donde esté.

**Apenas entregues:** DESTINO-1, PESO-NETO-1 y PRORRATEO-1 esperan datos
del despachante; te aviso cuando lleguen.

## Qué pasó el 2026-10-24

Emi y el despachante cargaron en el MARIA un TXT de CDI de una factura real
(decenas de renglones de un mismo producto en varios colores y medidas,
una sola posición SIM, origen China, CFR). Entró después de doce correcciones a mano. Cada una es
un defecto del generador. La versión que cargó tiene esta forma (valores
inventados acá):

```
[DDT]
ISTA=IC05
IDSO=AB1234CD                ← corto: con 19 caracteres el MARIA lo rechaza
CDDTEXE=01
CDDTBUR=001
CDDTTYPDEC=IC05
CDDTAGR=20111111112          ← CUIT del despachante: sin esta línea, «No existe el campo CDDTAGR»
CDDTIMPEXP=I
...
MDDTFLE=3480.00              ← CDI escribió 3.48: tomó «3.480» como decimal
...
[DVD]
LDVDREFDOC=<número real de la factura>   ← CDI escribió un pedazo («E7L1-1»)
...
[ART]
NART=0001
CARTSBITEM=S                 ← un ítem por posición, con subítems
CARTUNTDCL=03                ← m² (CDI puso 07 = unidad)
QARTUNTDCL=<suma de m²>
CARTUNTEST=01                ← kilogramo, la unidad estadística de VUCE
QARTUNTEST=<igual a QARTKGRNET, al centésimo>   ← si no, error 2122
QARTKGRNET=<kilo neto>
...
[SBT]
NART=0001
ISBT=0001
MSBTFOB=...
QSBTUNTDCL=...
MSBTUNITAR=...
IEXT=1-1
CSBTSVL=AA(MARCA)-AI(500G AZUL001 120CMX40M)-   ← AI distinto por renglón; sólo letras, números y espacios
QSBTUNTEST=<kilos del renglón>
```

Todas las líneas terminan en CRLF (una línea sin CR: «falta carácter de fin
(crlf) en línea 15»). El MARIA no acepta guiones, puntos ni caracteres raros
dentro de los valores de los sufijos: van espacios. El guión que separa un
sufijo del otro (`)-`) sí.

## Respuestas a tus D

MARIA-7, 2026-10-24:

- **D1: (a).** Le pregunto al despachante el largo máximo y si el MARIA
  rechaza un IDSO repetido (los choques de la tabla de la reproducción). No
  cambies `NDDTIMMTRN` ni `IEXT` sin esa respuesta.
- **D2: (b)**, devolución punto 2.
- **D3: (a).** El archivo aceptado trae «S.A.», comas y paréntesis.
- **D4: (a).** El «mandala igual» es propuesta, si aparece un proveedor que
  lo necesite. Las palabras de cuenta, devolución punto 3.
- **D5: (a).** La (c), validar la fecha en el alta, la paso a la cola de la
  Dev técnica.
- **D6: (b)**, devolución punto 5.
- **D7: (a)** mientras pregunto al despachante cómo va un decimal en un
  sufijo y si acepta un valor vacío.
- **D8: (a).** La v1 no es la pantalla en uso; queda con el aviso.

SEPARADORES-1 y 1b, 2026-10-25: **D19 (b)**, **D20 (a)**, **D21 (b)**
(SEPARADORES-1c). SUFIJOS-1: **D22 (a)**, **D23 (c)**. Todas decididas por
la PM (`DECISIONS.md`).

SEPARADORES-1c, 2026-10-27: **D24 (a)**, **D25 (b)** (SEPARADORES-1d).
Decididas por la PM. Aceptada en `140c122`. La próxima D es la D26.
