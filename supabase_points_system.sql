-- ===========================================
-- SISTEMA DE PUNTOS/TOKENS PARA VIDEOS SIN ANUNCIOS
-- ===========================================
-- Fecha: Diciembre 2025
-- Versión: 1.0
-- Descripción: Sistema de economía de puntos basado en referidos
-- ===========================================

-- ===========================================
-- TABLA: user_points
-- Descripción: Balance de puntos por usuario
-- ===========================================
CREATE TABLE IF NOT EXISTS user_points (
    user_id BIGINT PRIMARY KEY,
    points_balance INTEGER DEFAULT 0 CHECK (points_balance >= 0),
    total_earned INTEGER DEFAULT 0 CHECK (total_earned >= 0),
    total_used INTEGER DEFAULT 0 CHECK (total_used >= 0),
    last_earned_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_balance CHECK (points_balance <= 5), -- Máximo 5 puntos
    CONSTRAINT valid_totals CHECK (total_used <= total_earned)
);

-- Comentarios
COMMENT ON TABLE user_points IS 'Balance de puntos/tokens por usuario para videos sin anuncios';
COMMENT ON COLUMN user_points.user_id IS 'ID de Telegram del usuario';
COMMENT ON COLUMN user_points.points_balance IS 'Puntos disponibles actualmente (máx 5)';
COMMENT ON COLUMN user_points.total_earned IS 'Total de puntos ganados históricamente';
COMMENT ON COLUMN user_points.total_used IS 'Total de puntos usados históricamente';
COMMENT ON COLUMN user_points.last_earned_at IS 'Última vez que ganó puntos';

-- Indexes para performance
CREATE INDEX IF NOT EXISTS idx_user_points_balance ON user_points(points_balance);
CREATE INDEX IF NOT EXISTS idx_user_points_updated ON user_points(updated_at);

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION update_user_points_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_user_points_updated_at
    BEFORE UPDATE ON user_points
    FOR EACH ROW
    EXECUTE FUNCTION update_user_points_updated_at();

