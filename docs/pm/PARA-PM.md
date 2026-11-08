# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## COBRO-MP-2+3, devolución de pruebas, entregada en `71e15df` (informe en el commit de arriba)

Base de la devolución: `cb740f3` (tu veredicto). Base de esta vuelta: `64770b9` (merge de tu rama antes de empezar).

### Resultado

Los cinco mutantes que dejaste verdes ahora dan rojo, y cada punto de la devolución tiene su caso y su sabotaje:

1. **Firma:** con clave vacía y sin secreto, con los 8 primeros caracteres reales, con el último cambiado, más corta y más larga, el aviso da 401 y no se consulta a Mercado Pago (`LLAMADAS == []`). El estado de la cuenta queda igual.
2. **Quién toca a quién:** si la dueña de otro estudio intenta sacar a un miembro, da 404; el miembro sigue en su estudio y su suscripción en Mercado Pago no cambia. Quien abrió la que paga puede reactivar con el sid anotado: 200.
3. **Plazo único:** caso nuevo `test_el_tope_es_uno_para_todos_los_pedidos_a_mp`, con una fila por fase. Las llamadas anteriores consumen casi todo el tope, y la fase de la fila, que por sí sola entra en el tope, lo pasa. Da 503 dentro del tope. Cada fase con un plazo propio da rojo en su fila.
4. **Texto falso:** cancelar decía «No se pudo cancelar en Mercado Pago; tu plan sigue igual.» Ahora dice «No se pudo confirmar la cancelación en Mercado Pago. Probá de nuevo en unos minutos.» El caso compara el texto exacto. **Sacar y el checkout no tenían esa frase**, así que no los cambié:
   - sacar dice «No se pudo confirmar en Mercado Pago la suscripción de {username}; sigue en el estudio.». Es cierto: el 503 sale antes de `member.organization_id = None`, y el caso compara el estado antes y después.
   - el checkout dice «No pudimos confirmar tu suscripción actual con Mercado Pago.» No afirma nada del plan.

Archivo de producto tocado: `proyecto_maria/main.py` (`cancel_billing`: el texto, el docstring y un comentario). Además, `CHANGELOG.md`. **producto +3/−3** contra `64770b9`.

### Decisiones

- **D64 (a)** y **D66 (a)**, registradas como las contestaste:
  - D64: lo hace Emi antes de publicar; se lo aviso yo.
  - D66: un cambio de `core/rate_limit.py` sería otra pieza.
- **D112** (los pares son míos, pero a MARIA le diste la D108 y la D110 en FRONT-422 y ENTRADAS-2; salto a la próxima par libre para no chocar). **Después de un 503 por el tope, Mercado Pago pudo haber aplicado el cambio, pero CDI no lo anota.**
  - **El caso:** cancelar no recibe a tiempo la respuesta del PUT, pero Mercado Pago sí lo canceló. CDI deja `billing_status` y `mp_preapproval_id` como estaban.
  - **Si se reintenta, se concilia:** `_cancelar_suscripcion_mp` lee el estado, ve «cancelled» y sigue (`test_si_mp_ya_la_tenia_cancelada_cancelar_sigue`). El texto nuevo pide reintentar.
  - **Sin reintento, no lo verifiqué:** no sé qué muestra el perfil ni qué hace el corte.
  - **Opciones:**
    - (a) dejarlo como riesgo;
    - (b) pieza aparte: conciliar con la próxima lectura o con el aviso de Mercado Pago.
  - **Recomiendo (b):** es plata. Esta devolución era sólo de pruebas, y meterlo acá agranda el producto sin que lo pidieras.

### SHAs

