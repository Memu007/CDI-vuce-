# Roadmap — PROPUESTA, sin aprobar (2026-10-07)

Hasta que Emi lo apruebe, nada de esto se le asigna a una Dev. Sale de
`AUDITORIA-2026-10-06.md` (con su agregado del 2026-10-07) y de un auditor que
midió el tamaño de cada pieza y qué piezas tocan el mismo código. Reemplaza la
propuesta del 2026-10-06. Las fechas van en semanas desde que Emi apruebe,
porque Emi dijo que se rehacen. El precio no se escribe acá.

**Objetivo:** cobrarles a los estudios con un producto que no filtre datos, no
declare mal ante la aduana y no cobre mal.

**Cómo se mide:** por puertas (G0 a G8, en `NOW.md`), no por porcentaje. Una
puerta se cierra con la salida del comando pegada.

## En una mirada

**Casi todo se puede hacer sin esperar al despachante.** Se parte en dos fases:

- **Fase A, ya:** seguridad, cobro, datos y casi todo el archivo MARIA. Lo que
  cambia el archivo MARIA se hace en esta fase, pero **se publica sólo cuando
  hay prueba**: la ley, un archivo real o la respuesta del despachante.
- **Fase B, con sus respuestas:** se ajustan cinco datos y los
  identificadores, se prueba un archivo en su Kit María y arranca el piloto.

| Semana desde la aprobación | Con dos Devs (recomendado) | Con una Dev |
|---|---|---|
| 1 | Publicación de ensayo (cierra la fuga de hoy). Arrancan la cola técnica y la del MARIA | Publicación de ensayo. Arranca la cola técnica |
| 3 | Primera publicación de seguridad | Primera publicación de seguridad |
| 4 | MARIA listo, salvo lo que espera al despachante | Sigue el MARIA |
| 5 | Cobro real publicado | MARIA listo |
| 6 | Fase B y prueba en el Kit, si el despachante ya respondió | Cobro real (semanas 6 y 7) |
| 7 y 8 | Piloto con 3 a 5 estudios | Fase B |
| 9 en adelante | Oleadas | Piloto (semanas 9 y 10) |

Son las fechas más tempranas: si el despachante tarda, se corren la Fase B y el
piloto, no el resto.

**Por qué dos Devs:** hay dos colas que casi no se pisan (medido archivo por
archivo, más abajo). Una sesión más gasta más del plan de uso compartido.
**Decide Emi.**

## Lo que decide o hace Emi

**Esta semana:**

1. **Rotar las claves de Gemini** (G0). Es lo más urgente.
2. **Mandar las preguntas al despachante** (`PREGUNTAS-DESPACHANTE.md`).
3. **En Railway** (donde está publicado el sitio):
   - confirmar que estén `DATABASE_URL` y `ENVIRONMENT=production`;
   - ver si la base tiene copia de seguridad;
   - apagar la red pública de la base (la app usa la interna);
   - **prender «Wait for CI»**: así Railway publica sólo si las pruebas
     automáticas pasan. Hoy publica aunque fallen.
4. **Decir si CDI usa Google Cloud.** En el repositorio hay un segundo camino
   de publicación hacia Google Cloud. Si no lo usás, se borra (LIMPIEZA-1).
5. **Decir si alguna vez subió datos reales** al sitio publicado. Define si la
   fuga de hoy afectó a alguien.
6. **Aprobar este plan**, decir si hay Dev 2 y si va la publicación de ensayo.

**Más adelante** (antes del piloto):

- crear los planes en Mercado Pago y hacer un cobro chico con su tarjeta;
- conseguir, con su abogado o contador, el texto de los términos y de la
  política de privacidad (LEGAL-1 los pone en el sitio);
- confirmar en Railway que el correo esté configurado: sin eso, recuperar la
  contraseña falla en silencio;
- decidir quién atiende el soporte y elegir los estudios del piloto;
- precio y fecha del primer cobro (no se escriben acá).

## Fase A — sin esperar al despachante

### Publicación de ensayo (semana 1, opcional, recomendada)

Publicar **ya** la rama de trabajo tal como está (`e8344d0`, 25 cambios
revisados, pruebas en verde) más las reglas nuevas, que son sólo documentos
encima de ella. El «dale» de Emi va para ese SHA exacto, que la PM le pasa con
los chequeos hechos.

- **Gana:** cierra la fuga de MARIA.TXT que hoy está en producción, lleva las
  reglas nuevas a `main` y ensaya publicar y volver atrás cuando nadie más usa
  el sitio.
