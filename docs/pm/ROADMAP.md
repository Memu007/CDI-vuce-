# Roadmap — aprobado por Emi el 2026-10-24 («Dale. Comenzá»)

> Reemplaza las semanas del 2026-10-07. Sale de la reunión de prueba con el
> despachante del 2026-10-24: el TXT de una factura real entró al MARIA
> después de corregirlo a mano doce veces. Lo que hubo que corregir es la
> Fase 1b. Tres meses: del 26/10/2026 al 24/01/2027. Estado y evidencia en
> `NOW.md`; los acuerdos de la reunión, en `DECISIONS.md` (2026-10-24).

## Para Emi

**Primero que el TXT entre al MARIA sin tocarlo; después el cobro; la
seguridad antes de cualquier estudio nuevo.** Dos Devs nuevas: la Dev MARIA
(el TXT, esfuerzo alto) y la Dev técnica (lectura, clientes, cobro y
seguridad, esfuerzo medio).

| Semanas | Fechas | Fase | Está lista cuando… |
|---|---|---|---|
| 1 y 2 | 26/10 al 08/11 | **1b · El TXT entra al MARIA sin tocarlo** | la factura de lonas del 24/10, subida tal como vino, da un TXT que el MARIA carga sin errores (subítems, sufijos, unidades, flete, ajustes) |
| 3 y 4 | 09/11 al 22/11 | **1c · Pruebas con el despachante** y sufijos automáticos | el despachante prueba 3 o 4 operaciones reales en dos sesiones (cada 15 días) y no corrige nada a mano salvo lo que decide él |
| 5 y 6 | 23/11 al 06/12 | **2 · El cobro** con Mercado Pago | pagás con tu tarjeta y ves alta, cobro, cancelación y corte |
| 7 a 9 | 07/12 al 27/12 | **3 · Seguridad y datos, a fondo** | una auditoría nueva y completa no encuentra nada grave, y está publicado |
| 10 a 13 | 28/12 al 24/01 | **4 · Piloto** con 3 a 5 estudios | tres estudios presentaron un MARIA hecho con CDI |

**Lo que hacés vos:**
- **Esta semana:** el «dale» para publicar la mejora del Excel (EXCEL-2,
  ya aceptada); mandarle al despachante las preguntas 5 a 9 de
  `PREGUNTAS-DESPACHANTE.md` (los destinos, el packing y los despachos
  llegaron el 28/10).
- **Al terminar la Fase 1b (~08/11):** la sesión con el despachante para
  probar; la siguiente, 15 días después.
- **En la Fase 2:** pagar un plan chico con tu tarjeta.
- **Antes del piloto:** textos de términos y privacidad, quién atiende el
  soporte, qué estudios entran, precio y fecha.
- **Pendiente de antes:** cambiar la clave de Gemini.

**Riesgos:**
- **El MARIA sólo lo tiene el despachante.** Cada prueba depende de su
  tiempo: por eso las sesiones quincenales quedan fijas.
- **La lectura con IA puede inventar** (lo dijo el despachante). Todo dato
  que la IA no encontró en la factura queda marcado para que lo complete el
  despachante; nunca se rellena solo.
- **VUCE puede cambiar o caerse.** Si no responde, el sistema pide los
  sufijos a mano y lo avisa; no inventa.
- **Fiestas de fin de año:** la Fase 3 cae en diciembre; si se corre, se
  corre el piloto, no la seguridad.

**Fuera de estos tres meses (decide Emi si entra después):** el bot de
turnos de las terminales portuarias (es otro producto), la exportación
completa (EC*), estudios con varias sucursales.

---

**Avance:** `python3 docs/pm/herramientas/avance.py` lo cuenta desde las
marcas de cada pieza de abajo: ✅ aceptada por la PM, 🔵 en curso o lista
sin revisar, ⏳ espera a alguien de afuera (despachante, Emi), ⚪ sin
empezar. La PM cambia la marca en el mismo commit del veredicto. Aceptada
no es publicada: lo publicado está en `NOW.md`, «Publicado».

## Detalle, para la PM y las Devs

**Regla del archivo** (límite que no se negocia): lo que cambia el TXT
necesita prueba: la ley, un archivo real, la respuesta del despachante o la
prueba en su MARIA. La reunión del 24/10 cuenta como prueba para lo que se
corrigió en vivo (ver «Prueba» abajo). Los TXT corregidos de esa reunión
tienen datos reales de un cliente: **no entran al repositorio**; las pruebas
usan un sintético con la misma forma.

