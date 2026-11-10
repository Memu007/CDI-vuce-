# Reproducción de BORRADOR-1 (2026-11-10, PM principal)

Entrega `22163cec`, base `4555f7c4`, Dev técnica. Producto: sólo
`proyecto_maria/static/v2/app_v2.js` (+7/−9).

**Estado: clasificada; falta el veredicto.** Para aceptar faltan los arneses
de navegador que dieron 429 (`cliente1`, `foco_cliente1`, `destino1`,
`despacho1a` y `orden1`), que la Técnica vuelve a correr con D173 (a) en
`4e7da21f`. Antes de contarlos para este SHA hay que ver que
`git diff 22163cec 4e7da21f -- proyecto_maria` dé vacío.

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
