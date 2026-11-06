# COBRO-CORTE-1 (vuelta 3): reproducción de la PM, 2026-11-06

Producto `8295bb5`, informe `f05cf98`, base `7eda007`. Rama `claude/dev-tecnica`.
Entorno: venv Python 3.12, Postgres 16 local descartable, SQLite para pytest,
Chromium. Sin red; adversarios con `GEMINI_API_KEY` vacía.

**Veredicto: devolución corta.** La causa 1 (cobrar sin entregar) queda
cerrada. La causa 2 (una respuesta tardía escribe en la carga siguiente) sigue
abierta en el aprendizaje del catálogo y en el cliente del guardado. La carga
nueva queda trabada en la pantalla real. Si `os.link` falla, regenerar da 500,
y en la base no pasaba.

## Lo que coincide con el informe

| Puerta | Resultado PM |
|---|---|
| `test_cobro_corte1.py` + `test_valor1c.py` en `8295bb5` | `126 passed` |
| lo mismo en la base | `9 failed, 87 passed` (distingue) |
| `cobro_corte1_postgres.py` | rc=0, `fallas: 0`, 18 OK |
| `chequeo-6.py 7eda007 8295bb5` | `producto +122/−60`, historia vacía, `avisos: 4`, los cuatro explicados en el informe |
| sabotajes | se anotan al terminar |
| suite completa | se anota al terminar |

## Adversarios (contexto nuevo, sin red)

**Opus alto, servidor.** No encontró doble cobro, generación gratis ni escape
del directorio, tampoco con regeneraciones concurrentes ni ids con NUL.
Hallazgos:

1. **Baja, nueva.** Si `os.link` falla (`main.py:5966`), cada regeneración
   da 500 (`[500, 500, 500]`); en la base, `[200, 200, 200]`. No cobra.
2. **Media, de antes.** Si el commit llega a la base y Python tira error, da
   500: se cobró, el archivo se borra y el reintento cobra otra vez. Es raro.
   Va a la cola.
3. **Razonado, no reproducido.** `delete_cliente` bloquea usuario y después
   organización; sacar a un miembro, al revés. Puede trabarse con 500, sin
   perder datos. Va a la cola.

**Sonnet alto, pantalla.** Sin doble cobro.

1. **Media, de antes, misma causa.** `saveCatalogLearn` toma el proveedor de
   `CDI.state` al volver. Reproducido por la PM en Chromium, con la respuesta
   de A demorada: `POST /api/catalog/proveedor_b_sa/productos` con «Lona de
   PVC gris de la carga A».
2. **Media, de antes.** Con A en vuelo, «Generar» de B queda deshabilitado y
   no se vuelve a pintar. Reproducido por la PM: `B validating con A
   pendiente: boton disabled = true / tras volver A: pantalla validating
   boton disabled = true pedidos 1 usadas 1`. El caso de la pieza usa
   `CDI.goTo('ready')`, así que no lo distingue.
3. **Baja.** v2 toma el cliente al volver y v1 al pedir.
4. **Razonado.** Si la respuesta se pierde, el reintento cobra otra vez. Es
   lo que pasa con cualquier cobro sin idempotencia del cliente; no se pide
   ahora.

## Pedido

Está en `PARA-DEV.md`, «Veredicto de COBRO-CORTE-1, vuelta 3».
