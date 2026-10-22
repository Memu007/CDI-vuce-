# QA independiente EXCEL-2 XML

SHA producto/tests 7f3deb3; final 04e1d003fce518a754909e8de5cf56ee22365ae2 sólo docs posterior.

32 focales passed,81 deselected,3warnings,1.10s; exit0. Log focals.log.

Checks propios en direct_checks.py/direct-checks.log: IV256/IW257, entidad hex, lowercase, namespace, máximo varias celdas, salida temprana con colaXMLinválida lejana, malformed bajo tope, fuente cerrada normal/error/salida temprana. Exit0.

Medición segura ejecutada memory_check.py (tracemalloc sólo parser):100000 rows,600046bytes XML,peak8.15MiB,0.41s;500000rows,3000046bytes XML,peak38.69MiB,2.13s. clear conserva referencias a nodos vacíos hasta cerrar padre. Comentario no conserva árbol demasiado absoluto. No se midió máximo ni concurrencia; no se afirma techo1GB. No se recomienda ampliar producto en esta entrega por esta observación.

Sin productoedits, sin fullsuite, sin pushes, sin datos reales ni llamadas externas.

Pendientes: suite completa y CI sobre candidato integrado exacto; medir memoria/concurrencia del flujo completo antes de afirmar cumplimiento1GB. El guard preexistente limita primera hoja a EXCEL_MAX_PRIMERA_HOJA_MB (defecto10MiB), configurable; la medición actual usa3MBXML, no garantiza techo global de memoria.
