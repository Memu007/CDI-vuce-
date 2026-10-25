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

## Veredicto de EXCEL-3c y CLIENTE-1b (2026-10-25)

Sobre `273c153` (informe `69347ff`). Detalle y salidas en
`REPRODUCCION-EXCEL-3c-2026-10-25.md`. Mi adversario fue Opus, alto. Yo
re-corrí mis casos en la entrega y en la base `e08b4c4`.

- **EXCEL-3c: devolución, EXCEL-3d.** R1, B1 y R2 mejoraron. Pero la vuelta
  trae una regresión de plata sin aviso.
- **CLIENTE-1b: aceptada con nota.** Todavía no la integro. La rama no se
  separa limpia: `23936d5` ya trae `test_excel3.py` y `excel3.sh`. Entra
  junto con EXCEL-3d.

### EXCEL-3d: lo que vuelve (va primero)

1. **Causa:** cuando hay celdas combinadas o copiadas, la fila se decide con
   una lista de palabras (`_es_solo_un_cargo`, `main.py:4600-4637`). Una fila
   cuyo rótulo empieza como un cargo y trae una palabra que la lista no
   conoce entra como producto, en silencio.
   - Con el origen combinado (`C2:C4`), «Flete int.», «Gastos
     administrativos» e «Insurance 40 GBP» suben el FOB de 3550 a 4750 con
     avisos `[]`.
   - La base leía «Flete int.» como flete de 1200, con aviso de su fila.
   - **Lo que tiene que quedar:** ninguna fila que empiece como un cargo
     cambia el FOB sin un aviso que nombre su fila. Si queda afuera o entra
     marcada, lo decidís vos.
   - **Piso:** lo que hacía la base con «Flete int.» combinado, o mejor.
   - «Freight elevator» (un producto real) se resuelve con la misma regla.
   - **No** se arregla agregando palabras a la lista.
2. **Cabecera y su hijo, la misma decisión (regresión sin combinadas).** Una
   cabecera con código y rótulo de cargo («H-1», «Insurance», con medidas)
   queda sin leer. Su hijo sin descripción hereda «Insurance» y entra como
   producto: 40 USD al FOB.
   - El único aviso es el genérico de herencia.
   - La causa: `rotulo_propio = ""` si `del_grupo` (`main.py:4958`).
   - En la base quedaban los dos sin leer.
3. **D12 (a) en toda la familia.** El aviso de «sin precio» está sólo en el
   grupo con medidas (`main.py:4921`). Con la descripción combinada
   (`B2:B4`), sin medidas y el precio sólo arriba, dos hijos entran sin
   precio y con avisos `[]`.
   - Tiene que avisar, con su fila, con la descripción combinada, con el
     origen combinado y sin combinadas.
   - Sigue sin inventar precio.

**La prueba barre la familia, no mis ejemplos:**
- varios rótulos de cargo (flete, seguro, gastos, handling, pago, comisión),
  cada uno con palabras de más arbitrarias;
- el rótulo en la columna del código y en la de la descripción;
- origen combinado, descripción combinada, los dos juntos y sin combinadas;
- cabecera con hijos, en vertical y en horizontal;
- al menos un producto real que empiece como un cargo.

Cada punto con su sabotaje en rojo. Las recetas están en la reproducción.
Corregí el CHANGELOG para que diga sólo lo que queda probado.

**Siguen como en EXCEL-3c:**
- D12 (b) es aparte, después de ESTUDIO-1;
- R3 se queda como está;
- los riesgos que no se arreglan: «Ocean freight», el subtotal con largo,
  «10m2 m» y el aviso de unidad.

**Riesgos que anoto, no los arregles:**
- la herencia de R2 cambia tres proformas del fuzz, todas con aviso;
- «Ins.», «Commission» y parecidos entran al FOB también en la base.

### Notas de CLIENTE-1b (van a CLIENTE-1c)

- El día con una cifra pasa.
- Los años 0001 y 9999 pasan.
- Con un `--base` mal escrito, el script muestra la clave en el error de
  Python. Esto sí arreglalo: que el error no la muestre.
- Un dígito de ancho completo se lee distinto en la pantalla y en el
  generador.

### Tus D (decidido por la PM)

- **D15: (b).**
- **D16: (b).** Va junto con D15 en una pieza chica, **CLIENTE-1c**, con las
  dos últimas notas de arriba. (c) no: toca el modelo y cambia el error de
  tres lugares a la vez.
- **D17: (a).** Arreglá `ataque_aislamiento.sh` vos, en un commit aparte de
  EXCEL-3d. La puerta está ciega también en mi rama.
- **D8: (b)**, como ya estaba. D12 como arriba.

### Orden

1. EXCEL-3d (con D17 en commit aparte).
2. ESTUDIO-1 (abajo).
3. CLIENTE-1c.
4. GUARDAR-2.

## Después de EXCEL-3d

### ESTUDIO-1, con lo que pediste definido (decidido por la PM)

1. **Los estudios son de la cuenta**, como los clientes: cada usuario ve y
   elige sólo los suyos (mismo aislamiento por dueño que clientes; prueba
   de que otro usuario no los ve ni los usa).
2. **Se elige en la operación donde hoy se carga el CUIT del despachante**
   (`cuit_agr`), con el último usado o el único como opción preseleccionada.
3. **Sin migración de datos:** `users.cuit` sigue como respaldo cuando la
   operación no trae estudio. Nada se copia ni se borra.

Costura con MARIA-7 punto 3: el error cuando falta el CUIT ya está
integrado en mi rama (`1fa0b6e`). Traés mi rama y cambiás sólo de dónde
sale el CUIT y el texto de «dónde cargarlo».

## Después — CLIENTE-1c

D15 y D16 (b), con las dos últimas notas de CLIENTE-1b. Toca datos:
revisión fuerte. Cada lugar con su sabotaje en rojo.

## Más adelante — GUARDAR-2

Ya hay un candidato aislado: `2d930c5` en la rama vieja
`claude/dev1-tecnica` (sobre `1cdfe49`). Partí de ahí, no lo rehagas;
faltaba lo de `CIERRE-RETOMA-2026-10-24.md` («Qué sigue», punto 2).
