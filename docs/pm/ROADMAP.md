# Roadmap — aprobado por Emi (orden del 2026-10-07)

Reemplaza las versiones anteriores, que siguen en Git. Las semanas se cuentan
desde el 2026-10-07 (semana 1). El precio no se escribe acá.

**Objetivo:** cobrarles a los estudios con un producto que arme bien el
MARIA.TXT, no filtre datos y no cobre mal.

**Orden de Emi (2026-10-07):** primero el camino del TXT (subir un PDF o un
Excel, que lea todo solo y salga el MARIA.TXT); después el cobro; la
seguridad, al final y exhaustiva, «así ya está todo terminado».

**Puerta que no se saltea:** ningún estudio entra antes de cerrar la Fase 3.
Producción ya tiene facturas reales de Emi: la publicación de ensayo de la
semana 1 sigue en pie porque cierra la fuga de MARIA.TXT.

## En una mirada

| Semana | Qué pasa |
|---|---|
| 1 | Publicación de ensayo (cierra la fuga de hoy). Arranca la Fase 1 |
| 1 a 3 | **Fase 1 — el camino del TXT**, con las dos Devs |
| fin de la 3 | Publicación del TXT. Emi prueba con facturas reales. Se le manda un archivo al despachante para su Kit |
| 4 y 5 | **Fase 2 — cobro** |
| 6 y 7 | **Fase 3 — seguridad y datos, exhaustiva**, con una auditoría completa nueva al final |
| 8 y 9 | **Fase 4 — piloto** con 3 a 5 estudios |
| 10 en adelante | Oleadas |

Son las fechas más tempranas. Si algo se demora, se corre lo que sigue; no se
saltea la Fase 3.

## Lo que hace Emi

**Mañana (semana 1), para la publicación de ensayo,** en Railway, con la
lista de `NOW.md` («Para Emi»). Lo primero: ver si existen los usuarios de
prueba `demo`, `premium` o `basico`.

**Esta semana:** rotar las claves de Gemini. Recordarle al despachante los
archivos reales (favor 1).

**Al final de la Fase 1:** subir dos o tres facturas reales en el sitio
publicado y decir si el TXT salió bien. La lectura con Gemini real no se
puede probar desde la nube: esta es la prueba de verdad.

**Antes del final de la Fase 2:** crear los planes en Mercado Pago y hacer un
cobro chico con su tarjeta.

**Antes del piloto:** el texto de términos y privacidad (con su abogado o
contador); confirmar que el correo del sitio esté configurado; quién atiende
el soporte; qué estudios entran; precio y fecha del primer cobro.

## Fase 1 — El camino del TXT (semanas 1 a 3)

Subir un PDF o un Excel → lectura automática → controles → MARIA.TXT
correcto. **Regla del archivo** (límite que no se negocia): lo que cambia el
TXT necesita prueba (la ley, un archivo real o la respuesta del despachante).

### Dev 2 — el archivo y la lectura de la factura

| Orden | Pieza | Qué arregla, en llano | Hallazgos | Tamaño | ¿Cambia el TXT? | Prueba |
|---|---|---|---|---|---|---|
| ✅ | MARIA-2 | Sin clave de Gemini no se inventan productos | M4 | chico | no | aceptada el 2026-10-07 |
| 1 | MARIA-1a | País de origen bien leído (hoy China sale como Suiza; dos copias del lector), cantidades y precios con coma, nada inventado si falta un dato | M5 | medio | sí, donde hoy está mal | tabla oficial de países (VUCE) y norma ISO 3166-1 |
| 2 | MARIA-2b | Con Gemini caído o la clave inválida, el mismo error claro y la carga manual | — | chico | no | — |
| 3 | MARIA-4 | Estado de la mercadería: se elige entre seis, por producto (por defecto, nuevo sin uso importado si el origen es extranjero). IVA adicional: completo en reventa; deja de declararse siempre «uso particular» | M2, M3 | medio | sí | respuestas 1 y 2 del despachante y el archivo real de 2026 |
| 4 | MARIA-3 | Los avisos, **antes** de generar y completos. Los gastos anteriores al FOB llegan al TXT en EXW, FCA y FAS (FAS se suma a las condiciones válidas). La procedencia se carga en pantalla | M6, M8 | grande | sí | respuesta 6, Código Aduanero art. 15, la nota del SIM y el archivo real de 2025 |
| 5 | MARIA-4b | El banco se elige en cada operación (propone el último de ese cliente) y sale en el TXT. La empresa de digitalización pasa a la configuración del estudio, con cambio por operación | — | medio | sí (el banco) | respuestas 4 y 5 y el archivo real de 2026 |
| 6 | MARIA-5 | Peso total por producto (hoy sale el de una unidad). Cuentas exactas (hoy a veces no cierran por un centavo) | M1, M9 | medio | sí | el peso: respuesta 3 y el archivo real de 2026. Las cuentas: se publican con la prueba en el Kit |
| 7 | MARIA-6 | El código de cada empresa de digitalización; cómo va una reducción o exclusión del IVA adicional | — | chico | sí | las dos preguntas cortas (enviadas el 2026-10-07) |
| 8 | MARIA-7 | Identificadores, sufijos de valor por producto y código de proveedor como en los archivos reales | M7, M11 | medio | sí | los archivos reales del despachante (favor 1) |

