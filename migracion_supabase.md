# Migración a Supabase (PostgreSQL) - CineStelar Bot

## Paso a Paso para Migrar tu Base de Datos

### 1. Crear cuenta en Supabase
1. Ve a https://supabase.com/
2. Regístrate con tu email o GitHub
3. Crea un nuevo proyecto
4. Elige un nombre para tu proyecto (ej: "cinestelar-bot")
5. Selecciona una región cercana (ej: "US East")
6. Crea una contraseña segura para la base de datos
7. Espera a que se cree el proyecto (2-3 minutos)

### 2. Obtener la cadena de conexión
1. En tu dashboard de Supabase, ve a "Project Settings" → "Database"
2. Copia la "Connection string" (debe empezar con `postgresql://`)
3. **IMPORTANTE:** Cambia el protocolo de `postgresql://` a `postgresql+asyncpg://` para SQLAlchemy

Ejemplo de cadena de conexión:
```
postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

### 3. Instalar dependencias
En tu terminal local:
```powershell
pip install asyncpg
```

Agrega a tu `requirements.txt`:
```
asyncpg
```

### 4. Crear las tablas en Supabase
1. En tu dashboard de Supabase, ve a "SQL Editor"
2. Copia y pega el siguiente SQL y ejecuta:

```sql
-- Crear tabla users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    verified BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE
);

-- Crear tabla videos
CREATE TABLE IF NOT EXISTS videos (
    id SERIAL PRIMARY KEY,
    file_id VARCHAR(200) UNIQUE NOT NULL,
    message_id BIGINT,
    title VARCHAR(500),
    description TEXT,
    tags VARCHAR(500),
    file_size BIGINT,
    duration INTEGER,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tmdb_id INTEGER,
    original_title VARCHAR(500),
    year VARCHAR(10),
    overview TEXT,
    poster_url VARCHAR(500),
    backdrop_url VARCHAR(500),
    vote_average INTEGER,
    runtime INTEGER,
    genres VARCHAR(500),
    channel_message_id BIGINT
);

-- Crear tabla searches
CREATE TABLE IF NOT EXISTS searches (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    query VARCHAR(200),
    results_count INTEGER,
    searched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear tabla favorites
CREATE TABLE IF NOT EXISTS favorites (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    video_id INTEGER NOT NULL,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear tabla ad_tokens
CREATE TABLE IF NOT EXISTS ad_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(100) UNIQUE NOT NULL,
    user_id BIGINT NOT NULL,
    video_id INTEGER NOT NULL,
    message_id BIGINT,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Crear índices para mejor rendimiento
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_videos_file_id ON videos(file_id);
CREATE INDEX IF NOT EXISTS idx_videos_message_id ON videos(message_id);
CREATE INDEX IF NOT EXISTS idx_videos_channel_message_id ON videos(channel_message_id);
CREATE INDEX IF NOT EXISTS idx_searches_user_id ON searches(user_id);
CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_favorites_video_id ON favorites(video_id);
CREATE INDEX IF NOT EXISTS idx_ad_tokens_token ON ad_tokens(token);
CREATE INDEX IF NOT EXISTS idx_ad_tokens_user_id ON ad_tokens(user_id);
```

### 5. Actualizar configuración
1. Abre tu archivo `.env` local
2. Cambia la línea `DATABASE_URL` por la nueva cadena de Supabase:

```
DATABASE_URL=postgresql+asyncpg://postgres:[TU-PASSWORD]@db.[TU-PROJECT-REF].supabase.co:5432/postgres
```

### 6. Probar localmente
1. Ejecuta el bot localmente para verificar que funciona:
```powershell
python main.py
```

2. Si hay errores de conexión, verifica:
   - Que la cadena de conexión sea correcta
   - Que asyncpg esté instalado
   - Que tu firewall permita conexiones a Supabase

### 7. Subir cambios a GitHub
```powershell
git add requirements.txt .env
git commit -m "Migrate to Supabase PostgreSQL database"
git push
```

### 8. Actualizar Render
1. Ve a tu dashboard de Render
2. Selecciona tu servicio
3. Ve a "Environment" o "Env Vars"
4. Cambia la variable `DATABASE_URL` por la nueva cadena de Supabase
5. Render hará redeploy automáticamente

### 9. Verificar que funciona
1. Espera a que Render termine el deploy
2. Prueba el bot en Telegram
3. Si hay errores, revisa los logs de Render

### 10. (Opcional) Migrar datos existentes
Si tienes datos en tu SQLite local y quieres migrarlos:

1. Exporta datos de SQLite (usa DB Browser for SQLite)
2. Importa a Supabase usando el SQL Editor o scripts de migración

---

## Notas Importantes

- **Costo:** Supabase tiene un plan gratuito generoso (500MB, 50MB de archivos)
- **Seguridad:** Nunca subas tu `.env` con contraseñas reales al repositorio
- **Backup:** Supabase hace backups automáticos
- **Escalabilidad:** PostgreSQL maneja mejor el crecimiento que SQLite

Si tienes problemas en algún paso, dime cuál y te ayudo a resolverlo.