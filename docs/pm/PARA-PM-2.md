# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## RENDIMIENTO-1d, devolución: **entregada** en `558c941` (2026-11-05)

| Punto | Resultado | Qué decidís |
|---|---|---|
| 1. Lo que saca el hijo vuelve entero | Arreglado en `_main` de `despacho_lector.py`: una mitad de par suelta vuelve como «�» y el resto del texto queda, en `texto` y en `leer`. Además, el hijo escribe en UTF-8 aunque herede un locale que no lo es: con Latin-1, «中» lo tiraba abajo igual que el surrogate | Nada |
| 2. Un caso distingue el tope de 64 K | `test_lo_que_vuelve_del_texto_tiene_tope`: vuelve exactamente 65 536 | Nada |
| 3. Dos del mismo usuario, en fila y a la vez | `test_dos_del_mismo_usuario_uno_tras_otro_y_a_la_vez`, en `validar` y `texto`: rojo sin `release()` y sin `del filas[clave]` | Nada |

**Nada para decidir.** Un aviso de numeración: **D67 quedó usada dos veces**. Una es «sin lugar al leer da 504» (contestaste (b), pieza aparte después de SESION-1). La otra es «el id de proveedor nunca pasa de 60», en DESPACHO-1d. Esa la contestaste en `PARA-DEV-2.md:125` y `:139`. No renumero nada. En el informe de DESPACHO-1d la cito como «D67 (id a 60)» y mi próxima D es D69.

**Ojo para publicar, sigue igual:** la rama tiene `e0b8626` (COBRO-CORTE-1, COBRO-MP-2, AISLAMIENTO-2, LIMPIEZA-1 y BACKUP-1a, sin aceptar). Ningún SHA mío sirve para publicar hasta que esas cinco estén ✅.

**Encima de `558c941`** sólo está el merge `2a87aca` de tu `343a1b5`: toca `docs/pm/` y nada más. Encima de los dos viene este informe.

**Archivo de producto que toqué:** `proyecto_maria/core/despacho_lector.py`, sólo `_main` (~808–814). **Producto +4/−1.**

### Una corrección mía

Al principio escribí el resultado del hijo con `sys.stdout.write`. Di por no reproducible el riesgo del locale porque con `LC_ALL=C` Python pasa a UTF-8. Estaba mal: el locale Latin-1 no estaba instalado en el contenedor, así que no lo probé de verdad. `/code-review` lo marcó. Generé `en_US.ISO-8859-1` con `localedef`, sólo en este contenedor descartable, y con ese locale «中» da `UnicodeEncodeError` y se pierde la lectura en los dos modos. El caso nuevo usa `PYTHONIOENCODING=latin-1`, que produce el mismo error sin depender de los locales instalados.

### SHAs (base `724484c`, tu merge sobre DESPACHO-1d)

| SHA | Qué |
|---|---|
| `55a64e3` | test: los tres casos. Sobre `aaed661` (rojo de `rojo_r1d_aaed661.log`): `FAILED ...test_lo_que_saca_el_hijo_vuelve_entero[D800-�]`, `FAILED ...[DCFF-�]`, `2 failed, 8 passed` |
| `333feb3` | fix: `_MEDIO_PAR.sub("�", …)` sobre toda la salida del hijo, y el CHANGELOG |
| `98b00fe` | test: sabotajes del tope de 64 K, las mitades de par y la fila |
| `3602191` | test: el hijo escribe UTF-8 aunque su salida no lo sea. Sobre `98b00fe`: `UnicodeEncodeError: 'latin-1' codec can't encode character '中'`, `FAILED ...[texto]`, `FAILED ...[leer]` |
| `9e8a6e4` | fix: el hijo escribe bytes UTF-8 (`sys.stdout.buffer.write`), y una línea en el CHANGELOG |
| `558c941` | test: sabotaje de la escritura en UTF-8 |

Por qué «�» y no sacar el carácter: la app ve que algo no se pudo leer, y `_CARACTER_ROTO` ya avisa en `leer` con la misma marca.

**El tope de 64 K y la fila ya pasaban en `aaed661`:** son casos nuevos sobre código que ya estaba. Su rojo es el sabotaje (abajo).

**En `leer`, la línea nueva no se distingue sola.** `leer` ya reemplazaba la mitad suelta por página (línea ~367, la que dispara el aviso de `_CARACTER_ROTO`, que sigue haciendo falta), y por eso el modo `leer` del caso 1 ya pasaba en `aaed661`. La línea nueva de `_main` cubre todo lo que sale del hijo; `texto` es el modo que la distingue.

### Comandos

```bash
git checkout 558c941
# «12 passed»
<entorno de la suite> python -m pytest -q --no-cov tests/test_rendimiento1d.py
# 12 ROJO y «fallas: 0»
PY=<venv>/bin/python scripts/testing/sabotajes/rendimiento1d.sh 558c941
# «producto +4/−1», historia vacía, «avisos: 0»
python docs/pm/herramientas/chequeo-6.py 724484c 558c941
```

### Puertas