### Fase 1b — El TXT entra al MARIA sin tocarlo (semanas 1 y 2)

**Dev MARIA (Dev 2, esfuerzo alto):**

| Orden | Pieza | Qué arregla | Prueba |
|---|---|---|---|
| 1 | ✅ MARIA-7 | Lo que el MARIA rechazó el 24/10: todas las líneas con CRLF; identificador de la operación corto (`IDSO`, `IDDT`, `IARTESPAPU`; con 19 caracteres el MARIA lo rechaza, con 8 lo acepta); `CDDTAGR` (CUIT del despachante) obligatorio: sin él no se genera; la referencia de la factura (`LDVDREFDOC`) es el número real de la factura; unidad declarada la de la factura (m² = `03`, no `07` unidad); con unidad estadística en kilos, la cantidad estadística es igual al kilo neto, al centésimo; en sufijos y textos libres sólo letras, números y espacios (lo demás, espacio); el número de cuenta del banco nunca va como identificación del proveedor | los errores del MARIA del 24/10 (capturas de Emi) y el TXT que finalmente cargó |
| 2 | ✅ MARIA-8 | Subítems por posición: cada renglón de la factura es un subítem con sus sufijos propios; los renglones con la misma posición SIM, origen, procedencia y estado van en un solo ítem; las sumas del ítem cierran exactas | el TXT de 1 ítem con 48 subítems que cargó el 24/10 |
| 3 | ✅ VALOR-1 | Ajustes a incluir, ajustes a deducir y FOB casillero: campos que carga el usuario (el sistema no decide qué se descuenta) y cuentas a la vista; botón «calcular seguro» (1 % de FOB + flete) cuando la factura no lo trae; el reparto ítem por ítem queda para PRORRATEO-1 | reunión del 24/10 (forma: FOB de factura − ajuste = FOB casillero; seguro = 1 % de FOB + flete) |
| 4 | ✅ SEPARADORES-1 | Montos con punto o coma: «3.480» y «3.480,00» son tres mil cuatrocientos ochenta, «3,48» es tres con cuarenta y ocho; si es ambiguo, se pregunta | el flete del 24/10 salió mil veces más chico |

**Dev técnica (Dev 1, esfuerzo medio):**

| Orden | Pieza | Qué arregla | Prueba |
|---|---|---|---|
| 0 | ✅ EXCEL-2 | Ya aceptada: integrar y publicar con el «dale» de Emi | — |
| 1 | ✅ EXCEL-3 | La proforma china del 24/10 se lee tal como viene: encabezado en la fila 11, descripción que vale para los renglones de abajo, columnas `Specification`, `QTY (Rolls)`, `SM.TOTAL (sqm)`, `Unit price (USD/sqm)`, `Gross Weight(kgs)`; la cantidad es la unidad del precio (m²); descuento, flete y totales no son productos y el descuento se ofrece como ajuste | un sintético con la misma forma (la proforma real no entra al repo) |
| 2 | ✅ CLIENTE-1 | Alta de cliente con lo que pide el MARIA: CUIT, razón social, domicilio y fecha de inicio de actividades; email y teléfono dejan de ser obligatorios | reunión del 24/10 |
| 3 | ✅ ESTUDIO-1 | El CUIT del despachante se carga por estudio (puede haber varios) y se elige en la operación; va solo al `CDDTAGR` | reunión del 24/10 |
| 4 | ✅ PA-1 | En pantallas, «NCM» pasa a «Posición arancelaria (PA SIM)» donde se habla de la posición de 11 dígitos con su letra | reunión del 24/10 |

**Cierre de la Fase 1b:** publicar con el «dale»; la factura de lonas,
subida tal como vino, da un TXT que el MARIA carga sin errores.

### Fase 1c — Pruebas con el despachante y sufijos automáticos (semanas 3 y 4)

**Dev MARIA:**

