# Reproducción de ORG-1 (2026-10-28)

Entrega de la Dev MARIA: ORG-1, ORG-1b y DESPACHO-1a en `4ce6d22`.
Integrada en la rama de la PM con el merge `cda3320`.

## Suite y sabotajes

- Suite de la PM sobre `4ce6d22`, copia limpia, SQLite: `2 failed, 3902
  passed`. Los dos rojos son de tiempos bajo carga (`test_excel2`,
  `test_excel1_lectura`), los mismos de bases anteriores; no son de esta
  pieza.
- `sabotaje_org1.sh`: 9 de 9 sabotajes en rojo.
- `despacho1a.sh` y `org1b.sh` sobre `4ce6d22`, de a uno desde la raíz (los
  dos usan el puerto 8852): `sabotajes sin rojo: 0`, `rc=0` cada uno. Una
  primera corrida en paralelo chocó en el puerto; no cuenta.

## Adversarios (Opus alto y Sonnet alto, contexto nuevo)

Los guardas del producto están bien: no se encontró entrada a otro estudio
ni un invitado que pase el tope del plan. Lo que encontraron, y lo que la
PM reprodujo:

1. **Reingreso del sacado** (Opus, Postgres 16): con dos invitaciones al
   mismo email, el sacado cambia su email y entra con la segunda (`200`).
   Lo cierra la regla 2 de la D40.
2. **Email que el registro rechaza** se puede invitar y ocupa lugar.
3. **Email largo, reproducido por la PM en Postgres 16:** 101 caracteres dan
   `500` (`Invitation.email` es `String(100)`); 100 dan `200`.
4. **Guardas sin prueba.** Mutantes del revisor que dejan
   `test_org1.py` + `test_despacho1a.py` en `59 passed`. Reproducidos por la
   PM: sin el filtro por estudio de `/mine`, sin el 403 al que no es dueño
   al invitar, y borrar un miembro de otro estudio. Dos mutantes del revisor
   (`rm_sin_403`, `rm_sin_guarda_duenio`) daban `IndentationError`: no
   valen y no se citan.

## Veredicto

Aceptada sobre `4ce6d22`. Los puntos 1 a 4 van a los commits de la D40,
encima de la cadena, antes de publicar (`PARA-DEV-2.md`).