MARIA-4, MARIA-3, MARIA-4b y MARIA-5 tocan el mismo generador: van en ese
orden. MARIA-6 y MARIA-7 arrancan cuando llegue lo que esperan; si no llegó,
la Dev 2 sigue con la Fase 2.

### Dev 1 — que la lectura no se trabe y el Excel

| Orden | Pieza | Qué arregla, en llano | Hallazgos | Tamaño |
|---|---|---|---|---|
| ✅ | ADMIN-1 | Lo de administración, sólo para el admin | S2 | chico (aceptada el 2026-10-07) |
| 1 | ADMIN-2 | Lo que encontró en ADMIN-1: borrar la función que activaba una suscripción sin pagar; la configuración del sistema, sólo para el admin; dos puntos ciegos de la prueba. Está a mitad: se termina | — | chico |
| 2 | RENDIMIENTO-1 | Leer un PDF no frena el sitio para todos, y tiene un tiempo máximo | D3 | chico |
| 3 | DEPENDENCIAS-1 | Cambiar el lector de PDF viejo, que se cuelga con un PDF armado, por su sucesor; actualizar las librerías con avisos | X3 | medio |
| 4 | EXCEL-1 | Revisar la carga por Excel de punta a punta (nunca se auditó) y arreglar lo que falle, con la misma regla de «nada inventado» | — | medio |
| 5 | MARIA-1b | Controles antes de generar: NCM que exista en el catálogo, moneda, incoterm, CUIT y montos; ningún texto puede meter líneas en el TXT | M10 | medio |
| 6 | PUNTA-A-PUNTA-1 | Una prueba automática que sube un PDF y un Excel (con un Gemini simulado) y compara el TXT con los archivos reales | — | medio |

MARIA-1b toca los controles (`validate_items_for_maria`, `MariaRequest`); la
Dev 2 trabaja en el cuerpo del generador. Zonas distintas del mismo archivo:
la PM integra una después de la otra.

### Cierre de la Fase 1

- **PUBLICAR-TXT**, con el «dale» de Emi para el SHA.
- **Emi sube dos o tres facturas reales** en el sitio publicado y dice si el
  TXT salió bien.
- **PRUEBA-KIT:** el despachante carga en su Kit un archivo de CDI, sin
  oficializar. **Cierra G4.** Con eso se publican las cuentas exactas de
  MARIA-5.

## Fase 2 — Cobro (semanas 4 y 5)

| Pieza | Quién | Qué arregla | Hallazgos | Tamaño |
|---|---|---|---|---|
| COBRO-CORTE-1 | Dev 1 | Quien no paga no genera valor ni gasta Gemini. Se cuenta una vez por operación. Sin pasarse del tope con pedidos al mismo tiempo | C1, C5, C6 | medio |
| COBRO-MP-1 | Dev 1 | El aviso de pago de Mercado Pago, verificado; cada pago se aplica una vez; se controla el monto | C3 | medio |
| COBRO-MP-2 | Dev 1 | Cancelar también cancela en Mercado Pago, con servicio hasta el fin del período pagado; una sola suscripción; no se pierden días pagados; reactivar exige pagar | C2, C4, C8 | grande |
| ORG-1 | Dev 2 | Invitaciones que funcionan en la base de producción, tope de usuarios del plan, invitación atada al email | C7 | medio |
| LEGAL-1 | Dev 2 | Páginas de términos y privacidad con el texto de Emi, y cómo pedir el borrado de los datos | X5 | chico |

**Decidido para COBRO-CORTE-1** (las D4 a D6 de la Dev 1, 2026-10-07):
la operación se crea y se cuenta la primera vez que se genera su MARIA, con un
máximo de 10 regeneraciones con contenido distinto; en las rutas que gastan
Gemini, el corte es sólo por estado de cobro; las carreras se resuelven
bloqueando la cuenta mientras se cuenta (el índice único en la base, más
adelante y después de mirar producción).

**Cierre:** publicación con el «dale» de Emi y su cobro chico: alta, cobro,
renovación, cancelación (también en Mercado Pago) y corte. **Cierra G7.**

## Fase 3 — Seguridad y datos, exhaustiva (semanas 6 y 7)

