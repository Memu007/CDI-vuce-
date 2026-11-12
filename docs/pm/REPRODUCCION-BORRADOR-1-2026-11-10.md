# Reproducción de BORRADOR-1 (2026-11-10, PM principal)

Entrega `22163cec`, base `4555f7c4`, Dev técnica. Producto: sólo
`proyecto_maria/static/v2/app_v2.js` (+7/−9).

**Estado: aceptada sobre `c8733be`** (merge de mi rama en la de la Técnica,
con su informe en `52029147`). Producto igual a `22163cec`: las líneas de
`app_v2.js` que entran con el merge son las mismas de
`git diff 4555f7c4 22163cec`. Abajo, primero lo corrido sobre `c8733be`; después,
la clasificación del 10/11, que sigue igual.

## Sobre `c8733be` (2026-11-11/12, venv de la PM, pytest 9.2.0)

| Corrida | Resultado |
|---|---|
| `cliente1` | 34 ROJO, rc=0 |
| `destino1` | 19 ROJO, rc=0 |
| `despacho1a` | 14 ROJO, rc=0 |
| `orden1` | 76 ROJO, rc=0 |
| `foco_cliente1` | igual al informe, «mediciones con falla: 0», 1716 s |
| `sabotajes/estudio1b.sh` | 20 ROJO, rc=0 |
| `sabotajes/despacho1d.sh` | 9 ROJO, rc=0 |
| `sabotajes/estudio1.sh` | 36 ROJO y 1 ROJO?, rc=1 (abajo) |
| `sabotajes/borrador1.sh` | 5 ROJO, rc=0 |
| `sabotajes/cobro_mp1.sh` | 145 ROJO, 5 BASE en verde y 1 VERDE esperado por diseño; «sabotajes con falla: 0» |
| `ataque_aislamiento.sh`, puerto ocupado | rc=1, «❌ No levantó Postgres 16», «Address already in use» |
| `ataque_aislamiento.sh`, control | `Bloqueado: 47 · Fugas: 0 · Sin probar: 0`, PUERTA G3 PASADA |
| `scripts/testing/e2e_maria.sh` | `E2E MARIA OK` |
| `chequeo-6.py` | igual al informe |
| suite completa (pytest 9.2.0, sobre `c8733be`) | `6077 passed, 110 skipped, 3 xfailed, 105 warnings in 1434.22s`, igual a la referencia de `f45243a` |

Ningún arnés de navegación dio 429. La suite, después del resumen, imprimió
una vez «Task was destroyed but it is pending!» (un generador asíncrono al
cerrar) y salió con 0; no lo comparé con la corrida de referencia.

Portón: `git rev-list --no-merges 22163cec..c8733be --not origin/claude/practical-shannon-szpwkn -- proyecto_maria`
da 0 commits. `git show --remerge-diff` de cada merge de `22163cec..c8733be`,
limitado a `proyecto_maria`: 0 líneas, salvo `2b59f396`, que es el merge de
MARIA y ya es ancestro de mi rama. Con
`git show --remerge-diff --format= 2b59f396 -- proyecto_maria | wc -l` da 97,
igual al informe (yo había anotado 137 contando de otra forma).

Merge de prueba de `c8733be` sobre mi rama, en otro worktree: sin conflictos,
`git diff c8733be <merge> -- proyecto_maria` vacío, y
`tests/test_despacho1c.py tests/test_front422.py` (el arnés 402 de MARIA, que
`c8733be` no tiene): `118 passed`.

**El ROJO? de `estudio1`, con su causa atada.** El sabotaje «el nombre de más
de 200 entra» sí rompe la prueba: falla como
`test_el_alta_rechaza_un_nombre_vacio_o_que_no_sirve[nombre4]`. Con pytest
9.2.0 (el de `requirements.txt`) un parámetro de texto largo da id
`[nombre+índice]`, y `estudio1.sh` busca `[xxxxx`. Es el mismo hallazgo que
`disco1.sh` de MARIA (acta del arnés 402). El patrón ya estaba antes de D149:
`b7db6f65` no lo tocó. Con pytest 9.1.1 sobre las mismas dependencias,
`--collect-only` de `tests/test_estudio1.py` da ese caso como `[xxxxxxxx…]`,
que es lo que busca el guion. La Técnica informó 37 ROJO; después informó que su entorno tiene pytest
9.1.1 (ver «IDS-PYTEST»).

D149 (a) queda aceptada en lo que pedía; `estudio1.sh` entero queda abierto
hasta dar rc=0 con 9.2.0 (agregado en `PARA-DEV.md`), igual que `disco1.sh`.

**No corrido:** adversarios nuevos (es arnés, sin dinero, sesión ni
permisos); `estudio1.sh` saboteado con pytest 9.1.1 (sólo el `--collect-only`).

