# 🚀 GUÍA PASO A PASO - Configurar Anuncios con Netlify + Render

## 📌 Resumen de la Arquitectura

```
┌─────────────┐
│   NETLIFY   │ ← Mini App (HTML estático)
│ ad_viewer   │    https://tu-app.netlify.app
└─────────────┘
       │
       │ API call
       ▼
┌─────────────┐
│   RENDER    │ ← Servidor Flask + Bot Python
│ Flask API   │    https://tu-app.onrender.com
└─────────────┘
       │
       ▼
    Bot envía video
```

---

## 📋 PARTE 1: SUBIR MINI APP A NETLIFY

### Paso 1.1: Crear cuenta en Netlify

1. Ve a https://www.netlify.com
2. Click en **"Sign up"**
3. Registrarte con GitHub (recomendado) o email
4. Confirma tu email

### Paso 1.2: Preparar archivos

Ya están listos:
- ✅ `webapp/ad_viewer.html` - Mini App
- ✅ `netlify.toml` - Configuración de Netlify

### Paso 1.3: Subir a Netlify (Método Drag & Drop)

#### Opción A: Sin Git (Más rápido)

1. Abre https://app.netlify.com
2. Click en **"Add new site"** → **"Deploy manually"**
3. **Arrastra** la carpeta `webapp` a la zona de drop
4. Espera 30 segundos
5. ✅ Te dará una URL como: `https://random-name-123.netlify.app`
6. **ANOTA ESTA URL** (la necesitarás después)

#### Opción B: Con Git (Más profesional)

1. Instala Git si no lo tienes:
```powershell
winget install Git.Git
```

2. Crear repositorio en GitHub:
```powershell
cd C:\Users\stail\Desktop\bot
git init
git add .
git commit -m "Initial commit"
# Ve a github.com y crea un nuevo repositorio vacío
# Luego:
git remote add origin https://github.com/TU_USUARIO/tu-repo.git
git push -u origin main
```

3. En Netlify:
   - Click **"Add new site"** → **"Import from Git"**
   - Conecta GitHub
   - Selecciona tu repositorio
   - Build settings:
     - **Base directory**: `webapp`
     - **Publish directory**: `webapp`
   - Click **"Deploy"**

### Paso 1.4: Personalizar URL (Opcional)

1. En Netlify, ve a **"Site settings"** → **"Change site name"**
2. Elige un nombre único: `cinestelar-ads`
3. Tu URL será: `https://cinestelar-ads.netlify.app`

**📝 ANOTA TU URL DE NETLIFY:**
```
https://TU-NOMBRE.netlify.app
```

---

## 📋 PARTE 2: SUBIR BOT Y SERVIDOR A RENDER

### Paso 2.1: Crear cuenta en Render

1. Ve a https://render.com
2. Click **"Get Started"**
3. Registrarte con GitHub (recomendado)
4. No necesitas tarjeta de crédito

### Paso 2.2: Preparar código para Render

Ya tenemos `webapp_server.py`, pero necesitamos un archivo unificado:

Crea `server_and_bot.py` que ejecuta ambos:

```python
# Este archivo se creará en el siguiente paso
```

### Paso 2.3: Crear archivo de inicio

Este archivo ejecutará Flask y el Bot juntos.

### Paso 2.4: Subir a GitHub (Si no lo hiciste antes)

```powershell
cd C:\Users\stail\Desktop\bot
git init
git add .
git commit -m "Bot con sistema de anuncios"

# Crear repo en https://github.com/new
# Luego:
git remote add origin https://github.com/TU_USUARIO/cinestelar-bot.git
git push -u origin main
```

### Paso 2.5: Deploy en Render

1. Ve a https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Conecta tu repositorio de GitHub
4. Configuración:

```
Name: cinestelar-bot
Region: Oregon (US West)
Branch: main
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: python webapp_server.py & python main.py
```

5. Scroll abajo, en **"Environment Variables"** agregar:

```
BOT_TOKEN=8352053218:AAGNe-yZ-_nXTEFFuSulfUJ5MUGPOPzwIaY
BOT_USERNAME=CineStelar_bot
VERIFICATION_CHANNEL_ID=-1003216346183
VERIFICATION_CHANNEL_USERNAME=@CineStellar_S
STORAGE_CHANNEL_ID=-1003371387168
DATABASE_URL=sqlite+aiosqlite:///bot_database.db
TMDB_API_KEY=809a7e60ba4a7eb2fe7513d9ab88d2e2
ADMIN_IDS=7830343272
WEBAPP_URL=https://TU-NOMBRE.netlify.app/ad_viewer.html
FLASK_PORT=10000
```

**⚠️ IMPORTANTE:** Cambia `TU-NOMBRE.netlify.app` por tu URL real de Netlify del Paso 1.4

6. Click **"Create Web Service"**
7. Espera 5-10 minutos mientras se despliega
8. ✅ Te dará una URL como: `https://cinestelar-bot.onrender.com`

**📝 ANOTA TU URL DE RENDER:**
```
https://TU-APP.onrender.com
```

---

## 📋 PARTE 3: CONECTAR TODO

### Paso 3.1: Actualizar URL del servidor en search.py

Ya está configurado para usar `WEBAPP_URL` de `.env`, pero necesitas agregar el parámetro `api_url`.

### Paso 3.2: Configurar dominio en BotFather

1. Abre Telegram y busca **@BotFather**
2. Envía: `/setdomain`
3. Selecciona: **@CineStelar_bot**
4. Envía tu dominio de Netlify (SIN https://):
```
TU-NOMBRE.netlify.app
```

### Paso 3.3: Actualizar .env local

Edita tu archivo `.env`:

```env
WEBAPP_URL=https://TU-NOMBRE.netlify.app/ad_viewer.html
```

### Paso 3.4: Verificar que todo funcione

1. Ve a tu dashboard de Render: https://dashboard.render.com
2. Abre tu servicio "cinestelar-bot"
3. Ve a **"Logs"** - Debes ver:
```
Bot iniciado...
Base de datos inicializada
🌐 Servidor Flask iniciado en puerto 10000
```

---

## 📋 PARTE 4: PROBAR EL SISTEMA

### Paso 4.1: Indexar un video con TMDB

1. En Telegram, envía a tu bot: `/indexar`
2. Espera que termine (verás el mensaje de finalización)

### Paso 4.2: Buscar y probar anuncio

1. Envía: `/buscar thor`
2. Selecciona una película
3. Deberías ver el botón: **"📺 Ver Anuncio para Continuar"**
4. Toca el botón → Se abre la Mini App
5. Ve el anuncio completo
6. ✅ El bot envía automáticamente la película

---

## 🔧 CONFIGURACIÓN AVANZADA

### Actualizar handler de búsqueda

Necesitamos pasar la URL del servidor API a la Mini App:

```python
# En handlers/search.py
webapp_url = f"{WEBAPP_URL}?token={token}&title={title_encoded}&poster={poster_encoded}&api_url={API_SERVER_URL}"
```

---

## ⚠️ PROBLEMAS COMUNES

### "Mini App no se abre"
✅ **Solución:** Verifica que configuraste `/setdomain` en @BotFather

### "Token inválido"
✅ **Solución:** Verifica que la variable `WEBAPP_URL` en Render apunte a Netlify

### "Video no se envía"
✅ **Solución:** Revisa logs en Render: https://dashboard.render.com → Tu servicio → Logs

### "Anuncio no carga"
✅ **Solución:** Verifica que el script de libtl.com esté accesible desde Netlify

### Render dice "Build failed"
✅ **Solución:** Verifica que `requirements.txt` tenga todas las dependencias

---

## 📊 RESUMEN DE URLs

Una vez completado, tendrás:

```
Mini App (Netlify):  https://TU-NOMBRE.netlify.app
Servidor (Render):   https://TU-APP.onrender.com
Bot:                 @CineStelar_bot
```

---

## 🎯 SIGUIENTE PASO

**¿Quieres que modifique el código ahora para que incluya la URL del servidor API?**

Necesito:
1. Agregar variable `API_SERVER_URL` en settings.py
2. Modificar `handlers/search.py` para pasar `api_url` a la Mini App
3. Crear script unificado para Render

¿Procedo con estas modificaciones? 🚀