- **Cuesta:** una hora de Emi: los chequeos de Railway, mirar en la pestaña
  de datos de la base qué cuentas hay, y el «dale». Al arrancar, toda cuenta
  activa con el período vencido hace más de 7 días pasa a impaga, y no vuelve
  sola si se vuelve atrás. La PM no ve la base de producción: eso lo confirma
  Emi.
- **Volver atrás:** en Railway, «Redeploy» de la publicación anterior (se hace
  desde el teléfono). Si hiciera falta tocar `main`, un commit que deshace el
  cambio, con su propio «dale». El esquema de la base es el mismo en las dos
  versiones (probado en local).
- **Sí cambia el archivo MARIA** en cuatro puntos que ya están en la rama con
  sus pruebas: varios modelos bajo una misma NCM (sacado de un archivo real),
  el año de un identificador que estaba escrito a mano, los gastos hasta el
  FOB según la condición de venta y la lista de supuestos.
- **No arregla** el resto de los agujeros: eso es la cola técnica.
- **Importa más de lo que parecía:** Emi cargó facturas reales en el sitio
  (2026-10-07). Antes, Emi mira en Railway si hay cuentas que no sean suyas:
  la fuga pedía sesión iniciada.
- **Se borra** lo que vive en el disco del servidor: los TXT generados y el
  historial de NCM. Pasa en cada publicación (DISCO-1 lo arregla); las
  operaciones en la base quedan.

### Cola técnica (Dev 1)

Primero lo que deja entrar a quien no debe. Cada pieza se revisa sola; la PM
reproduce cada hallazgo antes de aceptarla.

| Orden | Pieza | Qué arregla, en llano | Hallazgos | Tamaño |
|---|---|---|---|---|
| 1 | ADMIN-1 | Las pantallas de administración, sólo para Emi. Lista cerrada de funciones globales | S2 | chico |
| 2 | COBRO-CORTE-1 | Quien no paga no genera el MARIA ni gasta Gemini. Las operaciones se cuentan una vez por operación y sin pasarse del tope con pedidos al mismo tiempo | C1, C5, C6 | medio |
| 3 | LIMPIEZA-1 | Las 10 pruebas excluidas a mano vuelven a la CI; se borra el segundo camino de publicación (Emi confirmó que no se usa); se sacan de los archivos las cadenas que pueden tener contraseñas | X2, X4, secretos | chico |
| 4 | SESION-1 | Cambiar o resetear la contraseña y cerrar sesión revocan de verdad; cambiar el email pide la contraseña | S3 | medio |
| 5 | ABUSO-1 | Límite de intentos con la IP real; topes en registro, recuperar usuario, eventos de pantalla y sugerencias de NCM; no revelar qué emails existen | S4, S5, S6, C9, X1 | medio |
| 6 | ORG-1 | Invitaciones que funcionan en la base de producción, tope de usuarios del plan, invitación atada al email | C7 | medio |
| 7 | DATOS-1 | Borrar un cliente siempre funciona (pedido de borrado de datos); el chequeo de salud dice la verdad; los errores no muestran detalles internos | D2, D5, D6 | chico |
| 8 | RENDIMIENTO-1 | Leer un PDF no frena el sitio para todos, y tiene un tiempo máximo | D3 | chico |
| 9 | DEPENDENCIAS-1 | Cambiar el lector de PDF viejo, que se cuelga con un PDF armado, por su sucesor; sacar o actualizar las librerías con avisos de seguridad | X3 | medio |
| 10 | AISLAMIENTO-2 | La prueba de aislamiento ataca **todas** las funciones con datos de un estudio, no sólo clientes y descargas | G3 | medio |
| 11 | PUBLICAR-1 | Emi confirma antes qué cuentas pasan a impagas; copia de la base, publicar con el «dale» y probar volver atrás | C10, G6 | chico |
| 12 | COBRO-MP-1 | El aviso de pago de Mercado Pago, verificado; cada pago se aplica una vez; se controla el monto | C3 | medio |
| 13 | COBRO-MP-2 | Cancelar también cancela en Mercado Pago, con servicio hasta el fin del período pagado; una sola suscripción; no se pierden días pagados; reactivar exige pagar | C2, C4, C8 | grande |
| 14 | BACKUP-1 | Copia de la base programada fuera de Railway y una restauración probada | D1 | medio |
| 15 | DISCO-1 | El historial de NCM y los TXT descargados pasan a la base (hoy se borran en cada publicación) | D4 | medio |
| 16 | LEGAL-1 | Páginas de términos y de privacidad con el texto de Emi, y cómo pedir el borrado de los datos | X5 | chico |
| 17 | PUBLICAR-2 | Con el «dale» de Emi | — | chico |

