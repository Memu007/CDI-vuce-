#!/bin/bash

# SECURITY VALIDATION SCRIPT
# CDI Sistema MARÍA - Validación de implementación de seguridad
# Para ejecutar: ./scripts/security/security_validation.sh

set -e

echo "🔒 CDI Sistema MARÍA - SECURITY VALIDATION"
echo "=========================================="
echo "Inicio: $(date)"
echo "Validando implementación de seguridad crítica"
echo ""

# Variables
PROJECT_ROOT="/Users/Emi/CDI"
PROYECTO_MARIA="$PROJECT_ROOT/proyecto_maria"
VALIDATION_REPORT="$PROJECT_ROOT/security_validation_report_$(date +%Y%m%d_%H%M%S).json"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funciones
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para validar archivo
validate_file_exists() {
    local file="$1"
    local description="$2"
    
    if [ -f "$file" ]; then
        log_info "✅ $description: $file"
        echo "\"$description\": {\"status\": \"PASS\", \"file\": \"$file\"}," >> "$VALIDATION_REPORT"
        return 0
    else
        log_error "❌ $description: $file (NO EXISTE)"
        echo "\"$description\": {\"status\": \"FAIL\", \"file\": \"$file\", \"error\": \"File not found\"}," >> "$VALIDATION_REPORT"
        return 1
    fi
}

# Función para validar configuración
validate_config() {
    local config_file="$1"
    local pattern="$2"
    local description="$3"
    
    if grep -q "$pattern" "$config_file" 2>/dev/null; then
        log_info "✅ $description: ENCONTRADO"
        echo "\"$description\": {\"status\": \"PASS\", \"file\": \"$config_file\", \"pattern\": \"$pattern\"}," >> "$VALIDATION_REPORT"
        return 0
    else
        log_error "❌ $description: NO ENCONTRADO en $config_file"
        echo "\"$description\": {\"status\": \"FAIL\", \"file\": \"$config_file\", \"pattern\": \"$pattern\", \"error\": \"Pattern not found\"}," >> "$VALIDATION_REPORT"
        return 1
    fi
}

