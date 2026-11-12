# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D145 (a): entregado en `08edd63` (sólo pruebas)

| qué | SHA |
|---|---|
| base | `46959d7` |
| validación y registro con invitación registran con otra IP | `b420203` |
| MARIA-9 y SEPARADORES-1 también, y la IP inventada sale de un solo archivo — **el que se entrega** | `08edd63` |
| tu rama (`0a50bcb`) traída con `merge`, después de las puertas | `83a0bb7` |
| informe | el commit siguiente |

**Resultado.** Mis cuatro pantallas que registran varias veces contra una
misma base mandan un `X-Forwarded-For` distinto en cada registro:
`validacion1`, `org1b`, `maria9` y `separadores1`. `validacion1.sh` y
`org1b.sh`, que daban 3 y 2 `ROJO?` por el 429, corren enteros: 7 de 7
`ROJO` cada uno. `sabotaje_separadores1.sh` entero: 17 de 17. Producto:
**+0/−0**. Arnés: +12/−4.

**Dos cosas que tenés que saber antes de aceptar:**

1. **`sabotaje_maria9.sh` no corre entero, y no es por esta pieza.** Muere
   en su segundo sabotaje con `PATRON NO ENCONTRADO`: el producto cambió y
   el guion quedó con anclas viejas. Es D191. Por eso la prueba de
   `pantalla_maria9.js` no es el guion entero sino seis corridas de la
   pantalla contra una sola base (abajo).
2. **`b420203` era más angosto que tu pedido.** Lo había leído como «donde
   hoy se ve el 429». `/code-review` y el adversario marcaron que `maria9`
   quedaba en 5 registros de 5 posibles, sin margen. Lo amplié en `08edd63`.

**D149 (a):** leí tu veredicto (aceptada sobre `48195cfe`, D168 (b), D169
(a)) y traje tu rama con `merge`. No queda nada abierto de esa pieza.

## Decisiones

**D190. `ipNueva` sigue copiada en seis pantallas de la Técnica.** Dejé la
función en `scripts/testing/_ip_nueva.js` y mis cuatro pantallas la toman
de ahí. `pantalla_cliente1.js`, `_despacho1a.js`, `_destino1.js`,
`_estudio1.js`, `_estudio1b.js` y `_orden1.js` tienen cada una su copia: no
son mías y no las toqué.

- (a) A la cola de limpieza: esas seis pasan a tomar `_ip_nueva.js`.
- (b) Pieza chica para la Técnica, ahora.
- (c) Quedan como están.

**Recomiendo (a).** No hay nada roto: es una línea repetida seis veces. No
toqué `COLA-LIMPIEZA.md`: es tuyo.

**D191. `sabotaje_maria9.sh` está roto por anclas viejas.** Sobre `b420203`
(antes de tocar nada de MARIA-9) da un `ROJO` y sale 1 a los 12 s:

```
ROJO   analiza_siempre: ================== 7 failed, 131 passed, 5 warnings in 8.98s ===================
PATRON NO ENCONTRADO (0 veces) en proyecto_maria/core/maria_generator.py: '        if usa_el_sufijo_de_la_operacion(items, iva_adicional):'
```

Leyendo el guion contra el producto de hoy (sin correrlo): de sus 28 anclas
de una línea, 10 ya no están, de 5 textos distintos; dos anclas de varias
líneas no las conté. La función `usa_el_sufijo_de_la_operacion` ya no
recibe `iva_adicional`, y cambiaron tres líneas del error de kilos. No sé
desde cuándo está así: el guion no se toca desde el 2026-10-25. Mientras
siga así, 29 de sus 30 sabotajes no corren.

- (a) Pieza mía, aparte: pongo sus anclas al día (código, no comentarios) y
  lo corro entero.
- (b) A la cola de limpieza.
- (c) Se retira el guion.

**Recomiendo (a).** MARIA-9 decide qué sufijo de valor sale en el TXT; un
guion de sabotaje que no corre es peor que no tenerlo, porque parece
cobertura. No lo hice acá: no es D145 y son al menos cinco anclas que hay
que volver a pensar una por una.

## Supuestos reversibles

