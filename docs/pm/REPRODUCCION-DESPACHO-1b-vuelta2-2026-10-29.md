# Reproducción de DESPACHO-1b, tercera vuelta (2026-10-29)

Entrega de la Dev MARIA: informe en `PARA-PM-2.md` («DESPACHO-1b, vuelta 3:
entregada en `1f5480e`»). Producto `9aee77f` y `712778a`; pruebas `8d9fbc0`,
`fe6dfbc`, `c6ad2f4` y `1f5480e`. Base `f125939`. Es la vuelta de la
devolución sobre `09e16f3`.

## Lo que corrió la PM, sobre `1f5480e`

- `tests/test_despacho1a.py` y `tests/test_despacho1b.py`: 152 passed.
- `despacho1b.sh`: 67 ROJO, «sabotajes sin rojo: 0», salida 0 (igual que el
  informe).
- Tope de CPU del hijo, con un PDF armado por la PM (42 KB, 200 hojas que
  comparten un contenido de 4000 líneas), por `leer_despacho_aparte`:

  ```
  rc 0 wall 19.9 cpu_user 19.6 sys 0.1 maxrss_MB 64
  aviso: «leí hasta la hoja 70»
  ```

  El informe dice «el hijo corta a los 10 s de CPU». Es falso: el tope de
  `_hojas_del_pdf` cubre la extracción de hojas, no el parseo del texto
  (`leer_texto`) que corre después en el mismo hijo. Ese parseo sólo lo
  acotan el timeout de 120 s y el tope de 4 MB de texto. Es la causa de la
  vuelta anterior (topes de bytes, no de trabajo) que sigue en otra etapa.
- Negativos propios de la PM (21 casos): 20 passed, 1 failed:

  ```
  test_pm_ncm_con_guiones_de_learn_y_despacho_es_el_mismo  assert 2 == 1
  ```

  Un NCM con guiones que llega por `learn` y el mismo NCM por `guardar`
  quedan en dos filas.

## Adversario (Sonnet alto, contexto nuevo)

Lo marcado «PM» lo corrió la PM con las pruebas del adversario, sobre
SQLite, en una copia de `1f5480e`; lo demás es del adversario.

1. **Media, PM: la identidad nueva vale sólo para `guardar`.** `learn` y
   `/operaciones` siguen con la similitud sobre la descripción cortada.
   Dos productos con los mismos 275 caracteres iniciales (uno con 1 kg, otro
   con 500 kg): un `learn` del segundo con peso 500 cae en la fila del
   primero, que queda con 2 usos y peso 250,5; la fila del segundo no se
   mueve.
2. **Media, PM: el mismo producto en dos filas según cómo llegó.**

   | Caso | Resultado |
   |---|---|
   | NCM de 10 dígitos por `learn`, después `guardar` | 2 filas |
   | el orden inverso | 1 fila con 2 usos: depende del orden |
   | la misma descripción con acentos compuestos y descompuestos | 2 filas |
   | NCM con guiones (negativo de la PM) | 2 filas |
   | NCM en dígitos arábigos o de ancho completo | 200 y 3 filas, dos con un NCM que no existe; el PUT también los acepta |

3. **Media, PM, sólo SQLite: guardados simultáneos duplican.** Seis `POST`
   a la vez a `guardar` con el mismo renglón: seis 200 y seis filas
   iguales. Después cada guardado suma a una sola de las seis. Lo dispara el
   doble clic, el reintento o dos pestañas. Es buscar y después insertar,
   sin restricción de unicidad. En Postgres no corrió.
4. **Media-baja, PM: el tope de CPU no cubre el parseo** (arriba).
5. **Media-baja: las filas viejas pesan por `veces_usado`.** La migración
   deja `veces_*` en NULL sin relleno, y el promedio toma `veces_usado` como
   cuenta. Una fila vieja con muchos usos casi no se mueve con el valor
   nuevo. Además la migración imprime el error y sigue.
6. **Baja, PM: `learn` con un ítem que no es objeto** (`"x"`, `[1]`, `5`)
   levanta `AttributeError`: 500 en producción. Con `\ud800` en el NCM da
   200 con 0 aprendidos.
7. **Baja, PM: el PUT acepta lo que `guardar` rechaza.** Descripción vacía,
   descripción con NUL y 300 000 caracteres, peso `"1_000"`, NCM arábigo: 200.
   Editar una descripción para igualar otra del mismo NCM deja el mismo
   producto en dos filas.
8. **Baja, PM: el borde de 1e12.** Un peso por unidad de 999999800000,04 kg
   se acepta; uno de 1e12 justo da 200 sin aviso y se pierde. Dos reglas
   distintas para el mismo tope.
9. **Baja: carga sin tope.** `learn` con 100 ítems contra 5000 filas del
   mismo NCM tardó 19,3 s, sin tope de ítems.
10. Informativo: `/operaciones` con `\ud800` da 500 (fuera del diff); la
    consulta de la migración no filtra por esquema (sólo lectura); el
    candado por usuario es por proceso; `update_product_history` sólo lo
    llama una prueba.

Lo que aguanta, según el adversario: el candado por usuario tras timeout,
error al lanzar el hijo y cancelación; el tope de CPU entre hojas; el
`\ud800` en `guardar` y `learn` sin 500; la migración en SQLite es
idempotente.

Mutantes del adversario: 54 aplicados. Los vivos que cambian el
comportamiento: el tope en la fila nueva (`valor_para_promedio` quitado
guarda un infinito), el control de `\ud800` en NCM y origen del PUT, el borde
`>=` de 1e12, `_usos` con filas viejas, `casefold` y el colapso de espacios
en `_misma_descripcion`, los espacios en `ncm_sin_puntos`, la normalización
de la divisa, `salteadas = True` tras el corte de CPU, y la migración entera
(no tiene prueba).

## No corrido por la PM

La suite completa (MARIA informa 4138 passed, 336 skipped, 2 xfailed sobre
`c6ad2f4`), Postgres 16, el humo y el navegador. El adversario tampoco
corrió Postgres.

## Veredicto

Devolución sobre `1f5480e`. Los cinco puntos cambiaron el código y las
pruebas nuevas matan sus mutantes, pero dos causas siguen:

- la identidad del producto se aplica en una sola de las cuatro vías de
  escritura, y la normalización del NCM y de la descripción no es la misma
  en todas (1, 2 y negativo de la PM);
- el tope de trabajo del hijo cubre una etapa y no la otra (4).

Y aparece una nueva: la identidad no la sostiene la base, así que dos
guardados a la vez la rompen (3). El detalle está en `PARA-DEV-2.md`.
