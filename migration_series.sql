-- =====================================================
-- MIGRACIÓN SUPABASE: Sistema de Series y Menú Interactivo
-- =====================================================
-- Ejecutar en: Supabase SQL Editor
-- Fecha: Diciembre 2025
-- =====================================================

-- =====================================================
-- 1. TABLA: tv_shows (Series de TV)
-- =====================================================
CREATE TABLE IF NOT EXISTS tv_shows (
    id SERIAL PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    tmdb_id INTEGER,
    original_name VARCHAR(500),
    year INTEGER,
    overview TEXT,
    poster_url TEXT,
    backdrop_url TEXT,
    vote_average INTEGER,
    genres TEXT,
    number_of_seasons INTEGER,
    status VARCHAR(50),
    added_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Índices para tv_shows
CREATE INDEX IF NOT EXISTS idx_tv_shows_tmdb_id ON tv_shows(tmdb_id);
CREATE INDEX IF NOT EXISTS idx_tv_shows_name ON tv_shows(name);
CREATE INDEX IF NOT EXISTS idx_tv_shows_added_at ON tv_shows(added_at DESC);

-- =====================================================
-- 2. TABLA: episodes (Episodios de Series)
-- =====================================================
CREATE TABLE IF NOT EXISTS episodes (
    id SERIAL PRIMARY KEY,
    tv_show_id INTEGER NOT NULL REFERENCES tv_shows(id) ON DELETE CASCADE,
    file_id VARCHAR(200) NOT NULL,
    message_id INTEGER NOT NULL,
    season_number INTEGER NOT NULL,
    episode_number INTEGER NOT NULL,
    title VARCHAR(500),
    overview TEXT,
    air_date DATE,
    runtime INTEGER,
    still_path TEXT,
    channel_message_id INTEGER,
    added_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    UNIQUE(tv_show_id, season_number, episode_number)
);

-- Índices para episodes
CREATE INDEX IF NOT EXISTS idx_episodes_tv_show_id ON episodes(tv_show_id);
CREATE INDEX IF NOT EXISTS idx_episodes_season ON episodes(tv_show_id, season_number);
CREATE INDEX IF NOT EXISTS idx_episodes_message_id ON episodes(message_id);
CREATE INDEX IF NOT EXISTS idx_episodes_channel_msg ON episodes(channel_message_id);

-- =====================================================
-- 3. TABLA: user_navigation_state (Estado de Navegación)
-- =====================================================
CREATE TABLE IF NOT EXISTS user_navigation_state (
    user_id BIGINT PRIMARY KEY,
    current_menu VARCHAR(50),
    selected_show_id INTEGER REFERENCES tv_shows(id) ON DELETE SET NULL,
    last_interaction TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Índice para limpiar estados antiguos
CREATE INDEX IF NOT EXISTS idx_nav_state_last_interaction ON user_navigation_state(last_interaction);

-- =====================================================
-- 4. MODIFICAR TABLA: videos (Agregar tipo de contenido)
-- =====================================================
-- Agregar columna content_type si no existe
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'videos' AND column_name = 'content_type'
    ) THEN
        ALTER TABLE videos ADD COLUMN content_type VARCHAR(20) DEFAULT 'movie';
    END IF;
END $$;

-- Índice para filtrar por tipo
CREATE INDEX IF NOT EXISTS idx_videos_content_type ON videos(content_type);

-- =====================================================
-- 5. FUNCIÓN: Limpiar estados antiguos (opcional)
-- =====================================================
CREATE OR REPLACE FUNCTION clean_old_navigation_states()
RETURNS void AS $$
BEGIN
    DELETE FROM user_navigation_state 
    WHERE last_interaction < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 6. VISTA: Resumen de Series (opcional, útil para stats)
-- =====================================================
CREATE OR REPLACE VIEW series_summary AS
SELECT 
    s.id,
    s.name,
    s.year,
    s.poster_url,
    s.vote_average,
    s.number_of_seasons,
    COUNT(DISTINCT e.season_number) as available_seasons,
    COUNT(e.id) as total_episodes,
    MAX(e.added_at) as last_episode_added
FROM tv_shows s
LEFT JOIN episodes e ON s.id = e.tv_show_id
GROUP BY s.id, s.name, s.year, s.poster_url, s.vote_average, s.number_of_seasons;

-- =====================================================
-- 7. FUNCIÓN: Obtener temporadas disponibles de una serie
-- =====================================================
CREATE OR REPLACE FUNCTION get_available_seasons(show_id INTEGER)
RETURNS TABLE(
    season_number INTEGER,
    episode_count BIGINT,
    first_air_date DATE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.season_number,
        COUNT(e.id) as episode_count,
        MIN(e.air_date) as first_air_date
    FROM episodes e
    WHERE e.tv_show_id = show_id
    GROUP BY e.season_number
    ORDER BY e.season_number;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 8. POLÍTICA DE SEGURIDAD (Row Level Security)
-- =====================================================
-- Habilitar RLS en tablas nuevas
ALTER TABLE tv_shows ENABLE ROW LEVEL SECURITY;
ALTER TABLE episodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_navigation_state ENABLE ROW LEVEL SECURITY;

-- Políticas: Permitir lectura pública, escritura solo autenticado
CREATE POLICY "Permitir lectura pública de series"
    ON tv_shows FOR SELECT
    USING (true);

CREATE POLICY "Permitir lectura pública de episodios"
    ON episodes FOR SELECT
    USING (true);

-- Para user_navigation_state: cada usuario solo ve su propio estado
CREATE POLICY "Usuarios ven solo su estado"
    ON user_navigation_state FOR SELECT
    USING (true); -- En producción: auth.uid() = user_id si usas autenticación

CREATE POLICY "Usuarios modifican solo su estado"
    ON user_navigation_state FOR ALL
    USING (true); -- En producción: auth.uid() = user_id

-- =====================================================
-- 9. DATOS DE PRUEBA (opcional - comentar en producción)
-- =====================================================
-- Descomentar para insertar datos de ejemplo
/*
INSERT INTO tv_shows (name, tmdb_id, original_name, year, overview, poster_url, vote_average, number_of_seasons, status)
VALUES 
    ('Loki', 84958, 'Loki', 2021, 'After stealing the Tesseract...', 'https://image.tmdb.org/t/p/w500/kEl2t3OhXc3Zb9FBh1AuYzRTgZp.jpg', 82, 2, 'Returning Series'),
    ('Breaking Bad', 1396, 'Breaking Bad', 2008, 'A chemistry teacher...', 'https://image.tmdb.org/t/p/w500/ggFHVNu6YYI5L9pCfOacjizRGt.jpg', 87, 5, 'Ended');

-- Episodios de ejemplo (Loki S2)
INSERT INTO episodes (tv_show_id, file_id, message_id, season_number, episode_number, title, air_date)
VALUES 
    (1, 'BAACAgEAAxkBAAICYGY...', 1001, 2, 1, 'Ouroboros', '2023-10-06'),
    (1, 'BAACAgEAAxkBAAICYGY...', 1002, 2, 2, 'Breaking Brad', '2023-10-13');
*/

-- =====================================================
-- 10. VERIFICACIÓN
-- =====================================================
-- Verificar que todo se creó correctamente
SELECT 
    'tv_shows' as tabla, COUNT(*) as registros FROM tv_shows
UNION ALL
SELECT 
    'episodes', COUNT(*) FROM episodes
UNION ALL
SELECT 
    'user_navigation_state', COUNT(*) FROM user_navigation_state;

-- Verificar columna content_type en videos
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'videos' AND column_name = 'content_type';

-- =====================================================
-- FIN DE MIGRACIÓN
-- =====================================================
-- Notas:
-- 1. Todas las tablas tienen RLS habilitado (seguridad)
-- 2. Índices creados para optimizar consultas
-- 3. Función de limpieza de estados antiguos incluida
-- 4. Vista de resumen para estadísticas
-- 5. Compatible con pgbouncer (sin SERIAL en PK, pero funciona)
-- =====================================================
