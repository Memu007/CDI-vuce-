# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ORDEN-1b vuelta 2, entregada en `8b087fd` (informe en el commit de arriba)

**Resultado.** Cada condición del freno tiene su prueba, y cada prueba su
sabotaje, que da rojo. Las dos bajas de producto quedan resueltas: una se
arregló y la otra no tiene camino natural. En la vuelta aparecieron dos
defectos más de producto, y los dos quedaron arreglados (abajo).

Lo que decidís vos: **D50**. Nada se integra en esta vuelta.

## Decisiones

**D50. `pantalla_orden1.js:280` creció 103 líneas en su propio cuerpo.**
Es el cuerpo principal del arnés, que va de 1343 a 1520 líneas. Lo
nuevo son los casos z29 a z34, que siguen el mismo patrón que los que ya
estaban.

- **(a)** A la cola de limpieza: partir el arnés en un archivo por familia
  de casos.
- **(b)** Partirlo ahora, en esta vuelta.

**Recomiendo (a).** Partirlo toca los 76 sabotajes de `orden1.sh` y los 24
de `orden1b.sh`, que buscan sus patrones en ese archivo. Eso agranda la
vuelta sin cambiar qué se prueba.

## SHAs

| SHA | Qué |
|---|---|
| `f4b2bed` | fix: al volver del pago, la pestaña no toma los datos de otro usuario (la rama `else` de `loadCurrentUser`) |
| `400feb4` | test: una prueba con su sabotaje por condición del freno |
| `41e4c81` | fix: la pestaña tapada al abrir no toma los datos del otro usuario (H1 del adversario) |
| `2142f00` | test: z34 y la pestaña tapada al abrir |
| `c00e579` | fix: normalizar el usuario sin nombre (lo revirtió `02a2877`) |
| `2e8001a` | test: z34 retiene desde la segunda lectura y `contestadas` espera lo pedido mientras tanto |
| `02a2877` | fix: `confirmarSesion` vuelve a comparar el nombre tal como llega |
| `90e86bb` | test: z34 retiene sólo la lectura de después de cargar a A, y `contestadas` no pierde avisos |
| `8b087fd` | test: `orden1.sh` sigue al código de la vuelta, y k y z8 miran a nombre de quién se guardó antes de exigir el diálogo |

**producto +6/−11**, en `app_v2.js`, más 5 líneas en `CHANGELOG.md`. El
arnés suma +233/−10.

## Condición, caso y sabotaje

| Condición que pediste | Caso | El sabotaje dice (copiado de `orden1b`) |
|---|---|---|
| la comparación de cookie de `confirmarSesion` (respuesta vieja, cookie nueva) | z29 | «FALLA: la pestaña de A preguntó quién es, entró otro usuario antes de la respuesta y guardó un cliente y el cliente quedó en la cuenta de B» |
| la guarda `sesionAjena` (primera carga ajena, escritura después) | z30 | «FALLA: la pestaña de A quedó tapada al abrir y guardó un cliente y el cliente quedó en la cuenta de B» |
| PUT, DELETE y PATCH | z31 | «FALLA: entró otro usuario y la pestaña de A mandó PUT » y lo mismo con DELETE y PATCH, un sabotaje por método |
| Escape no cierra el diálogo | z32 | «FALLA: la pestaña tapada se destapa con Escape» |
| «Recargar» recarga | z32 | «FALLA: la pestaña tapada no recarga con «Recargar»» |
| «Comprobando la sesión…» se va al recuperar | z12 | «FALLA: A volvió a entrar (otra sesión) mientras la duplicada miraba si la original vive y, ya recuperada, sigue diciendo que comprueba la sesión» |
| baja: la rama `else` de `loadCurrentUser` | z34 | «FALLA: A volvió del pago con B adentro y la pestaña tomó los datos de B» |
| H1: la primera carga tapada | z30 | «FALLA: entró otro usuario antes de que la pestaña de A supiera quién es y la pestaña tomó los datos de B» |