| SHA | qué |
|---|---|
| `64770b9` | base: merge de tu rama |
| `08bab23` | producto: el texto de cancelar y `CHANGELOG.md` |
| `3726c53` | arnés: un caso por causa para firma, quién toca a quién y plazo único |
| `67413fe` | producto: el comentario de cancelar ya no cita el texto viejo |
| `247c081` | arnés: el 503 de cancelar no dice que el plan sigue igual; la firma rota conserva su ts |
| `8abdc48` | merge de tu rama (`e29ec1d`) |
| `10d9389` | arnés: el tope se prueba fase por fase y se compara el texto exacto |
| `71e15df` | arnés: los sabotajes de MP-2 prueban el plazo único fase por fase |
| `a4bb6d6` | merge de tu rama (`c73e0ea`), sólo `docs/pm` |
| `4e082ab` | merge de tu rama (`ff88333`), sólo `docs/pm` |
| `921c069` | merge de tu rama (`ba3289f`), sólo `docs/pm` |

### Cada punto con su rojo

**1. Firma** (`tests/test_cobro_mp3.py`, `_SIN_FIRMA` y `test_un_aviso_sin_firma_verificable_no_cambia_nada`, sabotajes en `cobro_mp3.sh`):

```
ROJO  | el límite cuenta también los avisos sin firma: dice «FAILED tests/test_cobro_mp3.py::test_el_aviso_de_pago_tiene_limite_de_pedidos»
ROJO  | sin clave, en desarrollo, el aviso pasa sin verificar: dice «FAILED tests/test_cobro_mp3.py::test_un_aviso_sin_firma_verificable_no_cambia_nada[sin-secreto-dev]»
ROJO  | se atiende un IPN por la URL, sin firma: dice «('ipn', 200»
ROJO  | un cuerpo que no es un objeto rompe la verificación: dice «'cuerpo que no es un objeto'»
ROJO  | un data que no es un objeto rompe la verificación: dice «'data que no es un objeto'»
ROJO  | la firma se compara como texto: dice «'firma con letras no ascii'»
ROJO  | sin clave configurada, se verifica con la clave vacía: dice «('firmado con clave vacía', 200»
ROJO  | la firma se compara a medias (sólo los primeros caracteres): dice «('sólo los primeros caracteres', 200»
ROJO  | la firma se compara a medias (firma más corta): dice «('firma más corta', 200»
ROJO  | la firma se compara a medias (firma más larga): dice «('firma más larga', 200»
ROJO  | la firma se compara a medias (el último carácter cambiado): dice «('el último carácter cambiado', 200»
```

**2. Quién toca a quién** (`test_solo_la_duena_o_quien_abrio_la_que_paga_la_tocan`, sabotajes en `cobro_mp2.sh`):

```
ROJO  | en una org, cualquier miembro cancela el plan: dice «FAILED tests/test_cobro_mp2.py::test_solo_la_duena_o_quien_abrio_la_que_paga_la_tocan[cancelar-miembro]»
ROJO  | reactivar no mira quién toca el plan: dice «FAILED tests/test_cobro_mp2.py::test_solo_la_duena_o_quien_abrio_la_que_paga_la_tocan[reactivar-miembro]»
ROJO  | al sacar a un miembro no se mira su suscripción: dice «FAILED tests/test_cobro_mp2.py::test_solo_la_duena_o_quien_abrio_la_que_paga_la_tocan[sacar_con_pendiente-duena]»
ROJO  | se saca del estudio a quien abrió la que paga: dice «FAILED tests/test_cobro_mp2.py::test_solo_la_duena_o_quien_abrio_la_que_paga_la_tocan[sacar_a_la_que_paga-duena]»
ROJO  | se saca del estudio a quien tiene la pausada: dice «FAILED tests/test_cobro_mp2.py::test_solo_la_duena_o_quien_abrio_la_que_paga_la_tocan[sacar_a_la_pausada-duena]»
ROJO  | al sacar, la ya cancelada se vuelve a cancelar: dice «FAILED tests/test_cobro_mp2.py::test_solo_la_duena_o_quien_abrio_la_que_paga_la_tocan[sacar_con_cancelada-duena]»
ROJO  | al sacar, si Mercado Pago no contesta se saca igual: dice «FAILED tests/test_cobro_mp2.py::test_solo_la_duena_o_quien_abrio_la_que_paga_la_tocan[sacar_sin_mp-duena]»
ROJO  | al sacar, la suscripción cancelada sigue anotada: dice «FAILED tests/test_cobro_mp2.py::test_solo_la_duena_o_quien_abrio_la_que_paga_la_tocan[sacar_con_pendiente-duena]»
ROJO  | la dueña de un estudio saca a un miembro de otro: dice «FAILED tests/test_cobro_mp2.py::test_solo_la_duena_o_quien_abrio_la_que_paga_la_tocan[sacar_con_pendiente-duena_de_otro]»
ROJO  | reactivar no mira la suscripción de quien la abrió: dice «FAILED tests/test_cobro_mp2.py::test_solo_la_duena_o_quien_abrio_la_que_paga_la_tocan[reactivar_con_la_suya-abrio]»
```

