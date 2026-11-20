# CATALOGO-PAIS-2 (D275 b): `9459a0d4` (informe `43f3aa29`), 2026-11-20, PM

**Veredicto: aceptada, integrada** (merge de `43f3aa29` en la rama de PM). Base `5e17da02`.
`git diff --stat 9459a0d4 43f3aa29 -- . ':!docs/pm'` da vacío: el informe no cambia nada más.
Sólo cambia `static/v2` (tres archivos) y el arnés: el servidor, lo guardado y el TXT no cambian.

## Diff

`chequeo-6.py 5e17da02 9459a0d4`: «producto +16/−3», «arnés +46/−8», historia vacía, un AVISO:
`paises_maria.js:2 <anónima> 286 → 293`. Es el envoltorio del módulo, el mismo aceptado en
PAISES-NOMBRES y ORIGEN-ETIQUETA; `alPasarElMouse` es una función aparte de 5 líneas. Explicación
suficiente.

## Lo que corrí (worktree `/tmp/cdi-pm/wt-cp2` en `9459a0d4`, 14:49 a 15:32 UTC)

Todos los guiones, con la copia de `9459a0d4`.

| Qué | SHA | Resultado |
|---|---|---|
| `sabotajes/holanda423.sh` | `9459a0d4` | base «113 passed» y «OK: pantalla Holanda→423»; 34 ROJO, 0 ROTO; «sabotajes sin rojo: 0», salida 0 |
| dos negativos míos sobre `paises_maria.js` (mismo arnés) | `9459a0d4` | `'input'`→`'keyup'` y `title` con lo que vino del servidor: los dos «FALLA: catálogo del»; «sabotajes sin rojo: 0» |
| `sabotajes/catalogo_largo2.sh` con `con_pg16.sh` | `9459a0d4` | 39 ROJO, «fallas: 0», salida 0; «el arranque traba las tablas en una transacción» y «el arranque no pasa el origen de los ítems a text» dan ROJO |
| `anclas_perdidas.py` | `43f3aa29` | no nombra `catalogo_largo2.sh` ni `holanda423.sh`; queda `limpieza1.sh:135`, de la Dev técnica (ya en la base) |
| `e2e_maria.sh` | `9459a0d4` | «E2E MARIA OK», salida 0 |
| `e2e_maria.sh` | unión con la rama de PM (`62690c58`) | «E2E MARIA OK», salida 0 |

Leído: el `input` que `clientes.js` manda después de guardar sólo lo escucha `mostrar` de
`paises_maria.js`. El guardado escucha `change`, que un `input` no dispara, y las máscaras de
`app_v2.js` (fecha, NCM) no se enganchan a este campo. No hay segundo pedido ni otro valor. Por eso
no hizo falta un adversario de la PM: sólo cambia `static/v2`, sin datos ni dinero.

No corrí la suite ni `catalogo3.sh`: la entrega no toca el servidor ni `tests/`, como pide la tarea.

## Escape de revisión (decidido por la PM)

Mi primera corrida usó `holanda423.sh` y `_casos_y_pantalla.sh` de la rama de PM, no la copia de
`9459a0d4`. Dio dos ROTO falsos («el catálogo del cliente deja lo escrito», «… corta el origen en
3»): MARIA había reescrito esas anclas en `28d0476a`. La corté y la repetí desde un worktree en el
SHA, con los dos negativos míos y `catalogo_largo2.sh` también desde ahí. La regla ya existía («un
guion de sabotaje se corre con la copia del SHA que se revisa»); la falla fue mía, al armar la corrida.

## Decidido por la PM

- Supuesto 1 (el `title` está siempre, aunque la etiqueta entre), supuesto 2 (`aria-label="Origen"`
  en vez de `title="Origen"`) y supuesto 3 (la sugerencia del navegador simulada con
  `insertReplacementText`): aceptados.
- Riesgos 1 a 3 (táctil y teclado no ven el `title`; el lector de pantalla puede repetir el valor;
  el tooltip nativo no se vio en el navegador sin ventana): riesgo escrito, bajo. La tarea pide «al
  pasar el mouse».
- Vencido `catalogo_largo2.sh`: cerrado con `cbd7718c`; sale su línea de `sabotajes-conocidos.txt`.
- Próxima D de MARIA: D278.
