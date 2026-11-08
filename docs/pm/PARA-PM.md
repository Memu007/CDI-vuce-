# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Dónde quedé (corte 2026-11-08 15:50 UTC)

Leí que aceptaste SEPARADORES-1b-ARNÉS sobre `1063b32`, y traje tu rama (`28a27a7`). No arranqué ninguna pieza nueva y no me queda nada sin subir. Freno acá hasta que me despiertes.

## SEPARADORES-1b-ARNÉS, entregada en `1063b32` (informe en el commit de arriba)

Base: `ea63923` (merge de tu rama con PERMISOS-3 aceptada y D127 en b).

| Commit | Qué |
|---|---|
| `1063b32` | arnés: `sabotaje_separadores1b.sh` corre primero sin sabotaje y exige verde; los tres sabotajes que ya no encontraban o ya no distinguían usan anclas de código actuales |

**producto +0/−0**, arnés +11/−5.

### Resultado

1. **El guion está en `scripts/testing/sabotaje_separadores1b.sh`.** La tarea dice `scripts/testing/sabotajes/separadores1b.sh`, que no existe en ninguna rama. No lo moví: moverlo no lo pedía la tarea.
2. **Paso de base nuevo.** Antes del primer sabotaje corre los tres archivos de casos sin tocar nada. Si hay un `failed` o un `error`, o no hay `passed`, sale con 1 y dice «BASE   en rojo». Así un guion roto en la base ya no se confunde con un sabotaje que no distingue.
3. **`pantalla_no_pregunta` (el patrón 3).** `4f2045f` cambió la condición de la pantalla. El ancla ahora es la línea actual de `montos_ar.js`, `} else if (/^\\d{4,}\$/.test(partes[0]) && !/^0+\$/.test(partes[0]) && partes[1].length === 3) {`, y el sabotaje la cambia por `} else if (false) {`.
4. **`pantalla_se_traba` pasa a `pantalla_sin_tope`.** Su ancla, `const grupos = trozos.join('.');`, también desapareció en `4f2045f`. Lo que el caso `test_una_cifra_larga_pegada_no_traba_la_pantalla` cuida hoy es el tope de 15 cifras, así que el sabotaje borra esa línea. Espera el mismo FAILED que antes.
5. **`factura_multiplica` espera otro caso.** Con la regla `sin_grupo` apagada ya no falla `test_en_la_factura_con_la_pista_en_contra_queda_sin_leer`. Falla `test_en_la_factura_con_grupos_de_espacio_tambien[4 500.000-,]`, y ese es el texto que espera ahora. Ver «Hallazgo».
6. Los otros nueve sabotajes no cambian. Sus anclas siguen apareciendo una vez cada una.

Nada para decidir. Hay una propuesta en «Hallazgo».

### Hallazgo (propuesta, fuera de alcance)

`test_en_la_factura_con_la_pista_en_contra_queda_sin_leer` ya no distingue la regla `sin_grupo` de `_monto_factura`. Desde SEPARADORES-1d, `_numero_factura("4500.000", ",")` ya devuelve None por su cuenta. Con la regla apagada, el caso sigue pasando. La regla la cuida sólo `test_en_la_factura_con_grupos_de_espacio_tambien` (grupos de espacio o apóstrofo, como «4 500.000»). No toqué el caso. Propongo anotarlo en `COLA-LIMPIEZA.md`: hay que darle una entrada que sólo la regla rechace, o sacarlo si está repetido.

### Pruebas

| Puerta | Sobre | Resultado |
|---|---|---|
| guion viejo | `ea63923` | «FALLA  factura_multiplica: rojo, pero sin «FAILED tests/test_separadores1b.py::test_en_la_factura_con_la_pista_en_contra_queda_sin_leer»» y «PATRON NO ENCONTRADO (0 veces) en proyecto_maria/static/v2/montos_ar.js: '            } else if (/^[1-9]\\d{3,}$/.test(partes[0]) && partes[1].length === 3) {'». Salida 1 |
| guion nuevo, base | `ea63923` con el guion de `1063b32` | «BASE   en verde: ======================= 265 passed, 5 warnings in 50.81s =======================» |
| guion nuevo, sabotajes | `ea63923` con el guion de `1063b32` | 12 `ROJO` y «OK: los 12 sabotajes dan rojo por la razón esperada». Salida 0 |

Rojos por sabotaje, tal como los dio la corrida:

| Sabotaje | failed |
|---|---|
| factura_multiplica | 5 failed, 260 passed |
| factura_ignora_la_pista | 3 failed, 262 passed |
| factura_grupo_con_espacio | 5 failed, 260 passed |
| pantalla_no_pregunta | 7 failed, 258 passed |
| pantalla_sin_tope | 1 failed, 264 passed |
| pedido_monto_cero | 5 failed, 260 passed |
| pedido_ajuste_nada | 7 failed, 258 passed |
| servidor_lee_como_python | 25 failed, 240 passed |
| flete_solo_numero | 13 failed, 252 passed |
| generar_sin_normalizar | 1 failed, 264 passed |
| avisos_sin_mirar | 4 failed, 261 passed |
| blanco_no_es_cero | 1 failed, 264 passed |

La corrida verde usó una copia del guion idéntica a la de `1063b32`, tomada antes del commit. `1063b32` no toca producto, así que el árbol que se sabotea es el mismo.

### chequeo-6

```
chequeo-6 ea63923..1063b32: avisos para mirar, no un veredicto
producto +0/−0
arnés +11/−5
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

### Lo que no se corrió

- **La suite completa** no corrió: el cambio es sólo del guion y el producto es el de `ea63923`.
- **Los subagentes, `/code-review` y `/security-review`** no corrieron. Es un cambio de arnés de 16 líneas sin producto, y la prueba es la corrida misma: base verde y 12 rojos.
- **La CI de GitHub** no corrió: esta rama no tiene PR.

### Para reproducir

```bash
git fetch origin claude/dev-tecnica && git checkout --detach 1063b32
export DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares

# «BASE   en verde», 12 ROJO, «OK: los 12 sabotajes dan rojo por la razón esperada», salida 0
bash scripts/testing/sabotaje_separadores1b.sh 1063b32 <venv>; echo salida=$?

# El rojo de antes: «PATRON NO ENCONTRADO (0 veces) en proyecto_maria/static/v2/montos_ar.js», salida 1
git show ea63923:scripts/testing/sabotaje_separadores1b.sh > /tmp/viejo.sh
bash /tmp/viejo.sh 1063b32 <venv>; echo salida=$?

# Los números de §6: la salida de arriba
python docs/pm/herramientas/chequeo-6.py ea63923 1063b32
```

`<venv>` es el entorno virtual del proyecto: el guion lo toma como segundo argumento.

/compact conservar: Dev 1, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM) con send_message priority next. PERMISOS-3 aceptada en 9428e00; D127 decidida (b, pieza aparte). SEPARADORES-1b-ARNÉS aceptada sobre 1063b32. Corte de 24 h: frenada, sin pieza activa. Próxima D libre: D128. Reglas de Emi: sólo la PM y Emi me piden, nada se publica sin su «dale» para el SHA, nunca main, sin secretos.
