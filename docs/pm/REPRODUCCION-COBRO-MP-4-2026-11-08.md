# Reproducción de COBRO-MP-4 (con D124), 2026-11-08

Entrega de la Dev técnica: producto y pruebas en `0fb991c`, informe en
`bc5d6b4`, base `3be86b7`. Corrido por la PM desde un worktree de `0fb991c`,
con los guiones de la entrega, venv Python 3.12 con `xlwt 1.3.0`, sin red y
con `GEMINI_API_KEY` vacía.

## Resultado

**Aceptada sobre `0fb991c`, sin integrar.** Todo da igual que el informe.

| Qué | Salida |
|---|---|
| `chequeo-6.py 3be86b7 0fb991c` | `producto +14/−6`, `arnés +336/−8`, historia vacía, `avisos: 0` |
| `cobro_mp4_postgres.py` con `con_pg16.sh` | 8 `OK`, `fallas: 0`, vuelta atrás `drop column if exists` corrida, salida 0 |
| suites de cobro del informe + `test_excel2d.py` + `test_excel3.py`, `-rs` | `1492 passed, 3 warnings in 270.13s`, ninguna línea `SKIPPED` |
| `sabotajes/cobro_mp4.sh 0fb991c` | `BASE  \| en verde`, 8 `ROJO`, `sabotajes con falla: 0`, salida 0 |

Diff de producto leído: la marca se escribe sólo dentro de `cancel_billing`,
después de pasar `_quien_toca_el_plan`; `con_sid` filtra sid vacío, así que
una marca `None` no coincide; reactivar llama sin `cancelar` y no usa la marca.
D124: `ci.yml` instala `xlwt==1.3.0` en un paso aparte (`162468e`). La CI de
GitHub no corrió sobre esta rama (no tiene PR): los `.xls` corriendo en la CI
quedan para la primera corrida; local, con la misma versión, sin saltos.

## Adversarios

**Opus alto** (pruebas propias en SQLite y Postgres 16 descartable): ningún
miembro sin la marca concilia; marcas `""`, `" "`, `"None"`, `"null"` dan 403;
no hay camino para que una cuenta existente cambie de estudio. Bajas:

1. Una marca de un 503 en el que MP no canceló sigue sirviendo si MP cancela
   meses después (nadie paga en ese momento; acceso hasta `trial_ends_at`).
2. Si el pedido muere con otra excepción después del PUT (no un 503), no
   queda marca y quien abrió recibe 403; la dueña destraba. Ya en el informe
   («Sin marca si se corta en el medio»).
3. Sacar a un miembro o un checkout no borran su marca; apunta a un sid que
   ya no existe. Ya en el informe.

**Sonnet alto** (12 mutaciones en una copia): 11 rojas por el caso esperado.
**Verde:** M12, el orden `(c is db_user, paga[c])`. Ningún caso tiene a quien
pide con suscripción propia que no paga mientras otra cuenta paga; ahí la que
paga se cancelaría antes de fallar la propia y el estudio seguiría `active`
sin nadie pagando. El producto de `0fb991c` lo hace bien (el adversario lo
mostró con un caso propio: con el código real da 503 y la que paga queda
`authorized`). Es un hueco de prueba, no de producto: va como primer paso de
PERMISOS-2 (caso + sabotaje del desempate).

## Riesgos que quedan

- La marca no vence (hallazgo 1 de Opus).
- Sin marca si se corta entre el PUT y el commit (hallazgo 2).
- La vuelta atrás es sintaxis de Postgres; en SQLite da error.
- La migración sigue sin `lock_timeout` y traga la excepción, como las demás
  columnas de esa lista (de antes).