**3. Plazo único.** Mutantes a mano, uno por fase: el pedido de esa fase con `hasta=anyio.current_time() + _TOPE_MP`. Cada mutante corrió contra el caso viejo (el de `cb740f3`) y contra el nuevo (`-k tope`):

| Mutante | Caso viejo | Caso nuevo |
|---|---|---|
| lectura de `_quien_toca_el_plan` | `11 passed` | `2 failed`: `[cancelar_lee]`, `[reactivar_lee]` |
| checkout: PUT de la vieja | `11 passed` | `1 failed`: `[checkout_cancela]` |
| checkout: create | `11 passed` | `1 failed`: `[checkout_crea]` |
| checkout: relectura | `11 passed` | `1 failed`: `[checkout_relee]` |
| cancelar: PUT | `11 passed` | `1 failed`: `[cancelar_cancela]` |
| sacar: PUT | `1 failed` `[sacar]` | `1 failed`: `[sacar_cancela]` |
| reactivar: plazo `+1e9` | `11 passed` | `1 failed`: `[reactivar_lee]` |
| sin mutar | | `15 passed, 91 deselected in 34.30s` |

El caso viejo dejaba verdes seis de siete. Los mismos mutantes quedaron como sabotajes en `cobro_mp2.sh`:

```
ROJO  | cada pedido a Mercado Pago tiene su propio tope: dice «FAILED tests/test_cobro_mp2.py::test_el_tope_es_uno_para_todos_los_pedidos_a_mp[cancelar_lee]»
ROJO  | un pedido a Mercado Pago con su propio plazo (cancelar_lee): dice «FAILED tests/test_cobro_mp2.py::test_el_tope_es_uno_para_todos_los_pedidos_a_mp[cancelar_lee]»
ROJO  | un pedido a Mercado Pago con su propio plazo (cancelar_cancela): dice «FAILED tests/test_cobro_mp2.py::test_el_tope_es_uno_para_todos_los_pedidos_a_mp[cancelar_cancela]»
ROJO  | un pedido a Mercado Pago con su propio plazo (checkout_relee): dice «FAILED tests/test_cobro_mp2.py::test_el_tope_es_uno_para_todos_los_pedidos_a_mp[checkout_relee]»
ROJO  | un pedido a Mercado Pago con su propio plazo (checkout_cancela): dice «FAILED tests/test_cobro_mp2.py::test_el_tope_es_uno_para_todos_los_pedidos_a_mp[checkout_cancela]»
ROJO  | un pedido a Mercado Pago con su propio plazo (checkout_crea): dice «FAILED tests/test_cobro_mp2.py::test_el_tope_es_uno_para_todos_los_pedidos_a_mp[checkout_crea]»
ROJO  | un pedido a Mercado Pago con su propio plazo (sacar_cancela): dice «FAILED tests/test_cobro_mp2.py::test_el_tope_es_uno_para_todos_los_pedidos_a_mp[sacar_cancela]»
ROJO  | reactivar no tiene tope: dice «FAILED tests/test_cobro_mp2.py::test_el_tope_es_uno_para_todos_los_pedidos_a_mp[reactivar_lee]»
```

**4. Texto.** Mutante T2: el texto de cancelar cambiado a «No se pudo confirmar la cancelación. Tu plan sigue activo y no se cobrará de más. Probá…». Corrió con `-k "sin_contestar or a_medias"`.

| | Resultado |
|---|---|
| caso viejo | `12 passed, 90 deselected in 17.28s` |
| caso nuevo | `2 failed, 10 passed, 94 deselected in 17.28s` |

