# 📋 Documentación MARIA - Sistema AFIP

## Resumen Ejecutivo

**MARIA (SIM)** = Sistema Informático Malvina de AFIP para declaraciones aduaneras.

### Formato del Archivo TXT

```
[DDT]     → Cabecera de la declaración
[CPL]     → Campos complementarios (múltiples)
[DVD]     → Documentos vinculados (factura)
[ART]     → Artículos/Items (múltiples)
[SBT]     → Sub-items (opcional)
```

---

## Estructura del NCM en MARIA

### Campo IESPNCE (Posición Arancelaria)

El NCM en MARIA tiene **11 dígitos + 1 letra**:

```
Ejemplo: 8479.89.99.900H
         ↑↑↑↑ ↑↑ ↑↑ ↑↑↑↑
         │    │  │  │  └── Letra control (H, Z, etc.)
         │    │  │  └── Sufijo valor (900 = genérico)
         │    │  └── Subpartida regional (dígitos 7-8)
         │    └── Subpartida SA (dígitos 5-6)
         └── Partida SA (dígitos 1-4)
```

| Parte | Dígitos | Descripción |
|-------|---------|-------------|
| Capítulo | 1-2 | Sistema Armonizado (84 = máquinas) |
| Partida | 3-4 | Categoría específica |
| Subpartida SA | 5-6 | Clasificación internacional |
| Subpartida NCM | 7-8 | Clasificación MERCOSUR |
| Sufijo Valor | 9-11 | Código adicional AFIP (900 = genérico) |
| Letra Control | 12 | Verificador (H, Z, etc.) |

### ¿Por qué aparecen asteriscos (*)?

Los asteriscos indican código **truncado** durante la extracción PDF.
- `T718108*` → Código incompleto

---

## Secciones del TXT MARIA

### [DDT] - Cabecera

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| IESPNCE | NCM completo | `8479.89.99.900H` |
| MDDTFOB | Monto FOB | `5000.00` |
| MDDTFLE | Flete | `3221.66` |
| MDDTASS | Seguro | `50.00` |
| CDDTINCOTE | Incoterm | `DDP` |

### [ART] - Artículos

| Campo | Descripción |
|-------|-------------|
| IESPNCE | NCM completo (11+1) |
| QARTKGRNET | Peso neto (kg) |
| MARTFOB | Valor FOB item |
| IEXT | Código de parte (opcional) |

---

## Reglas de Validación

| Campo | Obligatorio | Nota |
|-------|-------------|------|
| NCM | ✅ SÍ | AFIP rechaza sin NCM |
| Código Parte | ❌ NO | Opcional, va en IEXT |
| Descripción | ✅ SÍ | Mínimo 10 chars |
| Cantidad | ✅ SÍ | > 0 |
| Valor FOB | ✅ SÍ | > 0 |
| Peso | ✅ SÍ | > 0 |
| Origen | ✅ SÍ | Código país válido |

### NCM: ¿Vacío o Completo?

- **Excel AVG**: NCM puede quedar vacío
- **MARIA TXT**: NCM debe tener 8+ dígitos

---

## Códigos de País INDEC

| Código | País |
|--------|------|
| 200 | Argentina |
| 203 | Brasil |
| 218 | China |
| 212 | USA |
| 217 | Japón |
| 220 | Corea |
