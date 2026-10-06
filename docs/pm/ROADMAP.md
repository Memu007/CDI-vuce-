# Roadmap — PROPUESTA, sin aprobar (2026-10-06)

Hasta que Emi lo apruebe, nada de esto se le asigna a una Dev. Sale de
`AUDITORIA-2026-10-06.md`. Las fechas son propuestas: Emi dijo que se rehacen.
El precio no se escribe acá.

**Objetivo:** cobrarle a los estudios con un producto que no filtre datos, no
declare mal ante la aduana y no cobre mal.

**Cómo se mide:** por puertas (G0 a G8, en `NOW.md`), no por porcentaje. Una
puerta se cierra con la salida del comando pegada.

## Dos ritmos posibles

| | Con una Dev | Con dos Devs (recomendado) |
|---|---|---|
| Primera publicación (seguridad) | ~16 de octubre | ~16 de octubre |
| Archivo MARIA confiable | ~28 de octubre | ~23 de octubre |
| Cobro real de punta a punta | ~6 de noviembre | ~30 de octubre |
| Piloto con 3 a 5 estudios | 9 al 20 de noviembre | 2 al 13 de noviembre |
| Primeras oleadas | desde el ~23 de noviembre | desde el ~16 de noviembre |

**Por qué dos:** hay dos colas que casi no se pisan. Una es técnica (cobro,
sesión, permisos), para la Dev 1. La otra es el archivo MARIA y sus pantallas
(`maria_generator.py`, el extractor, `static/v2`), para la Dev 2. Una sesión
más gasta más del plan de uso compartido. **Decide Emi.**

## Antes de empezar (Emi, esta semana)

1. Rotar las claves de Gemini (G0).
2. Mandar las preguntas al despachante (`PREGUNTAS-DESPACHANTE.md`).
3. En Railway: confirmar `DATABASE_URL` y `ENVIRONMENT=production`, ver si el
   Postgres tiene backup y apagar su red pública.
4. Aprobar este plan, decidir si hay Dev 2 y revisar las fechas.

## Bloque 1 — Seguro para publicar (Dev 1, del 7 al 16 de octubre)

Primero lo que deja entrar a quien no debe. Cada pieza se puede revisar sola.

| Pieza | Qué arregla | Hallazgos |
|---|---|---|
| ADMIN-1 | `/api/admin/*` y las funciones globales, sólo para admin | S2 |
| SESION-1 | Cambiar o resetear la contraseña y cerrar sesión revocan de verdad; cambiar el email pide la contraseña | S3 |
| COBRO-CORTE-1 | El corte por impago cubre todo lo que genera valor o gasta Gemini; generar el MARIA cuenta como operación | C1, C5 |
| ORG-1 | Invitaciones que funcionan en Postgres, límite de usuarios del plan, invitación atada al email | C7 |
| DATOS-1 | Borrar un cliente con presupuesto; `/health` honesto; sin detalles de error al público | D5, D2, D6 |
| ABUSO-1 | IP real detrás del proxy, límites en registro, recuperar usuario y `/api/ui/event` | S4, S5, S6, C9 |
| PUBLICAR-1 | Contar los `active` vencidos, backup, publicar con el «dale» de Emi y probar volver atrás | S1, C10, G6 |

**Puerta:** la PM reproduce cada arreglo. Al final, el ataque de aislamiento
contra la imagen que se publica y la suite completa. **Publicar arregla la
fuga de MARIA.TXT que hoy está en producción** (S1). Con la publicación llegan
a `main` las reglas nuevas.

## Bloque 2 — Archivo MARIA confiable (Dev 2 en paralelo, o Dev 1 después)

| Pieza | Qué arregla | ¿Espera al despachante? |
|---|---|---|
| MARIA-1 | Peso total por ítem; origen sin cortar a 2 letras; cantidades con coma; nada inventado si falta un dato; validar NCM contra el catálogo, moneda, incoterm, CUIT y montos; sin inyección de líneas | sólo confirmar el peso |
| MARIA-2 | Sin clave de Gemini no se inventan ítems: error claro | no |
| MARIA-3 | Avisos **antes** de generar y completos; gastos FOB de la pantalla al TXT; procedencia en pantalla (Código Aduanero, art. 15) | no |
| MARIA-4 | `CARTUSO`, `IVAADICIONAL1`, banco, código de proveedor, identificadores, `PSAD`, sufijos SBT y redondeo, según las respuestas | **sí** |
| MARIA-5 | Prueba en el Kit María del despachante (sólo leer, sin oficializar) | sí |

**Puerta G4:** el despachante lee en su Kit un TXT de CDI sin corregirlo a mano.

## Bloque 3 — Cobro real (Dev 1)

| Pieza | Qué arregla | Hallazgos |
|---|---|---|
| COBRO-MP-1 | Aviso de pago con firma o verificado contra la suscripción; cada pago se procesa una sola vez; se controla el monto | C3, C6 |
| COBRO-MP-2 | Cancelar también en Mercado Pago, servicio hasta el fin del período pagado; una sola suscripción; los días pagados no se pierden; reactivar exige pagar | C2, C4, C8 |
| BACKUP-1 | Copia de la base programada fuera de Railway y una restauración probada | D1 |
| DISCO-1 | El historial de NCM de cada estudio pasa a la base | D4 |
| PUBLICAR-2 | Con el «dale» de Emi | — |

**Puerta G7:** Emi crea los planes en Mercado Pago y hace un cobro real chico
con su propia tarjeta. Se ve el ciclo entero: alta, cobro, renovación,
cancelación (también en Mercado Pago) y corte.

## Bloque 4 — Piloto (3 a 5 estudios, dos semanas)

Con el kit que ya existe (`wave1_*`) y la telemetría. Se eligen los estudios
más tolerantes, no los más grandes. Antes, Emi decide quién atiende el soporte.
**Puerta G8:** tres estudios presentaron de verdad un MARIA generado por CDI.

## Bloque 5 — Oleadas

De a 10 o 15 estudios, con una semana de margen entre oleadas. Precio y fecha
del primer cobro: los decide Emi y no se escriben acá.

## Fuera de este plan (propuesto para después)

- Ordenar `HANDOFF.md`, que está desactualizado.
- Partir `main.py` (8.4k líneas). No es urgente y toca todo.
- VUCE-4, el listado de cobro para el admin: va después de ADMIN-1.
- AFIP/WSAA y VUCE reales: siguen simulados por decisión.

## Riesgos del plan

| Riesgo | Mitigación |
|---|---|
| Las respuestas del despachante tardan | MARIA-1 a MARIA-3 no lo esperan |
| La normativa no se puede leer desde la nube | Cada cambio del TXT, con la fuente y la confirmación del despachante |
| Mercado Pago se comporta distinto en producción que en pruebas | Cobro real chico a una cuenta propia antes del piloto |
| El plan de uso compartido no alcanza con dos Devs | Medir con `medir.py` la primera semana; si no rinde, se cierra la Dev 2 |