Tamaño: chico = hasta medio día; medio = 1 a 2 días; grande = 3 días o más.

**Puertas:** G3 (aislamiento) y G6 (volver atrás) con PUBLICAR-1. G7 (cobro)
con PUBLICAR-2 y el cobro chico de Emi: alta, cobro, renovación, cancelación
(también en Mercado Pago) y corte.

### Cola MARIA (Dev 2, o Dev 1 después de PUBLICAR-1)

| Orden | Pieza | Qué arregla, en llano | Hallazgos | Tamaño | ¿Cambia el archivo? | Se publica |
|---|---|---|---|---|---|---|
| 1 | MARIA-2 | Sin clave de Gemini no se inventan productos: error claro | M4 | chico | no (evita productos falsos) | con PUBLICAR-1 |
| 2 | MARIA-1a | Lectura de la factura: el país de origen bien leído (hoy China sale como Suiza; está en **dos** copias del lector), cantidades con coma, nada de peso inventado | M5 | medio | sí, donde hoy está mal | con PUBLICAR-1 o 2. Prueba: la tabla oficial de países, que ya está en el código |
| 3 | MARIA-4 | **Estado de la mercadería e IVA adicional, como respondió el despachante:** el estado se elige entre seis, por producto (por defecto, nuevo sin uso importado si el origen es extranjero). El IVA adicional se paga completo en reventa: deja de declararse siempre «uso particular» | M2, M3 | medio | **sí** | con PUBLICAR-2. Prueba: las respuestas 1 y 2 del despachante y el archivo real de 2026 (`PREGUNTAS-DESPACHANTE.md`, «Respuestas») |
| 4 | MARIA-1b | Controles antes de generar: NCM que exista en el catálogo, moneda, incoterm, CUIT, montos; ningún texto puede meter líneas en el archivo | M10 | medio | no, con datos correctos | con PUBLICAR-1 o 2 |
| 5 | MARIA-3 | Los avisos se muestran **antes** de generar y completos; los gastos anteriores al FOB llegan al archivo en EXW; la procedencia se carga en pantalla | M6, M8 | grande | sí | con PUBLICAR-2. Prueba: la ley (Código Aduanero, art. 15), la nota del SIM y un archivo real con procedencia distinta del origen |
| 6 | MARIA-4b | El banco lo elige el cliente en cada operación: se carga en la operación (con el último que usó ese cliente como propuesta) y sale en el archivo (hoy no sale). La empresa de digitalización pasa a la configuración del estudio, con cambio por operación; por defecto, la de hoy hasta saber los códigos | — | medio | **sí** (el banco) | con PUBLICAR-2. Prueba: las respuestas 4 y 5 y el archivo real de 2026 |
| 7 | MARIA-5 | Peso total por producto (hoy sale el de una unidad) y cuentas exactas (hoy a veces no cierran por un centavo) | M1, M9 | medio | **sí** | El peso, con PUBLICAR-2. Prueba: la respuesta 3 y el archivo real de 2026. Las cuentas exactas, en la **Fase B**, con la prueba en su Kit. Los dos archivos reales tienen que salir idénticos |

MARIA-1b y MARIA-3 tocan la misma función que COBRO-CORTE-1: arrancan después
de que esa pieza esté aceptada. RENDIMIENTO-1 va después de MARIA-2 (tocan la
misma línea). MARIA-4, MARIA-3, MARIA-4b y MARIA-5 tocan el mismo generador: van en ese
orden, una después de la otra. MARIA-4 subió al tercer
lugar el 2026-10-07: el despachante ya respondió y hoy CDI declara el IVA
adicional como si toda la mercadería fuera de uso particular.

**Se miró y está bien** (no hace falta pieza): orígenes permitidos, cookies y
CSRF, cabeceras de seguridad y topes de subida de archivos.

### Lo que hace la PM mientras tanto

- Revisar cada pieza y reproducir cada hallazgo (`/revisar-entrega`).
- Escribir las herramientas que faltan: `suite-y-puertas.sh` (suite completa
  y puertas en una sola corrida) y un recorrido en navegador del camino
  principal (alta, cliente, PDF, validación, MARIA) para cada revisión.
