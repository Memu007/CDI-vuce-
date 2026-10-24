# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CLIENTE-1 — alta de cliente con lo que pide el MARIA: entregada

**Resultado: terminada, para revisar.** Hecha según tu D2 = (a). En el alta
se ven arriba la razón social, el CUIT, el domicilio y el inicio de
actividad, marcados «lo pide el MARIA». El email y el teléfono quedan en
«Más datos». El cliente se guarda igual sin esos datos, con un aviso de
advertencia que dice cuáles faltan. Con los cuatro cargados no hay aviso. No
cambian la API, la importación de clientes ni el alta rápida desde la
revisión (`review.js` no se tocó).

| Qué | SHA |
|---|---|
| Base (merge de tu rama con D2) | `cb98105` |
| Producto | `fbc006a` + `12ff9b6` (lo que salió de la autorrevisión) |
| Pruebas: pantalla y sabotajes | `9c53522`, `b0c920b` |
| Informe | este commit |

Archivos de producto que toqué: `proyecto_maria/templates/dashboard_v2.html`
(formulario de cliente), `proyecto_maria/static/v2/screens/clientes.js`
(alta y detalle) y `proyecto_maria/static/v2/app_v2.js` (una línea: el
ícono de los avisos de advertencia, compartido).

### Decisiones

- **D1 (de EXCEL-3), sigue abierta.** Son el nombre y el signo de
  `operacion.descuento` para VALOR-1. El planteo está en el informe de
  EXCEL-3 (`8622aab`). Recomiendo (a): queda como está, positivo.
- **D3. ¿Arreglo que al editar un cliente se borre una fecha de inicio que
  no está en formato AAAA-MM-DD?** Esto ya pasaba antes de CLIENTE-1; ahora
  el campo está a la vista. Si un cliente tiene `fecha_inic_activ =
  '01/03/2015'` (la API acepta cualquier texto de hasta 10 caracteres), el
  campo de fecha del formulario lo muestra vacío. Al guardar cualquier
  cambio, se manda vacío y la fecha queda en NULL, sin aviso. La
  importación asistida normaliza a ISO, así que el caso entra por la API o
  por datos viejos. Opciones:
  (a) arreglarlo ahora en `clientes.js`: si la fecha guardada no es ISO y
  el campo queda vacío, no se manda (la fecha se conserva);
  (b) pieza aparte, que la API normalice o rechace las fechas que no son
  ISO;
  (c) dejarlo.
  **Recomiendo (a)**: son unas pocas líneas en el mismo archivo y evitan
  perder datos. (b) toca la API, que D2 dejó afuera.

### Qué cambió

1. **Formulario.** CUIT, domicilio e inicio de actividad van arriba con
   «· lo pide el MARIA»; la razón social, con «· requerido · lo pide el
   MARIA». Debajo, la frase «Se puede guardar sin estos datos; al guardar te
   avisamos cuáles faltan para el MARIA.TXT.». La fecha salió de «Más
   datos», que ya no se abre sola por tener fecha.
2. **Aviso al guardar.** Si falta el CUIT, el domicilio o el inicio de
   actividad, el aviso es de advertencia, con «!» y «Faltan para el MARIA:
   domicilio, inicio de actividad.». Si están los cuatro, el aviso es el
   verde de siempre. El CUIT se evalúa ya normalizado; el domicilio y la
   fecha, sin espacios.
3. **Detalle del cliente** (pestaña Datos): fila nueva «Inicio de actividad»
   en DD/MM/AAAA. Si está vacía, muestra «—». Una fecha guardada en otro
   formato se muestra tal cual.

### Puertas

| Puerta | Resultado |
|---|---|
| Rojo antes (prueba de pantalla sobre la base) | `FALLA: el rótulo de CUIT no dice «lo pide el MARIA»: CUIT` |
| Rojo antes de lo de la autorrevisión (sobre `9c53522`) | `FALLA: el aviso de advertencia tiene el ícono «i», no «!»`; con el ícono arreglado, `FALLA: una fecha guardada que no es AAAA-MM-DD se muestra como vacía` |
| `scripts/testing/pantalla_cliente1.js` sobre `b0c920b` | 4 líneas `OK` y `PANTALLA CLIENTE-1 OK` |
| Sabotajes `scripts/testing/sabotajes/cliente1.sh` sobre `b0c920b` | 14 `ROJO` por el motivo esperado, `sabotajes sin rojo: 0`, exit 0 |
| Suite completa, worktree limpio en `b0c920b`, `--no-cov --timeout=120` | `1757 passed, 102 skipped, 2 xfailed, 23 warnings in 162.46s (0:02:42)`, `FIN 0` |
| e2e de la CI (`scripts/testing/e2e_maria.sh`) sobre `b0c920b` | «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.», `FIN 0` |
| Suite y e2e sobre `9c53522` (antes de la autorrevisión) | `1757 passed, 102 skipped, 2 xfailed, 25 warnings in 165.03s`, «E2E MARIA OK», los dos exit 0 |
| `/code-review high` sobre `cb98105..9c53522` | 6 hallazgos: 3 arreglados; 2 en parte (el ícono sí, la duración del aviso no; el detalle sí, el borrado va a D3); 1 queda como riesgo (abajo) |
| Subagente adversario Sonnet alto | 5 hallazgos y XSS probado sin hallazgo: 1 arreglado (la prueba); 1 en parte (el detalle sí, el borrado va a D3); 3 quedan como riesgo (abajo) |
| `/security-review` | no lo corrí: la pieza no toca plata, sesión, permisos ni API; el texto nuevo va con `textContent` y `escapeHtml` (el subagente probó XSS en el nombre y en el aviso, sin ejecución) |

