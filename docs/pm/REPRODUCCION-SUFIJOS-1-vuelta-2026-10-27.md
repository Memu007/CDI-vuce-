# Reproducción de SUFIJOS-1, vuelta — 2026-10-27

Sobre `45a3ea1` (informe en la versión de `PARA-PM-2.md` de `76570de`;
producto de la vuelta en `252f04d`, diff de revisión desde `97cd2fa` sobre
`despachante.js` y `finalize.js`). Todo local, con sintéticos, sin Gemini.
La primera revisión está en `REPRODUCCION-SUFIJOS-1-2026-10-27.md`.

**Veredicto:** SUFIJOS-1 **sin hallazgos que frenen**; se acepta si la suite no trae rojos nuevos. Se cumple la regla de la familia:
al generar, lo que va al TXT por producto es lo que muestra su celda. La
PM la probó con fallas del arancel, códigos y casos distintos de los del
informe.

## Lo que corrió la PM

| Qué | Resultado |
|---|---|
| `scripts/testing/sabotaje_sufijos1.sh 45a3ea1 <venv>` | 47 de 47 en rojo por la razón esperada (rc=0) |
| Suite completa sobre `45a3ea1`, desde base limpia | corriendo al subir esto; el resultado va acá en la próxima vuelta |
| Negativos propios en Chromium, 390 px (abajo) | 9 de 9 OK |

## Negativos propios en Chromium

Con la app en `45a3ea1`, una cuenta nueva, dos productos sintéticos
(«Marca Uno», «Marca Dos»), `/generate_maria` interceptado para leer lo
que viaja, y esperas por condición (sin esperas fijas).

```
OK arancel 500: celdas ["",""] notas [NO_CONTESTO x2] viaja [[null,null],[null,null]]
OK arancel 200 {}: celdas ["",""] notas ["",""] viaja [[null,null],[null,null]]
OK arancel 200 items texto: celdas ["",""] notas ["La posición no está en el F: cargalo a mano." x2] viaja nulls
OK arancel 200 no JSON: NO_CONTESTO, viaja nulls
OK arancel 200 items de otro largo: celdas ["CA00-AA(Ajena)-",""] viaja [["CA00-AA(Ajena)-",null],[null,null]]
OK H5 con AI: celda AI(PROPIO 9)-CA00-AA(Marca Uno)-; nota «El arancel propone AI(X1); queda el de la operación: AI(PROPIO 9).»; viaja lo de la celda (unidad 01)
OK H2 con AB: nota «Lo escribiste con otro sufijo…»; viaja [["AB(Y)-AA(Marca Uno)-AI(X1)-","01"],["AB(X)-AA(MIA)-","01"]] = celdas
OK H2 sólo espacios no avisa
OK marca cambiada por fuera (artificial): viaja [[null,null],[...Marca Dos...]] celdas muestran la vieja
```

H1 se probó con otras cuatro formas de falla que la del informe (500, 200
con cuerpo vacío, con `items` que no es lista y no JSON), H2 con AB en vez
de CA, y H5 con AI en vez de AA.

## Observaciones (se anotan, no frenan)

- **Arancel con 200 y `{}`:** las celdas quedan sin nota ni aviso. No
  viaja nada, así que es coherente, pero la persona no sabe que el arancel
  no propuso. Va a la cola como mejora chica.
- **Una respuesta con menos productos que los pedidos** pinta la propuesta
  en el primero. Es un servidor roto a propósito; lo que viaja es lo que
  se ve.
- **Marca cambiada sin repintar** (último caso): la celda muestra la
  propuesta vieja y el producto viaja sin propuesta. Sólo se llega
  cambiando el estado a mano: la marca se edita en la pantalla anterior y
  esta pantalla se pinta al entrar. Erra hacia no mandar lo viejo.
- **El sabotaje 47** prueba un camino angosto (el pedido del cliente
  colgado y los productos cambiados sin repintar). Queda; su caso no
  molesta.
- **El rojo de `test_excel2`** (subida normal 400 a los 30 s detrás de
  ocho libros pesados) es de tiempo en este contenedor y no de esta pieza:
  el diff no toca Excel. Va con su diagnóstico a la cola de Excel.

## No corrió

- La comparación del TXT byte a byte sin sufijo propio: la corrió la Dev
  en siete casos; el generador no cambió en esta vuelta.
- Adversario con contexto nuevo: no hay cuota hasta el 28/10 18:00 UTC.

## Limpieza

Sin `uvicorn` ni `chromium` de la revisión andando al terminar.