-- ===========================================
-- TABLA: referrals
-- Descripción: Sistema de referidos para ganar puntos
-- ===========================================
CREATE TABLE IF NOT EXISTS referrals (
    id SERIAL PRIMARY KEY,
    referrer_id BIGINT NOT NULL, -- Quién invita
    referred_id BIGINT, -- Quién fue invitado (NULL hasta completar)
    referral_code VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'expired', 'cancelled')),
    referral_link TEXT, -- Link completo de referido
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '7 days'),

    -- Constraints
    CONSTRAINT no_self_referral CHECK (referrer_id != referred_id),
    CONSTRAINT valid_dates CHECK (completed_at IS NULL OR completed_at >= created_at),
    CONSTRAINT unique_referral_per_user UNIQUE(referrer_id, referred_id),

    -- Foreign keys (asumiendo que existe tabla users)
    FOREIGN KEY (referrer_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (referred_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Comentarios
COMMENT ON TABLE referrals IS 'Sistema de referidos para ganar puntos';
COMMENT ON COLUMN referrals.referrer_id IS 'Usuario que invita (gana puntos)';
COMMENT ON COLUMN referrals.referred_id IS 'Usuario invitado (NULL hasta completar)';
COMMENT ON COLUMN referrals.referral_code IS 'Código único del referido (hash)';
COMMENT ON COLUMN referrals.status IS 'Estado: pending, completed, expired, cancelled';
COMMENT ON COLUMN referrals.referral_link IS 'Link completo de Telegram para compartir';
COMMENT ON COLUMN referrals.expires_at IS 'Fecha de expiración del referido (7 días)';

-- Indexes para performance
CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referred ON referrals(referred_id);
CREATE INDEX IF NOT EXISTS idx_referrals_code ON referrals(referral_code);
CREATE INDEX IF NOT EXISTS idx_referrals_status ON referrals(status);
CREATE INDEX IF NOT EXISTS idx_referrals_expires ON referrals(expires_at);

-- ===========================================
-- TABLA: points_transactions
-- Descripción: Historial de transacciones de puntos (auditoría)
-- ===========================================
CREATE TABLE IF NOT EXISTS points_transactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('earned', 'used', 'bonus', 'penalty')),
    points_amount INTEGER NOT NULL,
    reason VARCHAR(100), -- 'referral_completed', 'video_watched', etc.
    reference_id INTEGER, -- ID del referido o video relacionado
    balance_before INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Comentarios
COMMENT ON TABLE points_transactions IS 'Historial de transacciones de puntos para auditoría';
COMMENT ON COLUMN points_transactions.transaction_type IS 'Tipo: earned, used, bonus, penalty';
COMMENT ON COLUMN points_transactions.points_amount IS 'Cantidad de puntos (positiva o negativa)';
COMMENT ON COLUMN points_transactions.reason IS 'Razón específica de la transacción';
COMMENT ON COLUMN points_transactions.reference_id IS 'ID de referencia (referido, video, etc.)';

-- Indexes
CREATE INDEX IF NOT EXISTS idx_points_transactions_user ON points_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_points_transactions_type ON points_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_points_transactions_created ON points_transactions(created_at);

-- ===========================================
-- FUNCIONES ÚTILES
-- ===========================================

-- Función para otorgar puntos por referido completado
CREATE OR REPLACE FUNCTION award_referral_points(p_referrer_id BIGINT, p_referred_id BIGINT)
RETURNS INTEGER AS $$
DECLARE
    current_balance INTEGER;
    new_balance INTEGER;
    earned_points INTEGER := 1; -- 1 punto por referido
BEGIN
    -- Verificar que no exceda el límite de 5 puntos
    SELECT points_balance INTO current_balance
    FROM user_points
    WHERE user_id = p_referrer_id;

    IF current_balance IS NULL THEN
        -- Usuario nuevo, crear registro
        INSERT INTO user_points (user_id, points_balance, total_earned)
        VALUES (p_referrer_id, earned_points, earned_points);
        new_balance := earned_points;
    ELSIF current_balance >= 5 THEN
        -- Ya tiene máximo, no otorgar puntos
        RETURN 0;
    ELSE
        -- Otorgar puntos
        new_balance := LEAST(current_balance + earned_points, 5);
        UPDATE user_points
        SET points_balance = new_balance,
            total_earned = total_earned + earned_points,
            last_earned_at = CURRENT_TIMESTAMP
        WHERE user_id = p_referrer_id;
    END IF;

    -- Registrar transacción
    INSERT INTO points_transactions (
        user_id, transaction_type, points_amount, reason,
        reference_id, balance_before, balance_after
    ) VALUES (
        p_referrer_id, 'earned', earned_points, 'referral_completed',
        (SELECT id FROM referrals WHERE referrer_id = p_referrer_id AND referred_id = p_referred_id LIMIT 1),
        COALESCE(current_balance, 0), new_balance
    );

    RETURN earned_points;
END;
$$ LANGUAGE plpgsql;

-- Función para usar puntos
CREATE OR REPLACE FUNCTION use_user_points(p_user_id BIGINT, p_points INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    current_balance INTEGER;
BEGIN
    -- Verificar balance suficiente
    SELECT points_balance INTO current_balance
    FROM user_points
    WHERE user_id = p_user_id;

    IF current_balance IS NULL OR current_balance < p_points THEN
        RETURN FALSE;
    END IF;

    -- Descontar puntos
    UPDATE user_points
    SET points_balance = points_balance - p_points,
        total_used = total_used + p_points
    WHERE user_id = p_user_id;

    -- Registrar transacción
    INSERT INTO points_transactions (
        user_id, transaction_type, points_amount, reason,
        balance_before, balance_after
    ) VALUES (
        p_user_id, 'used', -p_points, 'video_without_ad',
        current_balance, current_balance - p_points
    );

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Función para limpiar referidos expirados
CREATE OR REPLACE FUNCTION cleanup_expired_referrals()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    UPDATE referrals
    SET status = 'expired'
    WHERE status = 'pending'
    AND expires_at < CURRENT_TIMESTAMP;

    GET DIAGNOSTICS expired_count = ROW_COUNT;
    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- DATOS INICIALES
-- ===========================================

-- Insertar configuración inicial si no existe
INSERT INTO bot_config (key, value) VALUES
('points_max_balance', '5'),
('points_per_referral', '1'),
('referral_expiry_days', '7'),
('referral_min_activity_hours', '24')
ON CONFLICT (key) DO NOTHING;

-- ===========================================
-- PERMISOS Y SEGURIDAD
-- ===========================================

-- Políticas RLS (Row Level Security) para Supabase
ALTER TABLE user_points ENABLE ROW LEVEL SECURITY;
ALTER TABLE referrals ENABLE ROW LEVEL SECURITY;
ALTER TABLE points_transactions ENABLE ROW LEVEL SECURITY;

-- Políticas básicas (ajustar según necesidades de seguridad)
-- Nota: Estas políticas son básicas, ajustar según el modelo de auth de Supabase

-- Para user_points: usuarios solo ven sus propios puntos
CREATE POLICY "Users can view own points" ON user_points
    FOR SELECT USING (auth.uid()::text = user_id::text);

-- Para referrals: usuarios ven sus propios referidos
CREATE POLICY "Users can view own referrals" ON referrals
    FOR SELECT USING (auth.uid()::text = referrer_id::text);

-- Para transacciones: usuarios ven su propio historial
CREATE POLICY "Users can view own transactions" ON points_transactions
    FOR SELECT USING (auth.uid()::text = user_id::text);

-- ===========================================
-- ÍNDICES ADICIONALES PARA PERFORMANCE
-- ===========================================

-- Índices compuestos para queries frecuentes
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_status ON referrals(referrer_id, status);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_created ON referrals(referrer_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_points_transactions_user_created ON points_transactions(user_id, created_at DESC);

-- ===========================================
-- VISTAS ÚTILES PARA REPORTES
-- ===========================================

-- Vista de estadísticas de referidos
CREATE OR REPLACE VIEW referral_stats AS
SELECT
    referrer_id,
    COUNT(*) as total_referrals,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_referrals,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_referrals,
    COUNT(CASE WHEN status = 'expired' THEN 1 END) as expired_referrals,
    MAX(completed_at) as last_completed_at
FROM referrals
GROUP BY referrer_id;

-- Vista de estadísticas de puntos
CREATE OR REPLACE VIEW points_stats AS
SELECT
    up.user_id,
    up.points_balance,
    up.total_earned,
    up.total_used,
    rs.total_referrals,
    rs.completed_referrals,
    up.last_earned_at,
    up.created_at as points_created_at
FROM user_points up
LEFT JOIN referral_stats rs ON up.user_id = rs.referrer_id;

-- ===========================================
-- JOB PARA LIMPIEZA AUTOMÁTICA
-- ===========================================

-- Nota: En Supabase, configurar un Edge Function o cron job para ejecutar:
-- SELECT cleanup_expired_referrals();

COMMIT;