| Orden | Pieza | Qué arregla | Prueba |
|---|---|---|---|
| 1 | ✅ SUFIJOS-1 | Con la posición SIM, el sistema trae de VUCE (consulta pública `/cice/sufijos/<posición>`) qué sufijos pide y la unidad estadística; los completa con lo que la IA encuentra en la factura (marca, modelo, código, medidas, color); el código de artículo (`AI`) es distinto en cada renglón; lo que falta queda marcado para el despachante; sin VUCE, se piden a mano con aviso | la consulta a VUCE del 24/10 (una posición de plásticos pidió AA marca y AI código; unidad kilogramo `01`) |
| 2 | ✅ DESTINO-1 | Tres destinos por operación: comercialización en el mercado interno, bien de uso de la empresa, bien de uso particular, con su código en el TXT. Corrige lo de hoy: `GANANCIASOP3` siempre `COMERC` y «uso particular» con `COMERC` + `IVAAD1` | los tres pares del despachante del 28/10 (`COMERC`/`NO_VALIDA`, `BDEUSO`/`IVAAD2`, `USOPAR`/`IVAAD1`) |
| 3 | 🔵 SUFIJOS-2 | Sufijos (D7 de MARIA-7): un número en un sufijo libre puede llevar coma; en uno que pide número, sin decimales (hoy `2.5` sale `2 5`); ninguno vacío (hoy `AA()` pasa) | respuesta del despachante del 28/10 |
| 4 | 🔵 SEGURO-1 | El botón «calcular seguro» no se ofrece en CIF, CIP, DPU, DAP y DDP (D14 de VALOR-1); el seguro se sigue declarando | respuesta del despachante del 28/10 |
| 5 | ⏳ PESO-NETO-1 | El peso neto sale del packing list cuando la factura sólo trae bruto; si no hay packing list, el aviso de hoy | un packing list, tapado, de cualquier operación (las lonas no tienen; mientras, el aviso de hoy) |
| 6 | ⏳ MARIA-6 | Identificadores y sufijos como en los archivos reales del despachante (M7, M11) | sus archivos TXT reales (los despachos del 28/10 muestran los sufijos, no el TXT) |
| 7 | 🔵 DESPACHO-1 | Sumada por Emi el 28/10; ubicada por la PM (Emi: «acomodalo dónde digas»): después de ORG-1, detrás de las piezas que hacen entrar el TXT; como todas esperan al despachante, se hace la primera que tenga lo suyo; tiene que estar lista antes del piloto (28/12), porque es lo que facilita sumar estudios. Para que un despachante que viene de otro sistema arme rápido el catálogo de sus clientes con despachos que ya tiene, y después haga el predespacho en CDI con ese catálogo. El despacho oficializado es el formulario OM-1993-A SIM que el despachante imprime y firma después de oficializar en el MARIA; trae por ítem y subítem la posición SIM, los sufijos, el origen, la procedencia, el estado, la unidad, la cantidad, el FOB y el peso neto (normativa de ARCA, búsqueda del 28/10). Subir un despacho ya oficializado para armar el catálogo del cliente: se lee por renglón la posición SIM, la descripción, los sufijos, el origen, la unidad, el valor unitario y el peso; se revisa y se edita en pantalla antes de guardar en el catálogo de ese cliente; el catálogo del cliente se puede bajar en Excel, o en el formato que usen los despachantes si la pregunta 6 trae uno. Nunca arma un TXT ni una operación (el lector de facturas sigue rechazando despachos); lo que no se encontró queda marcado, no se rellena | tres despachos oficializados del despachante, del 28/10 (los reales sólo fuera del repo; las pruebas usan un sintético con la forma de `DESPACHOS-FORMA.md`) |

**Dev técnica:**

| Orden | Pieza | Qué arregla |
|---|---|---|
| 0 | EXCEL-2b | Carril liviano: una subida chica no espera en cola detrás de libros pesados (vuelve a cumplir el criterio D26 a de EXCEL-2, ya aceptada; arreglo de esa pieza, no cuenta aparte; D4 y D5 de la técnica, 28/10) |
| 1 | ✅ GUARDAR-2 | La sugerencia de posición: si el historial del cliente tiene 8 dígitos y el proveedor la SIM completa que empieza con esos 8, gana la del proveedor (D32 b; sin migración; Postgres descartable) |
| 2 | 🔵 ORDEN-1 | Reordenar los productos arrastrando, en la pantalla de revisión |
| 3 | COBRO-MP-1 | Primera pieza de la Fase 2 (ver abajo) |

**Cierre de la Fase 1c (cierra G4):** dos sesiones con el despachante, 3 o
4 operaciones reales cargadas en el MARIA sin corregir el TXT a mano.

### Fase 2 — Cobro (semanas 5 y 6)