En z31 el PUT, el DELETE y el PATCH los frena la pestaña antes de salir. Si
alguno llegara al servidor con la sesión de B, igual daría 403 por CSRF.
El caso mira que no salga.

**La baja del «Comprobando…» fijo con la sesión ya cerrada no se arregla.**
Lo reproduje forzando el estado, pero en uso normal no se llega. Vos lo
marcaste «forzado en E6, camino natural sólo por lectura»: el texto engaña,
pero no bloquea nada. Saqué el caso z33 que lo forzaba.

## Puertas sobre `8b087fd`

| Puerta | Resultado |
|---|---|
| suite completa | «4407 passed, 121 skipped, 3 xfailed in 621.88s (0:10:21)», 0 FAILED o ERROR, salida 0 |
| `orden1b.sh` | 24 ROJO, «sabotajes sin rojo: 0» |
| `orden1.sh` | 76 ROJO, «sabotajes sin rojo: 0» |
| chequeo-6 7ebfc50..8b087fd | entero abajo |
| `/security-review` (Sonnet) sobre 7ebfc50..90e86bb | «Sin hallazgos (ninguno con confianza >= 8/10)». No volví a correrlo sobre 8b087fd porque el producto no cambió desde 90e86bb |
| `/code-review high` | sobre tres deltas, en la tabla de hallazgos. Sobre 90e86bb..8b087fd (+8/−8, sólo pruebas) no lo corrí: lo revisé yo leyendo el diff |

```
chequeo-6 7ebfc50..8b087fd: avisos para mirar, no un veredicto
producto +6/−11
arnés +233/−10
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/static/v2/app_v2.js: 1204 → 1199
  AVISO creció una función de más de 150: proyecto_maria/static/v2/app_v2.js:7 <anónima> 1198 → 1193, 1 en su propio cuerpo (§6: lo nuevo va aparte)
  AVISO creció una función de más de 150: scripts/testing/pantalla_orden1.js:280 <anónima> 1343 → 1520, 103 en su propio cuerpo (§6: lo nuevo va aparte)
avisos: 2
```

- **`app_v2.js:7`:** es mío y no viene de un merge. Es el envoltorio de
  todo el archivo (la función que lo encierra entero) y bajó 5 líneas.
  La línea que cuenta es una condición que cambió dentro de
  `loadCurrentUser`; no agregué ninguna rama.
- **`pantalla_orden1.js:280`:** es mío. Lo decidís en D50.

## Hallazgos

| Quién, modelo y esfuerzo | Hallazgo | Qué pasó |
|---|---|---|
| `adversario-sonnet-alto` sobre 400feb4 | H1: la primera carga tapada toma los datos de B | reproducido y arreglado en `41e4c81`, con su sabotaje en z30 |
| ídem | H2: `sesionAntes !== sesionAlAbrir ||` es casi redundante | queda; ahora también es casi redundante `getCsrfToken() !== sesionAlAbrir`, porque `confirmarSesion` igual impide guardar. El sabotaje de z8 da rojo por la toma de dueño en el reintento |
| ídem | H3: la relectura después del pago se descarta si A vuelve a entrar | riesgo, abajo |
| `/code-review high` 400feb4..2142f00 | 1 CHANGELOG, 3 `contestadas`, 6 z34 a los 4 s | arreglados |
| ídem | 2 `continue()` con la cookie vieja | refutado |
| ídem | 4 el `|| ''` | lo moví y después lo revertí |
| ídem | 5 la relectura descartada | riesgo (es H3) |
| ídem | 7 duplicación | a la cola de limpieza |
| ídem | 8 `alTraer` | descartado |
| `/code-review high` 2142f00..2e8001a | a, g (con try/finally) | arreglados |
| ídem | b | confirmado con rojo y arreglado |
| ídem | c, d, e y f | se resuelven revirtiendo la normalización (`02a2877`) |
| `/code-review high` 2e8001a..90e86bb | 1 | no tiene camino de hoy y falla cerrado: no se toca |
| ídem | 2 y 4 | riesgos, abajo |
| ídem | 3 | descartado |

## Errores míos en esta vuelta