| Pieza | Quién | Qué arregla | Hallazgos | Tamaño |
|---|---|---|---|---|
| SESION-1 | Dev 1 | Cambiar o resetear la contraseña y cerrar sesión revocan de verdad; cambiar el email pide la contraseña | S3 | medio |
| ABUSO-1 | Dev 1 | Límite de intentos con la IP real; topes en registro, recuperar usuario, eventos de pantalla y sugerencias de NCM; no revelar qué emails existen | S4, S5, S6, C9, X1 | medio |
| AISLAMIENTO-2 | Dev 1 | La prueba de aislamiento ataca todas las funciones con datos de un estudio | G3 | medio |
| LIMPIEZA-1 | Dev 1 | Las 10 pruebas excluidas a mano vuelven a la CI; se borra el camino viejo a Google Cloud; se sacan de los archivos las cadenas que pueden tener contraseñas | X2, X4, secretos | chico |
| DATOS-1 | Dev 2 | Borrar un cliente siempre funciona; el chequeo de salud dice la verdad; los errores no muestran detalles internos | D2, D5, D6 | chico |
| BACKUP-1 | Dev 2 | Copia de la base programada fuera de Railway y una restauración probada | D1 | medio |
| DISCO-1 | Dev 2 | El historial de NCM y los TXT descargados pasan a la base (hoy se borran en cada publicación) | D4 | medio |
| AUDITORIA-FINAL | PM | Auditoría completa nueva de todo el producto, con subagentes Opus alto y Sonnet alto, y una vuelta de arreglos con lo que encuentre | — | grande |

**Cierre:** publicación con el «dale» de Emi, volver atrás probado. **Cierra
G3 y G6.** Recién ahí entra el primer estudio.

## Fase 4 — Piloto y oleadas (semanas 8 en adelante)

Piloto con 3 a 5 estudios durante dos semanas, con el kit que ya existe
(`wave1_*`). Se eligen los más tolerantes, no los más grandes. **G8:** tres
estudios presentaron de verdad un MARIA generado por CDI. Después, oleadas de
10 a 15 estudios, con una semana entre una y otra.

## Qué hallazgo va en qué pieza

| Hallazgos | Pieza |
|---|---|
| S1 (fuga de MARIA.TXT) | ya arreglada en la rama; llega a producción con la publicación de ensayo |
| S2 | ADMIN-1 ✅ |
| M4 | MARIA-2 ✅ |
| M5 | MARIA-1a |
| M10 | MARIA-1b |
| M2, M3 | MARIA-4 |
| M6, M8 | MARIA-3 |
| M1, M9 | MARIA-5 |
| M7, M11 | MARIA-7 |
| D3 | RENDIMIENTO-1 |
| X3 | DEPENDENCIAS-1 |
| C1, C5, C6 | COBRO-CORTE-1 |
| C3 | COBRO-MP-1 |
| C2, C4, C8 | COBRO-MP-2 |
| C7 | ORG-1 |
| X5 | LEGAL-1 |
| S3 | SESION-1 |
| S4, S5, S6, C9, X1 | ABUSO-1 |
| X2, X4, cadenas con contraseña | LIMPIEZA-1 |
| D2, D5, D6 | DATOS-1 |
| D1 | BACKUP-1 |
| D4 | DISCO-1 |
| C10 | antes de cada publicación: Emi mira qué cuentas pasan a impagas |
| X6 (correo) | Emi, en Railway |
| Clave de Gemini | Emi la rota (G0). Sacarla del archivo no alcanza: sigue en la historia, que no se reescribe |

**Se miró y está bien** (no hace falta pieza): orígenes permitidos, cookies y
CSRF, cabeceras de seguridad y topes de subida de archivos.

## Fuera de este plan

- Ordenar `HANDOFF.md`, que está desactualizado.
- Partir `main.py` (8.400 líneas). No es urgente y toca todo.
- VUCE-4, el listado de cobro para el admin.
- AFIP/WSAA y VUCE reales: siguen simulados por decisión.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| La seguridad va al final y producción ya tiene facturas reales | La publicación de ensayo cierra la fuga; Emi revisa los usuarios de prueba y las variables de Railway; ningún estudio entra antes de cerrar la Fase 3 |
| La lectura con Gemini real no se puede probar desde la nube | Emi prueba con facturas reales al cerrar la Fase 1 |
| El despachante tarda con los archivos o la prueba en su Kit | MARIA-6 y MARIA-7 esperan; la Dev 2 sigue con la Fase 2 |
| La normativa no se puede leer desde la nube | Cada cambio del TXT, con su prueba y la confirmación del despachante |
| Dos Devs se pisan en `main.py` y en el generador | Orden fijado arriba; la PM integra una pieza a la vez |
| Mercado Pago se comporta distinto en producción | Cobro chico con la tarjeta de Emi antes del piloto |
| El plan de uso compartido no alcanza | Medir con `medir.py`; compactar desde el 30 % (Devs) y el 40 % (PMs) |