Los dos rojos del caso nuevo:

- `FAILED tests/test_cobro_mp2.py::test_con_mp_sin_contestar_se_contesta_503_dentro_del_tope[cancelar_lee]`
- `FAILED tests/test_cobro_mp2.py::test_con_mp_sin_contestar_se_contesta_503_dentro_del_tope[cancelar_cancela]`

En el script:

```
ROJO  | si Mercado Pago no contesta, cancelar dice que el plan sigue igual: dice «FAILED tests/test_cobro_mp2.py::test_con_mp_sin_contestar_se_contesta_503_dentro_del_tope[cancelar_lee]»
```

### Sabotajes, sobre `71e15df`

| Script | ROJO | Fallas | Salida |
|---|---|---|---|
| `cobro_mp2.sh 71e15df` | 77 de 77 | `sabotajes con falla: 0` | `salida 0` |
| `cobro_mp3.sh 71e15df` | 18 de 18 | `sabotajes con falla: 0` | `salida 0` |

Las líneas de base, copiadas:

```
BASE  | en verde
BASE  | los cruces en Postgres, en verde
BASE  | tests/test_cobro_mp3.py en verde
```

Ninguna línea `ROJO?`, `VERDE`, `TRABA` ni `ROTO`. Los 77 de MP-2 incluyen 6 sobre Postgres 16 descartable (candados y tope desde el candado).

**Cómo corrió MP-2.** Tardó ~2 min por sabotaje (~2 h 20 min en total), cuando la corrida anterior hizo 61 en 30 min. Cada pytest ocupaba ~99 % de un núcleo y la carga de la máquina era ~1 sobre 4 núcleos. No diagnostiqué la causa de la lentitud.
- La primera corrida se cortó por el tope de 30 min de mi espera.
- La segunda, por el tope de 2 h de los trabajos en segundo plano, a los 62 sabotajes, todos ROJO y sin `salida`. No la cuento.
- La que vale es una tercera, desacoplada de ese tope y lanzada antes de que se cortara la segunda: la de la tabla.

MP-3 corrió aparte, también sobre `71e15df`.

### Puertas, sobre `71e15df`

| Puerta | Salida |
|---|---|
| suite completa, desde worktree limpio | `4585 passed, 101 skipped, 3 xfailed in 744.40s (0:12:24)`, salida 0 |
| `python -m compileall -q proyecto_maria` | salida 0, sin texto |
| chequeo-6 | abajo, entero |
| `/code-review high` y `/security-review` | en «Revisión» |

La suite deja 714 líneas `Task was destroyed but it is pending!` al cerrar. No es nuevo: la corrida sobre `8abdc48` dejó 690, y una anterior, 630. No lo diagnostiqué en esta pieza.

### chequeo-6, `64770b9 a4bb6d6`

```
chequeo-6 64770b9..a4bb6d6: avisos para mirar, no un veredicto
producto +3/−3
arnés +154/−22
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11358 → 11358
avisos: 0
```

Contra tu base, `cb740f3 a4bb6d6`:

```
chequeo-6 cb740f3..a4bb6d6: avisos para mirar, no un veredicto
producto +17/−12
arnés +214/−39
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11358 → 11358
  proyecto_maria/static/v2/screens/finalize.js: 1386 → 1391
avisos: 0
```

`finalize.js` entra por el merge de VALIDACION-1; no es de esta pieza.

### Revisión

**`/code-review high`**, sobre `cb740f3..10d9389`:

| N.º | Dónde | Qué | Qué hice |
|---|---|---|---|
| 1, 2 | `finalize.js:133` y `:110` | VALIDACION-1 | Ya está en sus riesgos. Fuera de esta pieza |
| 3 | `main.py:2109` | El comentario citaba el texto viejo | Arreglado en `67413fe` |
| 4 | `CHANGELOG.md` | — | Falso positivo: la línea existe y describe el cambio |
| 5 | `test_cobro_mp2.py:824` | El texto se miraba por partes | Ahora se compara exacto (`10d9389`) |
| 6, 9 | `pantalla_validacion1.js:110` y `:102` | VALIDACION-1 | Ya está en sus riesgos. Fuera de esta pieza |
| 7 | `test_cobro_mp2.py:860` | `_Lenta` simula la demora | Es una entrada simulada a propósito. El tope real lo cubre el caso fase por fase |
| 8 | `test_cobro_mp3.py:40` | La firma rota perdía su ts | Arreglado en `247c081` |