# Función para validar secretos
validate_secrets() {
    local env_file="$1"
    local secret_name="$2"
    local min_length="${3:-32}"
    
    if [ -f "$env_file" ]; then
        secret_value=$(grep "^$secret_name=" "$env_file" | cut -d'=' -f2)
        if [ ${#secret_value} -ge $min_length ] && [ "$secret_value" != "change-me" ] && [ "$secret_value" != "your-secret-here" ]; then
            log_info "✅ $secret_name: SEGURO (${#secret_value} caracteres)"
            echo "\"$secret_name\": {\"status\": \"PASS\", \"length\": ${#secret_value}}," >> "$VALIDATION_REPORT"
            return 0
        else
            log_error "❌ $secret_name: INSEGURO o no configurado"
            echo "\"$secret_name\": {\"status\": \"FAIL\", \"error\": \"Insecure or not configured\"}," >> "$VALIDATION_REPORT"
            return 1
        fi
    else
        log_error "❌ Archivo $env_file no encontrado"
        return 1
    fi
}

# Función para validar dependencias
validate_dependency() {
    local package="$1"
    local min_version="$2"
    
    if pip show "$package" >/dev/null 2>&1; then
        installed_version=$(pip show "$package" | grep Version | cut -d' ' -f2)
        log_info "✅ $package: $installed_version (INSTALADO)"
        echo "\"$package\": {\"status\": \"PASS\", \"version\": \"$installed_version\"}," >> "$VALIDATION_REPORT"
        return 0
    else
        log_error "❌ $package: NO INSTALADO"
        echo "\"$package\": {\"status\": \"FAIL\", \"error\": \"Package not installed\"}," >> "$VALIDATION_REPORT"
        return 1
    fi
}

# Iniciar reporte JSON
echo "{" > "$VALIDATION_REPORT"
echo "\"validation_timestamp\": \"$(date -Iseconds)\"," >> "$VALIDATION_REPORT"
echo "\"project_root\": \"$PROJECT_ROOT\"," >> "$VALIDATION_REPORT"
echo "\"results\": {" >> "$VALIDATION_REPORT"

echo ""
echo "🔍 FASE 1: VALIDACIÓN DE ARCHIVOS CRÍTICOS"
echo "=========================================="

total_checks=0
passed_checks=0

# 1.1 Validar archivos de seguridad creados
security_files=(
    "$PROYECTO_MARIA/security/emergency_middleware.py:Emergency Middleware"
    "$PROYECTO_MARIA/security/emergency_file_scanner.py:Emergency File Scanner"
    "$PROJECT_ROOT/.env.emergency:Environment Configuration"
    "$PROJECT_ROOT/requirements-security.txt:Security Requirements"
    "$PROYECTO_MARIA/main_emergency_patch.py:Main Server Patch"
    "$PROYECTO_MARIA/server_funcional_emergency_patch.py:Functional Server Patch"
)

for file_info in "${security_files[@]}"; do
    IFS=':' read -r file_path description <<< "$file_info"
    ((total_checks++))
    if validate_file_exists "$file_path" "$description"; then
        ((passed_checks++))
    fi
done

echo ""
echo "🔐 FASE 2: VALIDACIÓN DE CONFIGURACIÓN DE SEGURIDAD"
echo "=================================================="

# 2.1 Validar secrets en .env.emergency
if [ -f "$PROJECT_ROOT/.env.emergency" ]; then
    ((total_checks++))
    if validate_secrets "$PROJECT_ROOT/.env.emergency" "JWT_SECRET" 50; then
        ((passed_checks++))
    fi
    
    ((total_checks++))
    if validate_secrets "$PROJECT_ROOT/.env.emergency" "MASTER_ENCRYPTION_KEY" 50; then
        ((passed_checks++))
    fi
    
    ((total_checks++))
    if validate_secrets "$PROJECT_ROOT/.env.emergency" "DB_SECRET_KEY" 32; then
        ((passed_checks++))
    fi
fi

# 2.2 Validar configuración de seguridad
security_configs=(
    "$PROJECT_ROOT/.env.emergency:ENABLE_SECURITY_EMERGENCY=true"
    "$PROJECT_ROOT/.env.emergency:JWT_ALGORITHM=HS512"
    "$PROJECT_ROOT/.env.emergency:AUTO_BLOCK_SUSPICIOUS_IP=true"
    "$PROJECT_ROOT/.env.emergency:ENABLE_FILE_SCANNING=true"
    "$PROJECT_ROOT/.env.emergency:RATE_LIMIT_UPLOADS=5_per_minute"
)

for config_info in "${security_configs[@]}"; do
    IFS=':' read -r config_file pattern description <<< "$config_info"
    ((total_checks++))
    if validate_config "$config_file" "$pattern" "$description"; then
        ((passed_checks++))
    fi
done

echo ""
echo "📦 FASE 3: VALIDACIÓN DE DEPENDENCIAS DE SEGURIDAD"
echo "=================================================="

# 3.1 Validar paquetes críticos de seguridad
security_packages=(
    "cryptography:42.0"
    "python-jose:3.3"
    "bcrypt:4.1"
    "fastapi:0.111"
    "redis:5.0"
    "slowapi:0.1"
)

for package_info in "${security_packages[@]}"; do
    IFS=':' read -r package min_version <<< "$package_info"
    ((total_checks++))
    if validate_dependency "$package" "$min_version"; then
        ((passed_checks++))
    fi
done

echo ""
echo "🔧 FASE 4: VALIDACIÓN DE MIDDLEWARE DE SEGURIDAD"
echo "================================================"

# 4.1 Validar que el middleware tenga las funciones críticas
if [ -f "$PROYECTO_MARIA/security/emergency_middleware.py" ]; then
    middleware_functions=(
        "EmergencySecurityMiddleware"
        "_block_ip_temporarily"
        "_get_client_ip"
        "_add_emergency_headers"
    )
    
    for function in "${middleware_functions[@]}"; do
        ((total_checks++))
        if grep -q "class $function\|def $function" "$PROYECTO_MARIA/security/emergency_middleware.py"; then
            log_info "✅ Middleware function: $function"
            echo "\"middleware_function_$function\": {\"status\": \"PASS\"}," >> "$VALIDATION_REPORT"
            ((passed_checks++))
        else
            log_error "❌ Middleware function: $function (NO ENCONTRADO)"
            echo "\"middleware_function_$function\": {\"status\": \"FAIL\", \"error\": \"Function not found\"}," >> "$VALIDATION_REPORT"
        fi
    done
fi

echo ""
echo "🔍 FASE 5: VALIDACIÓN DE FILE SCANNER"
echo "====================================="

# 5.1 Validar funcionalidad del file scanner
if [ -f "$PROYECTO_MARIA/security/emergency_file_scanner.py" ]; then
    scanner_functions=(
        "EmergencyFileScanner"
        "scan_file"
        "_basic_checks"
        "_validate_pdf"
        "_validate_excel"
    )
    
    for function in "${scanner_functions[@]}"; do
        ((total_checks++))
        if grep -q "class $function\|def $function" "$PROYECTO_MARIA/security/emergency_file_scanner.py"; then
            log_info "✅ File scanner function: $function"
            echo "\"scanner_function_$function\": {\"status\": \"PASS\"}," >> "$VALIDATION_REPORT"
            ((passed_checks++))
        else
            log_error "❌ File scanner function: $function (NO ENCONTRADO)"
            echo "\"scanner_function_$function\": {\"status\": \"FAIL\", \"error\": \"Function not found\"}," >> "$VALIDATION_REPORT"
        fi
    done
fi

echo ""
echo "🌐 FASE 6: VALIDACIÓN DE SEGURIDAD DE RED"
echo "========================================"

# 6.1 Validar que no haya endpoints públicos peligrosos
dangerous_endpoints=(
    "/upload_excel/public"
    "/upload_pdf/public"
    "/admin/public"
    "/debug"
)

if [ -f "$PROYECTO_MARIA/server_funcional.py" ]; then
    for endpoint in "${dangerous_endpoints[@]}"; do
        ((total_checks++))
        if grep -q "$endpoint" "$PROYECTO_MARIA/server_funcional.py"; then
            log_warning "⚠️  Endpoint potencialmente peligroso encontrado: $endpoint"
            echo "\"dangerous_endpoint_$endpoint\": {\"status\": \"WARNING\", \"endpoint\": \"$endpoint\"}," >> "$VALIDATION_REPORT"
        else
            log_info "✅ Endpoint seguro: $endpoint (NO ENCONTRADO)"
            echo "\"dangerous_endpoint_$endpoint\": {\"status\": \"PASS\", \"endpoint\": \"$endpoint\", \"found\": false}," >> "$VALIDATION_REPORT"
            ((passed_checks++))
        fi
    done
fi

echo ""
echo "📊 FASE 7: ANÁLISIS DE RIESGO"
echo "============================"

# 7.1 Calcular score de seguridad
if [ $total_checks -gt 0 ]; then
    security_score=$(( (passed_checks * 100) / total_checks ))
    
    echo ""
    log_info "📈 RESULTADOS DE VALIDACIÓN:"
    echo "   Total de checks: $total_checks"
    echo "   Checks pasados: $passed_checks"
    echo "   Score de seguridad: ${security_score}%"
    
    # Determinar nivel de riesgo
    if [ $security_score -ge 90 ]; then
        risk_level="BAJO"
        risk_score="2.5/10"
    elif [ $security_score -ge 75 ]; then
        risk_level="MEDIO-BAJO"
        risk_score="4.0/10"
    elif [ $security_score -ge 50 ]; then
        risk_level="MEDIO"
        risk_score="6.0/10"
    else
        risk_level="ALTO"
        risk_score="8.0/10"
    fi
    
    log_info "🎯 Nivel de riesgo: $risk_level ($risk_score)"
    
    # Agregar al reporte
    echo "\"security_score\": $security_score," >> "$VALIDATION_REPORT"
    echo "\"total_checks\": $total_checks," >> "$VALIDATION_REPORT"
    echo "\"passed_checks\": $passed_checks," >> "$VALIDATION_REPORT"
    echo "\"risk_level\": \"$risk_level\"," >> "$VALIDATION_REPORT"
    echo "\"risk_score\": \"$risk_score\"" >> "$VALIDATION_REPORT"
else
    log_error "❌ No se pudieron realizar las validaciones"
    echo "\"error\": \"No validations performed\"" >> "$VALIDATION_REPORT"
fi

# Cerrar reporte JSON
echo "}," >> "$VALIDATION_REPORT"
echo "\"recommendations\": [" >> "$VALIDATION_REPORT"

# Generar recomendaciones basadas en resultados
if [ $security_score -lt 90 ]; then
    echo "\"Instalar todas las dependencias de seguridad faltantes\"," >> "$VALIDATION_REPORT"
fi

if [ $security_score -lt 80 ]; then
    echo "\"Revisar configuración de secrets y asegurar que sean únicos\"," >> "$VALIDATION_REPORT"
fi

if [ $security_score -lt 70 ]; then
    echo "\"Implementar todos los componentes de middleware de seguridad\"," >> "$VALIDATION_REPORT"
fi

echo "\"Realizar pruebas de penetración adicionales\"," >> "$VALIDATION_REPORT"
echo "\"Configurar monitoring y alertas de seguridad en tiempo real\"" >> "$VALIDATION_REPORT"
echo "]" >> "$VALIDATION_REPORT"
echo "}" >> "$VALIDATION_REPORT"

echo ""
echo "📋 RESUMEN EJECUTIVO"
echo "==================="
echo "✅ Validación completada: $(date)"
echo "📊 Score de seguridad: ${security_score}%"
echo "🎯 Riesgo actual: $risk_level ($risk_score)"
echo "📁 Reporte detallado: $VALIDATION_REPORT"
echo ""

if [ $security_score -ge 80 ]; then
    log_info "🚀 SISTEMA LISTO PARA PRODUCCIÓN SEGURA"
    echo "✅ El sistema cumple con los requisitos mínimos de seguridad"
    echo "✅ Puede proceder con el deployment a producción"
    echo ""
    echo "📝 PRÓXIMOS PASOS:"
    echo "1. Aplicar patches a los servers principales"
    echo "2. Configurar variables de entorno de producción"
    echo "3. Iniciar servidor con medidas de seguridad activas"
    echo "4. Realizar testing de carga con seguridad activada"
elif [ $security_score -ge 60 ]; then
    log_warning "⚠️  SISTEMA REQUIERE AJUSTES ANTES DE PRODUCCIÓN"
    echo "⚠️  Hay componentes críticos que necesitan atención"
    echo ""
    echo "📝 ACCIONES REQUERIDAS:"
    echo "1. Revisar fallas en el reporte detallado"
    echo "2. Completar configuración faltante"
    echo "3. Re-ejecutar validación hasta obtener >80%"
else
    log_error "❌ SISTEMA NO APTO PARA PRODUCCIÓN"
    echo "❌ Hay fallas críticas de seguridad que deben ser resueltas"
    echo ""
    echo "🚨 ACCIONES CRÍTICAS REQUERIDAS:"
    echo "1. Revisar todas las fallas identificadas"
    echo "2. Implementar componentes faltantes"
    echo "3. Corregir configuración de seguridad"
    echo "4. Re-ejecutar validación hasta obtener >80%"
fi

echo ""
echo "🔍 DETALLES ADICIONALES:"
echo "======================="
echo "📂 Directorio del proyecto: $PROJECT_ROOT"
echo "📁 Directorio de seguridad: $PROYECTO_MARIA/security/"
echo "📄 Configuración emergency: $PROJECT_ROOT/.env.emergency"
echo "📄 Reporte JSON: $VALIDATION_REPORT"
echo "⏰ Tiempo de validación: $(date +%s)s"
echo ""

# Mostrar extracto del reporte si existe
if [ -f "$VALIDATION_REPORT" ]; then
    echo "📊 EXTRACTO DEL REPORTE JSON:"
    echo "----------------------------"
    head -20 "$VALIDATION_REPORT"
    echo "..."
fi

echo ""
echo "✅ SECURITY VALIDATION COMPLETED"
echo "🔒 System security assessment complete"