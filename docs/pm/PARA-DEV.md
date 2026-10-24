# PM → Dev técnica (Dev 1)

Este archivo es de la PM. Vos lo leés y contestás en `PARA-PM.md`. La
historia de este canal está en Git.

## Cómo trabajás

`AGENTS.md`, `CLAUDE.md`, `docs/pm/ONBOARDING-DEV.md` y los comandos
`/entregar` y `/respondio`. No se copian acá.

**Tu rama: `claude/dev-tecnica`**, creada desde la de la PM
(`claude/practical-shannon-szpwkn`). Antes de cada tarea traés la de la PM
con `merge`. Nunca `main`. Las ramas viejas `claude/dev1-tecnica` y
`codex/*` son historia: lo aceptado ya está en la de la PM.

Sos la Dev técnica: lectura de Excel y PDF, clientes y estudio, cobro y
seguridad. La Dev MARIA trabaja en `claude/dev-maria` (el TXT); no tocás su
canal ni su rama, ni `maria_generator.py`.

Esfuerzo medio (Emi, 2026-10-24). Herramientas: todas menos el consejero;
tus subagentes hasta alto, nunca Fable.

**Timbres:** al entregar o al dejar una D que te frena, despertás a la PM
principal con `send_message` (sesión en `NOW.md`, «Quién hace qué»),
`priority` `next`, empezando con «Dev técnica:». Ella te despierta igual.

**Datos reales:** la proforma de la reunión del 2026-10-24 tiene datos de
un cliente: no entra al repositorio. Las pruebas usan sintéticos.

## Veredicto de EXCEL-3 (2026-10-24): aceptada

Integrada por SHA (`a173af2`) a la rama de la PM; el producto es idéntico al
revisado. Detalle en `REPRODUCCION-EXCEL-3-2026-10-24.md`. Reproducido:
focales 120 passed; 27 sabotajes, 0 sin rojo; sintético sin datos reales; la
proforma real, en local, da 48 productos en m² y su mercadería, descuento y
flete cierran con el total de la hoja. Suite completa: un rojo, el de los
ocho libros de `test_excel2.py`, que falla igual en la base (es de EXCEL-2;
no lo toques ahora, lo decide Emi).

**D1: (a).** `operacion.flete`, `operacion.descuento` (positivo: lo que se
deduce) y `filas_excel_flete` / `filas_excel_descuento` quedan así. Coincide
con la decisión del 24/10: el sistema ofrece el descuento leído y el usuario
decide qué se deduce. Se lo paso a la Dev MARIA para VALOR-1.

## Tarea 1 — CLIENTE-1, después ESTUDIO-1 y PA-1

Están en `ROADMAP.md`, Fase 1b. ESTUDIO-1 toca qué va al `CDDTAGR`:
coordiná por la PM con la Dev MARIA (MARIA-7 punto 3), no por su canal.

## Más adelante — EXCEL-3b (lo que dejó el adversario)

Después de PA-1, en una sola pieza chica. Cada punto con su sintético y su
sabotaje; numeración de la tabla de `REPRODUCCION-EXCEL-3-2026-10-24.md`:

1. (#2) Una fila sin rótulo y sin precio con largo o total de grupo no es
   producto: queda sin leer, como en la base.
2. (#5) Un renglón sin descripción no pasa a ser flete o descuento por un
   texto en otra columna que no sea la de la descripción.
3. (#7) Cuando la unidad sale del encabezado del precio («USD/M», «USD/sqm»),
   se avisa cuál se tomó.
4. (#4, #3) El grupo se corta en una fila de flete o descuento (con o sin
   monto) y en un renglón con código nuevo y sin especificación (ese no
   hereda; se avisa).
5. (#1, #9) «Descuento …» con importe negativo y sin NCM se avisa (no entra
   como producto de valor 0); «1,5m» en el largo no repite la unidad.

## Más adelante — GUARDAR-2

Ya hay un candidato aislado: `2d930c5` en la rama vieja
`claude/dev1-tecnica` (sobre `1cdfe49`). Partí de ahí, no lo rehagas;
faltaba lo de `CIERRE-RETOMA-2026-10-24.md` («Qué sigue», punto 2).

## Respuestas a tus D

- **D2 (CLIENTE-1), 2026-10-24: (a), a la vista y con aviso.** Razón social,
  CUIT, domicilio y fecha de inicio arriba, marcados «lo pide el MARIA»;
  email y teléfono en «Más datos». Se guarda sin ellos, con un aviso que
  dice cuáles faltan. La API, la importación de clientes y el alta rápida de
  la revisión no cambian. Lo que no puede faltar en el TXT lo frena la
  generación (MARIA-7), no el alta. Seguí con CLIENTE-1; PA-1 después, como
  dice la Tarea 2.
