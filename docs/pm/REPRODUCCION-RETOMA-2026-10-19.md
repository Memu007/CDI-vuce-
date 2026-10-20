# Retoma PM — 2026-10-19

Emi pidió continuar el plan con subagentes. Base PM `99f3625`; publicado en
Git `a9b03cf`; ramas Dev conservadas `d22ff1a` y `dfb6d24`. Se consultaron
las ramas remotas y los informes desde sus propias ramas. No se verificó
un despliegue nuevo ni se consultó la base de producción.

## MARIA-5d: devolución sobre d22ff1a

La revisión independiente del subagente ejecutó 65 focales de MARIA-5d,
peso Excel y devolución (verdes) y 68 de generador/subítems (verdes).
Esto no equivale a suite completa ni a comparación íntegra de todos los
archivos de referencia.

La PM leyó el código y repitió la prueba HTTP sintética siguiente en un
checkout aislado del mismo SHA:

```python
@pytest.mark.parametrize("columna", [
    "Peso bruto unit (kg)", "Gross weight unit (kg)", "Unit gross weight",
])
def test_pm_bruto_unitario_con_unidad_de_medida(auth_override, client, columna):
    data = _subir(client, [columna], [3])  # helper: cantidad 10
    assert data["items"][0]["peso_unitario"] == pytest.approx(3)
```

Resultado PM: **3 failed**, todos `0.3 != 3`. Además el aviso afirma que
el bruto es de toda la línea y se dividió. `_bruto_de_una_unidad`,
`proyecto_maria/main.py:5119-5122`, normaliza `unit (kg)` a `unitkg`, pero la
expresión sólo reconoce `unit` al final o junto a `weight`. El caso con
`Unit gross weight` tampoco coincide.

Veredicto: **vuelve**, dentro de la tarea ya aprobada. Consigna y límites
en `PARA-DEV-2.md`, «Retoma 2026-10-19». No integrar ni publicar hasta una
reentrega con pruebas discriminantes y revisión independiente.

## Dev 1: recepción pendiente

- GUARDAR-1 ya está publicado en `a9b03cf`.
- EXCEL-2, `c2f8063`, y GUARDAR-2, `2d930c5`, son candidatos hermanos sobre
  `1cdfe49`. No se toma la punta de Dev 1 como una entrega conjunta.
- El `PARA-PM.md` conservado entrega GUARDAR-1 y dice D32 abierta; Git y
  `DECISIONS.md` demuestran que esa D ya se resolvió como (b), sin migración.
- No se reinventa ninguna de las dos piezas ni se heredan los verdes de
  otra entrega. Falta cerrar evidencia sobre sus SHA exactos.

## Incidente de documento/operación

Hipótesis auditada con dobles locales y datos inventados: el lector supone
factura comercial de importación, descarta metadata de tipo documental y
la v2 siempre llama al generador de importación. Una destinación EC02
puede alcanzar ese generador y conservar el indicador `I` de importación.
Mezcla entre dos documentos: **no demostrada**. El camino normal de subida
reemplaza operación e ítems; faltan los casos A→B y error/reintento.

La revisión no constituye autorización para implementar exportación.
`DECISIONS.md` deja v1/exportación fuera del roadmap. Próxima propuesta
mínima: identificar/rechazar documentos no admitidos y frenar EC* en la
ruta de importación, sin generar TXT. Requiere delimitar la cobertura de
clasificación y su criterio de ambigüedad; no hacer una detección por nombre
de archivo. Exportación completa necesita referencia validada en Kit.

## Reproducción PM del incidente

La PM ejecutó los dos scripts de auditoría sintéticos fuera del repositorio,
con código tomado de `a9b03cf` y `99f3625`. Quedaron conservados en
`docs/pm/herramientas/auditoria_documentos_sinteticos.py` y
`auditoria_generador_sintetico.py` (sólo dobles locales y datos inventados).
Desde la raíz, `python3 docs/pm/herramientas/<script>.py .` repite la prueba.
Ambos terminaron en 0 y confirmaron:

- `process_pdf` pierde clase documental, destinación y aduana devueltas por
  el doble local, y acepta fecha, rol y peso sin contraste documental.
- El generador, con EC02 explícita, conserva `CDDTIMPEXP=I` en ambos SHA.
- El lector no puede, con esa normalización, distinguir una fecha de
  oficialización que el modelo asignó a factura, ni el rol del despachante.

Esto prueba el tratamiento del resultado simulado, no atribuye a Gemini una
respuesta concreta del archivo privado. No se usa la normativa de interfaz
abrogada encontrada online como prueba de formato vigente.

## GUARDAR-2: verificación exploratoria, no aceptación

Sobre el candidato `2d930c5`, la revisión ejecutó 17 casos (16 de
`test_guardar2.py` y la regresión de memoria cliente): todos verdes. Otra
corrida de 18 casos agregó conservación de SIM completa del cliente y
separación entre dos cuentas/catálogos con iguales nombres: todos verdes,
con conexiones externas bloqueadas por socket. No se suman ambas corridas
como si fueran casos distintos.

Un harness manual fuera de pytest no terminó y se interrumpió; no se cuenta
como verde. Las comprobaciones adicionales sí terminaron dentro de pytest
con tope de 25 s. Faltan Postgres descartable, sabotajes, suite, e2e y cierre
del informe Dev. No se integra GUARDAR-2 ni se reabre D32.

## Límites de esta revisión

Python 3.12, entorno con paquetes heredados y pypdf añadido en venv local;
no instalación limpia desde requirements. SQLite temporal, claves
inventadas, servicios externos simulados o localhost:9. No Kit real,
Postgres, suite completa ni pantallas en esta primera revisión.

Subagentes con modelo heredado: Sonnet/Opus y consejero Fable no están
expuestos en este entorno. No se afirma haberlos usado ni se rebaja por eso
la puerta de publicación. No se reactivaron rutinas históricas de Claude.

## Reentrega MARIA-5d, todavía candidata

- Producto inicial `b3fd518`: 146 focales verdes en revisión PM independiente
  sobre `000a74d`. Una segunda revisión encontró un borde nuevo con `Unit
  gross weight per line` y `Unit gross weight line`: `d22ff1a` los trataba
  como totales y el nuevo substring los convertía en unitarios.
- La PM reprodujo por AST ambos cambios y devolvió la pieza. El arreglo
  mínimo `8b8b789` conserva también las líneas en inglés. Pruebas `67d18a8`
  y negativo discriminante `eff9dea`.
- Sobre `eff9dea`, PM repitió las seis baterías focales: **148 passed,
  3 warnings in 10.84s**, proceso terminado con 0. Incluyen subida automática,
  mapeo guardado, generación HTTP, 10 × 3 = 30 kg, totales/plurales/línea,
  precedencia neto y referencias del generador/subítems.
- Otro subagente verificó por AST del SHA exacto 14 clasificaciones y 10
  órdenes de selección, también con mapeo guardado. Sin otro defecto
  concreto dentro del alcance. No reemplaza una prueba de pantalla.
- La primera suite sobre `000a74d` fue interrumpida al devolver la pieza:
  no cuenta como suite pasada. Estado final de suite/sabotajes y puertas
  pendientes: se registra al recibir el informe Dev del candidato exacto.
- No se acepta ni publica todavía. La modificación de peso es de Excel;
  **no corrige el incidente del despacho EC02 ni certifica exportación**.
