-- ============================================================================
-- Índices de Performance para CDI Sistema MARÍA
-- ============================================================================
-- Ejecutar en PostgreSQL después de crear las tablas.
-- Estos índices optimizan queries frecuentes para 2000+ usuarios.
--
-- Uso:
--   psql -d maria_db -f add_indexes.sql
--   O via docker-compose: se copia a /docker-entrypoint-initdb.d/
-- ============================================================================

-- Usuarios: búsqueda por username (login)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username 
    ON users(username);

-- Clientes: búsqueda por email (registro, validación)  
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clients_email 
    ON clients(email);

-- Clientes: filtrar activos
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clients_active 
    ON clients(is_active) WHERE is_active = true;

-- Operaciones: filtrar por cliente (historial)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_operations_client_id 
    ON operations(client_id);

-- Operaciones: ordenar por fecha (últimas primero)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_operations_created_at 
    ON operations(created_at DESC);

-- API Logs: filtrar por endpoint (analytics)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_logs_endpoint 
    ON api_logs(endpoint);

-- API Logs: filtrar por fecha (métricas últimas 24h)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_logs_created_at 
    ON api_logs(created_at DESC);

-- API Logs: filtrar errores (debugging)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_logs_errors 
    ON api_logs(status_code) WHERE status_code >= 400;

-- NCM Notes: búsqueda por cliente + código NCM (autocompletado)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ncm_notes_client_ncm 
    ON ncm_notes(client_id, ncm_code);

-- System Backups: último backup por tipo
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_backups_type_date 
    ON system_backups(backup_type, created_at DESC);

-- Client Product History: autocompletado por cliente
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_product_history_client 
    ON client_product_history(client_id, ultima_vez DESC);

-- ============================================================================
-- Índices de texto para búsqueda fuzzy (opcional, requiere pg_trgm)
-- ============================================================================

-- Habilitar extensión para búsqueda fuzzy (ejecutar como superuser)
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Índice GIN para búsqueda fuzzy en descripciones (opcional)
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_product_history_desc_gin 
--     ON client_product_history USING gin (descripcion_normalizada gin_trgm_ops);

-- ============================================================================
-- Verificación de índices creados
-- ============================================================================

-- Ver todos los índices creados:
-- SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'public';
