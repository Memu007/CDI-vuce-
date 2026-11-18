# PAISES-NOMBRES (D266): `fa89e917` (informe `bf787b2d`), 2026-11-18, PM

**Veredicto: aceptada, integrada** (merge de `bf787b2d` en la rama de PM). Base `e5476182`.
Revisión de datos (§3): adversario Sonnet alto, `e2e_maria.sh` en el SHA y en la unión.

## Diff

`chequeo-6.py e5476182 fa89e917`:
```
producto +248/−7
  AVISO producto suma 241 líneas netas: el informe dice por qué (§6: más de 20)
arnés +178/−7
historia (grep de §6, sin líneas movidas): vacío
  AVISO creció una función de más de 150: proyecto_maria/static/v2/paises_maria.js:2 <anónima> 54 → 287, 233 en su propio cuerpo (§6: lo nuevo va aparte)
avisos: 2
```
Igual que el informe. Los dos avisos son la misma cosa: `const NOMBRES`, 233 líneas de datos
generados de ISO 3166-1 dentro del envoltorio del módulo. Explicación suficiente: es una constante,
no una rama nueva. Fuera de los datos, el producto cambia 15 líneas (dos lectores leen la letra ancha
con una tabla y `_nombres_de_pais` suma NOMBRES debajo de los alias que ya existían).

## Lo que corrí (worktrees en el scratchpad de la PM, 22:20 a 22:35 UTC)

| Qué | SHA | Resultado |
|---|---|---|
| `test_paises_nombres.py`, `test_catalogo3.py`, `test_despacho1a/1b/1c.py` | `fa89e917` | «516 passed» (el aviso de cobertura es por correr una parte) |
| `sabotajes/paises_nombres.sh` | `fa89e917` | base «22 passed»; 9 sabotajes ROJO; «OK: todos los sabotajes en rojo», salida 0 |
| `e2e_maria.sh` | `fa89e917` | «E2E MARIA OK», salida 0 |
| `e2e_maria.sh` | unión `d5a6677f` + `fa89e917` | «E2E MARIA OK», salida 0 |
| sonda mía: 294 textos de nombres que se contienen (Niger/Nigeria, Guineas, Samoa, Irlandas, Congos, Virgin Islands, Jordan, Turkey, «310 TURKEY BREAST»…), despacho, factura y `codigo_de_pais` | base y `fa89e917` | 0 país→otro país; las diferencias son ninguno→país correcto, o país→ninguno con el código de otro país (criterio 1) |
| sonda mía: el aviso | `fa89e917` | `_renglon` con «143 SUDAFRICA» y «310 JORDAN» da origen None y «No reconocí el origen «…».»; «310 CHINA» da CN sin aviso |
| sonda mía: «MADE IN U.S.A.», «MADE IN E.E.U.U.», con y sin 212 | `fa89e917` | ninguno en los tres lectores; nunca India (D274) |
| los cinco pares de D273, nombre solo | base y `fa89e917` | «South Africa» None → 159, como ya daba «Sudáfrica»; «Netherlands Antilles» None → 241, como ya daba «Antillas Holandesas»; Aruba 242 y Hong Kong 341 igual |

Adversario Sonnet alto (sin red, `GEMINI_API_KEY` vacía), ~137 000 textos: los 1532 nombres de
NOMBRES, COUNTRIES, ALIASES y PAISES_INDEC en mayúsculas, sin acentos, cortados, con ruido, con
homoglifos, en letra ancha y con códigos al azar; ~400 textos de producto, ciudad y estado.
**0 país→otro país** en `codigo_de_pais`, `get_pais_codigo`, `origen_iso2`, `_origen_desde_factura`,
`origen_valido` y `clave_de_origen`. Ninguna de las 728 claves que ya existían cambió de código. La
pantalla (node) y el servidor coinciden en los 137 000. Contra `/usr/share/iso-codes`, ningún nombre
de ISO da un país distinto.

## Supuesto 4: el TXT ahora sale donde antes frenaba

La validación frenaba «Holland», «Republic of Finland», «Northern Ireland» o «Netherlands Antilles»;
ahora el TXT sale con 423, 411, 426 y 241. Es ninguno→país correcto, lo que permite el criterio 4.
Riesgo escrito, baja: el adversario marcó nombres que ISO asigna a un país y la tabla podría separar:
«Kingdom of the Netherlands» → 423 (podría ser Aruba o Curazao), «Kingdom of Denmark» → 409
(Groenlandia 666, Feroe), «Saint Helena, Ascension and Tristan da Cunha» → 694 (Ascensión 662 y
Tristán 697 tienen código), «República del Congo» → 108 (hay quien lo escribe por el democrático).

## No corrí

- La suite entera: el «6224 passed» es de MARIA, no mío.
- Regenerar NOMBRES con `generar_nombres_paises.py`: el venv de PM no tiene pycountry. Lo cubre el
  cotejo independiente del adversario contra `iso-codes`.
- `/security-review`: MARIA tampoco (sin `origin/HEAD`); no toca sesión, permisos ni dinero.

## Decisiones

- **D273 (a)**, decidido por la PM: código de un par y nombre del otro sigue dando ninguno, con
  aviso. Para (b) hace falta saber cuál código de cada par vale en la tabla oficial, y eso no sale
  del repo (lo de Países Bajos lo dijo Emi). Riesgo escrito.
- **D274 (a)**, decidido por la PM: «MADE IN U.S.A.» da ninguno, con y sin 212, nunca India. Pérdida
  con aviso, igual que en la base.
