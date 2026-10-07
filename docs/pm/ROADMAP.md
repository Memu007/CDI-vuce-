# Roadmap — aprobado por Emi (orden del 2026-10-07)

## Para Emi

**Primero el TXT, después el cobro, la seguridad al final.** Ningún estudio
entra antes de terminar la seguridad. Semanas desde el 2026-10-07.

| Semanas | Fase | Está lista cuando… |
|---|---|---|
| 1 a 3 | **1 · El TXT:** subís un PDF o un Excel, lee todo solo y sale el MARIA.TXT bien | subís 2 o 3 facturas reales y el TXT sale bien, y el despachante lo carga en su Kit sin corregirlo |
| 4 y 5 | **2 · El cobro** con Mercado Pago | pagás con tu tarjeta y ves alta, cobro, cancelación y corte |
| 6 y 7 | **3 · Seguridad y datos, a fondo** | una auditoría nueva y completa no encuentra nada grave, y está publicado |
| 8 y 9 | **4 · Piloto** con 3 a 5 estudios | tres estudios presentaron un MARIA hecho con CDI |

Después, de a 10 o 15 estudios por semana.

**Lo que hacés vos:**
- **Mañana:** la revisión de Railway y el «dale» para la publicación de
  ensayo, que cierra la fuga de hoy (lista en `NOW.md`).
- **Esta semana:** cambiar las claves de Gemini; recordarle al despachante
  los archivos reales.
- **Al terminar la fase 1:** probar con 2 o 3 facturas reales.
- **En la fase 2:** crear los planes en Mercado Pago y pagar uno chico.
- **Antes del piloto:** textos de términos y privacidad, correo del sitio,
  quién atiende el soporte, qué estudios entran, precio y fecha.

**Riesgos:**
- **La seguridad va al final y el sitio ya tiene facturas reales.** Por eso
  el ensayo de mañana y la revisión de Railway no se mueven.
- **La lectura con Gemini de verdad sólo la podés probar vos.** Desde acá se
  prueba con uno simulado.
- **Si el despachante tarda, se corre la prueba en su Kit,** no el resto.

---

## Detalle, para la PM y las Devs

**Regla del archivo** (límite que no se negocia): lo que cambia el TXT
necesita prueba: la ley, un archivo real o la respuesta del despachante
(`PREGUNTAS-DESPACHANTE.md`). Columna «Prueba» abajo.

### Fase 1 — El TXT

**Dev 2:**

| Orden | Pieza | Qué arregla | Prueba para el TXT |
|---|---|---|---|
| ✅ | MARIA-2 | Sin clave de Gemini no se inventan productos (M4) | no cambia el TXT |
| ✅ | MARIA-1a | País de origen bien leído (China salía Suiza), cantidades y precios con coma, nada inventado si falta un dato (M5) | tabla oficial de países (VUCE) e ISO 3166-1 |
| ✅ | MARIA-2b | Con Gemini caído o la clave inválida, el mismo error claro y la carga manual | no cambia el TXT |
| 1 | MARIA-1c | Lo que el lector encontró pero no pudo leer (flete, seguro) se avisa en vez de salir 0; la pantalla vieja no repone cantidad 1 ni origen China (D5 de la Dev 2). Se publica junto con MARIA-1a | no cambia el TXT de una factura bien leída |
| 2 | MARIA-4 | Lo que decide el despachante: estado de la mercadería (seis, por producto), IVA adicional (completo en reventa; si hay reducción o exclusión, aviso de que se elige en «Ventajas» del Kit, no va en el TXT), banco y empresa de digitalización (las dos por operación; Modoc = `PSAD06`, Lakaut = `PSAD01`) (M2, M3) | respuestas 1, 2, 4 y 5, las dos cortas y el archivo real de 2026 |
| 3 | MARIA-3 | Avisos antes de generar; gastos anteriores al FOB en EXW, FCA y FAS; procedencia en pantalla (M6, M8) | respuesta 6, Código Aduanero art. 15, nota del SIM, archivo real de 2025 |
| 4 | MARIA-5 | Peso total por producto; cuentas exactas al centavo (M1, M9) | peso: respuesta 3 y archivo real de 2026; cuentas: la prueba en el Kit |
| 5 | MARIA-6 | Identificadores y sufijos como en los archivos reales del despachante (M7, M11) | sus archivos reales |

MARIA-4, MARIA-3 y MARIA-5 tocan el mismo generador: van en ese orden.
MARIA-6 arranca cuando lleguen sus archivos reales.

**Dev 1:**

