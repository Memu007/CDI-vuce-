# Reproducción de NAVEGADOR (2026-11-13)

Pieza de la Dev técnica: las 31 pantallas abren el navegador de una sola
forma, `chromium.launch()`, y nadie lee `CHROMIUM`. Entregada en `9059c696`
(arnés `740eac45`). Base `25e13c44`. Diff fuera de `docs/pm`: tres
`pantalla_*.js` (una línea cada una), `correr_pantallas.sh` y
`sabotajes/cliente1.sh`. `chequeo-6 25e13c44 740eac45`: igual al informe
(producto +0/−0, arnés +6/−7, historia vacía, 0 avisos).

Corrido por la PM sobre `740eac45`, con `env -u DATABASE_URL -u ENVIRONMENT`.

| qué | salida |
|---|---|
| `grep -ho 'chromium.launch([^;]*' scripts/testing/*.js \| sort \| uniq -c` | `31 chromium.launch()` |
| `grep -rn CHROMIUM scripts/` | vacío |
| negativo mío: `git grep -n "pw-browsers\|executablePath" 740eac45` fuera de `docs` | vacío |
| `correr_pantallas.sh` con las tres | `verde borrador1 rc=0` · `verde cliente1 rc=0` · `verde destino1 rc=0` · `resumen: 3 verdes, 0 rojas` |
| `sabotajes/cliente1.sh 740eac45` | 34 `ROJO`, rc=0 (la línea final no la capturé) |

**No corrido por la PM:** las otras 28 pantallas (no cambiaron) y adversarios
(la pieza es del arnés, sin producto).

`CHROMIUM` fuera de `scripts/` aparece sólo en `docs/pm` (la tarea en
`PARA-DEV.md` y un ítem de `COLA-LIMPIEZA.md`, que sale en el commit del
veredicto).
