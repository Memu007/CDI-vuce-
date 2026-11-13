# Reproducción de EXCEL2D-TIEMPO (2026-11-13)

Entrega de la Técnica: prueba `181e0dfc`, informe `5e2c7b5c`, base `205b7457`.
Sólo pruebas (producto +0/−0): `test_la_subida_cara_no_frena_a_nadie` mide
CPU del proceso (`time.process_time()`) en vez de reloj. Revisado por la PM
principal en worktrees en el SHA entregado y en la base, con el `excel2d.sh`
de la entrega. Veredicto: **aceptada e integrada**.

| qué | salida |
|---|---|
| `chequeo-6.py 205b7457 181e0dfc` | producto +0/−0, sólo pruebas, historia vacía, 0 AVISO: igual que el informe |
| `excel2d.sh` sobre `181e0dfc` | 20 `ROJO`, 0 sin rojo |
| `excel2d.sh` sobre la base | el sabotaje de atributos da `VERDE`: la base no lo veía |
| negativo de la PM, GIL retenido (`re.match(r"(a+)+$", "a"*26+"b")` después de `validar_con_carril` en `upload_excel_v2`) | rojo en los dos SHA: distinto del sabotaje de formatos de la Dev |
| negativo de la PM, espera sin CPU (`time.sleep(4)` en el mismo lugar) | base rojo, `181e0dfc` **verde**: es D214 |
| 4 procesos ocupados, archivo entero, tres veces | `26 passed` las tres |
| 8 ocupados en 4 núcleos, `-k no_frena`, dos veces por SHA | base y entrega `7 passed`: el 0,506 / 0,66 s de la CI **no se reprodujo** acá |
| **lo que distingue el cambio:** un núcleo (`taskset -c 0`) con 8 ocupados, `-k no_frena`, dos veces por SHA (06:24–06:27 UTC) | base `4 failed, 3 passed` las dos (reloj 4,8 y 8,0 s contra 3; pasos 2,1 y 2,0 s contra 1); `181e0dfc` `7 passed` las dos |
| reloj de la entrega en ese caso de hambre (`--durations`) | 7,20 s (9995), 4,86 (2499), 4,52 (300 000), 3,47 (200 000), 2,56 (640 000) |

`ci.yml:49` corre `pytest --no-cov`; `pytest.ini` suma `--cov` en local. Con
cobertura, «2499» gasta 1,16–1,22 s de CPU contra el tope 1,5 (D215).

**D214 (a), decidido por la PM, como pieza siguiente.** Medir CPU deja de ver
una espera sin CPU en la subida (sleep, candado, timeout): hoy ningún camino
la trae, así que no es devolución. Un tope de reloj generoso la vuelve a ver;
tiene que quedar por encima de los 7,2 s del caso de hambre de arriba.

**D215 (a), decidido por la PM.** Queda 1,5; el margen con cobertura va a
`COLA-LIMPIEZA.md`. La única medición en otra máquina será la CI de la PR
sobre la rama integrada: un rojo de esta prueba ahí es de la pieza, no ruido.

Mis cargas de 06:20–06:22 y 06:24–06:29 cayeron mientras corría
`catalogo3.sh` de MARIA (acta de D223+D224).

**Medida en otra máquina (agregado 13/11).** La CI de la PR sobre `927d35fe`,
que trae esta pieza, dio verde: «Suite completa» 18:01, a 1:22 del tope de
20 min (`ci.yml:15`).

No corrido: pytest entero y adversarios (sólo pruebas).
