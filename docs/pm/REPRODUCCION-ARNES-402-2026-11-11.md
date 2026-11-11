# Reproducción: arnés de pantalla del 402 (Dev MARIA), 2026-11-11

Entregado en `899f9ee` (informe `94a765fc`). Base del informe `d49a436`;
mi base para los números, `f36cc83` (su merge de mi rama). Sólo pruebas.

## Resultado

**Aceptado.** Integrado con `merge` de `94a765fc` (no la cabeza de la rama:
`2e7c8807` es D149 y no está revisado).

## Lo corrido (checkout limpio en `899f9ee`, venv de la PM, pytest 9.2.0)

| qué | resultado |
|---|---|
| `chequeo-6.py f36cc83 899f9ee` | producto +0/−0, arnés +35/−10, historia vacía, avisos 0 (igual al informe) |
| `sabotajes/despacho1c.sh` | rc=0, 19 ROJO, ninguno sin rojo |
| `sabotajes/front422.sh` | rc=0, 17 ROJO, ninguno sin rojo |
| `pytest tests/test_despacho1c.py tests/test_front422.py` | `118 passed, 5 warnings` |
| `git diff HEAD 94a765fc -- proyecto_maria` | vacío |

Los dos sabotajes que pedí, por nombre, en rojo:

- `err.code === 'payment_required'` cambiado: «el plan vencido se avisa como
  una falla de red», dice `'detalle': 'Error de red`.
- `err.message` por `err.motivo` en el toast: «el plan vencido no dice el
  motivo del servidor», dice `'detalle': 'Plan vencido`.

Los dos de `app_v2.js` (el código y el mensaje que lanza el cliente) también
en rojo.

## Mis negativos

- La forma del 402 que el arnés espera es la del servidor:
  `_detalle_402` en `main.py` devuelve `detail` como objeto con `message`,
  `code` y `billing_status`, y `app_v2.js` lee `detail.message`.
- En `app_v2.js`, `const lead = motivo.message ||` cambiado por
  `const lead = ` (el cliente ignora el texto del servidor):
  `4 failed, 81 passed` en `test_despacho1c.py` (los tres `-402` de la
  pantalla y uno más). Revertido; `git status` limpio.

## Supuestos de la Dev

1. `front422_pantalla.js` en modo `api` devuelve `{lanza: {code, message}}`
   si `CDI.api` lanza: aceptado; `front422.sh` y su pytest siguen verdes.
2. Los hallazgos de `/code-review` arreglados dentro de la pieza: aceptado.
3. `f2709a2` (patrones de `maria1b`, `entradas1`, `abuso1`,
   `catalogolargo1`) es ancestro de `899f9ee`, así que entra con este merge.
   Son sólo guiones de sabotaje; **no está aceptado**: se revisa con D149.

## Hallazgo para D149: patrones que dependen del id de pytest

Con pytest 9.2.0 (el que instala `requirements.txt`, `pytest>=9.1.0`) un
parámetro de texto largo ya no da su valor como id: da el nombre del
argumento y el índice. Probado con un archivo aislado: `"x" * 201` da
`[nombre1]` con 9.2.0 y `[xxxx…]` con 9.1.1; `"x" * 100` conserva el valor en
las dos. En la rama de MARIA, `disco1.sh` líneas 200 y 227 buscan
`[BBBB` (el caso de `"B" * 2001` de `test_disco1.py`): con 9.2.0 darían
ROJO? aunque el sabotaje rompa la prueba. No corrí `disco1.sh`.

## No corrido

Suite completa (sólo pruebas, y la de la Dev en `f36cc83` da
`6077 passed, 110 skipped`); `e2e_maria.sh`; adversarios (sin dinero,
sesión ni permisos: es arnés).
