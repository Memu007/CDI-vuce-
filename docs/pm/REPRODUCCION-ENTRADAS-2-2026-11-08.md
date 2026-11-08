# Reproducción ENTRADAS-2 (Dev MARIA), 2026-11-08

Sobre `b8aa9bd` (rama `claude/dev-maria`), base de la pieza `3447b10`.
Veredicto: **aceptada, sin integrar** (la rama lleva debajo piezas en
devolución).

## Lo que corrí

| Qué | Resultado |
|---|---|
| `chequeo-6.py 3447b10 b8aa9bd` | `producto +115/−49`, arnés `+383/−5`, historia vacío, 1 AVISO (66 netas; el informe dice por qué y alcanza: seis entradas distintas que antes daban 500) — igual al informe |
| `tests/test_entradas2.py` (y vecinos que corre la Dev) | `36 passed` |
| `scripts/testing/entradas2_postgres.py` contra PG16 descartable | 33 OK, `fallas: 0`, salida 0 |
| `scripts/testing/sabotajes/entradas2.sh b8aa9bd` | `BASE | en verde`, 24 ROJO, `sabotajes con falla: 0`, salida 0 |
| Negativos míos (fuera del repo) | `21 passed` |

Negativos míos, de otro borde que los del informe: cantidad `"nan"`,
`"inf"` y `[1]` en la manual; guardar al cliente con `resumen.items` `1e999`,
`-Infinity` anidado, `"abc"`, `4294967296`, `valor_total` `"inf"`, cuerpo
vacío y una lista; clave de estudio `abcdefgh`, `abc` y `ñandúñandú` dan 400
y `abcdefg!` da 200; NUL en `/%00` y en `/static`; cliente con una lista en
vez de objeto da menos de 500.

**No corrí la suite completa.** Tomo las dos de la Dev (`5193 passed, 335
skipped, 3 xfailed`). Tampoco `smoke_friccion` ni `ataque_aislamiento` (la
Dev los declara no corridos).

## Adversario (Sonnet alto, contexto nuevo, sin red, Gemini vacía)

Nada nuevo introducido por la pieza. Anterior a la pieza:

- **Medio:** un número finito enorme (`1e308`) se guarda (dos guardados del
  cliente con `valor_total: 1e308`, o una manual con `cantidad: 1e308`);
  después `GET /api/clientes` y las métricas del cliente dan 500 en Postgres
  (`NumericValueOutOfRangeError` en la suma de `total_value`). Sólo la propia
  cuenta; se arregla borrando el cliente. Va a ENTRADAS-3.
- **Bajo:** 40000 ítems con NCM al guardar al cliente tardan 207 s (sin tope
  de ítems); el log de métricas falla con una ruta de 5000 caracteres; el 409
  del cliente siempre dice «email»; `"abc\n"` pasa la regex de usuario del
  alta de estudio.
- **Cambios visibles:** el texto de change-password («La contraseña…») y la
  clave de estudio de 8 letras sin número ni símbolo, ahora 400
  (`landing.html` sólo valida el largo). Sin mirar en navegador.
