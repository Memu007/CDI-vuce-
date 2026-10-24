# Reproducción de CLIENTE-1 — 2026-10-24

PM principal. Entrega de la Dev técnica: informe `c402bcb` (rama
`claude/dev-tecnica`), producto `fbc006a` + `12ff9b6`, pruebas `9c53522` +
`b0c920b`. Base: `cb98105`.

**Veredicto: aceptada.** Integrada a la rama de la PM por SHA (`c402bcb`); el
producto integrado es idéntico al revisado. D3: (a), pieza chica que se
entrega con PA-1.

Fuera de `docs/`, el diff `cb98105..c402bcb` toca sólo `CHANGELOG.md`, tres
archivos de pantalla (`dashboard_v2.html`, `clientes.js`, `app_v2.js`) y dos
de prueba. No toca API, modelo de datos, plata, sesión ni permisos.

## Lo corrido

Worktree limpio en `b0c920b` levantado con `docs/pm/herramientas/levantar.sh`
(puerto 8852, base de datos de prueba). Clientes inventados.

| Qué | Resultado |
|---|---|
| Sabotajes `scripts/testing/sabotajes/cliente1.sh` | 14 `ROJO` por el motivo esperado, «sabotajes sin rojo: 0», exit 0 |
| Prueba de pantalla de la Dev `pantalla_cliente1.js` | 4 `OK`, «PANTALLA CLIENTE-1 OK», exit 0 |
| Negativos de la PM (`pm_cliente1.js`, fuera del repo) | abajo, exit 0 |
| Focales `test_maria1b_controles.py` | 37 passed |
| `compileall proyecto_maria` | ok |
| Captura del alta | los cuatro datos arriba con «lo pide el MARIA», la frase de abajo, email y teléfono en «Más datos». El `mm/dd/yyyy` del campo de fecha es el idioma del navegador de prueba, no de la pantalla |
| Estilo del aviso | `app_v2.css:789`: `.toast.is-warning .toast-icon` con el color de advertencia; el aviso se distingue del verde |

### Negativos de la PM, salida exacta

```
1 espacios: clase=toast is-warning | ! Cliente creado PM Inventado Espacios SA. Faltan para el MARIA: domicilio.
2 abre edición: cuit=30-71234567-1 fecha=2015-03-01 masDatosAbierto=true
2 sin CUIT: clase=toast is-warning | ! Cliente actualizado PM Inventado Completo SA. Faltan para el MARIA: CUIT.
2 guardado: cuit="" fecha="2015-03-01"
3 campo fecha al editar: ""
3 aviso: ! Cliente actualizado PM Inventado Fecha SA. Faltan para el MARIA: inicio de actividad.
3 fecha después de guardar: ""
4 cuit corto guardado=false modalAbierto=true
FIN
```

1. Domicilio de sólo espacios: avisa que falta. Correcto.
2. Editar un cliente completo y borrarle el CUIT: avisa CUIT y no toca la
   fecha. Correcto. `masDatosAbierto=true` sale de los valores por defecto
   que pone la API (origen o moneda), no de esta pieza: cosmético, previo.
3. D3: una fecha guardada `01/03/2015` (entra por la API) se ve vacía al
   editar y se pierde al guardar. Ya pasaba antes. **Matiz:** la Dev dijo
   «sin aviso», pero sí avisa «Faltan… inicio de actividad»; lo que no dice
   es que había una fecha. Se arregla igual (D3 a).
4. CUIT de tres dígitos: no guarda y el formulario queda abierto. Correcto.

### Suite completa

Corrida por la PM en `b0c920b` (`--no-cov --timeout=120`): ver
«Suite de la PM» al final. La de la Dev, en el mismo SHA: `1757 passed, 102
skipped, 2 xfailed`.

## Hallazgo fuera de la pieza: la fecha va al TXT en otro formato

Leído en el código, no generado (el generador pide sufijo SBT, peso y demás
antes de llegar ahí, y un TXT completo no aportaba más):

- El alta guarda la fecha como `AAAA-MM-DD` (campo de fecha del navegador).
- `review.js` y `finalize.js` la pasan tal cual a
  `comprador_fecha_inic_activ`.
- `maria_generator.py` (bloque 6, `FECHA INIC.ACTIV`) la escribe en `MCPL`
  sin convertir.
- Los dos golden (`tests/fixtures/maria_golden*_anon.TXT`) tienen
  `DD/MM/AAAA`.

Con un cliente cargado desde la pantalla, el TXT sale con `MCPL=2015-03-01`.
No es de CLIENTE-1: el campo ya era de fecha antes, en «Más datos». Ahora se
usa más. Va a MARIA-7 como punto 9 (Dev MARIA). `controles_maria.py` sólo
limpia el texto de la fecha, no mira su formato.

## Lo que no corrió la PM

- e2e de la CI: lo corrió la Dev en `b0c920b` («E2E MARIA OK»). La pieza no
  toca el flujo del TXT.
- Subagente adversario propio: no. Es una pieza de pantalla sin plata,
  sesión, permisos ni datos. La Dev ya corrió un adversario Sonnet alto y
  `/code-review high`, con XSS probado, y mis cuatro negativos atacan otros
  bordes.
- `/security-review`: no. El texto nuevo va con `textContent`.

## Riesgos que quedan (de la Dev, aceptados)

- El aviso dura 4 s, como todos.
- Un CUIT de 11 dígitos con verificador malo no se avisa en el alta (lo frena
  el TXT).
- La lista de lo que pide el MARIA está escrita a mano en el alta.
- El alta rápida desde la revisión puede avisar «falta domicilio» aunque la
  carátula lo traiga.

## Consejero

Consultado antes del veredicto. Pidió:

- mirar que el aviso se vea distinto (hecho: tiene estilo propio);
- corregir el «sin aviso» de D3 (hecho);
- mirar si el TXT controla la fecha (no la controla, y además sale en otro
  formato: va a MARIA-7);
- correr la suite;
- pedir la prueba de D3 por la familia;
- avisar a la Dev que EXCEL-3 y D1 ya estaban respondidas.

## Suite de la PM

Corrida en `b0c920b` (worktree limpio, `--no-cov --timeout=120`), terminada
después del commit del veredicto:

```
==== 1757 passed, 102 skipped, 2 xfailed, 23 warnings in 241.11s (0:04:01) =====
fin: b0c920b
exit 0
```

Igual a la de la Dev en el mismo SHA.