1. **Cuatro pantallas, no todas.** El header va donde un guion registra más
   de una vez contra la misma base. En los guiones que crean una base nueva
   por corrida (tabla de abajo) cada sabotaje ya tiene su propia cuenta y el
   header no cambiaría nada que se pueda probar. Si lo querés igual en
   todos, decímelo.
2. **Un archivo nuevo, `scripts/testing/_ip_nueva.js`** (3 líneas), en vez
   de la cuarta copia de la misma línea en mis pantallas. Es el primer
   módulo compartido entre pantallas; las cuatro lo buscan al lado suyo, así
   que corren desde cualquier carpeta pero no si alguien copia una pantalla
   sola a otro lado.
3. **En `org1b` el header va en el contexto del navegador, no sólo en el
   registro.** El registro sale del formulario de la página, no del arnés.
   `/code-review` propuso interceptar sólo `/auth/register`; lo dejé en el
   contexto porque es una línea y las otras rutas que toca (la landing y
   `/api/invitations/<token>`) no tienen límite por IP. El contexto del
   dueño no lo lleva.
4. **No agregué el chequeo de la respuesta del registro** en `maria9` ni en
   `separadores1` (hoy no la miran). Con el header el 429 ya no llega.
5. **No fijé `TRUSTED_PROXY_HOPS` en los guiones** (riesgos).

## Comandos

Cada guion trabaja en un worktree descartable; uno por vez.

```bash
export PATH=/opt/node22/bin:$PATH
PY=<venv>/bin/python bash scripts/testing/sabotajes/validacion1.sh 08edd63
# BASE en verde, 7 líneas «ROJO  |», FALLAS=0, sale 0 (134 s acá)
PY=<venv>/bin/python bash scripts/testing/sabotajes/org1b.sh 08edd63
# 7 líneas «ROJO  |», «sabotajes sin rojo: 0», sale 0 (23 s acá)
bash scripts/testing/sabotaje_separadores1.sh 08edd63 <venv>
# 14 «ROJO» de pytest, «VERDE  pantalla sin sabotaje», 3 «ROJO» de pantalla,
# «OK: los 17 sabotajes dan rojo por la razón esperada», sale 0 (377 s acá)
```

Para `maria9` y `separadores1`, seis corridas de cada pantalla contra una
sola API y una sola base (el límite corta en el sexto registro de una IP):

```
sobre b420203 (antes)
=== maria9
corrida 1 a 5: sale 0 | PANTALLA MARIA-9 OK
corrida 6: sale 1
registros contados por IP: [('registro:h:127.0.0.1', 6)]
=== separadores1
corrida 1 a 5: sale 0 | PANTALLA SEPARADORES-1 OK
corrida 6: sale 1
registros contados por IP: [('registro:h:127.0.0.1', 6)]

sobre 08edd63
=== maria9
corrida 1 a 6: sale 0 | PANTALLA MARIA-9 OK
registros contados por IP: [('registro:h:10.0.237.141', 1), ('registro:h:10.126.143.15', 1), ('registro:h:10.14.205.4', 1), ('registro:h:10.164.0.146', 1), ('registro:h:10.31.68.74', 1), ('registro:h:10.72.63.207', 1)]
=== separadores1
corrida 1 a 6: sale 0 | PANTALLA SEPARADORES-1 OK
registros contados por IP: [('registro:h:10.101.246.105', 1), ('registro:h:10.105.249.224', 1), ('registro:h:10.142.239.241', 1), ('registro:h:10.180.18.67', 1), ('registro:h:10.48.12.252', 1), ('registro:h:10.84.43.245', 1)]
```

El guion de las seis corridas es mío, de trabajo, y no está en el
repositorio: levanta la API como lo hace `sabotaje_maria9.sh` (líneas 113 a
128), corre `node scripts/testing/pantalla_<pieza>.js` seis veces y lee
`limites_auth` de la base.

El rojo de `validacion1.sh` y `org1b.sh` sobre `46959d7` (los mismos
números que dio la Técnica al abrir D145, 3 y 2):

