-- ==================================================
-- SCRIPT SQL PARA SUPABASE - SISTEMA DE ESTADÍSTICAS POR CANAL
-- ==================================================
-- Ejecutar este script en el SQL Editor de Supabase
-- Fecha: 09/01/2026

-- Crear tabla de fuentes de canales
CREATE TABLE IF NOT EXISTS channel_sources (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(100) UNIQUE NOT NULL,
    channel_name VARCHAR(200) NOT NULL,
    channel_url VARCHAR(300),
    description TEXT,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Crear tabla de visitas por canal
CREATE TABLE IF NOT EXISTS channel_visits (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    channel_source_id INTEGER NOT NULL,
    visited_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_new_user BOOLEAN DEFAULT FALSE,
    
    -- Foreign key constraint
    CONSTRAINT fk_channel_source 
        FOREIGN KEY (channel_source_id) 
        REFERENCES channel_sources(id) 
        ON DELETE CASCADE
);

-- ==================================================
-- ÍNDICES PARA MEJORAR RENDIMIENTO
-- ==================================================

-- Índice para búsquedas rápidas por channel_id
CREATE INDEX IF NOT EXISTS idx_channel_sources_channel_id 
    ON channel_sources(channel_id);

-- Índice para canales activos
CREATE INDEX IF NOT EXISTS idx_channel_sources_active 
    ON channel_sources(is_active) 
    WHERE is_active = TRUE;

-- Índice para búsquedas por user_id
CREATE INDEX IF NOT EXISTS idx_channel_visits_user_id 
    ON channel_visits(user_id);

-- Índice para búsquedas por canal
CREATE INDEX IF NOT EXISTS idx_channel_visits_channel_source_id 
    ON channel_visits(channel_source_id);

-- Índice para filtros por fecha
CREATE INDEX IF NOT EXISTS idx_channel_visits_visited_at 
    ON channel_visits(visited_at);

-- Índice compuesto para estadísticas por período
CREATE INDEX IF NOT EXISTS idx_channel_visits_stats 
    ON channel_visits(channel_source_id, visited_at, user_id);

-- Índice para usuarios nuevos
CREATE INDEX IF NOT EXISTS idx_channel_visits_new_users 
    ON channel_visits(is_new_user, visited_at) 
    WHERE is_new_user = TRUE;

-- ==================================================
-- COMENTARIOS DESCRIPTIVOS
-- ==================================================

-- Comentarios para la tabla channel_sources
COMMENT ON TABLE channel_sources IS 'Tabla que almacena los canales fuente para tracking de estadísticas';
COMMENT ON COLUMN channel_sources.channel_id IS 'Identificador único del canal (ej: canal_principal)';
COMMENT ON COLUMN channel_sources.channel_name IS 'Nombre del canal (ej: @mi_canal)';
COMMENT ON COLUMN channel_sources.channel_url IS 'URL del canal de Telegram';
COMMENT ON COLUMN channel_sources.description IS 'Descripción opcional del canal';
COMMENT ON COLUMN channel_sources.added_at IS 'Fecha cuando se agregó el canal al sistema';
COMMENT ON COLUMN channel_sources.is_active IS 'Si el canal está activo para tracking';

-- Comentarios para la tabla channel_visits
COMMENT ON TABLE channel_visits IS 'Registro de todas las visitas desde canales específicos';
COMMENT ON COLUMN channel_visits.user_id IS 'ID del usuario de Telegram que visitó';
COMMENT ON COLUMN channel_visits.channel_source_id IS 'Referencia al canal desde donde vino';
COMMENT ON COLUMN channel_visits.visited_at IS 'Timestamp de la visita';
COMMENT ON COLUMN channel_visits.is_new_user IS 'Si era la primera vez que el usuario usaba el bot';

-- ==================================================
-- PERMISOS Y SEGURIDAD (opcional)
-- ==================================================

-- Si necesitas dar permisos específicos a un usuario/rol:
-- GRANT SELECT, INSERT, UPDATE ON channel_sources TO tu_usuario;
-- GRANT SELECT, INSERT ON channel_visits TO tu_usuario;

-- ==================================================
-- DATOS DE EJEMPLO (opcional - quitar en producción)
-- ==================================================

-- Insertar algunos canales de ejemplo
INSERT INTO channel_sources (channel_id, channel_name, channel_url, description) 
VALUES 
    ('canal_principal', '@mi_canal_principal', 'https://t.me/mi_canal_principal', 'Canal principal de películas'),
    ('canal_series', '@mi_canal_series', 'https://t.me/mi_canal_series', 'Canal dedicado a series'),
    ('canal_anime', '@mi_canal_anime', 'https://t.me/mi_canal_anime', 'Canal de anime y contenido asiático')
ON CONFLICT (channel_id) DO NOTHING;

-- ==================================================
-- CONSULTAS DE VERIFICACIÓN
-- ==================================================

-- Verificar que las tablas se crearon correctamente
SELECT 
    table_name, 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name IN ('channel_sources', 'channel_visits')
ORDER BY table_name, ordinal_position;

-- Verificar que los índices se crearon
SELECT 
    tablename, 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename IN ('channel_sources', 'channel_visits')
ORDER BY tablename, indexname;

-- Contar registros en las nuevas tablas
SELECT 
    'channel_sources' as tabla,
    COUNT(*) as registros
FROM channel_sources
UNION ALL
SELECT 
    'channel_visits' as tabla,
    COUNT(*) as registros  
FROM channel_visits;

-- ==================================================
-- CONSULTAS ÚTILES PARA ESTADÍSTICAS
-- ==================================================

-- Obtener estadísticas de hoy por canal
SELECT 
    cs.channel_name,
    COUNT(cv.id) as total_visitas,
    COUNT(DISTINCT cv.user_id) as usuarios_unicos,
    SUM(CASE WHEN cv.is_new_user THEN 1 ELSE 0 END) as usuarios_nuevos
FROM channel_sources cs
LEFT JOIN channel_visits cv ON cs.id = cv.channel_source_id 
    AND cv.visited_at >= CURRENT_DATE
WHERE cs.is_active = TRUE
GROUP BY cs.id, cs.channel_name
ORDER BY usuarios_unicos DESC;

-- Obtener estadísticas de la última semana
SELECT 
    cs.channel_name,
    COUNT(cv.id) as total_visitas,
    COUNT(DISTINCT cv.user_id) as usuarios_unicos,
    MAX(cv.visited_at) as ultima_visita
FROM channel_sources cs
LEFT JOIN channel_visits cv ON cs.id = cv.channel_source_id 
    AND cv.visited_at >= CURRENT_DATE - INTERVAL '7 days'
WHERE cs.is_active = TRUE
GROUP BY cs.id, cs.channel_name
ORDER BY usuarios_unicos DESC;

-- Estadísticas totales por canal
SELECT 
    cs.channel_name,
    cs.added_at as canal_agregado,
    COUNT(cv.id) as total_visitas_historicas,
    COUNT(DISTINCT cv.user_id) as usuarios_unicos_totales,
    MAX(cv.visited_at) as ultima_visita,
    EXTRACT(days FROM NOW() - cs.added_at) as dias_activo
FROM channel_sources cs
LEFT JOIN channel_visits cv ON cs.id = cv.channel_source_id
WHERE cs.is_active = TRUE
GROUP BY cs.id, cs.channel_name, cs.added_at
ORDER BY usuarios_unicos_totales DESC;

-- ==================================================
-- FINALIZACIÓN
-- ==================================================

-- Confirmar que todo está listo
SELECT 'Sistema de estadísticas por canal instalado correctamente' as resultado;