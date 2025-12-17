# Configuración de Variables de Entorno en Netlify

Para que la Mini App funcione, necesitas configurar estas variables de entorno en Netlify:

## Pasos:

1. Ve a tu sitio en Netlify Dashboard
2. Ve a **Site settings** → **Environment variables**
3. Agrega las siguientes variables:

### Variables requeridas:

- `SUPABASE_URL`: La URL de tu proyecto Supabase (ejemplo: `https://xxx.supabase.co`)
- `SUPABASE_KEY`: La clave anónima/pública de Supabase (anon/public key)
- `BOT_USERNAME`: El username del bot (ejemplo: `CineStelar_bot`)

## Obtener credenciales de Supabase:

1. Ve a tu proyecto en https://supabase.com/dashboard
2. Ve a **Settings** → **API**
3. Copia:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** key → `SUPABASE_KEY`

## Después de configurar:

1. Haz un nuevo deploy en Netlify o espera el auto-deploy desde GitHub
2. Las funciones serverless estarán disponibles en:
   - `https://TU-SITIO.netlify.app/.netlify/functions/get-movies`

## Verificar que funciona:

Abre en el navegador:
```
https://bottm.netlify.app/.netlify/functions/get-movies
```

Deberías ver un JSON con las películas.
