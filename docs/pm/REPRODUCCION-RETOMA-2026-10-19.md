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

## Límites de esta revisión

Python 3.12, entorno con paquetes heredados y pypdf añadido en venv local;
no instalación limpia desde requirements. SQLite temporal, claves
inventadas, servicios externos simulados o localhost:9. No Kit real,
Postgres, suite completa ni pantallas en esta primera revisión.

Subagentes con modelo heredado: Sonnet/Opus y consejero Fable no están
expuestos en este entorno. No se afirma haberlos usado ni se rebaja por eso
la puerta de publicación. No se reactivaron rutinas históricas de Claude.