## Lo que corrió la PM

- `scripts/testing/sabotajes/borrador1.sh`: el producto da OK, los 5
  sabotajes dan ROJO como corresponde y `corridas que no dieron lo esperado: 0`.
  Es igual al informe.
- `docs/pm/herramientas/chequeo-6.py 4555f7c4 22163cec`:
  ```
  producto +7/−9
  arnés +183/−0
  historia (grep de §6, sin líneas movidas): vacío
  archivos de producto:
    proyecto_maria/static/v2/app_v2.js: 1201 → 1199
  avisos: 0
  ```
- **Negativo propio** (lo que el aviso le pide hacer a la usuaria, con la
  pestaña de antes cerrada normalmente):
  ```
  recargada, en clientes: {"pantalla":"clientes","fact":null,"guardado":[{"closed":true,"edad_s":2}],"aviso":"Quedó guardada la operación que tenías a"}
  otra pestaña: {"pantalla":"review","fact":"F-VIEJA-DRAFT","guardado":[{"closed":false,"edad_s":2}],"aviso":""}
  recarga de la primera: {"pantalla":"review","fact":"F-VIEJA-DRAFT","guardado":[{"closed":false,"edad_s":2}],"aviso":""}
  ```
  La pieza no la saca de Clientes. La operación se recupera en otra pestaña.

- **e2e de la CI** (`scripts/testing/e2e_maria.sh`) sobre `22163cec`
  (2026-11-10 14:17 UTC): falla sólo en `config/e2e_maria.js:279`, «no
  alimentó la memoria». Es la causa ya conocida de `e035fc98`, que esta
  pieza trae de la base. Con el parche de una línea en `client_memory.py:110`
  (sólo evidencia, revertido): `E2E MARIA OK`. La pieza no suma rojos en la
  e2e.

## Adversario de la PM (Opus alto, sin red, `GEMINI_API_KEY` vacía)

Comparó cada caso en las dos versiones: la pieza en el puerto 8890 y la base
`4555f7c4` en el 8891.

### Lo que introduce la pieza

**4. Baja. El aviso manda a otra pestaña que, durante 3 minutos, no la encuentra.**

Pasa si la pestaña de antes murió sin `pagehide` (se colgó o el navegador la
descartó). El borrador queda con `closed:false` y reciente, y:

- otra pestaña lo saltea;
- recargar ésta tampoco lo encuentra.

Salida, con la muerte sin `pagehide` simulada:

| | Pieza | Base |
|---|---|---|
| La pestaña recargada | aviso en Clientes | recupera enseguida, pero la saca de Clientes |
| Otra pestaña | `upload`, `fact:null` | |
| Recargar la primera | `upload`, `fact:null` | |
| El borrador | sigue guardado | |

- **No se pierde:** se puede adoptar pasados 3 min (`BORRADOR_HUERFANO_MS`).
  Eso es lectura de código: **no corrido**.
- Con el cierre normal funciona: ver el negativo propio, arriba.
- Va en la respuesta a D170.

### Lo que ya pasaba en `4555f7c4`, igual en los dos SHAs

**1. Una subida en curso en la carga se mezcla con el borrador viejo, y el viejo se pierde.**

- Si llega el usuario mientras ella está en la carga, el arranque llama a
  `adoptarBorrador` sin mirar `subidaEnCurso` ni los ítems. Esas protecciones
  están sólo en `adoptarTarde`.
- Resultado: la factura nueva queda con el `operacionId` de la vieja, y el
  borrador viejo sale del localStorage.
- Si la subida falla, queda en review vacío.
- **La ventana real** es desde que abre la pestaña hasta que llega el usuario,
  con un tope de 4 s. El adversario retuvo el usuario sin tope. Después del
  tope entra `adoptarTarde`, que la protege. Es improbable, pero existe.
- **Plata: leído, no corrido.** Con el `operacionId` viejo, `_contar_maria`
  (`main.py:6321`) trata el TXT nuevo como regeneración de la operación vieja:
  - no lo cuenta, hasta 10 por período, y pisa el `generated_file` de la vieja;
  - es la misma franquicia que ya tiene regenerar una operación propia;
  - no cruza usuarios, porque usa `_operacion_del_usuario`.
- El `operacionId` lo inyectó el adversario. Un borrador real lo tiene si ya
  generó MARIA (`finalize.js:769`).

**2. Media. Con el tour forzado, el borrador se pierde.** Es D171 de la Dev,
reproducido por los dos adversarios. El tour llega a la carga después de
recuperar, y el guardado automático borra la clave.

**3. Baja. «Nueva operación» tocada antes de que llegue el usuario igual se
pisa.** Es la misma causa que el 1.

**Sin problemas:**