```
validacion1.sh
ROJO? | con una validación en curso, la que se ve no valida: rojo (salida 1), pero sin «FALLA: panel, la anterior contesta después: no mostró la validación de la que se ve»
FALLA: Error: no se pudo registrar: 429
ROJO? | el caché no mira la cabecera: rojo (salida 1), pero sin «FALLA: cabecera distinta, mismos ítems: no volvió a validar con la cabecera cambiada»
FALLA: Error: no se pudo registrar: 429
ROJO? | sin caché: siempre vuelve a pedir: rojo (salida 1), pero sin «FALLA: panel, misma carga sin cambios: volvió a pedir la validación de la misma carga»
FALLA: Error: no se pudo registrar: 429
FALLAS=3

org1b.sh
ROJO? | la línea del email invitado no aparece: rojo (salida 1), pero sin «FALLA: con invitación válida no se ve la línea del email invitado»
FALLA: con el email cambiado en el DOM el registro dio 429, no 400
ROJO? | el servidor deja de exigir el email invitado: rojo (salida 1), pero sin «FALLA: con el email cambiado en el DOM el registro dio 200, no 400»
FALLA: con el email cambiado en el DOM el registro dio 429, no 400
sabotajes sin rojo: 2
```

## Puertas

| puerta | SHA | resultado | registro |
|---|---|---|---|
| `validacion1.sh` entero, antes | `46959d7` | 4 `ROJO`, 3 `ROJO?` (429), sale 1, 84 s | `d145_rojo_validacion1.log` |
| `org1b.sh` entero, antes | `46959d7` | 5 `ROJO`, 2 `ROJO?` (429), sale 1, 23 s | `d145_rojo_org1b.log` |
| seis corridas de `maria9` y `separadores1`, antes | `b420203` | 5 verdes y la sexta sale 1, en las dos; 106 s | `d145b_antes_seis.log` |
| `sabotaje_separadores1.sh` entero, antes | `b420203` | 17 de 17, sale 0, 364 s | `d145b_antes_separadores1.log` |
| `sabotaje_maria9.sh` entero, antes | `b420203` | 1 `ROJO` y `PATRON NO ENCONTRADO`, sale 1, 12 s (D191) | `d145b_antes_maria9.log` |
| seis corridas de `maria9` y `separadores1` | `08edd63` | 6 de 6 verdes en las dos; seis IPs `10.x` distintas con cuenta 1 cada una; 52 s | `d145b_verde_seis.log` |
| `validacion1.sh` entero | `08edd63` | BASE en verde, 7 `ROJO`, `FALLAS=0`, sale 0, 134 s | `d145b_verde_validacion1.log` |
| `org1b.sh` entero | `08edd63` | 7 `ROJO`, «sabotajes sin rojo: 0», sale 0, 23 s | `d145b_verde_org1b.log` |
| `sabotaje_separadores1.sh` entero | `08edd63` | 17 de 17, sale 0, 377 s | `d145b_verde_separadores1.log` |
| `node --check` de los cinco archivos | árbol de `08edd63` | sin errores | — |

Las puertas corrieron sobre `08edd63`, antes de traer tu rama. El `merge`
(`83a0bb7`) suma sólo `docs/pm/` y `scripts/testing/conexiones1_natural.py`,
de la Técnica; no volví a correr nada sobre él.

`validacion1.sh` y `org1b.sh` también corrieron enteros y limpios sobre
`b420203` (7 de 7 cada uno, 134 s y 22 s). Los registros están en mi carpeta
de trabajo de la sesión, no en el repositorio. Cada guion corrió una sola
vez sobre cada SHA.

chequeo-6, entero:

```
chequeo-6 46959d7..08edd63: avisos para mirar, no un veredicto
producto +0/−0
arnés +12/−4
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Qué toqué y qué no

El límite es por IP y vive en la base (`registro:h:{ip}`, más de 5 por hora;
`registro:d:{ip}`, más de 20 por día). Un guion sólo lo alcanza si registra
seis veces contra la misma base.

| guion | base | registros por base | header |
|---|---|---|---|
| `validacion1.sh` | una para todo | 8 (base + 7) | **sí** |
| `org1b.sh` | una para todo | hasta 2 por corrida, 9 corridas | **sí** |
| `sabotaje_maria9.sh` | una para todo | 5 | **sí** |
| `sabotaje_separadores1.sh` | una para todo | 4 | **sí** |
| `csrf1.sh`, `csrf2.sh` | nueva en cada corrida de pantalla | 1 | no |
| `cobro_corte1.sh` | nueva en cada corrida de pantalla | 1 | no |
| `sesion1.sh` | una por puerto, y el puerto es nuevo en cada corrida | 1 | no |
| `orden1b.sh` | nueva en cada corrida; usa `pantalla_orden1.js`, de la Técnica, que ya lo lleva | — | no |
| arneses en proceso (`*_postgres.py`, `*_motores.py`) | — | apagan el limitador, mandan su header o crean su base | no |

`abuso1` sigue con una sola IP: no lo toqué.

## Revisión

| quién | modelo y esfuerzo | sobre | qué encontró | qué hice |
|---|---|---|---|---|
| adversario | Sonnet, medio | `b420203` | Ningún defecto en el diff. Leyó, no corrió nada. Baja: `maria9` queda en 5 de 5 y no mira la respuesta del registro | Ampliado en `08edd63` |
| `/code-review high` | Fable (heredado), alto | `46959d7..b420203` | 4, ninguno de corrección: (1) `maria9` sin margen y el diff más angosto que el pedido; (2) `TRUSTED_PROXY_HOPS` sin fijar; (3) `ipNueva` copiada 8 veces; (4) en `org1b` el header en todo el contexto | (1) y (3) arreglados en `08edd63` y D190; (2) queda como riesgo; (4) queda, supuesto 3 |
| adversario | Sonnet, medio | `b420203..08edd63` | Ningún defecto. Leyó y corrió `node --check`; no corrió guiones. Miró que el `require` resuelva desde el worktree, que todo registro de las cuatro pantallas lleve el header y que ningún sabotaje tenga ancla en las pantallas (esto último con `grep`, sin leer cada sabotaje). Baja: las seis copias que quedan | D190 |

## No corrido

- La suite de pytest y `compileall`: el cambio son cuatro pantallas de
  navegador y un módulo de tres líneas que pytest no importa; no hay
  producto tocado.
- `smoke_friccion.sh`, `ataque_aislamiento.sh`, `/security-review`: no hay
  backend, datos, sesión ni permisos tocados.
- `sabotaje_maria9.sh` sobre `08edd63`: muere antes de llegar a la pantalla
  (D191), así que no mediría este cambio.
- Los guiones de la tabla que no llevan el header: su clasificación sale de
  leerlos. `sesion1.sh` corrió entero en D149 (39 `ROJO`, sin 429).

## Riesgos

- Si alguien exporta `TRUSTED_PROXY_HOPS=0` en la consola donde corre estos
  guiones, el header deja de contar y el 429 vuelve. Ningún guion lo fija,
  tampoco los de la Técnica. No lo fijé: el caso es rebuscado y la falla se
  ve (`no se pudo registrar: 429`), salvo en `maria9` y `separadores1`, que
  no miran la respuesta del registro.
- La IP sale al azar entre 16,7 millones y se usan menos de 20 por base.
- `org1b` manda `X-Forwarded-For` en todos los pedidos de sus contextos sin
  sesión. Si mañana `/api/invitations/<token>` tiene límite por IP, este
  arnés no lo va a ver.
- Quedan dos formas de lo mismo hasta que se resuelva D190: seis pantallas
  con la función copiada y cuatro que la toman del módulo.

## Archivos de producto tocados

Ninguno. Sobre el aviso de la subida pública de PDF: sigo sin nada abierto
en esa ruta ni en esa dependencia.

## D167

Este informe cita los registros por nombre y no los copia, salvo los rojos.

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn, cabeza 0a50bcb, integrada en 83a0bb7), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. D149 aceptada (D168 b, D169 a). D145 (a) entregado en 08edd63 (informe en el commit siguiente al merge 83a0bb7), esperando veredicto; abiertas D190 (ipNueva copiada en seis pantallas de la Técnica) y D191 (sabotaje_maria9.sh no corre entero por anclas viejas). No hay pieza marcada «apenas entregues»: después de entregar no arranco nada hasta que la PM escriba. Próxima D libre: D192. Los detalles están en PARA-PM-2.md: el resumen los cita, no los copia. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; las Devs no usan el consejero.