| Puerta | Salida exacta |
|---|---|
| `pytest -q --no-cov --timeout=120` (suite completa, worktree limpio en `558c941`) | `4903 passed, 355 skipped, 3 xfailed, 102 warnings in 699.56s (0:11:39)`, `pytest 0` |
| `compileall -q proyecto_maria` | sin salida, `compileall 0` |
| `rendimiento1d.sh 558c941` | 12 ROJO, `fallas: 0` |

Los rojos de `rendimiento1d.sh`, copiados de la salida:

```
ROJO  | el texto del vendedor vuelve a sacarse en un hilo de la app: dice «la app creció»
ROJO  | el texto sin topes por flujo: dice «sacar el texto llegó a»
ROJO  | el texto sin tope de CPU: dice «DID NOT RAISE»
ROJO  | el proceso aparte no sabe sacar el texto: dice «'normal': [200, None]»
ROJO  | el texto ocupa los lugares de validar: dice «assert 503 == »
ROJO  | el texto vuelve a la app sin tope: dice «FAILED tests/test_rendimiento1d.py::test_lo_que_vuelve_del_texto_tiene_tope»
ROJO  | el tope del texto que vuelve no es de 64 K: dice «FAILED tests/test_rendimiento1d.py::test_lo_que_vuelve_del_texto_tiene_tope»
ROJO  | el hijo devuelve las mitades de par sueltas: dice «FAILED tests/test_rendimiento1d.py::test_lo_que_saca_el_hijo_vuelve_entero[DCFF»
ROJO  | el hijo escribe con la codificación del locale: dice «FAILED tests/test_rendimiento1d.py::test_el_hijo_escribe_utf8_aunque_su_salida_no_lo_sea[texto]»
ROJO  | el turno del usuario no se suelta: dice «FAILED tests/test_rendimiento1d.py::test_dos_del_mismo_usuario_uno_tras_otro_y_a_la_vez»
ROJO  | la fila del usuario no se borra: dice «FAILED tests/test_rendimiento1d.py::test_dos_del_mismo_usuario_uno_tras_otro_y_a_la_vez»
ROJO  | esperar lugar para leer un despacho se descuenta del tope: dice «AssertionError: venció leyendo»
fallas: 0
```

«El texto vuelve a la app sin tope» antes esperaba «la app creció»; ahora espera el caso del tope, que es el que lo distingue.

### Revisiones

`/code-review high` sobre `724484c..98b00fe`:

| # | Hallazgo | Qué hice |
|---|---|---|
| 1 | El hijo hereda el locale: si no es UTF-8, una letra fuera de él pierde la lectura | Confirmado y arreglado: rojo en `3602191`, arreglo en `9e8a6e4` |
| 2 | Un par válido armado con dos glifos distintos (uno da D83D, otro DE00) vuelve como «��» y no como el emoji | Riesgo bajo: hace falta un PDF armado así, y `leer` ya hacía lo mismo en la línea ~367 |
| 3 | Se reemplaza en dos lugares (~367 y `_main`) | A propósito: ~367 hace falta para el aviso, `_main` cubre todos los modos |
| 4 | El modo `leer` del caso 1 no distingue la línea nueva | Declarado arriba |
| 5 | El caso de la fila no mide que dos pedidos del mismo usuario vayan uno detrás del otro | Fuera de lo que pidió el punto 3. Lo distingue el sabotaje «sin fila por usuario» de `rendimiento1c.sh` |
| 6 | El sabotaje de `release()` se pone rojo sólo en el segundo pedido en fila, después de los 5 s de espera | Aceptable: el rojo es el correcto |

No volví a correr `/code-review` después de `9e8a6e4`: el arreglo son 2 líneas y es lo que marcó su hallazgo 1. Tampoco corrí un adversario en esta vuelta. La pieza no es de plata, sesión ni permisos, y el adversario de tu reproducción ya la había atacado.

### Chequeo §6, entero

`docs/pm/herramientas/chequeo-6.py 724484c 558c941`:

```
chequeo-6 724484c..558c94196199f9026ebb665c81b60b9cb33ca213: avisos para mirar, no un veredicto
producto +4/−1
arnés +81/−1
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/despacho_lector.py: 897 → 900
avisos: 0
```

### Riesgos

- Un par válido armado con dos glifos distintos vuelve como «��» (hallazgo 2).
- Sigue lo de la entrega anterior: sacar `clave=` en `main.py` no lo ve ningún caso, y las fallas del texto quedan sólo en `logging.debug`.

### Lo que no corrí

- `rendimiento1c.sh` y `rendimiento1.sh`: no cambié nada de lo que miran.
- Postgres, `smoke_friccion.sh` y `ataque_aislamiento.sh`: la pieza no toca base, sesión ni permisos.
- `/code-review` sobre `9e8a6e4..558c941`, y un adversario de esta vuelta.

### Para la cola de limpieza (lo pediste vos)

- `CLAUDE.md` §5 dice que la CI deselecciona tests, y `ci.yml:45` no deselecciona nada.
- `test_maria1b_devolucion.py` y `test_excel2.py:512` usan una ruta fija en `/tmp`: que pasen a `tmp_path`.
