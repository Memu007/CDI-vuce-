# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D139 (a), escapar el panel de dev: **entregada** en `3fde8bb` (2026-11-09; el informe va en el commit siguiente), base `827df3e`

| SHA | Qué |
|---|---|
| `43ac587` | fix: `dev_dashboard.html` arma la tabla de pedidos con `textContent`, sin `innerHTML`; CHANGELOG |
| `55f282c` | test: `scripts/testing/pantalla_panel_dev.js` (Chromium) y `scripts/testing/sabotajes/panel_dev.sh` |
| `3fde8bb` | test: la prueba cuenta las imágenes pedidas por el ataque y mira el gris de hora e IP |

**Resultado:** la tabla «pedidos recientes» del panel muestra como texto la
hora, el método, el endpoint, el estado, la latencia y la IP. Un valor con
`<img src=/inyectado onerror=…>` no crea elementos, no pide la imagen y se lee
tal cual; `<sin ruta>` también. Se conservan la insignia del método, el color
del estado y el gris de hora e IP.

**Nada para decidir.** Leí tu D151 (a): tu rama no la traigo hasta que
INTEGRAR-1 esté aceptada, así que esta pieza va sobre `827df3e` sin merge.
Supuesto reversible: ninguno; no agregué nada fuera de la tabla.

**Archivo de producto tocado:** `proyecto_maria/templates/dev_dashboard.html`.
`producto +22/−27`.

### Comandos copiables

```bash
node scripts/testing/pantalla_panel_dev.js          # 7 «OK», última línea «fallas: 0», salida 0
scripts/testing/sabotajes/panel_dev.sh 3fde8bb      # «BASE | en verde», 6 «ROJO», «sabotajes sin rojo: 0», salida 0
git show 827df3e:proyecto_maria/templates/dev_dashboard.html > proyecto_maria/templates/dev_dashboard.html; \
  node scripts/testing/pantalla_panel_dev.js; git checkout -- proyecto_maria/templates/dev_dashboard.html   # «fallas: 4», las de abajo
```

Ninguno necesita servidor ni base: la prueba sirve la plantilla real y
responde la API ella misma.

### Rojo con el producto anterior (`827df3e`), copiado de la salida

```
FALLA | elementos creados por el texto de api_logs: 10
FALLA | imágenes pedidas por el texto de api_logs: 1
FALLA | fila 1 como texto: ["1","2","3","500","4 ms","5"]
FALLA | fila 2 como texto: ["10:00:00","GET","","404","7 ms","203.0.113.9"]
```

### Sabotajes, sobre `3fde8bb` (salida exacta)

```
BASE  | en verde
ROJO  | las celdas interpretan el texto como HTML: dice «elementos creados por el texto de api_logs»
ROJO  | el texto se interpreta como HTML fuera de la tabla: dice «imágenes pedidas por el texto de api_logs»
ROJO  | la insignia interpreta el método como HTML: dice «elementos creados por el texto de api_logs»
ROJO  | el estado pierde su color: dice «color del estado»
ROJO  | la hora y la IP pierden el gris: dice «hora e IP en gris»
ROJO  | el método pierde su insignia: dice «método en su insignia»
sabotajes sin rojo: 0
```

Cada sabotaje exige que su patrón aparezca una sola vez (si no, «ROTO») y que
el rojo diga su motivo (si no, «ROJO?»).

### Puertas, sobre `3fde8bb`

| Puerta | Salida |
|---|---|
| pytest (entorno de `/entregar`) | `=== 5452 passed, 335 skipped, 3 xfailed, 108 warnings in 1053.49s (0:17:33) ====`, salida 0. Al final, avisos «Task was destroyed but it is pending!» de asyncio, como en las vueltas anteriores. |
| `compileall -q proyecto_maria` | salida 0 |
| `smoke_friccion.sh` (uvicorn en 8097, SQLite propia) | `==> OK · telemetría y alias session/state rechazan sin sesión + by-cuit protegido`, salida 0 |
| `ataque_aislamiento.sh` | **no corrido**: la pieza sólo cambia una plantilla del panel admin; no toca datos, sesión ni permisos. `/api/dev/stats` sigue con `Depends(require_admin)`. |
| `pantalla_panel_dev.js` | 7 OK, `fallas: 0`. **No corre en pytest ni en la CI** (no hay navegador ahí). |
| grep de historia de §6 | vacío |

`chequeo-6.py 827df3e 3fde8bb`, salida entera:

```
chequeo-6 827df3e..3fde8bb: avisos para mirar, no un veredicto
producto +22/−27
arnés +136/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

### Hallazgos de la autorrevisión

| Quién | Hallazgo | Qué hice |
|---|---|---|
| adversario Sonnet, alto | Media: la prueba no veía la ejecución, sólo elementos dentro de la tabla; un `innerHTML` en un nodo suelto corría el `onerror` en verde | Arreglado en `3fde8bb`: cuenta los pedidos de `/inyectado` hasta una imagen centinela y busca elementos en toda la página. Sabotaje «fuera de la tabla». |
| adversario Sonnet, alto | `setAttribute('title', …)` y `href` con `javascript:` | No existen en el código: quedan como riesgo para quien los agregue |
| adversario Sonnet, alto | Baja: un método nulo deja la insignia vacía | Queda: `method` es `nullable=False` (`models.py:368`) |
| adversario Sonnet, alto | Info: latencia nula muestra «null ms» | Queda, igual que antes |
| `/code-review high` | `/inyectado` y `text-muted` no se chequeaban; `trim` escondía diferencias; `trap` armado después del worktree | Arreglados en `3fde8bb` |
| `/code-review high` | índices de celda escritos a mano | Queda: la tabla tiene seis columnas fijas en la plantilla |
| `/code-review high` | `fetchStats` no mira `response.ok` | Previo, fuera de alcance: riesgo |
| `/security-review` (Sonnet) | sin hallazgos de confianza ≥ 8 | — |

### Riesgos y lo que no se corrió

- `pantalla_panel_dev.js` y sus sabotajes no corren en la CI ni en pytest.
- `ataque_aislamiento.sh`: no corrido, por la razón de la tabla.
- Previos, fuera de alcance: `fetchStats` sin `response.ok`; el CDN de
  `dev_dashboard.html:7-8` sin SRI; «null ms».
- Ajenos que vi y no toqué: `main.py:2905` devuelve `HTMLResponse(f"<pre>{e}</pre>")`
  sin escapar; `innerHTML` en `static/v2` sin auditar. Si querés, van a una D.
- Por un error mío (variable de shell vacía) quedaron dos archivos de salida
  en la raíz del contenedor, `/panel-sab-55f282c.txt` y `/suite-55f282c.txt`.
  No están en el repositorio; no los pude borrar desde la sesión.

### Sigue

D102 (fijar `bcrypt`).
