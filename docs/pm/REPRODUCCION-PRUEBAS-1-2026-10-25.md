# Reproducción de PRUEBAS-1 + PA-1b — 2026-10-25

Sobre `e924b29` (base `913d282`). Revisor adversarial Sonnet, esfuerzo alto,
con worktrees propios para cada sabotaje. Todo local y con sintéticos.

**Veredicto: aceptada con nota.** Se integra `e924b29` exactamente, no la
punta de `claude/dev-tecnica`: después de `e924b29` vienen los commits de
EXCEL-3b, que volvieron como EXCEL-3c.

## Lo que se corrió

| Qué | Resultado |
|---|---|
| `excel1.sh` | 36 ROJO, `sabotajes con falla: 0`, rc=0, 11 min 35 s |
| `excel2.sh` | 42 ROJO, `sabotajes con falla: 0`, rc=0, 4 min 48 s (la combinada, cortada a los 90 s) |
| `maria1b.sh` | 34 ROJO, `sabotajes con falla: 0`, rc=0, 10 min 36 s |
| Línea base sin sabotaje (excel1 ×3, excel2, maria1b ×2, pa1_textos) | `302 passed in 79.84s` |
| `test_mapeo_guardado_no_deja_afuera_encabezados_nuevos` con `elegido = g` | la nueva `1 failed`, la de `913d282` `1 passed`: la vieja no distinguía |
| `e2e_rerun.sh` | VERDE / ROJO («Node is either not clickable…») / VERDE, `mediciones con falla: 0` |
| `foco_cliente1.sh`, N=5 M=30 | ver nota 1 |

Además:
- las cinco aperturas de `cxForm` (`pantalla_cliente1.js:29`, `:75`, `:133`,
  `:155`, `:177`) pasan por `formularioListo()`;
- `formularioListo()` tiene tope de 10 s y la espera de la e2e, de 15 s:
  ninguna puede colgar;
- `landing.html:130` pasa de NCM a PA SIM, con su prueba y su caso en
  `pa1.sh`;
- no se borró ninguna prueba.

## Notas

1. **`foco_cliente1.sh` no es determinista como puerta.** Sobre código
   sano dio «sin espera … 0 fallas de 30 … VERDE | … esta medición no
   distingue … mediciones con falla: 1 rc=1». Que la variante sin espera
   falle o no es azar, así que su rc también. Va a CLIENTE-1b: o la
   medición «no distingue» pasa a ser sólo informativa (sin rc=1), o M
   sube hasta que el rojo sin espera sea seguro.
2. `e2e_maria.js:52-67` (`entrarAValidacion`) supone exactamente dos
   respuestas de avisos. Es frágil, pero no da un verde falso. La Dev lo
   declaró. Queda como riesgo.
3. El corte de 90 s de `excel2.sh` esconde un colgado posterior al FAILED
   esperado. Es aceptable: si el FAILED no sale antes del corte, cuenta
   como falla («ROJO?»).

## Lo que no se corrió

- `foco_cliente1.sh` con N=100 (unos 25 min).
- La e2e normal 30 veces.
- `cliente1.sh` y `pa1.sh` completos.
- La suite completa.
