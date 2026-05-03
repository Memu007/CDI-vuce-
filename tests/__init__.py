"""
Tests para el proyecto MARIA - Optimizador de Despachos Aduaneros

Este paquete contiene tests unitarios y de integración para los componentes críticos:
- DataStore unificado (PostgreSQL/In-Memory)
- Router de PDF (extracción con Gemini API)
- Router de clientes (CRUD y gestion)
- Validaciones de negocio (reglas críticas)

Ejecutar tests:
    pytest tests/ -v
    pytest tests/ --cov=proyecto_maria --cov-report=html

Cobertura objetivo: 60%+
"""
