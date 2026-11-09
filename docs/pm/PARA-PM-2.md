# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CATALOGO-3: en curso, falta decidir D155 (2026-11-09)

Sigo con los puntos 1, 2, 3 y 5 mientras tanto. El punto 4 (D80) no se puede
hacer sin romper una prueba ya aceptada, cualquiera sea el criterio:

- `tests/test_catalogo_largo2.py:54-70` y `:118-119` piden que el catálogo y
  la memoria guarden «TAIWAN», «JAPON» y «ALEMANIA» enteros (y que «TAIWAN»
  dé 313, no el 310 de «TAI»).
- `tests/test_despacho1b.py:460` y `:2171-2177` piden que el despacho rechace
  «CHINA», «XYZ», «123», «ZZ», «ＢＲ» y «ÉS» con «usá el código de dos letras».

Hoy hay tres criterios: el despacho (`despacho_lector.py:841`) sólo acepta dos
letras reconocidas; el catálogo acepta nombres; el extractor
(`pdf_extractor.py:573-575`) recorta a 3 letras («TAIWAN» → «TAI» → 310). El
extractor ya tiene `_origen_desde_factura` (`pdf_extractor.py:2070`), que
convierte nombre, ISO3 o dos letras a ISO2, y la usa en otros cinco lugares.

### Decisiones

- **D155 — qué es un origen válido (D80).** Opciones:
  (a) todo lo que `pais_reconocido` reconoce, nombre o código, y se guarda tal
  cual. Cambia `test_despacho1b`: el despacho pasa a aceptar «CHINA» y el
  mensaje deja de decir «usá el código de dos letras»; siguen rechazados
  «XYZ», «ZZ», «123», «ＢＲ» y «ÉS».
  (b) sólo el ISO2: un nombre se convierte con `_origen_desde_factura` antes
  de guardar. Cambia `test_catalogo_largo2`: guarda «TW» y no «TAIWAN». Los
  cinco códigos MARIA sin ISO2 (143, 402, 403, 408, 423) no tienen dos letras
  que los representen y quedan sin origen.
  **Recomiendo (a):** no pierde información y no deja afuera esos cinco
  países. En los dos casos: el extractor deja de recortar a 3 y usa el mismo
  criterio, «XX» y vacío cuentan como «no vino», y el cambio en lo que sale en
  el TXT lleva su prueba y la corrida del golden. Anoto sin arreglar: la tabla
  da 434 para «NL» y «HOLANDA» pero 423 para «PAISES BAJOS».

## D102 (a), fijar la versión de `bcrypt`: **entregada** en `af924ea` (2026-11-09; el informe va en el commit siguiente), base `d39c1f6`

| SHA | Qué |
|---|---|
| `a7bc85a` | chore: `requirements.txt` fija `bcrypt==5.0.0`; CHANGELOG |
| `2a68280` | test: el login con una clave de 72 bytes y algo más da 401 |
| `af924ea` | test: esas mismas claves tampoco valen como clave actual en el cambio de clave (400) |

**Resultado:** `requirements.txt` sólo fijaba `passlib[bcrypt]`, que acepta
cualquier `bcrypt>=3.1`. Con una 4.x, `checkpw` compara sólo los primeros 72
bytes: una clave más larga que empieza igual que la verdadera entraba al login
y servía como «clave actual» para cambiarla. Con la 5.0.0 fijada, `checkpw`
lanza `ValueError`, `verify_password` (`main.py:3203-3213`) la atrapa y
devuelve `False`: falla cerrado, 401 en el login y 400 en el cambio. La clave
exacta de 72 bytes sigue entrando.

### Decisiones

- **D153 — `pwd_context` de passlib (`main.py:166`).** Es código muerto: no
  hay ningún `.verify` ni `.hash` en el repositorio. Con bcrypt 5, si alguien
  lo usara, passlib lanza `ValueError` al detectar el backend. Opciones:
  (a) pieza chica de limpieza que saca `pwd_context` y `passlib` de
  `requirements.txt`; (b) dejarlo. **Recomiendo (a)**, a la cola de limpieza:
  es una trampa para quien lo use creyendo que funciona.
- **D154 — tope propio de 72 bytes en `verify_password`.** Opciones:
  (a) dejarlo como está: el pin y la prueba nueva lo cubren; (b) agregar el
  tope en `verify_password`. **Recomiendo (a)**: con (b) la prueba deja de
  distinguir que alguien saque el pin (daría verde con bcrypt 4.x), y el
  `except` ya falla cerrado.

Supuesto reversible: ninguno; no agregué nada fuera del pin y su prueba.

**Archivos de producto tocados:** `requirements.txt` (+1) y `CHANGELOG.md`
(+4). `chequeo-6` dice `producto +0/−0` porque cuenta sólo `proyecto_maria/`;
`main.py` no cambió.

### Comandos copiables

```bash
pip show bcrypt | grep Version                                    # «Version: 5.0.0»
python -m pytest -q --no-cov tests/test_entradas1.py -k "72"      # 5 passed, salida 0
# rojo con una 4.3.0 instalada aparte (pip install --target <dir> bcrypt==4.3.0):
PYTHONPATH=<dir>:. python -m pytest -q --no-cov tests/test_entradas1.py -k "72"   # «assert 200 == 401», «1 failed, 4 passed, 75 deselected»
```