- No hay mezcla entre usuarios: buscar, adoptar y leer siguen exigiendo el usuario.
- El `return` nuevo no deja la pantalla en blanco.
- Pasar por Clientes y después por «Nueva operación»: la pieza conserva la
  operación y la base la perdía.
- Con dos pestañas no cambia nada.

## Clasificación

**1 a 3 no son una devolución de esta pieza.**

- Pasan igual en la base.
- D143 (a) era «no sacarla de Clientes».

**Una sola causa** junta 1, 3 y D171: recuperar no mira lo que ella ya está
haciendo en la carga (una subida, los ítems, el tour). Va a Emi como una pieza
nueva.

Esa pieza no choca con la prueba de esta. El caso «el tour la lleva a la
carga» y el sabotaje `tour_ocupa` no tienen subida ni ítems. Una protección
basada en `subidaEnCurso` y en los ítems (no en `pestanaTocada`) los deja
pasar.

## Las D

- **D170 (b), decidido por la PM.** Queda así: no se pierde nada.
  - Excepción: la del hallazgo 4. Si la pestaña de antes murió sin
    `pagehide`, ni otra pestaña ni recargar la encuentran durante 3 min.
  - Lo que pasa después de los 3 min es lectura de código, no corrido.
  - Va a la cola de limpieza junto con el aviso que no se borra.
- **D171:** pieza nueva para Emi, juntando los hallazgos 1 y 3. Recomiendo que sí.
- **D172:** a la cola de limpieza (`recuperar(b)`).
- **D173 (a):** ya decidida a las 13:48. La Técnica la hizo en `4e7da21f`.

## IDS-PYTEST, arnés `dd0eab7e` (padre `c57b645e`), 2026-11-12

**Aceptada sobre `dd0eab7e`** e integrada con el merge de la Técnica `8d61bb09`.

- El arreglo: `pytest.param("x" * 201, id="largo")` y `estudio1.sh` busca
  `[largo]`. El id ya no depende de la versión de pytest.
- `chequeo-6.py c57b645e dd0eab7e`: producto +0/−0, arnés +4/−2, historia
  vacío, avisos 0.
- `--collect-only` de `tests/` con 9.2.0 y con 9.1.1: los 7 ids que cambian y
  sus patrones coinciden con la tabla del informe. El barrido de los 237
  patrones de los guiones queda informado y no reproducido.
- `estudio1.sh` con 9.2.0, dos corridas sobre `dd0eab7e`:
  - primera: 36 ROJO, 1 ROJO?, rc=1;
  - segunda: 37 ROJO, `sabotajes sin rojo: 0`, rc=0.
- El 37 ROJO con 9.1.1 está informado; no lo corrí.

**El ROJO? de la primera corrida no es del arreglo: es una carrera de la
prueba.** Sabotaje «un alta o un borrado no refresca los avisos», falla «sin
perfil, el estudio no aparece en la lista».

- Causa: `profile.js`, `open()`, termina con
  `setTimeout(() => cuitInput && cuitInput.focus(), 150)` después de cargar
  perfil, facturación y estudio. `pantalla_estudio1.js` (paso 9, y el mismo
  patrón en el paso 2) abre el modal y llena enseguida `#pfEstudioNombre` y
  `#pfEstudioCuit`. Si el foco salta durante el `fill`, el CUIT cae en
  «Mi CUIT (despachante)», el del estudio queda vacío y el POST da 400.
- **Observado** en una copia instrumentada (registra los campos antes del
  clic de alta), 3 pantallas a la vez, 10 rondas: 29 bien, 1 mal. En la mala:
  `["Estudio Inventado Tres", "", "30222222229", "pfCuit"]` (nombre, CUIT del
  estudio, «Mi CUIT», elemento con foco) y POST `{"cuit":""}` → 400.
- Tandas anteriores, por familia (sin instrumentar el foco):
  - mismo estado observado: 2;
  - compatibles sólo por el mensaje «CUIT no válido»: 3;
  - sin clasificar: 2;
  - 500 del servidor con 8 pantallas a la vez: 2 (otra causa, carga).
  - Válidas con 8 a la vez: 16 (8 de la ronda 1 fueron ECONNREFUSED por
    servidor no listo y no cuentan).
- La corrida original queda «compatible, estado no capturado».
- No lo introduce `dd0eab7e`: la prueba y el frente no cambiaron desde
  `c8733be`. Se le pide a la Técnica arreglar la prueba (comportamiento y
  prueba, sin espera fija) en `PARA-DEV.md`.
- Observación de producto, leída y no corrida: con carga lenta, a quien ya
  escribe en otro campo el foco le salta a «Mi CUIT». Va a la cola de
  limpieza.

**No corrido:** adversarios (arnés, sin dinero, sesión ni permisos);
`estudio1.sh` con 9.1.1; el barrido de 237 patrones.