- Preparar tres casos inventados (EXW, CIF, varios productos) para el archivo
  que se le manda al despachante a probar en su Kit.
- Medir el uso del plan con `medir.py` la primera semana.

## Fase B — con las respuestas del despachante

| Pieza | Qué hace | Espera |
|---|---|---|
| MARIA-6 | Según sus respuestas: el código de cada empresa de digitalización, gastos en FCA y FAS, y cómo va en el archivo una reducción o exclusión del IVA adicional | la pregunta 6 y dos cortas nuevas (1 a 5 ya respondidas) |
| MARIA-7 | Identificadores, sufijos de valor por producto y código de proveedor como en sus archivos reales | favor 1 (los archivos) |
| MARIA-5 | Se publican las cuentas exactas (el peso sale antes) | favor 2 |
| PRUEBA-KIT | El despachante carga en su Kit un archivo de CDI, sin oficializar | favor 2. **Cierra G4** |
| PUBLICAR-3 | Con el «dale» de Emi | — |

**Después:** piloto con 3 a 5 estudios, dos semanas, con el kit que ya existe
(`wave1_*`). Se eligen los más tolerantes, no los más grandes. **G8:** tres
estudios presentaron de verdad un MARIA generado por CDI. Luego, oleadas de
10 a 15 estudios con una semana entre una y otra.

## Qué hallazgo va en qué pieza

| Hallazgos | Pieza |
|---|---|
| C1, C5, C6 | COBRO-CORTE-1 |
| C2, C4, C8 | COBRO-MP-2 |
| C3 | COBRO-MP-1 |
| C7 | ORG-1 |
| C9, S4, S5, S6, X1 | ABUSO-1 |
| C10 | PUBLICAR-1 |
| S1 | publicación de ensayo o PUBLICAR-1 (ya arreglada en la rama) |
| S2 | ADMIN-1 |
| S3 | SESION-1 |
| M1, M9 | MARIA-5 |
| M2, M3 | MARIA-4 (con las respuestas 1 y 2) |
| M4 | MARIA-2 |
| M5 | MARIA-1a |
| M6, M8 | MARIA-3 |
| M7, M11 | MARIA-7 |
| M10 | MARIA-1b |
| D1 | BACKUP-1 |
| D2, D5, D6 | DATOS-1 |
| D3 | RENDIMIENTO-1 |
| D4 | DISCO-1 |
| X2, X4 | LIMPIEZA-1 |
| X3 | DEPENDENCIAS-1 |
| X5 | LEGAL-1 |
| X6 | Emi, en Railway |
| Clave de Gemini | Emi la rota (G0). Sacarla del archivo no alcanza: sigue en la historia, y esa historia no se reescribe |
| Otras cadenas con contraseña | LIMPIEZA-1 |

## Para decidir antes de que arranque cada pieza

- **COBRO-CORTE-1:** hoy la operación ya se cuenta al crearla. Generar el
  MARIA no tiene que cobrarse otra vez por cada descarga: cuenta una vez por
  operación. Lo decide la PM salvo que Emi diga otra cosa.
- **ORG-1:** no hay ninguna prueba de organizaciones. Primero se reproduce el
  error de las invitaciones en Postgres local.
- **MARIA-5 y MARIA-6:** el redondeo es una sola decisión, con la respuesta
  del despachante.

## Fuera de este plan (propuesto para después)

- Ordenar `HANDOFF.md`, que está desactualizado.
- Partir `main.py` (8.400 líneas). No es urgente y toca todo.
- VUCE-4, el listado de cobro para el admin: va después de ADMIN-1.
- AFIP/WSAA y VUCE reales: siguen simulados por decisión.

## Riesgos del plan

| Riesgo | Mitigación |
|---|---|
| Las respuestas del despachante tardan | Fase A no las espera. Lo único que queda frenado es MARIA-5 a MARIA-7 y el piloto |
| La normativa no se puede leer desde la nube | Cada cambio del archivo, con su fuente y la confirmación del despachante |
| Dos Devs se pisan en `main.py` | Orden fijado arriba: lo que comparte función va en secuencia |
| Mercado Pago se comporta distinto en producción que en pruebas | Cobro real chico con la tarjeta de Emi antes del piloto |
| El plan de uso compartido no alcanza con dos Devs | Medir con `medir.py` la primera semana; si no rinde, se cierra la Dev 2 |
