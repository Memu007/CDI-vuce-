# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## EMAIL-1 (D45 (1)): **entregada sin cambio de producto**, pruebas en `40423be` (2026-11-08)

| SHA | qué |
|---|---|
| `dc2943d` | test: un email vacío no encuentra la cuenta sin email (la prueba de `_cuenta_por_email` que pediste) |
| `9c5f671` | test: dos sabotajes de `email1.sh` apuntan al código de hoy (estaban **ROTO**) |
| `40423be` | test: `scripts/testing/email1_minusculas_pg.py`, qué letras pasan a minúscula distinto en Python y en PG |
| este commit | docs: el informe |

**Producto +0/−0.** La premisa de D45 ya no se cumple:

1. **No hay tope por correo.** Los topes de recuperar son por IP
   (`recuperar:ip:`, `main.py:1850`) y por cuenta encontrada
   (`recuperar:cuenta:{user.username}`, `main.py:1859`, de ABUSO-2). La cuenta
   la encuentra la base con `lower()` de los dos lados (`_cuenta_por_email`,
   `main.py:1768`). Entonces dos textos que la base toma por el mismo email
   cuentan para la misma cuenta, sin importar cómo los baje Python.
2. **El rojo con «İ» en Postgres 16 ya existe.** Está en
   `scripts/testing/abuso2_postgres.py`, caso 1: cinco variantes con İ
   mandan 3 mails, no 5. Su sabotaje está en `abuso2.sh` y corre con
   `PG_URL`. Salida abajo.
3. **«Otra letra de la misma familia» no existe con la collation de la base
   ni con ICU.** Recorrí todo lo imprimible hasta U+2FFFF:
   ```
   PG 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) collation base: C.UTF-8
   default: 1 letras con minúscula distinta en Python; primeras: ['U+0130']
   und-x-icu: 0 letras con minúscula distinta en Python; primeras: []
   ucs_basic: 1407 letras con minúscula distinta en Python; primeras: ['U+00C0', 'U+00C1', 'U+00C2', 'U+00C3', 'U+00C4']
   ```
   No puedo darte el segundo rojo que pedís: no hay letra con la que
   hacerlo. Con `ucs_basic` sí hay muchas, pero ahí la base no baja las
   letras con tilde. Eso es la D131.
4. **La İ sólo puede estar en filas viejas.** Todo email nuevo pasa por
   `_email_valido` (`main.py:331`), que acepta sólo ASCII. Lo usan el perfil
   (2378), el registro (3391), el alta de estudio (10643) y la invitación
   (10799). La otra creación de cuentas (`main.py:1701`) son los usuarios
   demo, y no llevan email.

**La prueba de `_cuenta_por_email`.** Ya está en `dc2943d`. Con
`if not email:` cambiado a `if False:` da rojo: «un email vacío encuentra la
cuenta sin email», en recuperar usuario y en recuperar contraseña.

**Lo admito:** `email1.sh` estaba roto desde ENTRADAS-1. Dos patrones ya no
estaban en el código (la invitación con `func.lower` y el registro con
`.strip().lower()`) y el arnés se commiteó así. Lo arreglé en `9c5f671`.

## Decisiones

**D131. No sabemos qué collation tiene la base de producción.** Si fuera
`ucs_basic` (o `C`), `lower()` de la base no bajaría las mayúsculas con
tilde. Una fila vieja `ÁLVARO@x.com` no se encontraría con `álvaro@x.com`:
no se manda el mail de recuperar, aunque nunca se manda a otra cuenta.

- (a) Emi o la PM miran `select datcollate from pg_database where datname = current_database()`
  en producción. Es de sólo lectura, pero es producción, así que no lo corro
  yo. Recomiendo esta.
- (b) Dejarlo: los emails nuevos son ASCII y el riesgo queda en filas viejas
  con tilde.

**D132. Pedir el reset de contraseña tiene sólo tope por IP**
(`reset:{ip}`, 5 cada 15 minutos, `main.py:1783`). No tiene tope por
cuenta, como recuperar usuario. Quien cambia de IP puede llenarle el correo
de links a una cuenta. Cada link nuevo mata el anterior (RESET-1), así que
no abre la cuenta, pero molesta y sirve para phishing.

