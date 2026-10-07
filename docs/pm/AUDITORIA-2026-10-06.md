# Auditoría — 2026-10-06

Verificación del plan de septiembre contra el código. Emi la aprobó el
2026-10-06.

- **Rama de trabajo:** `claude/project-deploy-review-4nct96` = `e8344d0`.
- **Publicado:** `main` = `a771693`, del 2026-07-18.
- **Cómo se hizo:** cinco subagentes atacaron en paralelo una copia local, con
  datos inventados y sin servicios de terceros. Dos investigaron la normativa en
  la web. La PM reprodujo lo más grave.
- **Qué significa cada marca:** «PM» = la PM lo corrió y vio el resultado.
  «sub» = lo reprodujo sólo el subagente, con salida. «código» = sale de leer el
  código, sin correrlo.
- Los scripts de reproducción quedaron fuera del repositorio (tienen datos de
  prueba).

## En una línea

**Las pruebas están sanas y la separación entre estudios está bien hecha en la
rama de trabajo. Pero el cobro no corta a quien no paga, el archivo MARIA
declara mal el peso y otros campos, y hay agujeros de sesión y permisos.**
Nada de esto afecta hoy a nadie, porque producción la usa sólo Emi. Todo tiene
que estar resuelto antes del primer estudio.

## Lo que se confirmó de septiembre

| Afirmación | Resultado |
|---|---|
| Suite: «680 passed, 102 skipped, 0 failed» | ✅ PM/sub: `680 passed, 102 skipped` en 65 s |
| G1: la app no arranca con configuración mala | ✅ G1.1–G1.4 (sub) y G1.5 sin `DATABASE_URL` (PM: `RuntimeError`, salida 1) |
| G3: «22 bloqueados, 0 fugas» | ✅ sub en la rama. Pero el script cubre sólo clientes y descargas |
| Publicar no rompe el esquema de la base | ✅ sub: `models.py` idéntico. Ir y volver entre versiones funciona en SQLite |
| Catálogo NCM: «22 posiciones de ~9.500» | ❌ quedó viejo: hoy hay **10.226** posiciones de ARCA (julio de 2026) |
| «Agujero de cobro cerrado» (VUCE-3) | ❌ cerró el vencimiento de los `active`, no el corte en lo que genera valor (ver Cobro) |

## Hallazgos

Ordenados por gravedad dentro de cada área. Las categorías: **Rompe** (algo
falla, se pierde, se filtra o se cobra mal), **Riesgo** (puede pasar en un caso
borde), **Prueba** (no lo ve el usuario).

### Cobro (G7)

| # | Qué pasa | Cat. | Marca | ¿En prod. hoy? | Esfuerzo |
|---|---|---|---|---|---|
| C1 | El corte por falta de pago (402) está sólo en 2 funciones (guardar operación). Una cuenta impaga genera el MARIA, sube PDFs a Gemini, pide sugerencias de NCM y hace migraciones | Rompe | **PM** (`/generate_maria` → 200 con `past_due`) | sí | medio |
| C2 | Cancelar en CDI no cancela la suscripción en Mercado Pago: la tarjeta se sigue cobrando. Además corta el servicio en el acto, aunque dice «activo hasta…» | Rompe | **PM** (código: no hay ninguna llamada a MP en `cancel`) | sí | medio |
| C3 | El aviso de pago sin firma (formato IPN) se acepta aunque esté el secreto. Sólo recuerda el último pago: reenviando pagos viejos alternados se renueva gratis | Rompe | PM parcial (el test G7 lo muestra); la repetición, código | sí | medio |
| C4 | El checkout no mira si ya hay suscripción: se puede pagar dos veces. Cada pago fija 30 días desde hoy, y se pierden los días que quedaban | Rompe | código | sí | chico |
| C5 | `/generate_maria` no cuenta operaciones: 17 generaciones con tope 15 y el contador en 0 | Rompe | sub | sí | chico |
| C6 | Carreras: con pedidos en paralelo se pasa el tope del plan y los `op_code` se duplican | Riesgo | sub (Postgres local) | sí | medio |
| C7 | Organizaciones: el límite de 3 usuarios no se aplica (llegó a 7). La invitación no está atada al email. **En Postgres, validar o usar una invitación da error 500** | Rompe | sub | sí | chico |
| C8 | Cancelar y reactivar desde una prueba gratis deja la cuenta «activa» con 7 días de gracia, sin haber pagado | Riesgo | código | parcial | chico |
| C9 | Pruebas gratis infinitas: un email nuevo da 14 días más, y el registro no tiene límite | Riesgo | sub | sí | chico |
| C10 | Al publicar la rama, el primer arranque pasa a `past_due` a todo `active` vencido hace más de 7 días. No se deshace al volver atrás | Riesgo | sub | — | chico (contar antes) |

