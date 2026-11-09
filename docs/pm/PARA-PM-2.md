# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CATALOGO-3: en curso; D155 (a) recibida, con la corrección de las 20:45 (2026-11-09)

Busqué quién compara el origen por igualdad o supone tres letras, como pediste.
Esto es lo que encontré:

| Lugar | Qué hace | Qué hago |
|---|---|---|
| `models.py:283`, `operation_items.origen` | `String(3)`: «TAIWAN» no entra en Postgres | D156 |
| `main.py:3773` (operación manual) y `:8177` (ítems de la factura) | recortan a 3 (`[:3]`) | sacar el recorte (depende de D156) |
| `pdf_extractor.py:573-575` | recorta a 3 letras | el criterio único (depende de D156 para llegar a la operación) |
| `maria_generator.py:1418` y `main.py:8290` (agrupar) | comparan el texto: «CHINA» y «CN» darían «orígenes distintos» | comparar el código MARIA |
| `main.py:9706` (`/api/ncm/calcular`) | recorta a 3 y pone «CN» si no viene | sólo lo anoto: no llega al TXT ni al catálogo |
| `maria_generator.py:129` y `:134` | «NL» dos veces (423 y 434); es el único conflicto de la tabla, medido con `ast` sobre las 446 claves | la prueba de la familia lo marca pendiente, como pediste |

Sigo con D76, D77, D78 y D84, que no dependen de esto.

### Decisiones

- **D156 — ancho de `operation_items.origen` (D155 a).** La columna es
  `String(3)`. Con «se guarda tal cual», un ítem con origen «TAIWAN» no entra
  en Postgres; por eso hoy se recorta y queda «TAI» → 310. Opciones:
  (a) ensanchar la columna a `Text`, con su migración en el arranque (Postgres
  descartable), y sacar los dos `[:3]`; (b) dejar la columna y, al entrar a la
  operación, guardar el código MARIA de tres dígitos («TAIWAN» → «313»), que
  `pais_reconocido` ya acepta. **Recomiendo (a):** es lo que dice D155 (a), y
  (b) cambia lo que ve el usuario en la pantalla de la operación. El
  `ALTER ... TYPE TEXT` en Postgres reescribe la tabla y la bloquea mientras
  dura; con el tamaño de hoy son segundos.
- **D157 — proveedor mixto, CJK y latín (D76).** «深圳某某有限公司 Co., Ltd»
  da el slug `co_ltd`, igual que casi cualquier proveedor chino con el sufijo
  en inglés: comparten catálogo. Opciones: (a) sumar al `vendor_id` el hash de
  las letras no latinas que se sacaron, como en D77; (b) dejarlo. **Recomiendo
  (a)**, y que se decida antes de que entregue: si entra después, los
  `vendor_id` se migran dos veces.

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
(/respondio). Pieza activa CATALOGO-3 (D76, D77, D78/D86, D80, D84). D155 (a)
recibida, con la corrección de las 20:45 (prueba sobre la familia de la tabla,
NL pendiente de Emi, buscar comparaciones por igualdad). D156 (ancho de
operation_items.origen) y D157 (proveedor mixto) pendientes de la PM; sigo con
D76, D77, D78 y D84. Después, PRESUPUESTO-CLIENTE-1. Próxima D libre: D158.
D151 sigue: no traer la rama de la PM con merge hasta que INTEGRAR-1 esté
aceptada. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin
secretos.