**Adversario:** uno solo, `adversario-sonnet-alto` (Sonnet, esfuerzo alto), sobre `3726c53`.

| Hallazgo | Severidad | Reproducido | Qué hice |
|---|---|---|---|
| Tres rojos propios en el arnés (ver «Error propio») | Alta | Sí | Arreglado en `247c081` |
| El texto T2 pasaba el caso | Media | Sí, mutante T2 | El caso compara el texto exacto |
| Un plazo por fase pasaba el caso | Media | Sí, tabla de mutantes | Caso fase por fase y sabotajes |
| Quitar `or not req_id`, o cambiar `compare_digest` por `==`, no da rojo | — | No lo reproduje | Riesgo 1 |
| La firma no mira la frescura del ts | — | Por código | Riesgo 2 |
| El hilo de cancelar puede durar hasta 20 s con un tope de 15 s | — | Por código | Riesgo 3 |

El adversario vio rojo con el caso viejo en el mutante de la relectura del checkout. En mi corrida, el caso viejo da `11 passed`. Va en la tabla como lo corrí.

**`/security-review`:** subagente general-purpose (Sonnet, esfuerzo alto), sobre todo lo que cambió la rama. Sin hallazgos de severidad media o alta. Anotó, como menor, que la firma usa el `data.id` del cuerpo y no el de la query: viene de antes de este rango (riesgo 4).

### Error propio

`08bab23` dejó en rojo `test_si_mp_no_cancela_no_se_cancela_a_medias`: el caso todavía esperaba el texto viejo. Lo vi al correr el arnés y quedó arreglado en `247c081`. `08bab23` no se entrega solo.

### Riesgos

1. **La firma tiene dos variantes sin rojo:** sin el `x-request-id` y con `compare_digest` cambiado por `==`. Una comparación con `==` filtra tiempo pero no acepta firmas falsas. No agregué casos: no son de esta devolución.
2. **La firma no mira la frescura del ts:** un aviso firmado se puede repetir. Hoy repetir un pago ya anotado no cambia nada. Es una pieza aparte si la querés.
3. **El hilo abandonado sigue hasta 20 s** (`timeout=10` del cliente por PUT + GET). La respuesta sale a los 15 s, y el hilo ocupa uno de los 8 cupos hasta que termina.
4. **Hallazgo menor de `/security-review`:** la firma usa el `data.id` del cuerpo. Viene de antes de este rango.
5. **D112.**

### Lo que no se corrió

- La suite de Postgres fuera de los sabotajes: sus escenarios corrieron como base de `cobro_mp2.sh` (en verde).
- Los sabotajes de piezas anteriores: los corrés vos antes de publicar.
- Nada contra Mercado Pago real.

### Para reproducir

```bash
scripts/testing/sabotajes/cobro_mp2.sh 71e15df   # cada línea «ROJO …» y al final «sabotajes con falla: 0»
scripts/testing/sabotajes/cobro_mp3.sh 71e15df   # lo mismo
python -m pytest -q --no-cov tests/test_cobro_mp2.py -k tope   # «15 passed»
docs/pm/herramientas/chequeo-6.py 64770b9 71e15df   # «producto +3/−3», «avisos: 0»
```

/compact conservar: Dev 1, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM) con send_message priority next. COBRO-MP-2+3 devolución entregada en 71e15df (informe en el commit de arriba). Abierta D112 (recomiendo b). Sigue AISLAMIENTO-2 / LIMPIEZA-1, después BACKUP-1a y EXCEL-2c; frenar 2026-11-08 15:50 UTC. Reglas de Emi: sólo la PM y Emi me piden, nada se publica sin su «dale» para el SHA, nunca main, sin secretos.