### Sesión y permisos

| # | Qué pasa | Cat. | Marca | ¿En prod.? | Esfuerzo |
|---|---|---|---|---|---|
| S1 | **Fuga de MARIA.TXT entre estudios en producción:** cualquier usuario baja la declaración de otro adivinando el número de factura, y también su historial de NCM. Arreglado en la rama (c9aceef), no publicado | Rompe | sub (con la copia de `a771693`) | **sí** | chico (se arregla al publicar) |
| S2 | `/api/admin/*` abierto a cualquier usuario: salud del servidor, errores, métricas, y **borrar el registro de errores** | Rompe | **PM** (usuario común: `clear-old` → 200) | sí | chico |
| S3 | Resetear o cambiar la contraseña **revive** todas las sesiones viejas, incluso las ya revocadas. Cerrar sesión no revoca. Con una sesión robada se cambia el email sin contraseña y se toma la cuenta | Rompe | sub | sí | chico-medio |
| S4 | El límite de intentos de login usa una IP que manda el cliente (`X-Forwarded-For`): se esquiva, y se puede bloquear a otra persona | Riesgo | sub | sí* | medio |
| S5 | `/api/ui/event` sin sesión ni tope de tamaño: 4 pedidos de 5 MB llenaron 21 MB de disco | Riesgo | sub | sí | chico |
| S6 | Enumeración de usuarios y emails en el registro; recuperar usuario sin límite (correo masivo) | Riesgo | sub | sí | chico |

\* Depende de cómo pase la IP el proxy de Railway; no se pudo verificar.

### Archivo MARIA y producto (G4)

| # | Qué pasa | Cat. | Marca | ¿Necesita despachante? | Esfuerzo |
|---|---|---|---|---|---|
| M1 | **El peso del TXT es el de una unidad:** 10 notebooks de 2,5 kg salen como 2,5 kg. La pantalla de validación sí muestra el total | Rompe | **PM** (`QARTKGRNET=2.500` para 10 × 2,5) | confirmar (pregunta 3) | chico |
| M2 | `CARTUSO` siempre 3. Según la investigación, 3 = «usado argentino»; para mercadería nueva importada iría 2 | Rompe | **PM** (TXT: `CARTUSO=3`) | sí (pregunta 1) | chico |
| M3 | `IVAADICIONAL1` siempre `IVAAD1`. Según la investigación, es «uso o consumo particular», que exceptúa la percepción. Para reventa no correspondería | Rompe | **PM** (TXT) | sí (pregunta 2) | chico |
| M4 | Sin clave de Gemini, la extracción inventa ítems de demostración, que llegan al TXT sin marca | Rompe | sub | no | chico |
| M5 | El extractor corta el origen a 2 letras: `CHN` → `CH` = **Suiza**, `MEX` → Montenegro. Cantidades con coma se descartan en silencio; peso faltante = 0,5 | Rompe | sub (con simulación) | no | chico |
| M6 | Los avisos de supuestos se muestran **después** de generar, debajo del botón de descarga, y faltan varios | Rompe | sub | no | medio |
| M7 | Identificadores (`IDSO`, `IEXT`, `NDDTIMMTRN`) armados con el número de factura, y `LDVDREFDOC` inventado | Rompe | sub | sí (pregunta 7) | medio |
| M8 | El campo «gastos anteriores al FOB» está en pantalla pero no llega al TXT. La procedencia sigue igual al origen | Rompe | sub | no (la ley y el aviso lo resuelven) | chico |
| M9 | Las cuentas usan decimales binarios: el seguro de los ítems suma 10,01 contra 10,00 | Riesgo | sub | sí (pregunta 10) | medio |
| M10 | Valida sólo el formato: NCM inexistente, moneda, incoterm, CUIT y flete negativo pasan. Un nombre con salto de línea inyecta líneas en el TXT | Riesgo | sub | no | chico |
| M11 | El mismo sufijo SBT va a todos los ítems | Riesgo | sub | sí (pregunta 9) | medio |