| Orden | Pieza | Qué arregla |
|---|---|---|
| ✅ | ADMIN-1 | Lo de administración, sólo para el admin (S2) |
| ✅ | ADMIN-2 | Lo que encontró en ADMIN-1 (activar una suscripción sin pagar, configuración del sistema a la vista, dos puntos ciegos de la prueba) |
| ✅ | RENDIMIENTO-1 | Leer un PDF no frena el sitio y tiene un tiempo máximo; el lector de PDF viejo, que se cuelga con un PDF armado, se cambia por su sucesor (D3, X3) |
| 1 | RENDIMIENTO-1b | Un PDF armado no deja a nadie sin lectura: la adivinanza del vendedor usa sólo `pypdf`; tiempos en 0 o negativos caen al valor por defecto (D10 b de la Dev 1). Se publica junto con RENDIMIENTO-1 |
| 2 | EXCEL-1 | Revisar la carga por Excel de punta a punta (nunca se auditó) y arreglar lo que falle; leer un Excel tampoco frena el sitio (D12 de la Dev 1) |
| 3 | MARIA-1b | Controles antes de generar: NCM del catálogo, moneda, incoterm, CUIT, montos; ningún texto mete líneas en el TXT; al guardar la operación no se inventan cantidad 1 ni peso 0,5 (M10, D6 de la Dev 2) |
| 4 | PUNTA-A-PUNTA-1 | Prueba automática: sube un PDF y un Excel (Gemini simulado) y compara el TXT con los archivos reales |

**Cierre:** publicar con el «dale»; Emi prueba con facturas reales; el
despachante carga un archivo en su Kit (cierra G4).

### Fase 2 — Cobro

| Pieza | Quién | Qué arregla |
|---|---|---|
| COBRO-MP-1 | Dev 1 | Aviso de pago verificado, aplicado una vez aunque se reenvíe, con el monto controlado (C3, D8 de la Dev 1). Va primero: es el único camino que hoy activa sin pagar. Además, que las renovaciones de la suscripción extiendan el período (hoy sólo se procesa `type=payment`; leído en el ataque al ensayo, sin verificar) |
| COBRO-CORTE-1 | Dev 1 | Quien no paga no genera valor ni gasta Gemini; se cuenta una vez por operación; sin pasarse del tope; el aviso del corte dice la razón real (hoy una cuenta que fue activa recibe «prueba vencida») (C1, C5, C6). Ya decidido: D4 (b, N = 10), D5 (a), D6 (a) de la Dev 1 (`PARA-DEV.md`) |
| COBRO-MP-2 | Dev 1 | Cancelar también en Mercado Pago, sin perder días pagados, una sola suscripción, reactivar pagando (una prueba gratuita no pasa a activa); sin token de Mercado Pago, no decir «activada» (C2, C4, C8, D9 de la Dev 1) |
| ORG-1 | Dev 2 | Invitaciones que funcionan, tope de usuarios del plan, atadas al email (C7) |
| LEGAL-1 | Dev 2 | Términos y privacidad con el texto de Emi, y cómo pedir el borrado de datos (X5) |

**Cierre:** publicar; el pago chico de Emi recorre todo el ciclo (cierra G7).

### Fase 3 — Seguridad y datos, a fondo

| Pieza | Quién | Qué arregla |
|---|---|---|
| SESION-1 | Dev 1 | Cambiar o resetear la contraseña y cerrar sesión revocan de verdad; cambiar el email pide la contraseña (S3) |
| ABUSO-1 | Dev 1 | Leer un PDF en un proceso aparte, con tiempo y memoria máximos, que se pueda matar (D10 a de la Dev 1); límite de intentos con la IP real; topes en registro, recuperar usuario, telemetría y sugerencias de NCM; no revelar qué emails existen (S4, S5, S6, C9, X1) |
| AISLAMIENTO-2 | Dev 1 | La prueba de aislamiento ataca todas las funciones con datos de un estudio; la de admin también ve WebSockets y las rutas `/api/admin` y `/dev` exactas, y `roles` siempre es lista (revisión de ADMIN-2) |
| LIMPIEZA-1 | Dev 1 | Las 10 pruebas excluidas vuelven a la CI; se borra el camino viejo a Google Cloud; fuera las cadenas que pueden tener contraseñas (X2, X4) |
| DATOS-1 | Dev 2 | Borrar un cliente siempre funciona; la salud dice la verdad; los errores no muestran detalles internos (D2, D5, D6) |
| BACKUP-1 | Dev 2 | Copia de la base fuera de Railway, con una restauración probada (D1) |
| DISCO-1 | Dev 2 | El historial de NCM y los TXT pasan a la base (hoy se borran al publicar; si el servicio tuviera un volumen, los TXT viejos quedan donde `/download` ya no los busca) (D4) |
| AUDITORIA-FINAL | PM | Auditoría completa nueva (Opus alto y Sonnet alto) y una vuelta de arreglos |

**Cierre:** publicar y probar volver atrás (cierra G3 y G6). Recién ahí entra
el primer estudio.

### Fase 4 — Piloto y oleadas

Con el kit `wave1_*`. Los estudios más tolerantes, no los más grandes. Cierra
G8.

### Referencias

- Hallazgos (C, S, M, D, X): `AUDITORIA-2026-10-06.md`. Todos tienen pieza
  arriba, salvo: S1 (ya arreglada; llega con el ensayo), C10 (Emi mira las
  cuentas antes de cada publicación), X6 (correo, Emi en Railway) y la clave
  de Gemini (Emi la rota; sigue en la historia de Git, que no se reescribe).
- Se miró y está bien: orígenes permitidos, cookies y CSRF, cabeceras de
  seguridad, topes de subida de archivos.
- Fuera del plan: ordenar `HANDOFF.md`, partir `main.py`, VUCE-4, AFIP y VUCE
  reales (simulados por decisión).
