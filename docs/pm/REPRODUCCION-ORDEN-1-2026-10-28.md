# Reproducción de ORDEN-1 (2026-10-28)

Entrega de la Dev técnica en `0d89c20` (informe `cdc9c57`), base `cef45ce`.

## Adversario (Sonnet alto, contexto nuevo)

El reordenado (ítems, grupos, subítems, selección, 30 y 800 ítems, TXT sin
números saltados ni repetidos) aguantó todo. Las fallas están en el
borrador por pestaña (`static/v2/app_v2.js`, `recuperarBorrador`).

## Reproducido por la PM

API local en SQLite, usuarios inventados, scripts del adversario
(`/tmp/cdi-pm/adv-o1`, fuera del repo), pieza en el puerto 8871 y base
`cef45ce` en el 8872.

1. **Otro usuario ve las operaciones a medias del anterior, todas.** El
   usuario A deja dos operaciones en dos pestañas, sale y cierra; B entra
   en la misma computadora y abre pestañas nuevas.
   - Pieza: `#1 ve: OP-A2-CLIENTE-Y`, `#2 ve: OP-A1-CLIENTE-X`, `#3 ve: null`,
     las dos con «Se recuperó la operación en curso».
   - Base: `#1 ve: OP-A2-CLIENTE-Y`, `#2 ve: null`. Ver una ya pasaba; la
     pieza la convierte en una cola con todas.
2. **Los borradores abandonados no vencen y vuelven de a uno.** Tres
   pestañas cerradas ZZ-1/2/3: la primera pestaña nueva trae ZZ-3; después
   de «nueva operación», las siguientes traen ZZ-2 y ZZ-1. Un borrador de
   hace 40 días también se recupera (`VIEJO-40d`).
3. **Una pestaña duplicada toma la operación de una viva.** (El duplicado
   se simuló copiando el id de pestaña de sessionStorage, como hace el
   navegador.) La duplicada recupera `DUP-A` con la original viva; editan
   las dos y quedan dos claves: `DUP-A-editada-en-D` y `DUP-A-editada-en-A`.

## Del adversario, no reproducido por la PM

- Una pestaña congelada más de 3 minutos se toma como huérfana (congelado
  real por CDP; la edad, simulada). A riesgos.
- Mutantes que las pruebas no distinguen: `BORRADOR_HUERFANO_MS = 1e15`
  (el camino de recuperar tras un cierre sin `pagehide` no tiene prueba) y
  quitar el `selectedRows.add` de `reorderItems`.
- Dos filas con el mismo renglón se funden en un ítem del TXT en el lugar
  del primero (MARIA-8, preexistente). Queda como está.
- `draggable` colgado si se suelta el agarre fuera de la tabla
  (preexistente).

## Veredicto

Devolución sobre `0d89c20`, por la causa: el borrador no sabe de quién es,
ni cuán viejo es, ni si su pestaña vive.
