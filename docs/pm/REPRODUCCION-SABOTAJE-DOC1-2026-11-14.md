# Vencido `sabotaje_doc1.py`: reproducción de la PM

Entrega `d4c6b73` (informe `f3a7d29`, canal `PARA-PM-2.md`). Base `a926930`. Sólo arnés:
`scripts/testing/sabotaje_doc1.py` +5/−4 y una línea menos en `sabotajes-conocidos.txt`.
«servidor» pasa a apagar `destinacion_del_txt` dentro de `_destinacion_o_400` (`main.py`);
«generador», a pasarle al generador la exportación que corresponde a la destinación, así el
control nunca salta. Un adversario revisó el SHA final. Veredicto: **aceptado sobre `d4c6b73`**.

## Corrido por la PM (2026-11-14, entre 09:46 y 09:55 UTC)

El guion mide el `HEAD` del árbol donde está: cada copia corrió desde `scripts/testing/` de
un worktree parado en `d4c6b73`. Se superpuso con la reproducción de valor1b y con `run6` y
`despacho1b`. Al terminar no quedó ningún worktree en `d4c6b73`.

| Qué | Resultado |
|---|---|
| `chequeo-6.py a926930 d4c6b730` | producto +0/−0, arnés +5/−4, historia vacía, `avisos: 0` |
| unión `d4c6b730..f3a7d29a` fuera de `docs/pm`, y en `docs/pm/herramientas` | vacía |
| copia del guion de `d4c6b730` | 3 `OK`, `rc=0` |
| guion de `a926930` sobre `d4c6b730` | `AssertionError: Patrón cambiado: servidor`, `rc=1` |
| copia con «generador» neutro, `destinacion_del_txt(tipo_destinacion, False)` (mío) | `AssertionError` con `5 passed`, `rc=1` |
| `test_doc1_documentos.py` sin cambio | `74 passed` |
| «servidor» a mano, el archivo entero | `38 failed, 36 passed`, todas `test_ec_directa_nunca_entra_a_importacion` |
| «generador» a mano, el archivo entero | `5 failed, 69 passed`, todas `test_generador_directo_rechaza_ec` |
| `anclas_perdidas` sobre `d4c6b730` | de una línea 2 (maria7, guardar2), de varias 0, otra cantidad 0 |
| `vencido` en `sabotajes-conocidos.txt` (contado a mano) | 2: maria7, guardar2 |

Mi negativo muestra que el guion no acepta una mutación que deja el control andando: el
caso queda verde y el guion corta.

Por qué falla cada mutación (riesgo 2 de la Dev, que el guion acepte cualquier aserción):
- «servidor»: la EC pasa el control y la respuesta trae el error siguiente («No hay productos
  para generar…») en vez del de exportación. Ningún 500.
- «generador»: `DID NOT RAISE ValueError` (3) y, con los EC disfrazados, el mensaje de
  formato en vez del de exportación (2).

En los dos la EC entra donde no debe: es la razón buscada.

## Decisiones

- Riesgos 1 a 4: aceptados. El 3 («servidor» apaga más que su prueba) lo cubre más fino
  `sabotajes/avisos2.sh`. La línea de cola de la Dev va a `COLA-LIMPIEZA.md`.
- Sin D nueva: la próxima sigue siendo D250.

## No corrido

- Suite entera y `e2e_maria.sh`: sin cambio de producto.
- Subagentes adversariales de la PM: arnés sin dinero, sesión ni datos.
- `test_avisos2` con «servidor» (los `26 failed` son de la Dev) y el `NameError` que midió la Dev.
