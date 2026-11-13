# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## DOS-RELOJES: el mensaje de `forzar_orden1.js` ya no cambia entre corridas

| | SHA |
|---|---|
| base (mi informe de CONFTEST-TMP) | `eea0eab5` |
| arreglo (`test:`, sólo `scripts/testing/forzar_orden1.js`) | `894bc67a` |
| merge de tu rama (sólo `docs/pm/`, sin conflictos) | `4a8652a7` |
| informe | el commit `docs:` que sigue |

**Resultado:** verde. El comando 1 del informe de ORDEN1 da el mismo mensaje
cuatro veces seguidas. `orden1b.sh` sigue con 30 `ROJO`. **Nada para
decidir.**

**Causa.** El producto corta la consulta de sesión a los 10 s
(`ESPERA_SESION_MS`, `app_v2.js`) desde que la pestaña la pide. El preload la
retenía 10 s desde el login. Los dos relojes casi empataban, y según quién
llegaba primero salía un mensaje u otro.

**Arreglo.** El preload cuenta desde que la pestaña pide la consulta, igual
que el producto. El tope sube a 15 s, por encima del corte. El tope 15 s es un
supuesto reversible: cualquier valor entre 10 y el límite del caso alcanza;
elegí 5 s de margen.

### Comandos

```bash
# 1. Arreglo: cuatro corridas, las cuatro con rc=0, la línea OK y
#    «forzar_orden1: la consulta del hueco se cortó sin respuesta antes de entrar».
F=$PWD/scripts/testing/forzar_orden1.js
for i in 1 2 3 4; do NODE_OPTIONS="--require $F" CASOS=z22 SOLO=orden1 PY=$PY \
  scripts/testing/correr_pantallas.sh 894bc67a /tmp/dr_$i >/dev/null 2>&1; echo "rc=$?"; \
  grep -E 'forzar_orden1: la|FALLA|OK A salió' /tmp/dr_$i/orden1.log; done

# 2. Rojo: lo mismo con el preload viejo; el mensaje cambia entre corridas.
#    El producto no cambió entre eea0eab5 y 894bc67a: sirve el mismo SHA.
git show eea0eab5:scripts/testing/forzar_orden1.js > /tmp/forzar_viejo.js   # y F=/tmp/forzar_viejo.js

# 3. Ningún sabotaje de ORDEN-1b pierde su rojo: 30 ROJO, «sabotajes sin rojo: 0», rc=0.
PY=$PY scripts/testing/sabotajes/orden1b.sh 894bc67a
```

### Lo corrido (salida copiada de los logs)

**Rojo, preload viejo sobre `eea0eab5`:** el mensaje cambia entre corridas.

| corrida | rc | `forzar_orden1:` |
|---|---|---|
| 1 | 0 | la consulta del hueco se cortó sin respuesta antes de entrar |
| 2 | 0 | la consulta del hueco seguía retenida a los 10 s |
| 3 | 0 | la consulta del hueco seguía retenida a los 10 s |
| 4 | 0 | la consulta del hueco seguía retenida a los 10 s |

Las cuatro corridas traen además «OK A salió, volvió a entrar y generó
enseguida: genera sin falsos bloqueos».

**Arreglo, preload nuevo sobre `eea0eab5`:** las cuatro corridas dan rc=0,
«forzar_orden1: la consulta del hueco se cortó sin respuesta antes de entrar»
y la misma línea OK.

**Comando 2 del informe de ORDEN1 (base `74e3cc74`) con el preload nuevo:**
sigue rojo. Da rc=1 con:

```
forzar_orden1: activo
forzar_orden1: la consulta del hueco volvió antes de entrar: 401
FALLA: page.evaluate: TypeError: Cannot read properties of null (reading 'click')
```

**El preload ve el corte del producto, no su propio tope.** Hice un commit
local `5ce86061` sobre `894bc67a` que sólo cambia `ESPERA_SESION_MS` de 10000
a 20000 en `app_v2.js`. No está subido; se rehace con ese `sed` y un commit
en un worktree. Con el preload nuevo da rc=0 y
«forzar_orden1: la consulta del hueco seguía retenida a los 15 s de pedida».
El mensaje cambia cuando cambia el producto.

**`orden1b.sh 894bc67a`:** 30 `ROJO`, «sabotajes sin rojo: 0», rc=0.

**`chequeo-6 eea0eab5 894bc67a`**, entero:

```
chequeo-6 eea0eab5..894bc67a: avisos para mirar, no un veredicto
producto +0/−0
arnés +9/−6
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

### No corrido

- Adversarios y `/code-review`: la tarea dice «sin adversarios», y la pieza
  son 15 líneas de arnés.
- Suite de pytest, el resto de los arneses de pantalla, `smoke_friccion.sh` y
  ataques: el producto no cambió, y ningún guion, prueba ni arnés nombra
  `forzar_orden1.js` (`grep -rl forzar_orden1 scripts tests` da sólo el
  archivo mismo); sólo lo carga el `NODE_OPTIONS` del comando.

### Riesgos

- Si alguien sube `ESPERA_SESION_MS` por encima de 15 s, el preload vuelve a
  ganarle al producto. El mensaje lo dice con el número («a los 15 s de
  pedida»), así que se ve; no es silencioso.

/compact conservar: Dev 1 técnica, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica, PM principal session_01B7FVQspcEHF7PqNv797wNM (aviso con send_message priority next). DOS-RELOJES entregada: arreglo 894bc67a, merge 4a8652a7, informe docs: encima. Sin tarea nueva hasta el veredicto. Próxima D: D229. Nunca main, sin secretos, nada publicado sin «dale» de Emi para el SHA; tests/test_conexiones1.py nunca a git add.