### Hallazgos de la autorrevisión

| Hallazgo | Quién (modelo, esfuerzo) | Qué pasó |
|---|---|---|
| La prueba aceptaba la fecha ISO cruda en el detalle: no veía si se formateaba | los dos | reproducido; ahora exige `01/03/2015`; sabotaje nuevo |
| La prueba leía el detalle en una pestaña oculta | `/code-review` | reproducido; ahora abre «Datos» y exige que se vea; sabotaje nuevo |
| El aviso de advertencia tenía el ícono «i» de información | `/code-review` | reproducido; ahora «!» (`app_v2.js`, igual que el diálogo de advertencia) |
| Una fecha que no es ISO se mostraba «—» en el detalle | los dos | reproducido; se muestra tal cual |
| Al editar, esa fecha se borra | los dos | ya pasaba antes de esta pieza; va a **D3** |
| La ruta de Chromium por defecto no existe en este entorno | los dos | cambiada a `/opt/pw-browsers/chromium` (`CHROMIUM` la pisa) |

### Riesgos que quedan (no arreglados)

- **El aviso dura 4 s y se pisa con el siguiente** (es el toast común). Es
  la única señal de qué falta; después, en el detalle sólo se ve «—». Baja.
  Alargar sólo este aviso implica cambiar el toast común; no lo hice.
- **Un CUIT de 11 dígitos con dígito verificador inválido** no se avisa:
  el alta valida sólo el largo y el aviso mira sólo si está vacío. Lo frena
  la generación del TXT (`controles_maria.cuit_valido`). Media-baja; se
  puede sumar «CUIT inválido» al aviso si querés.
- **La lista de lo que pide el MARIA está escrita a mano** en el alta, aparte
  de lo que exige la generación (MARIA-7). Si MARIA-7 cambia los
  obligatorios, el alta queda vieja. Baja; lo anoto para ESTUDIO-1.
- **En el alta rápida desde la revisión** el aviso puede decir «falta
  domicilio» aunque la carátula lo traiga: es cierto para la ficha, y
  después la operación lo copia (fill-if-empty). Baja; `review.js` quedó
  afuera por D2.
- Las otras pruebas de pantalla del repositorio tienen la ruta vieja de
  Chromium (`chromium-1194`); no las toqué.

### Supuestos reversibles

- La fila «Inicio de actividad» en el detalle del cliente no estaba pedida
  explícitamente: sin ella, el dato se carga y no se ve en ningún lado.
- El ícono «!» vale para todo aviso de advertencia; hoy hay uno más
  («Origen no reconocido», `ncm.js`).

### Comandos para reproducir

```sh
# desde un worktree en b0c920b levantado con docs/pm/herramientas/levantar.sh
BASE_URL=http://127.0.0.1:<puerto> CHROMIUM=/opt/pw-browsers/chromium \
  node scripts/testing/pantalla_cliente1.js          # 4 «OK» y «PANTALLA CLIENTE-1 OK»
PY=<venv>/bin/python CHROMIUM=/opt/pw-browsers/chromium \
  scripts/testing/sabotajes/cliente1.sh b0c920b      # 14 «ROJO», «sabotajes sin rojo: 0»
# rojo antes: la prueba sobre la base
git worktree add /tmp/c1-base cb98105                # levantarla y correr la prueba de arriba:
                                                     # «FALLA: el rótulo de CUIT no dice «lo pide el MARIA»»
```

Datos reales: no entró nada de la reunión del 24/10; los clientes de las
pruebas son inventados («Cliente Inventado Uno SA», CUIT 20-12345678-6).

**EXCEL-3** sigue esperando tu veredicto: el informe está en `8622aab` y
D1, arriba. **Sigo con PA-1.**

Última vuelta: 2026-10-24 19:32 UTC

/compact conservar: Soy la Dev técnica (Dev 1) de CDI, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica (nunca main), rutina trig_011UpBfwEu9TUzoNUrviqoP5 min 15; aviso a la PM principal session_01B7FVQspcEHF7PqNv797wNM con send_message priority next empezando «Dev técnica:». CLIENTE-1 entregada: producto fbc006a+12ff9b6, pruebas 9c53522+b0c920b, base cb98105; D3 abierta (¿arreglo que editar borre una fecha no ISO?). EXCEL-3 en revisión (informe 8622aab), D1 abierta. Sigo con PA-1 (sólo textos «NCM» → «Posición arancelaria (PA SIM)»); ESTUDIO-1 espera la coordinación de la PM con MARIA-7; GUARDAR-2 más adelante desde 2d930c5. Reglas de Emi: sólo me piden la PM o Emi; nada se publica sin su «dale» para el SHA; nunca main; sin secretos ni datos reales; subagentes hasta alto, sin Fable.