### Datos y operación (G6)

| # | Qué pasa | Cat. | Marca | Esfuerzo |
|---|---|---|---|---|
| D1 | No hay ninguna copia de seguridad de la base de producción | Riesgo | sub (no hay mecanismo) | medio |
| D2 | `/health` responde 200 con la base caída (Railway no lo detecta) y muestra el error de la base al público | Riesgo | sub | chico |
| D3 | Una extracción de PDF frena todo el servidor (un solo proceso, llamada que bloquea) | Riesgo | sub (simulado) | chico |
| D4 | El historial de NCM de cada estudio vive en el disco de Railway, que se borra en cada publicación | Rompe | código | medio |
| D5 | Borrar un cliente con presupuesto compartido da error en Postgres: no se puede cumplir un pedido de supresión de datos | Rompe | sub (Postgres local) | chico |
| D6 | Los errores 500 devuelven el texto de la excepción (`dev_detail`) también en producción | Riesgo | sub | chico |

### Secretos (G0)

- Una clave de Gemini estuvo en este repositorio cuando era público
  (`docs/audits/AUDITORIA_PRE_TESTING_5_USUARIOS.md`). Emi lo pasó a privado:
  falta rotarla.
- En `Memu007/CDI`, `RAILWAY_SETUP.md` tiene escrita una clave de sesión. Si es
  la de Railway, hay que cambiarla.
- Revisar dos cadenas de conexión con contraseña posible:
  `cloudbuild.yaml:87` (en `main`) y
  `docs/deployment/PLAN_DEPLOY_ADVERSARIAL.md:76`. La PM no las abrió.

## Agregado del 2026-10-07: lo que la auditoría no había mirado

Un auditor (Sonnet alto) sobre `e8344d0`. Marca: «sub» = lo corrió el
subagente, con salida; «código» = leído; «PM» = la PM lo confirmó leyendo el
archivo.

| # | Qué pasa | Cat. | Marca | Esfuerzo |
|---|---|---|---|---|
| X1 | Las sugerencias de NCM llaman a Gemini sin ningún tope (ni por minuto ni por día). Es la única función con IA sin límite (`main.py:6930`) | Riesgo | código (PM: sin `@limiter` en la ruta) | chico |
| X2 | La CI (las pruebas automáticas de GitHub) excluye a mano 10 pruebas desde julio, entre ellas las de presupuestos públicos y una de CSRF. Hoy las 10 pasan; si se rompen, la CI no lo ve (`.github/workflows/ci.yml:36-47`) | Riesgo | sub (10 + 4 passed; suite sin exclusiones: 680/102/0) | chico |
| X3 | Librerías con fallas conocidas: el lector de PDF viejo (`PyPDF2 3.0.1`) se cuelga con un PDF armado; `python-jose` y `ecdsa` tienen avisos de seguridad | Riesgo | sub (`pip-audit`: 4 avisos en 3 librerías; el cuelgue, reproducido con un PDF hecho a mano) | medio |
| X4 | `cloudbuild.yaml` es un segundo camino de publicación (Cloud Run, abierto al público). En el repositorio nada lo dispara; no se pudo ver si en Google Cloud hay un disparador armado | Riesgo | código (PM: no hay `deploy.yml` ni en `main` ni en la rama) | chico |
| X5 | No hay páginas de términos ni de privacidad, ni una forma de pedir el borrado de datos | Riesgo | código (`templates/`) | chico (el texto lo pone Emi) |
| X6 | Si el correo no está configurado en producción, recuperar la contraseña falla en silencio | Riesgo | código | — (lo revisa Emi en Railway) |

**Se miró y está bien:** orígenes permitidos (CORS), cookies de sesión y CSRF,
cabeceras de seguridad, y topes de tamaño y tipo en la subida de PDF, Excel y
CSV.

## Lo que no se pudo ver

Producción real (variables de Railway, si hay volumen o backups), Mercado Pago
real, Gemini real, la normativa oficial (la red la bloquea), el Kit María, y el
comportamiento con carga.

## Quién encontró qué

Detalle por subagente, con modelo y esfuerzo, en
`archivo/MEDICION-SUBAGENTES.md`.