### Rojos con bcrypt 4.3.0, copiados de la salida

Login (`af924ea`; en `2a68280`, con su `-k`, daba el mismo `assert 200 == 401` con `1 failed, 79 deselected`):

```
E   AssertionError: ('login', 73, '{"message":"Login exitoso","access_token":"eyJ…",...}')
E   assert 200 == 401
1 failed, 4 passed, 75 deselected
```

Cambio de clave, con el tramo del login salteado (`af924ea`):

```
E   AssertionError: ('cambio', 73, '{"success":true,"message":"Contraseña actualizada","access_token":"eyJ…"}')
E   assert 200 == 400
1 failed, 4 passed, 75 deselected
```

### Puertas, sobre `af924ea`

| Puerta | Salida |
|---|---|
| pytest (entorno de `/entregar`) | `=== 5453 passed, 335 skipped, 3 xfailed, 107 warnings in 1065.78s (0:17:45) ====`, salida 0 (uno más que en D139: la prueba nueva) |
| `compileall -q proyecto_maria` | salida 0 |
| `smoke_friccion.sh` (uvicorn en 8097, SQLite propia) | `==> OK · telemetría y alias session/state rechazan sin sesión + by-cuit protegido`, salida 0 |
| `ataque_aislamiento.sh` | **no corrido**: la pieza sólo fija la dependencia del hashing; no cambia datos, sesión ni permisos de clientes o descargas, que es lo que cubre el script. Login y cambio de clave los cubre la prueba nueva. |
| grep de historia de §6 | vacío |

`chequeo-6.py d39c1f6 af924ea`, salida entera:

```
chequeo-6 d39c1f6..af924ea: avisos para mirar, no un veredicto
producto +0/−0
arnés +16/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

### Hallazgos de la autorrevisión

| Quién | Hallazgo | Qué hice |
|---|---|---|
| adversario Sonnet, alto | Baja: una cuenta cuyo hash se hizo con 4.x sobre una clave de más de 72 bytes ya no entra con la clave completa | Queda como riesgo (abajo) |
| adversario Sonnet, alto | Baja: `pwd_context` lanza `ValueError` con bcrypt 5 | Código muerto: D153 |
| adversario Sonnet, alto | Sin problema: registro, estudio, reset y cambio pasan por `ClaveNueva` (tope de 72 bytes); `pip check` limpio; los hashes 4.x verifican con 5; la prueba distingue el defecto | — |
| `/code-review high` | Faltaba el cambio de clave, que verifica la actual con la misma función | Arreglado en `af924ea`, con su rojo |
| `/code-review high` | Sacar passlib | D153 |
| `/code-review high` | `verify_password` sin chequeo de largo propio | D154 |
| `/code-review high` | Aserción unitaria del contrato de `verify_password` | Queda: el rojo con 4.x y el login exacto final ya lo muestran |
| `/code-review high` | Registro duplicado en la prueba | Queda: `_por_registro` no devuelve el usuario |
| `/code-review high` | `proyecto_maria/requirements.txt` sin el pin | No aplica: archivo viejo que no usa nada (Dockerfile y CI leen el de la raíz) |
| `/security-review` (Sonnet) | sin hallazgos de confianza ≥ 8. Planteó un 500 por `ValueError` en `hash_password` | No se alcanza: las cuatro entradas externas usan `ClaveNueva` (`main.py:353`, `1799`, `2498`, `10640`); la llamada de `1717` hashea claves de semilla fijas y cortas |

### Riesgos y lo que no se corrió

- Cuentas viejas: si en producción corrió alguna vez una 4.x y alguien
  registró una clave de más de 72 bytes antes de que existiera el tope de
  `ClaveNueva`, ya no entra con la clave completa; sí con sus primeros 72
  bytes o con un reset. No lo puedo medir sin mirar producción.
- La CI instala `requirements.txt` y corre `pytest --no-cov` entero
  (`ci.yml:31,45`), así que corre la prueba nueva con la 5.0.0; Railway no
  espera la CI. (`CLAUDE.md` §5 dice que la CI deselecciona tests de
  presupuestos: en el `ci.yml` actual no veo ningún `--deselect`.)
- `ataque_aislamiento.sh`: no corrido, por la razón de la tabla.
- Siguen en la raíz del contenedor de D139 los dos archivos sueltos
  (`/panel-sab-55f282c.txt`, `/suite-55f282c.txt`); no están en el repositorio.

### Sigue

Nada asignado después de D102: espero tu próxima tarea.

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi,
rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama
claude/practical-shannon-szpwkn), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP
(/respondio). Pieza activa CATALOGO-3 (D76, D77, D78/D86, D80, D84); D155
(criterio de origen) pendiente de la PM; sigo con 1, 2, 3 y 5. Después,
PRESUPUESTO-CLIENTE-1. Próxima D libre: D156. D151 sigue: no traer la rama de
la PM con merge hasta que INTEGRAR-1 esté aceptada. Nada se publica sin el
«dale» de Emi para el SHA; nunca main; sin secretos.