- **`orden1.sh` quedó atrás del código.** Sobre 90e86bb dio «sabotajes sin
  rojo: 6».
  - Cuatro sabotajes quedaron en ROTO porque su patrón ya no estaba:
    - «la pestaña no mira si la sesión cambió desde que abrió»;
    - «al abrir con otra sesión no se avisa»;
    - «el aviso de espera no se va cuando llega el usuario»;
    - «el reintento no corta con la sesión vencida».
  - z8 daba «FALLA: page.waitForFunction: Timeout 10000ms exceeded.». Lo
    causé yo al hacer que k y z8 esperaran el diálogo con una espera que
    tira excepción.
  - z12 daba «FALLA: la operación de la pestaña abierta no se guarda: []»,
    porque el sabotaje viejo rompía también la primera carga.
  - Lo arreglé en `8b087fd`. Antes de commitear corrí cada sabotaje nuevo
    sobre su caso: todos dieron su FALLA y k y z8 sin sabotear dieron OK.
- **`c00e579` normalizó el usuario sin nombre** y abrió cuatro hallazgos.
  Lo revertí en `02a2877`.
- **En `707bfba`, que nunca se subió, saqué el `|| ''` de `loadCurrentUser`.**
  Lo descarté: mi lectura del hallazgo estaba mal. No tiene camino de hoy
  y falla cerrado.
- **Puertas que maté** porque cambié el SHA mientras corrían: sobre 2142f00,
  2e8001a, la primera de 90e86bb y 707bfba. Sus exit 1 y 144 no son rojos.
  Otra vez una cadena `&&` … `&` mandó las puertas a c00e579; las maté y las
  relancé.
- **La primera corrida de `orden1` sobre 8b087fd se cortó** por el límite de
  30 minutos en segundo plano, con 73 de 76 en ROJO. La relancé entera con
  un límite más largo.

## Riesgos

- **H3, media.** La relectura después del pago se descarta si A vuelve a
  entrar mientras tanto. La pestaña no toma datos de nadie, pero A queda con
  los datos de antes del pago hasta recargar.
- **z34 puede dar rojo falso, baja.** Pasa si la primera carga tarda más
  de 4 s. Es una prueba, no el producto.
- **`contestadas` espera 15 s, baja.** Pasa si `ruta.fetch` falla. Es la
  prueba, que tarda más; no da verde de más.
- **Telemetría v2 con `CSRF_ENFORCE=true`.** Es la de tu devolución, la
  dejé como estaba.

## Comandos para reproducir

```bash
git fetch origin claude/dev-tecnica && git checkout 8b087fd
# 1. Sabotajes de la pieza: tienen que dar «sabotajes sin rojo: 0» los dos
PY=python bash scripts/testing/sabotajes/orden1b.sh 8b087fd | tail -1
PY=python bash scripts/testing/sabotajes/orden1.sh 8b087fd | tail -1
# 2. Números de §6: los mismos 2 AVISOS de arriba
python docs/pm/herramientas/chequeo-6.py 7ebfc50 8b087fd
# 3. Historia: vacío
git diff 7ebfc50 8b087fd -- proyecto_maria/ | grep '^+' | grep -E '[A-Z]{4,}(-[A-Z]{2,})*-[0-9]|caso [0-9]'
```

## Archivos de producto tocados

`proyecto_maria/static/v2/app_v2.js` y `CHANGELOG.md`.

/compact conservar: Dev 1, rama claude/dev-tecnica. ORDEN-1b vuelta 2
entregada en 8b087fd y en revisión de la PM, con D50 para decidir (arnés
a la cola de limpieza o partirlo ahora). Apenas entregué: COBRO-MP-1 vuelta
4 (toda cuenta con suscripción abierta tiene salida; caso con la familia
none/None/expired/desconocido, rojo en 9048b6a y sabotaje). Después CSRF-1,
CORTE-1, MP-2, MP-3, AIS2, LIM, BACKUP-1a y EXCEL-2c. Nada se publica sin
el «dale» de Emi; nunca main.
