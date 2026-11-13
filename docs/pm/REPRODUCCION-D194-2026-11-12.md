# D194 (MARIA): conteo de anclas perdidas, aceptada sobre `f507763`

2026-11-12, PM principal. Corrido en un worktree aparte, con la venv
`/tmp/cdi-pm/venv`, de 16:40 a 16:44 UTC.

## Lo reproducido

- **`anclas_perdidas.py` sobre `f507763`:** rc=0. Da 101 guiones, 2438
  anclas medidas y 11 llamadas sin medir. Hay **18 anclas de una línea
  perdidas, en 8 guiones**; además 10 de varias líneas, 2 de otra cantidad,
  5 no medidas y 6 sin ancla. Coincide con el informe.
- **Sobre `3ff4e77`:** 28 en 9 guiones, también como el informe.
- **`tests/test_anclas_perdidas.py`:** 27 passed.
- **`chequeo-6 a65403f f507763`:** producto +0/−0, arnés +869/−0, historia
  vacía, 0 avisos. La función más larga de la herramienta es `sentencias`,
  con 40 líneas, y el archivo tiene 749, dentro de los topes de §6.

## Mis negativos (otro borde que el de la Dev)

- **Saco un ancla que hoy está.** Agregué un espacio a
  `cantidad_est = kilos_al_centesimo(peso_neto)` en `maria_generator.py`,
  en un commit local descartable. Las anclas de una línea perdidas pasan de
  18 a 19, y `sabotaje_maria7.sh` gana la fila de su línea 93.
- **Repongo un ancla perdida y duplico otra.** Agregué como comentario el
  texto de `sabotaje_maria7.sh:97` y otra copia del de la línea 93.
  - Las perdidas de una línea bajan a 17, en 7 guiones. La línea 97 pasa a
    «está».
  - La 93 pasa a «otra cantidad (está 2)», junto con
    `sabotaje_maria7_devolucion.sh:80`, que usa la misma ancla.

La herramienta se mueve en los dos sentidos.

## Un guion corrido, para cotejar una fila con lo que pasa de verdad

`sabotaje_maria7.sh f507763`, una vez:
- 4 ROJO;
- después, `PATRON NO ENCONTRADO (0 veces) … 'sufijo_sbt = limpiar_sufijo(…)'`,
  que es justo la fila 97;
- rc=1.

Un ancla perdida frena el guion: no lo deja pasar en verde. Para los demás,
la función que reemplaza la leí en `maria7`, `valor1b` y `catalogo_largo2`,
y en todos corta igual. Los otros guiones no los corrí.

## `sabotaje_doc1.py`, que la herramienta no lee

Conté a mano sus dos anclas `…startswith("EC"):` sobre `f507763`: 0 en
`main.py` y 0 en `maria_generator.py`. Confirma lo que dice la Dev.

## D195: (a), decidido por la PM

Entre `origin/main` (`8b452071`) y `f507763` cambian `main.py`,
`maria_generator.py`, `static/v2`, `catalog_service.py` y `pdf_extractor.py`.
«Publicar» ya manda correr los guiones que tocan esos archivos en la
publicación pendiente, así que (b) sería (a) más tarde.

- Los 10 quedan anotados en `herramientas/sabotajes-conocidos.txt`, con
  dueña MARIA (son todos del recorrido MARIA y del catálogo) y salida
  «reescribirlo».
- Cada guion es una pieza de arnés. Cada pieza decide, ancla por ancla, si
  el sabotaje todavía tiene una protección que atacar; si no, ese sabotaje
  vuelve como D que propone retirarlo.

## Supuestos de la Dev

1. La herramienta y sus pruebas quedan en el repositorio: sí. Todavía no hay
   selector de la tanda; el formato con la ruta en el segundo campo lo
   decido yo, y queda así.
2. Las clases extra de la salida (varias líneas, otra cantidad, no medido,
   sin ancla): sí.
3. «Perdida» incluye un archivo que ya no existe: sí.

## No corrido

- Ningún otro guion de sabotaje.
- El rojo de las pruebas contra `6d39895` (14 failed).
- La comparación sobre 137 revisiones.
- La comparación byte por byte con `bash`.
- Un segundo `/code-review` sobre los arreglos.
- La suite completa, porque el producto no cambia.

## Escape

El escape de D191 (`sabotaje_maria9.sh`) era una familia: hoy son 10 guiones
vencidos, y las actas que los aceptaron no los corrieron enteros. Vale la
regla de «Publicar», y antes de publicar corre `anclas_perdidas.py` sobre el
SHA candidato.