| Pieza | Quién | Qué arregla |
|---|---|---|
| 🔵 COBRO-MP-1 | Dev técnica | Aviso de pago verificado, aplicado una vez, con el monto controlado; las renovaciones extienden el período (C3, D8) |
| 🔵 COBRO-CORTE-1 | Dev técnica | Quien no paga no genera ni gasta Gemini; contar una vez por operación sin pasarse del tope (también con guardados a la vez); el aviso dice la razón real (C1, C5, C6; D4 b N = 10, D5 a, D6 a) |
| 🔵 COBRO-MP-2 | Dev técnica | Cancelar también en Mercado Pago sin perder días pagados, una sola suscripción, reactivar pagando (C2, C4, C8, D9) |
| ⏳ PRORRATEO-1 | Dev MARIA | El reparto ítem por ítem de ajustes, seguro y flete hasta el FOB casillero, con las sumas exactas al centavo (segunda etapa acordada el 24/10) |
| ✅ ORG-1 | Dev MARIA | Invitaciones que funcionan, tope de usuarios del plan, atadas al email (C7) |
| ⏳ LEGAL-1 | Dev MARIA | Términos y privacidad con el texto de Emi; aviso de que CDI es un asistente y el despachante revisa; cómo pedir el borrado de datos (X5) |

**Cierre:** publicar; el pago chico de Emi recorre todo el ciclo (cierra G7).

### Fase 3 — Seguridad y datos, a fondo (semanas 7 a 9)

Sin cambios respecto del 2026-10-07, más OBSERVABILIDAD-1:

| Pieza | Quién | Qué arregla |
|---|---|---|
| 🔵 SESION-1 | Dev MARIA | Ver `AUDITORIA-2026-10-06.md` |
| 🔵 ABUSO-1 | Dev MARIA | Ver `AUDITORIA-2026-10-06.md` |
| ✅ EMAIL-1 | Dev MARIA | Sumada por Emi el 28/10 (D36 de MARIA): recuperar usuario y contraseña encuentran el email con otras mayúsculas; ningún alta ni cambio crea un email repetido con otras mayúsculas; los pares que ya existan no se tocan hasta que Emi los cuente |
| 🔵 CONEXIONES-1 | Dev MARIA | Sumada por Emi el 28/10 (D37 de MARIA): medir si el cierre de la sesión de base cancelado deja conexiones tomadas, con Postgres 16; arreglar sólo si las deja |
| 🔵 AISLAMIENTO-2 | Dev técnica | Ver `AUDITORIA-2026-10-06.md` |
| 🔵 LIMPIEZA-1 | Dev técnica | Ver `AUDITORIA-2026-10-06.md` |
| 🔵 OBSERVABILIDAD-1 | Dev MARIA | La columna `api_logs.owner_username` que falta en producción, con migración probada en Postgres descartable |
| ✅ DATOS-1 | Dev MARIA | Borrar un cliente con presupuesto; `/health` honesto; sin detalles de error al público (D5, D2, D6 de `AUDITORIA-2026-10-06.md`) |
| 🔵 BACKUP-1 | Dev técnica (pasada por la PM el 28/10) | Ver `AUDITORIA-2026-10-06.md`. BACKUP-1a: copia y restauración probada; el destino fuera de Railway y dónde se programa esperan a Emi |
| 🔵 DISCO-1 | Dev MARIA | El historial de NCM de cada estudio pasa del disco de Railway a la base (D4 de `AUDITORIA-2026-10-06.md`) |
| ⚪ AUDITORIA-FINAL | PM | Ver `AUDITORIA-2026-10-06.md` |

**Cierre:** publicar y probar volver atrás (cierra G3 y G6). Recién ahí
entra el primer estudio nuevo.

### Fase 4 — Piloto (semanas 10 a 13)

Con el kit `wave1_*`. Los estudios más tolerantes, no los más grandes; el
despachante de la prueba, primero. Cierra G8.

| Pieza | Quién | Qué arregla |
|---|---|---|
| ⚪ PILOTO-1 | PM y Emi | Tres estudios presentan un MARIA hecho con CDI |

### Referencias

- Hallazgos (C, S, M, D, X): `AUDITORIA-2026-10-06.md`.
- Acuerdos de la reunión del 2026-10-24: `DECISIONS.md`.
- Fuera del plan: ordenar `HANDOFF.md`, partir `main.py`, VUCE-4, AFIP
  real, el bot de turnos, la exportación completa.
