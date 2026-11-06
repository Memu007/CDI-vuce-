# Reproducción de DESPACHO-1c, vuelta 2 — 2026-11-05

Entrega: rama `claude/dev-maria`, producto hasta `fbbb2ad`, informe `5ecc6ff`.
Base `03bdc9f`. Worktree de PM `/tmp/cdi-pm/wd1c2` en `fbbb2ad`.

**Veredicto: aceptada, sin integrar.** `HEAD..fbbb2ad` trae `ca87d82`
(RENDIMIENTO-1c v2, DESPACHO-1b v6, CATALOGO-LARGO-1), todavía en revisión:
se integra después de ese veredicto. Lo que encontró el adversario va a una
subpieza chica, DESPACHO-1d.

## Lo que corrí yo (salida exacta)

```
== test_despacho1c
======================== 39 passed, 5 warnings in 4.05s ========================
== chequeo6
chequeo-6 03bdc9f..fbbb2ad: avisos para mirar, no un veredicto
producto +45/−19
  AVISO producto suma 26 líneas netas: el informe dice por qué (§6: más de 20)
arnés +187/−21
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/static/v2/screens/finalize.js: 1400 → 1426
  AVISO creció una función de más de 150: proyecto_maria/static/v2/screens/finalize.js:9 <anónima> 1392 → 1418, 44 en su propio cuerpo (§6: lo nuevo va aparte)
  proyecto_maria/static/v2/screens/ncm.js: 2341 → 2341
avisos: 2
== despacho1c
salida 0
16
fallas: 0
```

- Primer AVISO: el informe dice por qué. Segundo: la función anónima es el
  IIFE de todo `finalize.js`; partirlo por pantalla va a la cola de limpieza.
- Ejemplos míos de la familia, distintos de los del informe (copia temporal
  del caso con 403, 503 y 422 en `/operaciones`): `12 passed`. En todos, lo
  último a la vista es el error.
- Arnés de pantalla, `confirmar-ncm`: con 500 sale el aviso «No se guardó en
  la memoria de productos»; con red caída y con 402, `toasts: []` (es D65).

## Lo que encontró el adversario (Sonnet alto)

Sin doble guardado. Lo que sigue va a DESPACHO-1d:

1. Reproducido. `finalize.js:755-759` guarda la operación recién cuando
   termina el aprendizaje del catálogo: si ese pedido no vuelve, la operación
   no se guarda y no hay aviso.
2. Reproducido. Red caída o 402 al confirmar NCM (`ncm.js:1844-1846`) o al
   aprender el catálogo no muestran nada (D65 de la Dev).
3. Por lectura. El cartel «Memoria activada: Guardamos este NCM…» dura 8 s y
   el aviso de falla 4 s: puede quedar a la vista después de la falla.
4. Reproducido. Crear A (falla), asignar B (falla), crear otra vez sin CUIT:
   crea un segundo cliente (`clientesCreados: 2`).
5. Avisos de 4 s sin marca fija; «Volvé a Listo y reintentá» confunde porque
   entrar a Listo regenera; `ERROR_AJENA` y `ERROR_SIN_SESION` salen como
   «Error de red». Va a la cola de limpieza.
6. Pruebas: 9 de 10 mutaciones dan rojo. Sacar `clienteCreadoAca = null` en
   `renderOrphanPanel` (`finalize.js:939`) no se nota.

## No corrido por mí

- La suite y la suite con el entorno de la CI sobre `fbbb2ad` (la Dev: 4835 y
  4825 passed). La corro al integrar, junto con `ca87d82`.
- Playwright sobre las pantallas: el arnés de la Dev ya da rojo con sus
  sabotajes y mis ejemplos de la familia pasan.
