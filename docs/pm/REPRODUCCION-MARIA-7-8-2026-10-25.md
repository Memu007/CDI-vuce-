# Reproducción de MARIA-7 (devolución) y MARIA-8 — 2026-10-25

Entrega de la Dev MARIA: informe `f71eaa9`, producto probado `536c679` y
`30ceace` (sin diferencias de producto entre ellos ni con `f71eaa9`).
Revisor: adversario Sonnet, esfuerzo alto, en su propio worktree, con su API
en el puerto 8212 y un `.env` inventado. Todo con datos sintéticos.

**Veredicto: aceptada con nota.** No se encontró ningún camino que saque un
TXT con datos equivocados: lo nuevo frena en vez de generar. Integrada en
`1fa0b6e`. Lo que queda es la pieza MARIA-9 (`PARA-DEV-2.md`).

## Corrido, con su salida

| Qué | Sobre | Salida |
|---|---|---|
| Suite completa | `30ceace` | `2046 passed, 102 skipped, 2 xfailed, 23 warnings in 229.29s` |
| `-k maria` | `30ceace` | 1063 passed, 6 skipped |
| Sabotajes de la Dev | `536c679` / `30ceace` | 13/13, 38/38 y 25/25 en rojo |
| `smoke_friccion.sh` | API 8212 | `==> OK` |
| `e2e_maria.sh` | `30ceace` | `E2E MARIA OK: …` |
| `chequeo-previo.sh 30ceace 8212` | | todo OK |
| `test_excel2` (borde del tope) | `30ceace` | pasa en 23,4 s y 24,1 s (tope 30 s): el rojo de entorno de la Dev no reprodujo |
| Fuzz propio | `30ceace` | 5000 ítems (renglones unidos, flete, seguro): FOB, cantidad, estadística y kilo neto cierran exactos; ningún sub-ítem en 0,00 |
| Alcance | `536c679..f71eaa9` | `proyecto_maria` sin cambios; el producto de la Dev, sólo `maria_generator.py` y `main.py` |

Negativos propios, distintos de los de la devolución:
- **Sufijos:** `;`, espacio duro y salto de línea se separan bien. Dan error con el lugar:
  - `AA(ROJO)) -AB(AZUL)`;
  - `ÁA(ROJO)`;
  - `AA(ROJO)-CA00-AB`;
  - `CA0012-`;
  - 121 caracteres.
- **Kilos:** `0.004` y `0.001` dan error; `0.005` sale `0.010`.
- **Unidad del grupo:** `1`/`01`, `kg`/`KGS` y `m2`/`m²` cuentan como la misma; `pcs`/`kg` da error.
- **Cuentas:**
  - `ARABIC` y `VAT ARBANK` ya no cuentan como cuenta;
  - `ICBC_ACCOUNT`, `1_BANK` y `A/C NO 123` sí cuentan.

## Hallazgos (van a MARIA-9)

1. **Regresión:** un sufijo general en texto libre que no se usa (todos los
   sub-ítems o renglones con sufijo propio válido) da 400 en
   `/generate_maria`. En `284b029` generaba. `/avisos` no lo anticipa.
2. **Pantalla v2:** los errores nuevos de sufijo no van a su campo ni al
   sub-ítem (`static/v2/screens/finalize.js:401` y `:410`; verificado en el
   código por la PM). El TXT no sale mal.
3. **Pruebas que no distinguen:** las mutaciones del tope 121, `CA100-`,
   `A(X)-`, `;` y las unidades numéricas del aviso siguen en verde.
4. **Mensaje:** el error de kilos chicos nombra los dos renglones aunque
   sólo uno sea chico (`maria_generator.py` ~1304).

Riesgos, no defectos de la pieza:
- doble redondeo de kilos (`465.1249` sale `465.13`);
- `2.675` sale `2.67` solo y `2.68` como renglón unido (familia de Argon 9.2).

## D9–D11

- **D9 (a).** La herramienta de auditoría de la PM ya fallaba antes, en `284b029`, por el CUIT del despachante. Corregir su línea 27 no la revive (pide EC02). La arregla la PM.
- **D10 (a).** Riesgo anotado: los nombres pegados con menos de 16 dígitos (`CITIBANK 123456789`) pasan como IDTRIB.
- **D11 (b),** con la regresión del hallazgo 1. Va a MARIA-9, junto con el hallazgo 2.

## No corrido

- `ataque_aislamiento.sh`: no se tocaron datos, sesión ni permisos.
- La pantalla con los errores de sufijo en el navegador: el hallazgo 2 sale del código y del regex evaluado en node.
- Nada contra el MARIA o el Kit real.