- (a) Pieza aparte: tope por cuenta como `recuperar:cuenta:`, con su rojo
  y su sabotaje. Recomiendo esta.
- (b) Dejarlo como está.

## Comandos

```bash
git checkout 40423be
# negativos de EMAIL-1: «sabotajes sin rojo: 0»
PY=python scripts/testing/sabotajes/email1.sh 40423be
# la İ en PG: «fallas: 0», y en el arnés el sabotaje de la İ en ROJO
python scripts/testing/abuso2_postgres.py postgresql://cdi@127.0.0.1:55432/postgres
PG_URL=postgresql://cdi@127.0.0.1:55432/postgres PY=python scripts/testing/sabotajes/abuso2.sh 40423be
# la familia: default 1 (U+0130), und-x-icu 0
python scripts/testing/email1_minusculas_pg.py postgresql://cdi@127.0.0.1:55432/postgres
python docs/pm/herramientas/chequeo-6.py 3af69c0 40423be
```

## Puertas

| qué | dónde | resultado |
|---|---|---|
| `email1.sh` | árbol de `f7d7eb7` con el script de `9c5f671` (lo único que agrega `40423be` es `email1_minusculas_pg.py`, que el arnés no usa); no se volvió a correr sobre `40423be` por el corte | 15 ROJO, «sabotajes sin rojo: 0», salida 0 |
| `abuso2_postgres.py` | PG 16, árbol de `9c5f671` | 6 OK, «fallas: 0», salida 0 |
| `abuso2.sh` con `PG_URL` | `9c5f671` | 20 ROJO, «fallas: 0», salida 0; el de la İ: «ROJO  | Postgres: el tope de recuperar va por el texto en minúsculas de Python: dice «FALLA \| cinco variantes del mismo email mandan tres mails»» |
| `email1_minusculas_pg.py` | PG 16 | la tabla de arriba |
| suite completa | — | **no corrida**: el producto no cambia |
| `/code-review`, `/security-review`, adversario | — | **no corridos**: el diff es sólo de pruebas (+48/−6) |

Las últimas líneas de `email1.sh`:
```
ROJO  | el registro no pasa el email a minúsculas: «FAILED tests/test_email1.py::test_registro_con_invitacion_acepta_otras_mayusculas» 
ROJO  | la pista de dev vuelve con ENVIRONMENT que falta (RESET-2): «FAILED tests/test_email1.py::test_la_pista_de_dev_solo_en_el_entorno_de_prueba» 
ROJO  | un email vacío encuentra la cuenta sin email: «FAILED tests/test_email1.py::test_un_email_vacio_no_encuentra_la_cuenta_sin_email[/auth/recover-username-dev_username_hint]» «FAILED tests/test_email1.py::test_un_email_vacio_no_encuentra_la_cuenta_sin_email[/auth/request-password-reset-dev_token_hint]» 
sabotajes sin rojo: 0
```

## chequeo-6

```
chequeo-6 3af69c0..HEAD: avisos para mirar, no un veredicto
producto +0/−0
arnés +48/−6
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

- D131 y D132, arriba.
- Ya los marcaste vos y siguen abiertos: `user.name` va sin escapar en el
  HTML del mail de recuperar (`main.py:1824` y `1864`); el mail se manda en el
  mismo pedido.
- En el producto hay cuatro líneas con historia, «EMAIL-1», en `main.py`
  1754, 1771, 2373 y 3406. No son de este diff: van a la cola de limpieza.

## Archivos de producto

Ninguno.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (send_message next, «Dev MARIA: …»), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. EMAIL-1 entregada sin producto en 40423be (informe en este archivo); D129 (a) y D130 (a) decididas por la PM en 28a27a7; abiertas D131 y D132; la próxima D libre es la D133. Sigue AVISOS-2 (con las tres bajas), CONEXIONES-1, después OBSERVABILIDAD-1, ORG-1+D40 y D102. Nunca main, nada se publica sin el «dale» de Emi para el SHA, sin secretos, sólo datos inventados.
